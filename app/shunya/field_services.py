"""Shunya Field Services Module — Work Orders, Scheduling, Subcontractors.

For construction, maintenance, field service, and project-based businesses.
"""
from datetime import datetime
from typing import Any, Dict, List

from app import db
from app.models import Entity, EntityDefinition, ActivityLog

# ---------------------------------------------------------------------------
# Field Services Entity Type Definitions (seeded to EntityDefinition)
# ---------------------------------------------------------------------------

FS_ENTITY_TYPES = {
    "work_order": {
        "label": "Work Order",
        "icon": "🔧",
        "schema": [
            {"name": "title", "label": "Title", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "customer_name", "label": "Customer", "type": "text", "required": True},
            {"name": "customer_phone", "label": "Customer Phone", "type": "text"},
            {"name": "customer_address", "label": "Service Address", "type": "textarea"},
            {"name": "technician", "label": "Assigned Technician", "type": "text"},
            {"name": "scheduled_date", "label": "Scheduled Date", "type": "date"},
            {"name": "completed_date", "label": "Completed Date", "type": "date"},
            {"name": "estimated_hours", "label": "Est. Hours", "type": "number"},
            {"name": "actual_hours", "label": "Actual Hours", "type": "number"},
            {"name": "parts_used", "label": "Parts Used", "type": "json"},
            {"name": "total_charge", "label": "Total Charge", "type": "number"},
            {"name": "customer_signature", "label": "Customer Sign-off", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["pending", "scheduled", "in_progress", "completed", "cancelled"],
        "layout": "kanban",
        "searchable_fields": ["title", "customer_name", "technician", "description"],
    },
    "subcontractor": {
        "label": "Subcontractor",
        "icon": "👷",
        "schema": [
            {"name": "company_name", "label": "Company", "type": "text", "required": True},
            {"name": "contact_person", "label": "Contact", "type": "text"},
            {"name": "phone", "label": "Phone", "type": "text"},
            {"name": "email", "label": "Email", "type": "text"},
            {"name": "specialty", "label": "Specialty", "type": "select", "options": ["electrical", "plumbing", "carpentry", "painting", "hvac", "general", "roofing", "landscaping"]},
            {"name": "license_number", "label": "License #", "type": "text"},
            {"name": "insurance_expiry", "label": "Insurance Expiry", "type": "date"},
            {"name": "rating", "label": "Rating", "type": "number"},
            {"name": "contract_amount", "label": "Contract Amount", "type": "number"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "on_project", "inactive", "suspended"],
        "layout": "table",
        "searchable_fields": ["company_name", "contact_person", "specialty"],
    },
    "estimate": {
        "label": "Estimate",
        "icon": "📐",
        "schema": [
            {"name": "project_name", "label": "Project", "type": "text", "required": True},
            {"name": "customer_name", "label": "Customer", "type": "text", "required": True},
            {"name": "items", "label": "Line Items", "type": "json"},
            {"name": "subtotal", "label": "Subtotal", "type": "number"},
            {"name": "tax", "label": "Tax", "type": "number"},
            {"name": "total", "label": "Total", "type": "number"},
            {"name": "valid_until", "label": "Valid Until", "type": "date"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["draft", "sent", "accepted", "rejected", "expired"],
        "layout": "table",
        "searchable_fields": ["project_name", "customer_name"],
    },
}


# ---------------------------------------------------------------------------
# Field Services Dashboard — Data Aggregation
# ---------------------------------------------------------------------------

class FSDashboard:
    """Aggregates Field Services data for the dashboard views."""

    @staticmethod
    def get_overview(tenant_id: int) -> Dict[str, Any]:
        """Get all field services metrics for the overview dashboard."""
        wo_def = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type="work_order"
        ).first()
        sub_def = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type="subcontractor"
        ).first()
        est_def = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type="estimate"
        ).first()

        work_orders = []
        if wo_def:
            work_orders = db.session.query(Entity).filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == wo_def.id,
                Entity.is_archived == False,
            ).all()

        subcontractors = []
        if sub_def:
            subcontractors = db.session.query(Entity).filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == sub_def.id,
                Entity.is_archived == False,
            ).all()

        estimates = []
        if est_def:
            estimates = db.session.query(Entity).filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == est_def.id,
                Entity.is_archived == False,
            ).all()

        scheduled = [wo for wo in work_orders if wo.status == "scheduled"]
        in_progress = [wo for wo in work_orders if wo.status == "in_progress"]
        completed = [wo for wo in work_orders if wo.status == "completed"]

        wo_statuses = {}
        for wo in work_orders:
            wo_statuses[wo.status] = wo_statuses.get(wo.status, 0) + 1

        total_revenue = sum(float(wo.data.get("total_charge", 0)) for wo in completed)
        active_subs = [s for s in subcontractors if s.status in ("active", "on_project")]

        return {
            "work_orders": work_orders,
            "subcontractors": subcontractors,
            "estimates": estimates,
            "scheduled": scheduled,
            "in_progress": in_progress,
            "completed": completed,
            "wo_statuses": wo_statuses,
            "total_revenue": total_revenue,
            "active_subs": active_subs,
            "wo_def": wo_def,
            "sub_def": sub_def,
            "est_def": est_def,
        }

    @staticmethod
    def get_recent(tenant_id: int, entity_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent entities of a given type."""
        edef = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=entity_type
        ).first()
        if not edef:
            return []
        entities = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == edef.id,
            Entity.is_archived == False,
        ).order_by(Entity.created_at.desc()).limit(limit).all()
        return [{
            "id": e.id,
            "code": e.code,
            "display_name": e.display_name,
            "status": e.status,
            "data": e.data,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        } for e in entities]


# ---------------------------------------------------------------------------
# Ensure Field Services entity types exist for a tenant
# ---------------------------------------------------------------------------

def _ensure_fs_types(tenant_id: int):
    """Ensure field services entity types exist."""
    for etype, config in FS_ENTITY_TYPES.items():
        existing = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=etype
        ).first()
        if existing:
            continue
        definition = EntityDefinition(
            tenant_id=tenant_id,
            type=etype,
            label=config["label"],
            label_plural=f"{config['label']}s",
            icon=config["icon"],
            schema=config["schema"],
            statuses=config["statuses"],
            layout=config["layout"],
            searchable_fields=config["searchable_fields"],
            primary_field=config["schema"][0]["name"] if config["schema"] else "name",
        )
        db.session.add(definition)
    db.session.commit()