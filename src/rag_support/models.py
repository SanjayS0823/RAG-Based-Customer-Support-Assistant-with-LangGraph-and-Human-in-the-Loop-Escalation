"""Data models for retrieval, graph state, and HITL payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from typing_extensions import TypedDict


@dataclass
class RetrievedChunk:
    """A chunk returned by vector retrieval."""

    text: str
    source: str
    page: int | None
    distance: float


@dataclass
class HitlTicket:
    """Escalation ticket persisted for human follow-up."""

    query: str
    reason: str
    intent: str
    user_id: str
    retrieved_sources: list[str]
    model_answer: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "OPEN"
    human_response: str | None = None
    ticket_id: str = field(default_factory=lambda: f"hitl-{uuid4().hex[:10]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "query": self.query,
            "reason": self.reason,
            "intent": self.intent,
            "user_id": self.user_id,
            "retrieved_sources": self.retrieved_sources,
            "model_answer": self.model_answer,
            "created_at": self.created_at,
            "status": self.status,
            "human_response": self.human_response,
        }


class GraphState(TypedDict, total=False):
    """State object flowing through LangGraph nodes."""

    query: str
    user_id: str
    intent: str
    retrieved_chunks: list[RetrievedChunk]
    answer_draft: str
    confidence: float
    escalate: bool
    escalation_reason: str
    ticket_id: str
    human_response: str
    final_response: str
