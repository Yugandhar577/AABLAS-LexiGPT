# import subprocess
# from config import OLLAMA_MODEL

# def query_ollama(prompt):
#     """
#     Calls Ollama locally with the given prompt and returns the response.
#     """
#     try:
#         result = subprocess.run(
#             ["ollama", "run", OLLAMA_MODEL, prompt],
#             capture_output=True,
#             text=True
#         )
#         return result.stdout.strip()
#     except Exception as e:
#         return f"Error: {str(e)}"

"""
services/ollama_services.py
Unified Ollama interface:
- Uses `ollama` Python package if available
- Falls back to subprocess call if not
"""

import os
import subprocess
from typing import Dict, Any

# Configuration
MODEL_NAME = os.environ.get("LEXIGPT_LOCAL_MODEL", "llama3:instruct")
TEMPERATURE = float(os.environ.get("LEXIGPT_TEMPERATURE", 0.2))

# Try importing ollama; fallback handled below
USE_SUBPROCESS = False
try:
    from config import OLLAMA_MODEL
except ImportError:
    USE_SUBPROCESS = True


def query_ollama(prompt: str) -> str:
    """
    Calls Ollama locally with a given prompt using subprocess.
    Used if `ollama` package is unavailable.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, prompt],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error (subprocess): {str(e)}"


def llm_chat(system: str, user: str, temperature: float | None = None) -> str:
    """
    Unified chat wrapper. Uses ollama Python SDK if available, else subprocess.
    system: system prompt string
    user: user prompt string
    """
    temp = temperature if temperature is not None else TEMPERATURE

    # If ollama package is available
    if not USE_SUBPROCESS:
        try:
            resp = OLLAMA_MODEL.chat(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                options={"temperature": temp},
            )
            return resp["message"]["content"]
        except Exception as e:
            return f"Error (ollama SDK): {str(e)}"

    # Fallback: subprocess
    combined_prompt = f"System: {system}\nUser: {user}"
    return query_ollama(combined_prompt)


if __name__ == "__main__":
    # Test call
    system_prompt = "You are LexiGPT, a local legal AI assistant."
    user_prompt = "Explain the concept of 'habeas corpus' in simple terms."
    print(llm_chat(system_prompt, user_prompt))
