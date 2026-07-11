"""Shunya Operations Module — Projects, Tasks, and Workflow Management.

Every business needs to track work. This module provides:
- Project management with milestones and phases
- Task management with dependencies and assignments
- Workflow states with semantic clarity (PENDING, READY, ACTIVE, BLOCKED, DONE)
"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog
from app.routes.auth import login_required

ops_bp = Blueprint("operations", __name__, url_prefix="/ops")

OPS_ENTITY_TYPES = {
    "project": {
        "label": "Project",
        "icon": "📋",
        "schema": [
            {"name": "name", "label": "Project Name", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "start_date", "label": "Start Date", "type": "date"},
            {"name": "end_date", "label": "End Date", "type": "date"},
            {"name": "budget", "label": "Budget", "type": "number"},
            {"name": "priority", "label": "Priority", "type": "select", "options": ["low", "medium", "high", "critical"]},
            {"name": "department", "label": "Department", "type": "text"},
            {"name": "tags", "label": "Tags", "type": "text"},
        ],
        "statuses": ["planning", "active", "on_hold", "completed", "cancelled"],
        "layout": "kanban",
        "searchable_fields": ["name", "description", "department"],
    },
    "task": {
        "label": "Task",
        "icon": "✅",
        "schema": [
            {"name": "title", "label": "Title", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "project_id", "label": "Project ID", "type": "text"},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
            {"name": "due_date", "label": "Due Date", "type": "date"},
            {"name": "priority", "label": "Priority", "type": "select", "options": ["low", "medium", "high", "critical"]},
            {"name": "estimated_hours", "label": "Estimated Hours", "type": "number"},
            {"name": "actual_hours", "label": "Actual Hours", "type": "number"},
            {"name": "dependencies", "label": "Dependencies", "type": "text"},
            {"name": "blocker_reason", "label": "Blocker Reason", "type": "textarea"},
        ],
        "statuses": ["pending", "ready", "active", "blocked", "completed", "cancelled"],
        "layout": "kanban",
        "searchable_fields": ["title", "description", "assigned_to"],
    },
    "milestone": {
        "label": "Milestone",
        "icon": "🏁",
        "schema": [
            {"name": "name", "label": "Milestone Name", "type": "text", "required": True},
            {"name": "project_id", "label": "Project ID", "type": "text"},
            {"name": "target_date", "label": "Target Date", "type": "date"},
            {"name": "description", "label": "Description", "type": "textarea"},
        ],
        "statuses": ["pending", "achieved", "missed"],
        "layout": "table",
        "searchable_fields": ["name", "description"],
    },
}


@ops_bp.route("")
@login_required
def ops_dashboard():
    """Operations overview — projects, tasks, milestones."""
    _ensure_ops_types(g.tenant.id)

    proj_def = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="project").first()
    task_def = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="task").first()

    projects = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=proj_def.id, is_archived=False).all() if proj_def else []
    tasks = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=task_def.id, is_archived=False).all() if task_def else []

    # Task status breakdown
    task_statuses = {}
    for t in tasks:
        s = t.status
        task_statuses[s] = task_statuses.get(s, 0) + 1

    # Project status breakdown
    project_statuses = {}
    for p in projects:
        s = p.status
        project_statuses[s] = project_statuses.get(s, 0) + 1

    # Blocked tasks (important to surface)
    blocked_tasks = [t for t in tasks if t.status == "blocked"]

    return render_template("ops/dashboard.html",
        projects=projects, tasks=tasks,
        task_statuses=task_statuses, project_statuses=project_statuses,
        blocked_tasks=blocked_tasks,
        proj_def=proj_def, task_def=task_def,
    )


@ops_bp.route("/api/tasks/kanban")
@login_required
def kanban_data():
    """JSON data for kanban board view."""
    task_def = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="task").first()
    if not task_def:
        return jsonify({"columns": []})

    tasks = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=task_def.id, is_archived=False).all()

    columns = {}
    for t in tasks:
        s = t.status
        if s not in columns:
            columns[s] = []
        columns[s].append({
            "id": t.id,
            "code": t.code,
            "title": t.data.get("title", t.display_name),
            "priority": t.data.get("priority", "medium"),
            "assigned": t.data.get("assigned_to", "Unassigned"),
            "due": t.data.get("due_date", ""),
            "blocker": t.data.get("blocker_reason", ""),
        })

    return jsonify({"columns": columns})


@ops_bp.route("/api/status/<string:entity_type>/<int:entity_id>", methods=["PUT"])
@login_required
def update_status(entity_type, entity_id):
    """Update entity status with dependency awareness."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "")
    if not new_status:
        return jsonify({"error": "Status required"}), 400

    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first()
    if not entity:
        return jsonify({"error": "Not found"}), 404

    old_status = entity.status

    # Check if status transition is valid
    definition = EntityDefinition.query.get(entity.definition_id)
    if definition and definition.statuses and new_status not in definition.statuses:
        return jsonify({"error": f"Invalid status '{new_status}'. Valid: {definition.statuses}"}), 400

    entity.status = new_status

    # Log
    activity = ActivityLog(
        tenant_id=entity.tenant_id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="status_changed",
        detail=f"{entity_type}: {old_status} → {new_status}",
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({"success": True, "old_status": old_status, "new_status": new_status})


def _ensure_ops_types(tenant_id: int):
    """Ensure operations entity types exist."""
    for etype, config in OPS_ENTITY_TYPES.items():
        existing = EntityDefinition.query.filter_by(tenant_id=tenant_id, type=etype).first()
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