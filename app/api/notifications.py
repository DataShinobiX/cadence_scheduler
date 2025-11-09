from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Query
import os
import psycopg2
from psycopg2.extras import RealDictCursor

from app.db.calendar_events import fetch_calendar_events
from app.services.weather import get_weather_summary

router = APIRouter()

# Use same LLM gateway settings as other modules for consistency
API_KEY = "sk-aU7KLAifP85EWxg4J7NFJg"
BASE_URL = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"


def _get_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "scheduler_db"),
        user=os.getenv("DB_USER", "scheduler_user"),
        password=os.getenv("DB_PASSWORD", "scheduler_pass"),
    )


def _get_user_name(user_id: str) -> Optional[str]:
    try:
        print(f"[NOTIFY] 🔎 Looking up user name for user_id={user_id}")
        conn = _get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT name, email FROM users WHERE user_id = %s::uuid LIMIT 1;",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                print(f"[NOTIFY] ⚠️ No user row found")
                return None
            name = (row.get("name") or "").strip()
            if not name:
                # Fallback to the part of email before '@'
                email = (row.get("email") or "").strip()
                if "@" in email:
                    print(f"[NOTIFY] ℹ️  User has no name; deriving from email '{email}'")
                    return email.split("@", 1)[0]
                return None
            print(f"[NOTIFY] ✅ Found user name: {name}")
            return name
    except Exception:
        print(f"[NOTIFY] ⚠️ Error while fetching user name; continuing without it")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _first_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return name.strip().split(" ")[0]


async def _generate_notification_text(event: Dict[str, Any], weather: Dict[str, Any] | None, user_name: Optional[str]) -> str:
    """
    Generate a concise, friendly notification string for a single event.
    Uses LLM if available; falls back to a rule-based string.
    """
    title = (event.get("summary") or "Upcoming Event").strip()
    start_ts = event.get("start_datetime")
    location = (event.get("location") or "").strip()
    if isinstance(start_ts, datetime):
        # Short, human-friendly timestamp
        start_str = start_ts.strftime("%a %I:%M %p")
    else:
        start_str = str(start_ts)

    # Fallback string first
    salutation = _first_name(user_name)
    if salutation:
        parts = [f"Hey {salutation}, you've got {title.lower()} at {start_str}"]
    else:
        parts = [f"You've got {title.lower()} at {start_str}"]
    if location:
        parts.append(f"in {location}")
    suggestions = []
    if weather:
        wx_bits = []
        cond = weather.get("conditions")
        temp = weather.get("temperature_c")
        precip = weather.get("precipitation_probability")
        if cond:
            wx_bits.append(cond.lower())
        if isinstance(temp, (int, float)):
            wx_bits.append(f"{round(temp)}°C")
            if temp <= 8:
                suggestions.append("wear a warm jacket")
            elif temp >= 28:
                suggestions.append("stay hydrated")
        if isinstance(precip, (int, float)):
            wx_bits.append(f"{int(precip)}% rain")
            if precip >= 50:
                suggestions.append("bring an umbrella")
        if wx_bits:
            parts.append(f"({', '.join(wx_bits)})")
    # Add one actionable tip if any
    if suggestions:
        parts.append(f"— {suggestions[0]}.")
    fallback_text = " ".join(parts)
    print(f"[NOTIFY]   ✍️  Fallback text prepared")

    # Try LLM for a more helpful, personalized message
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatOpenAI(model="gpt-5", api_key=API_KEY, base_url=BASE_URL, temperature=1.0)
        system = SystemMessage(
            content=(
                "You are a helpful assistant that writes SHORT, friendly notifications for upcoming events. "
                "Be actionable and specific. Include weather implication if relevant (e.g., bring umbrella). "
                "Return only a single sentence under 180 characters."
            )
        )
        human_payload = {
            "event": {
                "title": title,
                "start": start_str,
                "location": location,
            },
            "weather": weather or {},
            "user": {"name": user_name or ""},
            "style": "short, warm, and natural; 1 sentence; include actionable tip if relevant",
        }
        human = HumanMessage(content=f"Create a notification:\n{human_payload}")
        print(f"[NOTIFY]   🤖 Invoking LLM for message generation")
        response = llm.invoke([system, human])
        text = getattr(response, "content", None) or ""
        text = text.strip()
        # Guard rails
        if not text:
            print(f"[NOTIFY]   ⚠️  LLM returned empty content; using fallback: ")
            return fallback_text
        if len(text) > 220:
            text = text[:217] + "..."
        print(f"[NOTIFY]   ✅ LLM message generated ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"[NOTIFY]   ❌ Error: {e}")
        print(f"[NOTIFY]   ⚠️  LLM generation failed; using fallback")
        return fallback_text


@router.get("/api/notifications")
async def get_upcoming_notifications(
    user_id: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=14),
) -> Dict[str, Any]:
    """
    Return smart notifications for upcoming events in the next N days.
    Each notification includes event info, optional weather, and a short message.
    """
    print("\n" + "=" * 60)
    print("[NOTIFY] 📣 Incoming notifications request")
    print("=" * 60)
    print(f"[NOTIFY] Params: user_id={user_id} days={days}")

    # Normalize user_id: match Agent2 behavior for default users
    effective_user_id = user_id or "default-user"
    if effective_user_id == "default-user":
        effective_user_id = "84d559ab-1792-4387-aa30-06982c0d5dcc"
    print(f"[NOTIFY] 👤 Effective user_id: {effective_user_id}")

    start_dt = datetime.now()
    end_dt = start_dt + timedelta(days=days)
    print(f"[NOTIFY] 🗓️  Window: {start_dt.isoformat()} → {end_dt.isoformat()}")

    events = fetch_calendar_events(effective_user_id, start_dt, end_dt)
    print(f"[NOTIFY] 📦 Retrieved {len(events)} event(s) from DB")
    # Try to personalize with user's name
    user_name = _get_user_name(effective_user_id)

    notifications: List[Dict[str, Any]] = []
    for idx, ev in enumerate(events, 1):
        print(f"[NOTIFY] ── Event {idx} ───────────────────────────────────────")
        print(f"[NOTIFY]   title={ev.get('summary')} start={ev.get('start_datetime')} end={ev.get('end_datetime')} location={(ev.get('location') or '').strip()}")
        location = (ev.get("location") or "").strip()
        start_time = ev.get("start_datetime")
        wx = None
        if location and isinstance(start_time, datetime):
            try:
                wx = await get_weather_summary(location, start_time)
                if wx:
                    print(f"[NOTIFY]   🌤️  Weather: cond={wx.get('conditions')} temp={wx.get('temperature_c')}C precip={wx.get('precipitation_probability')}% wind={wx.get('wind_speed_kmh')}km/h")
                else:
                    print(f"[NOTIFY]   🌤️  Weather: unavailable for '{location}'")
            except Exception:
                print(f"[NOTIFY]   🌤️  Weather fetch raised; continuing without")
                wx = None

        message = await _generate_notification_text(ev, wx, user_name)
        print(f"[NOTIFY]   📝 Message ({len(message)} chars): {message}")

        notifications.append(
            {
                "title": ev.get("summary") or "Upcoming Event",
                "message": message,
                "start_datetime": ev.get("start_datetime"),
                "end_datetime": ev.get("end_datetime"),
                "location": ev.get("location"),
                "weather": wx,
            }
        )

    payload = {
        "count": len(notifications),
        "notifications": notifications,
        "window": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
    }
    print(f"[NOTIFY] ✅ Returning {payload['count']} notification(s)")
    return payload



def _is_routine_event(title: str | None) -> bool:
    """
    Heuristic filter for routine/recurring events we want to ignore in highlights.
    """
    if not title:
        return False
    t = title.strip().lower()
    routine_keywords = [
        "gym",
        "workout",
        "run",
        "standup",
        "stand-up",
        "daily",
        "weekly",
        "sync",
        "check-in",
        "check in",
        "1:1",
        "1-1",
        "one on one",
        "scrum",
        "planning",
        "retro",
        "retrospective",
        "review",
        "focus",
        "deep work",
        "lunch",
        "commute",
        "status",
        "catch up",
        "catch-up",
        "meeting",
        "team meeting",
        "stand up",
    ]
    return any(k in t for k in routine_keywords)


def _days_until(dt: datetime) -> int:
    today = datetime.now().date()
    return (dt.date() - today).days


def _fallback_highlight_message(events: List[Dict[str, Any]], user_name: Optional[str]) -> str:
    """
    Create a simple, actionable single-sentence reminder from special events.
    """
    first_name = _first_name(user_name)
    salutation = f"Hey {first_name}, " if first_name else ""

    if not events:
        return f"{salutation}no special events in the next 7 days."

    # Pick the most imminent event
    ev = sorted(events, key=lambda e: e.get("start_datetime"))[0]
    title = (ev.get("summary") or "an event").strip()
    start_dt = ev.get("start_datetime")
    in_days = None
    if isinstance(start_dt, datetime):
        in_days = _days_until(start_dt)

    lower = title.lower()
    suggestion = "get ready"
    if "birthday" in lower or "b'day" in lower or "bday" in lower:
        suggestion = "remember to buy a gift"
    elif "anniversary" in lower:
        suggestion = "plan something thoughtful"
    elif "wedding" in lower:
        suggestion = "arrange a gift and outfit"
    elif "flight" in lower or "travel" in lower or "trip" in lower:
        suggestion = "check in and pack essentials"
    elif "deadline" in lower or "submission" in lower:
        suggestion = "finish up and submit early"
    elif "interview" in lower:
        suggestion = "review your stories and portfolio"
    elif "doctor" in lower or "dentist" in lower or "medical" in lower or "appointment" in lower:
        suggestion = "bring ID/insurance and arrive early"
    elif "concert" in lower or "show" in lower or "game" in lower:
        suggestion = "charge your phone and sort transport"
    elif "party" in lower or "celebration" in lower:
        suggestion = "grab a small gift or snacks"
    elif "delivery" in lower:
        suggestion = "be available or leave instructions"

    when_part = ""
    if isinstance(in_days, int):
        if in_days == 0:
            when_part = "today"
        elif in_days == 1:
            when_part = "tomorrow"
        elif in_days > 1:
            when_part = f"in {in_days} days"

    if when_part:
        return f"{salutation}{title} {when_part} — {suggestion}."
    return f"{salutation}{title} is coming up — {suggestion}."


async def _generate_weekly_highlight_message(
    events: List[Dict[str, Any]],
    user_name: Optional[str],
) -> str:
    """
    Use the LLM to craft a single, warm, concise reminder focused on
    noteworthy events in the next 7 days. Falls back to heuristic.
    """
    # Prepare payload for LLM (only minimal, privacy-aware details)
    prepared: List[Dict[str, Any]] = []
    for ev in events:
        start_ts = ev.get("start_datetime")
        location = (ev.get("location") or "").strip()
        if isinstance(start_ts, datetime):
            prepared.append(
                {
                    "title": (ev.get("summary") or "").strip(),
                    "start_iso": start_ts.isoformat(),
                    "day": start_ts.strftime("%a"),
                    "in_days": _days_until(start_ts),
                    "location": location,
                }
            )
        else:
            prepared.append(
                {
                    "title": (ev.get("summary") or "").strip(),
                    "start_iso": str(start_ts),
                    "day": "",
                    "in_days": None,
                    "location": location,
                }
            )

    # If nothing to highlight, fallback immediately
    if not prepared:
        return _fallback_highlight_message([], user_name)

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatOpenAI(model="gpt-5", api_key=API_KEY, base_url=BASE_URL, temperature=1)
        system = SystemMessage(
            content=(
                "You are a helpful calendar assistant. From the user's next 7 days of events, "
                "identify only meaningful/non-routine items (e.g., birthdays, anniversaries, weddings, flights/travel, deadlines, "
                "interviews, ceremonies, parties, deliveries, medical). "
                "IGNORE routine items like gym, daily standups, recurring syncs, focus time, lunch, generic meetings. "
                "Write ONE short, warm, proactive notification focused on the most important upcoming special event. "
                "Include 1 specific helpful action (e.g., for a birthday: buy a gift). "
                "Keep it under 180 characters. No bullet points, no lists, no emojis."
            )
        )
        human_payload = {
            "user": {"name": user_name or ""},
            "window_days": 7,
            "events": prepared,
            "style": "one sentence, warm, practical, under 180 chars",
            "examples_to_ignore": [
                "gym", "workout", "standup", "daily", "weekly sync", "check-in",
                "1:1", "planning", "retro", "review", "focus", "lunch", "commute", "meeting"
            ],
        }
        human = HumanMessage(content=f"Create the single best notification:\n{human_payload}")
        print(f"[NOTIFY]   🤖 Invoking LLM for weekly highlight")
        response = llm.invoke([system, human])
        text = getattr(response, "content", None) or ""
        text = text.strip()
        if not text:
            return _fallback_highlight_message(events, user_name)
        if len(text) > 220:
            text = text[:217] + "..."
        return text
    except Exception as e:
        print(f"[NOTIFY]   ❌ LLM weekly highlight error: {e}")
        return _fallback_highlight_message(events, user_name)


@router.get("/api/notifications/highlights")
async def get_weekly_highlights(
    user_id: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """
    Return a single, smart weekly highlight notification that filters out routine items
    and focuses on special events (e.g., friend's birthday in 2 days — remember to buy a gift).
    """
    print("\n" + "=" * 60)
    print("[NOTIFY] 🌟 Incoming weekly highlights request")
    print("=" * 60)
    print(f"[NOTIFY] Params: user_id={user_id}")

    effective_user_id = user_id or "default-user"
    if effective_user_id == "default-user":
        effective_user_id = "84d559ab-1792-4387-aa30-06982c0d5dcc"
    print(f"[NOTIFY] 👤 Effective user_id: {effective_user_id}")

    start_dt = datetime.now()
    end_dt = start_dt + timedelta(days=7)
    print(f"[NOTIFY] 🗓️  Window: {start_dt.isoformat()} → {end_dt.isoformat()}")

    events = fetch_calendar_events(effective_user_id, start_dt, end_dt)
    print(f"[NOTIFY] 📦 Retrieved {len(events)} event(s) from DB")

    # Prefer non-routine events for highlights
    special_events = [ev for ev in events if not _is_routine_event(ev.get("summary"))]
    print(f"[NOTIFY] ✂️  Filtered to {len(special_events)} special event(s)")

    user_name = _get_user_name(effective_user_id)
    message = await _generate_weekly_highlight_message(special_events, user_name)
    print(f"[NOTIFY]   📝 Weekly highlight: {message}")

    payload = {
        "message": message,
        "special_event_count": len(special_events),
        "window": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        "special_events": [
            {
                "title": ev.get("summary"),
                "start_datetime": ev.get("start_datetime"),
                "location": ev.get("location"),
            }
            for ev in special_events[:5]
        ],
    }
    print(f"[NOTIFY] ✅ Returning weekly highlight")
    return payload

