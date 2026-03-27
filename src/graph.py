"""Main agent graph definition.

The triage agent is fully wired. Sub-agents need to be added by the candidate.
Study the triage wiring to understand the pattern.
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage

from src.models import AgentState
from src.agents.triage import create_triage_node, TRIAGE_TOOLS

# Import your sub-agent creators and tool groups here.


def _make_route_target_fn(agent_map: dict[str, str]):
    """Create a routing function that knows about registered agents.

    Args:
        agent_map: Dict mapping agent names to graph node names.

    Returns:
        A routing function for use with add_conditional_edges.
    """

    def _get_route_target(state: AgentState) -> str:
        """Extract the routing target from triage tool calls.

        Returns node name to route to, or END if no tool calls.
        """
        last_message = state["messages"][-1]

        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return END

        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "route_to_agent":
                agent_name = tool_call["args"].get("agent_name", "")

                if agent_name in agent_map:
                    return agent_map[agent_name]

                # Agent not registered — route to unavailable handler
                return "unavailable_agent"

        # Any other tool call (e.g. search_knowledge_base) goes to triage_tools
        return "triage_tools"

    return _get_route_target


def _handle_unavailable_agent(state: AgentState) -> dict:
    """Handle routing to an agent that hasn't been implemented yet.

    Creates a ToolMessage telling triage the requested agent is not available,
    so triage can inform the customer honestly.
    """
    last_message = state["messages"][-1]

    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "route_to_agent":
            agent_name = tool_call["args"].get("agent_name", "unknown")
            return {
                "messages": [
                    ToolMessage(
                        content=f"Error: The '{agent_name}' agent is not available. "
                                "This specialist capability has not been implemented yet. "
                                "Please let the customer know and offer to help with what you can do "
                                "(knowledge base search and account lookup).",
                        tool_call_id=tool_call["id"],
                    )
                ],
            }

    return {"messages": []}


def _route_from_subagent(state: AgentState) -> str:
    """Route after a sub-agent responds.

    If the sub-agent made tool calls, route to its tool node.
    Otherwise, return to triage.

    This is a helper you can use (or adapt) for your sub-agents.
    """
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        current = state.get("current_agent", "triage")
        return f"{current}_tools"

    return "triage"


def build_graph(llm):
    """Build and compile the thinkmoney customer service agent graph.

    Args:
        llm: A LangChain chat model instance.

    Returns:
        A compiled LangGraph that can be invoked with AgentState.
    """
    # agent_map: maps triage routing names → graph node names
    agent_map: dict[str, str] = {}

    # available_agents: tells triage which agents exist and what they do
    # (populates the system prompt so triage only routes to real agents)
    available_agents: dict[str, str] = {}

    graph = StateGraph(AgentState)

    # --- Triage agent (PROVIDED) ---
    triage_node = create_triage_node(llm, available_agents=available_agents or None)
    graph.add_node("triage", triage_node)

    # --- Triage tool execution ---
    triage_tool_node = ToolNode(TRIAGE_TOOLS)
    graph.add_node("triage_tools", triage_tool_node)

    # --- Unavailable agent handler ---
    graph.add_node("unavailable_agent", _handle_unavailable_agent)

    # Add your sub-agent nodes here.

    # --- Entry point ---
    graph.set_entry_point("triage")

    # --- Triage routing ---
    _get_route_target = _make_route_target_fn(agent_map)
    graph.add_conditional_edges("triage", _get_route_target)
    graph.add_edge("triage_tools", "triage")
    graph.add_edge("unavailable_agent", "triage")

    # Add your sub-agent edges here.
    # Study the triage wiring above for the pattern.

    return graph.compile()
