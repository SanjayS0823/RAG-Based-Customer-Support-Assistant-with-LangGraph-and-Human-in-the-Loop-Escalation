"""Local deterministic embedding function for offline-friendly retrieval."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


class LocalHashEmbeddingFunction(EmbeddingFunction[Documents]):
    """A light-weight hashing embedder.

    This avoids model downloads while still producing deterministic vector embeddings.
    """

    def __init__(self, dimension: int = 512):
        self.dimension = dimension

    def _tokenize(self, text: str) -> Iterable[str]:
        return (token.lower() for token in _TOKEN_PATTERN.findall(text))

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        for token in self._tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], byteorder="big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def __call__(self, input: Documents) -> Embeddings:
        return [self._embed_one(text) for text in input]
