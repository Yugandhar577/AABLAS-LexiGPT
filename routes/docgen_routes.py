"""
routes/docgen_routes.py
FastAPI-style routes for document generation with download capability.
"""

from flask import Blueprint, jsonify, request, send_file
import os

from services.docgen_services import generate_document
from utils.file_utils import get_full_document_path

bp = Blueprint("docgen", __name__, url_prefix="/api/docgen")


@bp.route("", methods=["POST"])
def create_document():
    """
    POST /api/docgen
    Generate a document from a JSON payload.
    
    Expected JSON payload:
    {
        "type": "pdf" | "docx" | "xlsx" | "pptx",
        "title": "Document Title",
        "content": [
            {"h1": "Heading 1"},
            {"h2": "Heading 2"},
            {"p": "Paragraph text"},
            {"bullet": ["item1", "item2", "item3"]},
            {"table": [["Col1", "Col2"], ["Data1", "Data2"]]}
        ]
    }
    
    Returns:
    {
        "status": "success",
        "file_path": "generated/abc123def456.pdf",
        "filename": "abc123def456.pdf"
    }
    """
    try:
      data = request.get_json(force=True) or {}

      # Normalize frontend payloads into canonical shape expected by generate_document()
      # Canonical shape: { "type": "pdf|docx|xlsx|pptx", "title": "...", "content": [ ... ] }
      doc_payload = {}

      # If frontend already sent canonical payload, use it directly
      if isinstance(data.get("type"), str) and isinstance(data.get("content"), list):
        doc_payload = data
      else:
        # Support frontend modal/need_input payloads which may send { doc_type, format, params }
        fmt = (data.get("type") or data.get("format") or data.get("doc_type") or "pdf").lower()
        # Normalize to 'pdf','docx','xlsx','pptx'
        if fmt in ("doc", "document"):
          fmt = "docx"

        params = data.get("params") or data.get("payload") or {}

        # Build a sensible title
        title = (data.get("title") or
             (params.get("title") if isinstance(params, dict) else None) or
             (data.get("doc_type") and str(data.get("doc_type")).title()) or
             "Generated Document")

        content = []

        # If params is a simple string, treat it as a single paragraph
        if isinstance(params, str) and params.strip():
          content.append({"p": params.strip()})

        # If params is a dict with 'fields' (from need_input form), render each field as heading+paragraph
        elif isinstance(params, dict):
          # If it's already in canonical 'content' form, use it
          if isinstance(params.get("content"), list):
            content = params.get("content")
          # If fields provided, create sections
          elif isinstance(params.get("fields"), dict):
            fields = params.get("fields")
            for k, v in fields.items():
              # use field name as small heading and value as paragraph
              content.append({"h2": str(k)})
              content.append({"p": str(v)})
          else:
            # Fallback: flatten key/value pairs into paragraphs
            for k, v in params.items():
              # Skip empty values
              if v is None or (isinstance(v, str) and v.strip() == ""):
                continue
              content.append({"h2": str(k)})
              content.append({"p": str(v)})

        # Ensure there's at least a placeholder paragraph if nothing provided
        if not content:
          content = [{"p": ""}]

        doc_payload = {"type": fmt, "title": title, "content": content}

      # Call document generation service
      file_path = generate_document(doc_payload)
      filename = os.path.basename(file_path)

      return jsonify({
        "status": "success",
        "file_path": file_path,
        "filename": filename
      }), 200

    except ValueError as exc:
      return jsonify({"status": "error", "message": str(exc)}), 400

    except Exception as exc:
      return jsonify({"status": "error", "message": f"Document generation failed: {str(exc)}"}), 500


@bp.route("/download/<filename>", methods=["GET"])
def download_document(filename: str):
    """
    GET /api/docgen/download/{filename}
    Download a generated document.
    
    Args:
        filename: Name of the file to download (e.g., 'abc123def456.pdf')
    
    Returns:
        File as attachment or 404 if not found.
    """
    try:
        # Security: only allow alphanumeric, dash, underscore, and dot
        if not all(c.isalnum() or c in '.-_' for c in filename):
            return jsonify({
                "status": "error",
                "message": "Invalid filename"
            }), 400
        
        file_path = get_full_document_path(filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                "status": "error",
                "message": f"File not found: {filename}"
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"Download failed: {str(exc)}"
        }), 500


# ============================================================================
# EXAMPLE PAYLOAD for testing
# ============================================================================

"""
Example JSON payload for POST /api/docgen:

{
  "type": "pdf",
  "title": "Sample Legal Report",
  "content": [
    {"h1": "Legal Document Title"},
    {"p": "This is an introductory paragraph explaining the document."},
    {"h2": "Section 1: Background"},
    {"p": "Background information goes here."},
    {"bullet": [
      "Key point number one",
      "Key point number two",
      "Key point number three"
    ]},
    {"h2": "Section 2: Data Summary"},
    {"table": [
      ["Name", "Age", "Status"],
      ["John Doe", "30", "Active"],
      ["Jane Smith", "28", "Pending"],
      ["Bob Johnson", "35", "Inactive"]
    ]},
    {"p": "Conclusion and final remarks."}
  ]
}

Examples for different formats:
- Change "type": "pdf" to "docx", "xlsx", or "pptx"

Testing curl commands:

PDF:
curl -X POST http://localhost:5000/api/docgen \
  -H "Content-Type: application/json" \
  -d '{
    "type": "pdf",
    "title": "Test PDF",
    "content": [
      {"h1": "Hello PDF"},
      {"p": "This is a test PDF document."}
    ]
  }'

DOCX:
curl -X POST http://localhost:5000/api/docgen \
  -H "Content-Type: application/json" \
  -d '{
    "type": "docx",
    "title": "Test DOCX",
    "content": [
      {"h1": "Hello DOCX"},
      {"p": "This is a test Word document."}
    ]
  }'

XLSX:
curl -X POST http://localhost:5000/api/docgen \
  -H "Content-Type: application/json" \
  -d '{
    "type": "xlsx",
    "title": "Test XLSX",
    "content": [
      {"h1": "Data Report"},
      {"table": [
        ["Name", "Value"],
        ["Item1", "100"],
        ["Item2", "200"]
      ]}
    ]
  }'

PPTX:
curl -X POST http://localhost:5000/api/docgen \
  -H "Content-Type: application/json" \
  -d '{
    "type": "pptx",
    "title": "Test Presentation",
    "content": [
      {"h1": "Slide Title"},
      {"p": "Slide content here"}
    ]
  }'

Download example (after generation):
curl -X GET http://localhost:5000/api/docgen/download/abc123def456.pdf \
  --output downloaded.pdf
"""


