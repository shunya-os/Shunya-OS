"""SHUNYA CRM — Lead-to-Customer API Routes.

Connects to the canonical /api/v1/leads blueprint.
"""
from flask import Blueprint, request, jsonify, session
from app import db
from app.models import Lead, LeadStatus
from datetime import datetime, timedelta
from app.crm.service import (
    create_lead_with_identity, assign_lead, qualify_lead_and_update,
    check_sla, create_follow_up, create_opportunity,
    convert_to_customer, mark_lost, reassign_unattended_leads,
    qualify_lead,
)
from app.authz.decorators import require_permission

crm_bp = Blueprint("crm", __name__, url_prefix="/api/v1/crm")


def _resolve_tenant_from_session():
    """Resolve the canonical tenant (organization) id from the session.
    NEVER trusts request-body tenant_id — prevents cross-tenant writes.
    """
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    if org_id:
        return org_id
    return session.get("tenant_id") or 1


@crm_bp.route("/leads", methods=["POST"])
@require_permission("rel.create")
def api_create_lead():
    """Create a lead through the canonical CRM path."""
    data = request.get_json(silent=True) or {}
    tenant_id = _resolve_tenant_from_session() or 1
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
    """List leads for the current tenant/organization."""
    tenant_id = _resolve_tenant_from_session() or 1
    status = request.args.get("status")
    limit = min(int(request.args.get("limit", 50)), 200)
    try:
        q = Lead.query.filter_by(tenant_id=tenant_id)
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
def api_qualify_lead(lead_id: int):
    """Qualify a lead through the canonical path."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    tenant_id = _resolve_tenant_from_session()
    result = qualify_lead_and_update(lead, tenant_id)
    return jsonify({"success": True, "lead_id": lead.id, "qualification": result.to_dict()})


@crm_bp.route("/leads/<int:lead_id>/assign", methods=["POST"])
@require_permission("rel.edit")
def api_assign_lead(lead_id: int):
    """Assign a lead to a team member."""
    data = request.get_json(silent=True) or {}
    tenant_id = _resolve_tenant_from_session()
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    result = assign_lead(lead, tenant_id=tenant_id, **data)
    return jsonify({"success": True, "lead_id": lead.id, "assigned_to": result.get("assigned_to")})


@crm_bp.route("/leads/<int:lead_id>/sla", methods=["GET"])
def api_check_sla(lead_id: int):
    """Check SLA compliance for a lead."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    result = check_sla(lead)
    return jsonify({"success": True, "lead_id": lead.id, "sla": result})


@crm_bp.route("/leads/<int:lead_id>/follow-up", methods=["POST"])
@require_permission("rel.create")
def api_create_follow_up(lead_id: int):
    """Create a follow-up task for a lead."""
    data = request.get_json(silent=True) or {}
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    result = create_follow_up(lead, **data)
    return jsonify({"success": True, "follow_up": result}), 201


@crm_bp.route("/leads/<int:lead_id>/opportunity", methods=["POST"])
@require_permission("rel.create")
def api_create_opportunity(lead_id: int):
    """Convert a lead to an opportunity."""
    data = request.get_json(silent=True) or {}
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    result = create_opportunity(lead, **data)
    return jsonify({"success": True, "opportunity": result}), 201


@crm_bp.route("/leads/<int:lead_id>/won", methods=["POST"])
@require_permission("rel.create")
def api_lead_won(lead_id: int):
    """Mark a lead as won (converted to customer)."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    result = convert_to_customer(lead)
    return jsonify({"success": True, "customer": result})


@crm_bp.route("/leads/<int:lead_id>/lost", methods=["POST"])
@require_permission("rel.edit")
def api_lead_lost(lead_id: int):
    """Mark a lead as lost."""
    data = request.get_json(silent=True) or {}
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    result = mark_lost(lead, reason=data.get("reason", ""))
    return jsonify({"success": True, "lead_id": lead.id, "status": result})


@crm_bp.route("/leads/reassign", methods=["POST"])
@require_permission("rel.edit")
def api_reassign_leads():
    """Reassign unattended leads based on SLA rules."""
    tenant_id = _resolve_tenant_from_session()
    result = reassign_unattended_leads(tenant_id=tenant_id)
    return jsonify({"success": True, "reassigned": result})
