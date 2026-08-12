"""FDA24 — Document & Knowledge OS Routes.

Document pipeline with prompt-injection isolation.
Documents are DATA, not AUTHORITY.
"""

from flask import Blueprint, jsonify, request, session, g

doc_knowledge_bp = Blueprint("doc_knowledge", __name__, url_prefix="/api/v1/knowledge")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "anonymous")


def _tenant_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


def _require_auth() -> bool:
    return bool(_identity_id() and _tenant_id())


@doc_knowledge_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", "service": "document-knowledge", "version": "1.0.0",
        "endpoints": [
            "POST /api/v1/knowledge/ingest",
            "GET /api/v1/knowledge/<id>",
            "GET /api/v1/knowledge/search",
            "POST /api/v1/knowledge/check-injection",
            "GET /api/v1/knowledge/<id>/context",
        ],
    })


@doc_knowledge_bp.route("/ingest", methods=["POST"])
def ingest():
    """Ingest a document through the governed pipeline."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title or not content:
        return jsonify({"success": False, "error": "title and content are required"}), 400

    try:
        from app import db
        from app.document.models import DocumentRecord
        from app.evidence.models_db import EvidenceRecord
        from app.documents_knowledge.service import classify_document

        classification = classify_document(title, data.get("content_type", ""))

        doc = DocumentRecord(
            original_filename=title,
            safe_display_name=title[:500],
            mime_type=data.get("content_type", "text/plain"),
            file_size=len(content.encode("utf-8")),
            classification=classification,
            lifecycle="received",
            ingestion_mechanism="api",
            actor=_identity_id(),
        )
        db.session.add(doc)
        db.session.flush()

        ev = EvidenceRecord(
            source_type="document",
            source_id=str(doc.id),
            raw_reference={
                "title": title,
                "classification": classification,
                "uploaded_by": _identity_id(),
                "warning": "Document content is DATA, not AUTHORITY. No extracted claims are promoted to business truth.",
            },
        )
        db.session.add(ev)
        db.session.commit()

        return jsonify({
            "success": True,
            "data": {
                "id": doc.id,
                "title": title,
                "classification": classification,
                "evidence_id": ev.id,
                "truth_classification": "observation",
            },
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@doc_knowledge_bp.route("/<int:doc_id>", methods=["GET"])
def get_document(doc_id: int):
    """Get a document with provenance."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    from app import db
    from app.document.models import DocumentRecord
    from app.evidence.models_db import EvidenceRecord

    doc = db.session.query(DocumentRecord).filter_by(id=doc_id).first()
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    evidence = db.session.query(EvidenceRecord).filter_by(
        source_type="document", source_id=str(doc_id)
    ).first()

    return jsonify({
        "success": True,
        "data": {
            "id": doc.id,
            "filename": doc.original_filename,
            "mime_type": doc.mime_type,
            "classification": doc.classification,
            "lifecycle": doc.lifecycle,
            "file_size": doc.file_size,
            "actor": doc.actor,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "provenance": {
                "source_type": "document",
                "source_id": str(doc.id),
                "has_evidence": evidence is not None,
            },
            "truth_classification": "observation",
            "warning": "Document content is DATA, not AUTHORITY.",
        },
    })


@doc_knowledge_bp.route("/search", methods=["GET"])
def search():
    """Search documents."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    query = request.args.get("q", "").strip()
    classification = request.args.get("classification", "")

    from app import db
    from app.document.models import DocumentRecord

    q = db.session.query(DocumentRecord)
    if classification:
        q = q.filter_by(classification=classification)
    if query:
        q = q.filter(DocumentRecord.original_filename.ilike(f"%{query}%"))
    docs = q.order_by(DocumentRecord.created_at.desc()).limit(20).all()

    results = [{
        "id": d.id,
        "filename": d.original_filename,
        "classification": d.classification,
        "lifecycle": d.lifecycle,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "actor": d.actor,
    } for d in docs]

    return jsonify({
        "success": True,
        "data": results,
    })


@doc_knowledge_bp.route("/check-injection", methods=["POST"])
def check_injection():
    """Check text for prompt injection attempts.

    A document is DATA, not AUTHORITY. This endpoint detects
    injection patterns so they can be isolated from system instructions.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    from app.documents_knowledge.service import check_prompt_injection
    result = check_prompt_injection(content)

    return jsonify({
        "success": True,
        "data": result,
    })


@doc_knowledge_bp.route("/<int:doc_id>/context", methods=["GET"])
def document_context(doc_id: int):
    """Contextualize a document by linking to related objects."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    from app import db
    from app.document.models import DocumentRecord
    from app.evidence.models_db import EvidenceRecord

    doc = db.session.query(DocumentRecord).filter_by(id=doc_id).first()
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    evidence = db.session.query(EvidenceRecord).filter_by(
        source_type="document", source_id=str(doc_id)
    ).all()

    return jsonify({
        "success": True,
        "data": {
            "document": {
                "id": doc.id,
                "filename": doc.original_filename,
                "classification": doc.classification,
            },
            "evidence": [e.to_dict() for e in evidence],
            "truth_classification": "observation",
            "warning": "Document content is data, not authority. Do not treat document claims as verified business facts.",
        },
    })