"""SHUNYA — Organization CRUD API (Milestone X, D1).

Canonical Organization API using the Organization model (successor to Tenant).
All endpoints require authentication. Responses use standard envelope.
"""

import re
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.exceptions import NotFound, BadRequest, Forbidden

from app import db
from app.auth_routes import login_required
from app.models import Organization, OrgMember
from app.tenant import Tenant

from app.production.identity import identity_bp


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def _generate_slug(company_name: str) -> str:
    """Generate a URL-safe slug from a company name."""
    slug = company_name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:120] or "org"


def _ensure_unique_slug(base_slug: str) -> str:
    """Append a counter if the slug already exists."""
    slug = base_slug
    counter = 1
    while Organization.query.filter_by(slug=slug).first() is not None:
        suffix = str(counter)
        max_base = 120 - len(suffix) - 1
        slug = f"{base_slug[:max_base]}-{suffix}"
        counter += 1
    return slug


# ---------------------------------------------------------------------------
# Request validation helpers
# ---------------------------------------------------------------------------

def _require_json() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _require_field(data: dict, field: str, label: str = "") -> str:
    label = label or field
    value = data.get(field, "").strip()
    if not value:
        raise BadRequest(f"'{label}' is required")
    return value


# ---------------------------------------------------------------------------
# Serialization — map Organization fields to backward-compatible JSON names
# ---------------------------------------------------------------------------

def _org_to_dict(org: Organization) -> dict:
    """Serialize an organization to the standard JSON envelope."""
    return {
        "id": org.id,
        "company_name": org.name,
        "slug": org.slug,
        "business_type": org.business_type or "",
        "business_category": "",
        "company_email": org.email or "",
        "website": org.website or "",
        "phone": org.phone or "",
        "industry": "",
        "country": org.country or "",
        "timezone": org.timezone or "UTC",
        "currency": org.currency or "INR",
        "is_active": org.is_active,
        "plan": "free",
        "max_team_members": org.max_members,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "theme": {},
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@identity_bp.route("", methods=["GET"])
@login_required
def list_orgs():
    """List all organizations."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Organization.query.filter_by(is_active=True)
    pagination = query.order_by(Organization.created_at.desc()).paginate(
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
    company_email = data.get("company_email", "").strip() or ""
    website = data.get("website", "").strip() or ""
    phone = data.get("phone", "").strip() or ""
    country = data.get("country", "").strip() or ""
    timezone = data.get("timezone", "").strip() or "UTC"
    currency = data.get("currency", "").strip() or "INR"

    slug = _ensure_unique_slug(_generate_slug(company_name))

    org = Organization(
        name=company_name,
        slug=slug,
        business_type=business_type,
        email=company_email,
        website=website,
        phone=phone,
        country=country,
        timezone=timezone,
        currency=currency,
        is_active=True,
        max_members=data.get("max_team_members", 10),
    )
    db.session.add(org)
    db.session.flush()  # get org.id before creating member

    # Create owner membership for the current user
    identity_id = str(session.get("identity_id", "") or session.get("user_id", "") or "")
    if identity_id:
        member = OrgMember(
            organization_id=org.id,
            identity_id=identity_id,
            name=data.get("owner_name", ""),
            email=company_email,
            role="owner",
            designation="Owner",
        )
        db.session.add(member)

    db.session.commit()

    return jsonify({
        "success": True,
        "data": _org_to_dict(org),
        "org_id": org.id,
        "org_name": org.name,
    }), 201


@identity_bp.route("/<int:org_id>", methods=["GET"])
@login_required
def get_org(org_id: int):
    """Get a single organization by ID."""
    org = db.session.get(Organization, org_id)
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
    org = db.session.get(Organization, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")

    data = _require_json()

    if "company_name" in data:
        name = data["company_name"].strip()
        if name:
            org.name = name

    if "business_type" in data:
        org.business_type = data["business_type"].strip() or "other"

    if "company_email" in data:
        org.email = data["company_email"].strip()
    if "website" in data:
        org.website = data["website"].strip()
    if "phone" in data:
        org.phone = data["phone"].strip()
    if "country" in data:
        org.country = data["country"].strip()
    if "timezone" in data:
        org.timezone = data["timezone"].strip()
    if "currency" in data:
        org.currency = data["currency"].strip()

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
    """Soft-delete an organization (deactivate rather than hard delete)."""
    org = db.session.get(Organization, org_id)
    if not org:
        raise NotFound("Organization not found")

    org.is_active = False
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {"id": org_id, "status": "deactivated"},
    })