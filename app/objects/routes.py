from flask import Blueprint, request, jsonify, session
from app import db
from app.objects.legacy_models import Workspace
from core.object_service import get_object_service


objects_bp = Blueprint("objects", __name__, url_prefix="/api/v1/objects")


def _resolve_tenant_id() -> int | None:
    """Resolve the canonical tenant (organization) id from the session."""
    org_id = session.get("current_org_id")
    if org_id:
        return int(org_id)
    identity = session.get("identity_id") or session.get("user_id")
    if identity:
        from app.models import OrgMember
        om = OrgMember.query.filter_by(identity_id=str(identity), is_active=True).first()
        if om:
            return om.organization_id
    return None


@objects_bp.route("/", methods=["POST"])
def create():
    """Create a business object through the canonical object authority.

    Request (SPA frontend):
        { "name": "Q4 Strategy Doc", "object_type": "Document" }
    Returns:
        { "success": true, "object_id": "uuid", "id": 123, "object_type": "Document", "organization_id": 7 }
    """
    data = request.json or {}
    name = data.get("name", data.get("object_type", "Object"))
    object_type = data.get("object_type", data.get("type", "generic"))

    identity_id = session.get("identity_id") or session.get("user_id") or "system"
    if identity_id and isinstance(identity_id, int):
        identity_id = str(identity_id)

    organization_id = _resolve_tenant_id()

    # Workspace is org-scoped: pick the user's org workspace
    from app.authz.decorators import _resolve_org_workspace_ids
    workspace_ids = _resolve_org_workspace_ids(organization_id) if organization_id else []
    workspace = None
    if workspace_ids:
        workspace = Workspace.query.filter(
            Workspace.id.in_(workspace_ids), Workspace.status == "active"
        ).first()
    if not workspace:
        workspace = Workspace.query.filter_by(status="active").first()
    workspace_id = workspace.id if workspace else "spc_default"

    # Create through the canonical object authority (core/object_service.py)
    # This writes to sh_objects with proper organization_id, workspace_id chain
    svc = get_object_service()
    obj = svc.create(
        object_type=object_type,
        name=name,
        organization_id=organization_id or 0,
        data={"name": name, "type": object_type, "created_via": "http_route"},
        created_by=identity_id,
        workspace_id=workspace_id,
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
def update(object_id):
    """Update a canonical object (tenant-scoped). Routes through canonical service."""
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    svc = get_object_service()
    # Check existence + verify it's in the correct org
    existing = svc.get(object_id)
    if not existing:
        return jsonify({"error": "Not found"}), 404
    if org_id and existing.get("organization_id") and existing["organization_id"] != org_id:
        return jsonify({"error": "Forbidden"}), 403
    # Update through canonical service (which enforces org isolation)
    updates = request.json or {}
    ok = svc.update(object_id, organization_id=org_id or 0, **updates)
    if not ok:
        return jsonify({"error": "Update failed — cross-tenant or not found"}), 403
    updated = svc.get(object_id)
    if not updated:
        return jsonify({"error": "Not found after update"}), 500
    return jsonify({"id": updated["id"], "state": {k: v for k, v in updated.items() if k not in ("id",)}})