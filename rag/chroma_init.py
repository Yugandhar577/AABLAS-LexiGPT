# chroma_init.py
"""
ChromaDB Initialization Script + JSON Data Loader
-------------------------------------------------
Initializes a persistent Chroma database using the free built-in
DefaultEmbeddingFunction, then loads data from combined.json into the collection.
"""

import os
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# ==============================
# CONFIGURATION
# ==============================
CHROMA_PERSIST_DIR = "./vector_data"  # local folder where data will be stored
COLLECTION_NAME = "law_docs"            # collection name for legal documents
JSON_FILE = "./rag/vectordb/combined.json"           # your JSON data file

# ==============================
# INITIALIZATION
# ==============================
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

    print("ChromaDB initialized successfully.")
    print(f"Persistence directory: {CHROMA_PERSIST_DIR}")
    print(f"Collection ready: '{COLLECTION_NAME}'")

    return client, collection


# ==============================
# DATA LOADING
# ==============================
def load_json_data(json_path):
    """
    Loads an array of items from combined.json.
    Each item should have 'title' and 'description'.
    Returns separate lists for docs, metadatas, and ids.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"❌ JSON file not found at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON structure is invalid — expected a list of items.")

    documents = []
    metadatas = []
    ids = []

    for i, item in enumerate(data):
        title = item.get("title", f"Untitled_{i}")
        desc = item.get("description", "").strip()

        if not desc:
            continue  # skip empty entries

        documents.append(desc)
        metadatas.append({"title": title})
        ids.append(f"doc_{i}")

    return documents, metadatas, ids


# ==============================
# MAIN EXECUTION
# ==============================
if __name__ == "__main__":
    client, collection = init_chroma()

    # Load data from JSON
    docs, metas, ids = load_json_data(JSON_FILE)
    print(f"Loaded {len(docs)} records from {JSON_FILE}")

    if docs:
        # Add to ChromaDB
        collection.add(documents=docs, metadatas=metas, ids=ids)
        print(f"✅ Added {len(docs)} items to ChromaDB collection '{COLLECTION_NAME}'")

        print("Total documents in collection:", collection.count())

        # Simple test query
        results = collection.query(
            query_texts=["motor vehicles act commencement"],
            n_results=2
        )

        print("🔍 Sample Query Results:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("⚠️ No valid records found in JSON.")
