"""Conflict resolver agent for thinkmoney customer service."""

from langchain_core.messages import SystemMessage

from src.agents.utils import prepare_messages
from src.tools.account import get_account_status
from src.tools.cards import freeze_card
from src.tools.fraud import flag_fraud_investigation
from src.tools.transactions import dispute_transaction, get_transaction_history

CONFLICT_TOOLS = [freeze_card, get_transaction_history, dispute_transaction, get_account_status, flag_fraud_investigation]

_SYSTEM_PROMPT_TEMPLATE = (
    "You are the thinkmoney conflict resolver. Handle cross-domain issues such as fraud that require "
    "card and transaction actions simultaneously. Freeze the card first, then pull transaction history, "
    "then dispute unauthorised transactions, then open a fraud investigation. "
    "Keep the customer informed at each step.\n\n"
    "Customer context — use this information directly, do not ask the customer to repeat it:\n"
    "- Name: {first_name}\n"
    "- User ID: {user_id}\n"
    "- Account ID: {account_id}\n"
    "- Primary Card ID: {primary_card_id}\n\n"
    "Always address the customer as {first_name}. Always pass {user_id} to any tool that requires a user_id argument. "
    "Use {primary_card_id} as the default card to freeze if the customer does not specify one."
)


def create_conflict_resolver_node(llm):
    """Create the conflict resolver agent node for use in a LangGraph StateGraph."""
    llm_with_tools = llm.bind_tools(CONFLICT_TOOLS)

    def conflict_resolver_node(state):
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
        return {"messages": [response], "current_agent": "conflict_resolver"}

    return conflict_resolver_node
