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
        if self.vdb:
            try:
                hits = self.vdb.search(query, top_k=top_k)
                if hits:
                    return [
                        RetrieverResult(
                            title=hit["title"],
                            content=hit["content"],
                            score=float(hit.get("score", 0.0)),
                        )
                        for hit in hits
                    ]
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

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]