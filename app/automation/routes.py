"""SHUNYA M7 — Automation Routes.

Rule CRUD, execution logs, workflow templates, and trigger API.
"""
import json
from flask import Blueprint, jsonify, request, session

automation_bp = Blueprint("automation", __name__, url_prefix="/api/v1/automation")


def _funded_required() -> bool:
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    return bool(user_id and identity_id)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@automation_bp.route("/rules", methods=["GET"])
def api_list_rules():
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    from app.automation.service import get_rules
    return jsonify({"success": True, "data": get_rules(
        identity_id=identity_id, include_inactive=include_inactive
    )})


@automation_bp.route("/rules", methods=["POST"])
def api_create_rule():
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    identity_id = session.get("identity_id")

    name = data.get("name", "").strip()
    trigger_type = data.get("trigger_type", "").strip()
    action_type = data.get("action_type", "").strip()
    if not name or not trigger_type or not action_type:
        return jsonify({"success": False, "error": "name, trigger_type, and action_type are required"}), 400

    from app.automation.service import create_rule
    result = create_rule(
        identity_id=identity_id,
        name=name,
        description=data.get("description", ""),
        space_id=data.get("space_id"),
        trigger_type=trigger_type,
        trigger_config=data.get("trigger_config", {}),
        action_type=action_type,
        action_config=data.get("action_config", {}),
    )
    return jsonify({"success": True, "data": result}), 201


@automation_bp.route("/rules/<int:rule_id>", methods=["GET"])
def api_get_rule(rule_id: int):
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.automation.service import get_rule
    result = get_rule(rule_id)
    if not result:
        return jsonify({"success": False, "error": "Rule not found"}), 404
    return jsonify({"success": True, "data": result})


@automation_bp.route("/rules/<int:rule_id>", methods=["PUT"])
def api_update_rule(rule_id: int):
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    from app.automation.service import update_rule
    result = update_rule(rule_id=rule_id, **data)
    if not result:
        return jsonify({"success": False, "error": "Rule not found"}), 404
    return jsonify({"success": True, "data": result})


@automation_bp.route("/rules/<int:rule_id>/toggle", methods=["POST"])
def api_toggle_rule(rule_id: int):
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    is_active = data.get("is_active", True)
    from app.automation.service import toggle_rule
    result = toggle_rule(rule_id=rule_id, is_active=is_active)
    if not result:
        return jsonify({"success": False, "error": "Rule not found"}), 404
    return jsonify({"success": True, "data": result})


@automation_bp.route("/rules/<int:rule_id>", methods=["DELETE"])
def api_delete_rule(rule_id: int):
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.automation.service import delete_rule
    success = delete_rule(rule_id)
    return jsonify({"success": success})


# ---------------------------------------------------------------------------
# Execution Logs
# ---------------------------------------------------------------------------

@automation_bp.route("/logs", methods=["GET"])
def api_list_logs():
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    rule_id = request.args.get("rule_id", type=int)
    from app.automation.service import get_execution_logs
    logs = get_execution_logs(rule_id=rule_id, identity_id=identity_id)
    return jsonify({"success": True, "data": logs})


# ---------------------------------------------------------------------------
# Trigger (for programmatic event firing)
# ---------------------------------------------------------------------------

@automation_bp.route("/trigger", methods=["POST"])
def api_trigger():
    """Manually trigger automation rule evaluation for an event."""
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    trigger_type = data.get("trigger_type", "").strip()
    trigger_object_id = data.get("trigger_object_id", "").strip()
    trigger_summary = data.get("trigger_summary", "").strip()
    context = data.get("context", {})

    if not trigger_type or not trigger_object_id:
        return jsonify({"success": False, "error": "trigger_type and trigger_object_id required"}), 400

    from app.automation.service import evaluate_triggers
    results = evaluate_triggers(
        trigger_type=trigger_type,
        trigger_object_id=trigger_object_id,
        trigger_summary=trigger_summary or f"Triggered by {trigger_object_id}",
        context=context,
    )
    return jsonify({"success": True, "data": {"matched": len(results), "results": results}})


# ---------------------------------------------------------------------------
# Workflow Templates
# ---------------------------------------------------------------------------

@automation_bp.route("/templates", methods=["GET"])
def api_list_templates():
    from app.automation.service import get_workflow_templates
    return jsonify({"success": True, "data": get_workflow_templates()})


@automation_bp.route("/templates/<template_id>/create", methods=["POST"])
def api_create_from_template(template_id: str):
    if not _funded_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    identity_id = session.get("identity_id")
    from app.automation.service import create_from_template
    result = create_from_template(
        identity_id=identity_id,
        template_id=template_id,
        overrides=data.get("overrides"),
    )
    if not result:
        return jsonify({"success": False, "error": "Template not found"}), 404
    return jsonify({"success": True, "data": result}), 201