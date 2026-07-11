"""Shunya OS — Dashboard."""
from flask import Blueprint, render_template, g, jsonify, redirect, url_for
from app.routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    """Home dashboard — context-aware, never dead-end."""
    # Redirect to onboarding if not completed
    if not g.tenant.onboarding_completed:
        return redirect(url_for("onboarding.onboarding_page"))

    from app.models import Entity, EntityDefinition, ActivityLog
    from app.shunya.bird import Bird
    from app.shunya.next_best_action import NextBestActionEngine

    tenant = g.tenant
    user = g.user

    definitions = EntityDefinition.query.filter_by(
        tenant_id=tenant.id, is_active=True
    ).all()

    # Counts per type
    def_counts = {}
    for d in definitions:
        count = Entity.query.filter_by(
            tenant_id=tenant.id, definition_id=d.id, is_archived=False
        ).count()
        def_counts[d.type] = {"label": d.label_plural or d.label, "icon": d.icon, "count": count}

    # Recent activity
    recent = ActivityLog.query.filter_by(tenant_id=tenant.id)\
        .order_by(ActivityLog.created_at.desc()).limit(10).all()

    # Bird greeting (context-aware, not a static wall of charts)
    bird = Bird(tenant.id, user.id, user.role, user.name)
    greeting = bird.greet()

    # Next Best Actions
    next_actions = NextBestActionEngine.get_for_user(tenant.id, user.id, user.role)

    return render_template("dashboard.html",
        tenant=tenant, user=user,
        definitions=definitions,
        def_counts=def_counts,
        recent_activities=recent,
        bird_greeting=greeting,
        next_actions=next_actions,
        welcome_message=greeting["message"])


@dashboard_bp.route("/analytics")
@login_required
def analytics():
    """Analytics dashboard — founder visibility."""
    from app.shunya.analytics import AnalyticsEngine
    data = AnalyticsEngine.get_overview(g.tenant.id)
    insights = AnalyticsEngine.get_founder_insights(g.tenant.id)
    return render_template("analytics.html", data=data, insights=insights)


@dashboard_bp.route("/api/analytics")
@login_required
def analytics_api():
    """Analytics data as JSON."""
    from app.shunya.analytics import AnalyticsEngine
    data = AnalyticsEngine.get_overview(g.tenant.id)
    insights = AnalyticsEngine.get_founder_insights(g.tenant.id)
    return jsonify({"overview": data, "insights": insights})


@dashboard_bp.route("/learning")
@login_required
def learning_page():
    """Learning Engine dashboard."""
    return render_template("learning.html")
