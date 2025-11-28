"""
services/chat_history.py
Simple JSON-backed store for chat sessions.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from config import CHAT_HISTORY_FILE

CHAT_PATH = Path(CHAT_HISTORY_FILE)
CHAT_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load() -> Dict[str, Dict]:
    if not CHAT_PATH.exists():
        return {}
    try:
        with CHAT_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError:
        return {}


def _save(data: Dict[str, Dict]) -> None:
    with CHAT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def list_sessions() -> List[Dict]:
    chats = _load()
    sessions = []
    for sid, payload in chats.items():
        sessions.append(
            {
                "session_id": sid,
                "title": payload.get("title", "Untitled conversation"),
                "updated_at": payload.get("updated_at", 0),
            }
        )
    sessions.sort(key=lambda item: item["updated_at"], reverse=True)
    return sessions


def get_session(session_id: str) -> Optional[Dict]:
    chats = _load()
    return chats.get(session_id)


def _generate_session_id() -> str:
    return f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"


def create_session(title: str = "New chat", first_message: Optional[str] = None) -> str:
    chats = _load()
    session_id = _generate_session_id()
    chats[session_id] = {
        "title": title.strip() or "New chat",
        "messages": [],
        "updated_at": time.time(),
    }
    if first_message:
        chats[session_id]["messages"].append({"role": "user", "text": first_message})
    _save(chats)
    return session_id


def append_message(session_id: str, role: str, text: str) -> None:
    chats = _load()
    if session_id not in chats:
        chats[session_id] = {"title": text[:40] or "Chat", "messages": [], "updated_at": time.time()}
    chats[session_id]["messages"].append({"role": role, "text": text})
    chats[session_id]["updated_at"] = time.time()
    if role == "user" and len(chats[session_id]["messages"]) == 1:
        chats[session_id]["title"] = text[:48] + ("..." if len(text) > 48 else "")
    _save(chats)


def ensure_session(session_id: Optional[str], fallback_title: str) -> str:
    if session_id and get_session(session_id):
        return session_id
    return create_session(fallback_title)

