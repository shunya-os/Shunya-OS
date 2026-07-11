"""Shunya AI Settings — configure AI behavior from the frontend."""
from flask import Blueprint, render_template, request, jsonify, g
from app import db
from app.models import Tenant, KnowledgeEntry
from app.routes.auth import login_required

ai_settings_bp = Blueprint("ai_settings", __name__, url_prefix="/ai-settings")


@ai_settings_bp.route("")
@login_required
def ai_settings_page():
    """AI configuration panel."""
    tenant = g.tenant
    config = tenant.ai_config or {}
    
    # Get knowledge stats
    kb_count = KnowledgeEntry.query.filter_by(tenant_id=tenant.id).count()
    
    return render_template("ai_settings.html",
        config=config,
        kb_count=kb_count,
        web_search_enabled=config.get("web_search_enabled", True),
        confidence_threshold=config.get("confidence_threshold", 0.6),
        response_style=config.get("response_style", "balanced"),
        max_sources=config.get("max_sources", 3),
        silence_mentor=config.get("silence_mentor", False),
        auto_learn=config.get("auto_learn", True),
    )


@ai_settings_bp.route("/update", methods=["POST"])
@login_required
def update_ai_settings():
    """Update AI configuration."""
    data = request.get_json(silent=True) or request.form
    tenant = g.tenant
    config = tenant.ai_config or {}
    
    if "web_search_enabled" in data:
        config["web_search_enabled"] = data["web_search_enabled"] in (True, "true", "1")
    if "confidence_threshold" in data:
        config["confidence_threshold"] = float(data["confidence_threshold"])
    if "response_style" in data:
        config["response_style"] = data["response_style"]
    if "max_sources" in data:
        config["max_sources"] = int(data["max_sources"])
    if "silence_mentor" in data:
        config["silence_mentor"] = data["silence_mentor"] in (True, "true", "1")
    if "auto_learn" in data:
        config["auto_learn"] = data["auto_learn"] in (True, "true", "1")
    
    tenant.ai_config = config
    db.session.commit()
    
    return jsonify({"success": True, "config": config})


@ai_settings_bp.route("/knowledge")
@login_required
def knowledge_base():
    """View and manage knowledge base entries."""
    tenant = g.tenant
    entries = KnowledgeEntry.query.filter_by(tenant_id=tenant.id)\
        .order_by(KnowledgeEntry.use_count.desc()).limit(100).all()
    return jsonify({"entries": [{
        "id": e.id,
        "question": e.question,
        "answer": e.answer[:200],
        "source": e.source,
        "confidence": e.confidence,
        "use_count": e.use_count,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    } for e in entries]})


@ai_settings_bp.route("/knowledge/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_knowledge(entry_id):
    """Delete a knowledge base entry."""
    entry = KnowledgeEntry.query.filter_by(id=entry_id, tenant_id=g.tenant.id).first()
    if not entry:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"success": True})