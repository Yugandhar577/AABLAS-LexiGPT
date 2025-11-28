"""
services/ollama_services.py
Utility helpers to talk to the local Ollama runtime.
"""

from __future__ import annotations

import json
import subprocess
from typing import Dict, List, Optional

import requests

from config import (
    DEFAULT_CHAT_SYSTEM_PROMPT,
    OLLAMA_HOST,
    OLLAMA_MODEL,
)
from rag.rag_pipeline import get_relevant_context


def _normalise_history(history: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    normalised = []
    if not history:
        return normalised
    for item in history:
        role = item.get("role", "").lower()
        content = item.get("content") or item.get("text") or ""
        if role in {"user", "assistant", "system"} and content:
            normalised.append({"role": role, "content": content})
    return normalised


def _build_messages(
    system_prompt: Optional[str],
    user_prompt: str,
    history: Optional[List[Dict[str, str]]],
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(_normalise_history(history))
    messages.append({"role": "user", "content": user_prompt})
    return messages


def _chat_via_http(
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    response = requests.post(
        f"{OLLAMA_HOST.rstrip('/')}/api/chat", json=payload, timeout=120
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "message" in data:
        return data["message"]["content"]
    # When streaming is disabled, Ollama still returns a dict with `message`.
    # If something unexpected occurs, return the raw payload for visibility.
    return json.dumps(data)


def _chat_via_cli(messages: List[Dict[str, str]]) -> str:
    prompt_lines = []
    for msg in messages:
        prompt_lines.append(f"{msg['role'].upper()}: {msg['content']}")
    prompt_lines.append("ASSISTANT:")
    prompt = "\n".join(prompt_lines)
    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL, prompt],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or result.stderr.strip()


def llm_chat(
    system_prompt: Optional[str],
    user_prompt: str,
    history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.15,
    max_tokens: int = 768,
) -> str:
    """General-purpose chat helper with graceful HTTP/CLI fallback."""
    messages = _build_messages(system_prompt, user_prompt, history)
    try:
        return _chat_via_http(messages, temperature, max_tokens)
    except Exception:
        return _chat_via_cli(messages)


def stream_llm_chat(
    system_prompt: Optional[str],
    user_prompt: str,
    history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.15,
    max_tokens: int = 768,
):
    """Stream tokens from the Ollama HTTP API as a generator of text chunks.

    Yields decoded text chunks (strings). The caller can accumulate them
    to form the final assistant output.
    """
    messages = _build_messages(system_prompt, user_prompt, history)
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    resp = requests.post(
        f"{OLLAMA_HOST.rstrip('/')}/api/chat", json=payload, stream=True, timeout=120
    )
    resp.raise_for_status()

    # Ollama returns a chunked/ndjson-like stream. Iterate lines and try to
    # extract sensible text for each line; fall back to raw line text.
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        token = None
        try:
            data = json.loads(line)
            # flexible extraction depending on Ollama's streaming format
            if isinstance(data, dict):
                if "text" in data and data["text"]:
                    token = data["text"]
                elif "message" in data and isinstance(data["message"], dict):
                    msg = data["message"]
                    # message.content may be a string or structure
                    if isinstance(msg.get("content"), str):
                        token = msg.get("content")
                    else:
                        token = json.dumps(msg.get("content", ""))
        except Exception:
            # Not JSON or unexpected shape — use the raw line
            token = None

        if token is None:
            token = line

        yield token


def query_ollama(prompt: str) -> str:
    """Compatibility helper for legacy callers."""
    return llm_chat(system_prompt=None, user_prompt=prompt)


def query_ollama_with_rag(user_query: str, top_k: int = 3) -> dict:
    """
    Uses the RAG pipeline to ground the response in legal context.
    Returns the answer and the snippets that were supplied to the model.
    """
    context_docs = get_relevant_context(user_query, top_k=top_k)

    if context_docs:
        # Build a numbered context block with short snippets
        context_text = "\n\n".join([f"[{d['id']}] {d['title']}\n{d['snippet']}" for d in context_docs])
    else:
        context_text = "No relevant context found."

    prompt = (
        "You are an expert legal assistant. Use ONLY the provided Indian legal context to answer the user's question. "
        "When you use a document, cite it by its numeric id in square brackets (e.g. [1]). "
        "If the context is insufficient to answer, say explicitly which information is missing. "
        "At the end, return a short JSON object (not additional commentary) with keys: sources (array of {id, title, snippet}), and answer (string).\n\n"
        f"Context:\n{context_text}\n\nQuestion:\n{user_query}\n\nAnswer:"
    )

    answer = llm_chat(DEFAULT_CHAT_SYSTEM_PROMPT, prompt)
    return {
        "question": user_query,
        "answer": answer,
        "context": context_docs,
    }
