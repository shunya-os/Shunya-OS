"""Shunya Legal & Compliance Module — Contracts, Documents, Compliance.

Every business needs legal management: contracts, document templates,
compliance tracking, and e-signatures.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from app import db
from app.models import Entity, EntityDefinition, ActivityLog

LEGAL_ENTITY_TYPES = {
    "contract": {
        "label": "Contract",
        "icon": "📜",
        "schema": [
            {"name": "title", "label": "Title", "type": "text", "required": True},
            {"name": "contract_type", "label": "Type", "type": "select", "options": ["employment", "vendor", "client", "nda", "lease", "service", "partnership", "other"]},
            {"name": "party_a", "label": "Party A (Your Company)", "type": "text", "required": True},
            {"name": "party_b", "label": "Party B", "type": "text", "required": True},
            {"name": "start_date", "label": "Start Date", "type": "date"},
            {"name": "end_date", "label": "End Date", "type": "date"},
            {"name": "value", "label": "Contract Value", "type": "number"},
            {"name": "auto_renew", "label": "Auto Renew", "type": "boolean"},
            {"name": "renewal_alert_days", "label": "Renewal Alert (days)", "type": "number"},
            {"name": "file_url", "label": "Document URL", "type": "file"},
            {"name": "signed_by", "label": "Signed By", "type": "text"},
            {"name": "signed_date", "label": "Signed Date", "type": "date"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["draft", "pending_signature", "active", "expiring_soon", "expired", "terminated"],
        "layout": "table",
        "searchable_fields": ["title", "party_a", "party_b", "contract_type"],
    },
    "document_template": {
        "label": "Document Template",
        "icon": "📄",
        "schema": [
            {"name": "name", "label": "Template Name", "type": "text", "required": True},
            {"name": "category", "label": "Category", "type": "select", "options": ["agreement", "proposal", "report", "policy", "form", "letter"]},
            {"name": "content", "label": "Template Content", "type": "textarea"},
            {"name": "variables", "label": "Variables (comma-separated)", "type": "text"},
            {"name": "version", "label": "Version", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "draft", "archived"],
        "layout": "table",
        "searchable_fields": ["name", "category"],
    },
    "compliance_item": {
        "label": "Compliance Item",
        "icon": "✅",
        "schema": [
            {"name": "regulation", "label": "Regulation/Standard", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "category", "label": "Category", "type": "select", "options": ["iso", "gdpr", "safety", "environmental", "labor", "tax", "industry", "other"]},
            {"name": "due_date", "label": "Due Date", "type": "date"},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
            {"name": "certification_url", "label": "Certification URL", "type": "file"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["pending", "in_progress", "compliant", "non_compliant", "overdue"],
        "layout": "table",
        "searchable_fields": ["regulation", "category", "assigned_to"],
    },
}


# ---------------------------------------------------------------------------
# Legal Dashboard — Data Aggregation
# ---------------------------------------------------------------------------

class LegalDashboard:
    """Aggregates legal & compliance data for dashboard views."""

    @staticmethod
    def _get_def(tenant_id: int, entity_type: str) -> Optional[EntityDefinition]:
        """Get entity definition for a type, or None."""
        return db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=entity_type
        ).first()

    @staticmethod
    def get_overview(tenant_id: int) -> Dict[str, Any]:
        """Get all legal & compliance metrics for the overview dashboard."""
        cont_def = LegalDashboard._get_def(tenant_id, "contract")
        tmpl_def = LegalDashboard._get_def(tenant_id, "document_template")
        comp_def = LegalDashboard._get_def(tenant_id, "compliance_item")

        contracts = []
        if cont_def:
            contracts = db.session.query(Entity).filter_by(
                tenant_id=tenant_id, definition_id=cont_def.id, is_archived=False
            ).all()

        templates = []
        if tmpl_def:
            templates = db.session.query(Entity).filter_by(
                tenant_id=tenant_id, definition_id=tmpl_def.id, is_archived=False
            ).all()

        compliance = []
        if comp_def:
            compliance = db.session.query(Entity).filter_by(
                tenant_id=tenant_id, definition_id=comp_def.id, is_archived=False
            ).all()

        active_contracts = [c for c in contracts if c.status == "active"]
        expiring_soon = [c for c in contracts if c.status == "expiring_soon"]
        pending_signatures = [c for c in contracts if c.status == "pending_signature"]
        total_contract_value = sum(float(c.data.get("value", 0) or 0) for c in active_contracts)

        non_compliant = [c for c in compliance if c.status in ("non_compliant", "overdue")]
        compliant_count = len([c for c in compliance if c.status == "compliant"])

        contract_statuses = {}
        for c in contracts:
            contract_statuses[c.status] = contract_statuses.get(c.status, 0) + 1

        return {
            "contracts": contracts,
            "templates": templates,
            "compliance": compliance,
            "active_contracts": active_contracts,
            "expiring_soon": expiring_soon,
            "pending_signatures": pending_signatures,
            "total_contract_value": total_contract_value,
            "non_compliant": non_compliant,
            "compliant_count": compliant_count,
            "contract_statuses": contract_statuses,
            "total_contracts": len(contracts),
            "total_templates": len(templates),
            "total_compliance": len(compliance),
        }

    @staticmethod
    def get_recent(tenant_id: int, entity_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent entities of a given type for this tenant."""
        edef = LegalDashboard._get_def(tenant_id, entity_type)
        if not edef:
            return []
        entities = db.session.query(Entity).filter_by(
            tenant_id=tenant_id, definition_id=edef.id, is_archived=False
        ).order_by(
            Entity.created_at.desc()
        ).limit(limit).all()

        return [{
            "id": e.id,
            "code": e.code,
            "display_name": e.display_name,
            "status": e.status,
            "data": e.data,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in entities]


# ---------------------------------------------------------------------------
# Ensure legal entity types exist for a tenant
# ---------------------------------------------------------------------------

def _ensure_legal_types(tenant_id: int):
    """Ensure legal entity types exist."""
    for etype, config in LEGAL_ENTITY_TYPES.items():
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