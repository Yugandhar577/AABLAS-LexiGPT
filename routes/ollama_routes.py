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

    # AGENTIC INTENT DETECTION
    # Detect intents that should be handled by the agent (document generation, summarization, analysis, ingestion)
    intent_keywords = r'\b(create|generate|make|produce|draft|write|build|prepare|summarize|summarise|analyze|analyse|ingest|index)\b'
    intent_match = re.search(intent_keywords, user_message.lower())

    if intent_match:
        verb = intent_match.group(1).lower()
        # Route to agent planning pipeline instead of simple chat
        try:
            from services.agent_services import plan_and_run

            # Store user message in chat history immediately
            session_id = chat_history.ensure_session(session_id, user_message[:60])
            
            # Extract uploaded file reference from recent chat history
            uploaded_file_ref = None
            if session_id:
                hist = chat_history.load_session(session_id)
                if hist:
                    # Look for "[Uploaded Documents]" messages in the history
                    for msg in reversed(hist.get("messages", [])):
                        if msg.get("role") == "user" and "[Uploaded Documents]" in msg.get("content", ""):
                            # Extract filename from message like "[Uploaded Documents] Yugandhar Resume V2.pdf: 4"
                            match = re.search(r'\[Uploaded Documents\]\s*([^\n:]+)', msg.get("content", ""))
                            if match:
                                uploaded_file_ref = match.group(1).strip()
                                break
            
            chat_history.append_message(session_id, "user", user_message)

            # Create domain-specific goals
            if verb in ("summarize", "summarise"):
                chat_history.append_message(session_id, "assistant", "Summarization started. Check Agent Logs for progress...")
                file_context = f"\n\nFile to summarize: {uploaded_file_ref}" if uploaded_file_ref else ""
                goal = (
                    f"The user requested a summary: {user_message}{file_context}\n\n"
                    "Plan the steps to locate any referenced files or content, ask the user for missing inputs if needed, "
                    "and then produce a concise, structured summary using the summarize_text tool."
                )
                response_flag = {"is_summarization": True}
            elif verb in ("analyze", "analyse"):
                chat_history.append_message(session_id, "assistant", "Analysis started. Check Agent Logs for progress...")
                goal = (
                    f"The user requested an analysis: {user_message}\n\n"
                    "Plan the steps to gather supporting documents or context, use RAG searches where appropriate, "
                    "and synthesize an analytical answer citing sources using synthesize_rag and reason steps."
                )
                response_flag = {"is_analysis": True}
            elif verb in ("ingest", "index"):
                chat_history.append_message(session_id, "assistant", "Ingestion started. Check Agent Logs for progress...")
                file_context = f"\n\nFile to ingest: {uploaded_file_ref}" if uploaded_file_ref else ""
                goal = (
                    f"The user requested ingestion/indexing: {user_message}{file_context}\n\n"
                    "Plan the steps to locate and read the files, extract metadata, and index documents into the vector DB. "
                    "If needed, ask the user for file locations or uploads."
                )
                response_flag = {"is_ingest": True}
            else:
                chat_history.append_message(session_id, "assistant", "Document generation started. Check Agent Logs for progress...")
                goal = (
                    f"The user is asking you to create a document. Their request: {user_message}\n\n"
                    f"Plan the steps to gather any required information, ask the user for missing details if needed, "
                    f"and then generate a downloadable document using the doc_generate tool."
                )
                response_flag = {"is_document_generation": True}

            # Launch agent planning in background thread (non-blocking)
            def run_agent_async():
                try:
                    import traceback
                    plan_and_run(goal)  # This emits SSE events as it runs
                except Exception as e:
                    print(f"Background agent error: {e}")
                    traceback.print_exc()

            thread = threading.Thread(target=run_agent_async, daemon=True)
            thread.start()

            # Return immediately with streaming flag indicating the intent
            payload = {"response": "Agent task started. Check Agent Logs for progress...", "session_id": session_id}
            payload.update(response_flag)
            return jsonify(payload)
        except Exception as e:
            # Fall back to regular chat if agent fails
            import traceback
            print(f"Agent pipeline routing error: {e}")
            traceback.print_exc()
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
            context_docs = rag_payload.get("context") if isinstance(rag_payload, dict) else None
            context_block = ""
            if context_docs:
                try:
                    # context_docs is expected to be a list of dicts with id/title/snippet
                    context_block = "\n\n".join([f"[{d.get('id')}] {d.get('title')}\n{d.get('snippet')}" for d in context_docs])
                except Exception:
                    context_block = ""

            expl_prompt = (
                "You are given an assistant answer and the supporting context documents (if any). Return a concise, human-readable "
                "step-by-step chain of thought explaining how the assistant arrived at the answer, and list explicit sources used. "
                "The response MUST be a JSON object with keys: chain_of_thought (string), sources (array of {id, title, snippet}). "
                "Do not add extra commentary outside the JSON."
                f"\n\nContext:\n{context_block}\n\nAssistant answer:\n{assistant_text}\n\nJSON:\n"
            )
            try:
                expl_text = llm_chat(None, expl_prompt)
                # try to parse JSON from the model output; fall back to raw text
                import json as _json

                parsed = None
                try:
                    parsed = _json.loads(expl_text)
                except Exception:
                    # attempt to find a JSON block in the output
                    start = expl_text.find('{')
                    end = expl_text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        try:
                            parsed = _json.loads(expl_text[start : end + 1])
                        except Exception:
                            parsed = {"raw": expl_text}

                return jsonify({"response": bot_response, "session_id": session_id, "context": rag_payload.get("context"), "explain": parsed})
            except Exception:
                return jsonify({"response": bot_response, "session_id": session_id, "context": rag_payload.get("context"), "explain": None})

    return jsonify(
        {
            "response": bot_response,
            "session_id": session_id,
            "context": rag_payload.get("context"),
        }
    )
