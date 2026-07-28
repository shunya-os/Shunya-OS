"""FOR-2C.2: Authorization Engine — API routes."""

from flask import jsonify, request, session
from app import db
from app.authz import authz_bp
from app.authz.models import Role, OrgMemberRole
from app.authz.services import seed_default_roles, check_permission, get_member_permissions, get_all_permission_keys
from app.models import OrgMember


# ── Helpers ─────────────────────────────────────────────────────────────


def _identity():
    return session.get("identity_id") or session.get("user_id") or ""


def _require_auth():
    uid = _identity()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    return None


def _require_org():
    org_id = session.get("current_org_id")
    if not org_id:
        return jsonify({"error": "No organization selected"}), 400
    return org_id


# ── Permission definitions (read-only) ──────────────────────────────────


@authz_bp.route("/api/v1/authz/permissions", methods=["GET"])
def api_list_permissions():
    """List all canonical permission keys."""
    return jsonify({"permissions": get_all_permission_keys()})


# ── Role CRUD ────────────────────────────────────────────────────────────


@authz_bp.route("/api/v1/authz/roles", methods=["GET"])
def api_list_roles():
    """List all roles for the current organization."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    roles = Role.query.filter_by(organization_id=org_id).all()
    return jsonify({"roles": [r.to_dict() for r in roles]})


@authz_bp.route("/api/v1/authz/roles", methods=["POST"])
def api_create_role():
    """Create a custom role."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    data = request.get_json(silent=True) or {}
    import json
    role = Role(
        organization_id=org_id,
        name=data.get("name", "").strip().lower().replace(" ", "_"),
        display_name=data.get("display_name", "").strip(),
        description=data.get("description", ""),
        permissions=json.dumps(data.get("permissions", [])),
        is_system=False,
    )
    db.session.add(role)
    db.session.commit()
    return jsonify({"success": True, "role": role.to_dict()}), 201


@authz_bp.route("/api/v1/authz/roles/<int:role_id>", methods=["PATCH"])
def api_update_role(role_id):
    """Update a role's permissions."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    role = db.session.get(Role, role_id)
    if not role or role.organization_id != org_id:
        return jsonify({"error": "Role not found"}), 404
    if role.is_system:
        return jsonify({"error": "System roles cannot be modified"}), 403

    data = request.get_json(silent=True) or {}
    import json
    if "display_name" in data:
        role.display_name = data["display_name"]
    if "description" in data:
        role.description = data["description"]
    if "permissions" in data:
        role.permissions = json.dumps(data["permissions"])
    db.session.commit()
    return jsonify({"success": True, "role": role.to_dict()})


# ── Member role assignments ──────────────────────────────────────────────


@authz_bp.route("/api/v1/authz/members/<int:member_id>/roles", methods=["GET"])
def api_get_member_roles(member_id):
    """Get all roles assigned to a member."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    member = db.session.get(OrgMember, member_id)
    if not member or member.organization_id != org_id:
        return jsonify({"error": "Member not found"}), 404

    assignments = OrgMemberRole.query.filter_by(
        organization_id=org_id, member_id=member_id
    ).all()

    roles = []
    for a in assignments:
        role = db.session.get(Role, a.role_id)
        if role:
            roles.append({"assignment": a.to_dict(), "role": role.to_dict()})

    return jsonify({"member_id": member_id, "roles": roles})


@authz_bp.route("/api/v1/authz/members/<int:member_id>/roles", methods=["POST"])
def api_assign_role(member_id):
    """Assign a role to a member."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    member = db.session.get(OrgMember, member_id)
    if not member or member.organization_id != org_id:
        return jsonify({"error": "Member not found"}), 404

    data = request.get_json(silent=True) or {}
    role_id = data.get("role_id")
    if not role_id:
        return jsonify({"error": "role_id is required"}), 400

    role = db.session.get(Role, role_id)
    if not role or role.organization_id != org_id:
        return jsonify({"error": "Role not found"}), 404

    existing = OrgMemberRole.query.filter_by(
        organization_id=org_id, member_id=member_id, role_id=role_id
    ).first()
    if existing:
        return jsonify({"error": "Role already assigned"}), 409

    assignment = OrgMemberRole(
        organization_id=org_id,
        member_id=member_id,
        role_id=role_id,
        scope=data.get("scope", "organization"),
        scope_id=data.get("scope_id"),
        granted_by=_identity(),
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"success": True, "assignment": assignment.to_dict()}), 201


@authz_bp.route("/api/v1/authz/members/<int:member_id>/roles/<int:role_id>", methods=["DELETE"])
def api_remove_role(member_id, role_id):
    """Remove a role from a member."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    assignment = OrgMemberRole.query.filter_by(
        organization_id=org_id, member_id=member_id, role_id=role_id
    ).first()
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"success": True})


# ── Authorization check ─────────────────────────────────────────────────


@authz_bp.route("/api/v1/authz/check", methods=["GET"])
def api_check_permission():
    """Check if the current user has a specific permission."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    permission = request.args.get("permission", "")
    if not permission:
        return jsonify({"error": "permission parameter required"}), 400
    has_perm = check_permission(org_id, _identity(), permission)
    return jsonify({"permission": permission, "has_permission": has_perm})


@authz_bp.route("/api/v1/authz/my-permissions", methods=["GET"])
def api_my_permissions():
    """Get all permissions for the current user."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    perms = get_member_permissions(org_id, _identity())
    return jsonify({"permissions": perms})


# ── Seed roles on demand ─────────────────────────────────────────────────


@authz_bp.route("/api/v1/authz/seed", methods=["POST"])
def api_seed_roles():
    """Seed default roles for the current organization."""
    auth = _require_auth()
    if auth: return auth
    org_id = _require_org()
    if not org_id: return org_id

    seed_default_roles(org_id)
    roles = Role.query.filter_by(organization_id=org_id).all()
    return jsonify({"success": True, "roles": [r.to_dict() for r in roles]})