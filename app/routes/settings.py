"""Shunya OS — Settings & Admin."""
import json, os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app import db
from app.models import Tenant, TeamMember, EntityDefinition, Supplier, Entity
from app.routes.auth import login_required

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("")
@login_required
def settings_page():
    suppliers = Supplier.query.filter_by(tenant_id=g.tenant.id)\
        .order_by(Supplier.created_at.desc()).limit(200).all()
    definitions = EntityDefinition.query.filter_by(tenant_id=g.tenant.id).all()
    team = TeamMember.query.filter_by(tenant_id=g.tenant.id).all()

    # WhatsApp config status
    wa_config = (g.tenant.ai_config or {}).get("whatsapp", {}) or {}
    wa_configured = bool(wa_config.get("token") and wa_config.get("phone_id"))

    # Current user's phone info
    user = g.user

    return render_template("settings.html", suppliers=suppliers,
                           definitions=definitions, team=team,
                           wa_configured=wa_configured,
                           user=user)


# ── Phone Number Management API ──

@settings_bp.route("/api/phone", methods=["GET"])
@login_required
def get_phone_settings():
    """Return current user's phone numbers."""
    user = g.user
    return jsonify({
        "phone": user.phone or "",
        "secondary_phone": user.secondary_phone or "",
        "whatsapp_phone": user.whatsapp_phone or "",
        "whatsapp_verified": user.whatsapp_verified or False,
    })


@settings_bp.route("/api/phone", methods=["POST"])
@login_required
def update_phone_settings():
    """Update current user's phone numbers."""
    data = request.get_json(silent=True) or {}
    user = g.user

    phone = data.get("phone", "").strip()
    secondary_phone = data.get("secondary_phone", "").strip()

    if phone:
        user.phone = phone
    if secondary_phone:
        user.secondary_phone = secondary_phone

    # If whatsapp_phone is provided separately, update it too
    whatsapp_phone = data.get("whatsapp_phone", "").strip()
    if whatsapp_phone:
        user.whatsapp_phone = whatsapp_phone

    db.session.commit()
    return jsonify({"success": True, "message": "Phone numbers updated"})


# =====================================================================
# ENTITY TYPE MANAGER
# =====================================================================

@settings_bp.route("/entity-types")
@login_required
def list_entity_types():
    """List all entity definitions with counts."""
    definitions = EntityDefinition.query.filter_by(tenant_id=g.tenant.id)\
        .order_by(EntityDefinition.type).all()
    counts = {}
    for d in definitions:
        counts[d.id] = Entity.query.filter_by(
            tenant_id=g.tenant.id, definition_id=d.id, is_archived=False
        ).count()
    return render_template("entity_type_list.html", definitions=definitions, counts=counts)


@settings_bp.route("/entity-types/new", methods=["GET", "POST"])
@login_required
def new_entity_type():
    """Create a new entity type with a visual schema editor."""
    if request.method == "POST":
        data = request.form
        schema_raw = data.get("schema_json", "[]")
        statuses_raw = data.get("statuses_json", '["new","active","archived"]')

        try:
            schema = json.loads(schema_raw)
        except json.JSONDecodeError:
            flash("Invalid schema JSON", "error")
            return render_template("entity_type_form.html", definition=None)

        try:
            statuses = json.loads(statuses_raw)
        except json.JSONDecodeError:
            statuses = ["new", "active", "archived"]

        # Generate searchable_fields from schema fields marked searchable
        searchable = [f["name"] for f in schema if f.get("searchable")]

        definition = EntityDefinition(
            tenant_id=g.tenant.id,
            type=data.get("type", "").strip().lower(),
            label=data.get("label", "").strip(),
            label_plural=data.get("label_plural", "").strip(),
            icon=data.get("icon", "📋"),
            schema=schema,
            statuses=statuses,
            layout=data.get("layout", "table"),
            primary_field=data.get("primary_field", schema[0]["name"]) if schema else "name",
            searchable_fields=searchable,
            default_sort=data.get("default_sort", "created_at"),
        )
        db.session.add(definition)
        db.session.commit()
        flash(f"Entity type '{definition.label}' created", "success")
        return redirect(url_for("settings.list_entity_types"))

    return render_template("entity_type_form.html", definition=None)


@settings_bp.route("/entity-types/<int:def_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entity_type(def_id):
    """Edit an existing entity type."""
    definition = EntityDefinition.query.filter_by(
        id=def_id, tenant_id=g.tenant.id
    ).first_or_404()

    if request.method == "POST":
        data = request.form
        schema_raw = data.get("schema_json", "[]")
        statuses_raw = data.get("statuses_json", '[]')

        try:
            schema = json.loads(schema_raw)
        except json.JSONDecodeError:
            flash("Invalid schema JSON", "error")
            return render_template("entity_type_form.html", definition=definition)

        try:
            statuses = json.loads(statuses_raw)
        except json.JSONDecodeError:
            statuses = definition.statuses

        searchable = [f["name"] for f in schema if f.get("searchable")]

        definition.type = data.get("type", definition.type).strip().lower()
        definition.label = data.get("label", definition.label).strip()
        definition.label_plural = data.get("label_plural", "").strip()
        definition.icon = data.get("icon", definition.icon)
        definition.schema = schema
        definition.statuses = statuses
        definition.layout = data.get("layout", definition.layout)
        definition.primary_field = data.get("primary_field", schema[0]["name"]) if schema else definition.primary_field
        definition.searchable_fields = searchable
        definition.default_sort = data.get("default_sort", definition.default_sort)
        definition.is_active = data.get("is_active", "1") == "1"

        db.session.commit()
        flash(f"Entity type '{definition.label}' updated", "success")
        return redirect(url_for("settings.list_entity_types"))

    return render_template("entity_type_form.html", definition=definition)


@settings_bp.route("/entity-types/<int:def_id>/delete", methods=["POST"])
@login_required
def delete_entity_type(def_id):
    """Delete an entity type and all its entities."""
    definition = EntityDefinition.query.filter_by(
        id=def_id, tenant_id=g.tenant.id
    ).first_or_404()

    count = Entity.query.filter_by(definition_id=def_id, tenant_id=g.tenant.id).count()
    type_label = definition.label

    if count > 0:
        # Soft-delete: just deactivate
        definition.is_active = False
        db.session.commit()
        flash(f"Entity type '{type_label}' deactivated ({count} records preserved)", "warning")
    else:
        db.session.delete(definition)
        db.session.commit()
        flash(f"Entity type '{type_label}' deleted", "success")

    return redirect(url_for("settings.list_entity_types"))


@settings_bp.route("/entity-types/<int:def_id>/toggle", methods=["POST"])
@login_required
def toggle_entity_type(def_id):
    """Toggle entity type active/inactive."""
    definition = EntityDefinition.query.filter_by(
        id=def_id, tenant_id=g.tenant.id
    ).first_or_404()
    definition.is_active = not definition.is_active
    db.session.commit()
    status = "activated" if definition.is_active else "deactivated"
    flash(f"Entity type '{definition.label}' {status}", "success")
    return redirect(url_for("settings.list_entity_types"))


@settings_bp.route("/entity-types/<int:def_id>/field", methods=["POST"])
@login_required
def add_entity_field(def_id):
    """Add a field to an entity type schema (JSON API)."""
    definition = EntityDefinition.query.filter_by(
        id=def_id, tenant_id=g.tenant.id
    ).first_or_404()
    data = request.get_json(silent=True) or {}

    field = {
        "name": data.get("name", "").strip(),
        "label": data.get("label", "").strip(),
        "type": data.get("type", "text"),
        "required": data.get("required", False),
        "searchable": data.get("searchable", False),
        "options": data.get("options", []),
    }

    if not field["name"]:
        return jsonify({"error": "Field name required"}), 400

    # Check for duplicate
    if any(f["name"] == field["name"] for f in definition.schema):
        return jsonify({"error": f"Field '{field['name']}' already exists"}), 400

    definition.schema = definition.schema + [field]
    if field["searchable"] and field["name"] not in definition.searchable_fields:
        definition.searchable_fields = definition.searchable_fields + [field["name"]]
    db.session.commit()
    return jsonify({"success": True, "field": field, "schema": definition.schema})


@settings_bp.route("/entity-types/<int:def_id>/field/<field_name>", methods=["PUT", "DELETE"])
@login_required
def entity_field_ops(def_id, field_name):
    """Update or remove a field from an entity type schema."""
    definition = EntityDefinition.query.filter_by(
        id=def_id, tenant_id=g.tenant.id
    ).first_or_404()

    if request.method == "DELETE":
        definition.schema = [f for f in definition.schema if f.get("name") != field_name]
        definition.searchable_fields = [f for f in definition.searchable_fields if f != field_name]
        db.session.commit()
        return jsonify({"success": True, "schema": definition.schema})

    # PUT = update field
    data = request.get_json(silent=True) or {}
    for i, f in enumerate(definition.schema):
        if f.get("name") == field_name:
            for key in ("label", "type", "required", "searchable", "options"):
                if key in data:
                    definition.schema[i][key] = data[key]
            if data.get("searchable"):
                if field_name not in definition.searchable_fields:
                    definition.searchable_fields = definition.searchable_fields + [field_name]
            else:
                definition.searchable_fields = [f for f in definition.searchable_fields if f != field_name]
            break
    db.session.commit()
    return jsonify({"success": True, "schema": definition.schema})


@settings_bp.route("/entity-types/<int:def_id>/reorder-fields", methods=["POST"])
@login_required
def reorder_entity_fields(def_id):
    """Reorder fields in an entity type schema."""
    definition = EntityDefinition.query.filter_by(
        id=def_id, tenant_id=g.tenant.id
    ).first_or_404()
    data = request.get_json(silent=True) or {}
    field_names = data.get("field_names", [])

    if not field_names:
        return jsonify({"error": "field_names required"}), 400

    # Build new order, preserving any fields not in the list
    existing = {f["name"]: f for f in definition.schema}
    reordered = []
    for name in field_names:
        if name in existing:
            reordered.append(existing[name])
    # Append any fields that weren't in the reorder list
    for f in definition.schema:
        if f["name"] not in field_names:
            reordered.append(f)

    definition.schema = reordered
    db.session.commit()
    return jsonify({"success": True, "schema": definition.schema})