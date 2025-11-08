from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, List, Dict
import json
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Tuple


@dataclass
class Task:
    id: str
    description: str
    duration_minutes: int
    priority: int  # e.g., 1 (high) to 5 (low)
    deadline: Optional[datetime] = None
    location: Optional[str] = None
    category: Optional[str] = None
    # Metadata for advanced scoring
    metadata: Dict = field(default_factory=dict) 

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
) -> List['TimeSlot']:
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

    Respond ONLY with a JSON object containing the 'best_slot_id' and a brief 'reasoning'.
    """

    # Format the candidate slots for the LLM
    candidate_context = []
    for i, window in enumerate(candidates):
        slot_id = f"slot_{chr(97 + i)}" # slot_a, slot_b, etc.
        candidate_context.append({
            "id": slot_id,
            "start_time": window[0].start,
            "end_time": window[-1].end
        })
    
    context = {
        "task": task.__dict__,
        "user_preferences": preferences,
        "already_scheduled": already_scheduled,
        "candidate_slots": candidate_context
    }

    print(f"ca")
    
    response_str = call_llm(prompt, context)
    try:
        response_json = json.loads(response_str)
        best_id = response_json['best_slot_id']
        print(f"LLM Reasoning: {response_json['reasoning']}")
        
        # Find the original slot window that corresponds to the chosen ID
        chosen_index = ord(best_id.split('_')[1]) - 97
        return candidates[chosen_index]
    except (json.JSONDecodeError, KeyError, IndexError) as e:
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


def test_step_1():
    print("\n--- Testing Step 1: Get Existing Calendar ---")
    user_id = "user-123"
    today = datetime.now()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)
    
    events = get_existing_calendar(user_id, (start_of_day, end_of_day))
    
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

# scheduler_agent.py (append this code)

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


# def calculate_slot_score(
#     task: Task, 
#     slot_window: List[TimeSlot], 
#     preferences: Dict, 
#     already_scheduled: List[Dict]
# ) -> int:
#     """
#     Multi-factor scoring function as described in the prompt.
#     """
#     score = 100  # Start with a base score
#     start_time = slot_window[0].start

#     # Factor 1: Time preference match (example: gym in evening)
#     if task.category == "exercise" and start_time.hour >= 17:
#         score += 20
    
#     # Factor 2: Energy-task match
#     if task.metadata.get("energy_required") == "high":
#         productive_time = preferences.get("most_productive_time", "morning")
#         if productive_time == "morning" and start_time.hour < 12:
#             score += 15
#         elif productive_time == "afternoon" and 12 <= start_time.hour < 17:
#             score += 15

#     # Factor 3: Minimize context switching (group similar tasks)
#     if already_scheduled:
#         last_task = already_scheduled[-1]
#         # Check if the new task is close in time to the last one and has the same category
#         last_task_end_time = datetime.fromisoformat(last_task['end_time'])
#         time_gap_minutes = (start_time - last_task_end_time).total_seconds() / 60
#         if last_task.get("category") == task.category and time_gap_minutes <= 30:
#             score += 10

#     # Factor 4: Deadline urgency
#     if task.deadline:
#         time_until_deadline = (task.deadline - start_time).total_seconds() / 3600
#         if time_until_deadline < 24:
#             score += 30  # High urgency
#         elif time_until_deadline < 72:
#             score += 10 # Medium urgency

#     return score

# def schedule_tasks_intelligently(
#     tasks: List[Task],
#     availability: List[TimeSlot],
#     preferences: Dict
# ) -> Dict:
#     """The main scheduling algorithm."""
    
#     # 1. Sort tasks by priority and then by deadline
#     sorted_tasks = sorted(
#         tasks,
#         key=lambda t: (t.priority, t.deadline or datetime.max)
#     )

#     scheduled_tasks = []
#     conflicts = []

#     for task in sorted_tasks:
#         # 2. Find all possible candidate slots
#         candidates = find_candidate_slots(task, availability)

#         if not candidates:
#             # CONFLICT: No available slots of the required duration
#             conflicts.append({
#                 "task": task.description,
#                 "reason": f"No available time slots found for the required duration of {task.duration_minutes} minutes.",
#                 "suggestion": "Consider shortening the task, moving other events, or scheduling on another day."
#             })
#             continue

#         # 3. Score each candidate slot
#         scored_candidates = []
#         for slot_window in candidates:
#             score = calculate_slot_score(task, slot_window, preferences, scheduled_tasks)
#             scored_candidates.append({"window": slot_window, "score": score})
        
#         # 4. Select the best slot (highest score)
#         best_candidate = max(scored_candidates, key=lambda x: x['score'])
#         best_slot_window = best_candidate['window']
        
#         # 5. Schedule the task
#         start_time = best_slot_window[0].start
#         end_time = best_slot_window[-1].end
        
#         scheduled_tasks.append({
#             "task_id": task.id,
#             "description": task.description,
#             "category": task.category,
#             "date": start_time.date().isoformat(),
#             "start_time": start_time.isoformat(),
#             "end_time": end_time.isoformat(),
#             "duration_minutes": task.duration_minutes,
#             "location": task.location,
#         })

#         # 6. Update availability matrix
#         mark_slots_unavailable(availability, start_time, end_time)

#     return {
#         "scheduled_plan": scheduled_tasks,
#         "conflicts": conflicts,
#         "needs_user_input": len(conflicts) > 0
#     }



def schedule_tasks_intelligently(
    tasks: List[Task],
    availability: List[TimeSlot],
    preferences: Dict
) -> Dict:
    """The main scheduling algorithm, now powered by an LLM for decisions."""
    
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (t.priority, t.deadline or datetime.max)
    )

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
    user_id = "user-123"
    today = datetime.now().date()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)
    
    # Get calendar and build availability
    events = get_existing_calendar(user_id, (start_of_day, end_of_day))
    prefs = {
        "work_hours_start": "09:00",
        "work_hours_end": "18:00",
        "lunch_time_start": "13:00",
        "lunch_duration_minutes": 60,
        "most_productive_time": "morning"
    }
    availability_slots = build_availability_matrix(today, events, prefs)
    
    # Define tasks to be scheduled
    tasks_to_schedule = [
        Task(
            id="task-1",
            description="Draft Q4 report",
            duration_minutes=90,
            priority=1, # High priority
            category="work",
            metadata={"energy_required": "high"}
        ),
        Task(
            id="task-2",
            description="Team Brainstorm Session Prep",
            duration_minutes=45,
            priority=2,
            category="work",
            metadata={"energy_required": "medium"}
        ),
        Task(
            id="task-3",
            description="Go for a run",
            duration_minutes=60,
            priority=3,
            category="exercise"
        ),
        Task( # This task should cause a conflict
            id="task-4",
            description="Plan entire 2025 company strategy",
            duration_minutes=300, # 5 hours
            priority=1,
            category="work",
            metadata={"energy_required": "high"}
        )
    ]
    
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