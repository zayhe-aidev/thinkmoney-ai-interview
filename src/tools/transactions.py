"""Mock transaction query tools for thinkmoney customer service."""

import json

from langchain_core.tools import tool


MOCK_TRANSACTIONS = [
    {
        "transaction_id": "TXN-90001",
        "date": "2026-03-24T08:30:00Z",
        "description": "Tesco Express",
        "category": "Groceries",
        "amount": "-£12.45",
        "currency": "GBP",
        "status": "completed",
        "card_used": "CARD-5521",
        "type": "card_payment",
    },
    {
        "transaction_id": "TXN-89992",
        "date": "2026-03-23T18:42:00Z",
        "description": "TfL - Contactless",
        "category": "Transport",
        "amount": "-£4.80",
        "currency": "GBP",
        "status": "completed",
        "card_used": "CARD-5521",
        "type": "card_payment",
    },
    {
        "transaction_id": "TXN-89985",
        "date": "2026-03-22T14:15:00Z",
        "description": "Amazon.co.uk",
        "category": "Shopping",
        "amount": "-£67.99",
        "currency": "GBP",
        "status": "completed",
        "card_used": "CARD-8834",
        "type": "card_payment",
    },
    {
        "transaction_id": "TXN-89970",
        "date": "2026-03-21T09:00:00Z",
        "description": "Netflix",
        "category": "Entertainment",
        "amount": "-£15.99",
        "currency": "GBP",
        "status": "completed",
        "card_used": "CARD-5521",
        "type": "direct_debit",
    },
    {
        "transaction_id": "TXN-89960",
        "date": "2026-03-20T00:01:00Z",
        "description": "Acme Corp - Salary",
        "category": "Income",
        "amount": "+£3,250.00",
        "currency": "GBP",
        "status": "completed",
        "card_used": None,
        "type": "bank_transfer",
    },
    {
        "transaction_id": "TXN-89945",
        "date": "2026-03-19T13:20:00Z",
        "description": "Pret A Manger",
        "category": "Eating Out",
        "amount": "-£6.50",
        "currency": "GBP",
        "status": "completed",
        "card_used": "CARD-5521",
        "type": "card_payment",
    },
    {
        "transaction_id": "TXN-89930",
        "date": "2026-03-18T10:45:00Z",
        "description": "ATM Withdrawal - Barclays",
        "category": "Cash",
        "amount": "-£100.00",
        "currency": "GBP",
        "status": "completed",
        "card_used": "CARD-5521",
        "type": "atm_withdrawal",
    },
    {
        "transaction_id": "TXN-89920",
        "date": "2026-03-17T16:30:00Z",
        "description": "Transfer to James Wilson",
        "category": "Transfer",
        "amount": "-£50.00",
        "currency": "GBP",
        "status": "completed",
        "card_used": None,
        "type": "bank_transfer",
    },
]


@tool
def get_transaction_history(user_id: str, days: int = 30) -> str:
    """Get recent transaction history for a customer.

    Args:
        user_id: The customer's user ID.
        days: Number of days to look back (default 30, max 90).
    """
    return json.dumps({
        "user_id": user_id,
        "period": f"Last {min(days, 90)} days",
        "transaction_count": len(MOCK_TRANSACTIONS),
        "transactions": MOCK_TRANSACTIONS,
    })


@tool
def get_transaction_details(transaction_id: str) -> str:
    """Get full details of a specific transaction.

    Args:
        transaction_id: The transaction ID (e.g. TXN-90001).
    """
    for txn in MOCK_TRANSACTIONS:
        if txn["transaction_id"] == transaction_id:
            detail = {**txn}
            detail.update({
                "merchant_category_code": "5411" if txn["category"] == "Groceries" else "0000",
                "merchant_country": "GB",
                "exchange_rate": None,
                "fee": "£0.00",
                "reference": f"REF-{transaction_id}",
                "settlement_date": txn["date"][:10],
            })
            return json.dumps(detail)

    return json.dumps({
        "error": f"Transaction {transaction_id} not found.",
        "suggestion": "Use get_transaction_history to list recent transactions.",
    })


@tool
def dispute_transaction(transaction_id: str, reason: str) -> str:
    """File a dispute for a transaction. Starts the chargeback investigation process.

    Args:
        transaction_id: The transaction ID to dispute.
        reason: Reason for the dispute — e.g. 'unauthorised', 'goods_not_received',
                'duplicate_charge', 'incorrect_amount', 'other'.
    """
    valid_reasons = {"unauthorised", "goods_not_received", "duplicate_charge", "incorrect_amount", "other"}
    if reason not in valid_reasons:
        return json.dumps({
            "success": False,
            "error": f"Invalid reason '{reason}'. Must be one of: {', '.join(sorted(valid_reasons))}",
        })

    return json.dumps({
        "success": True,
        "dispute_id": "DSP-44210",
        "transaction_id": transaction_id,
        "reason": reason,
        "status": "under_review",
        "created_at": "2026-03-24T10:00:00Z",
        "estimated_resolution": "5-10 business days",
        "provisional_credit": reason == "unauthorised",
        "message": "Dispute filed successfully. You will receive updates via the app. "
                   "If the transaction was unauthorised, a provisional credit may be applied within 24 hours.",
    })


@tool
def get_dispute_status(dispute_id: str) -> str:
    """Check the status of an existing transaction dispute.

    Args:
        dispute_id: The dispute ID (e.g. DSP-44210).
    """
    return json.dumps({
        "dispute_id": dispute_id,
        "transaction_id": "TXN-89985",
        "status": "under_review",
        "reason": "goods_not_received",
        "filed_date": "2026-03-22T10:00:00Z",
        "estimated_resolution": "2026-04-01",
        "provisional_credit_applied": False,
        "updates": [
            {"date": "2026-03-22T10:00:00Z", "note": "Dispute received and logged."},
            {"date": "2026-03-23T14:00:00Z", "note": "Merchant contacted for evidence."},
        ],
        "message": "Your dispute is being reviewed. The merchant has been contacted.",
    })
