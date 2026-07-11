"""Shunya OS — Dashboard."""
from flask import Blueprint, render_template, g
from app.routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    """Home dashboard — shows summary based on tenant's business type."""
    from app.models import Entity, EntityDefinition

    tenant = g.tenant
    user = g.user

    # Get all entity types for this tenant
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
    from app.models import ActivityLog
    recent = ActivityLog.query.filter_by(tenant_id=tenant.id)\
        .order_by(ActivityLog.created_at.desc()).limit(10).all()

    return render_template("dashboard.html",
        tenant=tenant, user=user,
        definitions=definitions,
        def_counts=def_counts,
        recent_activities=recent)
