"""Conflict resolver agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools.account import get_account_status
from src.tools.cards import freeze_card
from src.tools.fraud import flag_fraud_investigation
from src.tools.transactions import dispute_transaction, get_transaction_history

CONFLICT_TOOLS = [freeze_card, get_transaction_history, dispute_transaction, get_account_status, flag_fraud_investigation]

_SYSTEM_PROMPT = (
    "You are the thinkmoney conflict resolver. Handle cross-domain issues such as fraud that require "
    "card and transaction actions simultaneously. Freeze the card first, then pull transaction history, "
    "then dispute unauthorised transactions, then open a fraud investigation. "
    "Keep the customer informed at each step."
)


def create_conflict_resolver_node(llm):
    """Create the conflict resolver agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(CONFLICT_TOOLS)

    def conflict_resolver_node(state):
        user_name = state.get("user_info", {}).get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"

        system = SystemMessage(content=_SYSTEM_PROMPT)
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "conflict_resolver"}

    return conflict_resolver_node
