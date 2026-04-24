"""PDF ingestion pipeline: load -> chunk -> embed -> store in ChromaDB."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
from pypdf import PdfReader

from .config import Settings
from .embeddings import LocalHashEmbeddingFunction


@dataclass
class IngestionStats:
    pdf_path: str
    pages_loaded: int
    chunks_created: int
    chunks_written: int


def _chunk_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)

    return chunks


def ingest_pdf_to_chroma(
    settings: Settings,
    pdf_path: Path,
    *,
    reset_collection: bool = True,
) -> IngestionStats:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((index, text))

    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_path))

    if reset_collection:
        try:
            client.delete_collection(settings.collection_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=settings.collection_name,
        embedding_function=LocalHashEmbeddingFunction(settings.embedding_dimension),
        metadata={"hnsw:space": "cosine"},
    )

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, int | str]] = []

    chunk_counter = 0
    for page_num, page_text in pages:
        chunks = _chunk_text(
            page_text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        for local_idx, chunk in enumerate(chunks):
            chunk_counter += 1
            ids.append(f"{pdf_path.stem}-p{page_num}-c{local_idx}")
            docs.append(chunk)
            metas.append(
                {
                    "source": pdf_path.name,
                    "page": page_num,
                    "chunk_index": local_idx,
                }
            )

    if ids:
        collection.add(ids=ids, documents=docs, metadatas=metas)

    return IngestionStats(
        pdf_path=str(pdf_path),
        pages_loaded=len(pages),
        chunks_created=chunk_counter,
        chunks_written=len(ids),
    )
