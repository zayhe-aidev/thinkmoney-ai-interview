"""Mock payment and transfer tools for thinkmoney customer service."""

import json
from datetime import datetime

from langchain_core.tools import tool


@tool
def get_payees(user_id: str) -> str:
    """List all saved payees for a customer's account.

    Args:
        user_id: The customer's user ID.
    """
    return json.dumps({
        "user_id": user_id,
        "payees": [
            {
                "payee_id": "PAY-001",
                "name": "James Wilson",
                "sort_code": "20-30-40",
                "account_number": "12345678",
                "type": "personal",
                "last_paid": "2026-03-17",
            },
            {
                "payee_id": "PAY-002",
                "name": "Landlord - Premier Properties",
                "sort_code": "11-22-33",
                "account_number": "87654321",
                "type": "business",
                "last_paid": "2026-03-01",
            },
            {
                "payee_id": "PAY-003",
                "name": "Maria Garcia",
                "iban": "ES91 2100 0418 4502 0005 1332",
                "type": "international",
                "currency": "EUR",
                "last_paid": "2026-02-15",
            },
        ],
    })


@tool
def initiate_transfer(
    user_id: str,
    payee_id: str,
    amount: float,
    currency: str = "GBP",
    reference: str = "",
) -> str:
    """Initiate a money transfer to a saved payee.

    Args:
        user_id: The customer's user ID.
        payee_id: The payee ID to send money to.
        amount: Amount to transfer (must be positive).
        currency: Currency code (default GBP).
        reference: Optional payment reference.
    """
    if amount <= 0:
        return json.dumps({
            "success": False,
            "error": "Amount must be a positive number.",
        })

    if amount > 25000:
        return json.dumps({
            "success": False,
            "error": "Amount exceeds single transfer limit of £25,000. "
                     "Please contact support for higher-value transfers.",
        })

    is_international = payee_id == "PAY-003"

    return json.dumps({
        "success": True,
        "payment_id": "PMT-78432",
        "user_id": user_id,
        "payee_id": payee_id,
        "amount": f"{amount:.2f}",
        "currency": currency,
        "reference": reference or "thinkmoney transfer",
        "type": "SWIFT" if is_international else "Faster Payments",
        "fee": "£3.00" if is_international else "£0.00",
        "estimated_arrival": "2-5 business days" if is_international else "Within minutes",
        "initiated_at": datetime.now().isoformat(),
        "status": "processing",
        "message": "Transfer initiated successfully.",
    })


@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """Get the current exchange rate between two currencies.

    Args:
        from_currency: Source currency code (e.g. GBP).
        to_currency: Target currency code (e.g. EUR).
    """
    rates = {
        ("GBP", "EUR"): 1.1650,
        ("GBP", "USD"): 1.2710,
        ("GBP", "PLN"): 5.0820,
        ("GBP", "RON"): 5.8140,
        ("EUR", "GBP"): 0.8584,
        ("EUR", "USD"): 1.0910,
        ("USD", "GBP"): 0.7868,
        ("USD", "EUR"): 0.9166,
        ("PLN", "GBP"): 0.1968,
        ("RON", "GBP"): 0.1720,
    }

    pair = (from_currency.upper(), to_currency.upper())
    rate = rates.get(pair)

    if rate is None:
        return json.dumps({
            "error": f"Exchange rate for {pair[0]}/{pair[1]} not available.",
            "supported_currencies": ["GBP", "EUR", "USD", "PLN", "RON"],
        })

    # Simulate weekend markup
    is_weekend = datetime.now().weekday() >= 5
    markup = 0.015 if is_weekend else 0.005

    return json.dumps({
        "from": pair[0],
        "to": pair[1],
        "rate": round(rate, 4),
        "markup": f"{markup * 100:.1f}%",
        "effective_rate": round(rate * (1 - markup), 4),
        "weekend_rate": is_weekend,
        "timestamp": datetime.now().isoformat(),
        "note": "Weekend rates include a higher markup due to FX market closure."
        if is_weekend
        else "Standard weekday rate.",
    })


@tool
def get_standing_orders(user_id: str) -> str:
    """List all active standing orders for a customer.

    Args:
        user_id: The customer's user ID.
    """
    return json.dumps({
        "user_id": user_id,
        "standing_orders": [
            {
                "order_id": "SO-101",
                "payee": "Landlord - Premier Properties",
                "payee_id": "PAY-002",
                "amount": "£1,200.00",
                "frequency": "monthly",
                "next_payment": "2026-04-01",
                "reference": "Rent - Flat 4B",
                "status": "active",
                "created": "2023-06-01",
            },
            {
                "order_id": "SO-102",
                "payee": "James Wilson",
                "payee_id": "PAY-001",
                "amount": "£25.00",
                "frequency": "monthly",
                "next_payment": "2026-04-15",
                "reference": "Shared Netflix",
                "status": "active",
                "created": "2024-01-10",
            },
        ],
    })


@tool
def cancel_standing_order(order_id: str) -> str:
    """Cancel an active standing order.

    Args:
        order_id: The standing order ID (e.g. SO-101).
    """
    return json.dumps({
        "success": True,
        "order_id": order_id,
        "status": "cancelled",
        "cancelled_at": datetime.now().isoformat(),
        "message": f"Standing order {order_id} has been cancelled. "
                   "No further payments will be made.",
    })
