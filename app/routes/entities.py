"""Shunya OS — Generic Entity CRUD (the core engine)."""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, g
from app import db
from app.models import Entity, EntityDefinition, next_entity_code, ActivityLog
from app.routes.auth import login_required

entities_bp = Blueprint("entities", __name__, url_prefix="/entities")


# ---------------------------------------------------------------------------
# List entities (table, kanban, calendar, cards)
# ---------------------------------------------------------------------------

@entities_bp.route("/<entity_type>")
@login_required
def list_entities(entity_type):
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type, is_active=True
    ).first()
    if not definition:
        flash(f"Entity type '{entity_type}' not found", "error")
        return redirect(url_for("dashboard.index"))

    # Filters
    status = request.args.get("status")
    q = request.args.get("q")
    assigned = request.args.get("assigned_to")

    query = Entity.query.filter_by(
        tenant_id=g.tenant.id, definition_id=definition.id, is_archived=False
    )

    if status:
        query = query.filter(Entity.status == status)
    if assigned:
        query = query.filter(Entity.assigned_to == int(assigned))

    # Search in JSONB data
    if q and definition.searchable_fields:
        search_filter = []
        for field_name in definition.searchable_fields:
            search_filter.append(Entity.data[field_name].as_string().ilike(f"%{q}%"))
        query = query.filter(db.or_(*search_filter))

    entities = query.order_by(Entity.created_at.desc()).limit(100).all()

    if request.is_json:
        return jsonify({"entities": [e.to_dict() for e in entities]})

    templates = {
        "kanban": "entity_pipeline.html",
        "calendar": "entity_calendar.html",
        "cards": "entity_cards.html",
    }
    template = templates.get(definition.layout, "entity_list.html")

    return render_template(template, entities=entities, definition=definition)


# ---------------------------------------------------------------------------
# View single entity
# ---------------------------------------------------------------------------

@entities_bp.route("/<entity_type>/<int:entity_id>")
@login_required
def entity_detail(entity_type, entity_id):
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first_or_404()
    entity = Entity.query.filter_by(
        id=entity_id, tenant_id=g.tenant.id, definition_id=definition.id
    ).first_or_404()

    activities = entity.activities.order_by(ActivityLog.created_at.desc()).limit(50).all()

    if request.is_json:
        return jsonify({"entity": entity.to_dict(), "activities": [{
            "id": a.id, "action": a.action, "detail": a.detail,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in activities]})

    # Next Best Action for this entity
    from app.shunya.next_best_action import NextBestActionEngine
    next_actions = NextBestActionEngine.get_for_user(
        g.tenant.id, g.user.id, g.user.role, entity_id=entity.id
    )

    # Workflow state
    from app.shunya.workflow import WorkflowEngine
    workflow = WorkflowEngine.get_state(g.tenant.id, entity.id)

    return render_template("entity_detail.html", entity=entity, definition=definition,
                           activities=activities, next_actions=next_actions,
                           workflow=workflow)


# ---------------------------------------------------------------------------
# Create entity
# ---------------------------------------------------------------------------

@entities_bp.route("/<entity_type>/new", methods=["GET", "POST"])
@login_required
def entity_new(entity_type):
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type, is_active=True
    ).first_or_404()

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()

        # Validate required fields
        for field in definition.schema:
            if field.get("required") and not data.get(field.get("name")):
                return jsonify({"error": f"{field.get('label')} is required"}), 400

        code = next_entity_code(db.session, g.tenant.id, entity_type)

        # Build data dict from form fields (only defined schema fields)
        entity_data = {}
        for field in definition.schema:
            fname = field["name"]
            if fname in data:
                val = data[fname]
                if field.get("type") == "number":
                    try:
                        val = float(val)
                    except (ValueError, TypeError):
                        val = 0
                entity_data[fname] = val

        entity = Entity(
            tenant_id=g.tenant.id,
            definition_id=definition.id,
            code=code,
            status=data.get("status", definition.statuses[0] if definition.statuses else "new"),
            data=entity_data,
            created_by=g.user.id,
        )
        db.session.add(entity)
        db.session.flush()

        # Log activity
        activity = ActivityLog(
            tenant_id=g.tenant.id,
            entity_id=entity.id,
            user_id=g.user.id,
            action="created",
            detail=f"{definition.label} created via {definition.type} form",
            governance_level="auto",
        )
        db.session.add(activity)
        db.session.commit()

        if request.is_json:
            return jsonify({"success": True, "entity": entity.to_dict()}), 201
        flash(f"{definition.label} created ({code})", "success")
        return redirect(url_for("entities.entity_detail", entity_type=entity_type, entity_id=entity.id))

    code = next_entity_code(db.session, g.tenant.id, entity_type)
    return render_template("entity_form.html", definition=definition, entity=None, code=code)


# ---------------------------------------------------------------------------
# Update entity
# ---------------------------------------------------------------------------

@entities_bp.route("/<entity_type>/<int:entity_id>/edit", methods=["GET", "POST"])
@login_required
def entity_edit(entity_type, entity_id):
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first_or_404()
    entity = Entity.query.filter_by(
        id=entity_id, tenant_id=g.tenant.id, definition_id=definition.id
    ).first_or_404()

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()

        changes = []
        for field in definition.schema:
            fname = field["name"]
            if fname in data:
                old_val = entity.data.get(fname)
                new_val = data[fname]
                if field.get("type") == "number":
                    try:
                        new_val = float(new_val)
                    except (ValueError, TypeError):
                        new_val = 0
                entity.data[fname] = new_val
                if str(old_val) != str(new_val):
                    changes.append(f"{fname}: {old_val} → {new_val}")

        if "status" in data and data["status"] != entity.status:
            changes.append(f"status: {entity.status} → {data['status']}")
            entity.status = data["status"]

        if changes:
            activity = ActivityLog(
                tenant_id=g.tenant.id,
                entity_id=entity.id,
                user_id=g.user.id,
                action="updated",
                detail="; ".join(changes[:5]),
            )
            db.session.add(activity)

        db.session.commit()

        if request.is_json:
            return jsonify({"success": True, "entity": entity.to_dict()})
        flash(f"{definition.label} updated", "success")
        return redirect(url_for("entities.entity_detail", entity_type=entity_type, entity_id=entity.id))

    return render_template("entity_form.html", definition=definition, entity=entity, code=entity.code)


# ---------------------------------------------------------------------------
# Update status
# ---------------------------------------------------------------------------

@entities_bp.route("/<entity_type>/<int:entity_id>/status", methods=["POST"])
@login_required
def entity_update_status(entity_type, entity_id):
    data = request.get_json(silent=True) or request.form
    new_status = data.get("status", "")

    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first_or_404()
    old_status = entity.status
    entity.status = new_status

    activity = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="status_changed",
        detail=f"Status changed: {old_status} → {new_status}",
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({"success": True, "status": new_status})


# ---------------------------------------------------------------------------
# Delete / Archive entity
# ---------------------------------------------------------------------------

@entities_bp.route("/<entity_type>/<int:entity_id>/archive", methods=["POST"])
@login_required
def entity_archive(entity_type, entity_id):
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first_or_404()
    entity.is_archived = True

    activity = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="archived",
        detail=f"{entity.definition.label if entity.definition else 'Entity'} archived",
    )
    db.session.add(activity)
    db.session.commit()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Entity code generator (for forms to pre-fill)
# ---------------------------------------------------------------------------

@entities_bp.route("/<entity_type>/next-code")
@login_required
def get_next_code(entity_type):
    code = next_entity_code(db.session, g.tenant.id, entity_type)
    return jsonify({"code": code})
