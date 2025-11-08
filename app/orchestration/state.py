"""
AgentState Definition
This is the shared state that flows between all agents in the LangGraph workflow
"""

from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime


class AgentState(TypedDict):
    """
    Shared state for all agents in the scheduling workflow.
    This state is passed between agents and updated by each one.
    """

    # ==================== User Context ====================
    user_id: str                    # User identifier
    session_id: str                 # Unique session ID for this request
    raw_transcript: str             # Original speech-to-text output

    # ==================== Agent 1 Output ====================
    decomposed_tasks: List[Dict[str, Any]]  # Tasks broken down by Agent 1

    # ==================== Agent 2 Output ====================
    scheduling_plan: List[Dict[str, Any]]   # Scheduled tasks from Agent 2
    conflicts: List[Dict[str, Any]]         # Detected scheduling conflicts
    needs_user_input: bool                  # Whether user needs to resolve conflicts
    user_feedback: Optional[str]            # User's conflict resolution choice

    # ==================== Agent 3 Output ====================
    scheduled_events: List[str]             # Google Calendar event IDs

    # ==================== Shared Context ====================
    existing_calendar: List[Dict[str, Any]] # Current calendar state
    user_preferences: Dict[str, Any]        # User preferences for scheduling
    conversation_history: List[str]         # Chat history for context

    # ==================== Error Handling ====================
    errors: List[str]                       # Any errors encountered
    current_agent: Optional[str]            # Currently executing agent

    # ==================== Metadata ====================
    created_at: Optional[str]               # When this session started
    updated_at: Optional[str]               # Last update time


def create_initial_state(
    user_id: str,
    session_id: str,
    raw_transcript: str,
    user_preferences: Optional[Dict[str, Any]] = None
) -> AgentState:
    """
    Create an initial AgentState for a new scheduling request.
    """
    return AgentState(
        user_id=user_id,
        session_id=session_id,
        raw_transcript=raw_transcript,
        decomposed_tasks=[],
        scheduling_plan=[],
        conflicts=[],
        scheduled_events=[],
        needs_user_input=False,
        user_feedback=None,
        existing_calendar=[],
        user_preferences=user_preferences or {},
        conversation_history=[],
        errors=[],
        current_agent=None,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
