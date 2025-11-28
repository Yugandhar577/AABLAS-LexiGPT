from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Ollama / LLM settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Vector database + legal corpus
VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", str(BASE_DIR / "rag" / "vectordb"))
LEGAL_DATA_FILE = os.getenv("LEGAL_DATA_FILE", str(DATA_DIR / "combined.json"))

# Chat history persistence
CHAT_HISTORY_FILE = os.getenv("CHAT_HISTORY_FILE", str(DATA_DIR / "chat_history.json"))

# Prompt defaults
DEFAULT_CHAT_SYSTEM_PROMPT = os.getenv(
    "DEFAULT_CHAT_SYSTEM_PROMPT",
    "You are LexiGPT, an Indian legal assistant. Provide precise, well-structured, and citation-backed answers.",
)