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

def create_app():
    """Flask app factory."""
    app = Flask(__name__)
    CORS(app)  # Enable cross-origin requests for frontend

    # Register routes
    app.register_blueprint(chat_bp)
    app.register_blueprint(rag_bp)

    return app


if __name__ == "__main__":
    app = create_app()

    print("Flask backend running on http://localhost:5000")
    print("Available routes:")
    print(" - /chat           (basic Ollama query)")
    print(" - /rag-query      (RAG: Chroma + LLaMA 3 answer generation)")

    app.run(host="0.0.0.0", port=5000, debug=True)
