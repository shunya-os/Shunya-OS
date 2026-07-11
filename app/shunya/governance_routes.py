"""Shunya OS — Governance UI routes.

Admins view and configure governance tiers per action type,
and manage the approval queue for govern-level actions.
"""
from flask import Blueprint, render_template, request, jsonify, g
from app import db
from app.routes.auth import login_required, admin_required
from app.shunya.governance import GovernanceEngine, ActionType, GOVERNANCE_RULES
from app.models import GovernanceLevel  # DB enum

governance_bp = Blueprint("governance", __name__, url_prefix="/governance")


ACTION_DISPLAY = {
    ActionType.CREATE_ENTITY: {"label": "Create Record", "icon": "➕", "desc": "AI creating new leads, patients, orders"},
    ActionType.UPDATE_ENTITY: {"label": "Update Record", "icon": "✏️", "desc": "Modifying existing record fields"},
    ActionType.DELETE_ENTITY: {"label": "Archive Record", "icon": "🗂️", "desc": "Soft-deleting / archiving records"},
    ActionType.CHANGE_STATUS: {"label": "Change Status", "icon": "🔄", "desc": "Moving records through pipeline stages"},
    ActionType.SEND_MESSAGE: {"label": "Send Message", "icon": "💬", "desc": "AI sending messages to clients/team"},
    ActionType.GENERATE_INVOICE: {"label": "Generate Invoice", "icon": "💰", "desc": "Creating invoices and payment links"},
    ActionType.CREATE_MODULE: {"label": "Create Module", "icon": "🧩", "desc": "Building new entity types via Module Builder"},
    ActionType.MODIFY_RULES: {"label": "Modify Rules", "icon": "⚙️", "desc": "Changing business rules or governance config"},
    ActionType.DELETE_PERMANENT: {"label": "Delete Permanently", "icon": "⚠️", "desc": "Irreversible data deletion"},
}


@governance_bp.route("")
@login_required
def governance_page():
    """Main governance settings page."""
    # Get tenant-specific overrides from ai_config
    config = g.tenant.ai_config or {}
    overrides = config.get("governance_overrides", {})

    actions = []
    for action_type in ActionType:
        default_level = GOVERNANCE_RULES.get(action_type, GovernanceLevel.GOVERN)
        effective = overrides.get(action_type.value, default_level.value)
        info = ACTION_DISPLAY.get(action_type, {"label": action_type.value, "icon": "❓", "desc": ""})
        actions.append({
            "key": action_type.value,
            "label": info["label"],
            "icon": info["icon"],
            "description": info["desc"],
            "default_level": default_level.value,
            "effective_level": effective,
        })

    # Get pending approvals
    from app.models import ActivityLog
    pending = ActivityLog.query.filter_by(
        tenant_id=g.tenant.id,
        governance_level="govern",
    ).order_by(ActivityLog.created_at.desc()).limit(20).all()

    return render_template("governance.html", actions=actions, pending=pending)


@governance_bp.route("/rules", methods=["GET"])
@login_required
def get_rules():
    """Get governance rules as JSON (including tenant overrides)."""
    config = g.tenant.ai_config or {}
    overrides = config.get("governance_overrides", {})

    rules = {}
    for action_type in ActionType:
        default = GOVERNANCE_RULES.get(action_type, GovernanceLevel.GOVERN).value
        effective = overrides.get(action_type.value, default)
        rules[action_type.value] = {
            "default": default,
            "effective": effective,
            "label": ACTION_DISPLAY.get(action_type, {}).get("label", action_type.value),
        }
    return jsonify({"rules": rules, "role": g.user.role})


@governance_bp.route("/rules", methods=["POST"])
@login_required
@admin_required
def update_rules():
    """Update governance rules for this tenant."""
    data = request.get_json(silent=True) or {}
    overrides = data.get("overrides", {})

    # Validate
    valid_actions = {a.value for a in ActionType}
    valid_levels = {l.value for l in GovernanceLevel}
    clean = {}
    for key, val in overrides.items():
        if key in valid_actions and val in valid_levels:
            clean[key] = val

    config = dict(g.tenant.ai_config or {})
    config["governance_overrides"] = clean
    g.tenant.ai_config = config
    db.session.commit()

    return jsonify({"success": True, "overrides": clean})


@governance_bp.route("/approvals/<int:log_id>/resolve", methods=["POST"])
@login_required
@admin_required
def resolve_approval(log_id):
    """Approve or reject a pending govern-level action."""
    data = request.get_json(silent=True) or request.form
    decision = data.get("decision", "approved")  # approved or rejected

    from app.models import ActivityLog
    log = db.session.get(ActivityLog, log_id)
    if not log or log.tenant_id != g.tenant.id:
        return jsonify({"error": "Not found"}), 404

    log.detail = f"[{decision.upper()}] {log.detail}"
    log.governance_level = f"govern_{decision}"
    db.session.commit()

    return jsonify({"success": True, "decision": decision})


@governance_bp.route("/approvals", methods=["GET"])
@login_required
def list_approvals():
    """List pending approvals for the current tenant."""
    from app.models import ActivityLog
    pending = ActivityLog.query.filter_by(
        tenant_id=g.tenant.id,
        governance_level="govern",
    ).order_by(ActivityLog.created_at.desc()).limit(50).all()

    items = []
    for a in pending:
        items.append({
            "id": a.id,
            "action": a.action,
            "detail": a.detail,
            "user_id": a.user_id,
            "entity_id": a.entity_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return jsonify({"approvals": items, "count": len(items)})