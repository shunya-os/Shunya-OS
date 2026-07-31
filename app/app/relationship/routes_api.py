"""FOR-2C Relationship Intelligence Operating System — API Routes."""

from flask import jsonify, request, session
from app import db
from . import relationship_bp
from .models import (
    CanonicalRelationship as Relationship,
    RelationshipCategory, RelationshipField,
    TimelineEntry, RelationshipMemory, RelationshipDocument,
    DuplicateGroup, DuplicateCandidate,
)
from app.relationship.services import (
    create_relationship, update_relationship, archive_relationship,
    search_relationships, get_timeline, _add_timeline_entry,
    find_duplicates, merge_relationships,
    get_or_create_memory, update_ai_memory, compute_health_score,
    seed_default_categories, get_categories,
)
from app.models import KnowledgeDocument


# ── Helpers ──────────────────────────────────────────────────────────────


def _identity():
    return session.get("identity_id") or session.get("user_id") or ""


def _require_identity():
    uid = _identity()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    return None


def _org():
    return session.get("current_org_id")


def _require_org():
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No organization selected"}), 400
    return None


# ── Relationship CRUD ────────────────────────────────────────────────────


@relationship_bp.route("/api/v1/relationships", methods=["POST"])
def api_create_relationship():
    auth = _require_identity()
    if auth: return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No organization selected"}), 400

    data = request.get_json(silent=True) or {}
    rel = create_relationship(org_id, data, created_by=_identity())
    timeline, _ = get_timeline(rel.id, limit=5)
    return jsonify({
        "success": True,
        "relationship": rel.to_dict(),
        "timeline": [e.to_dict() for e in timeline],
    }), 201


@relationship_bp.route("/api/v1/relationships/<int:rel_id>", methods=["GET"])
def api_get_relationship(rel_id):
    auth = _require_identity()
    if auth: return auth
    rel = db.session.get(Relationship, rel_id)
    if not rel or rel.organization_id != _org():
        return jsonify({"error": "Relationship not found"}), 404
    memory = get_or_create_memory(rel.id)
    return jsonify({
        "relationship": rel.to_dict(),
        "ai_memory": memory.to_dict() if memory else None,
    })


@relationship_bp.route("/api/v1/relationships/<int:rel_id>", methods=["PATCH"])
def api_update_relationship(rel_id):
    auth = _require_identity()
    if auth: return auth
    rel = db.session.get(Relationship, rel_id)
    if not rel or rel.organization_id != _org():
        return jsonify({"error": "Relationship not found"}), 404
    data = request.get_json(silent=True) or {}
    rel = update_relationship(rel, data, updated_by=_identity())
    return jsonify({"success": True, "relationship": rel.to_dict()})


@relationship_bp.route("/api/v1/relationships/<int:rel_id>", methods=["DELETE"])
def api_archive_relationship(rel_id):
    auth = _require_identity()
    if auth: return auth
    rel = db.session.get(Relationship, rel_id)
    if not rel or rel.organization_id != _org():
        return jsonify({"error": "Relationship not found"}), 404
    rel = archive_relationship(rel, archived_by=_identity())
    return jsonify({"success": True, "relationship": rel.to_dict()})


@relationship_bp.route("/api/v1/relationships", methods=["GET"])
def api_list_relationships():
    auth = _require_identity()
    if auth: return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No organization selected"}), 400

    query = request.args.get("q", "")
    type_filter = request.args.get("type", "")
    status = request.args.get("status", "active")
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))

    rels, total = search_relationships(org_id, query, type_filter, status, limit, offset)
    return jsonify({
        "relationships": [r.to_dict() for r in rels],
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── Timeline ─────────────────────────────────────────────────────────────


@relationship_bp.route("/api/v1/relationships/<int:rel_id>/timeline", methods=["GET"])
def api_get_timeline(rel_id):
    auth = _require_identity()
    if auth: return auth
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = int(request.args.get("offset", 0))
    entries, total = get_timeline(rel_id, limit, offset)
    return jsonify({
        "timeline": [e.to_dict() for e in entries],
        "total": total,
    })


@relationship_bp.route("/api/v1/relationships/<int:rel_id>/timeline", methods=["POST"])
def api_add_timeline_entry(rel_id):
    auth = _require_identity()
    if auth: return auth
    rel = db.session.get(Relationship, rel_id)
    if not rel or rel.organization_id != _org():
        return jsonify({"error": "Relationship not found"}), 404

    data = request.get_json(silent=True) or {}
    entry = _add_timeline_entry(
        organization_id=rel.organization_id,
        relationship_id=rel_id,
        event_type=data.get("event_type", "note"),
        title=data.get("title", ""),
        description=data.get("description", ""),
        reference_type=data.get("reference_type", ""),
        reference_id=data.get("reference_id"),
        metadata=data.get("metadata"),
        created_by=_identity(),
    )
    db.session.commit()
    return jsonify({"success": True, "entry": entry.to_dict()}), 201


# ── AI Memory ─────────────────────────────────────────────────────────────


@relationship_bp.route("/api/v1/relationships/<int:rel_id>/memory", methods=["GET"])
def api_get_memory(rel_id):
    auth = _require_identity()
    if auth: return auth
    memory = get_or_create_memory(rel_id)
    if not memory:
        return jsonify({"error": "Relationship not found"}), 404
    return jsonify({"ai_memory": memory.to_dict()})


@relationship_bp.route("/api/v1/relationships/<int:rel_id>/memory", methods=["PATCH"])
def api_update_memory(rel_id):
    auth = _require_identity()
    if auth: return auth
    data = request.get_json(silent=True) or {}
    memory = update_ai_memory(
        rel_id,
        memory_data=data.get("memory", {}),
        summary=data.get("summary", ""),
        health_score=data.get("health_score"),
    )
    if not memory:
        return jsonify({"error": "Relationship not found"}), 404
    return jsonify({"success": True, "ai_memory": memory.to_dict()})


# ── Duplicates ──────────────────────────────────────────────────────────


@relationship_bp.route("/api/v1/relationships/<int:rel_id>/duplicates", methods=["GET"])
def api_find_duplicates(rel_id):
    auth = _require_identity()
    if auth: return auth
    rel = db.session.get(Relationship, rel_id)
    if not rel or rel.organization_id != _org():
        return jsonify({"error": "Relationship not found"}), 404
    dupes = find_duplicates(rel.organization_id, rel_id)
    return jsonify({"duplicates": dupes, "count": len(dupes)})


@relationship_bp.route("/api/v1/relationships/merge", methods=["POST"])
def api_merge_relationships():
    auth = _require_identity()
    if auth: return auth
    data = request.get_json(silent=True) or {}
    primary_id = data.get("primary_id")
    secondary_id = data.get("secondary_id")
    if not primary_id or not secondary_id:
        return jsonify({"error": "primary_id and secondary_id required"}), 400
    result = merge_relationships(primary_id, secondary_id, merged_by=_identity())
    if not result:
        return jsonify({"error": "Merge failed — check that both relationships exist in the same organization"}), 400
    return jsonify({"success": True, "relationship": result.to_dict()})


# ── Documents (knowledge link) ────────────────────────────────────────────


@relationship_bp.route("/api/v1/relationships/<int:rel_id>/documents", methods=["GET"])
def api_list_relationship_documents(rel_id):
    auth = _require_identity()
    if auth: return auth
    docs = RelationshipDocument.query.filter_by(relationship_id=rel_id).order_by(
        RelationshipDocument.created_at.desc()
    ).all()
    return jsonify({"documents": [d.to_dict() for d in docs]})


# ── Categories ────────────────────────────────────────────────────────────


@relationship_bp.route("/api/v1/relationships/categories", methods=["GET"])
def api_get_categories():
    auth = _require_identity()
    if auth: return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No organization selected"}), 400
    seed_default_categories(org_id)
    cats = get_categories(org_id)
    return jsonify({"categories": cats})


@relationship_bp.route("/api/v1/relationships/categories", methods=["POST"])
def api_create_category():
    auth = _require_identity()
    if auth: return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No organization selected"}), 400
    data = request.get_json(silent=True) or {}
    cat = RelationshipCategory(
        organization_id=org_id,
        type_key=data.get("type_key", "").strip().lower().replace(" ", "_"),
        display_label=data.get("display_label", "").strip(),
        icon=data.get("icon", "person"),
        color=data.get("color", "#6366f1"),
        is_system=False,
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify({"success": True, "category": cat.to_dict()}), 201


# ── Custom Fields ────────────────────────────────────────────────────────


@relationship_bp.route("/api/v1/relationships/fields", methods=["GET"])
def api_list_custom_fields():
    auth = _require_identity()
    if auth: return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No organization selected"}), 400
    fields = RelationshipField.query.filter_by(organization_id=org_id).order_by(
        RelationshipField.sort_order
    ).all()
    return jsonify({"fields": [f.to_dict() for f in fields]})


@relationship_bp.route("/api/v1/relationships/fields", methods=["POST"])
def api_create_custom_field():
    auth = _require_identity()
    if auth: return auth
    org_id = _org()
    if not org_id:
        return jsonify({"error": "No organization selected"}), 400
    data = request.get_json(silent=True) or {}
    import json
    field = RelationshipField(
        organization_id=org_id,
        field_key=data.get("field_key", "").strip().lower().replace(" ", "_"),
        field_label=data.get("field_label", "").strip(),
        field_type=data.get("field_type", "text"),
        field_options=json.dumps(data.get("field_options", [])),
        is_required=data.get("is_required", False),
    )
    db.session.add(field)
    db.session.commit()
    return jsonify({"success": True, "field": field.to_dict()}), 201


# ── Intelligence ─────────────────────────────────────────────────────────


@relationship_bp.route("/api/v1/relationships/<int:rel_id>/intelligence", methods=["GET"])
def api_get_intelligence(rel_id):
    auth = _require_identity()
    if auth: return auth
    memory = get_or_create_memory(rel_id)
    if not memory:
        return jsonify({"error": "Relationship not found"}), 404

    # Compute health score
    health_score = compute_health_score(rel_id)
    memory.health_score = health_score
    db.session.commit()

    return jsonify({
        "health_score": health_score,
        "engagement_score": memory.engagement_score or 50,
        "lifetime_value": float(memory.lifetime_value or 0),
        "retention_risk": memory.retention_risk or 50,
    })