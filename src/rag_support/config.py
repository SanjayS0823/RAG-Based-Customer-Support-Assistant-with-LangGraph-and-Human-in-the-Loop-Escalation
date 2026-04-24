"""Configuration loading for the RAG customer support assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables with safe defaults."""

    project_root: Path
    chroma_path: Path
    hitl_queue_path: Path
    collection_name: str
    chunk_size: int
    chunk_overlap: int
    retrieval_k: int
    embedding_dimension: int
    min_confidence_for_auto_answer: float
    llm_model: str
    openai_api_key: str | None


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


def load_settings(project_root: Path | None = None) -> Settings:
    root = Path(project_root or Path.cwd()).resolve()
    data_dir = root / "data"

    return Settings(
        project_root=root,
        chroma_path=Path(os.getenv("CHROMA_PATH", data_dir / "chroma")).resolve(),
        hitl_queue_path=Path(os.getenv("HITL_QUEUE_PATH", data_dir / "hitl_queue")).resolve(),
        collection_name=os.getenv("COLLECTION_NAME", "customer_support_kb"),
        chunk_size=_int_env("CHUNK_SIZE", 900),
        chunk_overlap=_int_env("CHUNK_OVERLAP", 150),
        retrieval_k=_int_env("RETRIEVAL_K", 4),
        embedding_dimension=_int_env("EMBEDDING_DIMENSION", 512),
        min_confidence_for_auto_answer=_float_env("MIN_CONFIDENCE", 0.20),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
