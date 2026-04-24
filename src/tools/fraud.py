"""Fraud investigation tool for thinkmoney customer service."""

import json

from langchain_core.tools import tool


@tool
def flag_fraud_investigation(user_id: str, card_id: str, transaction_ids: str, summary: str) -> str:
    """Open a fraud investigation case combining card and transaction data.

    Args:
        user_id: The customer's user ID.
        card_id: The card ID involved in the fraud.
        transaction_ids: Comma-separated list of suspicious transaction IDs.
        summary: Plain-English description of the fraud situation.
    """
    case_id = f"FRAUD-{user_id[-4:]}-{card_id[-4:]}"
    return json.dumps({
        "case_id": case_id,
        "status": "open",
        "next_steps": "Our fraud team will review within 24 hours and contact you.",
    })
