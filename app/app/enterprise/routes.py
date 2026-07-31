"""SHUNYA M9 — Enterprise Ready Routes.

Audit trail, team management, roles, RBAC, tenant isolation.
"""
from flask import Blueprint, jsonify, request, session

enterprise_bp = Blueprint("enterprise", __name__, url_prefix="/api/v1/enterprise")


def _founder_required() -> bool:
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    return bool(user_id and identity_id)


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

@enterprise_bp.route("/audit", methods=["GET"])
def api_query_audit():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.enterprise.service import get_organization_for_identity, query_audit
    org_id = get_organization_for_identity(identity_id)
    results = query_audit(
        organization_id=org_id,
        actor_id=request.args.get("actor_id"),
        entity_id=request.args.get("entity_id"),
        action=request.args.get("action"),
        limit=request.args.get("limit", 100, type=int),
        offset=request.args.get("offset", 0, type=int),
    )
    return jsonify({"success": True, "data": results})


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

@enterprise_bp.route("/roles", methods=["GET"])
def api_list_roles():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.enterprise.service import get_organization_for_identity, get_roles, seed_system_roles
    org_id = get_organization_for_identity(identity_id)
    if not org_id:
        return jsonify({"success": False, "error": "No organization found"}), 400
    seed_system_roles(org_id)
    roles = get_roles(org_id)
    return jsonify({"success": True, "data": roles})


@enterprise_bp.route("/roles", methods=["POST"])
def api_create_role():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    data = request.get_json(silent=True) or {}
    from app.enterprise.service import create_role, get_organization_for_identity, record_audit
    org_id = get_organization_for_identity(identity_id)
    if not org_id:
        return jsonify({"success": False, "error": "No organization"}), 400
    role = create_role(
        organization_id=org_id,
        name=data.get("name", ""),
        description=data.get("description", ""),
        permissions=data.get("permissions"),
    )
    record_audit(
        actor_id=identity_id, action="permission_change",
        entity_type="permission", entity_name=role.name,
        organization_id=org_id,
    )
    return jsonify({"success": True, "data": role.to_dict()}), 201


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

@enterprise_bp.route("/team", methods=["GET"])
def api_list_team():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.enterprise.service import get_organization_for_identity, get_team
    org_id = get_organization_for_identity(identity_id)
    if not org_id:
        return jsonify({"success": False, "error": "No organization"}), 400
    team = get_team(org_id)
    return jsonify({"success": True, "data": team})


@enterprise_bp.route("/team/invite", methods=["POST"])
def api_invite_member():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    data = request.get_json(silent=True) or {}
    from app.enterprise.service import (
        get_organization_for_identity, invite_member, record_audit,
    )
    org_id = get_organization_for_identity(identity_id)
    if not org_id:
        return jsonify({"success": False, "error": "No organization"}), 400
    member = invite_member(
        organization_id=org_id,
        identity_id=data.get("identity_id", ""),
        name=data.get("name", ""),
        email=data.get("email", ""),
        role_id=data.get("role_id"),
        invited_by=identity_id,
    )
    record_audit(
        actor_id=identity_id, action="invite",
        entity_type="user", entity_id=member.identity_id,
        entity_name=member.name, organization_id=org_id,
    )
    return jsonify({"success": True, "data": member.to_dict()}), 201


@enterprise_bp.route("/team/<member_identity_id>", methods=["DELETE"])
def api_remove_member(member_identity_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.enterprise.service import get_organization_for_identity, record_audit, remove_member
    org_id = get_organization_for_identity(identity_id)
    if not org_id:
        return jsonify({"success": False, "error": "No organization"}), 400
    success = remove_member(organization_id=org_id, identity_id=member_identity_id)
    if success:
        record_audit(
            actor_id=identity_id, action="delete",
            entity_type="user", entity_id=member_identity_id,
            organization_id=org_id,
        )
    return jsonify({"success": success})


# ---------------------------------------------------------------------------
# RBAC Check
# ---------------------------------------------------------------------------

@enterprise_bp.route("/check-permission", methods=["POST"])
def api_check_permission():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    data = request.get_json(silent=True) or {}
    from app.enterprise.service import check_permission
    result = check_permission(
        identity_id=identity_id,
        resource=data.get("resource", ""),
        action=data.get("action", ""),
        organization_id=data.get("organization_id"),
    )
    return jsonify({"success": True, "data": result})