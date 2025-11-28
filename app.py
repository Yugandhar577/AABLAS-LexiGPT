# app.py
"""
Main Flask App
---------------
This file initializes the Flask application,
registers all blueprints (Ollama chat + RAG query),
and enables CORS for frontend access.
"""

from flask import Flask
from flask_cors import CORS

# Import routes
from routes.ollama_routes import bp as chat_bp       # regular Ollama chat route
from routes.rag_routes import bp as rag_bp           # new RAG query route
from routes.agent_routes import bp as agent_bp       # agentic planner
from routes.docgen_routes import bp as docgen_bp     # document generator
from routes.chat_history import bp as history_bp     # chat session CRUD

def create_app():
    """Flask app factory."""
    app = Flask(__name__)
    CORS(app)  # Enable cross-origin requests for frontend

    # Register routes
    app.register_blueprint(chat_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(docgen_bp)
    app.register_blueprint(history_bp)

    return app


if __name__ == "__main__":
    app = create_app()

    print("Flask backend running on http://localhost:5000")
    print("Available routes:")
    print(" - /api/chat             (chat with optional RAG)")
    print(" - /api/rag-query        (direct RAG endpoint)")
    print(" - /api/agent/plan-run   (planner -> executor loop)")
    print(" - /api/docgen           (legal template generator)")
    print(" - /api/chats            (chat history CRUD)")

    app.run(host="0.0.0.0", port=5000, debug=True)