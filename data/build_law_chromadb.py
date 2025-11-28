import os
import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from unstructured.partition.pdf import partition_pdf
from langchain.text_splitter import RecursiveCharacterTextSplitter


# ==========================================================
# CONFIGURATION
# ==========================================================

PDF_FOLDER = "./data/pdfs"            # <-- Put all your legal PDFs here
DB_DIR = "./vector_data"       # <-- ChromaDB storage directory

# Choose your embedding model
EMBED_MODEL = "BAAI/bge-large-en"  # VERY GOOD
# EMBED_MODEL = "hkunlp/instructor-xl"  # BEST but heavy


# ==========================================================
# LOAD EMBEDDING MODEL
# ==========================================================

print("Loading embedding model...")
model = SentenceTransformer(EMBED_MODEL)


# ==========================================================
# CLEAN TEXT UTIL
# ==========================================================

def clean_text(text):
    """
    Cleans text extracted from PDFs.
    Removes page numbers, headers, multiple spaces, junk chars.
    """
    import re

    text = re.sub(r'\n+', '\n', text)                # remove multiple newlines
    text = re.sub(r'\s{2,}', ' ', text)              # remove multi spaces
    text = re.sub(r'Page \d+ of \d+', '', text)      # common footer
    text = text.replace("\x0c", "")                  # junk char in PDFs

    return text.strip()


# ==========================================================
# EXTRACT OR PARTITION PDF INTO TEXT
# ==========================================================

def extract_pdf_text(pdf_path):
    """Extract text using pypdf as fallback."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return clean_text(text)
    except:
        return ""


def partition_pdf_text(pdf_path):
    """Uses unstructured (much better for legal docs)."""
    try:
        elements = partition_pdf(pdf_path)
        text = "\n".join([str(el) for el in elements])
        return clean_text(text)
    except Exception as e:
        print(f"[WARNING] Unstructured failed for {pdf_path}: {e}")
        return extract_pdf_text(pdf_path)


# ==========================================================
# CHUNKING LOGIC — OPTIMIZED FOR LEGAL DOCUMENTS
# ==========================================================

def chunk_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=[
            "\nSection", "SECTION", "\nSec", "Article", "ARTICLE",
            "\n\n", "\n", ". "
        ],
    )
    return text_splitter.split_text(text)


# ==========================================================
# INITIALIZE CHROMA DB
# ==========================================================

client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=DB_DIR
    )
)

collection = client.get_or_create_collection(
    name="indian_law_docs",
    metadata={"hnsw:space": "cosine"}
)


# ==========================================================
# EMBED + STORE IN CHROMA
# ==========================================================

def process_pdf(pdf_path):
    pdf_name = os.path.basename(pdf_path)
    print(f"\n📘 Processing: {pdf_name}")

    # 1. extract
    text = partition_pdf_text(pdf_path)
    if not text.strip():
        print("❌ Could not extract text!")
        return

    # 2. chunk
    chunks = chunk_text(text)
    print(f" - Total chunks: {len(chunks)}")

    # 3. embed
    embeddings = model.encode(chunks).tolist()

    # 4. prepare metadata
    ids = [f"{pdf_name}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": pdf_name, "chunk_id": i} for i in range(len(chunks))]

    # 5. store in chroma
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=chunks
    )

    print(f" ✅ Inserted {len(chunks)} chunks into ChromaDB.")


# ==========================================================
# MAIN LOOP
# ==========================================================

def main():
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("❌ No PDFs found in folder:", PDF_FOLDER)
        return

    print(f"📂 Found {len(pdf_files)} PDF files.")

    for pdf in pdf_files:
        pdf_path = os.path.join(PDF_FOLDER, pdf)
        process_pdf(pdf_path)

    # Save the DB
    client.persist()
    print("\n🎉 DONE! Your ChromaDB is ready at:", DB_DIR)


if __name__ == "__main__":
    main()
