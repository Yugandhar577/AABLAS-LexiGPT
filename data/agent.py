import time
import json
import os
import sys
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Ensure project root is on sys.path so sibling imports work when running
# this file as a script (python data/agent.py) or as a module.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Reuse utilities from the existing ingestion script. Try the package-style
# import first (when running under Flask/app context), otherwise fall back
# to importing the module directly when running as a script.
try:
    from data.build_law_chromadb import (
        PDF_FOLDER,
        DB_DIR,
        partition_pdf_text,
        chunk_text,
        model,
        collection,
        process_pdf,
    )
except Exception:
    from build_law_chromadb import (
        PDF_FOLDER,
        DB_DIR,
        partition_pdf_text,
        chunk_text,
        model,
        collection,
        process_pdf,
    )

LOG_PATH = Path("data/agent_logs.jsonl")


class SimpleIngestAgent:
    """A simple Observe -> Decide -> Act agent for ingesting PDFs.

    - Observe: list files and metadata
    - Decide: rank/prioritize files (rule-based)
    - Act: run ingestion skills (extract/chunk/embed/store)
    """

    def __init__(self, pdf_dir: str = PDF_FOLDER, max_files: Optional[int] = None, poll_interval: float = 10.0):
        self.pdf_dir = Path(pdf_dir)
        self.max_files = max_files
        self.poll_interval = poll_interval
        self._stop = False
        self._lock = threading.Lock()
        # Retry / backoff configuration and embedding batch size
        self.max_retries = int(os.environ.get("AGENT_MAX_RETRIES", "3"))
        self.backoff_factor = float(os.environ.get("AGENT_BACKOFF_FACTOR", "1.5"))
        self.embed_batch_size = int(os.environ.get("AGENT_EMBED_BATCH", "32"))

    # -----------------
    # Observations
    # -----------------
    def observe(self) -> List[Path]:
        files = [p for p in self.pdf_dir.glob("*.pdf")]
        # attach stat information for use in decision
        return files

    # -----------------
    # Planner / Decision
    # -----------------
    def decide(self, candidates: List[Path]) -> List[Path]:
        # Rule-based: prioritize newer files, then larger size
        ranked = sorted(candidates, key=lambda p: (p.stat().st_mtime, p.stat().st_size), reverse=True)
        if self.max_files:
            ranked = ranked[: self.max_files]
        # Log decision
        self._log({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "decide",
            "reason": "rule-based: newer then larger",
            "candidates": [str(p) for p in ranked],
            "status": "planned",
        })
        return ranked

    # -----------------
    # Skills / Act
    # -----------------
    def extract_skill(self, pdf_path: str) -> str:
        # partition_pdf_text is a wrapper that falls back to pypdf
        return partition_pdf_text(pdf_path)

    def chunk_skill(self, text: str) -> List[str]:
        return chunk_text(text)

    def embed_skill(self, chunks: List[str]) -> List[List[float]]:
        # model is imported from build_law_chromadb (SentenceTransformer)
        if not chunks:
            return []
        out = []
        total = len(chunks)
        for i in range(0, total, self.embed_batch_size):
            batch = chunks[i : i + self.embed_batch_size]
            emb = model.encode(batch)
            out.extend(emb.tolist())
            # per-batch progress log
            self._log({
                "ts": datetime.now(timezone.utc).isoformat(),
                "action": "embed_batch",
                "batch_start": i,
                "batch_size": len(batch),
                "total_chunks": total,
                "status": "completed",
            })
        return out

    def store_skill(self, pdf_name: str, chunks: List[str], embeddings: List[List[float]]):
        ids = [f"{pdf_name}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": pdf_name, "chunk_id": i} for i in range(len(chunks))]
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)

    def act(self, target: Path):
        target_str = str(target)
        overall_start = time.time()
        self._log({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "process_start",
            "target": target_str,
            "status": "started",
            "reason": "processing file",
        })

        # 1) Extract with retries
        extract_text = ""
        extract_error = None
        extract_start = time.time()
        for attempt in range(1, self.max_retries + 1):
            try:
                extract_text = self.extract_skill(target_str)
                extract_error = None
                break
            except Exception as e:
                extract_error = repr(e)
                backoff = self.backoff_factor ** (attempt - 1)
                self._log({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "action": "extract_retry",
                    "target": target_str,
                    "attempt": attempt,
                    "error": extract_error,
                    "reason": f"retrying extract (backoff {backoff}s)",
                })
                time.sleep(backoff)

        extract_duration = round(time.time() - extract_start, 2)
        self._log({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "extract_end",
            "target": target_str,
            "status": "failed" if extract_error else "completed",
            "duration": extract_duration,
            "output_chars": len(extract_text) if extract_text else 0,
            "error": extract_error,
        })

        if extract_error or not extract_text.strip():
            self._log({
                "ts": datetime.utcnow().isoformat(),
                "action": "process_end",
                "target": target_str,
                "status": "failed",
                "reason": "extract_failed_or_empty",
            })
            return

        # 2) Chunk
        chunk_start = time.time()
        chunks = []
        chunk_error = None
        try:
            chunks = self.chunk_skill(extract_text)
        except Exception as e:
            chunk_error = repr(e)
        chunk_duration = round(time.time() - chunk_start, 2)
        self._log({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "chunk_end",
            "target": target_str,
            "status": "failed" if chunk_error else "completed",
            "duration": chunk_duration,
            "num_chunks": len(chunks),
            "error": chunk_error,
        })

        if chunk_error or not chunks:
            self._log({
                "ts": datetime.utcnow().isoformat(),
                "action": "process_end",
                "target": target_str,
                "status": "failed",
                "reason": "chunk_failed_or_empty",
            })
            return

        # 3) Embed with retries
        embed_start = time.time()
        embeddings = []
        embed_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                embeddings = self.embed_skill(chunks)
                embed_error = None
                break
            except Exception as e:
                embed_error = repr(e)
                backoff = self.backoff_factor ** (attempt - 1)
                self._log({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "action": "embed_retry",
                    "target": target_str,
                    "attempt": attempt,
                    "error": embed_error,
                    "reason": f"retrying embed (backoff {backoff}s)",
                })
                time.sleep(backoff)

        embed_duration = round(time.time() - embed_start, 2)
        self._log({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "embed_end",
            "target": target_str,
            "status": "failed" if embed_error else "completed",
            "duration": embed_duration,
            "num_embeddings": len(embeddings),
            "error": embed_error,
        })

        if embed_error or not embeddings:
            self._log({
                "ts": datetime.utcnow().isoformat(),
                "action": "process_end",
                "target": target_str,
                "status": "failed",
                "reason": "embed_failed_or_empty",
            })
            return

        # 4) Store
        store_start = time.time()
        store_error = None
        try:
            pdf_name = os.path.basename(target_str)
            ids = [f"{pdf_name}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": pdf_name, "chunk_id": i} for i in range(len(chunks))]
            collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)
        except Exception as e:
            store_error = repr(e)
        store_duration = round(time.time() - store_start, 2)
        self._log({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "store_end",
            "target": target_str,
            "status": "failed" if store_error else "completed",
            "duration": store_duration,
            "num_documents": len(chunks),
            "error": store_error,
        })

        overall_duration = round(time.time() - overall_start, 2)
        final_status = "failed" if (extract_error or chunk_error or embed_error or store_error) else "completed"
        self._log({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "process_end",
            "target": target_str,
            "status": final_status,
            "duration": overall_duration,
        })

    # -----------------
    # Run loop
    # -----------------
    def run_once(self):
        candidates = self.observe()
        if not candidates:
            self._log({"ts": datetime.utcnow().isoformat(), "action": "idle", "status": "no_pdfs"})
            return
        plan = self.decide(candidates)
        for pdf in plan:
            if self._stop:
                break
            self.act(pdf)

    def run(self):
        self._log({"ts": datetime.utcnow().isoformat(), "action": "agent_start", "status": "running"})
        try:
            while not self._stop:
                try:
                    self.run_once()
                except Exception as e:
                    # Log and continue
                    self._log({"ts": datetime.utcnow().isoformat(), "action": "loop_error", "error": repr(e)})
                time.sleep(self.poll_interval)
        finally:
            self._log({"ts": datetime.utcnow().isoformat(), "action": "agent_stop", "status": "stopped"})

    def stop(self):
        with self._lock:
            self._stop = True

    # -----------------
    # Logging / explainability
    # -----------------
    def _log(self, entry: Dict[str, Any]):
        entry.setdefault("ts", datetime.utcnow().isoformat())
        Path(LOG_PATH.parent).mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(json.dumps(entry, ensure_ascii=False))


def demo_run_once(max_files: Optional[int] = None):
    agent = SimpleIngestAgent(max_files=max_files)
    agent.run_once()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--run", action="store_true", help="Run continuously")
    p.add_argument("--once", action="store_true", help="Run one iteration and exit")
    p.add_argument("--max-files", type=int, default=None, help="Max files to process per iteration")
    args = p.parse_args()

    agent = SimpleIngestAgent(max_files=args.max_files)
    if args.run:
        try:
            agent.run()
        except KeyboardInterrupt:
            agent.stop()
    else:
        agent.run_once()
