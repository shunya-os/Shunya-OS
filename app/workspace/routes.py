"""Workspace Experience Framework — API Routes."""

from flask import jsonify, request, session
from app import db
from app.workspace import workspace_bp
from app.workspace.models import (
    EXPERIENCE_CATALOG, CONTEXT_MODES,
    get_available_experiences, resolve_experience_setting,
    set_policy, get_policy_summary,
    WorkspacePolicy,
)


@workspace_bp.route("/api/v1/workspace/experiences", methods=["GET"])
def api_get_workspace_experiences():
    org_id = session.get("current_org_id")
    if not org_id: return jsonify({"error": "No org"}), 400
    context_mode = request.args.get("context", "normal")
    return jsonify(get_available_experiences(org_id, context_mode))


@workspace_bp.route("/api/v1/workspace/experience/<key>", methods=["GET"])
def api_get_experience_setting(key):
    org_id = session.get("current_org_id")
    if not org_id: return jsonify({"error": "No org"}), 400
    return jsonify(resolve_experience_setting(org_id, key))


@workspace_bp.route("/api/v1/workspace/policies", methods=["GET"])
def api_list_policies():
    org_id = session.get("current_org_id")
    if not org_id: return jsonify({"error": "No org"}), 400
    return jsonify({"policies": get_policy_summary(org_id)})


@workspace_bp.route("/api/v1/workspace/policies", methods=["POST"])
def api_set_policy():
    org_id = session.get("current_org_id")
    if not org_id: return jsonify({"error": "No org"}), 400
    uid = session.get("identity_id") or session.get("user_id") or ""
    data = request.get_json(silent=True) or {}
    if data.get("experience_key") not in EXPERIENCE_CATALOG:
        return jsonify({"error": f"Unknown experience: {data.get('experience_key')}"}), 400
    result = set_policy(org_id, data.get("level", "org"),
        data.get("experience_key", ""), data.get("setting", "controlled"),
        level_id=data.get("level_id"), created_by=uid)
    return jsonify(result), 201


@workspace_bp.route("/api/v1/workspace/contexts", methods=["GET"])
def api_list_contexts():
    return jsonify({"contexts": [{"key": k, "label": v["label"]} for k, v in CONTEXT_MODES.items()]})


@workspace_bp.route("/api/v1/workspace/catalog", methods=["GET"])
def api_list_catalog():
    return jsonify({"catalog": [{"key": k, **v} for k, v in EXPERIENCE_CATALOG.items()]})