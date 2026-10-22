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


def _delivery_payload(result: dict | None) -> dict:
    """Truthful delivery report: acceptance is not delivery (G1.24).

    ``accepted`` means a provider or MTA took the message. ``delivered`` stays
    false: no inbox confirmation exists, and claiming one would be a fabricated
    success. The UI uses this to avoid telling an admin "sent" when nothing left
    the building.
    """
    status = str((result or {}).get("status") or "unknown")
    return {
        "status": status,
        "accepted": status == "accepted",
        "delivered": False,
        "record_id": (result or {}).get("record_id"),
    }


def _invite_url(token: str) -> str:
    """The SPA accept link for an invitation token (same URL the email carries)."""
    from app.email_service import BASE_URL

    return f"{BASE_URL}/auth/invitation?token={token}"


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

    # Deliver the invitation by email — the journey is NOT complete until the
    # invitee receives the accept link (previously the record was created and
    # nothing was ever sent: dead-end). Reuses the canonical email service.
    #
    # A send failure does not undo the invitation: the record is already
    # committed, and reporting 500 here would invite a retry that hits the
    # duplicate-pending guard. The outcome is reported instead (G1.24).
    delivery = {"status": "not_attempted", "accepted": False, "delivered": False}
    try:
        from app.email_service import build_invitation_email, send_email
        org_name = org.name if (org := db.session.get(Organization, org_id)) else ""
        inviter_name = ""
        try:
            from app.auth import TeamMember
            inviter_id = g.identity_id or session.get("user_id")
            if inviter_id:
                inv_uid = str(inviter_id)
                inviter = (TeamMember.query.get(int(inv_uid))
                           if inv_uid.isdigit() else
                           TeamMember.query.filter_by(email=inv_uid).first())
                if inviter:
                    inviter_name = inviter.name or inviter.email
        except Exception:
            logger.exception("Failed to resolve inviter name for invitation email")
        subject, body = build_invitation_email(
            email, token, org_name=org_name, inviter_name=inviter_name
        )
        email_result = send_email(
            to=email,
            subject=subject,
            body=body,
            notification_type="team_invitation",
            business_event_id=f"invite:{org_id}:{token[:8]}",
            category="security",
        )
        delivery = _delivery_payload(email_result)
        logger.info("Invitation email result: status=%s", delivery["status"])
    except Exception:
        delivery = {"status": "error", "accepted": False, "delivered": False}
        logger.exception("Failed to send invitation email to %s", email)

    # G1.24 (truthful delivery): report what actually happened. `accepted` means
    # a mail server took the message; it is NOT inbox delivery, so `delivered`
    # stays false. The accept link is returned to the admin who created the
    # invitation (the same rule the org-scoped invitation route uses), so a
    # failed send has a recovery path instead of a dead end.
    payload = invitation.to_dict()
    payload["delivery"] = delivery
    payload["invite_url"] = _invite_url(token)
    return jsonify({
        "success": True,
        "data": payload,
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
# GET /api/v1/team/invitations — list pending invitations (visibility)
# ---------------------------------------------------------------------------
@team_bp.route("/invitations", methods=["GET"])
@require_permission("org.manage_members")
def list_invitations():
    """Return pending invitations for the caller's organization.

    Closes the duplicate-invite dead-end: when an invite already exists the
    UI must show it (email, role, status, age), not just reject the resend.
    """
    org_id = g.current_org_id
    now = datetime.now(timezone.utc)
    invites = (
        OrgInvitation.query
        .filter_by(organization_id=org_id)
        .order_by(OrgInvitation.created_at.desc())
        .all()
    )
    results = []
    for inv in invites:
        expired = bool(inv.expires_at) and inv.expires_at.replace(tzinfo=timezone.utc) < now
        results.append({
            "id": inv.id,
            "email": inv.email,
            "name": inv.name or "",
            "role": inv.role or "member",
            "status": "expired" if (inv.status == "pending" and expired) else (inv.status or "pending"),
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
        })
    return jsonify({"success": True, "data": results, "total": len(results)}), 200


# ---------------------------------------------------------------------------
# POST /api/v1/team/invitations/<inv_id>/resend — re-deliver the invite email
# ---------------------------------------------------------------------------
@team_bp.route("/invitations/<int:inv_id>/resend", methods=["POST"])
@require_permission("org.manage_members")
def resend_invitation(inv_id):
    """Re-send the invitation email for a pending invitation.

    Uses the SAME token (an accept link already delivered is still valid);
    extends expiry by 7 days so stale links don't fail the invitee.
    """
    org_id = g.current_org_id
    inv = OrgInvitation.query.filter_by(id=inv_id, organization_id=org_id).first()
    if not inv:
        return jsonify({"success": False, "error": "Invitation not found"}), 404
    if inv.status not in ("pending", None):
        return jsonify({"success": False, "error": f"Invitation is already {inv.status}"}), 400

    # Refresh expiry so the re-sent link is usable
    inv.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db.session.commit()

    try:
        from app.email_service import build_invitation_email, send_email
        from app.models import Organization
        org = db.session.get(Organization, org_id)
        subject, body = build_invitation_email(
            inv.email, inv.token, org_name=org.name if org else ""
        )
        email_result = send_email(
            to=inv.email,
            subject=subject,
            body=body,
            notification_type="team_invitation",
            business_event_id=f"invite-resend:{org_id}:{inv.token[:8]}",
            category="security",
        )
        delivery = _delivery_payload(email_result)
    except Exception:
        logger.exception("Failed to resend invitation email to %s", inv.email)
        return jsonify({"success": False, "error": "Invitation email could not be sent"}), 500

    logger.info("Invitation resent: org=%s id=%s email=%s status=%s",
                org_id, inv_id, inv.email, delivery["status"])
    return jsonify({
        "success": True,
        "data": {
            "id": inv.id,
            "status": inv.status,
            "delivery": delivery,
            "invite_url": _invite_url(inv.token),
        },
    }), 200


# ---------------------------------------------------------------------------
# DELETE /api/v1/team/invitations/<inv_id> — revoke a pending invitation
# ---------------------------------------------------------------------------
@team_bp.route("/invitations/<int:inv_id>", methods=["DELETE"])
@require_permission("org.manage_members")
def revoke_invitation(inv_id):
    """Revoke a pending invitation so the email can be invited again."""
    org_id = g.current_org_id
    inv = OrgInvitation.query.filter_by(id=inv_id, organization_id=org_id).first()
    if not inv:
        return jsonify({"success": False, "error": "Invitation not found"}), 404
    if inv.accepted_at:
        return jsonify({"success": False, "error": "Cannot revoke an accepted invitation"}), 400
    db.session.delete(inv)
    db.session.commit()
    logger.info("Invitation revoked: org=%s id=%s email=%s", org_id, inv_id, inv.email)
    return jsonify({"success": True, "data": {"id": inv_id, "status": "revoked"}}), 200


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