"""Mock card management tools for thinkmoney customer service."""

import json
from datetime import datetime

from langchain_core.tools import tool


@tool
def list_cards(user_id: str) -> str:
    """List all cards (physical and virtual) associated with a customer's account.

    Args:
        user_id: The customer's user ID.
    """
    return json.dumps({
        "user_id": user_id,
        "cards": [
            {
                "card_id": "CARD-5521",
                "type": "physical",
                "scheme": "Visa Debit",
                "variant": "Metal (Premium)",
                "last_four": "4821",
                "status": "active",
                "frozen": False,
                "expiry": "09/28",
                "contactless_enabled": True,
                "daily_limit": "£15,000",
            },
            {
                "card_id": "CARD-8834",
                "type": "virtual",
                "scheme": "Visa Debit",
                "variant": "Standard",
                "last_four": "7203",
                "status": "active",
                "frozen": False,
                "expiry": "12/27",
                "contactless_enabled": False,
                "daily_limit": "£5,000",
            },
        ],
    })


@tool
def freeze_card(card_id: str) -> str:
    """Freeze a card immediately, blocking all transactions. Can be unfrozen later.

    Args:
        card_id: The card ID to freeze (e.g. CARD-5521).
    """
    return json.dumps({
        "success": True,
        "card_id": card_id,
        "status": "frozen",
        "frozen_at": datetime.now().isoformat(),
        "message": "Card has been frozen. No transactions will be authorised until the card is unfrozen.",
    })


@tool
def unfreeze_card(card_id: str) -> str:
    """Unfreeze a previously frozen card, restoring normal transaction capability.

    Args:
        card_id: The card ID to unfreeze.
    """
    return json.dumps({
        "success": True,
        "card_id": card_id,
        "status": "active",
        "unfrozen_at": datetime.now().isoformat(),
        "message": "Card has been unfrozen and is now active for transactions.",
    })


@tool
def order_replacement_card(user_id: str, card_id: str, reason: str, delivery: str = "standard") -> str:
    """Order a replacement for a lost, stolen, or damaged card.

    Args:
        user_id: The customer's user ID.
        card_id: The card ID to replace.
        reason: Reason for replacement — one of 'lost', 'stolen', 'damaged', 'expired'.
        delivery: Delivery speed — 'standard' (5-7 days, free) or 'express' (1-2 days, £10).
    """
    fee = "£0.00" if delivery == "standard" else "£10.00"
    days = "5-7 business days" if delivery == "standard" else "1-2 business days"

    result = {
        "success": True,
        "user_id": user_id,
        "old_card_id": card_id,
        "new_card_id": "CARD-9917",
        "reason": reason,
        "delivery": delivery,
        "fee": fee,
        "estimated_delivery": days,
        "tracking_ref": "TM-REPL-20260324-001",
        "message": f"Replacement card ordered ({delivery} delivery, {days}). "
                   f"Old card has been cancelled. Fee: {fee}.",
    }

    if reason in ("lost", "stolen"):
        result["old_card_status"] = "cancelled"
        result["message"] += " We recommend monitoring your recent transactions for any unauthorised activity."

    return json.dumps(result)


@tool
def get_card_status(card_id: str) -> str:
    """Get detailed status information for a specific card.

    Args:
        card_id: The card ID to check.
    """
    cards = {
        "CARD-5521": {
            "card_id": "CARD-5521",
            "type": "physical",
            "scheme": "Visa Debit",
            "variant": "Metal (Premium)",
            "last_four": "4821",
            "status": "active",
            "frozen": False,
            "expiry": "09/28",
            "contactless_enabled": True,
            "pin_set": True,
            "apple_pay_enrolled": True,
            "google_pay_enrolled": False,
            "last_used": "2026-03-23T18:42:00Z",
            "last_used_merchant": "Tesco Express",
        },
        "CARD-8834": {
            "card_id": "CARD-8834",
            "type": "virtual",
            "scheme": "Visa Debit",
            "variant": "Standard",
            "last_four": "7203",
            "status": "active",
            "frozen": False,
            "expiry": "12/27",
            "contactless_enabled": False,
            "pin_set": False,
            "apple_pay_enrolled": False,
            "google_pay_enrolled": False,
            "last_used": "2026-03-20T11:05:00Z",
            "last_used_merchant": "Amazon.co.uk",
        },
    }

    if card_id in cards:
        return json.dumps(cards[card_id])

    return json.dumps({
        "error": f"Card {card_id} not found.",
        "suggestion": "Use list_cards to see available cards.",
    })
