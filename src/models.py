"""Shared state definitions and mock data for the thinkmoney customer service agent."""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State schema shared across all agent nodes in the graph.

    Attributes:
        messages: Conversation message history (auto-appended via add_messages reducer).
        current_agent: Name of the currently active agent node.
        user_info: Mock customer context (user_id, name, account_id, etc.).
    """

    messages: Annotated[list, add_messages]
    current_agent: str
    user_info: dict


# Mock customer identity used throughout the exercise.
# All mock tools reference this same customer for consistency.
MOCK_USER = {
    "user_id": "USR-2847",
    "name": "Sarah Johnson",
    "email": "sarah.j@email.com",
    "phone": "+44 7700 900123",
    "account_id": "ACC-9182",
    "primary_card_id": "CARD-5521",
    "address": "42 Kings Road, London, E1 7AZ",
    "account_type": "Premium",
    "member_since": "2023-03-15",
}
