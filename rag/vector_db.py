"""
rag/vector_db.py
Utility wrapper around ChromaDB for LexiGPT.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Sequence, Optional

import chromadb
from chromadb.utils import embedding_functions


def _clean_text(text: str) -> str:
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace("\x0c", "")
    return text.strip()


def _chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> List[str]:
    if not text:
        return []
    step = max(1, chunk_size - chunk_overlap)
    chunks: List[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= text_len:
            break
        start += step
    return chunks


class VectorDB:
    """Simple helper around Chroma to add/search legal documents.

    This class also includes a convenience method `process_and_embed_document`
    which extracts text from a file (PDF, TXT, DOCX if python-docx is installed),
    chunks it, and stores chunks with metadata (including optional session_id).
    """

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = "lexigpt_legal_corpus",
        auto_seed_file: Optional[Path] = None,
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Use persistent client (wraps same underlying storage used elsewhere)
        try:
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        except Exception:
            # fallback to regular client for environments without PersistentClient
            self.client = chromadb.Client()

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
        """Add additional documents to the collection.

        Accepts either a list of strings or a list of dicts with keys:
          - content (required)
          - title (optional)
          - metadata (optional dict) which will be stored alongside the document
        """
        documents: List[str] = []
        metadatas: List[Dict[str, str]] = []
        ids: List[str] = []

        start_index = self.collection.count()
        for offset, doc in enumerate(docs):
            idx = start_index + offset
            if isinstance(doc, str):
                content = doc
                title = f"Doc {idx+1}"
                meta = {"title": title}
            else:
                content = doc.get("content", "")
                title = doc.get("title", f"Doc {idx+1}")
                meta = dict(doc.get("metadata", {}))
                meta.setdefault("title", title)
            if not content:
                continue
            documents.append(content)
            metadatas.append(meta)
            ids.append(f"adhoc-{idx}")

        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    # ------------------------------------------------------------------ #
    def search(self, query: str, top_k: int = 3, where: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Return top_k hits as dicts: {title, content, score}.

        Allows passing a `where` dict to scope results by metadata (e.g. session_id).
        """
        if not query or not str(query).strip():
            return []

        query_kwargs = dict(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        if where:
            query_kwargs["where"] = where

        results = self.collection.query(**query_kwargs)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        hits: List[Dict[str, str]] = []
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append(
                {
                    "title": meta.get("title", "Legal Reference"),
                    "content": doc,
                    "score": max(0.0, 1 - float(dist)) if dist is not None else 0.0,
                    "metadata": meta,
                }
            )
        return hits

    # ------------------------------------------------------------------ #
    def is_empty(self) -> bool:
        return self.collection.count() == 0

    # ------------------------------------------------------------------ #
    def process_and_embed_document(self, file_path: str | Path, session_id: Optional[str] = None) -> Dict[str, int]:
        """Extract text from `file_path`, chunk, and add to the Chroma collection.

        Returns a small summary dict: { inserted_chunks: int }
        """
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(str(p))

        name = p.name
        text = ""
        # Try PDF first
        if p.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(p))
                parts: List[str] = []
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    parts.append(page_text)
                text = _clean_text("\n".join(parts))
            except Exception:
                text = ""
        elif p.suffix.lower() in (".txt",):
            text = _clean_text(p.read_text(encoding="utf-8", errors="ignore"))
        elif p.suffix.lower() in (".docx",):
            try:
                import docx

                doc = docx.Document(str(p))
                parts = [para.text for para in doc.paragraphs]
                text = _clean_text("\n".join(parts))
            except Exception:
                text = ""

        # If text extraction empty and unstructured available, try partition
        if not text:
            try:
                from unstructured.partition.pdf import partition_pdf

                elements = partition_pdf(str(p))
                text = _clean_text("\n".join([str(el) for el in elements]))
            except Exception:
                pass

        if not text:
            # last resort: read raw bytes
            try:
                text = _clean_text(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                text = ""

        if not text:
            return {"inserted_chunks": 0}

        chunks = _chunk_text(text)
        docs = []
        for i, c in enumerate(chunks):
            docs.append(
                {
                    "content": c,
                    "title": f"{name}::chunk-{i}",
                    "metadata": {"source": name, "chunk_id": i, **({"session_id": session_id} if session_id else {})},
                }
            )

        self.add(docs)
        return {"inserted_chunks": len(docs)}
