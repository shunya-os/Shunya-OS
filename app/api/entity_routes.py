from flask import Blueprint, jsonify, request
from app import db
from app.core.entity import Entity
from app.core.timeline import get_entity_timeline

entity_bp = Blueprint("entity_api", __name__, url_prefix="/api/v1/entities")

# Schema definitions for dynamic entity types
ENTITY_TYPE_SCHEMAS = {
    "customer": {
        "fields": [
            {"key": "name", "label": "Name", "type": "text", "required": True},
            {"key": "email", "label": "Email", "type": "email", "required": False},
            {"key": "phone", "label": "Phone", "type": "text", "required": False},
            {"key": "company", "label": "Company", "type": "text", "required": False},
            {"key": "industry", "label": "Industry", "type": "select", "options": ["Technology", "Finance", "Healthcare", "Education", "Manufacturing", "Other"], "required": False},
            {"key": "notes", "label": "Notes", "type": "textarea", "required": False},
        ]
    },
    "contact": {
        "fields": [
            {"key": "first_name", "label": "First Name", "type": "text", "required": True},
            {"key": "last_name", "label": "Last Name", "type": "text", "required": True},
            {"key": "email", "label": "Email", "type": "email", "required": False},
            {"key": "phone", "label": "Phone", "type": "text", "required": False},
            {"key": "role", "label": "Role", "type": "text", "required": False},
            {"key": "notes", "label": "Notes", "type": "textarea", "required": False},
        ]
    },
    "project": {
        "fields": [
            {"key": "name", "label": "Project Name", "type": "text", "required": True},
            {"key": "description", "label": "Description", "type": "textarea", "required": False},
            {"key": "status", "label": "Status", "type": "select", "options": ["Planning", "Active", "On Hold", "Completed", "Cancelled"], "required": True},
            {"key": "budget", "label": "Budget", "type": "number", "required": False},
            {"key": "deadline", "label": "Deadline", "type": "date", "required": False},
        ]
    },
}


@entity_bp.route("/", methods=["GET"])
def list_entities():
    entities = Entity.query.all()
    return jsonify([
        {"id": e.id, "type": e.type, "state": e.state, "data": e.data, "code": e.code, "status": e.status}
        for e in entities
    ])


@entity_bp.route("/<int:entity_id>", methods=["GET"])
def get_entity(entity_id):
    e = Entity.query.get_or_404(entity_id)
    return jsonify({
        "id": e.id,
        "type": e.type,
        "state": e.state,
        "data": e.data,
        "code": e.code,
        "status": e.status,
    })


@entity_bp.route("/", methods=["POST"])
def create_entity():
    data = request.get_json() or {}
    entity_type = data.get("type", "customer")
    entity_data = data.get("data", {})
    entity = Entity(
        tenant_id=data.get("tenant_id", 1),
        type=entity_type,
        state=data.get("state", "active"),
        data=entity_data,
        status=data.get("status", "new"),
        code=data.get("code", ""),
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify({"id": entity.id, "type": entity.type, "data": entity.data}), 201


@entity_bp.route("/<int:entity_id>", methods=["PATCH"])
def update_entity(entity_id):
    e = Entity.query.get_or_404(entity_id)
    data = request.get_json() or {}
    if "type" in data:
        e.type = data["type"]
    if "state" in data:
        e.state = data["state"]
    if "data" in data:
        e.data = {**(e.data or {}), **data["data"]}
    if "status" in data:
        e.status = data["status"]
    db.session.commit()
    return jsonify({"id": e.id, "type": e.type, "data": e.data})


@entity_bp.route("/types", methods=["GET"])
def list_types():
    """Return available entity types with their field schemas."""
    return jsonify({
        "types": [
            {"id": k, "name": k.title(), "fields": v["fields"]}
            for k, v in ENTITY_TYPE_SCHEMAS.items()
        ]
    })


@entity_bp.route("/<int:entity_id>/timeline", methods=["GET"])
def timeline(entity_id):
    return jsonify(get_entity_timeline(entity_id))