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


def _tenant_id() -> int | None:
    """Resolve the current tenant/org ID from session or request context."""
    return (
        session.get("current_org_id")
        or session.get("tenant_id")
        or g.get("tenant_id")
    )


def _require_auth() -> bool:
    return bool(_identity_id())


# ── Helpers ──


def _memory_record_to_dict(r, include_id=False):
    """Convert a MemoryRecord to the standard dict shape."""
    d = {
        "key": r.memory_key or "",
        "content": (r.value or "")[:300],
        "memory_type": r.memory_type or "",
        "source": r.creation_mechanism or "",
        "confidence": getattr(r, "confidence", 0.9) or 0.9,
        "timestamp": r.created_at.isoformat() if r.created_at else "",
        "status": r.status or "active",
    }
    if include_id:
        d["id"] = r.id
    return d


def _apply_tenant_filter(query):
    """Apply tenant isolation to a query, if a tenant_id is available."""
    tenant_id = _tenant_id()
    if tenant_id is not None:
        from app.memory.models import MemoryRecord
        return query.filter(MemoryRecord.tenant_id == tenant_id)
    return query


def _get_runtime_memory():
    """Try to get a memory item from the UIR runtime (fallback path)."""
    try:
        from core.intelligence_runtime import get_runtime
        return get_runtime().memory
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Existing endpoints (enhanced with tenant isolation)
# ═══════════════════════════════════════════════════════════════════════════════


@memory_bp.route("/entries", methods=["GET"])
def list_memory():
    """List memory entries from the canonical MemoryRecord table.

    Falls back to the UIR memory engine when no DB records exist.
    Filtered by tenant_id for isolation when available.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        # Primary path: canonical MemoryRecord table (DB-backed, always current)
        from app.memory.models import MemoryRecord
        from app import db
        query = MemoryRecord.query.filter(
            MemoryRecord.status.in_(["active", "confirmed", "candidate"])
        )
        query = _apply_tenant_filter(query)
        records = query.order_by(
            MemoryRecord.created_at.desc()
        ).limit(50).all()
        results = [_memory_record_to_dict(r) for r in records]
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
                    "status": getattr(item, "status", "active"),
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
    """List knowledge graph entries, filtered by tenant when available."""
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
            query = MemoryRecord.query.filter(
                MemoryRecord.memory_type.in_(["fact", "knowledge", "business_context"]),
                MemoryRecord.status.in_(["active", "confirmed"]),
            )
            query = _apply_tenant_filter(query)
            records = query.order_by(MemoryRecord.created_at.desc()).limit(50).all()
            items = []
            for r in records:
                items.append({
                    "key": r.id,
                    "content": (r.value or "")[:300],
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


# ═══════════════════════════════════════════════════════════════════════════════
# New endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@memory_bp.route("/entries/<int:entry_id>", methods=["GET"])
def get_memory_entry(entry_id: int):
    """Get a single memory entry with full detail and provenance.

    Returns the memory record plus any associated provenance chain.
    Access is scoped to the current tenant.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.memory.models import MemoryRecord, MemoryProvenance

        record = MemoryRecord.query.get(entry_id)
        if not record:
            return jsonify({"success": False, "error": "Memory entry not found"}), 404

        # Tenant isolation
        tenant_id = _tenant_id()
        if tenant_id is not None and record.tenant_id is not None and record.tenant_id != tenant_id:
            return jsonify({"success": False, "error": "Memory entry not found"}), 404

        # Base entry data
        entry = _memory_record_to_dict(record, include_id=True)
        entry["value"] = record.value
        entry["value_type"] = record.value_type
        entry["summary"] = getattr(record, "summary", "")
        entry["scope_type"] = record.scope_type
        entry["scope_object_type"] = getattr(record, "scope_object_type", "")
        entry["scope_object_id"] = getattr(record, "scope_object_id", None)
        entry["truth_classification"] = record.truth_classification
        entry["status"] = record.status
        entry["supersedes_id"] = record.supersedes_id
        entry["superseded_by_id"] = record.superseded_by_id
        entry["tenant_id"] = record.tenant_id

        # Load provenance chain
        provenance_records = MemoryProvenance.query.filter_by(
            memory_id=entry_id
        ).order_by(MemoryProvenance.created_at.desc()).all()

        entry["provenance"] = [
            {
                "id": p.id,
                "source_object_type": p.source_object_type,
                "source_object_id": p.source_object_id,
                "provenance_source": p.provenance_source,
                "provenance_source_id": p.provenance_source_id,
                "provenance_role": p.provenance_role,
                "creation_mechanism": p.creation_mechanism,
                "observed_at": p.observed_at.isoformat() if p.observed_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in provenance_records
        ]

        return jsonify({
            "success": True,
            "data": entry,
        })

    except Exception:
        logger.exception("Error fetching memory entry %s", entry_id)
        return jsonify({"success": False, "error": "Internal error"}), 500


@memory_bp.route("/entries/search", methods=["GET"])
def search_memory():
    """Search memory entries by content, key, or memory type.

    Query parameters:
      - q (required): search term to match against content/key
      - memory_type (optional): filter by memory type
      - limit (optional): max results (default 50, max 200)
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"success": False, "error": "Search query 'q' is required"}), 400

    try:
        limit = min(int(request.args.get("limit", 50)), 200)
    except (ValueError, TypeError):
        limit = 50

    memory_type_filter = request.args.get("memory_type", "").strip()

    try:
        from app.memory.models import MemoryRecord
        from app import db

        # Build query — search across content, key, summary, and memory_type
        like_pattern = f"%{q}%"
        query = MemoryRecord.query.filter(
            MemoryRecord.status.in_(["active", "confirmed", "candidate"])
        ).filter(
            db.or_(
                MemoryRecord.value.ilike(like_pattern),
                MemoryRecord.memory_key.ilike(like_pattern),
                MemoryRecord.summary.ilike(like_pattern),
            )
        )

        # Apply tenant isolation
        query = _apply_tenant_filter(query)

        # Optional memory type filter
        if memory_type_filter:
            query = query.filter(MemoryRecord.memory_type == memory_type_filter)

        records = query.order_by(
            MemoryRecord.created_at.desc()
        ).limit(limit).all()

        results = [_memory_record_to_dict(r, include_id=True) for r in records]

        return jsonify({
            "success": True,
            "data": {"entries": results, "total": len(results)},
        })

    except Exception:
        logger.exception("Error searching memory")
        return jsonify({"success": False, "error": "Internal error"}), 500


@memory_bp.route("/entries/<int:entry_id>", methods=["DELETE"])
def delete_memory_entry(entry_id: int):
    """Soft-delete a memory entry by marking it as archived.

    Only the owning tenant may archive an entry.
    Returns the updated record.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.memory.models import MemoryRecord
        from app import db

        record = MemoryRecord.query.get(entry_id)
        if not record:
            return jsonify({"success": False, "error": "Memory entry not found"}), 404

        # Tenant isolation
        tenant_id = _tenant_id()
        if tenant_id is not None and record.tenant_id is not None and record.tenant_id != tenant_id:
            return jsonify({"success": False, "error": "Memory entry not found"}), 404

        # Soft-delete: set status to archived
        record.status = "archived"
        db.session.commit()

        return jsonify({
            "success": True,
            "data": _memory_record_to_dict(record, include_id=True),
        })

    except Exception:
        logger.exception("Error deleting memory entry %s", entry_id)
        return jsonify({"success": False, "error": "Internal error"}), 500


@memory_bp.route("/provenance/<int:memory_id>", methods=["GET"])
def get_provenance(memory_id: int):
    """Get the full provenance chain for a memory entry.

    Returns all provenance records linked to this memory entry,
    ordered from most recent to oldest.
    Access is scoped to the current tenant.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.memory.models import MemoryRecord, MemoryProvenance

        # Verify the memory entry exists and is tenant-scoped
        record = MemoryRecord.query.get(memory_id)
        if not record:
            return jsonify({"success": False, "error": "Memory entry not found"}), 404

        # Tenant isolation
        tenant_id = _tenant_id()
        if tenant_id is not None and record.tenant_id is not None and record.tenant_id != tenant_id:
            return jsonify({"success": False, "error": "Memory entry not found"}), 404

        provenance_records = MemoryProvenance.query.filter_by(
            memory_id=memory_id
        ).order_by(MemoryProvenance.created_at.desc()).all()

        results = [
            {
                "id": p.id,
                "memory_id": p.memory_id,
                "source_object_type": p.source_object_type,
                "source_object_id": p.source_object_id,
                "provenance_source": p.provenance_source,
                "provenance_source_id": p.provenance_source_id,
                "provenance_role": p.provenance_role,
                "creation_mechanism": p.creation_mechanism,
                "observed_at": p.observed_at.isoformat() if p.observed_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in provenance_records
        ]

        return jsonify({
            "success": True,
            "data": {
                "memory_id": memory_id,
                "memory_key": record.memory_key,
                "provenance": results,
                "total": len(results),
            },
        })

    except Exception:
        logger.exception("Error fetching provenance for memory %s", memory_id)
        return jsonify({"success": False, "error": "Internal error"}), 500