"""Vector retrieval service backed by ChromaDB."""

from __future__ import annotations

from typing import Any

import chromadb

from .config import Settings
from .embeddings import LocalHashEmbeddingFunction
from .models import RetrievedChunk


class SupportRetriever:
    """Provides retrieval from a persisted Chroma collection."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.chroma_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.settings.chroma_path))
        self.collection = self.client.get_or_create_collection(
            name=self.settings.collection_name,
            embedding_function=LocalHashEmbeddingFunction(settings.embedding_dimension),
            metadata={"hnsw:space": "cosine"},
        )

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        limit = k or self.settings.retrieval_k
        if self.collection.count() == 0:
            return []

        raw = self.collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        dists = raw.get("distances", [[]])[0]

        results: list[RetrievedChunk] = []
        for doc, meta, dist in zip(docs, metas, dists):
            metadata: dict[str, Any] = meta or {}
            results.append(
                RetrievedChunk(
                    text=doc,
                    source=str(metadata.get("source", "unknown")),
                    page=metadata.get("page"),
                    distance=float(dist),
                )
            )

        return results


def score_confidence(chunks: list[RetrievedChunk]) -> float:
    """Estimate confidence from retrieval distances (cosine space)."""

    if not chunks:
        return 0.0

    similarities = [max(0.0, 1.0 - chunk.distance) for chunk in chunks]
    top = similarities[0]
    avg = sum(similarities) / len(similarities)
    return max(0.0, min(1.0, (0.7 * top) + (0.3 * avg)))
