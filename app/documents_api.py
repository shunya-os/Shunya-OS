"""
Document API routes for the SPA workspace.
Provides document serving, listing, and ingestion endpoints.
"""
# flake8: noqa: F401 — lazy imports to avoid circular import with app/__init__.py
import os
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, send_file, session

documents_bp = Blueprint("documents_api", __name__)


def _require_auth():
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    if not user_id or not identity_id:
        return None
    return {"user_id": user_id, "identity_id": identity_id}


def _get_context():
    return {
        "identity_id": session.get("identity_id", ""),
        "current_org_id": session.get("current_org_id"),
        "context_type": "organization" if session.get("current_org_id") else "personal",
    }


# ── List Documents ───────────────────────────────────────────────

@documents_bp.route("/api/v1/workspace/documents", methods=["GET"])
def list_documents():
    from app import db
    from app.models import Document

    auth = _require_auth()
    if not auth:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    ctx = _get_context()
    limit = request.args.get("limit", 50, type=int)

    try:
        docs = Document.query\
            .filter_by(uploaded_by=ctx["identity_id"])\
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

@documents_bp.route("/api/v1/workspace/documents/serve/<int:doc_id>", methods=["GET"])
def serve_document(doc_id):
    from app import db
    from app.models import Document

    auth = _require_auth()
    if not auth:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    if not doc.file_path or not os.path.isfile(doc.file_path):
        return jsonify({"success": False, "error": "File not found on disk"}), 404

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
    from app import db
    from app.models import Document

    auth = _require_auth()
    if not auth:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"success": False, "error": "Empty file"}), 400

    ctx = _get_context()

    from app.runtime_config import uploads_dir
    upload_dir = os.path.join(uploads_dir(), "documents")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{f.filename}"
    file_path = os.path.join(upload_dir, safe_name)

    try:
        f.save(file_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save file: {e}"}), 500

    ext = os.path.splitext(f.filename)[1].lower()
    file_type = "pdf" if ext == ".pdf" else ("xlsx" if ext == ".xlsx" else "csv" if ext == ".csv" else "text")

    doc = Document(
        filename=f.filename,
        file_path=file_path,
        file_type=file_type,
        classification="ingested",
        uploaded_by=ctx["identity_id"],
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(doc)
    db.session.flush()

    # Extract content for immediate analysis
    extracted_text = ""
    analysis_summary = ""
    try:
        if file_type == "pdf":
            import subprocess
            pdf_result = subprocess.run(
                ["python3", "-c", f"""
import sys; sys.path.insert(0, '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}')
try:
    import pdfplumber
    with pdfplumber.open('{file_path}') as pdf:
        text = ' '.join(page.extract_text() or '' for page in pdf.pages)
        print(text[:5000] if text else 'No text could be extracted from this PDF.')
except Exception as e:
    print(f'[extraction limited: {{e}}]')
"""],
                capture_output=True, text=True, timeout=15,
            )
            extracted_text = pdf_result.stdout.strip()
            if extracted_text and not extracted_text.startswith("[extraction"):
                analysis_summary = f"PDF extracted: {len(extracted_text)} characters. "
                # Generate a brief summary of key content
                if len(extracted_text) > 100:
                    sentences = extracted_text.replace('\\n', ' ').split('. ')
                    key_points = [s.strip() for s in sentences if len(s.strip()) > 30][:3]
                    if key_points:
                        analysis_summary += "Key content: " + "; ".join(key_points) + "."
        elif file_type == "csv":
            with open(file_path, 'r', errors='replace') as csvf:
                lines = csvf.readlines()
                extracted_text = ''.join(lines[:50])
                header = lines[0].strip() if lines else ""
                row_count = len(lines) - 1
                analysis_summary = f"CSV with {row_count} data rows. Columns: {header}"
        elif file_type == "text":
            with open(file_path, 'r', errors='replace') as txtf:
                extracted_text = txtf.read(5000)
                word_count = len(extracted_text.split())
                analysis_summary = f"Text file: approximately {word_count} words."
    except Exception as ext_err:
        analysis_summary = f"File stored. Content analysis limited: {ext_err}"

    doc.extracted_text = extracted_text
    db.session.commit()

    file_size = os.path.getsize(file_path)
    summary = f"File '{f.filename}' ({file_type}, {file_size:,} bytes) saved to your {ctx['context_type']} workspace."
    if analysis_summary:
        summary += f" {analysis_summary}"

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

@documents_bp.route("/api/v1/workspace/documents/<int:doc_id>", methods=["GET"])
def document_detail(doc_id):
    from app import db
    from app.models import Document

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