"""HITL escalation agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools.escalation import escalate_to_human

HITL_TOOLS = [escalate_to_human]

_SYSTEM_PROMPT_TEMPLATE = (
    "You are the thinkmoney escalation specialist. Call escalate_to_human immediately. "
    "Acknowledge the customer's frustration empathetically. "
    "Provide the ticket reference and wait time. "
    "Do not attempt to resolve the issue yourself.\n\n"
    "Customer context — use this information directly, do not ask the customer to repeat it:\n"
    "- Name: {first_name}\n"
    "- User ID: {user_id}\n"
    "- Account ID: {account_id}\n"
    "- Primary Card ID: {primary_card_id}\n\n"
    "Always address the customer as {first_name}. Pass {user_id} to escalate_to_human."
)


def create_hitl_node(llm):
    """Create the HITL escalation agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(HITL_TOOLS)

    def hitl_node(state):
        user_info = state.get("user_info", {})
        user_name = user_info.get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"
        system = SystemMessage(content=_SYSTEM_PROMPT_TEMPLATE.format(
            first_name=first_name,
            user_id=user_info.get("user_id", "unknown"),
            account_id=user_info.get("account_id", "unknown"),
            primary_card_id=user_info.get("primary_card_id", "unknown"),
        ))
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "hitl"}

    return hitl_node
