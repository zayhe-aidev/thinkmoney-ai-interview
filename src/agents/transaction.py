"""Transaction specialist agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools import TRANSACTION_TOOLS

_SYSTEM_PROMPT = (
    "You are the thinkmoney transaction specialist. Handle transaction history, details, and disputes. "
    "Always retrieve transaction details before filing a dispute. "
    "Valid dispute reasons: unauthorised, goods_not_received, duplicate_charge, incorrect_amount, other. "
    "Do not handle card or payment operations."
)


def create_transaction_node(llm):
    """Create the transaction agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(TRANSACTION_TOOLS)

    def transaction_node(state):
        user_name = state.get("user_info", {}).get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"

        system = SystemMessage(content=_SYSTEM_PROMPT)
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "transaction"}

    return transaction_node
