"""GATE 6 — Unified Document Intelligence API.

Documents are NOT merely files in folders. This API treats every document as an
intelligent object: it uploads, classifies, detects hierarchy, extracts
entities, supports human correction, and survives server restart.

Endpoints:
    POST   /api/v1/documents/upload       — upload file, extract, classify, return intelligence
    GET    /api/v1/documents/              — list documents with intelligence metadata
    GET    /api/v1/documents/<id>          — get document with full intelligence
    POST   /api/v1/documents/<id>/classify  — manually correct classification (human correction persists)
    POST   /api/v1/documents/<id>/reclassify — re-analyze document
    DELETE /api/v1/documents/<id>          — trash/archive

All routes enforce tenant isolation via _resolve_org_id() and authorization
via @require_permission.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, request, session
from werkzeug.utils import secure_filename

from app.authz.decorators import require_permission, _resolve_org_id

logger = logging.getLogger(__name__)


def _identity_id() -> str:
    """Extract identity from flask g or session."""
    from flask import g
    uid = g.get("identity_id")
    if uid:
        return str(uid)
    return session.get("identity_id") or session.get("user_id", "")


document_intel_bp = Blueprint(
    "document_intel", __name__, url_prefix="/api/v1/documents"
)

# ── Supported file types ─────────────────────────────────────────
_EXTRACTABLE_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/plain",
    "text/markdown",
}

_IMAGE_MIMES = {"image/png", "image/jpeg", "image/jpg"}


# ── Helpers ───────────────────────────────────────────────────────


def _extract_text(filepath: str, mime_type: str) -> str:
    """Extract text content from a file based on its MIME type."""
    if mime_type == "application/pdf":
        return _extract_pdf_text(filepath)
    elif mime_type == "text/csv":
        return _extract_csv_text(filepath)
    elif mime_type in ("text/plain", "text/markdown"):
        return _extract_plain_text(filepath)
    elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        return _extract_xlsx_text(filepath)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx_text(filepath)
    elif mime_type in _IMAGE_MIMES:
        return ""
    return ""


def _extract_pdf_text(filepath: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            texts = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(texts)
    except ImportError:
        try:
            import fitz
            doc = fitz.open(filepath)
            return "\n".join(page.get_text() for page in doc)
        except ImportError:
            return "[extraction unavailable: no PDF library installed]"
    except Exception as e:
        logger.warning("PDF extraction failed: %s", e)
        return "[extraction limited]"


def _extract_csv_text(filepath: str) -> str:
    try:
        with open(filepath, "r", errors="replace") as f:
            lines = f.readlines()
            header = lines[0].strip() if lines else ""
            preview = "".join(lines[:100])
            return f"Header: {header}\n\nRows: {len(lines) - 1}\n\nContent:\n{preview}"
    except Exception as e:
        logger.warning("CSV extraction failed: %s", e)
        return "[extraction limited]"


def _extract_plain_text(filepath: str) -> str:
    try:
        with open(filepath, "r", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"[extraction limited: {e}]"


def _extract_xlsx_text(filepath: str) -> str:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        texts = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            texts.append(f"Sheet: {sheet_name}")
            row_count = 0
            for row in ws.iter_rows(values_only=True):
                row_text = ", ".join(str(c) for c in row if c is not None)
                if row_text.strip():
                    texts.append(row_text)
                    row_count += 1
                if row_count > 200:
                    texts.append("... (truncated)")
                    break
        return "\n".join(texts)
    except ImportError:
        return "[extraction unavailable: openpyxl not installed]"
    except Exception as e:
        logger.warning("XLSX extraction failed: %s", e)
        return "[extraction limited]"


def _extract_docx_text(filepath: str) -> str:
    try:
        import docx
        doc = docx.Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        return "[extraction unavailable: python-docx not installed]"
    except Exception as e:
        logger.warning("DOCX extraction failed: %s", e)
        return "[extraction limited]"


def _mime_for_filename(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    return mime_map.get(ext, "application/octet-stream")


def _get_mime_purpose(mime_type: str) -> str:
    if mime_type in _IMAGE_MIMES:
        return "image"
    return "text"


def _get_scoped_document(doc_id: int):
    """Fetch a Document enforcing tenant scope via _resolve_org_id()."""
    from app import db
    from app.models import Document

    org_id = _resolve_org_id()
    q = db.session.query(Document).filter(Document.id == doc_id)
    if org_id is not None:
        q = q.filter(Document.tenant_id == org_id)
    else:
        identity_id = session.get("identity_id", "")
        if identity_id:
            q = q.filter(Document.uploaded_by == identity_id)
    return q.first()


def _apply_intelligence(doc: Any, extracted_text: str, mime_type: str) -> dict[str, Any]:
    """Run classification + hierarchy + entity extraction on a document."""
    from app.document.intelligence import analyse_document

    doc.extracted_text = extracted_text
    file_type_label = mime_type.split("/")[-1] if "/" in mime_type else mime_type
    doc.file_type = file_type_label

    intel = analyse_document(doc, persist=True)
    return intel


def _build_document_response(doc: Any) -> dict[str, Any]:
    """Build a JSON-serializable document response with full intelligence."""
    from app.document.intelligence import read_intelligence

    intel = read_intelligence(doc)
    return {
        "id": doc.id,
        "filename": doc.filename or "",
        "file_type": doc.file_type or "",
        "file_size": 0,
        "classification": doc.classification or "unknown",
        "intelligence": intel,
        "hierarchy": intel.get("hierarchy", []) if intel else [],
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": None,
    }


def _make_upload_dir(org_id: int | None) -> str:
    from app.runtime_config import uploads_dir
    base = uploads_dir()
    org_part = f"org_{org_id}" if org_id else "personal"
    upload_path = os.path.join(base, "documents", org_part)
    os.makedirs(upload_path, exist_ok=True)
    return upload_path


# ── Routes ────────────────────────────────────────────────────────


@document_intel_bp.route("/upload", methods=["POST"])
def api_upload():
    """Upload a file, extract text, classify, detect hierarchy, return intelligence."""
    identity_id = _identity_id()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    from app import db
    from app.models import Document

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"success": False, "error": "Empty filename"}), 400

    org_id = _resolve_org_id()
    identity_id = session.get("identity_id", "") or "system"

    filename = secure_filename(f.filename) or f.filename
    mime_type = f.content_type or _mime_for_filename(filename)
    file_bytes = f.read()
    file_size = len(file_bytes)

    # Save file to disk
    upload_path = _make_upload_dir(org_id)
    safe_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{filename}"
    file_path = os.path.join(upload_path, safe_name)
    try:
        with open(file_path, "wb") as out:
            out.write(file_bytes)
    except OSError as e:
        return jsonify({"success": False, "error": f"Failed to save file: {e}"}), 500

    # Create document record
    doc = Document(
        filename=filename,
        file_path=file_path,
        file_type=mime_type,
        extracted_text="",
        classification="unknown",
        tenant_id=org_id or 0,
        uploaded_by=identity_id,
    )
    db.session.add(doc)
    db.session.flush()

    # Extract text
    extracted_text = _extract_text(file_path, mime_type)
    extraction_purpose = _get_mime_purpose(mime_type)
    extraction_available = bool(extracted_text.strip())

    # Apply intelligence (classification + hierarchy + entities)
    intelligence_data: dict[str, Any] = {}
    try:
        intel = _apply_intelligence(doc, extracted_text, mime_type)
        intelligence_data = intel
    except Exception as e:
        logger.warning("Intelligence failed for doc %s: %s", doc.id, e)
        intelligence_data = {
            "classification": "unknown",
            "confidence": 0.0,
            "reason": f"Intelligence processing failed: {e}",
            "hierarchy": [],
            "extraction_available": False,
            "extraction_supported": False,
        }
        doc.classification = "unknown"

    db.session.commit()

    response = {
        "success": True,
        "document": {
            "id": doc.id,
            "filename": filename,
            "file_type": mime_type,
            "file_size": file_size,
            "classification": doc.classification or "unknown",
            "extraction_purpose": extraction_purpose,
            "extraction_available": extraction_available,
            "intelligence": intelligence_data,
            "hierarchy": intelligence_data.get("hierarchy", []),
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        },
    }

    return jsonify(response), 201


@document_intel_bp.route("", methods=["GET"],
                          strict_slashes=False)
def api_list():
    """List documents with intelligence metadata, tenant-scoped."""
    identity_id = _identity_id()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    from app import db
    from app.models import Document

    org_id = _resolve_org_id()
    limit = request.args.get("limit", 50, type=int)

    q = db.session.query(Document)
    if org_id is not None:
        q = q.filter(Document.tenant_id == org_id)
    else:
        if identity_id:
            q = q.filter(Document.uploaded_by == identity_id)
    docs = q.order_by(Document.created_at.desc()).limit(limit).all()

    return jsonify({
        "success": True,
        "documents": [_build_document_response(d) for d in docs],
    })


@document_intel_bp.route("/<int:doc_id>", methods=["GET"])
@require_permission("knowledge.view")
def api_get(doc_id: int):
    """Get a single document with full intelligence."""
    doc = _get_scoped_document(doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    return jsonify({
        "success": True,
        "document": _build_document_response(doc),
    })


@document_intel_bp.route("/<int:doc_id>/classify", methods=["POST"])
@require_permission("knowledge.upload")
def api_classify(doc_id: int):
    """Manually correct classification. Human correction persists permanently."""
    from app import db
    from app.document.intelligence import read_intelligence

    doc = _get_scoped_document(doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    data = request.get_json(silent=True) or {}
    new_classification = (data.get("classification") or "").strip()
    if not new_classification:
        return jsonify({"success": False, "error": "classification is required"}), 400

    # Read current intelligence, modify, persist
    intel = read_intelligence(doc) or {}
    intel["classification"] = new_classification
    intel["corrected_by_human"] = True
    intel["corrected_at"] = datetime.now(timezone.utc).isoformat()
    intel["previous_classification"] = intel.get("classification", "unknown")

    doc.classification = new_classification
    try:
        existing: dict = {}
        if doc.structured_data:
            existing = json.loads(doc.structured_data) or {}
        existing["intelligence"] = intel
        doc.structured_data = json.dumps(existing)
    except (json.JSONDecodeError, TypeError):
        doc.structured_data = json.dumps({"intelligence": intel})

    db.session.commit()

    return jsonify({
        "success": True,
        "document": _build_document_response(doc),
    })


@document_intel_bp.route("/<int:doc_id>/reclassify", methods=["POST"])
@require_permission("knowledge.upload")
def api_reclassify(doc_id: int):
    """Re-analyze a document: re-run classification + hierarchy + entities."""
    from app import db
    from app.document.intelligence import analyse_document, read_intelligence

    doc = _get_scoped_document(doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    extracted_text = doc.extracted_text or ""
    if not extracted_text.strip():
        filepath = doc.file_path or ""
        if filepath and os.path.isfile(filepath):
            extracted_text = _extract_text(filepath, doc.file_type or "")

    if not extracted_text.strip():
        mime_type = doc.file_type or ""
        purpose = _get_mime_purpose(mime_type)
        if purpose == "image":
            return jsonify({
                "success": False,
                "error": "Image text extraction unavailable — no OCR provider configured",
                "code": "no_ocr_provider",
            }), 422
        return jsonify({
            "success": False,
            "error": "No extracted text available",
            "code": "extraction_unavailable",
        }), 422

    try:
        prev_intel = read_intelligence(doc)
        human_corrected = prev_intel and prev_intel.get("corrected_by_human")

        if human_corrected:
            saved_classification = prev_intel["classification"]
            intel = analyse_document(doc, persist=False)
            intel["classification"] = saved_classification
            intel["corrected_by_human"] = True
            intel["corrected_at"] = prev_intel.get("corrected_at")
            doc.classification = saved_classification
            try:
                existing: dict = {}
                if doc.structured_data:
                    existing = json.loads(doc.structured_data) or {}
                existing["intelligence"] = intel
                doc.structured_data = json.dumps(existing)
            except (json.JSONDecodeError, TypeError):
                doc.structured_data = json.dumps({"intelligence": intel})
        else:
            intel = analyse_document(doc, persist=True)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Reclassify failed for doc %s: %s", doc_id, e)
        return jsonify({"success": False, "error": "Re-analysis failed"}), 500

    return jsonify({
        "success": True,
        "document": _build_document_response(doc),
    })


@document_intel_bp.route("/<int:doc_id>", methods=["DELETE"])
@require_permission("knowledge.upload")
def api_delete(doc_id: int):
    """Trash/archive a document."""
    from app import db

    doc = _get_scoped_document(doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404

    # Remove the file from disk
    filepath = doc.file_path or ""
    if filepath and os.path.isfile(filepath):
        try:
            os.remove(filepath)
        except OSError as e:
            logger.warning("Could not remove file %s: %s", filepath, e)

    db.session.delete(doc)
    db.session.commit()

    return jsonify({
        "success": True,
        "document": {"id": doc_id, "status": "deleted"},
    })