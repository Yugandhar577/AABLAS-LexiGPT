import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from unstructured.partition.pdf import partition_pdf

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except Exception:
    class RecursiveCharacterTextSplitter:
        """Lightweight fallback splitter when langchain is unavailable."""

        def __init__(self, chunk_size=1000, chunk_overlap=150, separators=None):
            self.chunk_size = int(chunk_size)
            self.chunk_overlap = int(chunk_overlap)
            self.separators = separators or []

        def split_text(self, text: str):
            if not text:
                return []
            text = text.strip()
            if len(text) <= self.chunk_size:
                return [text]

            chunks = []
            step = max(1, self.chunk_size - self.chunk_overlap)
            start = 0
            text_len = len(text)
            while start < text_len:
                end = start + self.chunk_size
                chunk = text[start:end]
                chunks.append(chunk)
                if end >= text_len:
                    break
                start += step
            return chunks


REPO_ROOT = Path(__file__).resolve().parent.parent
PDF_FOLDER = REPO_ROOT / "data" / "pdfs"
DB_DIR = REPO_ROOT / "vector_data"
EMBED_MODEL = "BAAI/bge-large-en"

print("Loading embedding model...")
model = SentenceTransformer(EMBED_MODEL)


def clean_text(text):
    import re

    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = text.replace("\x0c", "")
    return text.strip()


def extract_pdf_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
        return clean_text(text)
    except Exception:
        return ""


def partition_pdf_text(pdf_path):
    try:
        elements = partition_pdf(pdf_path)
        text = "\n".join([str(element) for element in elements])
        return clean_text(text)
    except Exception as exc:
        print(f"[WARNING] Unstructured failed for {pdf_path}: {exc}")
        return extract_pdf_text(pdf_path)


def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\nSection", "SECTION", "\nSec", "Article", "ARTICLE", "\n\n", "\n", ". "],
    )
    return splitter.split_text(text)


client = chromadb.Client(
    Settings(
        is_persistent=True,
        persist_directory=str(DB_DIR),
    )
)

collection = client.get_or_create_collection(
    name="indian_law_docs",
    metadata={"hnsw:space": "cosine"},
)


def process_pdf(pdf_path):
    pdf_name = os.path.basename(pdf_path)
    print(f"Processing: {pdf_name}")

    text = partition_pdf_text(pdf_path)
    if not text.strip():
        print("Could not extract text")
        return

    chunks = chunk_text(text)
    print(f" - Total chunks: {len(chunks)}")

    embeddings = model.encode(chunks).tolist()
    ids = [f"{pdf_name}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": pdf_name, "chunk_id": i} for i in range(len(chunks))]

    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)
    print(f"Inserted {len(chunks)} chunks into ChromaDB.")


def main():
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDFs found in folder:", PDF_FOLDER)
        return

    print(f"Found {len(pdf_files)} PDF files.")

    for pdf in pdf_files:
        pdf_path = os.path.join(PDF_FOLDER, pdf)
        process_pdf(pdf_path)

    client.persist()
    print("Done. Your ChromaDB is ready at:", DB_DIR)


if __name__ == "__main__":
    main()