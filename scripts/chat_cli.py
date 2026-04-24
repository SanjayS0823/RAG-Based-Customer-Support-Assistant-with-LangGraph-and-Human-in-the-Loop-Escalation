#!/usr/bin/env python3
"""Interactive customer support assistant with LangGraph + HITL."""

from __future__ import annotations

import argparse
from pathlib import Path

from rag_support.config import load_settings
from rag_support.graph import SupportAssistant

HELP_TEXT = """
Commands:
  /help                          Show commands
  /exit                          Exit chat
  /tickets                       List open HITL tickets
  /resolve <ticket_id> <answer>  Resolve a ticket with human response
""".strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run support assistant CLI")
    parser.add_argument("--user-id", default="intern-demo", help="Customer identifier")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    settings = load_settings(root)
    assistant = SupportAssistant(settings)

    print("RAG Customer Support Assistant")
    print("Type /help for commands")

    while True:
        query = input("\nYou: ").strip()
        if not query:
            continue

        if query == "/exit":
            print("Assistant: Session closed.")
            break

        if query == "/help":
            print(HELP_TEXT)
            continue

        if query == "/tickets":
            tickets = assistant.list_open_tickets()
            print("Assistant: Open tickets ->", tickets if tickets else "none")
            continue

        if query.startswith("/resolve "):
            parts = query.split(" ", 2)
            if len(parts) < 3:
                print("Assistant: Usage -> /resolve <ticket_id> <human_answer>")
                continue
            _, ticket_id, human_answer = parts
            try:
                confirmation = assistant.resolve_ticket(ticket_id=ticket_id, human_response=human_answer)
            except FileNotFoundError:
                print(f"Assistant: Ticket not found: {ticket_id}")
                continue
            print(f"Assistant: {confirmation}")
            continue

        state = assistant.ask(query, user_id=args.user_id)
        print(f"Assistant: {state.get('final_response', 'No response generated')}\n")


if __name__ == "__main__":
    main()
