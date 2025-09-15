from flask import Flask
from routes.ollama_routes import bp as chat_bp
from flask_cors import CORS  # NEW

def create_app():
    app = Flask(__name__)
    CORS(app)  # Allow frontend to call backend
    app.register_blueprint(chat_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
