"""Payment specialist agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools import PAYMENT_TOOLS

_SYSTEM_PROMPT = (
    "You are the thinkmoney payment specialist. Handle transfers to saved payees, exchange rates, and standing orders. "
    "Always confirm amount, payee, and currency before initiating a transfer. State fees explicitly. "
    "You cannot add new payees. Do not handle card or account operations."
)


def create_payment_node(llm):
    """Create the payment agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(PAYMENT_TOOLS)

    def payment_node(state):
        user_name = state.get("user_info", {}).get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"

        system = SystemMessage(content=_SYSTEM_PROMPT)
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "payment"}

    return payment_node
