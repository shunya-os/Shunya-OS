"""SHUNYA — Generic Object Creation (SPA onboarding).

Handles POST /api/v1/objects — the SPA calls this during onboarding
to create the first business object.

Routes are registered on production_bp (url_prefix = /api/v1).
"""

import uuid
from datetime import datetime

from flask import jsonify, request, g
from app import db
from app.production import production_bp
from app.auth_routes import login_required
from app.founder.models import FounderObject, FounderSpace


@production_bp.route("/objects", methods=["POST"])
@login_required
def create_generic_object():
    """Create a business object.

    SPA sends: {name: str, object_type: str}
    Returns: {success: bool, data: {object_id, name, type}}
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    object_type = data.get("object_type", "").strip()

    if not name or not object_type:
        return jsonify({"success": False, "error": "Name and object_type are required."}), 400

    # Clean emoji prefixes from object_type (e.g. "📄 Document" -> "Document")
    clean_type = object_type.split(" ", 1)[-1] if " " in object_type else object_type

    # Find or create a default space for this user
    identity_id = str(g.user.id)
    space = FounderSpace.query.filter_by(identity_id=identity_id).first()
    if not space:
        space = FounderSpace(
            space_id=f"space_{uuid.uuid4().hex[:16]}",
            name="My Workspace",
            identity_id=identity_id,
            space_type="personal",
            status="active",
            member_count=1,
        )
        db.session.add(space)
        db.session.flush()

    obj_id = f"obj_{uuid.uuid4().hex[:16]}"
    obj = FounderObject(
        object_id=obj_id,
        space_id=space.space_id,
        name=name,
        object_type=clean_type,
        content="",
        status="active",
        created_by=identity_id[:12],
    )
    db.session.add(obj)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "object_id": obj.object_id,
            "name": obj.name,
            "type": clean_type,
        },
        "object_id": obj.object_id,
    }), 201