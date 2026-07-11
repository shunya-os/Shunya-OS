"""Shunya OS — Module Builder routes.

Users describe a business workflow → AI generates entity definition → Review → Save.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, g
from app import db
from app.routes.auth import login_required
from app.shunya.module_builder import ModuleBuilder, preview_from_description, save_from_preview

module_builder_bp = Blueprint("module_builder", __name__, url_prefix="/modules")


@module_builder_bp.route("")
@login_required
def builder_page():
    """Main module builder page."""
    return render_template("module_builder.html")


@module_builder_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    """Generate an entity definition from natural language description."""
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()

    if not description or len(description) < 10:
        return jsonify({"error": "Please describe your workflow in at least 10 characters"}), 400

    try:
        preview = preview_from_description(description)
        return jsonify({
            "success": True,
            "preview": preview,
        })
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500


@module_builder_bp.route("/create", methods=["POST"])
@login_required
def create():
    """Save a generated definition (after user review)."""
    data = request.get_json(silent=True) or {}

    # Check for duplicate entity type
    from app.models import EntityDefinition
    entity_type = data.get("type", "").strip().lower()
    existing = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first()

    if existing:
        return jsonify({
            "error": f"Entity type '{entity_type}' already exists. Edit it in Settings instead.",
            "entity_type_id": existing.id
        }), 409

    try:
        definition = save_from_preview(data, g.tenant.id)
        return jsonify({
            "success": True,
            "entity_type_id": definition.id,
            "redirect": url_for("settings.edit_entity_type", def_id=definition.id),
        })
    except Exception as e:
        return jsonify({"error": f"Save failed: {str(e)}"}), 500


@module_builder_bp.route("/enhance", methods=["POST"])
@login_required
def enhance():
    """Refine an existing preview with additional description."""
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    current_preview = data.get("current_preview", {})

    if not description:
        return jsonify({"error": "Description required"}), 400

    # Re-run generation with the new description
    preview = preview_from_description(description)

    # Merge: keep existing field choices where they overlap, add new ones
    existing_fields = {f["name"]: f for f in current_preview.get("schema", [])}
    merged_schema = list(existing_fields.values())

    for new_field in preview.get("schema", []):
        if new_field["name"] not in existing_fields:
            merged_schema.append(new_field)

    preview["schema"] = merged_schema
    return jsonify({"success": True, "preview": preview})