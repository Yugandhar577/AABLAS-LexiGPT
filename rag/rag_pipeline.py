"""
rag/rag_pipeline.py
RAG pipeline helpers shared by the Flask routes and services.
"""

from __future__ import annotations

from typing import List, Dict

from .retriever import Retriever, RetrieverResult

_RETRIEVER = Retriever()


def get_relevant_context(query: str, top_k: int = 3, session_id: str | None = None) -> List[Dict]:
    """Return structured context snippets for the given query.

    Each entry is a dict containing: id (int), title, content, score, snippet.
    """
    hits: List[RetrieverResult] = _RETRIEVER.search(query, top_k=top_k, session_id=session_id)
    results: List[Dict] = []
    for idx, hit in enumerate(hits, start=1):
        # Create a short snippet from the content for prompting and display
        snippet = hit.content[:400]
        results.append({
            "id": idx,
            "title": hit.title,
            "content": hit.content,
            "score": hit.score,
            "snippet": snippet,
        })
    return results
