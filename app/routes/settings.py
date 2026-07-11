"""Shunya OS — Settings & Admin."""
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app import db
from app.models import Tenant, TeamMember, EntityDefinition, Supplier
from app.routes.auth import login_required, admin_required

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("")
@login_required
def settings_page():
    suppliers = Supplier.query.filter_by(tenant_id=g.tenant.id)\
        .order_by(Supplier.created_at.desc()).limit(200).all()
    definitions = EntityDefinition.query.filter_by(tenant_id=g.tenant.id).all()
    team = TeamMember.query.filter_by(tenant_id=g.tenant.id).all()
    return render_template("settings.html", suppliers=suppliers,
                           definitions=definitions, team=team)


# ---------------------------------------------------------------------------
# Entity Definition Management (admin)
# ---------------------------------------------------------------------------

@settings_bp.route("/entity-types", methods=["POST"])
@login_required
def create_entity_type():
    """Create a new entity definition (Module Builder)."""
    data = request.get_json(silent=True) or request.form
    etype = data.get("type", "").strip().lower().replace(" ", "_")
    label = data.get("label", "").strip()
    icon = data.get("icon", "📋")

    if not etype or not label:
        return jsonify({"error": "Type and label required"}), 400

    existing = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=etype
    ).first()
    if existing:
        return jsonify({"error": f"Entity type '{etype}' already exists"}), 409

    schema_raw = data.get("schema", "[]")
    if isinstance(schema_raw, str):
        try:
            schema = json.loads(schema_raw)
        except json.JSONDecodeError:
            schema = []
    else:
        schema = schema_raw

    statuses_raw = data.get("statuses", "[]")
    if isinstance(statuses_raw, str):
        try:
            statuses = json.loads(statuses_raw)
        except json.JSONDecodeError:
            statuses = ["new"]
    else:
        statuses = statuses_raw

    definition = EntityDefinition(
        tenant_id=g.tenant.id,
        type=etype,
        label=label,
        label_plural=data.get("label_plural", f"{label}s"),
        icon=icon,
        schema=schema,
        statuses=statuses,
        layout=data.get("layout", "table"),
        primary_field=data.get("primary_field", "name"),
        searchable_fields=data.get("searchable_fields", []),
    )
    db.session.add(definition)
    db.session.commit()

    if request.is_json:
        return jsonify({"success": True, "definition": definition.to_dict()}), 201
    flash(f"Entity type '{label}' created", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/entity-types/<int:def_id>", methods=["PUT"])
@login_required
def update_entity_type(def_id):
    definition = EntityDefinition.query.filter_by(
        id=def_id, tenant_id=g.tenant.id
    ).first_or_404()
    data = request.get_json(silent=True) or request.form

    if "label" in data:
        definition.label = data["label"]
    if "icon" in data:
        definition.icon = data["icon"]
    if "layout" in data:
        definition.layout = data["layout"]
    if "schema" in data:
        definition.schema = json.loads(data["schema"]) if isinstance(data["schema"], str) else data["schema"]
    if "statuses" in data:
        definition.statuses = json.loads(data["statuses"]) if isinstance(data["statuses"], str) else data["statuses"]

    db.session.commit()
    return jsonify({"success": True})


@settings_bp.route("/entity-types/<int:def_id>", methods=["DELETE"])
@login_required
def delete_entity_type(def_id):
    definition = EntityDefinition.query.filter_by(
        id=def_id, tenant_id=g.tenant.id
    ).first_or_404()
    definition.is_active = False
    db.session.commit()
    return jsonify({"success": True})
