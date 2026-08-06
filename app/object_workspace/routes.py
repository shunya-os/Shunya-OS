"""EP-03 — Universal Living Object Workspace API.

Single endpoint: GET /api/v1/workspace/<object_id>
Returns the complete workspace for any Living Object.
"""

from flask import Blueprint, jsonify, request, g

from app.object_workspace.workspace import build_object_detail

workspace_bp = Blueprint("workspace", __name__, url_prefix="/api/v1/workspace")


def _require_identity():
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    identity_id = request.headers.get("X-Identity-Id")
    return identity_id


@workspace_bp.route("/<object_id>", methods=["GET"])
def get_object_workspace(object_id: str):
    """GET /api/v1/workspace/<object_id> — full workspace for any Living Object.

    Returns a dynamically composed workspace based on object type,
    runtime capabilities, relationships, available actions, evidence,
    and execution state. No switch statements. No object-specific pages.
    """
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    object_type = request.args.get("type", "other")
    name = request.args.get("name", object_id)

    workspace = build_object_detail(
        object_id=object_id,
        object_type=object_type,
        name=name,
        identity_id=identity_id,
    )

    return jsonify({"success": True, "data": workspace})