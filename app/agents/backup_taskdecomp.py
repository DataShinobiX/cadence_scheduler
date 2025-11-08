# task_decomposer.py
# A single-file, provider-agnostic task decomposer with an OpenAI adapter,
# rule-based fallback, and a simple CLI for interactive use.

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, time, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Literal

# ---------------------------
# Models (Pydantic-like via dataclasses to avoid extra deps; easy to swap)
# ---------------------------

TaskKind = Literal["activity", "travel"]

@dataclass
class Task:
    kind: TaskKind
    title: str
    start: Optional[str] = None        # ISO 8601 or None
    end: Optional[str] = None          # ISO 8601 or None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None     # "unknown" if not set
    constraints: List[str] = None      # e.g., ["after 17:00","before EOD"]
    contacts: List[str] = None
    notes: str = ""
    confidence: float = 0.6

    def __post_init__(self):
        if self.constraints is None: self.constraints = []
        if self.contacts is None: self.contacts = []

@dataclass
class TaskList:
    tasks: List[Task]
    contacts: List[str]
    time_phrases: List[str]

# ---------------------------
# Prompt (kept in-file as requested)
# ---------------------------

TASK_JSON_INSTRUCTIONS = """
You are a planner that converts a user's free-text request into a JSON object.

Output STRICT JSON matching this schema:
{
  "tasks": [
    {
      "kind": "activity" | "travel",
      "title": "string",
      "start": "ISO 8601 datetime or null",
      "end": "ISO 8601 datetime or null",
      "duration_minutes": "number or null",
      "location": "string or null",
      "constraints": ["string", "..."],
      "contacts": ["string", "..."],
      "notes": "string",
      "confidence": "number 0..1"
    }
  ],
  "contacts": ["emails/phones/handles"],
  "time_phrases": ["e.g., 'at 3pm', 'after 5pm', 'before EOD'"]
}

Rules:
- Identify activities (lecture, class, meeting, gym, read, call, appointment, lunch).
- If travel is likely (previous location differs from task location or the activity implies a venue),
  add a travel task that ENDS before the activity start.
- If time is vague (e.g., 'after 5pm', 'before EOD'), put it in constraints; do NOT invent exact times.
- Extract any emails, phone numbers, or @handles into `contacts`.
- If you cannot infer something, set it to null and add a helpful note.
Return ONLY the JSON. Do not include backticks or extra text.
"""

# ---------------------------
# Generic LLM interface + OpenAI adapter
# ---------------------------

T = TypeVar("T")

class StructuredResponse(Generic[T]):
    def __init__(self, ok: bool, value: Optional[T], raw: Any = None, error: Optional[str] = None):
        self.ok = ok
        self.value = value
        self.raw = raw
        self.error = error

class BaseLLMClient:
    def structured(self, prompt: str, **kwargs) -> StructuredResponse[Dict[str, Any]]:
        raise NotImplementedError

class OpenAIClient(BaseLLMClient):
    """
    Minimal adapter over openai.OpenAI that requests strict JSON and parses it.
    Works with base_url gateways that implement Chat Completions.
    """
    def __init__(self, api_key: str, base_url: Optional[str], model: str = "gpt-4.1-mini", temperature: float = 0.0):
        import openai
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url) if base_url \
                      else openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def structured(self, prompt: str, **kwargs) -> StructuredResponse[Dict[str, Any]]:
        try:
            messages = [{"role": "user", "content": prompt}]
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                # Some gateways support response_format, some don't. Keeping it simple & robust:
                # response_format={"type": "json_object"},
                **kwargs
            )
            text = (resp.choices[0].message.content or "").strip()
            # If the model wrapped in code fences, try to strip them.
            if text.startswith("```"):
                text = text.strip("`")
                # Remove leading language hint if present (e.g., json)
                first_newline = text.find("\n")
                if first_newline != -1:
                    text = text[first_newline+1:].strip()
            data = json.loads(text or "{}")
            if not isinstance(data, dict):
                return StructuredResponse(False, None, raw=text, error="Non-dict JSON")
            return StructuredResponse(True, data, raw=text)
        except Exception as e:
            return StructuredResponse(False, None, raw=None, error=str(e))

# ---------------------------
# Rule-based fallback utilities
# ---------------------------

TIME_AT_RE = re.compile(r'\b(?:at\s*)?((?:1[0-2]|0?[1-9])(?::[0-5][0-9])?\s?(?:am|pm))\b', re.IGNORECASE)
AFTER_RE   = re.compile(r'\bafter\s+((?:1[0-2]|0?[1-9])(?::[0-5][0-9])?\s?(?:am|pm))\b', re.IGNORECASE)
BEFORE_RE  = re.compile(r'\bbefore\s+((?:1[0-2]|0?[1-9])(?::[0-5][0-9])?\s?(?:am|pm)|EOD)\b', re.IGNORECASE)
EOD_ALIASES = {"eod", "end of day"}

EMAIL_RE  = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
PHONE_RE  = re.compile(r'\+?\d[\d\s\-().]{6,}\d')
HANDLE_RE = re.compile(r'@\w+')

KEYWORDS = {
    "lecture":  {"title": "Attend lecture", "default_duration": 90, "implies_location": "campus"},
    "class":    {"title": "Attend class",   "default_duration": 60, "implies_location": "campus"},
    "meeting":  {"title": "Meeting",        "default_duration": 30, "implies_location": "office"},
    "gym":      {"title": "Gym session",    "default_duration": 45, "implies_location": "gym"},
    "read":     {"title": "Reading",        "default_duration": 30, "implies_location": None},
    "call":     {"title": "Call",           "default_duration": 30, "implies_location": "remote"},
    "appointment": {"title": "Appointment", "default_duration": 45, "implies_location": None},
    "lunch":    {"title": "Lunch",          "default_duration": 60, "implies_location": "cafeteria"},
}

DEFAULTS = {
    "activity_duration": 60,
    "travel_duration": 30,
    "eod_hour": 18,  # local end of day
}

def parse_ampm_to_24h(ts: str) -> (int, int):
    s = ts.strip().lower().replace(" ", "")
    m = re.match(r'(1[0-2]|0?[1-9])(?::([0-5][0-9]))?(am|pm)', s)
    if not m: raise ValueError(f"Bad time: {ts}")
    hh = int(m.group(1)) % 12
    mm = int(m.group(2) or 0)
    if m.group(3) == "pm": hh += 12
    return hh, mm

def iso_on_today(hour: int, minute: int, now: datetime) -> str:
    dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return dt.isoformat()

def extract_contacts(text: str) -> List[str]:
    return list({*EMAIL_RE.findall(text), *PHONE_RE.findall(text), *HANDLE_RE.findall(text)})

def extract_time_phrases(text: str) -> Dict[str, List[str]]:
    ats = [m for m in TIME_AT_RE.findall(text)]
    afters = [m for m in AFTER_RE.findall(text)]
    befores = []
    for b in BEFORE_RE.findall(text):
        befores.append("EOD" if b.lower() in EOD_ALIASES else b)
    return {"at_times": ats, "after_times": afters, "before_times": befores}

def detect_keywords(text: str) -> List[str]:
    hits = []
    for k in KEYWORDS.keys():
        if re.search(rf'\b{k}\b', text, re.IGNORECASE):
            hits.append(k)
    return hits or ["meeting"]

def default_location_for(keyword: str, profession: Optional[str]) -> str:
    implied = KEYWORDS.get(keyword, {}).get("implies_location")
    if implied == "campus" and profession and profession.lower() == "student":
        return "campus"
    return implied or "unknown"

def default_activity_duration(keyword: Optional[str]) -> int:
    return KEYWORDS.get(keyword or "", {}).get("default_duration", DEFAULTS["activity_duration"])

# ---------------------------
# Decomposer Agent
# ---------------------------

class TaskDecomposerAgent:
    def __init__(
        self,
        llm: Optional[BaseLLMClient] = None,
        tz: str = "Europe/Amsterdam",
        travel_minutes_default: int = DEFAULTS["travel_duration"]
    ):
        self.llm = llm
        self.tz = tz
        self.travel_minutes_default = travel_minutes_default

    # --- Empty hooks to integrate later ---
    def get_user_current_location(self, state: Dict[str, Any]) -> Optional[str]:
        return None

    def get_task_location(self, text: str, profession: Optional[str]) -> Optional[str]:
        return None

    # --- Core ---
    # not being used 
    def rule_fallback(self, text: str, now: datetime, profession: Optional[str]) -> Dict[str, Any]:
        contacts = extract_contacts(text)
        tinfo = extract_time_phrases(text)
        keywords = detect_keywords(text)

        # Simple policy: use the first explicit "at" time if present
        fixed_time = tinfo["at_times"][0] if tinfo["at_times"] else None
        after_time = tinfo["after_times"][0] if tinfo["after_times"] else None
        before_time = tinfo["before_times"][0] if tinfo["before_times"] else None

        tasks: List[Task] = []
        for kw in keywords:
            duration = default_activity_duration(kw)
            start_iso = None
            end_iso = None
            constraints: List[str] = []
            if fixed_time:
                try:
                    hh, mm = parse_ampm_to_24h(fixed_time)
                    start_iso = iso_on_today(hh, mm, now)
                    # compute end
                    start_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    end_iso = (start_dt + timedelta(minutes=duration)).isoformat()
                except Exception:
                    constraints.append(f"at {fixed_time}")

            if after_time and start_iso is None:
                constraints.append(f"after {after_time}")
            if before_time:
                constraints.append(f"before {before_time}")

            loc = self.get_task_location(text, profession) or default_location_for(kw, profession)
            task = Task(
                kind="activity",
                title=KEYWORDS.get(kw, {}).get("title", kw.capitalize()),
                start=start_iso,
                end=end_iso,
                duration_minutes=duration,
                location=loc,
                constraints=constraints,
                contacts=contacts,
                notes=f"keyword={kw}",
                confidence=0.8 if start_iso else 0.6
            )
            tasks.append(task)

        time_phrases = []
        time_phrases.extend([f"at {t}" for t in tinfo["at_times"]])
        time_phrases.extend([f"after {t}" for t in tinfo["after_times"]])
        time_phrases.extend([f"before {t}" for t in tinfo["before_times"]])

        return {
            "tasks": [asdict(t) for t in tasks],
            "contacts": contacts,
            "time_phrases": time_phrases,
        }

    def insert_travel(self, tasks: List[Task], prev_loc: Optional[str]) -> List[Task]:
        out: List[Task] = []
        for t in tasks:
            if t.kind == "activity":
                activity_loc = (t.location or "unknown")
                need_travel = False
                if activity_loc not in {"unknown", "remote"}:
                    if prev_loc is None or prev_loc != activity_loc:
                        need_travel = True
                if need_travel:
                    # Travel ends at activity start if known
                    start_iso = None
                    end_iso = t.start
                    if end_iso:
                        try:
                            end_dt = datetime.fromisoformat(end_iso)
                            start_dt = end_dt - timedelta(minutes=self.travel_minutes_default)
                            start_iso = start_dt.isoformat()
                        except Exception:
                            start_iso = None
                    travel_task = Task(
                        kind="travel",
                        title=f"Travel to {activity_loc}",
                        start=start_iso,
                        end=end_iso,
                        duration_minutes=self.travel_minutes_default,
                        location=f"to:{activity_loc}",
                        constraints=(["finish before activity"] if end_iso else ["time flexible"]),
                        contacts=[],
                        notes="inferred travel",
                        confidence=0.7 if end_iso else 0.5
                    )
                    out.append(travel_task)
                    prev_loc = activity_loc
            out.append(t)
            prev_loc = t.location or prev_loc
        return out

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        state expects:
          - raw_transcript: str
          - user_profile: { profession?: str, home_location?: str }
          - now: ISO 8601 or datetime (optional; defaults to now UTC)
        """
        text = state.get("raw_transcript", "") or ""
        profile = state.get("user_profile") or {}
        profession = profile.get("profession")
        now_val = state.get("now")
        if isinstance(now_val, str):
            try:
                now = datetime.fromisoformat(now_val)
            except Exception:
                now = datetime.now(timezone.utc).astimezone()
        elif isinstance(now_val, datetime):
            now = now_val
        else:
            now = datetime.now(timezone.utc).astimezone()

        result_dict: Optional[Dict[str, Any]] = None
        errors: List[str] = []

        # 1) Try LLM if available
        if self.llm:
            prompt = (
                f"{TASK_JSON_INSTRUCTIONS}\n"
                f"Profession: {profession or 'unknown'}\n"
                f"Now: {now.isoformat()}\n"
                f"User text:\n{text}"
            )
            resp = self.llm.structured(prompt)
            if resp.ok and isinstance(resp.value, dict) and "tasks" in resp.value:
                result_dict = resp.value
            else:
                errors.append(f"LLM parse failed: {resp.error or 'unknown error'}")

        # 2) Fallback rules
        if not result_dict:
            print("No results from LLM; using rule-based fallback.")
            #result_dict = self.rule_fallback(text, now, profession)

        # 3) Normalize into Task objects
        tasks: List[Task] = []
        for td in result_dict.get("tasks", []):
            tasks.append(Task(
                kind=td.get("kind", "activity"),
                title=td.get("title", "Task"),
                start=td.get("start"),
                end=td.get("end"),
                duration_minutes=td.get("duration_minutes"),
                location=td.get("location"),
                constraints=list(td.get("constraints") or []),
                contacts=list(td.get("contacts") or []),
                notes=td.get("notes") or "",
                confidence=float(td.get("confidence") or 0.6)
            ))

        # 4) Insert travel based on previous known location
        prev_loc = self.get_user_current_location(state) or profile.get("home_location")
        tasks = self.insert_travel(tasks, prev_loc)

        # 5) Build final state
        out_contacts = list(result_dict.get("contacts") or [])
        time_phrases = list(result_dict.get("time_phrases") or [])

        state["decomposed_tasks"] = [asdict(t) for t in tasks]
        state["extracted_contacts"] = out_contacts
        state["time_phrases"] = time_phrases
        if errors:
            state["errors"] = state.get("errors", []) + errors
        return state

# ---------------------------
# CLI
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Task Decomposer (OpenAI + rule fallback)")
    parser.add_argument("--text", "-t", required=True, help="User input text (free-form)")
    parser.add_argument("--profession", "-p", default=None, help="User profession (e.g., student, engineer)")
    parser.add_argument("--home", default=None, help="Home/base location label (optional)")
    parser.add_argument("--now", default=None, help="ISO datetime (optional; defaults to local now)")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM (OpenAI) before rule fallback")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key")
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL"), help="OpenAI Base URL (for gateways)")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), help="Model name")
    args = parser.parse_args()

    llm: Optional[BaseLLMClient] = None
    if args.use_llm:
        if not args.api_key:
            raise SystemExit("Missing --api-key (or set OPENAI_API_KEY).")
        # You provided a custom base_url; pass it here (can be None if using OpenAI direct)
        llm = OpenAIClient(api_key=args.api_key, base_url=args.base_url, model=args.model, temperature=0.0)

    agent = TaskDecomposerAgent(llm=llm)

    state: Dict[str, Any] = {
        "raw_transcript": args.text,
        "user_profile": {
            "profession": args.profession,
            "home_location": args.home,
        },
    }
    if args.now:
        state["now"] = args.now

    result_state = agent.execute(state)
    print(json.dumps({
        "decomposed_tasks": result_state.get("decomposed_tasks", []),
        "extracted_contacts": result_state.get("extracted_contacts", []),
        "time_phrases": result_state.get("time_phrases", []),
        "errors": result_state.get("errors", []),
    }, indent=2))

if __name__ == "__main__":
    main()
