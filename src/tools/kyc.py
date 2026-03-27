"""Mock KYC/compliance tools for thinkmoney customer service."""

import json
from datetime import datetime

from langchain_core.tools import tool


@tool
def get_kyc_status(user_id: str) -> str:
    """Get the current KYC (Know Your Customer) verification status for a customer.

    Args:
        user_id: The customer's user ID.
    """
    return json.dumps({
        "user_id": user_id,
        "kyc_level": "full",
        "status": "verified",
        "verified_at": "2023-03-16T14:30:00Z",
        "identity_verified": True,
        "address_verified": True,
        "pep_check": "clear",
        "sanctions_check": "clear",
        "last_review": "2025-09-10T10:00:00Z",
        "next_review_due": "2026-09-10",
        "documents_on_file": [
            {"type": "passport", "status": "verified", "expiry": "2031-08-20"},
            {"type": "proof_of_address", "status": "verified", "document": "Utility bill"},
        ],
    })


@tool
def get_required_documents(user_id: str) -> str:
    """Check what documents are required or missing for a customer's KYC verification.

    Args:
        user_id: The customer's user ID.
    """
    return json.dumps({
        "user_id": user_id,
        "kyc_level": "full",
        "all_documents_provided": True,
        "documents": [
            {
                "type": "photo_id",
                "status": "verified",
                "accepted_types": ["passport", "driving_licence", "national_id"],
                "provided": "passport",
            },
            {
                "type": "proof_of_address",
                "status": "verified",
                "accepted_types": ["utility_bill", "bank_statement", "council_tax"],
                "provided": "utility_bill",
                "note": "Must be dated within the last 3 months.",
            },
            {
                "type": "selfie_verification",
                "status": "verified",
                "note": "Biometric liveness check completed.",
            },
        ],
        "message": "All required documents are on file and verified.",
    })


@tool
def submit_document(user_id: str, document_type: str) -> str:
    """Submit a document for KYC verification. In production, this would accept a file upload.

    Args:
        user_id: The customer's user ID.
        document_type: Type of document — one of 'passport', 'driving_licence',
                      'national_id', 'utility_bill', 'bank_statement', 'council_tax', 'selfie'.
    """
    valid_types = {
        "passport", "driving_licence", "national_id",
        "utility_bill", "bank_statement", "council_tax", "selfie",
    }

    if document_type not in valid_types:
        return json.dumps({
            "success": False,
            "error": f"Invalid document type '{document_type}'. "
                     f"Accepted types: {', '.join(sorted(valid_types))}",
        })

    return json.dumps({
        "success": True,
        "user_id": user_id,
        "document_type": document_type,
        "submission_id": "DOC-20260324-001",
        "status": "pending_review",
        "submitted_at": datetime.now().isoformat(),
        "estimated_review_time": "24-48 hours",
        "message": f"Document ({document_type}) submitted successfully. "
                   "You will be notified once the review is complete.",
    })


@tool
def get_account_restrictions(user_id: str) -> str:
    """Check if a customer's account has any active restrictions or limitations.

    Args:
        user_id: The customer's user ID.
    """
    return json.dumps({
        "user_id": user_id,
        "has_restrictions": False,
        "active_restrictions": [],
        "historical_restrictions": [
            {
                "restriction_id": "RST-001",
                "type": "kyc_pending",
                "applied": "2023-03-15T12:00:00Z",
                "lifted": "2023-03-16T14:30:00Z",
                "reason": "Initial identity verification pending.",
                "impact": "Outgoing transfers limited to £500/day.",
            },
        ],
        "message": "No active restrictions on this account.",
    })
