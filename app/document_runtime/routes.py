"""EP-05 — Universal Document Runtime API."""

from flask import Blueprint, jsonify, request, g

from .runtime import get_document_runtime, DOCUMENT_TYPES

doc_bp = Blueprint("documents", __name__, url_prefix="/api/v1/documents")


def _require_identity():
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    return request.headers.get("X-Identity-Id")


@doc_bp.route("", methods=["POST"])
def create_document():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400
    rt = get_document_runtime()
    doc = rt.create_document(title=title, content=data.get("content", ""),
                             format=data.get("format", "markdown"))
    return jsonify({"success": True, "data": doc.to_dict()}), 201


@doc_bp.route("", methods=["GET"])
def list_documents():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_document_runtime()
    docs = [d.to_dict() for d in rt.list_documents()]
    return jsonify({"success": True, "data": docs})


@doc_bp.route("/<doc_id>", methods=["GET"])
def get_document(doc_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_document_runtime()
    doc = rt.get_document(doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404
    return jsonify({"success": True, "data": doc.to_dict()})


@doc_bp.route("/<doc_id>/content", methods=["PUT"])
def update_document(doc_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    content = data.get("content", "")
    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400
    rt = get_document_runtime()
    doc = rt.update_content(doc_id, content, author=identity_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404
    return jsonify({"success": True, "data": doc.to_dict()})


@doc_bp.route("/<doc_id>/convert", methods=["POST"])
def convert_document(doc_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    target = data.get("format", "pdf")
    rt = get_document_runtime()
    result = rt.convert_format(doc_id, target)
    if result is None:
        return jsonify({"success": False, "error": "Conversion failed"}), 500
    return jsonify({"success": True, "data": {"content": result, "format": target}})


@doc_bp.route("/search", methods=["GET"])
def search_documents():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "error": "q parameter required"}), 400
    rt = get_document_runtime()
    results = rt.search(query)
    return jsonify({"success": True, "data": results})


@doc_bp.route("/<doc_id>/summary", methods=["GET"])
def document_summary(doc_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_document_runtime()
    summary = rt.generate_summary(doc_id)
    return jsonify({"success": True, "data": {"summary": summary}})


@doc_bp.route("/<doc_id>/ocr", methods=["POST"])
def document_ocr(doc_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_document_runtime()
    ocr_text = rt.extract_ocr(doc_id)
    return jsonify({"success": True, "data": {"ocr_text": ocr_text}})


@doc_bp.route("/types", methods=["GET"])
def list_document_types():
    """GET /api/v1/documents/types — list supported document types and their lifecycles."""
    return jsonify({"success": True, "data": {
        doc_type: {"lifecycle": config["lifecycle"], "default_purpose": config["default_purpose"]}
        for doc_type, config in DOCUMENT_TYPES.items()
    }})


@doc_bp.route("/<doc_id>/transition", methods=["POST"])
def transition_document(doc_id: str):
    """POST /api/v1/documents/<id>/transition — advance lifecycle stage."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    target = data.get("stage", "").strip()
    if not target:
        return jsonify({"success": False, "error": "stage is required"}), 400
    rt = get_document_runtime()
    doc = rt.transition_document(doc_id, target, actor=identity_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found or invalid transition"}), 404
    return jsonify({"success": True, "data": doc.to_dict()})


@doc_bp.route("/<doc_id>/evidence", methods=["POST"])
def add_evidence(doc_id: str):
    """POST /api/v1/documents/<id>/evidence — add evidence to document."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    event_type = data.get("event_type", "").strip()
    description = data.get("description", "").strip()
    if not event_type or not description:
        return jsonify({"success": False, "error": "event_type and description required"}), 400
    rt = get_document_runtime()
    doc = rt.add_evidence(doc_id, event_type, description)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404
    return jsonify({"success": True, "data": doc.to_dict()})


@doc_bp.route("/<doc_id>/risk", methods=["GET"])
def document_risk(doc_id: str):
    """GET /api/v1/documents/<id>/risk — AI risk analysis."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_document_runtime()
    risk = rt.analyze_risk(doc_id)
    return jsonify({"success": True, "data": {"risk": risk}})


@doc_bp.route("/<doc_id>/recommend", methods=["GET"])
def document_recommendation(doc_id: str):
    """GET /api/v1/documents/<id>/recommend — AI next-action recommendation."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_document_runtime()
    rec = rt.recommend_action(doc_id)
    return jsonify({"success": True, "data": {"recommendation": rec}})


@doc_bp.route("/<doc_id>/relationships", methods=["POST"])
def add_relationship(doc_id: str):
    """POST /api/v1/documents/<id>/relationships — link document to an object."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    object_name = data.get("object_name", "").strip()
    if not object_name:
        return jsonify({"success": False, "error": "object_name required"}), 400
    rt = get_document_runtime()
    doc = rt.add_relationship(doc_id, object_name, data.get("relationship", "references"))
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404
    return jsonify({"success": True, "data": doc.to_dict()})