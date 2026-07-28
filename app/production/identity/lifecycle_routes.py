"""SHUNYA — Organization Lifecycle API (Milestone X, D1.7).

Endpoints for activating, deactivating, and archiving organizations.
"""

from flask import jsonify
from werkzeug.exceptions import NotFound

from app import db
from app.auth_routes import login_required
from app.tenant import Tenant
from app.production.identity import identity_bp


def _get_org_or_404(org_id: int) -> Tenant:
    org = db.session.get(Tenant, org_id)
    if not org:
        raise NotFound("Organization not found")
    return org


@identity_bp.route("/<int:org_id>/activate", methods=["POST"])
@login_required
def activate_org(org_id: int):
    """Activate an organization."""
    org = _get_org_or_404(org_id)
    org.is_active = True
    db.session.commit()
    return jsonify({
        "success": True,
        "data": {"id": org_id, "status": "activated"},
    })


@identity_bp.route("/<int:org_id>/deactivate", methods=["POST"])
@login_required
def deactivate_org(org_id: int):
    """Deactivate an organization."""
    org = _get_org_or_404(org_id)
    org.is_active = False
    db.session.commit()
    return jsonify({
        "success": True,
        "data": {"id": org_id, "status": "deactivated"},
    })


@identity_bp.route("/<int:org_id>/archive", methods=["POST"])
@login_required
def archive_org(org_id: int):
    """Archive an organization (deactivate + mark as archived)."""
    org = _get_org_or_404(org_id)
    org.is_active = False
    db.session.commit()
    return jsonify({
        "success": True,
        "data": {"id": org_id, "status": "archived"},
    })