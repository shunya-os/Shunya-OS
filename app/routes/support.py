"""Shunya OS — Customer Support & Service Routes."""
from datetime import datetime
from flask import Blueprint, render_template, g, jsonify
from app import db
from app.models import Entity, EntityDefinition, ActivityLog
from app.routes.auth import login_required
from app.shunya.support import SupportDashboard, _ensure_support_types

support_bp = Blueprint("support", __name__, url_prefix="/support")


@support_bp.route("/dashboard")
@login_required
def support_dashboard():
    """Support overview — ticket queue, SLA metrics, feedback stats."""
    _ensure_support_types(g.tenant.id)

    overview = SupportDashboard.get_overview(g.tenant.id)
    ticket_stats = SupportDashboard.get_ticket_stats(g.tenant.id)
    sla_data = SupportDashboard.get_sla_compliance(g.tenant.id)

    # Get entity definitions for linking
    ticket_def = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type="ticket"
    ).first()
    kb_def = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type="knowledge_article"
    ).first()
    feedback_def = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type="feedback"
    ).first()

    return render_template("support/dashboard.html",
        overview=overview,
        ticket_stats=ticket_stats,
        sla_data=sla_data,
        ticket_def=ticket_def,
        kb_def=kb_def,
        feedback_def=feedback_def,
    )


@support_bp.route("/api/tickets/open")
@login_required
def open_tickets():
    """JSON endpoint for open tickets (for widgets / auto-refresh)."""
    ticket_def = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type="ticket"
    ).first()
    if not ticket_def:
        return jsonify({"tickets": [], "count": 0})

    tickets = Entity.query.filter_by(
        tenant_id=g.tenant.id,
        definition_id=ticket_def.id,
        is_archived=False,
    ).filter(
        Entity.status.in_(["new", "open", "in_progress"])
    ).order_by(
        # Urgent/high first, then by creation date
        db.case(
            (Entity.status == "new", 1),
            (Entity.status == "open", 2),
            (Entity.status == "in_progress", 3),
            else_=4
        ),
        Entity.created_at.desc()
    ).limit(50).all()

    return jsonify({
        "count": len(tickets),
        "tickets": [{
            "id": t.id,
            "code": t.code,
            "subject": t.data.get("subject", ""),
            "customer_name": t.data.get("customer_name", ""),
            "priority": t.data.get("priority", "medium"),
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        } for t in tickets]
    })


@support_bp.route("/api/metrics")
@login_required
def support_metrics():
    """JSON endpoint for support metrics (dashboard widgets)."""
    overview = SupportDashboard.get_overview(g.tenant.id)
    ticket_stats = SupportDashboard.get_ticket_stats(g.tenant.id)
    sla_data = SupportDashboard.get_sla_compliance(g.tenant.id)

    return jsonify({
        "overview": overview,
        "ticket_stats": {
            "status_counts": ticket_stats.get("status_counts", {}),
            "priority_data": ticket_stats.get("priority_data", {}),
            "monthly_trend": ticket_stats.get("monthly_trend", []),
            "avg_resolution_hours": ticket_stats.get("avg_resolution_hours", 0),
            "open_count": ticket_stats.get("open_tickets_count", 0),
        },
        "sla": {
            "compliance_rate": sla_data.get("compliance_rate", 100.0),
            "compliant": sla_data.get("compliant", 0),
            "breached": sla_data.get("breached", 0),
            "total_evaluated": sla_data.get("total_evaluated", 0),
        },
    })