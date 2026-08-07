from flask import Blueprint, jsonify
from app.core.entity import Entity
from app.core.timeline import get_entity_timeline

entity_bp = Blueprint("entity_api", __name__, url_prefix="/api/v1/entities")


@entity_bp.route("/", methods=["GET"])
def list_entities():
    entities = Entity.query.all()
    return jsonify([
        {"id": e.id, "type": e.type, "state": e.state}
        for e in entities
    ])


@entity_bp.route("/<int:entity_id>", methods=["GET"])
def get_entity(entity_id):
    e = Entity.query.get_or_404(entity_id)
    return jsonify({
        "id": e.id,
        "type": e.type,
        "state": e.state,
        "data": e.data
    })


@entity_bp.route("/<int:entity_id>/timeline", methods=["GET"])
def timeline(entity_id):
    return jsonify(get_entity_timeline(entity_id))