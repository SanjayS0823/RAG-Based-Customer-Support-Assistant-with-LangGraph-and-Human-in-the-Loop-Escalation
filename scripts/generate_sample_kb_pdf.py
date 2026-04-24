#!/usr/bin/env python3
"""Generate a sample knowledge-base PDF from the bundled markdown file."""

from __future__ import annotations

from pathlib import Path

from export_docs_to_pdf import convert_markdown_to_pdf


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "samples" / "customer_support_kb.md"
    target = root / "data" / "customer_support_kb.pdf"

    convert_markdown_to_pdf(source, target)
    print(f"Generated sample KB PDF: {target}")


if __name__ == "__main__":
    main()
