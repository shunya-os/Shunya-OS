"""Shunya OS — Public API."""
from flask import Blueprint, request, jsonify, g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog, KnowledgeEntry, TeamMember
from app.routes.auth import login_required
from datetime import datetime

api_bp = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Entity CRUD API
# ---------------------------------------------------------------------------

@api_bp.route("/entities/<entity_type>", methods=["GET"])
@login_required
def api_list_entities(entity_type):
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type, is_active=True
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    entities = Entity.query.filter_by(
        tenant_id=g.tenant.id, definition_id=definition.id, is_archived=False
    ).order_by(Entity.created_at.desc()).limit(100).all()

    return jsonify({"entities": [e.to_dict() for e in entities]})


@api_bp.route("/entities/<entity_type>", methods=["POST"])
@login_required
def api_create_entity(entity_type):
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type, is_active=True
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    data = request.get_json(silent=True) or {}
    from app.models import next_entity_code
    code = next_entity_code(db.session, g.tenant.id)

    entity_data = {}
    for field in definition.schema:
        fname = field["name"]
        if fname in data:
            entity_data[fname] = data[fname]

    entity = Entity(
        tenant_id=g.tenant.id,
        definition_id=definition.id,
        code=code,
        status=data.get("status", "new"),
        data=entity_data,
        created_by=g.user.id,
    )
    db.session.add(entity)
    db.session.flush()

    activity = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="created",
        detail=f"Created via API",
        governance_level="auto",
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({"success": True, "entity": entity.to_dict()}), 201


@api_bp.route("/entities/<entity_type>/<int:entity_id>", methods=["GET"])
@login_required
def api_get_entity(entity_type, entity_id):
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first()
    if not entity:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"entity": entity.to_dict()})


@api_bp.route("/entities/<entity_type>/<int:entity_id>", methods=["PUT"])
@login_required
def api_update_entity(entity_type, entity_id):
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first()
    if not entity:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}
    if "data" in data and isinstance(data["data"], dict):
        entity.data.update(data["data"])
    if "status" in data:
        entity.status = data["status"]

    activity = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="updated",
        detail="Updated via API",
    )
    db.session.add(activity)
    db.session.commit()
    return jsonify({"success": True, "entity": entity.to_dict()})


@api_bp.route("/entities/<entity_type>/<int:entity_id>", methods=["DELETE"])
@login_required
def api_delete_entity(entity_type, entity_id):
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first()
    if not entity:
        return jsonify({"error": "Not found"}), 404
    entity.is_archived = True

    activity = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="archived",
        detail="Deleted via API",
    )
    db.session.add(activity)
    db.session.commit()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# AI Query API
# ---------------------------------------------------------------------------

@api_bp.route("/ai/query", methods=["POST"])
@login_required
def ai_query():
    """Ask the AI a question — searches internal data first, then web.
    
    Returns structured context with source attribution so the frontend
    can show whether the answer came from company knowledge or the web.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query required"}), 400

    from app.shunya.knowledge import KnowledgePipeline

    # Search internal data AND web, then compare
    context = KnowledgePipeline.get_context_for_ai(query, g.tenant.id)

    # Build a human-readable response with source attribution
    response_parts = []

    if context["internal_sources"]:
        for src in context["internal_sources"]:
            label = src.get("label", "Source")
            content = src.get("content", "")
            confidence = src.get("confidence", 0)
            confidence_label = "High" if confidence >= 0.8 else "Medium" if confidence >= 0.5 else "Low"
            response_parts.append(f"[{label}] (Confidence: {confidence_label})\n{content}")

    if context["web_sources"]:
        for src in context["web_sources"]:
            title = src.get("title", "")
            url = src.get("url", "")
            snippet = src.get("snippet", "")
            response_parts.append(f"[Web Search] {title}\n{snippet}\nSource: {url}")

    if not response_parts:
        response_parts.append("I couldn't find information on this in your company data or the web. "
                              "Would you like to add this information to your knowledge base?")

    # Add verification warning if needed
    needs_verify = context.get("needs_verification", False)
    verify_reason = context.get("verification_reason", "")

    return jsonify({
        "query": query,
        "response": "\n\n".join(response_parts[:3]),
        "context": context,
        "has_internal_data": context["has_internal_data"],
        "has_web_data": context["has_web_data"],
        "needs_verification": needs_verify,
        "verification_reason": verify_reason,
    })


# ---------------------------------------------------------------------------
# Webhook receiver (for integrations)
# ---------------------------------------------------------------------------

@api_bp.route("/webhook/<integration>", methods=["POST"])
def webhook_receiver(integration):
    """Generic webhook receiver for external integrations."""
    payload = request.get_json(silent=True) or {}
    # TODO: Route to integration handler based on `integration` param
    return jsonify({"success": True, "integration": integration})


# ---------------------------------------------------------------------------
# Global Search (Cmd+K)
# ---------------------------------------------------------------------------

@api_bp.route("/search", methods=["GET"])
@login_required
def global_search():
    """Search across all data sources — entities, knowledge, customer memory."""
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify({"results": []})

    from app.shunya.command_palette import CommandPalette
    results = CommandPalette.search(query, g.tenant.id, g.user.id, g.user.role)
    return jsonify({"results": results, "query": query})


# ---------------------------------------------------------------------------
# Data export
# ---------------------------------------------------------------------------

@api_bp.route("/export", methods=["GET"])
@login_required
def export_data():
    import json
    from app.models import Entity, EntityDefinition

    entity_type = request.args.get("type")
    export = {}

    definitions = EntityDefinition.query.filter_by(tenant_id=g.tenant.id).all()
    for d in definitions:
        if entity_type and d.type != entity_type:
            continue
        entities = Entity.query.filter_by(
            tenant_id=g.tenant.id, definition_id=d.id, is_archived=False
        ).all()
        export[d.type] = {
            "definition": d.to_dict(),
            "entities": [e.to_dict() for e in entities],
        }

    return jsonify({"export": export, "exported_at": datetime.utcnow().isoformat()})
