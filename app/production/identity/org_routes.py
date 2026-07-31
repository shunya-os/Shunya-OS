"""SHUNYA — Organization CRUD API (Milestone X, D1).

RESTful endpoints for managing organizations (Tenant-based).
All endpoints require authentication. Responses use standard envelope.
"""

import re
from datetime import datetime

from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import NotFound, BadRequest, Forbidden

from app import db
from app.auth_routes import login_required
from app.tenant import Tenant, TenantTheme

# The blueprint is registered on identity_bp, which is mounted at /api/v1/orgs
# So routes here are relative to /api/v1/orgs
from app.production.identity import identity_bp


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def _generate_slug(company_name: str) -> str:
    """Generate a URL-safe slug from a company name.

    Examples:
        "SHUNYA OS" → "shunya-os"
        "My Company LLC" → "my-company-llc"
    """
    slug = company_name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:120] or "org"


def _ensure_unique_slug(base_slug: str) -> str:
    """Append a counter if the slug already exists."""
    slug = base_slug
    counter = 1
    while Tenant.query.filter_by(slug=slug).first() is not None:
        suffix = str(counter)
        max_base = 120 - len(suffix) - 1
        slug = f"{base_slug[:max_base]}-{suffix}"
        counter += 1
    return slug


# ---------------------------------------------------------------------------
# Request validation helpers
# ---------------------------------------------------------------------------

def _require_json() -> dict:
    """Get and validate JSON body."""
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _require_field(data: dict, field: str, label: str = "") -> str:
    """Get a required string field, raising BadRequest if missing/empty."""
    label = label or field
    value = data.get(field, "").strip()
    if not value:
        raise BadRequest(f"'{label}' is required")
    return value


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _org_to_dict(org: Tenant) -> dict:
    """Serialize an organization to the standard JSON envelope."""
    result = {
        "id": org.id,
        "company_name": org.company_name,
        "slug": org.slug,
        "business_type": org.business_type,
        "is_active": org.is_active,
        "plan": org.plan,
        "max_team_members": org.max_team_members,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "theme": org.theme.to_dict() if org.theme else {},
    }
    if org.parent_id:
        result["parent_id"] = org.parent_id
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@identity_bp.route("", methods=["GET"])
@login_required
def list_orgs():
    """List all organizations the current user has access to.

    For now, returns all active orgs. Future: filtered by user membership.
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Tenant.query.filter_by(is_active=True)
    pagination = query.order_by(Tenant.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "success": True,
        "data": [_org_to_dict(o) for o in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


@identity_bp.route("", methods=["POST"])
@login_required
def create_org():
    """Create a new organization."""
    data = _require_json()
    company_name = _require_field(data, "company_name", "Company name")
    business_type = data.get("business_type", "other").strip() or "other"

    slug = _ensure_unique_slug(_generate_slug(company_name))

    org = Tenant(
        company_name=company_name,
        slug=slug,
        business_type=business_type,
        is_active=True,
        plan=data.get("plan", "free"),
        max_team_members=data.get("max_team_members", 10),
    )
    db.session.add(org)
    db.session.flush()  # get org.id

    # Create default theme
    theme = TenantTheme(tenant_id=org.id)
    db.session.add(theme)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": _org_to_dict(org),
        "org_id": org.id,
        "org_name": org.company_name,
    }), 201


@identity_bp.route("/<int:org_id>", methods=["GET"])
@login_required
def get_org(org_id: int):
    """Get a single organization by ID."""
    org = db.session.get(Tenant, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")

    return jsonify({
        "success": True,
        "data": _org_to_dict(org),
    })


@identity_bp.route("/<int:org_id>", methods=["PUT"])
@login_required
def update_org(org_id: int):
    """Update an organization."""
    org = db.session.get(Tenant, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")

    data = _require_json()

    if "company_name" in data:
        name = data["company_name"].strip()
        if name:
            org.company_name = name

    if "business_type" in data:
        org.business_type = data["business_type"].strip() or "other"

    if "plan" in data:
        org.plan = data["plan"].strip()

    if "max_team_members" in data:
        org.max_team_members = int(data["max_team_members"])

    if "is_active" in data:
        org.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify({
        "success": True,
        "data": _org_to_dict(org),
    })


@identity_bp.route("/<int:org_id>", methods=["DELETE"])
@login_required
def delete_org(org_id: int):
    """Soft-delete an organization (deactivate rather than hard delete).

    For actual deletion, use the lifecycle endpoints (D1.7).
    """
    org = db.session.get(Tenant, org_id)
    if not org:
        raise NotFound("Organization not found")

    org.is_active = False
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {"id": org_id, "status": "deactivated"},
    })