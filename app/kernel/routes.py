"""Universal Object Protocol — HTTP API Routes.

Exposes the canonical UniversalObject protocol through HTTP,
bridging the core protocol contract with SQL persistence.

ZERO-GAP-CONTINUATION-04B M10: B-P01 HTTP/API integration.
"""
import json
from flask import Blueprint, request, jsonify, session, g
from app import db
from app.authz.decorators import require_permission
from app.kernel.object import UniversalObject
from app.kernel.models import UOPObject


uop_bp = Blueprint("uop", __name__, url_prefix="/api/v1/uop")


def _resolve_tenant() -> int:
    """Resolve current tenant from the VERIFIED org context (B22).

    ``require_permission`` has already validated membership for the caller's
    organization and stored it in ``g.current_org_id``; client-supplied
    ``tenant_id`` (query/body/header) is NEVER trusted for scoping.
    """
    org_id = getattr(g, "current_org_id", None) or session.get("current_org_id")
    if org_id:
        return int(org_id)
    identity = session.get("identity_id") or session.get("user_id")
    if identity:
        from app.models import OrgMember
        om = OrgMember.query.filter_by(
            identity_id=str(identity), is_active=True
        ).first()
        if om:
            return om.organization_id
    return 0


def _resolve_identity() -> str:
    """Resolve current identity from session."""
    i = session.get("identity_id") or session.get("user_id")
    return str(i) if i else "system"


def _scoped_object(object_id: str):
    """Object only when it belongs to the caller's organization."""
    tenant_id = _resolve_tenant()
    if not tenant_id:
        return None
    return UOPObject.query.filter_by(
        object_id=object_id, tenant_id=tenant_id
    ).first()


@uop_bp.route("/objects", methods=["POST"])
@require_permission("rel.create")
def create_object():
    """Create a UniversalObject via the protocol.

    Request:
        {
            "object_type": "human|document|deal|...",
            "name": "Object Name",
            "space_id": "optional_workspace_id",
            "metadata": { ... }
        }
    Returns: protocol dict with object_id, status, etc.
    """
    data = request.get_json(silent=True) or {}
    tenant_id = _resolve_tenant()
    identity = _resolve_identity()

    obj = UniversalObject(
        object_type=data.get("object_type", "generic"),
        name=data.get("name", ""),
        tenant_id=tenant_id,
        space_id=data.get("space_id", ""),
        created_by=identity,
        updated_by=identity,
        metadata=data.get("metadata", {}),
    )

    # Persist
    model = UOPObject.from_protocol(obj)
    db.session.add(model)
    db.session.commit()

    return jsonify({
        "success": True,
        "object": model.to_protocol_dict(),
    }), 201


@uop_bp.route("/objects/<object_id>", methods=["GET"])
@require_permission("rel.view")
def get_object(object_id: str):
    """Retrieve a UniversalObject by its protocol object_id."""
    model = _scoped_object(object_id)
    if not model:
        return jsonify({"error": "Object not found"}), 404
    return jsonify({
        "success": True,
        "object": model.to_protocol_dict(),
    })


@uop_bp.route("/objects", methods=["GET"])
@require_permission("rel.view")
def list_objects():
    """List objects — ALWAYS scoped to the caller's organization (B22)."""
    object_type = request.args.get("object_type", "")
    space_id = request.args.get("space_id", "")
    tenant_id = _resolve_tenant()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    query = UOPObject.query.filter(
        UOPObject.is_archived.is_(False),
        UOPObject.tenant_id == tenant_id,
    )
    if object_type:
        query = query.filter(UOPObject.object_type == object_type)
    if space_id:
        query = query.filter(UOPObject.space_id == space_id)

    objects = query.order_by(UOPObject.created_at.desc()).limit(100).all()
    return jsonify({
        "success": True,
        "objects": [o.to_protocol_dict() for o in objects],
        "count": len(objects),
    })


@uop_bp.route("/objects/<object_id>/archive", methods=["POST"])
@require_permission("rel.edit")
def archive_object(object_id: str):
    """Archive (soft-delete) an object."""
    model = _scoped_object(object_id)
    if not model:
        return jsonify({"error": "Object not found"}), 404
    model.is_archived = True
    model.status = "archived"
    model.updated_by = _resolve_identity()
    db.session.commit()
    return jsonify({"success": True, "object": model.to_protocol_dict()})


@uop_bp.route("/objects/<object_id>/evidence", methods=["POST"])
@require_permission("rel.edit")
def add_evidence(object_id: str):
    """Add an evidence reference to an object."""
    model = _scoped_object(object_id)
    if not model:
        return jsonify({"error": "Object not found"}), 404
    data = request.get_json(silent=True) or {}
    ev_list = json.loads(model.evidence_json or "[]")
    ev_list.append({
        "evidence_id": data.get("evidence_id", ""),
        "evidence_type": data.get("evidence_type", ""),
        "captured_at": data.get("captured_at", ""),
    })
    model.evidence_json = json.dumps(ev_list)
    model.updated_by = _resolve_identity()
    db.session.commit()
    return jsonify({"success": True, "object": model.to_protocol_dict()})