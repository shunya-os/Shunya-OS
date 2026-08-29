"""SHUNYA Memory & Knowledge API — surfaces UIR memory and knowledge graph.

Provides endpoints for the frontend to browse SHUNYA's memory and knowledge.
Reads from the canonical Universal Intelligence Runtime.
"""
import logging
from flask import Blueprint, jsonify, request, session, g

logger = logging.getLogger(__name__)

memory_bp = Blueprint("memory_api", __name__, url_prefix="/api/v1/memory")


def _identity_id() -> str:
    return (
        g.get("identity_id")
        or session.get("identity_id")
        or session.get("user_id", "")
    )


def _require_auth() -> bool:
    return bool(_identity_id())


@memory_bp.route("/entries", methods=["GET"])
def list_memory():
    """List memory entries from the canonical MemoryRecord table.

    Falls back to the UIR memory engine when no DB records exist.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        # Primary path: canonical MemoryRecord table (DB-backed, always current)
        from app.memory.models import MemoryRecord
        from app import db
        records = MemoryRecord.query.order_by(
            MemoryRecord.created_at.desc()
        ).limit(50).all()
        results = []
        for r in records:
            results.append({
                "key": r.memory_key or "",
                "content": (r.value or "")[:300],
                "memory_type": r.memory_type or "",
                "source": r.creation_mechanism or "",
                "confidence": 0.9,
                "timestamp": r.created_at.isoformat() if r.created_at else "",
            })
        return jsonify({
            "success": True,
            "data": {"entries": results, "total": len(results)},
        })
    except Exception:
        # Fallback: UIR intelligence runtime
        try:
            from core.intelligence_runtime import get_runtime
            runtime = get_runtime()
            memory_items = runtime.memory.recall_recent(limit=50)
            results = []
            for item in memory_items:
                results.append({
                    "key": getattr(item, "key", ""),
                    "content": (getattr(item, "content", "") or "")[:300],
                    "memory_type": getattr(item, "memory_type", ""),
                    "source": getattr(item, "source", ""),
                    "confidence": getattr(item, "confidence", 0.5),
                    "timestamp": getattr(item, "timestamp", ""),
                })
            return jsonify({
                "success": True,
                "data": {"entries": results, "total": len(results)},
            })
        except Exception:
            return jsonify({
                "success": True,
                "data": {"entries": [], "total": 0},
            })

@memory_bp.route("/knowledge", methods=["GET"])
def list_knowledge():
    """List knowledge graph entries."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from core.intelligence_runtime import get_runtime
        runtime = get_runtime()
        memory_items = runtime.memory.recall_recent(limit=50)
        knowledge_items = []
        for item in memory_items:
            mtype = getattr(item, "memory_type", "")
            confidence = getattr(item, "confidence", 0)
            if mtype and confidence > 0.3:
                knowledge_items.append({
                    "key": getattr(item, "key", ""),
                    "content": (getattr(item, "content", "") or "")[:300],
                    "type": mtype,
                    "confidence": confidence,
                    "source": getattr(item, "source", ""),
                    "timestamp": getattr(item, "timestamp", ""),
                })
        return jsonify({
            "success": True,
            "data": {"entries": knowledge_items, "total": len(knowledge_items)},
        })
    except Exception:
        try:
            from app.memory.models import MemoryRecord
            records = MemoryRecord.query.filter(
                MemoryRecord.memory_type.in_(["fact", "knowledge", "business_context"])
            ).order_by(MemoryRecord.created_at.desc()).limit(50).all()
            items = []
            for r in records:
                items.append({
                    "key": r.id,
                    "content": (r.content or "")[:300],
                    "type": r.memory_type,
                    "confidence": 0.8,
                    "source": "memory_record",
                    "timestamp": r.created_at.isoformat() if r.created_at else None,
                })
            return jsonify({
                "success": True,
                "data": {"entries": items, "total": len(items)},
            })
        except Exception:
            return jsonify({
                "success": True,
                "data": {"entries": [], "total": 0},
            })