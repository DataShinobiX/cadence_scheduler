"""
Agent Adapters
These wrappers adapt the individual agents to work with the AgentState format
"""

from typing import Dict, Any
from datetime import datetime
import os

from app.orchestration.state import AgentState
from app.agents.task_decomposer import TaskDecomposerLLM, OpenAIClient
from app.agents.scheduler_brain import schedule_tasks_for_next_seven_days


class Agent1Adapter:
    """
    Adapter for TaskDecomposerLLM to work with AgentState
    """

    def __init__(self):
        # Initialize the OpenAI client with the same credentials as transcribe.py
        # NOTE: Using hardcoded values to match transcribe.py configuration
        api_key = "sk-aU7KLAifP85EWxg4J7NFJg"
        base_url = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
        model = "gpt-4.1-mini"

        llm_client = OpenAIClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.0
        )

        self.agent = TaskDecomposerLLM(llm=llm_client, tz="UTC")

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute Agent 1: Task Decomposer

        Input (from state):
        - raw_transcript: str

        Output (updates state):
        - decomposed_tasks: List[Dict]
        - extracted_contacts: List[str]
        - time_phrases: List[str]
        """
        print("\n[AGENT 1] Task Decomposer starting...")
        print(f"[AGENT 1] Transcript: {state['raw_transcript'][:100]}...")

        try:
            # Prepare input for the agent
            agent_input = {
                "raw_transcript": state["raw_transcript"],
                "now": datetime.utcnow().isoformat(),
                "context": {}  # Could include user preferences later
            }

            # Execute the agent
            result = self.agent.execute(agent_input)

            # Update state with results
            state["decomposed_tasks"] = result.get("decomposed_tasks", [])
            state["current_agent"] = "Agent 1 Complete"

            print(f"[AGENT 1] ✅ Decomposed {len(state['decomposed_tasks'])} tasks")
            for i, task in enumerate(state['decomposed_tasks'], 1):
                print(f"  {i}. {task.get('title')} - Priority: {task.get('priority')} ({task.get('priority_num')})")

        except Exception as e:
            error_msg = f"Agent 1 failed: {str(e)}"
            print(f"[AGENT 1] ❌ {error_msg}")
            state["errors"].append(error_msg)

        return state


class Agent2Adapter:
    """
    Adapter for SchedulerBrainAgent to work with AgentState
    """

    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        """Check if a string is a valid UUID"""
        try:
            import uuid
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError, TypeError):
            return False

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute Agent 2: Scheduler Brain

        Input (from state):
        - decomposed_tasks: List[Dict]
        - user_preferences: Dict
        - user_id: str

        Output (updates state):
        - scheduling_plan: List[Dict]
        - conflicts: List[Dict]
        - needs_user_input: bool
        """
        print("\n[AGENT 2] Scheduler Brain starting...")

        try:
            # Get tasks from state
            decomposed_tasks = state.get("decomposed_tasks", [])

            if not decomposed_tasks:
                error_msg = "No tasks to schedule"
                print(f"[AGENT 2] ⚠️ {error_msg}")
                state["errors"].append(error_msg)
                state["needs_user_input"] = False
                return state

            print(f"[AGENT 2] Scheduling {len(decomposed_tasks)} tasks...")

            # Prepare preferences with user_id
            preferences = state.get("user_preferences", {}).copy()

            # Use a valid test UUID if user_id is "default-user" or invalid
            user_id = state.get("user_id", "default-user")
            if user_id == "default-user" or not self._is_valid_uuid(user_id):
                # Use a test UUID that exists in the database or will gracefully fail
                user_id = "84d559ab-1792-4387-aa30-06982c0d5dcc"
                print(f"[AGENT 2] Using test UUID for default user: {user_id}")

            preferences["user_id"] = user_id

            # Add default preferences if not provided
            if "work_hours_start" not in preferences:
                preferences["work_hours_start"] = "09:00"
            if "work_hours_end" not in preferences:
                preferences["work_hours_end"] = "18:00"
            if "lunch_time_start" not in preferences:
                preferences["lunch_time_start"] = "13:00"
            if "lunch_duration_minutes" not in preferences:
                preferences["lunch_duration_minutes"] = 60

            print(f"[AGENT 2] Using preferences: {preferences}")

            # Call the scheduler
            result = schedule_tasks_for_next_seven_days(
                tasks=decomposed_tasks,
                preferences=preferences
            )

            # Update state with results
            state["scheduling_plan"] = result.get("scheduled_plan", [])
            state["conflicts"] = result.get("conflicts", [])
            state["needs_user_input"] = result.get("needs_user_input", False)
            state["current_agent"] = "Agent 2 Complete"

            print(f"[AGENT 2] ✅ Scheduled {len(state['scheduling_plan'])} tasks")
            print(f"[AGENT 2] ⚠️ Found {len(state['conflicts'])} conflicts")

            if state["scheduling_plan"]:
                print(f"[AGENT 2] Scheduled tasks:")
                for task in state["scheduling_plan"]:
                    print(f"  - {task.get('description')} at {task.get('start_time')}")

            if state["conflicts"]:
                print(f"[AGENT 2] Conflicts:")
                for conflict in state["conflicts"]:
                    print(f"  - {conflict.get('task')}: {conflict.get('reason')}")

        except Exception as e:
            error_msg = f"Agent 2 failed: {str(e)}"
            print(f"[AGENT 2] ❌ {error_msg}")
            state["errors"].append(error_msg)
            state["needs_user_input"] = False

        return state


class Agent3Adapter:
    """
    Adapter for Calendar Integrator (to be implemented)
    For now, this is a placeholder
    """

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute Agent 3: Calendar Integrator

        Input (from state):
        - scheduling_plan: List[Dict]

        Output (updates state):
        - scheduled_events: List[str] (Google Calendar event IDs)
        """
        print("\n[AGENT 3] Calendar Integrator starting...")
        print("[AGENT 3] ⚠️ Not yet implemented - using placeholder")

        # For now, just mark as complete without actually creating calendar events
        state["scheduled_events"] = []
        state["current_agent"] = "Agent 3 Complete"

        print(f"[AGENT 3] ✅ Would create {len(state.get('scheduling_plan', []))} calendar events")

        return state
