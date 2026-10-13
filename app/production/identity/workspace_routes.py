"""SHUNYA — Workspace CRUD API (Milestone X, D1.2).

RESTful endpoints for managing workspaces within organizations.
"""

import re

from flask import request, jsonify, session
from werkzeug.exceptions import NotFound, BadRequest, Forbidden, Unauthorized

from app import db
from app.auth_routes import login_required
from app.models import Organization
from app.production.identity import identity_bp
from app.production.identity.workspace_model import Workspace


def _generate_slug(name: str) -> str:
    """Generate a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:120] or "workspace"


def _caller_identity_id() -> str:
    """Resolve the canonical identity id from the authenticated session.

    Prefers the canonical ``identity_id`` session key (set at login); falls
    back to the TeamMember's canonical identity; last resort the legacy
    user id. Never guesses.
    """
    sid = session.get("identity_id")
    if sid:
        return str(sid)
    uid = session.get("user_id")
    if not uid:
        raise Unauthorized("Authentication required")
    from app.auth import TeamMember
    member = db.session.get(TeamMember, uid)
    if member and getattr(member, "identity_id", None):
        return member.identity_id
    return str(uid)


def _require_membership(org_id: int) -> str:
    """Verify the caller is an ACTIVE member of the target organization.

    ZG-03 B4: previously every /orgs/<org_id>/workspaces route only checked
    ``login_required`` — ANY authenticated user could list, create, update or
    soft-delete workspaces inside ANY organization (cross-tenant access).
    Now the canonical OrgMember membership is enforced; non-members are
    denied (403) even though the org exists.
    """
    from app.models import OrgMember
    identity_id = _caller_identity_id()
    om = OrgMember.query.filter_by(
        organization_id=org_id,
        identity_id=identity_id,
        is_active=True,
    ).first()
    if om is None:
        raise Forbidden("You are not a member of this organization")
    return identity_id


def _accepted_tenant_ids(identity_id: str, org_id: int) -> list[int]:
    """Canonical tenant scoping for this org (org id + legacy bridge).

    Mirrors ``authz.workspace_context.resolve_tenant_scope``: the D1.2 legacy
    Workspace rows may legally carry either the canonical organization id or
    the organization's recorded ``legacy_tenant_id``; reads accept the union
    so a founder org with unfinished tenancy convergence sees its own rows on
    both sides of the split.
    """
    from app.authz.workspace_context import resolve_tenant_scope
    _org_id, accepted = resolve_tenant_scope(identity_id, org_id)
    return accepted or [org_id]


def _ensure_unique_slug(org_id: int, base_slug: str) -> str:
    """Append counter if slug already exists in this org."""
    slug = base_slug
    counter = 1
    while Workspace.query.filter_by(tenant_id=org_id, slug=slug).first() is not None:
        suffix = str(counter)
        max_base = 120 - len(suffix) - 1
        slug = f"{base_slug[:max_base]}-{suffix}"
        counter += 1
    return slug


def _get_org_or_404(org_id: int) -> Organization:
    """Get an active org or 404."""
    org = db.session.get(Organization, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")
    return org


def _require_json() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


# ---------------------------------------------------------------------------
# Routes — all at /api/v1/orgs/<org_id>/workspaces
# ---------------------------------------------------------------------------


@identity_bp.route("/<int:org_id>/workspaces", methods=["GET"])
@login_required
def list_workspaces(org_id: int):
    """List all workspaces in an organization (membership-gated, B4)."""
    _get_org_or_404(org_id)
    identity_id = _require_membership(org_id)
    accepted = _accepted_tenant_ids(identity_id, org_id)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Workspace.query.filter(
        Workspace.tenant_id.in_(accepted),
        Workspace.is_active.is_(True),
    )
    pagination = query.order_by(Workspace.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "success": True,
        "data": [w.to_dict() for w in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


@identity_bp.route("/<int:org_id>/workspaces", methods=["POST"])
@login_required
def create_workspace(org_id: int):
    """Create a new workspace in an organization (membership-gated, B4)."""
    _get_org_or_404(org_id)
    _require_membership(org_id)
    data = _require_json()

    name = data.get("name", "").strip()
    if not name:
        raise BadRequest("'name' is required")

    slug = _ensure_unique_slug(org_id, _generate_slug(name))

    ws = Workspace(
        tenant_id=org_id,
        name=name,
        slug=slug,
        description=data.get("description", "").strip(),
    )
    if "settings" in data and isinstance(data["settings"], dict):
        import json
        ws.settings = json.dumps(data["settings"])
    db.session.add(ws)
    db.session.commit()

    return jsonify({"success": True, "data": ws.to_dict()}), 201


@identity_bp.route("/<int:org_id>/workspaces/<int:ws_id>", methods=["GET"])
@login_required
def get_workspace(org_id: int, ws_id: int):
    """Get a single workspace by ID within an org (membership-gated, B4)."""
    _get_org_or_404(org_id)
    identity_id = _require_membership(org_id)
    accepted = _accepted_tenant_ids(identity_id, org_id)
    ws = db.session.get(Workspace, ws_id)
    if not ws or ws.tenant_id not in accepted or not ws.is_active:
        raise NotFound("Workspace not found")

    return jsonify({"success": True, "data": ws.to_dict()})


@identity_bp.route("/<int:org_id>/workspaces/<int:ws_id>", methods=["PUT"])
@login_required
def update_workspace(org_id: int, ws_id: int):
    """Update a workspace (membership-gated, B4)."""
    _get_org_or_404(org_id)
    identity_id = _require_membership(org_id)
    accepted = _accepted_tenant_ids(identity_id, org_id)
    ws = db.session.get(Workspace, ws_id)
    if not ws or ws.tenant_id not in accepted:
        raise NotFound("Workspace not found")

    data = _require_json()

    if "name" in data and data["name"].strip():
        ws.name = data["name"].strip()
    if "description" in data:
        ws.description = data["description"].strip()
    if "settings" in data and isinstance(data["settings"], dict):
        import json
        ws.settings = json.dumps(data["settings"])
    if "is_active" in data:
        ws.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify({"success": True, "data": ws.to_dict()})


@identity_bp.route("/<int:org_id>/workspaces/<int:ws_id>", methods=["DELETE"])
@login_required
def delete_workspace(org_id: int, ws_id: int):
    """Soft-delete a workspace (membership-gated, B4)."""
    _get_org_or_404(org_id)
    identity_id = _require_membership(org_id)
    accepted = _accepted_tenant_ids(identity_id, org_id)
    ws = db.session.get(Workspace, ws_id)
    if not ws or ws.tenant_id not in accepted:
        raise NotFound("Workspace not found")

    ws.is_active = False
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {"id": ws_id, "status": "deactivated"},
    })