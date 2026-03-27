"""Mock account management tools for thinkmoney customer service."""

import json

from langchain_core.tools import tool


@tool
def get_account_details(user_id: str) -> str:
    """Look up a customer's account details including name, email, account type, and status.

    Args:
        user_id: The customer's user ID (e.g. USR-2847).
    """
    return json.dumps({
        "user_id": user_id,
        "name": "Sarah Johnson",
        "email": "sarah.j@email.com",
        "phone": "+44 7700 900123",
        "address": "42 Kings Road, London, E1 7AZ",
        "account_id": "ACC-9182",
        "account_type": "Premium",
        "status": "active",
        "balance": {
            "GBP": "2,450.00",
            "EUR": "350.00",
            "USD": "0.00",
        },
        "verification_level": "full",
        "member_since": "2023-03-15",
    })


@tool
def get_account_limits(user_id: str) -> str:
    """Get the current spending and withdrawal limits for a customer's account.

    Args:
        user_id: The customer's user ID.
    """
    return json.dumps({
        "user_id": user_id,
        "account_type": "Premium",
        "limits": {
            "daily_spending": {"limit": "£15,000", "used_today": "£320.50"},
            "monthly_spending": {"limit": "£50,000", "used_this_month": "£4,812.30"},
            "daily_atm_withdrawal": {"limit": "£500", "used_today": "£0.00"},
            "single_transfer": {"limit": "£25,000"},
            "fee_free_exchange_remaining": "£720.00 of £1,000/month",
        },
    })


@tool
def update_contact_info(user_id: str, field: str, new_value: str) -> str:
    """Update a customer's contact information (email, phone, or address).

    Args:
        user_id: The customer's user ID.
        field: The field to update — one of 'email', 'phone', or 'address'.
        new_value: The new value for the field.
    """
    valid_fields = {"email", "phone", "address"}
    if field not in valid_fields:
        return json.dumps({
            "success": False,
            "error": f"Invalid field '{field}'. Must be one of: {', '.join(valid_fields)}",
        })

    return json.dumps({
        "success": True,
        "user_id": user_id,
        "field": field,
        "old_value": {
            "email": "sarah.j@email.com",
            "phone": "+44 7700 900123",
            "address": "42 Kings Road, London, E1 7AZ",
        }.get(field, "unknown"),
        "new_value": new_value,
        "message": f"{field.title()} updated successfully. A confirmation has been sent to the customer.",
    })


@tool
def get_account_status(user_id: str) -> str:
    """Check the current status of a customer's account (active, suspended, limited, closed).

    Args:
        user_id: The customer's user ID.
    """
    return json.dumps({
        "user_id": user_id,
        "account_id": "ACC-9182",
        "status": "active",
        "restrictions": [],
        "kyc_status": "verified",
        "last_login": "2026-03-24T09:15:00Z",
        "risk_score": "low",
    })
