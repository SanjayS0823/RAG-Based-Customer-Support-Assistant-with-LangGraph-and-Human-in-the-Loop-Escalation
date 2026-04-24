#!/usr/bin/env python3
"""Run the FastAPI web app for the RAG support assistant."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAG support web app")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", default=8000, type=int, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")

    uvicorn.run(
        "rag_support.web:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=[str(root / "src"), str(root / "templates"), str(root / "static")],
        log_level="info",
    )


if __name__ == "__main__":
    main()
