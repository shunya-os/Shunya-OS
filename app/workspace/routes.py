"""
Workspace API — workspace CRUD, switching, membership, and context endpoints.
"""

import logging
from flask import Blueprint, jsonify, request, session, g

from app import db
from app.workspace.models import (
    Workspace, WorkspaceMembership, WorkspaceType, WorkspaceMembership,
    create_workspace, get_workspaces_for_identity, switch_workspace,
    resolve_context, get_capabilities_for_type,
)

logger = logging.getLogger(__name__)

workspace_bp = Blueprint("workspace", __name__, url_prefix="/api/v1/workspace")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or str(session.get("user_id", ""))


def _require_auth():
    uid = _identity_id()
    if not uid:
        return None
    return uid


# ── Workspace CRUD ────────────────────────────────────────────────────


@workspace_bp.route("", methods=["GET"])
def api_list_workspaces():
    """List all workspaces the current identity belongs to."""
    uid = _require_auth()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    workspaces = get_workspaces_for_identity(uid)
    return jsonify({"success": True, "data": {"workspaces": workspaces}})


@workspace_bp.route("", methods=["POST"])
def api_create_workspace():
    """Create a new workspace."""
    uid = _require_auth()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    workspace_type = data.get("workspace_type", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return jsonify({"success": False, "error": "Workspace name is required."}), 400
    if not workspace_type:
        return jsonify({"success": False, "error": "Workspace type is required."}), 400

    from app.auth import TeamMember
    member = TeamMember.query.filter_by(email=uid).first() if "@" in str(uid) else None
    email = member.email if member else uid
    name_str = member.name if member else name

    ws = create_workspace(
        name=name,
        workspace_type=workspace_type,
        owner_identity_id=uid,
        owner_email=email,
        owner_name=name_str,
        description=description,
    )

    # Auto-switch to the new workspace
    session["current_workspace_id"] = ws.workspace_id
    session["current_workspace_type"] = ws.workspace_type
    session.modified = True

    return jsonify({"success": True, "data": ws.to_dict()}), 201


@workspace_bp.route("/<workspace_id>", methods=["GET"])
def api_get_workspace(workspace_id):
    """Get workspace details."""
    uid = _require_auth()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    membership = WorkspaceMembership.query.filter_by(
        identity_id=uid, is_active=True
    ).join(Workspace).filter(
        Workspace.workspace_id == workspace_id,
        Workspace.status == "active",
    ).first()

    if not membership:
        return jsonify({"error": "Workspace not found"}), 404

    ws = db.session.get(Workspace, membership.workspace_id)
    return jsonify({"success": True, "data": ws.to_dict()})


# ── Workspace Switching ────────────────────────────────────────────────


@workspace_bp.route("/switch", methods=["POST"])
def api_switch_workspace():
    """Switch the current workspace context."""
    uid = _require_auth()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    workspace_id = data.get("workspace_id", "").strip()

    if not workspace_id:
        return jsonify({"success": False, "error": "workspace_id is required."}), 400

    result = switch_workspace(uid, workspace_id)
    if not result:
        return jsonify({"success": False, "error": "Workspace not found or access denied."}), 404

    return jsonify({"success": True, "data": {"workspace": result}})


# ── Context ────────────────────────────────────────────────────────────


@workspace_bp.route("/context", methods=["GET"])
def api_get_context():
    """Get the current authorization context (who, where, what capabilities)."""
    uid = _require_auth()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    ctx = resolve_context(uid)
    return jsonify({"success": True, "data": ctx.to_dict()})


@workspace_bp.route("/capabilities", methods=["GET"])
def api_get_capabilities():
    """Get available capabilities for a workspace type."""
    workspace_type = request.args.get("workspace_type", "").strip()
    if workspace_type:
        wt = WorkspaceType.from_string(workspace_type)
        caps = get_capabilities_for_type(wt)
    else:
        uid = _require_auth()
        if not uid:
            return jsonify({"error": "Not authenticated"}), 401
        ctx = resolve_context(uid)
        caps = ctx.capabilities

    return jsonify({
        "success": True,
        "data": {
            "capabilities": sorted(caps),
            "count": len(caps),
        }
    })


@workspace_bp.route("/types", methods=["GET"])
def api_workspace_types():
    """List all supported workspace types."""
    types = [
        {
            "type": t.value,
            "name": t.name.title(),
            "description": _type_description(t),
        }
        for t in WorkspaceType
    ]
    return jsonify({"success": True, "data": {"types": types}})


def _type_description(t: WorkspaceType) -> str:
    descriptions = {
        WorkspaceType.PERSONAL: "Your personal SHUNYA — life, tasks, finance, knowledge, and AI.",
        WorkspaceType.BUSINESS: "Company workspace — operations, CRM, team, invoicing, and growth.",
        WorkspaceType.TEAM: "Team or group within a larger organization.",
        WorkspaceType.PROJECT: "Time-bounded project with focused collaboration.",
        WorkspaceType.FAMILY: "Family and household management.",
        WorkspaceType.COMMUNITY: "Community or group of shared interest.",
        WorkspaceType.NONPROFIT: "Nonprofit or charitable organization.",
        WorkspaceType.CREATOR: "Creator, freelancer, or artist workspace.",
        WorkspaceType.EDUCATION: "Educational or learning environment.",
        WorkspaceType.OTHER: "Custom workspace type.",
    }
    return descriptions.get(t, "SHUNYA workspace.")


# ── Register blueprint ─────────────────────────────────────────────────


def register_workspace_blueprint(app):
    """Register the workspace blueprint on the Flask app."""
    app.register_blueprint(workspace_bp)