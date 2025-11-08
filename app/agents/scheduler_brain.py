from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, List, Dict
import json
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Tuple
from uuid import uuid4
import os
from datetime import timezone


@dataclass
class Task:
    # Core identifiers
    id: str = field(default_factory=lambda: str(uuid4()))
    kind: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    # Time and duration
    duration_minutes: Optional[int] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    deadline: Optional[datetime] = None
    # Scheduling metadata
    priority: Optional[str] = None
    priority_num: int = 3  # e.g., 1 (high) to 5 (low)
    location: Optional[str] = None
    category: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    contacts: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    confidence: Optional[float] = None
    # Metadata for advanced scoring
    metadata: Dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: Dict) -> "Task":
        """
        Create a Task from a decomposed task JSON object as in app/agents/test_tasks.json.
        """
        def _parse_dt(value: Optional[str]) -> Optional[datetime]:
            if not value:
                return None
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return None

        def _infer_priority_num(priority_label: Optional[str], fallback: int = 3) -> int:
            if not priority_label:
                return fallback
            mapping = {
                "highest": 1,
                "very high": 1,
                "high": 1,
                "medium": 3,
                "normal": 3,
                "low": 5,
                "very low": 5,
                "lowest": 5,
            }
            # Normalize label
            label = str(priority_label).strip().lower()
            return mapping.get(label, fallback)

        title = data.get("title")
        description = data.get("description") or title
        start_dt = _parse_dt(data.get("start"))
        end_dt = _parse_dt(data.get("end"))
        # Normalize to naive (UTC) if timezone-aware
        if start_dt and start_dt.tzinfo is not None:
            start_dt = start_dt.astimezone(timezone.utc).replace(tzinfo=None)
        if end_dt and end_dt.tzinfo is not None:
            end_dt = end_dt.astimezone(timezone.utc).replace(tzinfo=None)
        # Default duration if not provided to ensure scheduling can proceed
        inferred_duration = data.get("duration_minutes") if data.get("duration_minutes") is not None else 60

        # Priority fields: accept both "priority" (label) and "priority_num" (1-5)
        priority_label = data.get("priority")
        priority_num_raw = data.get("priority_num")
        if priority_num_raw is None:
            inferred_priority_num = _infer_priority_num(priority_label, 3)
        else:
            try:
                inferred_priority_num = int(priority_num_raw)
            except (TypeError, ValueError):
                inferred_priority_num = _infer_priority_num(priority_label, 3)

        return cls(
            kind=data.get("kind"),
            title=title,
            description=description,
            duration_minutes=inferred_duration,
            start=start_dt,
            end=end_dt,
            # Treat 'end' as a soft deadline if provided
            deadline=end_dt,
            priority=priority_label,
            priority_num=inferred_priority_num,
            location=data.get("location"),
            category=data.get("category"),
            constraints=data.get("constraints") or [],
            contacts=data.get("contacts") or [],
            notes=data.get("notes"),
            confidence=data.get("confidence"),
            metadata={}
        )


def load_tasks_from_json() -> List[Task]:
    """
    Load decomposed tasks from app/agents/test_tasks.json and convert to Task objects.
    """
    json_path = os.path.join(os.path.dirname(__file__), "test_tasks.json")
    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    decomposed = payload.get("decomposed_tasks", [])
    return [Task.from_json(item) for item in decomposed]

@dataclass
class CalendarEvent:
    summary: str
    start: datetime
    end: datetime
    is_movable: bool = False
    is_external: bool = True # Assume events from calendar are external by default

@dataclass
class TimeSlot:
    start: datetime
    end: datetime
    available: bool = True

@dataclass
class SchedulingConflict:
    task: Task
    conflict_type: str
    conflicting_events: List[CalendarEvent]
    resolution_options: List[Dict]

@dataclass
class SchedulingResult:
    scheduled_tasks: List[Dict]
    conflicts: List[SchedulingConflict]
    needs_user_input: bool


def call_llm(prompt: str, context: Dict) -> str:
    """Call OpenAI via LangChain to choose the best slot; fallback to heuristic."""
    import logging
    import os
    logger = logging.getLogger(__name__)

    logger.info("Initializing SchedulerBrainAgent")

    model_name = "gpt-5-mini"

    # Load system prompt from prompts/scheduler.txt (co-located with this file)
    def _load_scheduler_system_prompt() -> str:
        path = os.path.join(os.path.dirname(__file__), "prompts", "scheduler.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            logger.info("Failed to load system prompt, defaulting to empty %s", exc)
            return ""

    system_prompt = _load_scheduler_system_prompt()

    api_key = "sk-aU7KLAifP85EWxg4J7NFJg"
    base_url = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
    temperature = 0.2

    try:
        # Match user's example signature exactly
        logger.info("Initializing LLM")
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )
    except Exception as exc:
        logger.info("Failed to initialize LLM, falling back to heuristic %s", exc)
        llm = None

    logger.info(
        "SchedulerBrainAgent initialized: llm_available=%s model=%s",
        bool(llm),
        model_name,
    )

    # Fallback heuristic if LLM unavailable
    if llm is None:
        return json.dumps(
            {
                "best_slot_id": "slot_a",
                "reasoning": "Heuristic fallback: chose earliest available slot.",
            }
        )

    # Prepare messages and invoke the model
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        human_content = (
            f"{prompt.strip()}\n\n"
            f"CONTEXT (JSON):\n{json.dumps(context, default=str)}"
        )
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_content),
            ]
        )
        # Expecting JSON string per prompt contract
        content = getattr(response, "content", None)
        if not content:
            content = str(response)
        return content
    except Exception as exc:
        logger.info("LLM invocation failed, falling back to heuristic %s", exc)
        return json.dumps(
            {
                "best_slot_id": "slot_a",
                "reasoning": "Heuristic fallback after LLM error: earliest slot.",
            }
        )


def llm_choose_best_slot(
    task: 'Task', 
    candidates: List[List['TimeSlot']], 
    preferences: Dict, 
    already_scheduled: List[Dict]
) -> Optional[List['TimeSlot']]:
    """
    Uses an LLM to choose the best slot from a list of candidates.
    """
    prompt = """
    You are an expert scheduling assistant. Your goal is to select the single best time slot for a given task by analyzing the user's preferences and the context of their day.

    Analyze the provided TASK, the CANDIDATE SLOTS, the USER PREFERENCES, and the tasks ALREADY SCHEDULED today.

    Based on all this context, choose the optimal slot. Consider factors like:
    - Matching task energy requirements with the user's productive times.
    - Grouping tasks by category or location to minimize context switching.
    - Placing tasks with deadlines appropriately.
    - Respecting implicit preferences (e.g., exercise after work).
    - STRICTLY RESPECT the task's explicit constraints (e.g., "after 5pm", "by EOD on 2025-11-10", "time flexible"). Do not select a slot that violates any constraint.

    Respond ONLY with a JSON object containing the 'best_slot_id' and a brief 'reasoning'. If multiple slots satisfy constraints, pick the earliest feasible one.
    """

    # Format the candidate slots for the LLM
    candidate_context = []
    for i, window in enumerate(candidates):
        slot_id = f"slot_{chr(97 + i)}" # slot_a, slot_b, etc.
        candidate_context.append({
            "id": slot_id,
            "start_time": window[0].start.isoformat(),
            "end_time": window[-1].end.isoformat()
        })
    
    context = {
        "task": task.__dict__,
        "constraints": getattr(task, "constraints", []),
        "user_preferences": preferences,
        "already_scheduled": already_scheduled,
        "candidate_slots": candidate_context,
        "today": datetime.now().date().isoformat()
    }
    
    response_str = call_llm(prompt, context)
    try:
        response_json = json.loads(response_str)
        best_id = response_json.get('best_slot_id')
        reasoning = response_json.get('reasoning')
        if reasoning:
            print(f"LLM Reasoning: {reasoning}")
        # If no best_id returned (e.g., no feasible slot), signal no selection
        if not best_id or not isinstance(best_id, str) or not best_id.startswith("slot_"):
            return None
        
        # Find the original slot window that corresponds to the chosen ID
        parts = best_id.split('_')
        if len(parts) != 2 or not parts[1]:
            return None
        letter = parts[1][0].lower()
        if not ('a' <= letter <= 'z'):
            return None
        chosen_index = ord(letter) - 97
        if chosen_index < 0 or chosen_index >= len(candidates):
            return None
        return candidates[chosen_index]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError) as e:
        print(f"Error parsing LLM response, defaulting to first candidate. Error: {e}")
        return candidates[0]


def get_existing_calendar(user_id: str, date_range: Tuple[datetime, datetime]) -> List[CalendarEvent]:
    """
    MOCK: Fetches all calendar events for the user within a date range.
    In a real application, this would query a database or a Calendar API.
    """
    print(f"Fetching calendar for user {user_id} between {date_range[0].isoformat()} and {date_range[1].isoformat()}...")
    
    # Let's create some sample events for testing
    today = date_range[0].date()
    
    mock_events = [
        CalendarEvent(
            summary="Dentist Appointment",
            start=datetime.combine(today, time(10, 0)),
            end=datetime.combine(today, time(10, 45)),
            is_movable=False
        ),
        CalendarEvent(
            summary="Team Standup",
            start=datetime.combine(today, time(14, 0)),
            end=datetime.combine(today, time(14, 30)),
            is_movable=False,
            is_external=True
        ),
        CalendarEvent(
            summary="Focus Work (can be moved)",
            start=datetime.combine(today, time(11, 30)),
            end=datetime.combine(today, time(13, 0)),
            is_movable=True
        )
    ]
    
    # Filter events that are within the requested date_range
    return [
        event for event in mock_events 
        if event.start >= date_range[0] and event.end <= date_range[1]
    ]


def get_existing_calendar_from_db(user_id: str, date_range: Tuple[datetime, datetime]) -> List[CalendarEvent]:
    """
    DB: Fetches all calendar events for the user within a date range.
    Uses repository in app/db/calendar_events.py to query PostgreSQL.
    """
    from app.db.calendar_events import fetch_calendar_events

    start_dt, end_dt = date_range
    rows = fetch_calendar_events(user_id, start_dt, end_dt)
    events: List[CalendarEvent] = []

    for row in rows:
        events.append(
            CalendarEvent(
                summary=(row.get("summary") or "").strip(),
                start=row.get("start_datetime"),
                end=row.get("end_datetime"),
                is_movable=bool(row.get("is_movable", True)),
                is_external=bool(row.get("is_external", True)),
            )
        )

    return events


def test_step_1():
    print("\n--- Testing Step 1: Get Existing Calendar ---")
    user_id = "84d559ab-1792-4387-aa30-06982c0d5dcc"
    today = datetime.now()
    start_dt = datetime.combine(today, time.min)
    end_dt = datetime.combine(today + timedelta(days=7), time.max)
    
    # events = get_existing_calendar(user_id, (start_of_day, end_of_day))
    events = get_existing_calendar_from_db(user_id, (start_dt, end_dt))
    
    print(f"Found {len(events)} events:")
    for event in events:
        print(f"- {event.summary} from {event.start.strftime('%H:%M')} to {event.end.strftime('%H:%M')} (Movable: {event.is_movable})")


# scheduler_agent.py (append this code to the existing file)

# --- Step 2: Build Availability Matrix ---

def initialize_day_slots(day: date, slot_duration_minutes: int = 15) -> List[TimeSlot]:
    """Creates a list of empty, available TimeSlots for an entire day."""
    slots = []
    start_of_day = datetime.combine(day, time.min)
    end_of_day = datetime.combine(day, time.max)
    current_time = start_of_day
    
    while current_time < end_of_day:
        slot_end_time = current_time + timedelta(minutes=slot_duration_minutes)
        slots.append(TimeSlot(start=current_time, end=slot_end_time))
        current_time = slot_end_time
        
    return slots

def mark_slots_unavailable(slots: List[TimeSlot], start_block: datetime, end_block: datetime):
    """Marks slots that overlap with a given time block as unavailable."""
    for slot in slots:
        # Check for overlap: (SlotStart < BlockEnd) and (SlotEnd > BlockStart)
        if slot.start < end_block and slot.end > start_block:
            slot.available = False

def apply_preferences(slots: List[TimeSlot], preferences: Dict):
    """Marks slots as unavailable based on user preferences."""
    # Example: Block time outside of work hours
    work_start = time.fromisoformat(preferences.get("work_hours_start", "09:00"))
    work_end = time.fromisoformat(preferences.get("work_hours_end", "17:00"))
    
    for slot in slots:
        slot_time = slot.start.time()
        if not (work_start <= slot_time < work_end):
            slot.available = False
            
    # Example: Block lunch time
    lunch_start = datetime.combine(slots[0].start.date(), time.fromisoformat(preferences.get("lunch_time_start", "13:00")))
    lunch_end = lunch_start + timedelta(minutes=preferences.get("lunch_duration_minutes", 60))
    mark_slots_unavailable(slots, lunch_start, lunch_end)


def build_availability_matrix(
    target_date: date,
    existing_events: List[CalendarEvent],
    preferences: Dict
) -> List[TimeSlot]:
    """
    Builds a list of time slots for a given day, marking availability
    based on existing events and user preferences.
    """
    # 1. Initialize all slots as available
    slots = initialize_day_slots(target_date, slot_duration_minutes=15)
    
    # 2. Apply user preferences (work hours, lunch)
    apply_preferences(slots, preferences)

    # 3. Mark existing events as unavailable
    for event in existing_events:
        # Only consider events on the target date
        if event.start.date() == target_date:
            mark_slots_unavailable(slots, event.start, event.end)

    return slots

# --- Test for Step 2 ---
def test_step_2():
    print("\n--- Testing Step 2: Build Availability Matrix ---")
    # Setup mock data
    user_id = "user-123"
    today = datetime.now().date()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)
    
    events = get_existing_calendar(user_id, (start_of_day, end_of_day))
    prefs = {
        "work_hours_start": "09:00",
        "work_hours_end": "17:30",
        "lunch_time_start": "13:00",
        "lunch_duration_minutes": 60
    }
    
    availability_slots = build_availability_matrix(today, events, prefs)
    
    print(f"Availability for {today}:")
    # Show a few examples
    for slot in availability_slots:
        slot_time = slot.start.strftime("%H:%M")
        if "09:00" <= slot_time < "11:00": # Check around the dentist appointment
             print(f"Slot {slot_time}-{slot.end.strftime('%H:%M')}: Available = {slot.available}")
        if "12:45" <= slot_time < "14:15": # Check around lunch and team standup
             print(f"Slot {slot_time}-{slot.end.strftime('%H:%M')}: Available = {slot.available}")


# --- Step 3 & 4: Intelligent Scheduling & Conflict Handling ---

def find_candidate_slots(
    task: Task, 
    availability: List[TimeSlot], 
    slot_duration_minutes: int = 15
) -> List[List[TimeSlot]]:
    """
    Finds all contiguous blocks of available slots that are long enough for the task.
    """
    required_slots_count = -(-task.duration_minutes // slot_duration_minutes)  # Ceiling division
    candidate_windows = []

    for i in range(len(availability) - required_slots_count + 1):
        window = availability[i : i + required_slots_count]
        if all(slot.available for slot in window):
            candidate_windows.append(window)
            
    return candidate_windows


def schedule_tasks_intelligently(
    tasks: List[Task],
    availability: List[TimeSlot],
    preferences: Dict
) -> Dict:
    """The main scheduling algorithm, now powered by an LLM for decisions."""
    
    def _to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    sorted_tasks = sorted(tasks, key=lambda t: (t.priority_num, _to_naive_utc(t.deadline) or datetime.max))

    scheduled_tasks = []
    conflicts = []

    for task in sorted_tasks:
        candidates = find_candidate_slots(task, availability)

        if not candidates:
            conflicts.append({
                "task": task.description,
                "reason": f"No available time slots found for the required duration of {task.duration_minutes} minutes.",
                "suggestion": "Consider shortening the task, moving other events, or scheduling on another day."
            })
            continue

        # ----------------------------------------------------
        # NEW: Instead of scoring, we ask the LLM to choose.
        # ----------------------------------------------------
        print(f"\nAsking LLM to choose best slot for: '{task.description}'")
        best_slot_window = llm_choose_best_slot(task, candidates, preferences, scheduled_tasks)
        if best_slot_window is None:
            conflicts.append({
                "task": task.description,
                "reason": "LLM could not identify a feasible slot that satisfies constraints and availability.",
                "suggestion": "Expand the scheduling window, adjust constraints, or provide alternative times."
            })
            continue
        
        start_time = best_slot_window[0].start
        end_time = best_slot_window[-1].end
        
        scheduled_tasks.append({
            "task_id": task.id,
            "description": task.description,
            "category": task.category,
            "date": start_time.date().isoformat(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": task.duration_minutes,
            "location": task.location,
        })

        mark_slots_unavailable(availability, start_time, end_time)

    return {
        "scheduled_plan": scheduled_tasks,
        "conflicts": conflicts,
        "needs_user_input": len(conflicts) > 0
    }

# --- Test for Step 3 & 4 ---
def test_step_3_and_4():
    print("\n--- Testing Step 3 & 4: Intelligent Scheduling ---")
    
    # --- Setup mock data ---
    user_id = "84d559ab-1792-4387-aa30-06982c0d5dcc"
    today = datetime.now().date()
    start_dt = datetime.combine(today, time.min)
    end_dt = datetime.combine(today + timedelta(days=7), time.max)
    
    # Get calendar and build availability
    # events = get_existing_calendar(user_id, (start_dt, end_dt))
    events = get_existing_calendar_from_db(user_id, (start_dt, end_dt))
    print(f"Found {len(events)} events:")
    for event in events:
        print(f"- {event.summary} from {event.start.strftime('%H:%M')} to {event.end.strftime('%H:%M')} (Movable: {event.is_movable})")
    prefs = {
        "work_hours_start": "09:00",
        "work_hours_end": "18:00",
        "lunch_time_start": "13:00",
        "lunch_duration_minutes": 60,
        "most_productive_time": "morning"
    }
    availability_slots = build_availability_matrix(today, events, prefs)
    
    # Define tasks to be scheduled by loading from JSON
    tasks_to_schedule = load_tasks_from_json()
    
    # --- Run the scheduler ---
    result = schedule_tasks_intelligently(tasks_to_schedule, availability_slots, prefs)
    
    # --- Print the results ---
    print("\n--- SCHEDULING RESULT ---")
    print(json.dumps(result, indent=2))
    

# Update the main execution block
if __name__ == "__main__":
    test_step_1()
    test_step_2()
    test_step_3_and_4()

def schedule_tasks_for_next_seven_days(
    tasks: List[Dict] | List[Task],
    preferences: Dict
) -> Dict:
    """
    Orchestrator-facing API.
    
    - Accepts tasks (either list of dicts in decomposed form or List[Task])
    - Accepts user preferences dict (should include 'user_id' if using DB-backed availability)
    - Internally fetches the user's calendar availability for the next 7 days
    - Returns the scheduling result dict with keys:
        { 'scheduled_plan': [...], 'conflicts': [...], 'needs_user_input': bool }
    """
    # Normalize tasks to Task objects
    normalized_tasks: List[Task] = []
    for t in tasks:
        if isinstance(t, Task):
            normalized_tasks.append(t)
        elif isinstance(t, dict):
            normalized_tasks.append(Task.from_json(t))
        else:
            raise TypeError("Each task must be a Task or dict")
    
    # Determine user_id for DB-backed calendar fetch. Fall back to test UUID if absent.
    user_id = preferences.get("user_id") or "84d559ab-1792-4387-aa30-06982c0d5dcc"
    
    # Compute 7-day range starting today
    today = datetime.now().date()
    start_dt = datetime.combine(today, time.min)
    end_dt = datetime.combine(today + timedelta(days=7), time.max)
    
    # Fetch existing events from DB within the 7-day range
    events = get_existing_calendar_from_db(user_id, (start_dt, end_dt))
    
    # Build availability across the next 7 days and flatten
    availability: List[TimeSlot] = []
    for day_offset in range(0, 7):
        target_date = today + timedelta(days=day_offset)
        day_slots = build_availability_matrix(target_date, events, preferences)
        availability.extend(day_slots)
    
    # Run the scheduler
    return schedule_tasks_intelligently(normalized_tasks, availability, preferences)