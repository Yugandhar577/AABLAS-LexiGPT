from flask import Blueprint, request, jsonify
from services.ollama_services import query_ollama

bp = Blueprint("chat", __name__)

@bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"response": "No message received"}), 400

    bot_response = query_ollama(user_message)

    return jsonify({"response": bot_response})
