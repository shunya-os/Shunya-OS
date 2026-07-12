"""Shunya HR & People Routes — Dashboard, Org Chart, Leave Approvals."""
from flask import Blueprint, render_template, jsonify, g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog
from app.routes.auth import login_required
from app.shunya.hr import HRDashboard, ensure_hr_types, _seed_sample_data

hr_bp = Blueprint("hr", __name__, url_prefix="/hr")


@hr_bp.route("/dashboard")
@login_required
def hr_dashboard():
    """HR & People Management dashboard."""
    ensure_hr_types(g.tenant.id)

    # Seed sample data if no entities exist yet
    _seed_sample_data(g.tenant.id)

    overview = HRDashboard.get_overview(g.tenant.id)

    emp_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="employee"
    ).first()
    leave_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="leave_request"
    ).first()
    dept_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="department"
    ).first()

    # Recent employees (last 10 joined)
    recent_employees = []
    if emp_def:
        recent_employees = db.session.query(Entity).filter_by(
            tenant_id=g.tenant.id, definition_id=emp_def.id, is_archived=False
        ).order_by(Entity.created_at.desc()).limit(10).all()

    # Pending leaves
    pending_leaves = []
    if leave_def:
        pending_leaves = db.session.query(Entity).filter(
            Entity.tenant_id == g.tenant.id,
            Entity.definition_id == leave_def.id,
            Entity.status == "pending",
            Entity.is_archived == False,
        ).order_by(Entity.created_at.asc()).limit(10).all()

    # Departments
    departments = []
    if dept_def:
        departments = db.session.query(Entity).filter_by(
            tenant_id=g.tenant.id, definition_id=dept_def.id, is_archived=False
        ).order_by(Entity.data["name"].astext.asc()).all()

    return render_template("hr/dashboard.html",
        overview=overview,
        emp_def=emp_def,
        leave_def=leave_def,
        dept_def=dept_def,
        recent_employees=recent_employees,
        pending_leaves=pending_leaves,
        departments=departments,
    )


@hr_bp.route("/api/org-chart")
@login_required
def org_chart_data():
    """JSON endpoint returning org chart data (employees grouped by department)."""
    emp_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="employee"
    ).first()
    dept_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="department"
    ).first()

    if not emp_def or not dept_def:
        return jsonify({"departments": [], "employees": []})

    departments = db.session.query(Entity).filter_by(
        tenant_id=g.tenant.id, definition_id=dept_def.id, is_archived=False
    ).all()

    employees = db.session.query(Entity).filter_by(
        tenant_id=g.tenant.id, definition_id=emp_def.id, is_archived=False
    ).all()

    dept_list = []
    for d in departments:
        dept_list.append({
            "id": d.id,
            "name": d.data.get("name", ""),
            "code": d.data.get("code", ""),
            "head_employee_id": d.data.get("head_employee_id"),
        })

    emp_list = []
    for e in employees:
        emp_list.append({
            "id": e.id,
            "code": e.code,
            "name": e.data.get("employee_name", ""),
            "department": e.data.get("department", ""),
            "position": e.data.get("position", ""),
            "manager_id": e.data.get("manager_id"),
            "status": e.status,
        })

    return jsonify({"departments": dept_list, "employees": emp_list})


@hr_bp.route("/api/leaves/pending")
@login_required
def pending_leaves():
    """JSON endpoint returning pending leave requests."""
    leave_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="leave_request"
    ).first()

    if not leave_def:
        return jsonify({"leaves": [], "count": 0})

    leaves = db.session.query(Entity).filter(
        Entity.tenant_id == g.tenant.id,
        Entity.definition_id == leave_def.id,
        Entity.status == "pending",
        Entity.is_archived == False,
    ).order_by(Entity.created_at.asc()).all()

    result = []
    for l in leaves:
        result.append({
            "id": l.id,
            "code": l.code,
            "employee_name": l.data.get("employee_name", ""),
            "employee_id": l.data.get("employee_id"),
            "leave_type": l.data.get("leave_type", ""),
            "start_date": l.data.get("start_date", ""),
            "end_date": l.data.get("end_date", ""),
            "total_days": l.data.get("total_days", 0),
            "reason": l.data.get("reason", ""),
            "created_at": l.created_at.isoformat() if l.created_at else "",
        })

    return jsonify({"leaves": result, "count": len(result)})
