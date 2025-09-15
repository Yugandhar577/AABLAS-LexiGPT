import subprocess
from config import OLLAMA_MODEL

def query_ollama(prompt):
    """
    Calls Ollama locally with the given prompt and returns the response.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, prompt],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"
