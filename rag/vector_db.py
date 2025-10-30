"""
rag/retriever.py
Simple Retriever API used by the agent. Uses VectorDB if available, otherwise keyword fallback.
"""
from typing import List, Optional

# try import vector DB
try:
    from .vector_db import VectorDB
    VECTOR_AVAILABLE = True
except Exception:
    VectorDB = None
    VECTOR_AVAILABLE = False

class Retriever:
    def __init__(self, corpus: Optional[List[str]] = None):
        # Minimal fallback corpus if none provided
        self.corpus = corpus or [
            "Jurisdiction clause defines governing law and venue.",
            "Non-disclosure agreements protect confidential information.",
            "Consideration is essential to form a valid contract.",
        ]
        self.vdb = None
        if VECTOR_AVAILABLE:
            try:
                self.vdb = VectorDB()
                self.vdb.add(self.corpus)
            except Exception:
                self.vdb = None

    def search(self, query: str, top_k: int = 3) -> List[str]:
        if self.vdb:
            try:
                return self.vdb.search(query, top_k=top_k)
            except Exception:
                pass
        # fallback: simple keyword scoring
        q_tokens = set(query.lower().split())
        scored = []
        for doc in self.corpus:
            score = len(q_tokens.intersection(set(doc.lower().split())))
            scored.append((score, doc))
        scored.sort(reverse=True)
        results = [d for s, d in scored if s > 0][:top_k]
        if not results:
            # if no match, return top documents
            return self.corpus[:top_k]
        return results
