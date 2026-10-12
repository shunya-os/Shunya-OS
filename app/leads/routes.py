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
from datetime import datetime

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
    search = (request.args.get("q") or "").strip()
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
    if search:
        term = f"%{search}%"
        q = q.filter(db.or_(
            Lead.code.ilike(term),
            Lead.customer_name.ilike(term),
            Lead.phone.ilike(term),
            Lead.email.ilike(term),
        ))
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


def _serialize_lead(l) -> dict:
    """Full lead representation for the detail/edit surfaces (ZG-03 B1)."""
    return {
        "id": l.id,
        "code": l.code,
        "source": l.source or "",
        "customer_name": l.customer_name or "",
        "phone": l.phone or "",
        "email": l.email or "",
        "destination": l.destination or "",
        "pax": l.pax or "",
        "dates": l.dates or "",
        "budget": float(l.budget or 0),
        "status": l.status,
        "stage": l.stage or "",
        "assigned_to": l.assigned_to or "",
        "outcome": l.outcome or "",
        "notes": l.notes or "",
        "person_id": l.person_id,
        "created_at": l.created_at.isoformat() if l.created_at else None,
        "updated_at": l.updated_at.isoformat() if l.updated_at else None,
    }


def _scoped_lead_or_none(lead_id: int):
    """A lead only when it belongs to the caller's tenant scope (fail closed)."""
    org_id, accepted = _lead_tenant_scope()
    if not org_id or not accepted:
        return None
    return Lead.query.filter(
        Lead.id == lead_id, Lead.tenant_id.in_(accepted)
    ).first()


def _audit(lead_id: int, action: str, detail: str, tenant_id: int | None = None) -> None:
    """Best-effort activity-log entry (the state change itself is committed).

    Writes directly rather than through the legacy ``_log_activity`` helper:
    that helper stores ``g.user`` as-is, which can be a TeamMember object —
    not a string — and poisons the session on insert (found by the ZG-03 B1
    tests). The user is normalized to a string, the tenant is set explicitly
    (production's activity_logs.tenant_id is NOT NULL), and a failed audit
    rolls back so the request session stays usable.
    """
    try:
        from app.models import ActivityLog

        user = ""
        try:
            u = g.get("user")
            user = getattr(u, "email", None) or (str(u) if u else "")
        except Exception:
            user = ""
        if not user:
            user = g.get("identity_id") or session.get("identity_id") or ""

        log = ActivityLog(lead_id=lead_id, tenant_id=tenant_id,
                          action=action, detail=(detail or "")[:500],
                          user=str(user)[:120])
        db.session.add(log)
        db.session.commit()
    except Exception:
        logger.exception("lead audit log failed (lead_id=%s action=%s)",
                         lead_id, action)
        try:
            db.session.rollback()
        except Exception:
            pass


_EDITABLE_FIELDS = (
    "customer_name", "phone", "email", "destination", "pax", "dates",
    "budget", "notes", "assigned_to", "source",
)

# Statuses reachable through the general transition route. "won" and "lost"
# are deliberately excluded: they have canonical transition routes with
# conversion / reason semantics (/api/v1/crm/leads/<id>/won|lost).
_GENERAL_STATUSES = ("new", "contacted", "qualified", "proposal", "negotiation", "on_hold")


@leads_bp.route("/<int:lead_id>", methods=["GET"])
@require_permission("rel.view")
def get_lead(lead_id: int):
    """Full lead detail, tenant-scoped (ZG-03 B1)."""
    lead = _scoped_lead_or_none(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    return jsonify({"lead": _serialize_lead(lead)})


@leads_bp.route("/<int:lead_id>", methods=["PATCH"])
@require_permission("rel.edit")
def update_lead(lead_id: int):
    """Edit lead details (whitelisted fields), tenant-scoped + audited."""
    data = request.json or {}
    lead = _scoped_lead_or_none(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    changes = {}
    for field in _EDITABLE_FIELDS:
        if field not in data:
            continue
        value = data.get(field)
        if field == "budget":
            try:
                value = float(value or 0)
            except (TypeError, ValueError):
                return jsonify({"error": "budget must be a number"}), 400
            if value < 0:
                return jsonify({"error": "budget must not be negative"}), 400
        else:
            value = "" if value is None else str(value).strip()
            if len(value) > 500:
                return jsonify({"error": f"{field} is too long (max 500 chars)"}), 400
            if field == "customer_name" and len(value) > 200:
                return jsonify({"error": "customer_name is too long (max 200 chars)"}), 400
        if getattr(lead, field, None) != value:
            changes[field] = value

    if changes:
        for field, value in changes.items():
            setattr(lead, field, value)
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        _audit(lead.id, "updated",
               "Fields changed: " + ", ".join(sorted(changes)),
               tenant_id=lead.tenant_id)
    return jsonify({"success": True, "lead": _serialize_lead(lead),
                    "changed": sorted(changes)})


@leads_bp.route("/<int:lead_id>/status", methods=["POST"])
@require_permission("rel.edit")
def update_lead_status(lead_id: int):
    """Move a lead through the general statuses, tenant-scoped + audited.

    'won' and 'lost' must go through their canonical transition routes —
    they carry conversion and reason semantics that a bare status write
    would bypass.
    """
    data = request.json or {}
    new_status = str(data.get("status") or "").strip().lower()
    lead = _scoped_lead_or_none(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    if new_status in ("won", "lost"):
        return jsonify({
            "error": (f"'{new_status}' has a canonical transition route; "
                      f"use POST /api/v1/crm/leads/{lead_id}/{new_status}"),
            "code": "use_transition_route",
        }), 400
    if new_status not in _GENERAL_STATUSES:
        return jsonify({
            "error": f"status must be one of {list(_GENERAL_STATUSES)}",
        }), 400

    previous = lead.status
    if previous == new_status:
        return jsonify({"success": True, "lead_id": lead.id,
                        "status": new_status, "unchanged": True})
    lead.status = new_status
    lead.stage = new_status
    lead.updated_at = datetime.utcnow()
    db.session.commit()
    _audit(lead.id, "status_changed", f"{previous} → {new_status}",
           tenant_id=lead.tenant_id)
    return jsonify({"success": True, "lead_id": lead.id,
                    "status": new_status, "previous": previous})


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
