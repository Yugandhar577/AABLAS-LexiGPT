# app.py
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

def query_ollama(prompt):
    """
    Calls Ollama locally with the given prompt and returns the response.
    """
    try:
        # Run ollama command and capture output as JSON
        result = subprocess.run(
            ["ollama", "run", "mistral", prompt],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"response": "No message received"}), 400

    bot_response = query_ollama(user_message)

    return jsonify({"response": bot_response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
