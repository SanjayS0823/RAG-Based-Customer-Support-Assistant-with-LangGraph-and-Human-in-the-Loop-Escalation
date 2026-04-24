"""Human-in-the-loop queue for escalation and human response injection."""

from __future__ import annotations

import json
from pathlib import Path

from .models import HitlTicket, RetrievedChunk


class HitlEscalationQueue:
    """File-based queue used to store and resolve escalation tickets."""

    def __init__(self, queue_dir: Path):
        self.queue_dir = queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def create_ticket(
        self,
        *,
        query: str,
        reason: str,
        intent: str,
        user_id: str,
        chunks: list[RetrievedChunk],
        model_answer: str,
    ) -> HitlTicket:
        ticket = HitlTicket(
            query=query,
            reason=reason,
            intent=intent,
            user_id=user_id,
            retrieved_sources=[chunk.source for chunk in chunks],
            model_answer=model_answer,
        )
        self._write_ticket(ticket)
        return ticket

    def resolve_ticket(self, ticket_id: str, human_response: str) -> HitlTicket:
        ticket = self.read_ticket(ticket_id)
        ticket.status = "RESOLVED"
        ticket.human_response = human_response
        self._write_ticket(ticket)
        return ticket

    def read_ticket(self, ticket_id: str) -> HitlTicket:
        path = self.queue_dir / f"{ticket_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return HitlTicket(
            ticket_id=payload["ticket_id"],
            query=payload["query"],
            reason=payload["reason"],
            intent=payload["intent"],
            user_id=payload["user_id"],
            retrieved_sources=payload["retrieved_sources"],
            model_answer=payload["model_answer"],
            created_at=payload["created_at"],
            status=payload["status"],
            human_response=payload.get("human_response"),
        )

    def list_tickets(self, status: str | None = None) -> list[HitlTicket]:
        tickets: list[HitlTicket] = []
        for path in sorted(self.queue_dir.glob("hitl-*.json")):
            ticket = self.read_ticket(path.stem)
            if status and ticket.status != status:
                continue
            tickets.append(ticket)
        return tickets

    def _write_ticket(self, ticket: HitlTicket) -> None:
        path = self.queue_dir / f"{ticket.ticket_id}.json"
        path.write_text(json.dumps(ticket.to_dict(), indent=2), encoding="utf-8")
