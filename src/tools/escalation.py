"""Human escalation tool for thinkmoney customer service."""

import json

from langchain_core.tools import tool


@tool
def escalate_to_human(user_id: str, reason: str, conversation_summary: str) -> str:
    """Create a human support escalation ticket.

    Args:
        user_id: The customer's user ID.
        reason: Why the escalation is being raised.
        conversation_summary: Summary of the conversation so far for the human agent.
    """
    ticket_id = f"TM-HMN-{user_id[-4:]}"
    return json.dumps({
        "ticket_id": ticket_id,
        "estimated_wait": "under 5 minutes",
        "message": "You're being connected to a team member now.",
    })
