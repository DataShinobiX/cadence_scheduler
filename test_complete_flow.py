#!/usr/bin/env python3
"""
Test Complete Flow: Transcript → Agent 1 → Agent 2 → Results
This simulates the complete pipeline without audio
"""

from app.orchestration.state import create_initial_state
from app.orchestration.scheduler_graph import create_scheduler_graph
import json
import uuid


def test_complete_pipeline():
    """
    Test the complete flow from transcript to scheduling
    """

    print("=" * 80)
    print("TESTING COMPLETE INTELLIGENT SCHEDULER PIPELINE")
    print("=" * 80)
    print()

    # Sample transcript (what would come from audio transcription)
    transcript = """
    I need to meet Bob at 2 PM downtown to discuss the budget.
    I also have to finish the Prosus pitch deck by end of day today.
    And I want to go to the gym after 5 PM.
    """

    print("📝 Input Transcript:")
    print("-" * 80)
    print(transcript.strip())
    print("-" * 80)
    print()

    # Step 3: Initialize AgentState
    session_id = str(uuid.uuid4())
    user_id = "test-user-123"

    state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        raw_transcript=transcript,
        user_preferences={
            "work_hours_start": "09:00",
            "work_hours_end": "18:00",
            "lunch_time_start": "13:00",
            "lunch_duration_minutes": 60,
            "most_productive_time": "morning"
        }
    )

    print("✅ Step 3: Session initialized")
    print(f"   Session ID: {session_id}")
    print(f"   User ID: {user_id}")
    print()

    # Steps 4-6: Run orchestration
    print("🚀 Running Agent Orchestration...")
    print()

    try:
        # Create and execute the workflow
        scheduler_graph = create_scheduler_graph()
        final_state = scheduler_graph.invoke(state)

        print()
        print("=" * 80)
        print("✅ ORCHESTRATION COMPLETE - RESULTS")
        print("=" * 80)
        print()

        # Display results
        print("📊 AGENT 1 OUTPUT: Task Decomposition")
        print("-" * 80)
        decomposed_tasks = final_state.get("decomposed_tasks", [])
        if decomposed_tasks:
            for i, task in enumerate(decomposed_tasks, 1):
                print(f"{i}. {task.get('title')}")
                print(f"   Kind: {task.get('kind')}")
                print(f"   Duration: {task.get('duration_minutes')} min")
                print(f"   Priority: {task.get('priority')} ({task.get('priority_num')})")
                if task.get('constraints'):
                    print(f"   Constraints: {', '.join(task.get('constraints'))}")
                print()
        else:
            print("   (No tasks decomposed)")
        print()

        print("📅 AGENT 2 OUTPUT: Scheduling Plan")
        print("-" * 80)
        scheduling_plan = final_state.get("scheduling_plan", [])
        if scheduling_plan:
            for i, scheduled in enumerate(scheduling_plan, 1):
                print(f"{i}. {scheduled.get('description')}")
                print(f"   Date: {scheduled.get('date')}")
                print(f"   Time: {scheduled.get('start_time')} - {scheduled.get('end_time')}")
                print(f"   Duration: {scheduled.get('duration_minutes')} min")
                if scheduled.get('location'):
                    print(f"   Location: {scheduled.get('location')}")
                print()
        else:
            print("   (No tasks scheduled)")
        print()

        # Display conflicts if any
        conflicts = final_state.get("conflicts", [])
        if conflicts:
            print("⚠️  CONFLICTS DETECTED")
            print("-" * 80)
            for i, conflict in enumerate(conflicts, 1):
                print(f"{i}. Task: {conflict.get('task')}")
                print(f"   Reason: {conflict.get('reason')}")
                print(f"   Suggestion: {conflict.get('suggestion')}")
                print()
        else:
            print("✅ NO CONFLICTS")
            print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Tasks Found: {len(decomposed_tasks)}")
        print(f"Tasks Scheduled: {len(scheduling_plan)}")
        print(f"Conflicts: {len(conflicts)}")
        print(f"Needs User Input: {final_state.get('needs_user_input', False)}")
        print()

        if final_state.get("errors"):
            print("❌ ERRORS:")
            for error in final_state["errors"]:
                print(f"   - {error}")
            print()

        # Full state (for debugging)
        print("🔍 FULL STATE (JSON):")
        print("-" * 80)
        print(json.dumps({
            "session_id": final_state.get("session_id"),
            "user_id": final_state.get("user_id"),
            "decomposed_tasks": decomposed_tasks,
            "scheduling_plan": scheduling_plan,
            "conflicts": conflicts,
            "needs_user_input": final_state.get("needs_user_input"),
            "errors": final_state.get("errors", [])
        }, indent=2))
        print("-" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR IN ORCHESTRATION")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_complete_pipeline()
