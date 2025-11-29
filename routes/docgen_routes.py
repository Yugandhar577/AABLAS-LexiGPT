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
        
        # Call document generation service
        file_path = generate_document(data)
        filename = os.path.basename(file_path)
        
        return jsonify({
            "status": "success",
            "file_path": file_path,
            "filename": filename
        }), 200
    
    except ValueError as exc:
        return jsonify({
            "status": "error",
            "message": str(exc)
        }), 400
    
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"Document generation failed: {str(exc)}"
        }), 500


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

