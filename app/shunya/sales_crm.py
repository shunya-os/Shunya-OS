"""Shunya Sales & CRM Module — Leads, Accounts, Contacts, Opportunities, Quotes, Products, Target Lists.

CRMs are the backbone of customer-facing businesses. This module provides:
- Lead management (capture, qualify, convert)
- Account & Contact management (org chart, communication)
- Opportunity pipeline tracking (deal stages, values, win/loss)
- Quote generation & management
- Product catalogue
- Target list / campaign audience management
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List, Dict, Any
from flask import g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog

# ---------------------------------------------------------------------------
# Sales & CRM Entity Type Definitions (seeded to EntityDefinition)
# ---------------------------------------------------------------------------

SALES_ENTITY_TYPES = {
    "lead": {
        "label": "Lead",
        "icon": "🎯",
        "schema": [
            {"name": "first_name", "label": "First Name", "type": "text", "required": True, "searchable": True},
            {"name": "last_name", "label": "Last Name", "type": "text", "required": True, "searchable": True},
            {"name": "email", "label": "Email", "type": "email", "searchable": True},
            {"name": "phone", "label": "Phone", "type": "phone", "searchable": True},
            {"name": "company", "label": "Company", "type": "text", "searchable": True},
            {"name": "job_title", "label": "Job Title", "type": "text"},
            {"name": "lead_source", "label": "Lead Source", "type": "select",
             "options": ["website", "referral", "cold_call", "email_campaign", "social_media",
                         "event", "partner", "paid_ad", "inbound", "other"]},
            {"name": "industry", "label": "Industry", "type": "text"},
            {"name": "lead_score", "label": "Lead Score", "type": "number"},
            {"name": "estimated_value", "label": "Estimated Value (₹)", "type": "number"},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
            {"name": "converted_to", "label": "Converted To", "type": "text"},
            {"name": "converted_at", "label": "Converted At", "type": "datetime"},
        ],
        "statuses": ["new", "contacted", "qualified", "unqualified", "converted", "junk"],
        "layout": "kanban",
        "searchable_fields": ["first_name", "last_name", "email", "phone", "company", "assigned_to"],
    },
    "account": {
        "label": "Account",
        "icon": "🏢",
        "schema": [
            {"name": "account_name", "label": "Account Name", "type": "text", "required": True, "searchable": True},
            {"name": "website", "label": "Website", "type": "text"},
            {"name": "phone", "label": "Phone", "type": "phone", "searchable": True},
            {"name": "email", "label": "Email", "type": "email", "searchable": True},
            {"name": "industry", "label": "Industry", "type": "select",
             "options": ["technology", "finance", "healthcare", "education", "manufacturing",
                         "retail", "real_estate", "hospitality", "media", "other"]},
            {"name": "account_type", "label": "Account Type", "type": "select",
             "options": ["customer", "partner", "vendor", "competitor", "other"]},
            {"name": "annual_revenue", "label": "Annual Revenue (₹)", "type": "number"},
            {"name": "employee_count", "label": "Employee Count", "type": "number"},
            {"name": "billing_address", "label": "Billing Address", "type": "textarea"},
            {"name": "shipping_address", "label": "Shipping Address", "type": "textarea"},
            {"name": "city", "label": "City", "type": "text"},
            {"name": "state", "label": "State", "type": "text"},
            {"name": "country", "label": "Country", "type": "text"},
            {"name": "pincode", "label": "Pincode", "type": "text"},
            {"name": "gstin", "label": "GSTIN", "type": "text"},
            {"name": "owner", "label": "Account Owner", "type": "text"},
            {"name": "description", "label": "Description", "type": "textarea"},
        ],
        "statuses": ["active", "inactive", "suspended", "churned"],
        "layout": "table",
        "searchable_fields": ["account_name", "phone", "email", "city", "industry", "owner"],
    },
    "contact": {
        "label": "Contact",
        "icon": "👤",
        "schema": [
            {"name": "first_name", "label": "First Name", "type": "text", "required": True, "searchable": True},
            {"name": "last_name", "label": "Last Name", "type": "text", "required": True, "searchable": True},
            {"name": "email", "label": "Email", "type": "email", "searchable": True},
            {"name": "phone", "label": "Phone", "type": "phone", "searchable": True},
            {"name": "mobile", "label": "Mobile", "type": "phone", "searchable": True},
            {"name": "account_id", "label": "Account", "type": "text"},
            {"name": "account_name", "label": "Account Name", "type": "text", "searchable": True},
            {"name": "job_title", "label": "Job Title", "type": "text"},
            {"name": "department", "label": "Department", "type": "text"},
            {"name": "reports_to", "label": "Reports To", "type": "text"},
            {"name": "birthdate", "label": "Birthdate", "type": "date"},
            {"name": "source", "label": "Source", "type": "select",
             "options": ["website", "referral", "event", "cold_outreach", "partner", "import", "other"]},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "inactive", "do_not_contact", "unsubscribed"],
        "layout": "table",
        "searchable_fields": ["first_name", "last_name", "email", "phone", "mobile", "account_name", "assigned_to"],
    },
    "opportunity": {
        "label": "Opportunity",
        "icon": "💎",
        "schema": [
            {"name": "name", "label": "Opportunity Name", "type": "text", "required": True, "searchable": True},
            {"name": "account_id", "label": "Account", "type": "text"},
            {"name": "account_name", "label": "Account Name", "type": "text", "searchable": True},
            {"name": "contact_id", "label": "Contact", "type": "text"},
            {"name": "amount", "label": "Amount (₹)", "type": "number", "required": True},
            {"name": "expected_close_date", "label": "Expected Close Date", "type": "date"},
            {"name": "probability", "label": "Probability (%)", "type": "number"},
            {"name": "lead_source", "label": "Lead Source", "type": "select",
             "options": ["website", "referral", "cold_call", "email_campaign", "social_media",
                         "event", "partner", "paid_ad", "inbound", "other"]},
            {"name": "sales_stage", "label": "Sales Stage", "type": "select",
             "options": ["prospecting", "qualification", "needs_analysis", "value_proposition",
                         "proposal", "negotiation", "closed_won", "closed_lost"]},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "competitors", "label": "Competitors", "type": "text"},
            {"name": "win_notes", "label": "Win / Loss Notes", "type": "textarea"},
            {"name": "lost_reason", "label": "Lost Reason", "type": "select",
             "options": ["", "price", "competitor", "timing", "budget", "no_decision", "other"]},
        ],
        "statuses": ["open", "in_progress", "won", "lost", "on_hold", "abandoned"],
        "layout": "kanban",
        "searchable_fields": ["name", "account_name", "assigned_to", "description"],
    },
    "quote": {
        "label": "Quote",
        "icon": "📄",
        "schema": [
            {"name": "quote_number", "label": "Quote Number", "type": "text", "required": True, "searchable": True},
            {"name": "account_id", "label": "Account", "type": "text"},
            {"name": "account_name", "label": "Account Name", "type": "text", "searchable": True},
            {"name": "contact_id", "label": "Contact", "type": "text"},
            {"name": "opportunity_id", "label": "Opportunity", "type": "text"},
            {"name": "valid_until", "label": "Valid Until", "type": "date"},
            {"name": "subtotal", "label": "Subtotal (₹)", "type": "number"},
            {"name": "discount", "label": "Discount (₹)", "type": "number"},
            {"name": "tax_rate", "label": "Tax Rate (%)", "type": "number"},
            {"name": "tax_amount", "label": "Tax Amount (₹)", "type": "number"},
            {"name": "total_amount", "label": "Total Amount (₹)", "type": "number"},
            {"name": "currency", "label": "Currency", "type": "select",
             "options": ["INR", "USD", "EUR", "GBP", "AUD", "SGD"]},
            {"name": "payment_terms", "label": "Payment Terms", "type": "text"},
            {"name": "delivery_terms", "label": "Delivery Terms", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
            {"name": "terms_and_conditions", "label": "Terms & Conditions", "type": "textarea"},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
        ],
        "statuses": ["draft", "sent", "reviewed", "accepted", "rejected", "expired", "cancelled"],
        "layout": "table",
        "searchable_fields": ["quote_number", "account_name", "assigned_to"],
    },
    "product": {
        "label": "Product",
        "icon": "📦",
        "schema": [
            {"name": "product_name", "label": "Product Name", "type": "text", "required": True, "searchable": True},
            {"name": "product_code", "label": "Product Code", "type": "text", "required": True, "searchable": True},
            {"name": "product_category", "label": "Category", "type": "select",
             "options": ["software", "hardware", "service", "subscription", "consumable", "other"]},
            {"name": "unit_price", "label": "Unit Price (₹)", "type": "number", "required": True},
            {"name": "cost_price", "label": "Cost Price (₹)", "type": "number"},
            {"name": "tax_rate", "label": "Tax Rate (%)", "type": "number"},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "uom", "label": "Unit of Measure", "type": "select",
             "options": ["each", "hour", "day", "month", "year", "kg", "meter", "sq_ft", "license"]},
            {"name": "stock_quantity", "label": "Stock Quantity", "type": "number"},
            {"name": "reorder_level", "label": "Reorder Level", "type": "number"},
            {"name": "active", "label": "Active", "type": "boolean"},
            {"name": "tags", "label": "Tags", "type": "text"},
        ],
        "statuses": ["active", "inactive", "discontinued"],
        "layout": "table",
        "searchable_fields": ["product_name", "product_code", "product_category", "description"],
    },
    "target_list": {
        "label": "Target List",
        "icon": "📋",
        "schema": [
            {"name": "name", "label": "List Name", "type": "text", "required": True, "searchable": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "list_type", "label": "List Type", "type": "select",
             "options": ["static", "dynamic", "campaign", "imported"]},
            {"name": "target_type", "label": "Target Type", "type": "select",
             "options": ["leads", "contacts", "accounts", "mixed"]},
            {"name": "member_count", "label": "Member Count", "type": "number"},
            {"name": "campaign", "label": "Campaign", "type": "text"},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
            {"name": "filter_criteria", "label": "Filter Criteria", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "inactive", "archived"],
        "layout": "table",
        "searchable_fields": ["name", "description", "campaign", "assigned_to"],
    },
}


# ---------------------------------------------------------------------------
# Sales Dashboard — Data Aggregation
# ---------------------------------------------------------------------------

class SalesDashboard:
    """Aggregates Sales & CRM data for the dashboard views."""

    @staticmethod
    def _get_def(tenant_id: int, entity_type: str):
        """Get entity definition for a type, or None."""
        return db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=entity_type
        ).first()

    @staticmethod
    def _get_entities(tenant_id: int, etype: str, archived: bool = False):
        """Get all entities of a type for this tenant."""
        edef = SalesDashboard._get_def(tenant_id, etype)
        if not edef:
            return []
        return db.session.query(Entity).filter_by(
            tenant_id=tenant_id,
            definition_id=edef.id,
            is_archived=archived,
        ).all()

    @staticmethod
    def get_overview(tenant_id: int) -> Dict[str, Any]:
        """Get all Sales & CRM metrics for the overview dashboard."""
        return {
            "lead_metrics": SalesDashboard.get_lead_metrics(tenant_id),
            "account_count": SalesDashboard.get_count(tenant_id, "account"),
            "contact_count": SalesDashboard.get_count(tenant_id, "contact"),
            "opportunity_metrics": SalesDashboard.get_opportunity_metrics(tenant_id),
            "quote_metrics": SalesDashboard.get_quote_metrics(tenant_id),
            "product_count": SalesDashboard.get_count(tenant_id, "product"),
            "target_list_count": SalesDashboard.get_count(tenant_id, "target_list"),
            "pipeline_value": SalesDashboard.get_pipeline_value(tenant_id),
            "stage_breakdown": SalesDashboard.get_stage_breakdown(tenant_id),
            "recent_activity": SalesDashboard.get_recent_activity(tenant_id),
        }

    @staticmethod
    def get_count(tenant_id: int, etype: str) -> int:
        """Count active (non-archived) entities of a type."""
        edef = SalesDashboard._get_def(tenant_id, etype)
        if not edef:
            return 0
        return db.session.query(db.func.count(Entity.id)).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == edef.id,
            Entity.is_archived == False,
        ).scalar() or 0

    @staticmethod
    def get_lead_metrics(tenant_id: int) -> Dict[str, Any]:
        """Lead counts by status and total value."""
        edef = SalesDashboard._get_def(tenant_id, "lead")
        if not edef:
            return {"total": 0, "new": 0, "contacted": 0, "qualified": 0, "converted": 0, "total_value": 0}

        leads = SalesDashboard._get_entities(tenant_id, "lead")
        status_counts = {"new": 0, "contacted": 0, "qualified": 0, "unqualified": 0, "converted": 0, "junk": 0}
        total_value = 0
        for l in leads:
            s = l.status
            status_counts[s] = status_counts.get(s, 0) + 1
            total_value += float(l.data.get("estimated_value", 0) or 0)

        return {
            "total": len(leads),
            "new": status_counts.get("new", 0),
            "contacted": status_counts.get("contacted", 0),
            "qualified": status_counts.get("qualified", 0),
            "converted": status_counts.get("converted", 0),
            "total_value": total_value,
        }

    @staticmethod
    def get_opportunity_metrics(tenant_id: int) -> Dict[str, Any]:
        """Opportunity pipeline metrics."""
        edef = SalesDashboard._get_def(tenant_id, "opportunity")
        if not edef:
            return {"total": 0, "open": 0, "won": 0, "lost": 0, "total_value": 0, "weighted_value": 0}

        opps = SalesDashboard._get_entities(tenant_id, "opportunity")
        open_count = sum(1 for o in opps if o.status in ("open", "in_progress", "on_hold"))
        won_count = sum(1 for o in opps if o.status == "won")
        lost_count = sum(1 for o in opps if o.status in ("lost", "abandoned"))
        total_value = sum(float(o.data.get("amount", 0) or 0) for o in opps)
        # Weighted pipeline value = amount * probability
        weighted_value = sum(
            float(o.data.get("amount", 0) or 0) * (float(o.data.get("probability", 0) or 0) / 100)
            for o in opps if o.status in ("open", "in_progress", "on_hold")
        )

        return {
            "total": len(opps),
            "open": open_count,
            "won": won_count,
            "lost": lost_count,
            "total_value": total_value,
            "weighted_value": round(weighted_value, 2),
        }

    @staticmethod
    def get_pipeline_value(tenant_id: int) -> float:
        """Total open opportunity value."""
        opps = SalesDashboard._get_entities(tenant_id, "opportunity")
        return sum(
            float(o.data.get("amount", 0) or 0)
            for o in opps if o.status in ("open", "in_progress", "on_hold")
        )

    @staticmethod
    def get_stage_breakdown(tenant_id: int) -> List[Dict]:
        """Opportunity count and value by sales stage."""
        edef = SalesDashboard._get_def(tenant_id, "opportunity")
        if not edef:
            return []

        opps = SalesDashboard._get_entities(tenant_id, "opportunity")
        stages = ["prospecting", "qualification", "needs_analysis", "value_proposition",
                   "proposal", "negotiation", "closed_won", "closed_lost"]
        stage_data = {}
        for s in stages:
            stage_data[s] = {"count": 0, "value": 0.0}

        for o in opps:
            stage = o.data.get("sales_stage", "prospecting")
            if stage in stage_data:
                stage_data[stage]["count"] += 1
                stage_data[stage]["value"] += float(o.data.get("amount", 0) or 0)

        return [{"stage": s, "count": stage_data[s]["count"], "value": stage_data[s]["value"]}
                for s in stages if stage_data[s]["count"] > 0]

    @staticmethod
    def get_quote_metrics(tenant_id: int) -> Dict[str, Any]:
        """Quote counts by status and total value."""
        edef = SalesDashboard._get_def(tenant_id, "quote")
        if not edef:
            return {"total": 0, "draft": 0, "sent": 0, "accepted": 0, "rejected": 0, "total_value": 0}

        quotes = SalesDashboard._get_entities(tenant_id, "quote")
        status_counts = {"draft": 0, "sent": 0, "reviewed": 0, "accepted": 0, "rejected": 0, "expired": 0, "cancelled": 0}
        total_value = 0
        for q in quotes:
            s = q.status
            status_counts[s] = status_counts.get(s, 0) + 1
            total_value += float(q.data.get("total_amount", 0) or 0)

        return {
            "total": len(quotes),
            "draft": status_counts.get("draft", 0),
            "sent": status_counts.get("sent", 0),
            "accepted": status_counts.get("accepted", 0),
            "rejected": status_counts.get("rejected", 0),
            "total_value": total_value,
        }

    @staticmethod
    def get_recent_activity(tenant_id: int, limit: int = 10) -> List[Dict]:
        """Get recent Sales-related activity log entries."""
        # Get all Sales entity definition IDs
        sales_types = list(SALES_ENTITY_TYPES.keys())
        defs = db.session.query(EntityDefinition).filter(
            EntityDefinition.tenant_id == tenant_id,
            EntityDefinition.type.in_(sales_types),
        ).all()
        def_ids = [d.id for d in defs]
        if not def_ids:
            return []

        activities = db.session.query(ActivityLog).filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.entity_id.in_(
                db.session.query(Entity.id).filter(
                    Entity.tenant_id == tenant_id,
                    Entity.definition_id.in_(def_ids),
                )
            ),
        ).order_by(
            ActivityLog.created_at.desc()
        ).limit(limit).all()

        return [{
            "id": a.id,
            "action": a.action,
            "detail": a.detail,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        } for a in activities]

    @staticmethod
    def get_status_breakdown(tenant_id: int, etype: str) -> Dict[str, int]:
        """Get count of entities by status for a given type."""
        edef = SalesDashboard._get_def(tenant_id, etype)
        if not edef:
            return {}

        rows = db.session.query(
            Entity.status, db.func.count(Entity.id)
        ).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == edef.id,
            Entity.is_archived == False,
        ).group_by(Entity.status).all()

        return {status: count for status, count in rows}

    @staticmethod
    def get_account_summary(tenant_id: int) -> List[Dict]:
        """Get account list with contact count."""
        accounts = SalesDashboard._get_entities(tenant_id, "account")
        contacts = SalesDashboard._get_entities(tenant_id, "contact")

        # Map account name/id to contact count
        contact_count_map = defaultdict(int)
        for c in contacts:
            acc_name = c.data.get("account_name", "")
            if acc_name:
                contact_count_map[acc_name] += 1

        results = []
        for a in accounts:
            name = a.data.get("account_name", "Unnamed")
            results.append({
                "id": a.id,
                "code": a.code,
                "name": name,
                "industry": a.data.get("industry", ""),
                "city": a.data.get("city", ""),
                "status": a.status,
                "contact_count": contact_count_map.get(name, 0),
                "annual_revenue": a.data.get("annual_revenue", 0),
            })
        return results

    @staticmethod
    def get_recent_leads(tenant_id: int, limit: int = 10) -> List[Dict]:
        """Get recent leads with minimal data."""
        edef = SalesDashboard._get_def(tenant_id, "lead")
        if not edef:
            return []

        leads = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == edef.id,
            Entity.is_archived == False,
        ).order_by(Entity.created_at.desc()).limit(limit).all()

        return [{
            "id": l.id,
            "code": l.code,
            "name": f"{l.data.get('first_name', '')} {l.data.get('last_name', '')}".strip() or "Unnamed",
            "company": l.data.get("company", ""),
            "email": l.data.get("email", ""),
            "lead_source": l.data.get("lead_source", ""),
            "status": l.status,
            "lead_score": l.data.get("lead_score", 0),
            "created_at": l.created_at.isoformat() if l.created_at else "",
        } for l in leads]

    @staticmethod
    def get_recent_opportunities(tenant_id: int, limit: int = 10) -> List[Dict]:
        """Get recent opportunities."""
        edef = SalesDashboard._get_def(tenant_id, "opportunity")
        if not edef:
            return []

        opps = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == edef.id,
            Entity.is_archived == False,
        ).order_by(Entity.created_at.desc()).limit(limit).all()

        return [{
            "id": o.id,
            "code": o.code,
            "name": o.data.get("name", "Unnamed"),
            "account_name": o.data.get("account_name", ""),
            "amount": o.data.get("amount", 0),
            "sales_stage": o.data.get("sales_stage", ""),
            "probability": o.data.get("probability", 0),
            "status": o.status,
            "assigned_to": o.data.get("assigned_to", ""),
            "expected_close_date": str(o.data.get("expected_close_date", "")),
            "created_at": o.created_at.isoformat() if o.created_at else "",
        } for o in opps]


# ---------------------------------------------------------------------------
# Ensure Sales entity types exist for a tenant
# ---------------------------------------------------------------------------

def ensure_sales_types(tenant_id: int):
    """Ensure all Sales & CRM entity definitions exist for this tenant."""
    for etype, config in SALES_ENTITY_TYPES.items():
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
            layout=config.get("layout", "table"),
            searchable_fields=config.get("searchable_fields", []),
            primary_field=config["schema"][0]["name"] if config["schema"] else "name",
        )
        db.session.add(definition)
    db.session.commit()