"""Main agent graph definition.

The triage agent is fully wired. Sub-agents need to be added by the candidate.
Study the triage wiring to understand the pattern.
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage

from src.models import AgentState
from src.tools.sentiment import make_detect_tone_tool
from src.agents.triage import create_triage_node, TRIAGE_TOOLS
from src.agents.account import create_account_node
from src.agents.card import create_card_node
from src.agents.transaction import create_transaction_node
from src.agents.payment import create_payment_node
from src.agents.kyc import create_kyc_node
from src.agents.conflict_resolver import create_conflict_resolver_node
from src.agents.hitl import create_hitl_node
from src.tools import ACCOUNT_TOOLS, CARD_TOOLS, TRANSACTION_TOOLS, PAYMENT_TOOLS, KYC_TOOLS
from src.tools.fraud import flag_fraud_investigation
from src.tools.escalation import escalate_to_human
from src.tools.cards import freeze_card
from src.tools.transactions import get_transaction_history, dispute_transaction
from src.tools.account import get_account_status


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

        tool_names = [tc["name"] for tc in last_message.tool_calls]

        # If detect_tone hasn't run yet but route_to_agent is present,
        # force triage_tools to run detect_tone first
        if "route_to_agent" in tool_names and "detect_tone" in tool_names:
            return "triage_tools"

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
    agent_map: dict[str, str] = {
        "account": "account_agent",
        "card": "card_agent",
        "transaction": "transaction_agent",
        "payment": "payment_agent",
        "kyc": "kyc_agent",
        "conflict": "conflict_resolver",
        "hitl": "hitl_escalation",
    }

    # available_agents: tells triage which agents exist and what they do
    # (populates the system prompt so triage only routes to real agents)
    available_agents: dict[str, str] = {
        "account": "Account details, balances, spending limits, and contact information updates",
        "card": "Card freezing, unfreezing, replacement orders, and card status checks",
        "transaction": "Transaction history, transaction details, dispute filing, and dispute status",
        "payment": "Transfers to saved payees, exchange rates, standing orders",
        "kyc": "KYC verification status, required documents, document submission, account restrictions",
        "conflict": "Cross-domain issues such as fraud requiring simultaneous card and transaction actions",
        "hitl": "Human agent escalation for frustrated customers or complex unresolved issues",
    }

    graph = StateGraph(AgentState)

    # --- Triage agent (PROVIDED) ---
    triage_node = create_triage_node(llm, available_agents=available_agents or None)
    graph.add_node("triage", triage_node)

    # --- Triage tool execution ---
    detect_tone_tool = make_detect_tone_tool(llm)
    triage_tool_node = ToolNode(TRIAGE_TOOLS + [detect_tone_tool])
    graph.add_node("triage_tools", triage_tool_node)

    # --- Unavailable agent handler ---
    graph.add_node("unavailable_agent", _handle_unavailable_agent)

    # --- Domain agent nodes ---
    graph.add_node("account_agent", create_account_node(llm))
    graph.add_node("card_agent", create_card_node(llm))
    graph.add_node("transaction_agent", create_transaction_node(llm))
    graph.add_node("payment_agent", create_payment_node(llm))
    graph.add_node("kyc_agent", create_kyc_node(llm))
    graph.add_node("conflict_resolver", create_conflict_resolver_node(llm))
    graph.add_node("hitl_escalation", create_hitl_node(llm))

    # --- Tool nodes ---
    graph.add_node("account_tools", ToolNode(ACCOUNT_TOOLS))
    graph.add_node("card_tools", ToolNode(CARD_TOOLS))
    graph.add_node("transaction_tools", ToolNode(TRANSACTION_TOOLS))
    graph.add_node("payment_tools", ToolNode(PAYMENT_TOOLS))
    graph.add_node("kyc_tools", ToolNode(KYC_TOOLS))
    graph.add_node("conflict_resolver_tools", ToolNode([freeze_card, get_transaction_history, dispute_transaction, get_account_status, flag_fraud_investigation]))
    graph.add_node("hitl_tools", ToolNode([escalate_to_human]))

    # --- Entry point ---
    graph.set_entry_point("triage")

    # --- Triage routing ---
    _get_route_target = _make_route_target_fn(agent_map)
    triage_targets = {"triage_tools": "triage_tools", "unavailable_agent": "unavailable_agent", END: END}
    triage_targets.update({v: v for v in agent_map.values()})
    graph.add_conditional_edges("triage", _get_route_target, triage_targets)
    graph.add_edge("triage_tools", "triage")
    graph.add_edge("unavailable_agent", "triage")

    # --- Sub-agent edges (5 domain agents + conflict resolver follow the simple pattern) ---
    for name in ["account_agent", "card_agent", "transaction_agent", "payment_agent", "kyc_agent", "conflict_resolver"]:
        tools_node = f"{name.replace('_agent', '')}_tools"
        graph.add_conditional_edges(name, _route_from_subagent, {tools_node: tools_node, "triage": "triage"})
        graph.add_edge(tools_node, name)

    # hitl uses 'hitl_tools' not 'hitl_escalation_tools', so wired manually
    graph.add_conditional_edges("hitl_escalation", _route_from_subagent, {"hitl_tools": "hitl_tools", "triage": "triage"})
    graph.add_edge("hitl_tools", "hitl_escalation")

    return graph.compile()
