from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime


class AgentState(TypedDict, total=False):
    # User context
    user_id: str
    session_id: str
    raw_transcript: str

    # Agent 1: Task Decomposer output
    decomposed_tasks: List[Dict[str, Any]]

    # Agent 2: Scheduler Brain output
    scheduling_plan: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    needs_user_input: bool
    user_feedback: Optional[str]

    # Agent 3: Calendar Integrator output
    scheduled_events: List[str]

    # Shared context
    existing_calendar: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    conversation_history: List[str]

    # Error handling
    errors: List[str]

# AgentState definition
