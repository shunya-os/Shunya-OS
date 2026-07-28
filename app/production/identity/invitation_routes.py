"""SHUNYA — Invitation System (Milestone X, D1.4).

Email-based invitation workflow for adding users to organizations.
"""

import secrets
from datetime import datetime, timedelta

from flask import request, jsonify
from werkzeug.exceptions import NotFound, BadRequest

from app import db
from app.auth_routes import login_required
from app.auth import TeamMember, UserRole
from app.tenant import Tenant
from app.production.identity import identity_bp

# ---------------------------------------------------------------------------
# Invitation Model (in-memory for now; migrate to SQLAlchemy when needed)
# ---------------------------------------------------------------------------

_invitations: dict = {}  # token -> Invitation dict


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


def _invitation_to_dict(inv: dict) -> dict:
    return {
        "id": inv["id"],
        "org_id": inv["org_id"],
        "email": inv["email"],
        "role": inv["role"],
        "token": inv["token"],
        "expires_at": inv["expires_at"].isoformat(),
        "accepted_at": inv.get("accepted_at").isoformat()
            if inv.get("accepted_at") else None,
        "status": "accepted" if inv.get("accepted_at") else "pending",
        "created_at": inv["created_at"].isoformat(),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@identity_bp.route("/<int:org_id>/invitations", methods=["GET"])
@login_required
def list_invitations(org_id: int):
    """List pending invitations for an organization."""
    _get_org_or_404(org_id)
    org_invites = [
        inv for inv in _invitations.values()
        if inv["org_id"] == org_id
    ]
    return jsonify({
        "success": True,
        "data": [_invitation_to_dict(inv) for inv in org_invites],
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
    now = datetime.utcnow()

    # Get next ID
    inv_id = max([inv["id"] for inv in _invitations.values()], default=0) + 1

    invitation = {
        "id": inv_id,
        "org_id": org_id,
        "email": email,
        "role": role,
        "token": token,
        "expires_at": now + timedelta(hours=48),
        "accepted_at": None,
        "created_at": now,
    }
    _invitations[token] = invitation

    return jsonify({
        "success": True,
        "data": _invitation_to_dict(invitation),
    }), 201


@identity_bp.route("/invitations/<token>", methods=["GET"])
@login_required
def get_invitation(token: str):
    """Get invitation details by token."""
    inv = _invitations.get(token)
    if not inv:
        raise NotFound("Invitation not found or expired")

    if inv.get("accepted_at"):
        raise NotFound("Invitation has already been accepted")

    if datetime.utcnow() > inv["expires_at"]:
        raise NotFound("Invitation has expired")

    return jsonify({
        "success": True,
        "data": _invitation_to_dict(inv),
    })


@identity_bp.route("/invitations/<token>/accept", methods=["POST"])
def accept_invitation(token: str):
    """Accept an invitation and create the user account."""
    inv = _invitations.get(token)
    if not inv:
        raise NotFound("Invitation not found or expired")

    if inv.get("accepted_at"):
        raise NotFound("Invitation has already been accepted")

    if datetime.utcnow() > inv["expires_at"]:
        raise NotFound("Invitation has expired")

    data = _require_json()
    name = data.get("name", "").strip()
    password = data.get("password", "")

    if not name:
        raise BadRequest("'name' is required")
    if not password or len(password) < 6:
        raise BadRequest("'password' must be at least 6 characters")

    # Check still no duplicate
    existing = TeamMember.query.filter_by(email=inv["email"]).first()
    if existing:
        raise BadRequest(f"User with email '{inv['email']}' already exists")

    user = TeamMember(
        name=name,
        email=inv["email"],
        role=inv["role"],
        is_active=True,
    )
    user.set_password(password)
    user.generate_token()

    db.session.add(user)
    db.session.commit()

    # Mark invitation as accepted
    inv["accepted_at"] = datetime.utcnow()

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
    for token, inv in list(_invitations.items()):
        if inv["id"] == inv_id and inv["org_id"] == org_id:
            if inv.get("accepted_at"):
                raise BadRequest("Cannot revoke an accepted invitation")
            del _invitations[token]
            return jsonify({
                "success": True,
                "data": {"id": inv_id, "status": "revoked"},
            })
    raise NotFound("Invitation not found")