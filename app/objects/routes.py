from flask import Blueprint, request, jsonify
from app.objects.service import ObjectService
from app.objects.models import Object

objects_bp = Blueprint("objects", __name__, url_prefix="/api/v1/objects")


@objects_bp.route("/", methods=["POST"])
def create():
    data = request.json or {}

    obj = ObjectService.create_object(
        object_type=data.get("type", "generic"),
        state=data.get("state", {})
    )

    return jsonify({
        "id": obj.id,
        "type": obj.object_type,
        "state": obj.state
    })


@objects_bp.route("/<int:object_id>", methods=["PATCH"])
def update(object_id):
    obj = Object.query.get_or_404(object_id)

    updated = ObjectService.update_state(
        obj,
        request.json or {}
    )

    return jsonify({
        "id": updated.id,
        "state": updated.state
    })