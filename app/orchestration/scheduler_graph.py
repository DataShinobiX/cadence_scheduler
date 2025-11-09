from langgraph.graph import StateGraph, END
from app.orchestration.state import AgentState
from app.orchestration.agent_adapters import (
    Agent1Adapter,
    Agent2Adapter,
    Agent3Adapter,
    Agent4Adapter,
)


# --- 1. Initialize Agent Adapters ---
# These adapters connect your agents to the AgentState format
agent1 = Agent1Adapter()
agent2 = Agent2Adapter()
agent3 = Agent3Adapter()
agent4 = Agent4Adapter()


def task_decomposer_node(state: AgentState) -> AgentState:
    """Agent 1: Task Decomposer"""
    print("=" * 60)
    print("ORCHESTRATOR: Calling Agent 1 (Task Decomposer)")
    print("=" * 60)
    return agent1.execute(state)


def scheduler_brain_node(state: AgentState) -> AgentState:
    """Agent 2: Scheduler Brain"""
    print("=" * 60)
    print("ORCHESTRATOR: Calling Agent 2 (Scheduler Brain)")
    print("=" * 60)
    return agent2.execute(state)


def calendar_integrator_node(state: AgentState) -> AgentState:
    """Agent 3: Calendar Integrator"""
    print("=" * 60)
    print("ORCHESTRATOR: Calling Agent 3 (Calendar Integrator)")
    print("=" * 60)
    return agent3.execute(state)


def meal_recommendation_node(state: AgentState) -> AgentState:
    """Agent 4: Meal Recommendation Advisor"""
    print("=" * 60)
    print("ORCHESTRATOR: Calling Agent 4 (Meal Recommendation Advisor)")
    print("=" * 60)
    return agent4.execute(state)


def ask_user_node(state: AgentState) -> AgentState:
    """
    This node handles conflict resolution.
    Since we don't have a real user feedback mechanism, we:
    1. Log the conflicts for the user to see
    2. Mark that we need to stop retrying after max attempts
    3. Return state to allow graceful exit
    """
    print("--- ORCHESTRATOR: Conflict resolution node. ---")
    print(f"--- Conflicts to show user: {state['conflicts']}")

    # Since there's no real user feedback mechanism implemented,
    # we'll mark that conflicts should be shown to user in the response
    # The routing logic will handle max retry limits
    state["show_conflicts_to_user"] = True

    return state


# --- 2. Define the Conditional Logic ---
# This function decides *where to go* after the 'scheduler_brain' node.
# It reads the "clipboard" (state) to make its decision.
def route_after_scheduling(state: AgentState) -> str:
    """
    Reads the state and decides the next step.
    This is the "conditional edge" from your documentation.
    """
    print("--- ORCHESTRATOR: Making decision... ---")

    # Check if max retries exceeded
    max_conflict_retries = 3
    conflict_attempts = state.get("conflict_resolution_attempts", 0)

    if conflict_attempts >= max_conflict_retries:
        print(f"--- ORCHESTRATOR: Max retries ({max_conflict_retries}) exceeded. Proceeding with partial results. ---")
        # Reset needs_user_input to break the loop
        state["needs_user_input"] = False
        return "integrate"

    if state.get("needs_user_input", False):
        print(f"--- ORCHESTRATOR: Decision: Conflicts found (attempt {conflict_attempts + 1}/{max_conflict_retries}), asking user. ---")
        # Increment retry counter
        state["conflict_resolution_attempts"] = conflict_attempts + 1
        return "ask_user"  # This string must match a node name
    else:
        print("--- ORCHESTRATOR: Decision: No conflicts, integrating calendar. ---")
        return "integrate"  # This string must match a node name


# --- 3. Build the Graph ---
def create_scheduler_graph():
    """
    This function builds the complete agent workflow.
    """

    # Initialize the graph and tell it what "clipboard" (State) to use.
    workflow = StateGraph(AgentState)

    # --- 4. Add Nodes ---
    # Give each agent function a unique name in the graph.
    workflow.add_node("decompose", task_decomposer_node)
    workflow.add_node("schedule", scheduler_brain_node)
    workflow.add_node("integrate", calendar_integrator_node)
    workflow.add_node("meal_advisor", meal_recommendation_node)
    workflow.add_node("ask_user", ask_user_node)

    # --- 5. Add Edges ---
    # Set the starting point
    workflow.set_entry_point("decompose")

    # "Happy Path" Edges
    # After 'decompose' finishes, *always* go to 'schedule'.
    workflow.add_edge("decompose", "schedule")

    # After 'integrate' (Agent 3) finishes, the flow is *done*.
    workflow.add_edge("integrate", "meal_advisor")
    workflow.add_edge("meal_advisor", END)

    # Conditional Edge
    # After 'schedule' (Agent 2) finishes, call our routing function
    # to decide where to go next.
    workflow.add_conditional_edges(
        "schedule",  # The node to start from
        route_after_scheduling,  # The function that makes the decision
        {
            # The possible return values from our function and
            # which node to go to.
            "ask_user": "ask_user",
            "integrate": "integrate"
        }
    )

    # Conflict Loop Edge
    # As per SOLUTION_ARCHITECTURE.md, after the user provides input
    # (at the 'ask_user' node), we loop *back* to the 'schedule' node
    # to try again with the new information.
    workflow.add_edge("ask_user", "schedule")

    # --- 6. Compile the Graph ---
    # This finalizes the workflow
    print("--- ORCHESTRATOR: Compiling graph... ---")
    app = workflow.compile()
    print("--- ORCHESTRATOR: Graph compiled successfully! ---")
    return app

# You will then import this `create_scheduler_graph` function
# in your main FastAPI file (`app/main.py`) to be used.
# Main scheduling workflow