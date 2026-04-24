"""HITL escalation agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools.escalation import escalate_to_human

HITL_TOOLS = [escalate_to_human]

_SYSTEM_PROMPT = (
    "You are the thinkmoney escalation specialist. Call escalate_to_human immediately. "
    "Acknowledge the customer's frustration empathetically. "
    "Provide the ticket reference and wait time. "
    "Do not attempt to resolve the issue yourself."
)


def create_hitl_node(llm):
    """Create the HITL escalation agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(HITL_TOOLS)

    def hitl_node(state):
        user_name = state.get("user_info", {}).get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"

        system = SystemMessage(content=_SYSTEM_PROMPT)
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "hitl"}

    return hitl_node
