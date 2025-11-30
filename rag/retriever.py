# retriever.py
"""
Retrieval layer for RAG
-----------------------
Provides a thin wrapper around the VectorDB along with a keyword fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from config import LEGAL_DATA_FILE, VECTOR_DB_DIR
from .vector_db import VectorDB
from .chat_history_store import get_chat_history_store


@dataclass
class RetrieverResult:
    title: str
    content: str
    score: float

    def as_text(self) -> str:
        return f"{self.title}\n{self.content}"


class Retriever:
    def __init__(self) -> None:
        data_path = Path(LEGAL_DATA_FILE)
        persist_dir = Path(VECTOR_DB_DIR)

        try:
            self.vdb = VectorDB(persist_dir=persist_dir, auto_seed_file=data_path)
        except Exception:
            self.vdb = None
        # Initialize chat history store
        try:
            self.chat_store = get_chat_history_store()
        except Exception:
            self.chat_store = None

        self.fallback_corpus: List[Dict[str, str]] = [
            {
                "title": "Arbitration Clause Basics",
                "content": "Arbitration clauses specify how disputes will be resolved and must define seat, governing law, and procedural rules.",
            },
            {
                "title": "Non-Disclosure Agreements",
                "content": "NDAs protect confidential information shared between parties. They typically define the confidential material, obligations, and duration.",
            },
            {
                "title": "Consideration in Contracts",
                "content": "A valid contract requires consideration, i.e., something of value exchanged between the parties.",
            },
        ]

    # ------------------------------------------------------------------ #
    def search(self, query: str, top_k: int = 3) -> List[RetrieverResult]:
        combined: List[RetrieverResult] = []

        # 1) Search chat history first (gives user-specific context)
        if getattr(self, "chat_store", None):
            try:
                chat_hits = self.chat_store.search(query, top_k=top_k)
                for hit in chat_hits:
                    meta = hit.get("metadata", {}) or {}
                    session_id = meta.get("session_id", "chat")
                    role = meta.get("role", "user")
                    title = f"Chat ({session_id} - {role})"
                    score = float(hit.get("score", 0.0))
                    # Slightly boost chat matches
                    score = min(1.0, score * 1.2)
                    combined.append(RetrieverResult(title=title, content=hit.get("content", ""), score=score))
            except Exception:
                pass

        # 2) Search legal corpus
        if self.vdb:
            try:
                hits = self.vdb.search(query, top_k=top_k)
                if hits:
                    for hit in hits:
                        combined.append(
                            RetrieverResult(
                                title=hit.get("title", "Legal Reference"),
                                content=hit.get("content", ""),
                                score=float(hit.get("score", 0.0)),
                            )
                        )
            except Exception:
                pass

        # Fallback: naive keyword scoring
        query_tokens = set(query.lower().split())
        scored: List[RetrieverResult] = []
        for entry in self.fallback_corpus:
            content = entry["content"]
            doc_tokens = set(content.lower().split())
            score = len(query_tokens & doc_tokens)
            scored.append(RetrieverResult(entry["title"], content, float(score)))

        # Merge combined results with fallback if needed
        if combined:
            # sort by score and return top_k
            combined.sort(key=lambda r: r.score, reverse=True)
            # dedupe by content text (keep highest score)
            seen = set()
            deduped: List[RetrieverResult] = []
            for r in combined:
                key = (r.content or "").strip()
                if not key or key in seen:
                    continue
                seen.add(key)
                deduped.append(r)
            return deduped[:top_k]

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]