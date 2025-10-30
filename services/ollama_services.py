# services/ollama_services.py

import subprocess
from config import OLLAMA_MODEL
from rag.rag_pipeline import get_relevant_context  # helper from your retriever

def query_ollama(prompt: str) -> str:
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


def query_ollama_with_rag(user_query: str) -> dict:
    """
    Uses RAG (retrieval + generation) pipeline.
    1. Retrieves top documents from ChromaDB
    2. Feeds them into Ollama with a formatted system prompt
    3. Returns the answer + context
    """
    # Step 1: Get retrieved documents
    context_docs = get_relevant_context(user_query, top_k=3)
    context_text = "\n\n".join(context_docs)

    # Step 2: Construct augmented prompt
    prompt = f"""
You are a legal assistant. Use the context below to answer the question accurately.
If the answer is not in the context, say "The provided legal documents do not contain enough information."

Context:
{context_text}

Question:
{user_query}

Answer:
"""

    # Step 3: Query Ollama (LLaMA 3)
    answer = query_ollama(prompt)

    # Step 4: Return structured output
    return {
        "question": user_query,
        "answer": answer,
        "context": context_docs
    }
