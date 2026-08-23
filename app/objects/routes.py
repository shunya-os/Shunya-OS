from flask import Blueprint, request, jsonify, session
from app import db
from app.objects.service import ObjectService
from app.objects.models import Object
from app.objects.legacy_models import ShunyaObject, Workspace
from datetime import datetime
import uuid

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
    """Create a business object. Accepts both legacy and SPA onboarding format.

    Request (SPA frontend):
        { "name": "Q4 Strategy Doc", "object_type": "Document" }
    Returns:
        { "success": true, "object_id": "uuid", "object_type": "Document" }
    """
    data = request.json or {}
    name = data.get("name", data.get("object_type", "Object"))
    object_type = data.get("object_type", data.get("type", "generic"))

    # Resolve the user's workspace from session (org-scoped)
    identity_id = session.get("identity_id") or session.get("user_id") or "system"
    if identity_id and isinstance(identity_id, int):
        identity_id = str(identity_id)

    tenant_id = _resolve_tenant_id()

    # Workspace is org-scoped: pick the user's org workspace
    from app.authz.decorators import _resolve_org_workspace_ids
    workspace_ids = _resolve_org_workspace_ids(tenant_id) if tenant_id else []
    workspace = None
    if workspace_ids:
        workspace = Workspace.query.filter(
            Workspace.id.in_(workspace_ids), Workspace.status == "active"
        ).first()
    if not workspace:
        workspace = Workspace.query.filter_by(status="active").first()
    workspace_id = workspace.id if workspace else "spc_default"

    # Create in sh_objects (production store used by workspace/reality_engine)
    obj = ShunyaObject(
        object_id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        object_type=object_type,
        name=name,
        status="active",
        data={"name": name, "type": object_type, "tenant_id": tenant_id},
        created_by=identity_id,
    )
    db.session.add(obj)
    db.session.flush()

    # Also write the legacy objects row with tenant_id (isolation column)
    legacy = Object(object_type=object_type, state={"name": name, "type": object_type}, tenant_id=tenant_id)
    db.session.add(legacy)
    db.session.commit()

    return jsonify({
        "success": True,
        "object_id": obj.object_id,
        "id": legacy.id,
        "object_type": obj.object_type,
        "name": obj.name,
        "tenant_id": tenant_id,
    })


@objects_bp.route("/<int:object_id>", methods=["PATCH"])
def update(object_id):
    """Update a business object (tenant-scoped)."""
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    obj = Object.query.get_or_404(object_id)
    if org_id and obj.tenant_id and obj.tenant_id != org_id:
        return jsonify({"error": "Forbidden"}), 403
    updated = ObjectService.update_state(obj, request.json or {})
    return jsonify({"id": updated.id, "state": updated.state})