# task_decomposer_llm.py
# LLM-first task decomposer (single file).
# - No rule-based fallback. The LLM decides task values.
# - Adds priority + priority_num.
# - Optional context envelope (no profession).
# - Simple CLI.

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

# ---------------------------
# Models (dataclasses for zero extra deps)
# ---------------------------

Priority = Literal["high", "medium", "low"]
TaskKind = Literal["activity", "travel"]

@dataclass
class Task:
    kind: TaskKind
    title: str
    start: Optional[str] = None         # ISO 8601 or null
    end: Optional[str] = None           # ISO 8601 or null
    duration_minutes: Optional[int] = None
    location: Optional[str] = None      # "unknown" or null if unknown
    constraints: List[str] = None       # ["at 15:00", "after 17:00", "before EOD"]
    contacts: List[str] = None          # emails/phones/@handles tied to this task
    notes: str = ""
    confidence: float = 0.6
    # NEW:
    priority: Priority = "medium"
    priority_num: int = 2               # 1=high, 2=medium, 3=low

    def __post_init__(self):
        if self.constraints is None: self.constraints = []
        if self.contacts is None: self.contacts = []

@dataclass
class TaskList:
    tasks: List[Task]
    contacts: List[str]               # globally extracted contacts (deduped)
    time_phrases: List[str]           # ["at 3pm","after 5pm","before EOD"]
    # You can extend with diagnostics if needed
    # diagnostics: Optional[Dict[str, Any]] = None


# ---------------------------
# Prompt (strict JSON; includes priority guidance)
# ---------------------------

TASK_JSON_INSTRUCTIONS = """
You are a planner that converts the user's free-text request into STRICT JSON.

Output EXACTLY this structure (no prose, no backticks):

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
      "confidence": "number 0..1",
      "priority": "high" | "medium" | "low",
      "priority_num": 1 | 2 | 3
    }
  ],
  "contacts": ["emails/phones/handles"],
  "time_phrases": ["e.g., 'at 3pm', 'after 5pm', 'before EOD'"]
}

Rules:
- Identify activities (lecture, class, meeting, gym, read, call, appointment, lunch, etc.).
- If travel is likely (the activity implies a different place than where the user currently is),
  ADD a separate travel task that ENDS before the activity start. If the activity time is unknown,
  keep travel time flexible and note that in constraints.
- Extract time constraints and keep them as constraints if exact times are not stated
  (e.g., "after 5pm", "before EOD"). Do NOT fabricate exact times.
- Extract contact info (emails, phone numbers, @handles) from the text. Put them on the
  relevant task and also include a deduplicated list in top-level "contacts".
- PRIORITY assignment:
  - "high" (priority_num=1): time-critical, external commitments, hard deadlines, interviews, flights,
    exams, medical appointments, meetings with others, tasks due today, urgent follow-ups, or blockers.
  - "medium" (priority_num=2): important but somewhat flexible (study blocks before exam week, gym today,
    grocery pick-up, preparation for tomorrow).
  - "low" (priority_num=3): aspirational or flexible (reading for pleasure, optional errands).
- If you cannot infer a field, set it to null and add a helpful note in "notes".
- Avoid hallucinations. Use only the information in the user's text and the optional context.
Return ONLY valid JSON.
"""

# ---------------------------
# OpenAI adapter (LLM-first)
# ---------------------------

class OpenAIClient:
    """
    Minimal adapter for OpenAI-compatible Chat Completions API.
    Requires: api_key (env/flag) and optional base_url gateway.
    """
    def __init__(self, api_key: str, base_url: Optional[str], model: str = "gpt-4.1-mini", temperature: float = 0.0):
        import openai
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url) if base_url \
                      else openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def json_chat(self, prompt: str) -> Dict[str, Any]:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            # If your gateway supports it, you may uncomment:
            # response_format={"type": "json_object"},
        )
        text = (resp.choices[0].message.content or "").strip()

        # Tolerate accidental fences:
        if text.startswith("```"):
            text = text.strip("`")
            nl = text.find("\n")
            if nl != -1:
                text = text[nl+1:].strip()
        data = json.loads(text or "{}")
        if not isinstance(data, dict):
            raise ValueError("LLM did not return a JSON object.")
        return data

# ---------------------------
# Agent (LLM-first; tiny normalization only)
# ---------------------------

class TaskDecomposerLLM:
    """
    LLM-first decomposer.
    - No rule-based fallback.
    - Normalizes priority_num if missing/mismatched.
    - Keeps profession out of inputs entirely.
    """

    def __init__(self, llm: OpenAIClient, tz: str = "Europe/Amsterdam"):
        self.llm = llm
        self.tz = tz

    # Optional environment hooks (empty for now; keep for future integrations)
    def get_user_current_location(self, state: Dict[str, Any]) -> Optional[str]:
        return None  # e.g., "home" or address if you integrate later

    def _priority_num_from_priority(self, p: Optional[str]) -> int:
        mapping = {"high": 1, "medium": 2, "low": 3}
        return mapping.get((p or "medium").lower(), 2)

    def _normalize_tasks(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure priority_num aligns with priority if the model omitted or mismatched it.
        tasks = payload.get("tasks") or []
        for t in tasks:
            p = t.get("priority") or "medium"
            pn = t.get("priority_num")
            correct = self._priority_num_from_priority(p)
            if pn not in (1, 2, 3) or pn != correct:
                t["priority_num"] = correct
        # Dedup contacts at top level
        all_contacts = set(payload.get("contacts") or [])
        for t in tasks:
            for c in (t.get("contacts") or []):
                all_contacts.add(c)
        payload["contacts"] = sorted(all_contacts)
        return payload

    def _now_iso(self, now: Any) -> str:
        if isinstance(now, datetime):
            return now.isoformat()
        if isinstance(now, str):
            try:
                # Validate string parses; if not, fall back to "now"
                datetime.fromisoformat(now)
                return now
            except Exception:
                pass
        return datetime.now(timezone.utc).astimezone().isoformat()

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        state:
          - raw_transcript: str      (required)
          - now: ISO string or datetime (optional; defaults to local now)
          - context: dict (optional)  # arbitrary "context envelope" — places/goals/hours/etc. (NO profession)
        """
        text = state.get("raw_transcript") or ""
        if not text.strip():
            raise ValueError("raw_transcript is required.")

        now_iso = self._now_iso(state.get("now"))
        context = state.get("context") or {}  # user-provided optional hints (no profession)

        prompt = (
            f"{TASK_JSON_INSTRUCTIONS}\n\n"
            f"Now: {now_iso}\n"
            f"Timezone: {self.tz}\n"
            f"Optional context (JSON):\n{json.dumps(context, ensure_ascii=False)}\n\n"
            f"User text:\n{text}\n"
        )

        data = self.llm.json_chat(prompt)
        data = self._normalize_tasks(data)

        # Return in a stable container
        tasks: List[Task] = []
        for t in data.get("tasks") or []:
            tasks.append(Task(
                kind=t.get("kind", "activity"),
                title=t.get("title", "Task"),
                start=t.get("start"),
                end=t.get("end"),
                duration_minutes=t.get("duration_minutes"),
                location=t.get("location"),
                constraints=list(t.get("constraints") or []),
                contacts=list(t.get("contacts") or []),
                notes=t.get("notes") or "",
                confidence=float(t.get("confidence") or 0.6),
                priority=(t.get("priority") or "medium"),
                priority_num=int(t.get("priority_num") or self._priority_num_from_priority(t.get("priority")))
            ))

        result = TaskList(
            tasks=tasks,
            contacts=list(data.get("contacts") or []),
            time_phrases=list(data.get("time_phrases") or []),
        )

        # Write back into state (for pipeline compatibility)
        state["decomposed_tasks"] = [asdict(t) for t in result.tasks]
        state["extracted_contacts"] = result.contacts
        state["time_phrases"] = result.time_phrases
        return state


# ---------------------------
# CLI
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="LLM-first Task Decomposer (priority-aware)")
    parser.add_argument("--text", "-t", required=True, help="User input text (free-form)")
    parser.add_argument("--now", default=None, help="ISO datetime (optional; defaults to local now)")
    parser.add_argument("--context", "-c", default=None,
                        help="Path to a JSON file or raw JSON string for optional context (NO profession).")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key")
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL"),
                        help="OpenAI Base URL (for gateways); omit if using api.openai.com")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                        help="Model name (e.g., gpt-4.1-mini)")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature (default 0.0)")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing --api-key (or set OPENAI_API_KEY).")

    # Load context if provided (file path or raw JSON)
    ctx: Dict[str, Any] = {}
    if args.context:
        if os.path.isfile(args.context):
            with open(args.context, "r", encoding="utf-8") as f:
                ctx = json.load(f)
        else:
            # Try parsing as JSON string
            try:
                ctx = json.loads(args.context)
            except Exception as e:
                raise SystemExit(f"--context is neither a file nor valid JSON: {e}")

    # Init LLM and agent
    llm = OpenAIClient(api_key=args.api_key, base_url=args.base_url, model=args.model, temperature=args.temperature)
    agent = TaskDecomposerLLM(llm=llm)

    state: Dict[str, Any] = {
        "raw_transcript": args.text,
        "now": args.now,
        "context": ctx,  # NOTE: do not include profession here
    }

    out = agent.execute(state)
    print(json.dumps({
        "decomposed_tasks": out.get("decomposed_tasks", []),
        "extracted_contacts": out.get("extracted_contacts", []),
        "time_phrases": out.get("time_phrases", []),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
