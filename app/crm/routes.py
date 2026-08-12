"""SHUNYA CRM — Lead-to-Customer API Routes.

Connects to the canonical /api/v1/leads blueprint.
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Lead, LeadStatus
from datetime import datetime, timedelta
from app.crm.service import (
    create_lead_with_identity, assign_lead, qualify_lead_and_update,
    check_sla, create_follow_up, create_opportunity,
    convert_to_customer, mark_lost, reassign_unattended_leads,
    qualify_lead,
)

crm_bp = Blueprint("crm", __name__, url_prefix="/api/v1/crm")


@crm_bp.route("/leads", methods=["POST"])
def api_create_lead():
    """Create a lead through the canonical CRM path."""
    data = request.get_json(silent=True) or {}
    tenant_id = data.get("tenant_id", 1)
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


@crm_bp.route("/leads/<int:lead_id>/qualify", methods=["POST"])
def api_qualify_lead(lead_id: int):
    """Qualify a lead through the canonical path."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    tenant_id = request.get_json(silent=True or {}).get("tenant_id", 1)
    result = qualify_lead_and_update(lead, tenant_id)
    return jsonify({
        "success": True,
        "lead_id": lead.id,
        "qualification": result.to_dict(),
    })


@crm_bp.route("/leads/<int:lead_id>/assign", methods=["POST"])
def api_assign_lead(lead_id: int):
    """Assign a lead to an owner."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    owner = data.get("owner", "")
    tenant_id = data.get("tenant_id", 1)
    if not owner:
        return jsonify({"success": False, "error": "Owner required"}), 400
    assign_lead(lead, owner, tenant_id)
    return jsonify({"success": True, "lead_id": lead.id, "assigned_to": owner})


@crm_bp.route("/leads/<int:lead_id>/sla", methods=["GET"])
def api_lead_sla(lead_id: int):
    """Check SLA status for a lead."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    return jsonify({"success": True, "sla": check_sla(lead)})


@crm_bp.route("/leads/<int:lead_id>/follow-up", methods=["POST"])
def api_create_followup(lead_id: int):
    """Create a follow-up task for a lead."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    from dateutil import parser as dt_parser
    due = (dt_parser.parse(data.get("due_date")) if data.get("due_date")
           else datetime.utcnow() + timedelta(days=1))
    task = create_follow_up(
        lead=lead, title=data.get("title", "Follow-up"),
        due_date=due, assigned_to=data.get("assigned_to", lead.assigned_to or ""),
        tenant_id=data.get("tenant_id", 1),
    )
    return jsonify({"success": True, "task": {"id": task.id, "title": task.title}})


@crm_bp.route("/leads/<int:lead_id>/opportunity", methods=["POST"])
def api_create_opportunity(lead_id: int):
    """Create an opportunity/proposal from a qualified lead."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    tenant_id = data.get("tenant_id", 1)
    proposal = create_opportunity(lead, tenant_id, title=data.get("title", ""))
    return jsonify({
        "success": True,
        "proposal": {"id": proposal.id, "title": proposal.title, "status": proposal.status},
    })


@crm_bp.route("/leads/<int:lead_id>/won", methods=["POST"])
def api_lead_won(lead_id: int):
    """Convert a won lead to customer."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    customer = convert_to_customer(lead, data.get("tenant_id", 1))
    return jsonify({
        "success": True,
        "customer": {"id": customer.id, "name": customer.name},
    })


@crm_bp.route("/leads/<int:lead_id>/lost", methods=["POST"])
def api_lead_lost(lead_id: int):
    """Mark a lead as lost."""
    lead = db.session.get(Lead, lead_id)
    if not lead:
        return jsonify({"success": False, "error": "Lead not found"}), 404
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "No reason provided")
    mark_lost(lead, reason, data.get("tenant_id", 1))
    return jsonify({"success": True, "lead_id": lead.id, "outcome": reason})


@crm_bp.route("/leads/reassign", methods=["POST"])
def api_reassign_leads():
    """Reassign unattended leads past SLA."""
    data = request.get_json(silent=True) or {}
    new_owner = data.get("new_owner", "")
    if not new_owner:
        return jsonify({"success": False, "error": "new_owner required"}), 400
    reassigned = reassign_unattended_leads(data.get("tenant_id", 1), new_owner)
    return jsonify({
        "success": True,
        "reassigned_count": len(reassigned),
        "reassigned_lead_ids": [l.id for l in reassigned],
    })