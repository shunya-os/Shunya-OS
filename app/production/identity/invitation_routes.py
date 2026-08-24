"""SHUNYA — Invitation System (Milestone X, D1.4).

Email-based invitation workflow for adding users to organizations.
Uses persistent InvitationToken model.
"""

import secrets
from datetime import datetime, timedelta, timezone

from flask import jsonify, request
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth import InvitationToken, TeamMember, UserRole
from app.auth_routes import login_required
from app.production.identity import identity_bp
from app.tenant import Tenant


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _get_org_or_404(org_id: int) -> Tenant:
    org = db.session.get(Tenant, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")
    return org


def _validate_role(role: str) -> str:
    valid = {r.value for r in UserRole}
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


def _invitation_to_dict(inv: InvitationToken) -> dict:
    return {
        "id": inv.id,
        "org_id": inv.org_id,
        "email": inv.email,
        "role": inv.role,
        "token": inv.token,
        "expires_at": inv.expires_at.isoformat(),
        "accepted_at": inv.accepted_at.isoformat()
            if inv.accepted_at else None,
        "status": inv.status,
        "created_at": inv.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@identity_bp.route("/<int:org_id>/invitations", methods=["GET"])
@login_required
def list_invitations(org_id: int):
    """List pending invitations for an organization."""
    _get_org_or_404(org_id)
    invites = InvitationToken.query.filter_by(org_id=org_id).order_by(
        InvitationToken.created_at.desc()
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
    role = data.get("role", UserRole.AGENT.value)

    if not email:
        raise BadRequest("'email' is required")
    role = _validate_role(role)

    # Check user doesn't already exist
    existing = TeamMember.query.filter_by(email=email).first()
    if existing:
        raise BadRequest(f"User with email '{email}' already exists")

    token = _generate_token()
    invitation = InvitationToken(
        token=token,
        org_id=org_id,
        email=email,
        role=role,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
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
    inv = InvitationToken.query.filter_by(token=token).first()
    if not inv:
        raise NotFound("Invitation not found or expired")

    if inv.accepted_at:
        raise NotFound("Invitation has already been accepted")

    if datetime.now(timezone.utc) > inv.expires_at:
        raise NotFound("Invitation has expired")

    return jsonify({
        "success": True,
        "data": _invitation_to_dict(inv),
    })


@identity_bp.route("/invitations/<token>/accept", methods=["POST"])
def accept_invitation(token: str):
    """Accept an invitation and create the user account."""
    inv = InvitationToken.query.filter_by(token=token).first()
    if not inv:
        raise NotFound("Invitation not found or expired")

    if inv.accepted_at:
        raise NotFound("Invitation has already been accepted")

    if datetime.now(timezone.utc) > inv.expires_at:
        raise NotFound("Invitation has expired")

    data = _require_json()
    name = data.get("name", "").strip()
    password = data.get("password", "")

    if not name:
        raise BadRequest("'name' is required")
    if not password or len(password) < 6:
        raise BadRequest("'password' must be at least 6 characters")

    # Check still no duplicate
    existing = TeamMember.query.filter_by(email=inv.email).first()
    if existing:
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
    db.session.commit()

    # Mark invitation as accepted
    inv.accepted_at = datetime.now(timezone.utc)
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
    inv = db.session.get(InvitationToken, inv_id)
    if not inv or inv.org_id != org_id:
        raise NotFound("Invitation not found")
    if inv.accepted_at:
        raise BadRequest("Cannot revoke an accepted invitation")
    db.session.delete(inv)
    db.session.commit()
    return jsonify({
        "success": True,
        "data": {"id": inv_id, "status": "revoked"},
    })