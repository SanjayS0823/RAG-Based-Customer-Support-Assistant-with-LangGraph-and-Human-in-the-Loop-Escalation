"""LLM answer generation with OpenAI-first and deterministic fallback behavior."""

from __future__ import annotations

import re
from textwrap import shorten

from .config import Settings
from .models import RetrievedChunk


class AnswerGenerator:
    """Generates grounded answers from retrieved context."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.openai_api_key:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=settings.openai_api_key)
            except Exception:
                self.client = None

    def generate(self, *, query: str, intent: str, chunks: list[RetrievedChunk]) -> str:
        if self.client is not None:
            try:
                return self._generate_with_openai(query=query, intent=intent, chunks=chunks)
            except Exception:
                # Fall back to deterministic answer if API call fails.
                pass

        return self._generate_fallback(query=query, intent=intent, chunks=chunks)

    def _generate_with_openai(self, *, query: str, intent: str, chunks: list[RetrievedChunk]) -> str:
        context = "\n\n".join(
            f"Source: {chunk.source} (page {chunk.page})\n{chunk.text}" for chunk in chunks
        )

        prompt = (
            "You are a customer support assistant. "
            "Only answer using the supplied context. "
            "Output only the final customer-facing answer. "
            "Do not include instructions, internal notes, confidence, or source labels. "
            "Use short paragraphs and bullets when helpful."
        )

        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Intent: {intent}\n"
                        f"Customer question: {query}\n"
                        f"Context:\n{context}"
                    ),
                },
            ],
        )
        message = response.choices[0].message.content
        return message or "I could not generate an answer from the context."

    def _generate_fallback(self, *, query: str, intent: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "I don’t have enough information in the knowledge base to answer this accurately."

        merged_text = " ".join(chunk.text for chunk in chunks[:2])
        cleaned = re.sub(r"\s+", " ", merged_text.replace("#", " ")).strip()
        segments = [
            re.sub(r"^[\-\s]+", "", segment.strip(" ."))
            for segment in re.split(r"(?:\s-\s+|[.?!]\s+)", cleaned)
            if len(segment.strip()) > 20
        ]

        if not segments:
            concise = shorten(cleaned, width=320, placeholder="...")
            return f"Answer:\n- {concise}"

        bullet_points = "\n".join(f"- {segment}" for segment in segments[:3])
        return f"Answer:\n{bullet_points}"
