"""SHUNYA — Invitation System (Milestone X, D1.4).

Email-based invitation workflow for adding users to organizations.
Uses canonical OrgInvitation model and creates OrgMember on acceptance.
"""

import secrets
from datetime import datetime, timedelta

from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth_routes import login_required
from app.models import Organization, OrgMember, OrgInvitation
from app.production.identity import identity_bp


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _get_org_or_404(org_id: int) -> Organization:
    """Get an organization by ID or raise NotFound."""
    org = db.session.get(Organization, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")
    return org


def _validate_role(role: str) -> str:
    valid = {"viewer", "member", "manager", "admin", "owner", "agent"}
    if role not in valid:
        raise BadRequest(
            f"Invalid role '{role}'. Valid roles: {', '.join(sorted(valid))}"
        )
    return role


def _require_json() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _invitation_to_dict(inv: OrgInvitation) -> dict:
    return {
        "id": inv.id,
        "org_id": inv.organization_id,
        "email": inv.email,
        "name": inv.name,
        "role": inv.role,
        "token": inv.token,
        "status": inv.status,
        "invited_by": inv.invited_by,
        "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
        "accepted_at": inv.accepted_at.isoformat() if inv.accepted_at else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@identity_bp.route("/<int:org_id>/invitations", methods=["GET"])
@login_required
def list_invitations(org_id: int):
    """List invitations for an organization."""
    _get_org_or_404(org_id)
    invites = OrgInvitation.query.filter_by(organization_id=org_id).order_by(
        OrgInvitation.created_at.desc()
    ).all()
    return jsonify({
        "success": True,
        "data": [_invitation_to_dict(inv) for inv in invites],
    })


@identity_bp.route("/<int:org_id>/invitations", methods=["POST"])
@login_required
def create_invitation(org_id: int):
    """Create an invitation to join an organization."""
    _get_org_or_404(org_id)
    data = _require_json()

    email = data.get("email", "").strip().lower()
    role = data.get("role", "agent")

    if not email:
        raise BadRequest("'email' is required")
    role = _validate_role(role)

    # Check user doesn't already exist as a member
    existing_member = OrgMember.query.filter_by(organization_id=org_id, email=email).first()
    if existing_member:
        raise BadRequest(f"User with email '{email}' is already a member")

    token = _generate_token()
    invitation = OrgInvitation(
        organization_id=org_id,
        email=email,
        name=data.get("name", email.split("@")[0]),
        role=role,
        token=token,
        invited_by=str(session.get("identity_id", "") or session.get("user_id", "") or ""),
        expires_at=datetime.utcnow() + timedelta(hours=48),
    )
    db.session.add(invitation)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": _invitation_to_dict(invitation),
    }), 201


@identity_bp.route("/invitations/<token>", methods=["GET"])
def get_invitation(token: str):
    """Get invitation details by token."""
    inv = OrgInvitation.query.filter_by(token=token).first()
    if not inv:
        raise NotFound("Invitation not found or expired")

    if inv.accepted_at:
        raise NotFound("Invitation has already been accepted")

    now = datetime.utcnow()
    if inv.expires_at and now.replace(tzinfo=None) > inv.expires_at.replace(tzinfo=None):
        raise NotFound("Invitation has expired")

    return jsonify({
        "success": True,
        "data": _invitation_to_dict(inv),
    })


@identity_bp.route("/invitations/<token>/accept", methods=["POST"])
def accept_invitation(token: str):
    """Accept an invitation, create member record and user account."""
    inv = OrgInvitation.query.filter_by(token=token).first()
    if not inv:
        raise NotFound("Invitation not found or expired")

    if inv.accepted_at:
        raise NotFound("Invitation has already been accepted")

    now = datetime.utcnow()
    if inv.expires_at and now.replace(tzinfo=None) > inv.expires_at.replace(tzinfo=None):
        raise NotFound("Invitation has expired")

    data = _require_json()
    name = data.get("name", "").strip()
    password = data.get("password", "")

    if not name:
        raise BadRequest("'name' is required")
    if not password or len(password) < 6:
        raise BadRequest("'password' must be at least 6 characters")

    # Check still no duplicate member
    existing_member = OrgMember.query.filter_by(
        organization_id=inv.organization_id, email=inv.email
    ).first()
    if existing_member:
        raise BadRequest(f"User with email '{inv.email}' is already a member")

    # Create TeamMember
    from app.auth import TeamMember

    existing_user = TeamMember.query.filter_by(email=inv.email).first()
    if existing_user:
        raise BadRequest(f"User with email '{inv.email}' already exists")

    user = TeamMember(
        name=name,
        email=inv.email,
        role=inv.role,
        is_active=True,
    )
    user.set_password(password)
    user.generate_token()
    db.session.add(user)
    db.session.flush()

    # Create OrgMember record
    identity_id = str(user.id)
    member = OrgMember(
        organization_id=inv.organization_id,
        identity_id=identity_id,
        name=name,
        email=inv.email,
        role=inv.role,
        invited_by=inv.invited_by,
    )
    db.session.add(member)

    # Mark invitation as accepted
    inv.accepted_at = datetime.utcnow()
    inv.status = "accepted"
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
        },
    }), 201


@identity_bp.route("/<int:org_id>/invitations/<int:inv_id>", methods=["DELETE"])
@login_required
def revoke_invitation(org_id: int, inv_id: int):
    """Revoke a pending invitation."""
    _get_org_or_404(org_id)
    inv = db.session.get(OrgInvitation, inv_id)
    if not inv or inv.organization_id != org_id:
        raise NotFound("Invitation not found")
    if inv.accepted_at:
        raise BadRequest("Cannot revoke an accepted invitation")
    db.session.delete(inv)
    db.session.commit()
    return jsonify({
        "success": True,
        "data": {"id": inv_id, "status": "revoked"},
    })