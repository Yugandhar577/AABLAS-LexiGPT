from flask import Blueprint, jsonify, request

from services import chat_history

bp = Blueprint("chat_history", __name__, url_prefix="/api/chats")


@bp.route("", methods=["GET"])
def list_chats():
    return jsonify(chat_history.list_sessions())


@bp.route("", methods=["POST"])
def create_chat():
    data = request.get_json(force=True) or {}
    title = data.get("title") or data.get("message") or "New chat"
    message = data.get("message")
    session_id = chat_history.create_session(title=title, first_message=message)
    return jsonify({"session_id": session_id})


@bp.route("/<session_id>", methods=["GET"])
def get_chat(session_id: str):
    session = chat_history.get_session(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404
    return jsonify(session)


@bp.route("/<session_id>/messages", methods=["POST"])
def add_message(session_id: str):
    data = request.get_json(force=True) or {}
    role = data.get("role")
    text = data.get("text", "")
    if role not in {"user", "assistant"} or not text:
        return jsonify({"error": "role/text required"}), 400
    chat_history.append_message(session_id, role, text)
    return jsonify({"status": "ok"})
