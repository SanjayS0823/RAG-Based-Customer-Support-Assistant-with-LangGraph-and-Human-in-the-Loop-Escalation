#!/usr/bin/env python3
"""CLI script to ingest a support knowledge-base PDF into ChromaDB."""

from __future__ import annotations

import argparse
from pathlib import Path

from rag_support.config import load_settings
from rag_support.ingestion import ingest_pdf_to_chroma


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest PDF into ChromaDB")
    parser.add_argument("--pdf", required=True, help="Path to knowledge-base PDF")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Append to existing collection instead of recreating it",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    settings = load_settings(root)
    stats = ingest_pdf_to_chroma(
        settings,
        Path(args.pdf).resolve(),
        reset_collection=not args.no_reset,
    )

    print("Ingestion complete")
    print(f"PDF: {stats.pdf_path}")
    print(f"Pages loaded: {stats.pages_loaded}")
    print(f"Chunks created: {stats.chunks_created}")
    print(f"Chunks written: {stats.chunks_written}")


if __name__ == "__main__":
    main()
