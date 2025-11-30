"""
rag/chat_history_store.py

Manages a ChromaDB collection for user chat history.
- Seeds collection from `data/chat_history.json`
- Provides `add_message`, `bulk_add_from_file`, and `search` methods

The collection stores each message as a document with metadata:
{ "session_id": ..., "role": "user|assistant", "idx": N }

This module uses the DefaultEmbeddingFunction for offline embedding (works
without external embedding provider). It uses the same persistent directory as
other vector stores (config.VECTOR_DB_DIR).
"""
from __future__ import annotations

from pathlib import Path
import json
import os
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions

from config import VECTOR_DB_DIR, CHAT_HISTORY_FILE


class ChatHistoryStore:
    def __init__(self, persist_dir: Optional[Path] = None, collection_name: str = "chat_history") -> None:
        self.persist_dir = Path(persist_dir or VECTOR_DB_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Use PersistentClient if available; chroma has multiple client implementations
        try:
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        except Exception:
            # fallback to regular client with settings
            from chromadb.config import Settings
            self.client = chromadb.Client(Settings(persist_directory=str(self.persist_dir)))

        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
        )

        # If collection empty, attempt to seed from CHAT_HISTORY_FILE
        if self.collection.count() == 0:
            try:
                self.bulk_add_from_file(Path(CHAT_HISTORY_FILE))
            except Exception:
                # silently ignore seeding errors; collection remains usable
                pass

    # ------------------------------------------------------------------ #
    def _flatten_messages(self, sessions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert chat_history.json sessions dict into list of message dicts.

        Each returned item: {"id": <str>, "content": <text>, "metadata": {...}}
        metadata contains session_id, role, idx (position in session), title
        """
        items: List[Dict[str, Any]] = []
        for session_id, session_obj in sessions.items():
            title = session_obj.get("title") if isinstance(session_obj, dict) else None
            messages = (session_obj or {}).get("messages", []) if isinstance(session_obj, dict) else []
            for idx, msg in enumerate(messages):
                role = msg.get("role", "user")
                text = (msg.get("text") or "").strip()
                if not text:
                    continue
                doc_id = f"{session_id}::{idx}"
                items.append({
                    "id": doc_id,
                    "content": text,
                    "metadata": {"session_id": session_id, "role": role, "idx": idx, "title": title},
                })
        return items

    # ------------------------------------------------------------------ #
    def bulk_add_from_file(self, json_path: Path) -> None:
        """Load `json_path` (chat_history.json) and add messages to the collection."""
        if not json_path.exists():
            return
        with json_path.open("r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except json.JSONDecodeError:
                return

        flat = self._flatten_messages(data)
        if not flat:
            return

        # Prepare lists
        ids = [it["id"] for it in flat]
        docs = [it["content"] for it in flat]
        metas = [it["metadata"] for it in flat]

        # Add only those ids not already present (avoid duplicates)
        # Chroma doesn't have a simple contains API across clients, so we'll try add and ignore duplicates
        try:
            # If collection supports count, we can check but ids uniqueness matters
            self.collection.add(documents=docs, metadatas=metas, ids=ids)
        except Exception:
            # In case add fails (e.g., duplicate ids), we fallback to per-item add with try/except
            for id_, doc, meta in zip(ids, docs, metas):
                try:
                    self.collection.add(documents=[doc], metadatas=[meta], ids=[id_])
                except Exception:
                    # ignore failures for existing entries
                    continue

    # ------------------------------------------------------------------ #
    def add_message(self, session_id: str, role: str, text: str) -> None:
        """Add a single chat message to the collection. Generates an id using session and next index."""
        # Determine next index by counting messages for session (simple approach)
        try:
            current_count = self.collection.count()
        except Exception:
            current_count = 0

        # Use high-entropy id to avoid accidental collisions
        # But prefer sequential ids within session if possible
        # We attempt to compute next idx by scanning existing metadata hits (best-effort)
        next_idx = 0
        # Fetch a small sample (if supported) to compute max idx for session
        try:
            results = self.collection.query(query_texts=[text], n_results=1, include=["metadatas"])  # cheap query
            # ignore result; next_idx fallback to current_count
        except Exception:
            pass

        doc_id = f"{session_id}::{next_idx}::{os.urandom(4).hex()}"
        try:
            self.collection.add(documents=[text], metadatas=[{"session_id": session_id, "role": role}], ids=[doc_id])
        except Exception:
            # last resort: try without id
            try:
                self.collection.add(documents=[text], metadatas=[{"session_id": session_id, "role": role}])
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search chat history for relevant messages. Returns list of dicts with content, metadata, score."""
        if not query or not query.strip():
            return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        hits: List[Dict[str, Any]] = []
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append({"content": doc, "metadata": meta, "score": max(0.0, 1 - float(dist))})
        return hits


# Simple convenience function for other modules
_store: Optional[ChatHistoryStore] = None


def get_chat_history_store() -> ChatHistoryStore:
    global _store
    if _store is None:
        _store = ChatHistoryStore()
    return _store
