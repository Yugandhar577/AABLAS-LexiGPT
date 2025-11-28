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


def query_ollama(prompt: str) -> str:
    """Compatibility helper for legacy callers."""
    return llm_chat(system_prompt=None, user_prompt=prompt)


def query_ollama_with_rag(user_query: str, top_k: int = 3) -> dict:
    """
    Uses the RAG pipeline to ground the response in legal context.
    Returns the answer and the snippets that were supplied to the model.
    """
    context_docs = get_relevant_context(user_query, top_k=top_k)
    context_text = "\n\n".join(context_docs) or "No relevant context found."

    prompt = (
        "Use ONLY the provided Indian legal context to answer the user's question. "
        "Cite the section titles in brackets when possible. "
        "If the context is insufficient, explicitly say so."
        f"\n\nContext:\n{context_text}\n\nQuestion:\n{user_query}\n\nAnswer:"
    )

    answer = llm_chat(DEFAULT_CHAT_SYSTEM_PROMPT, prompt)
    return {
        "question": user_query,
        "answer": answer,
        "context": context_docs,
    }
