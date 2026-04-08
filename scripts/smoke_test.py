import json
import sys

import requests


def main():
    base = "http://127.0.0.1:5000"
    print("Testing", base)
    try:
        print("\nPOST /api/chat")
        response = requests.post(base + "/api/chat", json={"message": "smoke test from script"})
        print("Status:", response.status_code)
        try:
            print("Response JSON:", json.dumps(response.json(), indent=2))
        except Exception:
            print("Response text:", response.text)

        print("\nGET /api/chats")
        response = requests.get(base + "/api/chats")
        print("Status:", response.status_code)
        try:
            docs = response.json()
            print("Chats count:", len(docs) if isinstance(docs, list) else "N/A")
            print("Sample:", json.dumps(docs[:2], indent=2))
        except Exception:
            print("Response text:", response.text)

    except Exception as exc:
        print("Error during smoke tests:", exc)
        sys.exit(2)


if __name__ == "__main__":
    main()