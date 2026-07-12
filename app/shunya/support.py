"""Shunya Support Module — Customer Support & Service Management.

Tickets, Knowledge Base, Feedback, SLA tracking, and Ticket Categories.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from flask import g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog, TeamMember


# ---------------------------------------------------------------------------
# Support Entity Types (seeded in seed_scripts/seed_all.py)
# ---------------------------------------------------------------------------

SUPPORT_ENTITY_TYPES = {
    "ticket": {
        "label": "Ticket",
        "icon": "🎫",
        "schema": [
            {"name": "subject", "label": "Subject", "type": "text", "required": True},
            {"name": "customer_name", "label": "Customer Name", "type": "text", "required": True},
            {"name": "customer_email", "label": "Customer Email", "type": "text"},
            {"name": "customer_phone", "label": "Customer Phone", "type": "text"},
            {"name": "category", "label": "Category", "type": "select",
             "options": ["billing", "technical", "account", "feature_request", "complaint", "other"]},
            {"name": "priority", "label": "Priority", "type": "select",
             "options": ["low", "medium", "high", "urgent"]},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
            {"name": "sla_deadline", "label": "SLA Deadline", "type": "datetime"},
            {"name": "resolution", "label": "Resolution Notes", "type": "textarea"},
            {"name": "channel", "label": "Channel", "type": "select",
             "options": ["email", "phone", "chat", "portal", "whatsapp", "social"]},
        ],
        "statuses": ["new", "open", "in_progress", "resolved", "closed"],
        "layout": "kanban",
        "searchable_fields": ["subject", "customer_name", "customer_email", "customer_phone"],
    },
    "knowledge_article": {
        "label": "Knowledge Article",
        "icon": "📚",
        "schema": [
            {"name": "title", "label": "Title", "type": "text", "required": True},
            {"name": "category", "label": "Category", "type": "select",
             "options": ["billing", "technical", "faq", "troubleshooting", "how_to", "policy"]},
            {"name": "content", "label": "Article Content", "type": "textarea", "required": True},
            {"name": "tags", "label": "Tags", "type": "text"},
            {"name": "author", "label": "Author", "type": "text"},
            {"name": "related_articles", "label": "Related Articles", "type": "text"},
            {"name": "article_type", "label": "Article Type", "type": "select",
             "options": ["public", "internal", "customer_facing"]},
        ],
        "statuses": ["draft", "review", "published", "archived"],
        "layout": "table",
        "searchable_fields": ["title", "category", "tags", "content"],
    },
    "feedback": {
        "label": "Feedback",
        "icon": "📝",
        "schema": [
            {"name": "customer_name", "label": "Customer Name", "type": "text"},
            {"name": "customer_email", "label": "Customer Email", "type": "text"},
            {"name": "rating", "label": "Rating", "type": "select",
             "options": ["1", "2", "3", "4", "5"]},
            {"name": "category", "label": "Category", "type": "select",
             "options": ["service", "product", "support", "billing", "general"]},
            {"name": "feedback_text", "label": "Feedback", "type": "textarea", "required": True},
            {"name": "source", "label": "Source", "type": "select",
             "options": ["email", "survey", "app", "chat", "phone", "social"]},
            {"name": "ticket_id", "label": "Related Ticket", "type": "text"},
            {"name": "action_taken", "label": "Action Taken", "type": "textarea"},
        ],
        "statuses": ["new", "acknowledged", "addressed", "closed"],
        "layout": "table",
        "searchable_fields": ["customer_name", "customer_email", "category"],
    },
    "sla": {
        "label": "SLA Policy",
        "icon": "⏱️",
        "schema": [
            {"name": "name", "label": "SLA Name", "type": "text", "required": True},
            {"name": "priority", "label": "Priority Level", "type": "select",
             "options": ["low", "medium", "high", "urgent"]},
            {"name": "response_time_hours", "label": "Response Time (hours)", "type": "number", "required": True},
            {"name": "resolution_time_hours", "label": "Resolution Time (hours)", "type": "number", "required": True},
            {"name": "escalation_after_hours", "label": "Escalation After (hours)", "type": "number"},
            {"name": "business_hours_only", "label": "Business Hours Only", "type": "boolean"},
            {"name": "penalty_if_breached", "label": "Penalty if Breached", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "inactive", "draft"],
        "layout": "table",
        "searchable_fields": ["name", "priority"],
    },
    "ticket_category": {
        "label": "Ticket Category",
        "icon": "🏷️",
        "schema": [
            {"name": "name", "label": "Category Name", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "color", "label": "Color", "type": "select",
             "options": ["blue", "green", "red", "amber", "purple", "teal", "pink", "indigo"]},
            {"name": "default_priority", "label": "Default Priority", "type": "select",
             "options": ["low", "medium", "high", "urgent"]},
            {"name": "auto_assign_to", "label": "Auto-Assign To", "type": "text"},
            {"name": "sla_policy", "label": "SLA Policy", "type": "text"},
        ],
        "statuses": ["active", "inactive"],
        "layout": "table",
        "searchable_fields": ["name", "description"],
    },
}


# ---------------------------------------------------------------------------
# Support Dashboard
# ---------------------------------------------------------------------------

class SupportDashboard:
    """Support analytics and dashboard data."""

    @staticmethod
    def get_overview(tenant_id: int) -> Dict[str, Any]:
        """Get high-level support overview metrics."""
        ticket_def = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type="ticket"
        ).first()
        feedback_def = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type="feedback"
        ).first()

        if not ticket_def:
            return {"error": "Ticket entity type not defined"}

        tickets = Entity.query.filter_by(
            tenant_id=tenant_id, definition_id=ticket_def.id, is_archived=False
        ).all()

        total_tickets = len(tickets)
        open_tickets = sum(1 for t in tickets if t.status in ("new", "open", "in_progress"))
        resolved_tickets = sum(1 for t in tickets if t.status in ("resolved", "closed"))
        unresolved = total_tickets - resolved_tickets

        # Priority breakdown
        priority_counts = {"low": 0, "medium": 0, "high": 0, "urgent": 0}
        for t in tickets:
            p = t.data.get("priority", "medium")
            priority_counts[p] = priority_counts.get(p, 0) + 1

        # Channel breakdown
        channel_counts = {}
        for t in tickets:
            ch = t.data.get("channel", "other")
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

        # Feedback summary
        feedback_stats = {}
        if feedback_def:
            feedbacks = Entity.query.filter_by(
                tenant_id=tenant_id, definition_id=feedback_def.id, is_archived=False
            ).all()
            ratings = [int(f.data.get("rating", 0)) for f in feedbacks if f.data.get("rating")]
            feedback_stats = {
                "total": len(feedbacks),
                "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else 0,
                "count_5star": sum(1 for r in ratings if r == 5),
                "count_1star": sum(1 for r in ratings if r == 1),
            }

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "unresolved": unresolved,
            "priority_counts": priority_counts,
            "channel_counts": channel_counts,
            "feedback": feedback_stats,
        }

    @staticmethod
    def get_ticket_stats(tenant_id: int) -> Dict[str, Any]:
        """Get detailed ticket statistics for dashboard widgets."""
        ticket_def = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type="ticket"
        ).first()
        if not ticket_def:
            return {}

        tickets = Entity.query.filter_by(
            tenant_id=tenant_id, definition_id=ticket_def.id, is_archived=False
        ).order_by(Entity.created_at.desc()).all()

        # Status breakdown
        status_counts = {}
        for t in tickets:
            status_counts[t.status] = status_counts.get(t.status, 0) + 1

        # Tickets by priority (for charting)
        priority_data = {"low": 0, "medium": 0, "high": 0, "urgent": 0}
        for t in tickets:
            p = t.data.get("priority", "medium")
            priority_data[p] = priority_data.get(p, 0) + 1

        # Monthly trend (last 6 months)
        now = datetime.utcnow()
        monthly_trend = []
        for i in range(6):
            m_start = datetime(now.year, now.month - i, 1) if now.month > i else \
                      datetime(now.year - 1, 12 + now.month - i, 1)
            m_end = datetime(m_start.year + (m_start.month // 12),
                             (m_start.month % 12) + 1, 1) if m_start.month < 12 else \
                    datetime(m_start.year + 1, 1, 1)
            month_tickets = [t for t in tickets if t.created_at >= m_start and t.created_at < m_end]
            monthly_trend.append({
                "month": m_start.strftime("%b"),
                "created": len(month_tickets),
                "resolved": sum(1 for t in month_tickets if t.status in ("resolved", "closed")),
            })
        monthly_trend.reverse()

        # Average resolution time (in hours)
        resolution_times = []
        for t in tickets:
            if t.status in ("resolved", "closed") and t.created_at and t.updated_at:
                delta = (t.updated_at - t.created_at).total_seconds() / 3600
                resolution_times.append(delta)
        avg_resolution_hours = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0

        # Open tickets sorted by priority
        open_tickets_list = [t for t in tickets if t.status in ("new", "open", "in_progress")]

        return {
            "status_counts": status_counts,
            "priority_data": priority_data,
            "monthly_trend": monthly_trend,
            "avg_resolution_hours": avg_resolution_hours,
            "open_tickets_count": len(open_tickets_list),
            "open_tickets": [t.to_dict() for t in open_tickets_list[:50]],
            "status_order": ["new", "open", "in_progress", "resolved", "closed"],
        }

    @staticmethod
    def get_sla_compliance(tenant_id: int) -> Dict[str, Any]:
        """Get SLA compliance metrics."""
        ticket_def = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type="ticket"
        ).first()
        sla_def = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type="sla"
        ).first()

        if not ticket_def or not sla_def:
            return {"error": "Required entity types not defined", "compliant": 0, "breached": 0, "rate": 0}

        sla_policies = Entity.query.filter_by(
            tenant_id=tenant_id, definition_id=sla_def.id, status="active"
        ).all()
        tickets = Entity.query.filter_by(
            tenant_id=tenant_id, definition_id=ticket_def.id, is_archived=False
        ).all()

        # Map priority -> sla hours
        sla_map = {}
        for s in sla_policies:
            pri = s.data.get("priority", "medium")
            sla_map[pri] = {
                "response": float(s.data.get("response_time_hours", 24)),
                "resolution": float(s.data.get("resolution_time_hours", 72)),
            }

        # Evaluate resolved/closed tickets
        compliant = 0
        breached = 0
        total_evaluated = 0
        breach_details = []

        for t in tickets:
            if t.status not in ("resolved", "closed") or not t.created_at or not t.updated_at:
                continue
            pri = t.data.get("priority", "medium")
            sla = sla_map.get(pri, {"response": 24, "resolution": 72})
            sla_hours = sla["resolution"]
            actual_hours = (t.updated_at - t.created_at).total_seconds() / 3600

            total_evaluated += 1
            if actual_hours <= sla_hours:
                compliant += 1
            else:
                breached += 1
                breach_details.append({
                    "ticket_id": t.id,
                    "subject": t.data.get("subject", ""),
                    "priority": pri,
                    "sla_hours": sla_hours,
                    "actual_hours": round(actual_hours, 1),
                })

        compliance_rate = round((compliant / total_evaluated * 100), 1) if total_evaluated else 100.0

        return {
            "compliant": compliant,
            "breached": breached,
            "total_evaluated": total_evaluated,
            "compliance_rate": compliance_rate,
            "breach_details": breach_details[:20],
            "sla_policies_count": len(sla_policies),
        }


# ---------------------------------------------------------------------------
# Helper — ensure support entity types exist for a tenant
# ---------------------------------------------------------------------------

def _ensure_support_types(tenant_id: int):
    """Ensure all support entity definitions exist for this tenant."""
    for etype, config in SUPPORT_ENTITY_TYPES.items():
        existing = EntityDefinition.query.filter_by(
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