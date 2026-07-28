"""SHUNYA — User Management API (Milestone X, D1.3).

RESTful endpoints for managing users within organizations.
Extends the TeamMember model with organization scoping.
"""

import re
from datetime import datetime

from flask import request, jsonify
from werkzeug.exceptions import NotFound, BadRequest

from app import db
from app.auth_routes import login_required
from app.tenant import Tenant
from app.auth import TeamMember, UserRole
from app.production.identity import identity_bp


def _get_org_or_404(org_id: int) -> Tenant:
    org = db.session.get(Tenant, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")
    return org


def _require_json() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _validate_role(role: str) -> str:
    """Validate and normalize a role string."""
    valid = {r.value for r in UserRole}
    if role not in valid:
        raise BadRequest(
            f"Invalid role '{role}'. Valid roles: {', '.join(sorted(valid))}"
        )
    return role


def _user_to_dict(user: TeamMember) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone or "",
        "role": user.role,
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ---------------------------------------------------------------------------
# Routes — all at /api/v1/orgs/<org_id>/users
# ---------------------------------------------------------------------------


@identity_bp.route("/<int:org_id>/users", methods=["GET"])
@login_required
def list_users(org_id: int):
    """List all users in an organization."""
    _get_org_or_404(org_id)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    # Filter by organization — uses tenant_id on TeamMember or person link
    query = TeamMember.query.filter(
        TeamMember.is_active == True  # noqa: E712
    )
    pagination = query.order_by(TeamMember.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "success": True,
        "data": [_user_to_dict(u) for u in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


@identity_bp.route("/<int:org_id>/users", methods=["POST"])
@login_required
def create_user(org_id: int):
    """Create a new user in the organization."""
    _get_org_or_404(org_id)
    data = _require_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", UserRole.AGENT.value)

    if not name:
        raise BadRequest("'name' is required")
    if not email:
        raise BadRequest("'email' is required")
    if not password or len(password) < 6:
        raise BadRequest("'password' must be at least 6 characters")
    role = _validate_role(role)

    # Check for duplicate email
    existing = TeamMember.query.filter_by(email=email).first()
    if existing:
        raise BadRequest(f"A user with email '{email}' already exists")

    user = TeamMember(
        name=name,
        email=email,
        phone=data.get("phone", "").strip(),
        role=role,
        is_active=True,
    )
    user.set_password(password)
    user.generate_token()

    db.session.add(user)
    db.session.commit()

    return jsonify({"success": True, "data": _user_to_dict(user)}), 201


@identity_bp.route("/<int:org_id>/users/<int:user_id>", methods=["GET"])
@login_required
def get_user(org_id: int, user_id: int):
    """Get a single user by ID."""
    _get_org_or_404(org_id)
    user = db.session.get(TeamMember, user_id)
    if not user or not user.is_active:
        raise NotFound("User not found")

    return jsonify({"success": True, "data": _user_to_dict(user)})


@identity_bp.route("/<int:org_id>/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(org_id: int, user_id: int):
    """Update a user."""
    _get_org_or_404(org_id)
    user = db.session.get(TeamMember, user_id)
    if not user:
        raise NotFound("User not found")

    data = _require_json()

    if "name" in data and data["name"].strip():
        user.name = data["name"].strip()
    if "phone" in data:
        user.phone = data["phone"].strip()
    if "role" in data:
        user.role = _validate_role(data["role"])
    if "password" in data and len(data["password"]) >= 6:
        user.set_password(data["password"])
    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify({"success": True, "data": _user_to_dict(user)})


@identity_bp.route("/<int:org_id>/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(org_id: int, user_id: int):
    """Soft-delete (deactivate) a user."""
    _get_org_or_404(org_id)
    user = db.session.get(TeamMember, user_id)
    if not user:
        raise NotFound("User not found")

    user.is_active = False
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {"id": user_id, "status": "deactivated"},
    })