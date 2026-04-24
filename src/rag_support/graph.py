"""LangGraph workflow for support query processing and HITL routing."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .config import Settings
from .hitl import HitlEscalationQueue
from .intents import detect_intent, should_escalate
from .llm import AnswerGenerator
from .models import GraphState
from .retriever import SupportRetriever, score_confidence


class SupportAssistant:
    """Customer-support assistant powered by retrieval + LangGraph orchestration."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.retriever = SupportRetriever(settings)
        self.answer_generator = AnswerGenerator(settings)
        self.hitl_queue = HitlEscalationQueue(settings.hitl_queue_path)
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(GraphState)

        builder.add_node("process", self._processing_node)
        builder.add_node("hitl", self._hitl_node)
        builder.add_node("output", self._output_node)

        builder.add_edge(START, "process")
        builder.add_conditional_edges(
            "process",
            self._routing_decision,
            {
                "hitl": "hitl",
                "output": "output",
            },
        )
        builder.add_edge("hitl", "output")
        builder.add_edge("output", END)

        return builder.compile()

    def _processing_node(self, state: GraphState) -> GraphState:
        query = state.get("query", "")
        user_id = state.get("user_id", "anonymous")

        intent = detect_intent(query)
        chunks = self.retriever.retrieve(query)
        confidence = score_confidence(chunks)
        answer = self.answer_generator.generate(query=query, intent=intent, chunks=chunks)

        escalate, reason = should_escalate(
            intent=intent,
            confidence=confidence,
            chunks_found=len(chunks),
            query=query,
            min_confidence=self.settings.min_confidence_for_auto_answer,
        )

        return {
            "query": query,
            "user_id": user_id,
            "intent": intent,
            "retrieved_chunks": chunks,
            "confidence": confidence,
            "answer_draft": answer,
            "escalate": escalate,
            "escalation_reason": reason,
        }

    def _routing_decision(self, state: GraphState) -> str:
        return "hitl" if state.get("escalate") else "output"

    def _hitl_node(self, state: GraphState) -> GraphState:
        ticket = self.hitl_queue.create_ticket(
            query=state.get("query", ""),
            reason=state.get("escalation_reason", "manual_review"),
            intent=state.get("intent", "general_support"),
            user_id=state.get("user_id", "anonymous"),
            chunks=state.get("retrieved_chunks", []),
            model_answer=state.get("answer_draft", ""),
        )

        return {
            "ticket_id": ticket.ticket_id,
        }

    def _output_node(self, state: GraphState) -> GraphState:
        if state.get("escalate"):
            response = (
                "This request has been escalated to a human support specialist.\n"
                f"Ticket ID: {state.get('ticket_id', 'pending')}\n"
                "Status: Pending human review."
            )
        else:
            response = state.get("answer_draft", "")

        return {"final_response": response}

    def ask(self, query: str, user_id: str = "anonymous") -> GraphState:
        initial_state: GraphState = {
            "query": query,
            "user_id": user_id,
        }
        result: GraphState = self.graph.invoke(initial_state)
        return result

    def resolve_ticket(self, ticket_id: str, human_response: str) -> str:
        ticket = self.hitl_queue.resolve_ticket(ticket_id=ticket_id, human_response=human_response)
        return (
            f"Ticket {ticket.ticket_id} has been resolved by human support. "
            f"Response: {ticket.human_response}"
        )

    def list_open_tickets(self) -> list[str]:
        return [ticket.ticket_id for ticket in self.hitl_queue.list_tickets(status="OPEN")]
