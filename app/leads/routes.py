"""Legacy leads API — tenant-scoped through the canonical resolver.

ZG-03 containment (REG-RC-001): both endpoints previously operated with NO
tenant filter — any authenticated identity could list every tenant's leads,
and creation bypassed the canonical service. Both now resolve the caller's
tenant scope via ``app.authz.workspace_context.resolve_tenant_scope`` — the
ONE canonical boundary that returns the authorized organization plus the
recorded legacy-bridge ids (``organizations.legacy_tenant_id``). Reads accept
the union so the founder's data (legacy tenant 89) stays visible through the
canonical organization (7); writes move toward the canonical id. Requests
without an authorized organization context fail closed.
"""
import logging

from flask import Blueprint, g, jsonify, request, session

from app import db
from app.authz.decorators import require_permission
from app.models import Lead

logger = logging.getLogger(__name__)

leads_bp = Blueprint("leads", __name__, url_prefix="/api/v1/leads")


def _lead_tenant_scope() -> tuple[int | None, list[int]]:
    """(organization_id, accepted_tenant_ids) for this request, fail closed."""
    from app.authz.workspace_context import resolve_tenant_scope

    identity_id = g.get("identity_id") or session.get("identity_id", "")
    requested = g.get("current_org_id") or session.get("current_org_id")
    try:
        return resolve_tenant_scope(identity_id, requested)
    except Exception:
        logger.exception("lead tenant scope resolution failed")
        return None, []


@leads_bp.route("/", methods=["GET"])
@require_permission("rel.view")
def list_leads():
    """List leads for the caller's organization (canonical id + legacy bridge)."""
    status = request.args.get("status")
    limit = min(request.args.get("limit", 100, type=int), 200)
    org_id, accepted = _lead_tenant_scope()
    if not org_id or not accepted:
        return jsonify({"error": "No organization context"}), 403
    q = (
        Lead.query
        .filter(Lead.tenant_id.in_(accepted))
        .order_by(Lead.created_at.desc())
    )
    if status:
        q = q.filter(Lead.status == status)
    leads = q.limit(limit).all()
    return jsonify({
        "leads": [{
            "id": l.id,
            "code": l.code,
            "source": l.source,
            "customer_name": l.customer_name or "",
            "phone": l.phone or "",
            "email": l.email or "",
            "destination": l.destination or "",
            "budget": float(l.budget or 0),
            "status": l.status,
            "stage": l.stage or "",
            "assigned_to": l.assigned_to or "",
            "outcome": l.outcome or "",
            "notes": (l.notes or "")[:200],
            "created_at": l.created_at.isoformat() if l.created_at else None,
        } for l in leads],
        "total": len(leads),
    })


@leads_bp.route("/", methods=["POST"])
@require_permission("rel.create")
def create_lead():
    """Create a lead through the canonical CRM service (tenant-bound).

    The tenant is resolved server-side (never from the request body) and the
    write moves toward the canonical organization id. The canonical service
    also provisions the tenant's 'lead' entity definition on first use.
    """
    data = request.json or {}
    org_id, _accepted = _lead_tenant_scope()
    if not org_id:
        return jsonify({"error": "No organization context"}), 403

    from app.crm.service import create_lead_with_identity

    lead = create_lead_with_identity(
        tenant_id=org_id,
        name=data.get("customer_name") or data.get("name") or "",
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        source=data.get("source", "direct"),
        destination=data.get("destination", ""),
        pax=str(data.get("pax", "") or ""),
        budget=float(data.get("budget", 0) or 0),
        notes=data.get("notes", ""),
        created_by=g.get("identity_id", "") or "",
    )
    return jsonify({"id": lead.id, "code": lead.code, "success": True})
