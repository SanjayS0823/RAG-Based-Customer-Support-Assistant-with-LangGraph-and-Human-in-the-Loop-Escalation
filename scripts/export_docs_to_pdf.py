#!/usr/bin/env python3
"""Export Markdown design documents to PDF using a dependency-free writer."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 50
TOP_MARGIN = 742
FONT_SIZE = 10
LINE_HEIGHT = 14
LINES_PER_PAGE = 48


def normalize_markdown(markdown_text: str) -> list[str]:
    lines = markdown_text.splitlines()
    cleaned: list[str] = []

    for raw in lines:
        line = raw.replace("\t", "    ").rstrip()
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"\*([^*]+)\*", r"\1", line)
        cleaned.append(line)

    return cleaned


def wrap_lines(lines: list[str], width: int = 95) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        if len(line) <= width:
            wrapped.append(line)
            continue

        current = line
        while len(current) > width:
            split_at = current.rfind(" ", 0, width)
            if split_at <= 0:
                split_at = width
            wrapped.append(current[:split_at])
            current = current[split_at:].lstrip()
        wrapped.append(current)
    return wrapped


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf(lines: list[str], output_path: Path) -> None:
    pages = [lines[i : i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)] or [[]]

    objects: list[bytes] = []

    def add_obj(content: str) -> int:
        objects.append(content.encode("latin-1", errors="replace"))
        return len(objects)

    page_object_numbers: list[int] = []
    content_object_numbers: list[int] = []

    # placeholders for catalog and pages
    add_obj("<< /Type /Catalog /Pages 2 0 R >>")
    add_obj("<< /Type /Pages /Kids [] /Count 0 >>")

    for _ in pages:
        page_obj_num = len(objects) + 1
        content_obj_num = len(objects) + 2
        page_object_numbers.append(page_obj_num)
        content_object_numbers.append(content_obj_num)

        add_obj(
            "<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            "/Resources << /Font << /F1 0 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>"
        )
        add_obj("<< /Length 0 >>\nstream\n\nendstream")

    font_object_num = add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    # Fill page objects with correct font reference.
    for idx, page_obj_num in enumerate(page_object_numbers):
        content_obj_num = content_object_numbers[idx]
        objects[page_obj_num - 1] = (
            "<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_object_num} 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>"
        ).encode("latin-1")

    # Fill content streams.
    for idx, page_lines in enumerate(pages):
        y_cursor = TOP_MARGIN
        stream_lines = [
            "BT",
            f"/F1 {FONT_SIZE} Tf",
            f"{LEFT_MARGIN} {y_cursor} Td",
            f"{LINE_HEIGHT} TL",
        ]
        for line in page_lines:
            stream_lines.append(f"({escape_pdf_text(line)}) Tj")
            stream_lines.append("T*")

        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines)
        content = (
            f"<< /Length {len(stream_data.encode('latin-1', errors='replace'))} >>\n"
            f"stream\n{stream_data}\nendstream"
        )
        objects[content_object_numbers[idx] - 1] = content.encode("latin-1", errors="replace")

    # Fill pages object.
    kids = " ".join(f"{num} 0 R" for num in page_object_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_numbers)} >>".encode("latin-1")

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("latin-1")
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf)


def convert_markdown_to_pdf(input_path: Path, output_path: Path) -> None:
    markdown = input_path.read_text(encoding="utf-8")
    normalized = normalize_markdown(markdown)
    wrapped = wrap_lines(normalized)
    write_simple_pdf(wrapped, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Markdown docs to PDF")
    parser.add_argument(
        "--input-dir",
        default=str(Path(__file__).resolve().parents[1] / "docs"),
        help="Directory containing HLD.md, LLD.md, TECHNICAL_DOCUMENTATION.md",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[1] / "deliverables"),
        help="Directory where PDFs are written",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    mapping = {
        input_dir / "HLD.md": output_dir / "HLD_Document.pdf",
        input_dir / "LLD.md": output_dir / "LLD_Document.pdf",
        input_dir / "TECHNICAL_DOCUMENTATION.md": output_dir / "Technical_Documentation.pdf",
    }

    for input_file, output_file in mapping.items():
        convert_markdown_to_pdf(input_file, output_file)
        print(f"Exported: {output_file}")


if __name__ == "__main__":
    main()
