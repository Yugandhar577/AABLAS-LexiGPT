from flask import Blueprint, jsonify, request, Response
import re
import threading

from config import DEFAULT_CHAT_SYSTEM_PROMPT
from services import chat_history
from services.ollama_services import llm_chat, query_ollama_with_rag, stream_llm_chat
from uuid import uuid4

# In-memory registry for pending streams. Structure: { stream_id: { message, session_id, history } }
_STREAM_REGISTRY = {}

bp = Blueprint("chat", __name__, url_prefix="/api")


@bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id")
    mode = data.get("mode", "chat")
    explain = data.get("explain", False)

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    # DOCUMENT GENERATION DETECTION
    # Check if user is asking to generate/create a document (PDF, contract, etc.)
    doc_keywords = r'\b(create|generate|make|produce|draft|write|build|prepare)\b.*\b(pdf|document|contract|agreement|form|template|file|report|invoice|receipt|deed|lease|rental|license)\b'
    doc_match = re.search(doc_keywords, user_message.lower())
    
    if doc_match:
        # Route to agent planning pipeline instead of simple chat
        try:
            from services.agent_services import plan_and_run
            
            # Store user message in chat history immediately
            session_id = chat_history.ensure_session(session_id, user_message[:60])
            chat_history.append_message(session_id, "user", user_message)
            chat_history.append_message(
                session_id, 
                "assistant", 
                "Document generation started. Check Agent Logs for progress..."
            )
            
            # Transform the user request into an agent goal
            goal = (
                f"The user is asking you to create a document. Their request: {user_message}\n\n"
                f"Plan the steps to gather any required information, ask the user for missing details if needed, "
                f"and then generate a downloadable document using the doc_generate tool."
            )
            
            # Launch agent planning in background thread (non-blocking)
            def run_agent_async():
                try:
                    plan_and_run(goal)  # This emits SSE events as it runs
                except Exception as e:
                    print(f"Background agent error: {e}")
            
            thread = threading.Thread(target=run_agent_async, daemon=True)
            thread.start()
            
            # Return immediately with streaming flag
            return jsonify({
                "response": "Document generation started. Check Agent Logs for progress...",
                "session_id": session_id,
                "is_document_generation": True
            })
        except Exception as e:
            # Fall back to regular chat if agent fails
            print(f"Agent pipeline error: {e}")
            pass

    history = []
    if session_id:
        session = chat_history.get_session(session_id)
        if session:
            history = session.get("messages", [])

    session_id = chat_history.ensure_session(session_id, user_message[:60])
    chat_history.append_message(session_id, "user", user_message)

    if mode == "rag":
        rag_payload = query_ollama_with_rag(user_message, session_id=session_id)
        bot_response = rag_payload["answer"]
    else:
        bot_response = llm_chat(
            DEFAULT_CHAT_SYSTEM_PROMPT,
            user_message,
            history=history,
        )
        rag_payload = {}

    chat_history.append_message(session_id, "assistant", bot_response)

    # If caller requested an explanation/chain-of-thought, try to generate
    # a structured explanation for the last assistant message and return it.
    if explain:
        # Find the last assistant message in session history
        session = chat_history.get_session(session_id)
        assistant_text = ""
        if session:
            for m in reversed(session.get("messages", [])):
                if m.get("role") == "assistant":
                    assistant_text = m.get("text") or m.get("content") or ""
                    break

        if assistant_text:
            # Provide context docs (if any) so the explainer can reference sources
            sources = rag_payload.get("sources", []) if rag_payload else []
            cot_text = llm_chat(
                "You are an explainer. Explain the response in a structured way, with reasoning and any sources.",
                f"Response: {assistant_text}\n\nSources: {sources}",
            )
            return jsonify({
                "response": bot_response,
                "session_id": session_id,
                "explain": cot_text,
                "sources": sources,
            })

    return jsonify({
        "response": bot_response,
        "session_id": session_id,
        "sources": rag_payload.get("sources", []) if rag_payload else [],
    })
