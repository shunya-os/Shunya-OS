from flask import Blueprint, request, jsonify, session
from app import db
from app.objects.service import ObjectService
from app.objects.models import Object
from app.objects.legacy_models import ShunyaObject, Workspace
from datetime import datetime
import uuid

objects_bp = Blueprint("objects", __name__, url_prefix="/api/v1/objects")


@objects_bp.route("/", methods=["POST"])
def create():
    """Create a business object. Accepts both legacy and SPA onboarding format.

    Request (SPA frontend):
        { "name": "Q4 Strategy Doc", "object_type": "Document" }
    Returns:
        { "success": true, "object_id": "uuid", "object_type": "Document" }
    """
    data = request.json or {}
    name = data.get("name", data.get("object_type", "Object"))
    object_type = data.get("object_type", data.get("type", "generic"))

    # Resolve the user's workspace from session
    identity_id = session.get("identity_id") or session.get("user_id") or "system"
    if identity_id and isinstance(identity_id, int):
        identity_id = str(identity_id)

    # Find an existing workspace, or use the first active one
    workspace = Workspace.query.filter_by(status="active").first()
    workspace_id = workspace.id if workspace else "spc_default"

    # Create in sh_objects (production store used by workspace/reality_engine)
    obj = ShunyaObject(
        object_id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        object_type=object_type,
        name=name,
        status="active",
        data={"name": name, "type": object_type},
        created_by=identity_id,
    )
    db.session.add(obj)
    db.session.commit()

    return jsonify({
        "success": True,
        "object_id": obj.object_id,
        "object_type": obj.object_type,
        "name": obj.name,
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