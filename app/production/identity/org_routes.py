"""SHUNYA — Organization CRUD API (Milestone X, D1).

Canonical Organization API using the Organization model (successor to Tenant).
All endpoints require authentication. Responses use standard envelope.
"""

import re
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.exceptions import NotFound, BadRequest, Forbidden

from app import db
from app.auth_routes import login_required
from app.models import Organization, OrgMember
from app.runtime_config import uploads_dir
from sqlalchemy.exc import IntegrityError

from app.production.identity import identity_bp


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def _generate_slug(company_name: str) -> str:
    """Generate a URL-safe slug from a company name.

    G1.21: delegated to ``app.authz.org_slug`` so every organization-creation
    path uses one implementation (the SPA route previously did not sanitize or
    de-duplicate at all).
    """
    from app.authz.org_slug import generate_org_slug

    return generate_org_slug(company_name)


def _ensure_unique_slug(base_slug: str) -> str:
    """Append a counter if the slug already exists (shared implementation)."""
    from app.authz.org_slug import ensure_unique_org_slug

    return ensure_unique_org_slug(base_slug)


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
        "plan": org.plan or "free",
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
    """List organizations the current user belongs to (scoped by membership)."""
    from app.models import OrgMember
    from app.authz.decorators import _resolve_identity
    identity = _resolve_identity()
    if not identity:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    member_org_ids = [
        m.organization_id for m in
        OrgMember.query.filter_by(identity_id=identity, is_active=True).all()
    ]

    if not member_org_ids:
        return jsonify({
            "success": True,
            "data": [],
            "pagination": {"page": 1, "per_page": 20, "total": 0, "pages": 0},
        })

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Organization.query.filter(
        Organization.id.in_(member_org_ids), Organization.is_active.is_(True)
    )
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
        plan=data.get("plan", "free"),
        is_active=True,
        max_members=data.get("max_team_members", 10),
    )
    db.session.add(org)
    try:
        db.session.flush()  # get org.id before creating member
    except IntegrityError:
        # Unique slug index is the authority; a competing request that won the
        # race must produce 409, not a driver error.
        db.session.rollback()
        current_app.logger.warning(
            "organization creation conflicted at insert (slug)")
        return jsonify({
            "success": False,
            "code": "organization_conflict",
            "error": "An organization with these details already exists",
        }), 409

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

    # Seed default roles for this organization
    from app.authz.services import seed_default_roles
    seed_default_roles(org.id, commit=False)  # same transaction as the workspace

    # Provision the organization's first canonical workspace in the SAME
    # transaction (G1.19). Without it the tenant owns no sh_workspaces row, so
    # every canonical object surface fails closed (`403 no_authorized_workspace`
    # on GET /api/v1/objects, onboarding seeding, uploads, media, AI creation).
    # The helper is idempotent, membership-gated and never elevates a role.
    from app.authz.org_provisioning import (
        WorkspaceProvisioningError,
        ensure_organization_workspace,
    )

    if not identity_id:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "An authenticated identity is required to create an organization",
        }), 400

    try:
        workspace = ensure_organization_workspace(
            org.id, identity_id, name=org.name, commit=False
        )
    except WorkspaceProvisioningError:
        db.session.rollback()
        current_app.logger.exception(
            "organization provisioning failed: org=%s identity=%s", org.id, identity_id
        )
        return jsonify({
            "success": False,
            "code": "workspace_provisioning_failed",
            "error": "Organization could not be provisioned with a workspace",
        }), 500

    try:
        db.session.commit()
    except IntegrityError:
        # Same concurrency guarantee as the SPA route: the unique slug index is
        # the authority, and the caller receives 409 rather than a stack trace.
        db.session.rollback()
        current_app.logger.warning(
            "organization creation conflicted (slug or duplicate org)")
        return jsonify({
            "success": False,
            "code": "organization_conflict",
            "error": "An organization with these details already exists",
        }), 409

    return jsonify({
        "success": True,
        "data": _org_to_dict(org),
        "org_id": org.id,
        "org_name": org.name,
        "workspace_id": workspace["workspace_id"],
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


# ---------------------------------------------------------------------------
# Org Theme + Logo — closes the dead-end where GET/PUT /orgs/<id>/theme and
# POST /orgs/<id>/logo returned 404 while the frontend ThemeSettings modal
# called them. Theme JSON is stored inside the Organization's existing
# settings blob (ai_config, a JSON text column already present in production)
# under the "theme" key — no schema change required. Branding columns stay
# mirrored for other surfaces.
# ---------------------------------------------------------------------------

THEME_DEFAULTS = {
    "primary_color": "#2563eb",
    "accent_color": "#7c3aed",
    "bg_color": "#f8fafc",
    "sidebar_bg": "#0f172a",
    "font_family": "Inter",
    "logo_path": None,
    "logo_style": "contain",
    "welcome_message": "",
    "company_motto": "",
    "custom_css": "",
}

THEME_ALLOWED_FIELDS = frozenset({
    "primary_color", "accent_color", "bg_color", "sidebar_bg",
    "font_family", "logo_style", "welcome_message", "company_motto",
    "custom_css", "logo_path",
})


def _org_theme(org: Organization) -> dict:
    """Read the org theme, merging stored values over defaults."""
    import json as _json
    try:
        stored = _json.loads(org.ai_config or "{}")
    except Exception:
        stored = {}
    theme = dict(THEME_DEFAULTS)
    theme.update((stored.get("theme") or {}) if isinstance(stored, dict) else {})
    if not theme.get("logo_path"):
        theme["logo_path"] = org.logo_url or None
    return theme


def _write_org_theme(org: Organization, theme: dict) -> None:
    """Persist the theme dict into the org settings blob."""
    import json as _json
    try:
        stored = _json.loads(org.ai_config or "{}")
    except Exception:
        stored = {}
    if not isinstance(stored, dict):
        stored = {}
    stored["theme"] = theme
    org.ai_config = _json.dumps(stored)
    # Mirror onto brand columns consumed elsewhere.
    org.logo_url = theme.get("logo_path") or org.logo_url
    if theme.get("primary_color"):
        org.brand_color = theme["primary_color"]
    if theme.get("accent_color"):
        org.brand_color_secondary = theme["accent_color"]


@identity_bp.route("/<int:org_id>/theme", methods=["GET"])
@login_required
def get_org_theme(org_id: int):
    """Get the organization's theme settings."""
    org = db.session.get(Organization, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")
    return jsonify({"success": True, "data": _org_theme(org)})


@identity_bp.route("/<int:org_id>/theme", methods=["PUT"])
@login_required
def update_org_theme(org_id: int):
    """Update the organization's theme settings."""
    org = db.session.get(Organization, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")

    data = _require_json()
    theme = _org_theme(org)
    updates = {k: v for k, v in data.items() if k in THEME_ALLOWED_FIELDS}
    if not updates:
        raise BadRequest("No valid theme fields provided")
    theme.update(updates)
    _write_org_theme(org, theme)
    db.session.commit()

    return jsonify({"success": True, "data": _org_theme(org)})


@identity_bp.route("/<int:org_id>/logo", methods=["POST"])
@login_required
def upload_org_logo(org_id: int):
    """Upload an organization logo; stores it under the uploads dir."""
    import os

    org = db.session.get(Organization, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")

    if "logo" not in request.files:
        return jsonify({"success": False, "error": "No logo file provided"}), 400

    file = request.files["logo"]
    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename"}), 400

    allowed = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"}
    if file.content_type not in allowed:
        return jsonify({
            "success": False,
            "error": "File type not allowed. Use PNG, JPG, GIF, SVG, or WebP.",
        }), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"):
        ext = ".png"

    filename = f"org_{org_id}_logo_{int(datetime.utcnow().timestamp())}{ext}"
    logo_dir = uploads_dir()
    file.save(os.path.join(logo_dir, filename))
    logo_path = f"/uploads/{filename}"

    theme = _org_theme(org)
    theme["logo_path"] = logo_path
    _write_org_theme(org, theme)
    db.session.commit()

    return jsonify({"success": True, "data": {"logo_path": logo_path}}), 201