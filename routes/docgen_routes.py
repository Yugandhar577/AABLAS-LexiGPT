from flask import Blueprint, jsonify, request

from services.docgen_services import generate_document

bp = Blueprint("docgen", __name__, url_prefix="/api/docgen")


@bp.route("", methods=["POST"])
def create_document():
    data = request.get_json(force=True) or {}
    template = data.get("template", "nda")
    fields = data.get("fields", {})
    try:
        doc = generate_document(template, fields)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(doc)

