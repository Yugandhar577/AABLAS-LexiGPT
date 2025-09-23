from flask import Flask, request, jsonify
import json, os, time

app = Flask(__name__)
CHAT_FILE = "chat_history.json"

# Helper to load/save
def load_chats():
    if not os.path.exists(CHAT_FILE):
        return {}
    with open(CHAT_FILE, "r") as f:
        return json.load(f)

def save_chats(chats):
    with open(CHAT_FILE, "w") as f:
        json.dump(chats, f, indent=4)

@app.route("/new_chat", methods=["POST"])
def new_chat():
    data = request.json
    first_message = data.get("message", "")
    session_id = f"session_{int(time.time())}"
    chats = load_chats()
    chats[session_id] = {
        "title": first_message[:25] + "...",
        "messages": [{"role": "user", "text": first_message}]
    }
    save_chats(chats)
    return jsonify({"session_id": session_id})

@app.route("/add_message", methods=["POST"])
def add_message():
    data = request.json
    session_id = data["session_id"]
    role = data["role"]
    text = data["text"]

    chats = load_chats()
    if session_id not in chats:
        return jsonify({"error": "session not found"}), 404
    chats[session_id]["messages"].append({"role": role, "text": text})
    save_chats(chats)
    return jsonify({"status": "ok"})

@app.route("/get_chat/<session_id>", methods=["GET"])
def get_chat(session_id):
    chats = load_chats()
    if session_id not in chats:
        return jsonify({"error": "not found"}), 404
    return jsonify(chats[session_id])

@app.route("/list_chats", methods=["GET"])
def list_chats():
    chats = load_chats()
    return jsonify([
        {"session_id": sid, "title": data["title"]}
        for sid, data in chats.items()
    ])

if __name__ == "__main__":
    app.run(debug=True)
