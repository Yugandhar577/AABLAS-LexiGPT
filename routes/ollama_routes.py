from flask import Blueprint, jsonify, request

from config import DEFAULT_CHAT_SYSTEM_PROMPT
from services import chat_history
from services.ollama_services import llm_chat, query_ollama_with_rag

bp = Blueprint("chat", __name__, url_prefix="/api")


@bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id")
    mode = data.get("mode", "chat")

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    history = []
    if session_id:
        session = chat_history.get_session(session_id)
        if session:
            history = session.get("messages", [])

    session_id = chat_history.ensure_session(session_id, user_message[:60])
    chat_history.append_message(session_id, "user", user_message)

    if mode == "rag":
        rag_payload = query_ollama_with_rag(user_message)
        bot_response = rag_payload["answer"]
    else:
        bot_response = llm_chat(
            DEFAULT_CHAT_SYSTEM_PROMPT,
            user_message,
            history=history,
        )
        rag_payload = {}

    chat_history.append_message(session_id, "assistant", bot_response)

    return jsonify(
        {
            "response": bot_response,
            "session_id": session_id,
            "context": rag_payload.get("context"),
        }
    )
