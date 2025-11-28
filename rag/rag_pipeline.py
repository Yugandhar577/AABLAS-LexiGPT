"""
rag/rag_pipeline.py
RAG pipeline helpers shared by the Flask routes and services.
"""

from __future__ import annotations

from typing import List

from .retriever import Retriever, RetrieverResult

_RETRIEVER = Retriever()


def get_relevant_context(query: str, top_k: int = 3) -> List[str]:
    """Return formatted context snippets for the given query."""
    hits: List[RetrieverResult] = _RETRIEVER.search(query, top_k=top_k)
    formatted = []
    for idx, hit in enumerate(hits, start=1):
        formatted.append(f"[{idx}] {hit.title}\n{hit.content}")
    return formatted
