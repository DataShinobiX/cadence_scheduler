"""
Orchestrator Module
Central controller for running the multi-agent scheduling workflow
"""

from typing import Dict, Any
from app.orchestration.state import AgentState
from app.orchestration.scheduler_graph import create_scheduler_graph


class SchedulingOrchestrator:
    """
    Central orchestrator for the intelligent scheduling system.
    Manages the execution of Agent 1 → Agent 2 → Agent 3 workflow.
    """

    def __init__(self):
        """Initialize the orchestrator with the LangGraph workflow"""
        print("[ORCHESTRATOR] Initializing scheduler graph...")
        self.scheduler_graph = create_scheduler_graph()
        print("[ORCHESTRATOR] Graph initialized successfully!")

    def run(self, state: AgentState) -> AgentState:
        """
        Execute the complete agent orchestration workflow.

        Args:
            state: Initial AgentState with user_id, session_id, raw_transcript

        Returns:
            Final AgentState with all agent outputs

        Workflow:
            1. Agent 1 (Task Decomposer): raw_transcript → decomposed_tasks
            2. Agent 2 (Scheduler Brain): decomposed_tasks → scheduling_plan + conflicts
            3. Agent 3 (Calendar Integrator): scheduling_plan → scheduled_events (Google Calendar)
        """
        print("\n" + "=" * 70)
        print("[ORCHESTRATOR] Starting agent workflow...")
        print("=" * 70)
        print(f"[ORCHESTRATOR] Session: {state.get('session_id')}")
        print(f"[ORCHESTRATOR] User: {state.get('user_id')}")
        print(f"[ORCHESTRATOR] Transcript: {state.get('raw_transcript', '')[:100]}...")

        try:
            # Execute the LangGraph workflow
            final_state = self.scheduler_graph.invoke(state)

            # Log summary
            print("\n" + "=" * 70)
            print("[ORCHESTRATOR] ✅ Workflow Complete!")
            print("=" * 70)
            self._log_summary(final_state)

            return final_state

        except Exception as e:
            print(f"\n[ORCHESTRATOR] ❌ Workflow failed: {e}")
            import traceback
            traceback.print_exc()

            # Add error to state
            state["errors"].append(f"Orchestration failed: {str(e)}")
            return state

    def _log_summary(self, state: AgentState):
        """Log a summary of the orchestration results"""
        num_tasks = len(state.get("decomposed_tasks", []))
        num_scheduled = len(state.get("scheduling_plan", []))
        num_conflicts = len(state.get("conflicts", []))
        num_events = len(state.get("scheduled_events", []))
        num_meal_recs = len(state.get("meal_recommendations", []))
        errors = state.get("errors", [])

        print(f"[ORCHESTRATOR] 📊 Results:")
        print(f"[ORCHESTRATOR]   Tasks Decomposed: {num_tasks}")
        print(f"[ORCHESTRATOR]   Tasks Scheduled: {num_scheduled}")
        print(f"[ORCHESTRATOR]   Conflicts: {num_conflicts}")
        print(f"[ORCHESTRATOR]   Calendar Events Created: {num_events}")
        print(f"[ORCHESTRATOR]   Meal Recommendations: {num_meal_recs}")

        if errors:
            print(f"[ORCHESTRATOR] ⚠️  Errors: {len(errors)}")
            for i, error in enumerate(errors, 1):
                print(f"[ORCHESTRATOR]     {i}. {error}")

        if state.get("needs_user_input"):
            print(f"[ORCHESTRATOR] ⚠️  User input required for conflict resolution")


# Global singleton instance (initialized once, reused across requests)
_orchestrator_instance = None


def get_orchestrator() -> SchedulingOrchestrator:
    """
    Get the global orchestrator instance (singleton pattern).
    Ensures the LangGraph is only compiled once.
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SchedulingOrchestrator()
    return _orchestrator_instance


def run_orchestration(state: AgentState) -> AgentState:
    """
    Convenience function to run orchestration.
    This is the main entry point for running the agent workflow.

    Args:
        state: Initial AgentState with user_id, session_id, raw_transcript

    Returns:
        Final AgentState with all agent outputs
    """
    orchestrator = get_orchestrator()
    return orchestrator.run(state)
