"""
Document API routes for the SPA workspace.
Provides document serving, listing, and ingestion endpoints.
"""
import os
import json
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, send_file, session, g

from app import db
from app.models import Document

documents_bp = Blueprint("documents_api", __name__)

# ── Helpers ──────────────────────────────────────────────────────

def _require_auth():
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    if not user_id or not identity_id:
        return None
    return {"user_id": user_id, "identity_id": identity_id}

def _get_context():
    """Determine active context from session."""
    return {
        "identity_id": session.get("identity_id", ""),
        "current_org_id": session.get("current_org_id"),
        "context_type": "organization" if session.get("current_org_id") else "personal",
    }

# ── List Documents ───────────────────────────────────────────────

@documents_bp.route("/api/v1/documents", methods=["GET"])
def list_documents():
    auth = _require_auth()
    if not auth:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    ctx = _get_context()
    limit = request.args.get("limit", 50, type=int)

    try:
        if ctx["context_type"] == "organization" and ctx["current_org_id"]:
            docs = Document.query.filter_by(tenant_id=ctx["current_org_id"])\
                .order_by(Document.created_at.desc()).limit(limit).all()
        else:
            docs = Document.query.filter_by(uploaded_by=ctx["identity_id"])\
                .order_by(Document.created_at.desc()).limit(limit).all()

        results = []
        for d in docs:
            results.append({
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "classification": d.classification,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "size": os.path.getsize(d.file_path) if d.file_path and os.path.isfile(d.file_path) else 0,
            })

        return jsonify({"success": True, "documents": results, "context": ctx})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Serve Document File ──────────────────────────────────────────

@documents_bp.route("/api/v1/documents/serve/<int:doc_id>", methods=["GET"])
def serve_document(doc_id):
    auth = _require_auth()
    if not auth:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    if not doc.file_path or not os.path.isfile(doc.file_path):
        return jsonify({"success": False, "error": "File not found on disk"}), 404

    # Determine MIME type
    mime_map = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".json": "application/json",
        ".md": "text/markdown",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    ext = os.path.splitext(doc.filename)[1].lower()
    mime = mime_map.get(ext, "application/octet-stream")

    return send_file(doc.file_path, mimetype=mime, as_attachment=False, download_name=doc.filename)


# ── Ingest File ──────────────────────────────────────────────────

@documents_bp.route("/api/v1/founder/ingest", methods=["POST"])
def ingest_file():
    auth = _require_auth()
    if not auth:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"success": False, "error": "Empty file"}), 400

    ctx = _get_context()

    # Save to runtime data
    from app.runtime_config import uploads_dir
    upload_dir = os.path.join(uploads_dir(), "documents")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{f.filename}"
    file_path = os.path.join(upload_dir, safe_name)

    try:
        f.save(file_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save file: {e}"}), 500

    # Extract basic info
    ext = os.path.splitext(f.filename)[1].lower()
    file_type = "pdf" if ext == ".pdf" else ("xlsx" if ext == ".xlsx" else "csv" if ext == ".csv" else "text")

    # Create document record
    doc = Document(
        filename=f.filename,
        file_path=file_path,
        file_type=file_type,
        classification="ingested",
        uploaded_by=ctx["identity_id"],
        tenant_id=ctx["current_org_id"] if ctx["context_type"] == "organization" else None,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(doc)
    db.session.commit()

    # Build summary
    file_size = os.path.getsize(file_path)
    summary = f"File '{f.filename}' ({file_type}, {file_size:,} bytes) saved to your {ctx['context_type']} workspace."

    return jsonify({
        "success": True,
        "document_id": doc.id,
        "filename": f.filename,
        "file_type": file_type,
        "size": file_size,
        "summary": summary,
        "context": ctx,
    })


# ── Document Detail ──────────────────────────────────────────────

@documents_bp.route("/api/v1/documents/<int:doc_id>", methods=["GET"])
def document_detail(doc_id):
    auth = _require_auth()
    if not auth:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    return jsonify({
        "success": True,
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "classification": doc.classification,
            "extracted_text": (doc.extracted_text or "")[:2000] if doc.extracted_text else "",
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "size": os.path.getsize(doc.file_path) if doc.file_path and os.path.isfile(doc.file_path) else 0,
        }
    })