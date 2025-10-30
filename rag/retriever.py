# retriever.py
"""
Retrieval layer for RAG
-----------------------
Loads the existing ChromaDB collection and provides a function to
retrieve the most relevant law sections for a user query.
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

CHROMA_PERSIST_DIR = "./rag/vectordb"
COLLECTION_NAME = "law_docs"

def load_collection():
    """Load existing Chroma collection."""
    client = chromadb.Client(Settings(persist_directory=CHROMA_PERSIST_DIR))
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )
    return collection


def retrieve_from_chroma(query, n_results=3):
    """Retrieve top N relevant documents."""
    collection = load_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    formatted_context = ""
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
        formatted_context += f"[{i+1}] {meta.get('title', 'Unknown')}\n{doc.strip()}\n\n"

    return formatted_context, results
