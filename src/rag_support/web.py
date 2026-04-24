"""FastAPI web interface for the RAG customer support assistant."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .config import load_settings
from .graph import SupportAssistant

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

settings = load_settings(PROJECT_ROOT)
assistant = SupportAssistant(settings)

app = FastAPI(
    title="RAG Customer Support Assistant",
    description="Web UI and API for LangGraph + HITL support workflow",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))


class AskRequest(BaseModel):
    user_id: str = Field(default="web-user", min_length=1, max_length=120)
    query: str = Field(min_length=2, max_length=4000)


class ResolveRequest(BaseModel):
    human_response: str = Field(min_length=3, max_length=4000)


def _serialize_state(state: dict) -> dict:
    chunks = state.get("retrieved_chunks") or []
    return {
        "final_response": state.get("final_response", ""),
        "intent": state.get("intent", "general_support"),
        "confidence": float(state.get("confidence", 0.0)),
        "escalate": bool(state.get("escalate", False)),
        "escalation_reason": state.get("escalation_reason", ""),
        "ticket_id": state.get("ticket_id"),
        "sources": [
            {
                "source": chunk.source,
                "page": chunk.page,
                "distance": round(float(chunk.distance), 4),
            }
            for chunk in chunks
        ],
    }


def _serialize_ticket(ticket) -> dict:
    return {
        "ticket_id": ticket.ticket_id,
        "query": ticket.query,
        "reason": ticket.reason,
        "intent": ticket.intent,
        "user_id": ticket.user_id,
        "retrieved_sources": ticket.retrieved_sources,
        "model_answer": ticket.model_answer,
        "created_at": ticket.created_at,
        "status": ticket.status,
        "human_response": ticket.human_response,
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "RAG Support Control Room",
            "collection_name": settings.collection_name,
            "active_page": "support",
        },
    )


@app.get("/hitl", response_class=HTMLResponse)
def hitl_console(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="hitl.html",
        context={
            "title": "HITL Escalation Console",
            "collection_name": settings.collection_name,
            "active_page": "hitl",
        },
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "collection": settings.collection_name,
        "indexed_chunks": assistant.retriever.collection.count(),
        "open_tickets": len(assistant.list_open_tickets()),
    }


@app.post("/api/ask")
def ask(payload: AskRequest) -> dict:
    try:
        state = assistant.ask(query=payload.query.strip(), user_id=payload.user_id.strip())
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise HTTPException(status_code=500, detail=f"Query processing failed: {exc}") from exc

    return _serialize_state(state)


@app.get("/api/tickets")
def list_tickets(status: str = Query(default="OPEN", pattern="^(OPEN|RESOLVED|ALL)$")) -> dict:
    if status == "ALL":
        tickets = assistant.hitl_queue.list_tickets(status=None)
    else:
        tickets = assistant.hitl_queue.list_tickets(status=status)

    return {
        "count": len(tickets),
        "tickets": [_serialize_ticket(ticket) for ticket in tickets],
    }


@app.post("/api/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str, payload: ResolveRequest) -> dict:
    try:
        assistant.resolve_ticket(ticket_id=ticket_id, human_response=payload.human_response.strip())
        ticket = assistant.hitl_queue.read_ticket(ticket_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {ticket_id}") from exc
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise HTTPException(status_code=500, detail=f"Ticket resolution failed: {exc}") from exc

    return {
        "message": f"Ticket {ticket_id} resolved",
        "ticket": _serialize_ticket(ticket),
    }
