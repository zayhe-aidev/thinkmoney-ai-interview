"""KYC specialist agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools import KYC_TOOLS

_SYSTEM_PROMPT = (
    "You are the thinkmoney KYC specialist. Handle identity verification status, required documents, "
    "document submission, and account restrictions. Speak reassuringly. "
    "Do not handle payments, cards, or transactions."
)


def create_kyc_node(llm):
    """Create the KYC agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(KYC_TOOLS)

    def kyc_node(state):
        user_name = state.get("user_info", {}).get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"

        system = SystemMessage(content=_SYSTEM_PROMPT)
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "kyc"}

    return kyc_node
