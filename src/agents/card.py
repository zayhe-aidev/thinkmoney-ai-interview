"""Card specialist agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools import CARD_TOOLS

_SYSTEM_PROMPT = (
    "You are the thinkmoney card specialist. Handle card freezing, unfreezing, replacements, and status checks. "
    "For lost or stolen cards, freeze immediately then offer replacement. "
    "Do not handle transactions, payments, or KYC. Always confirm the card ID before acting."
)


def create_card_node(llm):
    """Create the card agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(CARD_TOOLS)

    def card_node(state):
        user_name = state.get("user_info", {}).get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"

        system = SystemMessage(content=_SYSTEM_PROMPT)
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "card"}

    return card_node
