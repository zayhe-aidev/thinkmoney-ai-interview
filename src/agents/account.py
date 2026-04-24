"""Account specialist agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools import ACCOUNT_TOOLS

_SYSTEM_PROMPT = (
    "You are the thinkmoney account specialist. Handle account details, balances, limits, and contact info updates. "
    "Do not handle card, payment, transaction, or KYC requests — those belong to other agents. "
    "Always confirm before updating contact information. Address the customer by first name."
)


def create_account_node(llm):
    """Create the account agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(ACCOUNT_TOOLS)

    def account_node(state):
        user_name = state.get("user_info", {}).get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"

        system = SystemMessage(content=_SYSTEM_PROMPT)
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "account"}

    return account_node
