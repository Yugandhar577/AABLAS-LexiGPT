# routes/rag_routes.py

from flask import Blueprint, request, jsonify, current_app
from services.ollama_services import query_ollama_with_rag
from pathlib import Path
from rag.vector_db import VectorDB

bp = Blueprint("rag", __name__, url_prefix="/api")


@bp.route("/rag-query", methods=["POST"])
def rag_query():
    """
    Endpoint for RAG pipeline.
    Expects JSON: { "query": "your question" }
    """
    data = request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "Missing 'query' field"}), 400

    result = query_ollama_with_rag(query)
    return jsonify(result)


@bp.route("/upload", methods=["POST"])
def upload_and_index():
    """Accept multipart/form-data with files under key 'files'.

    Optional form field: session_id — will be stored with document metadata
    Returns inserted chunk counts per file.
    """
    files = request.files.getlist("files")
    session_id = request.form.get("session_id") or request.args.get("session_id")

    if not files:
        return jsonify({"error": "No files provided. Use 'files' field."}), 400

    save_dir = Path("data/pdfs")
    save_dir.mkdir(parents=True, exist_ok=True)

    # instantiate VectorDB against local vector store
    vdb = VectorDB(Path("vector_data"), collection_name="lexigpt_legal_corpus")

    results = []
    for f in files:
        filename = f.filename or "uploaded_file"
        dest = save_dir / filename
        # avoid overwriting by appending counter if necessary
        if dest.exists():
            base = dest.stem
            suf = dest.suffix
            counter = 1
            while True:
                candidate = save_dir / f"{base}_{counter}{suf}"
                if not candidate.exists():
                    dest = candidate
                    break
                counter += 1
        f.save(str(dest))

        try:
            out = vdb.process_and_embed_document(dest, session_id=session_id)
            results.append({"file": dest.name, "inserted_chunks": out.get("inserted_chunks", 0)})
        except Exception as e:
            results.append({"file": dest.name, "error": str(e)})

    return jsonify({"status": "ok", "results": results})
