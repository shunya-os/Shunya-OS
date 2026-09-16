from flask import Blueprint, request, jsonify, session
from core.object_service import get_object_service
from app.authz.decorators import require_permission
from app.authz.workspace_context import (
    OwnershipContextError,
    resolve_current_organization,
    resolve_current_workspace,
)


objects_bp = Blueprint("objects", __name__, url_prefix="/api/v1/objects")


def _identity_id():
    identity = session.get("identity_id") or session.get("user_id")
    return str(identity) if identity else None


def _deny(exc: OwnershipContextError):
    return jsonify({"success": False, "error": exc.reason, "code": exc.code}), 403


@objects_bp.route("/", methods=["POST"])
@require_permission("rel.create")
def create():
    """Create a business object through the canonical object authority.

    Ownership is resolved by the canonical boundary only — organization and
    workspace are never selected arbitrarily and never defaulted.
    """
    identity_id = _identity_id()
    if not identity_id:
        return jsonify({"error": "Authentication required", "success": False}), 401

    data = request.json or {}
    name = data.get("name", data.get("object_type", "Object"))
    object_type = data.get("object_type", data.get("type", "generic"))

    try:
        organization_id = resolve_current_organization(
            identity_id, request.headers.get("X-Organization-Id")
        )
        workspace_id = resolve_current_workspace(
            identity_id, organization_id,
            data.get("workspace_id") or request.headers.get("X-Workspace-Id"),
        )
    except OwnershipContextError as exc:
        return _deny(exc)

    svc = get_object_service()
    obj = svc.create(
        object_type=object_type,
        name=name,
        organization_id=organization_id,
        data={"name": name, "type": object_type, "created_via": "http_route"},
        created_by=identity_id,
        workspace_id=workspace_id,
        identity_id=identity_id,
    )

    return jsonify({
        "success": True,
        "object_id": obj.get("object_id", ""),
        "id": obj["id"],
        "object_type": obj["object_type"],
        "name": obj["name"],
        "organization_id": obj["organization_id"],
    })


@objects_bp.route("/<int:object_id>", methods=["PATCH"])
@require_permission("rel.edit")
def update(object_id):
    """Update a canonical object (tenant + workspace scoped)."""
    identity_id = _identity_id()
    if not identity_id:
        return jsonify({"error": "Authentication required", "success": False}), 401

    try:
        organization_id = resolve_current_organization(
            identity_id, request.headers.get("X-Organization-Id")
        )
        workspace_id = resolve_current_workspace(
            identity_id, organization_id,
            request.headers.get("X-Workspace-Id"),
        )
    except OwnershipContextError as exc:
        return _deny(exc)

    svc = get_object_service()
    existing = svc.get(object_id, organization_id=organization_id,
                       identity_id=identity_id)
    if not existing or existing.get("workspace_id") != workspace_id:
        return jsonify({"error": "Not found"}), 404

    updates = request.json or {}
    ok = svc.update(object_id, organization_id=organization_id,
                    identity_id=identity_id, **updates)
    if not ok:
        return jsonify({"error": "Update failed — cross-tenant or not found"}), 403
    updated = svc.get(object_id, organization_id=organization_id,
                      identity_id=identity_id)
    if not updated:
        return jsonify({"error": "Not found after update"}), 500
    return jsonify({"id": updated["id"],
                    "state": {k: v for k, v in updated.items() if k != "id"}})
