# chroma_init.py
"""
ChromaDB Initialization Script
------------------------------
This script initializes a persistent Chroma database
using the free built-in embedding model (DefaultEmbeddingFunction).

It will create (or load, if already existing) a collection named 'law_docs'
that you can later use for adding, querying, or deleting documents.
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

CHROMA_PERSIST_DIR = "./chroma_db"      # local folder where data will be stored
COLLECTION_NAME = "law_docs"            # collection name for legal documents


def init_chroma():
    """
    Initialize Chroma client and collection with default (free) embeddings.
    Returns the collection object, ready for use.
    """
    client = chromadb.Client(Settings(persist_directory=CHROMA_PERSIST_DIR))

    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )

    print(f"ChromaDB initialized successfully.")
    print(f"Persistence directory: {CHROMA_PERSIST_DIR}")
    print(f"Collection ready: '{COLLECTION_NAME}'")
    return client, collection



if __name__ == "__main__":
    client, collection = init_chroma()

    collection.add(
        documents=["This is a sample legal text about contract law."],
        ids=["sample_doc_1"]
    )

    print("Current document count:", collection.count())
