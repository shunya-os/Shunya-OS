"""Shunya Field Services Routes — Dashboard, Summary."""
from flask import Blueprint, render_template, jsonify, g
from app import db
from app.models import Entity, EntityDefinition
from app.routes.auth import login_required
from app.shunya.field_services import FSDashboard, _ensure_fs_types

field_services_bp = Blueprint("field_services", __name__, url_prefix="/field-services")


@field_services_bp.route("")
@login_required
def fs_dashboard():
    """Field services overview dashboard."""
    _ensure_fs_types(g.tenant.id)
    overview = FSDashboard.get_overview(g.tenant.id)
    return render_template("field_services/dashboard.html", **overview)


@field_services_bp.route("/api/summary")
@login_required
def fs_summary():
    """JSON summary of work orders."""
    wo_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="work_order"
    ).first()
    work_orders = db.session.query(Entity).filter(
        Entity.tenant_id == g.tenant.id,
        Entity.definition_id == wo_def.id,
    ).all() if wo_def else []

    return jsonify({
        "total_work_orders": len(work_orders),
        "scheduled": len([w for w in work_orders if w.status == "scheduled"]),
        "in_progress": len([w for w in work_orders if w.status == "in_progress"]),
        "completed": len([w for w in work_orders if w.status == "completed"]),
        "total_revenue": sum(float(w.data.get("total_charge", 0)) for w in work_orders if w.status == "completed"),
    })