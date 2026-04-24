"""Intent detection and escalation criteria for support routing."""

from __future__ import annotations

import re


INTENT_RULES: dict[str, tuple[str, ...]] = {
    "refund_policy": ("refund", "return", "money back", "chargeback"),
    "account_management": ("cancel", "subscription", "plan", "upgrade", "downgrade"),
    "technical_issue": (
        "bug",
        "error",
        "not working",
        "failed",
        "issue",
        "login",
        "cannot",
    ),
    "shipping_query": ("shipping", "delivery", "tracking", "courier", "dispatch"),
    "human_request": ("human", "agent", "representative", "speak to someone"),
}


def detect_intent(query: str) -> str:
    normalized = query.lower()
    for intent, keywords in INTENT_RULES.items():
        if any(keyword in normalized for keyword in keywords):
            return intent
    return "general_support"


def is_complex_query(query: str) -> bool:
    word_count = len(re.findall(r"\w+", query))
    multi_question = query.count("?") >= 2
    contains_policy_plus_technical = (
        any(token in query.lower() for token in ("refund", "policy", "billing"))
        and any(token in query.lower() for token in ("error", "bug", "crash", "cannot"))
    )
    return word_count > 55 or multi_question or contains_policy_plus_technical


def should_escalate(
    *,
    intent: str,
    confidence: float,
    chunks_found: int,
    query: str,
    min_confidence: float,
) -> tuple[bool, str]:
    if intent == "human_request":
        return True, "User explicitly requested a human agent"

    if chunks_found == 0:
        return True, "No relevant chunks found in knowledge base"

    if confidence < min_confidence:
        return True, f"Low retrieval confidence ({confidence:.2f})"

    if is_complex_query(query) and confidence < min_confidence + 0.12:
        return True, "Complex multi-part query requires human review"

    return False, ""
