"""SHUNYA CRM — Lead-to-Customer API Routes.

Connects to the canonical /api/v1/leads blueprint.
"""
import logging

from flask import Blueprint, g, jsonify, request, session

from app import db
from app.models import Lead, LeadStatus
from datetime import datetime, timedelta, timezone
from app.crm.service import (
    create_lead_with_identity, assign_lead, qualify_lead_and_update,
    check_sla, create_follow_up, create_opportunity,
    convert_to_customer, mark_lost, reassign_unattended_leads,
    qualify_lead,
)
from app.authz.decorators import require_permission

logger = logging.getLogger(__name__)

crm_bp = Blueprint("crm", __name__, url_prefix="/api/v1/crm")


def _crm_tenant_scope() -> tuple[int | None, list[int]]:
    """(organization_id, accepted_tenant_ids) for this request, fail closed.

    Canonical resolver: the authorized organization plus the recorded legacy
    bridge (``organizations.legacy_tenant_id``) so the founder's data (legacy
    tenant 89) stays visible through the canonical organization. NEVER trusts
    request-body tenant_id — prevents cross-tenant reads and writes. A missing
    context returns ``(None, [])`` and callers must deny.
    """
    from app.authz.workspace_context import resolve_tenant_scope

    identity_id = g.get("identity_id") or session.get("identity_id", "")
    requested = g.get("current_org_id") or session.get("current_org_id")
    try:
        return resolve_tenant_scope(identity_id, requested)
    except Exception:
        logger.exception("crm tenant scope resolution failed")
        return None, []


def _scoped_lead(lead_id: int):
    """A lead only when it belongs to the caller's tenant scope (fail closed)."""
    org_id, accepted = _crm_tenant_scope()
    if not org_id or not accepted:
        return None
    return Lead.query.filter(
        Lead.id == lead_id, Lead.tenant_id.in_(accepted)
    ).first()


@crm_bp.route("/leads", methods=["POST"])
@require_permission("rel.create")
def api_create_lead():
    """Create a lead through the canonical CRM path."""
    data = request.get_json(silent=True) or {}
    tenant_id, _accepted = _crm_tenant_scope()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 403
    try:
        lead = create_lead_with_identity(
            tenant_id=tenant_id,
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            source=data.get("source", "api"),
            destination=data.get("destination", ""),
            pax=data.get("pax", ""),
            budget=float(data.get("budget", 0)),
            notes=data.get("notes", ""),
            assigned_to=data.get("assigned_to", ""),
            created_by=data.get("created_by", ""),
        )
        return jsonify({"success": True, "lead": {"id": lead.id, "code": lead.code}}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@crm_bp.route("/leads", methods=["GET"])
@require_permission("rel.view")
def api_list_leads():
    """List leads for the current organization (canonical id + legacy bridge)."""
    tenant_id, accepted = _crm_tenant_scope()
    if not tenant_id or not accepted:
        return jsonify({"success": False, "error": "No organization context"}), 403
    status = request.args.get("status")
    limit = min(int(request.args.get("limit", 50)), 200)
    try:
        q = Lead.query.filter(Lead.tenant_id.in_(accepted))
        if status:
            q = q.filter_by(stage=status)
        leads = q.order_by(Lead.created_at.desc()).limit(limit).all()
        return jsonify({
            "success": True,
            "data": [{
                "id": l.id, "code": l.code, "customer_name": l.customer_name,
                "phone": l.phone, "email": l.email, "stage": l.stage or l.status,
                "source": l.source, "assigned_to": l.assigned_to,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "destination": l.destination,
            } for l in leads],
            "total": len(leads),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@crm_bp.route("/leads/<int:lead_id>/qualify", methods=["POST"])
@require_permission("rel.edit")
def api_qualify_lead(lead_id: int):
    """Qualify a lead through the canonical path."""
    lead = _scoped_lead(lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    tenant_id, _accepted = _crm_tenant_scope()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 403
    result = qualify_lead_and_update(lead, tenant_id)
    return jsonify({
        "success": True,
        "lead_id": lead.id,
        "qualification": result.to_dict(),
    })


@crm_bp.route("/leads/<int:lead_id>/assign", methods=["POST"])
@require_permission("rel.edit")
def api_assign_lead(lead_id: int):
    """Assign a lead to an owner."""
    lead = _scoped_lead(lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    owner = data.get("owner", "")
    tenant_id, _accepted = _crm_tenant_scope()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 403
    if not owner:
        return jsonify({"success": False, "error": "Owner required"}), 400
    assign_lead(lead, owner, tenant_id)
    return jsonify({"success": True, "lead_id": lead.id, "assigned_to": owner})


@crm_bp.route("/leads/<int:lead_id>/sla", methods=["GET"])
@require_permission("rel.view")
def api_lead_sla(lead_id: int):
    """Check SLA status for a lead."""
    lead = _scoped_lead(lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    return jsonify({"success": True, "sla": check_sla(lead)})


@crm_bp.route("/leads/<int:lead_id>/follow-up", methods=["POST"])
@require_permission("rel.edit")
def api_create_followup(lead_id: int):
    """Create a follow-up task for a lead."""
    lead = _scoped_lead(lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    from dateutil import parser as dt_parser
    due = (dt_parser.parse(data.get("due_date")) if data.get("due_date")
           else datetime.now(timezone.utc) + timedelta(days=1))
    tenant_id, _accepted = _crm_tenant_scope()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 403
    task = create_follow_up(
        lead=lead, title=data.get("title", "Follow-up"),
        due_date=due, assigned_to=data.get("assigned_to", lead.assigned_to or ""),
        tenant_id=tenant_id,
    )
    return jsonify({"success": True, "task": {"id": task.id, "title": task.title}})


@crm_bp.route("/leads/<int:lead_id>/opportunity", methods=["POST"])
@require_permission("rel.edit")
def api_create_opportunity(lead_id: int):
    """Create an opportunity/proposal from a qualified lead."""
    lead = _scoped_lead(lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    tenant_id, _accepted = _crm_tenant_scope()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 403
    proposal = create_opportunity(lead, tenant_id, title=data.get("title", ""))
    return jsonify({
        "success": True,
        "proposal": {"id": proposal.id, "title": proposal.title, "status": proposal.status},
    })


@crm_bp.route("/leads/<int:lead_id>/won", methods=["POST"])
@require_permission("proposal.approve")
def api_lead_won(lead_id: int):
    """Mark a lead WON and convert it to customer.

    This is the sanctioned 'won' transition: it marks the lead won (status +
    stage + timeline) and then converts — the audit gate (convert_to_customer
    refuses arbitrary new/in-progress leads) is preserved for all other paths.
    """
    lead = _scoped_lead(lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    if lead.status == LeadStatus.CANCELLED.value:
        return jsonify({"success": False, "error": "A cancelled lead cannot be marked won"}), 400
    tenant_id, _accepted = _crm_tenant_scope()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 403
    # Mark won first (the gate then accepts the conversion)
    from app.crm.service import mark_lead_won
    mark_lead_won(lead, tenant_id)
    data = request.get_json(silent=True) or {}
    customer = convert_to_customer(lead, tenant_id)
    if customer is None:
        return jsonify({
            "success": False,
            "error": (
                f"Lead {lead.code} cannot be converted: status must be "
                f"won/qualified/converted (current status={lead.status}, "
                f"stage={lead.stage})."
            ),
        }), 400
    return jsonify({
        "success": True,
        "customer": {"id": customer.id, "name": customer.name},
    })


@crm_bp.route("/leads/<int:lead_id>/lost", methods=["POST"])
@require_permission("rel.edit")
def api_lead_lost(lead_id: int):
    """Mark a lead as lost."""
    lead = _scoped_lead(lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "No reason provided")
    tenant_id, _accepted = _crm_tenant_scope()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 403
    mark_lost(lead, reason, tenant_id)
    return jsonify({"success": True, "lead_id": lead.id, "outcome": reason})


@crm_bp.route("/leads/reassign", methods=["POST"])
@require_permission("rel.edit")
def api_reassign_leads():
    """Reassign unattended leads past SLA."""
    data = request.get_json(silent=True) or {}
    new_owner = data.get("new_owner", "")
    if not new_owner:
        return jsonify({"success": False, "error": "new_owner required"}), 400
    tenant_id, _accepted = _crm_tenant_scope()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 403
    reassigned = reassign_unattended_leads(tenant_id, new_owner)
    return jsonify({
        "success": True,
        "reassigned_count": len(reassigned),
        "reassigned_lead_ids": [l.id for l in reassigned],
    })
