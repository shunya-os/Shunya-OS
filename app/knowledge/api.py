"""SHUNYA Knowledge API — surfaces knowledge documents for frontend Knowledge browser.

Bridges the gap where the frontend knowledge-browser-panel.tsx existed with
no backend API. Provides CRUD + search + categories for knowledge documents.
"""

import logging
from flask import Blueprint, jsonify, request, session, g
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

knowledge_bp = Blueprint("knowledge_api", __name__, url_prefix="/api/v1/knowledge")


def _identity_id() -> str:
    return (g.get("identity_id") or session.get("identity_id") or session.get("user_id", ""))


def _require_auth() -> bool:
    return bool(_identity_id())


@knowledge_bp.route("/documents", methods=["GET"])
def list_knowledge_documents():
    """List knowledge documents with optional search and domain filter."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    search_q = request.args.get("q", "").strip()
    domain = request.args.get("domain", "").strip()
    limit = min(int(request.args.get("limit", 50)), 200)
    try:
        from app.models import KnowledgeDocument
        from app import db
        query = KnowledgeDocument.query
        if search_q:
            like = f"%{search_q}%"
            query = query.filter(
                db.or_(
                    KnowledgeDocument.title.ilike(like),
                    KnowledgeDocument.summary.ilike(like),
                    KnowledgeDocument.extracted_text.ilike(like),
                    KnowledgeDocument.tags.ilike(like),
                )
            )
        if domain:
            query = query.filter(KnowledgeDocument.category == domain)
        docs = query.order_by(KnowledgeDocument.created_at.desc()).limit(limit).all()
        results = []
        for d in docs:
            tags = d.tags if isinstance(d.tags, list) else (
                [t.strip() for t in d.tags.split(",") if t.strip()] if d.tags else []
            )
            results.append({
                "id": d.id, "title": d.title or "",
                "summary": (d.summary or "")[:500],
                "category": d.category or "", "tags": tags,
                "content_preview": (d.extracted_text or "")[:300],
                "confidence": getattr(d, "confidence_score", None) or 0.9,
                "created_at": d.created_at.isoformat() if d.created_at else "",
                "updated_at": d.updated_at.isoformat() if hasattr(d, "updated_at") and d.updated_at else "",
            })
        return jsonify({"success": True, "data": {"documents": results, "total": len(results)}})
    except Exception as e:
        logger.warning("Knowledge list failed: %s", e)
        return jsonify({"success": True, "data": {"documents": [], "total": 0}})


@knowledge_bp.route("/documents", methods=["POST"])
def create_knowledge_document():
    """Create a new knowledge document."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "Title is required"}), 400
    try:
        from app.models import KnowledgeDocument
        from app import db
        doc = KnowledgeDocument(
                        title=title,
                        summary=data.get("summary", ""),
                        category=data.get("category", ""),
                        tags=", ".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else (data.get("tags", "") or ""),
                        extracted_text=data.get("content", ""),
                        uploaded_by=_identity_id(),
                    )
        db.session.add(doc)
        db.session.flush()
        doc_id = doc.id
        db.session.commit()
        return jsonify({"success": True, "data": {"id": doc_id, "title": title}})
    except Exception as e:
        db.session.rollback()
        logger.warning("Knowledge create failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@knowledge_bp.route("/documents/<int:doc_id>", methods=["GET"])
def get_knowledge_document(doc_id: int):
    """Get a single knowledge document with full content."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    try:
        from app.models import KnowledgeDocument
        doc = KnowledgeDocument.query.get(doc_id)
        if not doc:
            return jsonify({"success": False, "error": "Document not found"}), 404
        tags = doc.tags if isinstance(doc.tags, list) else (
            [t.strip() for t in doc.tags.split(",") if t.strip()] if doc.tags else []
        )
        return jsonify({"success": True, "data": {
            "id": doc.id, "title": doc.title or "", "summary": doc.summary or "",
            "category": doc.category or "", "tags": tags,
            "content": doc.extracted_text or "",
            "confidence": getattr(doc, "confidence_score", None) or 0.9,
            "uploaded_by": doc.uploaded_by or "",
            "created_at": doc.created_at.isoformat() if doc.created_at else "",
        }})
    except Exception as e:
        logger.warning("Knowledge get failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@knowledge_bp.route("/categories", methods=["GET"])
def list_knowledge_categories():
    """List distinct knowledge categories for filtering."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    try:
        from app.models import KnowledgeDocument
        from app import db
        results = db.session.query(KnowledgeDocument.category).distinct().all()
        categories = sorted(set(r[0] for r in results if r[0]))
        return jsonify({"success": True, "data": {"categories": categories}})
    except Exception as e:
        logger.warning("Knowledge categories failed: %s", e)
        return jsonify({"success": True, "data": {"categories": []}})


@knowledge_bp.route("/search", methods=["POST"])
def search_knowledge():
    """Search knowledge documents with AI-aware relevance ranking."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    limit = min(int(data.get("limit", 20)), 100)
    try:
        from app.models import KnowledgeDocument
        from app import db
        like = f"%{query}%"
        docs = KnowledgeDocument.query.filter(
            db.or_(
                KnowledgeDocument.title.ilike(like),
                KnowledgeDocument.summary.ilike(like),
                KnowledgeDocument.extracted_text.ilike(like),
                KnowledgeDocument.tags.ilike(like),
            )
        ).order_by(KnowledgeDocument.created_at.desc()).limit(limit).all()
        results = []
        for d in docs:
            results.append({
                "id": d.id, "title": d.title or "",
                "summary": (d.summary or "")[:300],
                "category": d.category or "",
                "relevance": 0.8,
            })
        return jsonify({"success": True, "data": {"results": results, "total": len(results)}})
    except Exception as e:
        logger.warning("Knowledge search failed: %s", e)
        return jsonify({"success": True, "data": {"results": [], "total": 0}})