# from flask import Flask
# from routes.ollama_routes import bp as chat_bp
# from flask_cors import CORS  # NEW

# def create_app():
#     app = Flask(__name__)
#     CORS(app)  # Allow frontend to call backend
#     app.register_blueprint(chat_bp)
#     return app

# if __name__ == "__main__":
#     app = create_app()
#     app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask
from routes.ollama_routes import bp as chat_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Allow frontend (HTML/JS) to make API calls to Flask
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Register the Ollama route blueprint
    app.register_blueprint(chat_bp, url_prefix="/api")
    
    return app

if __name__ == "__main__":
    app = create_app()
    # Run Flask in debug mode for local testing
    app.run(host="0.0.0.0", port=5000, debug=True)
