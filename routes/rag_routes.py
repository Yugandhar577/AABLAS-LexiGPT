# routes/rag_routes.py

from flask import Blueprint, request, jsonify
from services.ollama_services import query_ollama_with_rag

bp = Blueprint("rag", __name__, url_prefix="/api")

@bp.route("/rag-query", methods=["POST"])
def rag_query():
    """
    Endpoint for RAG pipeline.
    Expects JSON: { "query": "your question" }
    """
    data = request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "Missing 'query' field"}), 400

    result = query_ollama_with_rag(query)
    return jsonify(result)
