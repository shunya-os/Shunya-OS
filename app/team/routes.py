"""Team Management API routes.

All routes require authentication and enforce RBAC via @require_permission.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from flask import Blueprint, jsonify, request, session, g

from app import db
from app.models import OrgMember, OrgInvitation
from app.authz.models import Role
from app.authz.decorators import require_permission

logger = logging.getLogger(__name__)

team_bp = Blueprint("team", __name__, url_prefix="/api/v1/team")


# ---------------------------------------------------------------------------
# GET /api/v1/team/members — list all active members of the current org
# ---------------------------------------------------------------------------
@team_bp.route("/members", methods=["GET"])
@require_permission("people.view")
def list_members():
    """Return all active members for the caller's organization."""
    org_id = g.current_org_id
    members = (
        OrgMember.query
        .filter_by(organization_id=org_id, is_active=True)
        .order_by(OrgMember.joined_at.desc())
        .all()
    )
    results = []
    for m in members:
        data = m.to_dict()
        # Resolve assigned role names from OrgMemberRole
        from app.authz.models import OrgMemberRole, Role as AuthRole
        assignments = (
            OrgMemberRole.query
            .filter_by(organization_id=org_id, member_id=m.id)
            .all()
        )
        roles = []
        for a in assignments:
            role = db.session.get(AuthRole, a.role_id)
            if role:
                roles.append({"id": role.id, "name": role.name, "display_name": role.display_name})
        data["roles"] = roles
        results.append(data)

    return jsonify({"success": True, "data": results, "total": len(results)}), 200


# ---------------------------------------------------------------------------
# POST /api/v1/team/invite — invite a person by email
# ---------------------------------------------------------------------------
@team_bp.route("/invite", methods=["POST"])
@require_permission("org.manage_members")
def invite_member():
    """Create an invitation record for the given email + role."""
    org_id = g.current_org_id
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    role_name = (body.get("role") or "member").strip()
    name = (body.get("name") or "").strip()

    if not email or "@" not in email:
        return jsonify({"success": False, "error": "A valid email is required"}), 400

    # Check member limit
    from app.models import Organization
    org = db.session.get(Organization, org_id)
    if org and org.max_members:
        current_count = OrgMember.query.filter_by(organization_id=org_id, is_active=True).count()
        if current_count >= org.max_members:
            return jsonify({"success": False, "error": "Organization member limit reached"}), 400

    # Prevent duplicate active members
    existing = OrgMember.query.filter_by(organization_id=org_id, email=email, is_active=True).first()
    if existing:
        return jsonify({"success": False, "error": "This person is already a member of your organization"}), 409

    # Prevent duplicate pending invitation
    pending = OrgInvitation.query.filter_by(
        organization_id=org_id, email=email, status="pending"
    ).first()
    if pending:
        return jsonify({"success": False, "error": "An invitation has already been sent to this email"}), 409

    token = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    inviter = g.identity_id or "system"

    invitation = OrgInvitation(
        organization_id=org_id,
        email=email,
        name=name,
        role=role_name,
        token=token,
        status="pending",
        invited_by=inviter,
        expires_at=expires_at,
    )
    db.session.add(invitation)
    db.session.commit()

    logger.info("Invitation created: org=%s email=%s role=%s", org_id, email, role_name)

    return jsonify({
        "success": True,
        "data": invitation.to_dict(),
    }), 201


# ---------------------------------------------------------------------------
# DELETE /api/v1/team/members/<member_id> — remove a member by id
# ---------------------------------------------------------------------------
@team_bp.route("/members/<int:member_id>", methods=["DELETE"])
@require_permission("org.manage_members")
def remove_member(member_id):
    """Deactivate an OrgMember (soft-delete by setting is_active=False)."""
    org_id = g.current_org_id
    member = OrgMember.query.filter_by(
        id=member_id, organization_id=org_id, is_active=True
    ).first()
    if not member:
        return jsonify({"success": False, "error": "Member not found"}), 404

    # Prevent removing yourself
    caller_identity = g.identity_id or ""
    if member.identity_id == caller_identity:
        return jsonify({"success": False, "error": "You cannot remove yourself from the organization"}), 400

    member.is_active = False
    db.session.commit()

    logger.info("Member removed: org=%s member_id=%s email=%s", org_id, member_id, member.email)

    return jsonify({"success": True, "data": {"id": member.id}}), 200


# ---------------------------------------------------------------------------
# PUT /api/v1/team/members/<member_id>/role — change member's role
# ---------------------------------------------------------------------------
@team_bp.route("/members/<int:member_id>/role", methods=["PUT"])
@require_permission("org.manage_members")
def change_member_role(member_id):
    """Update a member's role assignment."""
    org_id = g.current_org_id
    body = request.get_json(silent=True) or {}
    new_role = (body.get("role") or "").strip().lower()

    if not new_role:
        return jsonify({"success": False, "error": "Role is required"}), 400

    # Verify the role exists for this org
    role = Role.query.filter_by(organization_id=org_id, name=new_role).first()
    if not role:
        return jsonify({"success": False, "error": f"Role '{new_role}' does not exist in this organization"}), 400

    member = OrgMember.query.filter_by(
        id=member_id, organization_id=org_id, is_active=True
    ).first()
    if not member:
        return jsonify({"success": False, "error": "Member not found"}), 404

    # Update the role field on OrgMember
    member.role = new_role
    db.session.commit()

    # Sync OrgMemberRole assignment (replace existing)
    from app.authz.models import OrgMemberRole
    OrgMemberRole.query.filter_by(organization_id=org_id, member_id=member.id).delete()
    assignment = OrgMemberRole(
        organization_id=org_id,
        member_id=member.id,
        role_id=role.id,
        scope="organization",
        granted_by=g.identity_id or "system",
    )
    db.session.add(assignment)
    db.session.commit()

    logger.info("Role changed: org=%s member_id=%s new_role=%s", org_id, member_id, new_role)

    return jsonify({
        "success": True,
        "data": {"id": member.id, "role": new_role, "role_id": role.id},
    }), 200


# ---------------------------------------------------------------------------
# GET /api/v1/team/roles — list available roles with permissions
# ---------------------------------------------------------------------------
@team_bp.route("/roles", methods=["GET"])
@require_permission("people.view")
def list_roles():
    """Return all roles configured for the caller's organization."""
    org_id = g.current_org_id
    roles = Role.query.filter_by(organization_id=org_id).order_by(Role.display_name).all()
    results = [r.to_dict() for r in roles]

    return jsonify({"success": True, "data": results, "total": len(results)}), 200