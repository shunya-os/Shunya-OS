"""Shunya Marketing & Growth Routes — Dashboard, Campaigns, Metrics APIs."""
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog
from app.routes.auth import login_required
from app.shunya.marketing import MarketingDashboard

marketing_bp = Blueprint("marketing", __name__, url_prefix="/marketing")


# ---------------------------------------------------------------------------
# Marketing Dashboard (HTML)
# ---------------------------------------------------------------------------

@marketing_bp.route("/dashboard")
@login_required
def marketing_dashboard():
    """Marketing & Growth overview dashboard."""
    dashboard = MarketingDashboard(g.tenant.id)
    dashboard.ensure_types()

    # Get entity definitions for links
    campaign_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="campaign"
    ).first()
    lead_gen_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="lead_generator"
    ).first()
    email_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="email_campaign"
    ).first()
    content_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="content_asset"
    ).first()
    social_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="social_post"
    ).first()
    webinar_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="webinar"
    ).first()

    # Gather data
    overview = dashboard.get_overview()
    campaign_stats = dashboard.get_campaign_stats()
    lead_metrics = dashboard.get_lead_metrics()

    # Recent campaigns
    recent_campaigns = []
    if campaign_def:
        recent_campaigns = db.session.query(Entity).filter_by(
            tenant_id=g.tenant.id,
            definition_id=campaign_def.id,
            is_archived=False,
        ).order_by(Entity.created_at.desc()).limit(8).all()

    # Recent social posts
    recent_posts = []
    if social_def:
        recent_posts = db.session.query(Entity).filter_by(
            tenant_id=g.tenant.id,
            definition_id=social_def.id,
            is_archived=False,
        ).order_by(Entity.created_at.desc()).limit(8).all()

    # Campaign status breakdown
    campaign_statuses = {}
    if campaign_def:
        all_campaigns = db.session.query(Entity).filter_by(
            tenant_id=g.tenant.id,
            definition_id=campaign_def.id,
            is_archived=False,
        ).all()
        for c in all_campaigns:
            s = c.status
            campaign_statuses[s] = campaign_statuses.get(s, 0) + 1

    return render_template(
        "marketing/dashboard.html",
        overview=overview,
        campaign_stats=campaign_stats,
        lead_metrics=lead_metrics,
        recent_campaigns=recent_campaigns,
        recent_posts=recent_posts,
        campaign_statuses=campaign_statuses,
        campaign_def=campaign_def,
        lead_gen_def=lead_gen_def,
        email_def=email_def,
        content_def=content_def,
        social_def=social_def,
        webinar_def=webinar_def,
    )


# ---------------------------------------------------------------------------
# Campaign List API
# ---------------------------------------------------------------------------

@marketing_bp.route("/api/campaigns")
@login_required
def campaign_list():
    """JSON list of all campaigns."""
    dashboard = MarketingDashboard(g.tenant.id)
    dashboard.ensure_types()
    stats = dashboard.get_campaign_stats()
    return jsonify({"campaigns": stats, "total": len(stats)})


# ---------------------------------------------------------------------------
# Marketing Metrics API
# ---------------------------------------------------------------------------

@marketing_bp.route("/api/metrics")
@login_required
def marketing_metrics():
    """JSON marketing KPIs for dashboard widgets."""
    dashboard = MarketingDashboard(g.tenant.id)
    dashboard.ensure_types()
    overview = dashboard.get_overview()
    lead_metrics = dashboard.get_lead_metrics()

    # Monthly trend (simplified: count created per month for last 6 months)
    now = datetime.utcnow()
    monthly = []
    campaign_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="campaign"
    ).first()

    for i in range(6):
        m_start = datetime(now.year, now.month - i, 1) if now.month > i else \
            datetime(now.year - 1, 12 + now.month - i, 1)
        m_end = datetime(m_start.year + (m_start.month // 12),
                         (m_start.month % 12) + 1, 1) if m_start.month < 12 else \
            datetime(m_start.year + 1, 1, 1)

        campaign_count = 0
        if campaign_def:
            campaign_count = db.session.query(db.func.count(Entity.id)).filter(
                Entity.tenant_id == g.tenant.id,
                Entity.definition_id == campaign_def.id,
                Entity.created_at >= m_start,
                Entity.created_at < m_end,
            ).scalar() or 0

        monthly.append({
            "month": m_start.strftime("%b"),
            "campaigns_created": campaign_count,
        })
    monthly.reverse()

    return jsonify({
        "overview": overview,
        "lead_metrics": lead_metrics,
        "monthly": monthly,
    })