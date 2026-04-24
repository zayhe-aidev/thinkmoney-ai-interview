"""KYC specialist agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools import KYC_TOOLS

_SYSTEM_PROMPT_TEMPLATE = (
    "You are the thinkmoney KYC specialist. Handle identity verification status, required documents, "
    "document submission, and account restrictions. Speak reassuringly. "
    "Do not handle payments, cards, or transactions.\n\n"
    "Customer context — use this information directly, do not ask the customer to repeat it:\n"
    "- Name: {first_name}\n"
    "- User ID: {user_id}\n"
    "- Account ID: {account_id}\n"
    "- Primary Card ID: {primary_card_id}\n\n"
    "Always address the customer as {first_name}. Always pass {user_id} to any tool that requires a user_id argument."
)


def create_kyc_node(llm):
    """Create the KYC agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(KYC_TOOLS)

    def kyc_node(state):
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
        return {"messages": [response], "current_agent": "kyc"}

    return kyc_node
