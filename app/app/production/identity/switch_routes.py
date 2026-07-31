"""SHUNYA — Organization Switching API (Milestone X, D1.5).

Provides endpoints and middleware for switching between organizations.
Stores the current organization in the user's session.
"""

from flask import request, jsonify, session, g
from werkzeug.exceptions import NotFound

from app import db
from app.auth_routes import login_required
from app.tenant import Tenant
from app.production.identity import identity_bp


@identity_bp.route("/switch/<int:org_id>", methods=["POST"])
@login_required
def switch_organization(org_id: int):
    """Switch the current user's active organization.

    Stores org_id in the session for subsequent requests.
    Middleware in _set_current_org enforces org scoping.
    """
    org = db.session.get(Tenant, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")

    session["current_org_id"] = org.id

    return jsonify({
        "success": True,
        "data": {
            "id": org.id,
            "company_name": org.company_name,
            "slug": org.slug,
        },
    })


@identity_bp.route("/current", methods=["GET"])
@login_required
def get_current_organization():
    """Get the user's current active organization from session."""
    org_id = session.get("current_org_id")
    if not org_id:
        return jsonify({
            "success": True,
            "data": None,
        })

    org = db.session.get(Tenant, org_id)
    if not org or not org.is_active:
        session.pop("current_org_id", None)
        return jsonify({
            "success": True,
            "data": None,
        })

    return jsonify({
        "success": True,
        "data": {
            "id": org.id,
            "company_name": org.company_name,
            "slug": org.slug,
            "business_type": org.business_type,
        },
    })


def set_current_org_middleware():
    """Middleware to attach current_org to g for request-scoped access.

    Call this in app.before_request or in route decorators.
    Sets g.current_org from session['current_org_id'].
    """
    org_id = session.get("current_org_id")
    if org_id:
        org = db.session.get(Tenant, org_id)
        if org and org.is_active:
            g.current_org = org
            return
    g.current_org = None