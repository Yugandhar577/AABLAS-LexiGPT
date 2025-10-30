# rag/rag_pipeline.py
"""
RAG pipeline using ChromaDB (retriever) + Ollama (Llama 3 model)
"""

from rag.retriever import retrieve_from_chroma
import subprocess
from config import OLLAMA_MODEL


def query_ollama(prompt: str):
    """
    Calls Ollama locally with the given prompt and returns the model's response.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, prompt],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error querying Ollama: {e}"


def generate_rag_response(question: str, n_results: int = 3):
    """
    Main RAG logic:
    1. Retrieves top matching context from Chroma
    2. Builds a contextual prompt
    3. Sends prompt to Ollama model
    4. Returns the model's grounded answer
    """
    # Step 1: Retrieve from Chroma
    context, raw_results = retrieve_from_chroma(question, n_results=n_results)

    # Step 2: Construct grounded prompt
    prompt = f"""
You are a legal AI assistant trained on Indian Motor Vehicle laws.

Use the following context from the official legal database to answer the question.
Be precise, factual, and cite relevant sections when possible.
If the answer cannot be found, say "The context does not specify that information."

---------------------
CONTEXT:
{context}
---------------------

QUESTION:
{question}

FINAL ANSWER (cite section titles if relevant):
    """

    # Step 3: Query Ollama
    answer = query_ollama(prompt)

    # Step 4: Return structured response
    return {
        "question": question,
        "answer": answer,
        "context": context
    }
