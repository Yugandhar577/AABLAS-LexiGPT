"""
rag/vector_db.py
Utility wrapper around ChromaDB for LexiGPT.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence

import chromadb
from chromadb.utils import embedding_functions


class VectorDB:
    """Simple helper around Chroma to add/search legal documents."""

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = "lexigpt_legal_corpus",
        auto_seed_file: Path | None = None,
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

        if auto_seed_file:
            self._maybe_seed(auto_seed_file)

    # ------------------------------------------------------------------ #
    def _maybe_seed(self, json_path: Path) -> None:
        if self.collection.count() > 0:
            return
        if not json_path.exists():
            return

        with json_path.open("r", encoding="utf-8") as fh:
            try:
                rows = json.load(fh)
            except json.JSONDecodeError:
                return

        documents: List[str] = []
        metadatas: List[Dict[str, str]] = []
        ids: List[str] = []

        for idx, row in enumerate(rows):
            title = row.get("title") or f"Clause {idx+1}"
            content = (row.get("description") or "").strip()
            if not content:
                continue
            documents.append(content)
            metadatas.append({"title": title})
            ids.append(f"doc-{idx}")

        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    # ------------------------------------------------------------------ #
    def add(self, docs: Sequence[Dict[str, str]] | Sequence[str]) -> None:
        """Add additional documents to the collection."""
        documents: List[str] = []
        metadatas: List[Dict[str, str]] = []
        ids: List[str] = []

        start_index = self.collection.count()
        for offset, doc in enumerate(docs):
            idx = start_index + offset
            if isinstance(doc, str):
                content = doc
                title = f"Doc {idx+1}"
            else:
                content = doc.get("content", "")
                title = doc.get("title", f"Doc {idx+1}")
            if not content:
                continue
            documents.append(content)
            metadatas.append({"title": title})
            ids.append(f"adhoc-{idx}")

        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    # ------------------------------------------------------------------ #
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """Return top_k hits as dicts: {title, content, score}."""
        if not query.strip():
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        hits: List[Dict[str, str]] = []
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append(
                {
                    "title": meta.get("title", "Legal Reference"),
                    "content": doc,
                    "score": max(0.0, 1 - float(dist)),
                }
            )
        return hits

    # ------------------------------------------------------------------ #
    def is_empty(self) -> bool:
        return self.collection.count() == 0
