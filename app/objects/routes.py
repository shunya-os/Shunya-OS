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


@objects_bp.route("/<int:object_id>", methods=["GET"])
@require_permission("knowledge.view")
def get(object_id):
    """Read a single canonical object by integer ID."""
    identity_id = _identity_id()
    if not identity_id:
        return jsonify({"error": "Authentication required", "success": False}), 401
    try:
        organization_id = resolve_current_organization(
            identity_id, request.headers.get("X-Organization-Id")
        )
    except OwnershipContextError as exc:
        return _deny(exc)
    svc = get_object_service()
    obj = svc.get(object_id, organization_id=organization_id,
                  identity_id=identity_id)
    if not obj:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"id": obj["id"], "state": obj})


@objects_bp.route("/<int:object_id>/lifecycle", methods=["POST"])
@require_permission("rel.edit")
def lifecycle(object_id):
    """Apply a lifecycle action to an object.

    Explicit action dispatch — no dynamic getattr from user-controlled input.
    Legal transitions:
      ACTIVE    → archive → ARCHIVED,  trash → TRASHED
      ARCHIVED  → restore → ACTIVE,    trash → TRASHED
      TRASHED   → recover → ACTIVE
      any       → permanent_delete → (removed from DB)
    """
    identity_id = _identity_id()
    if not identity_id:
        return jsonify({"error": "Authentication required", "success": False}), 401
    data = request.json or {}
    action = data.get("action")
    if action not in ("archive", "restore", "trash", "recover", "permanent_delete"):
        return jsonify({"error": f"Unknown lifecycle action: {action}",
                        "valid": ["archive","restore","trash","recover","permanent_delete"],
                        "success": False}), 400
    try:
        organization_id = resolve_current_organization(
            identity_id, request.headers.get("X-Organization-Id")
        )
    except OwnershipContextError as exc:
        return _deny(exc)

    svc = get_object_service()

    # Explicit dispatch — not getattr(svc, action).
    LIFECYCLE_DISPATCH = {
        "archive": svc.archive,
        "restore": svc.restore,
        "trash": svc.trash,
        "recover": svc.recover,
        "permanent_delete": svc.permanent_delete,
    }
    handler = LIFECYCLE_DISPATCH[action]
    ok = handler(object_id, organization_id=organization_id,
                 identity_id=identity_id)
    if not ok:
        return jsonify({"error": f"Lifecycle action '{action}' failed — "
                        "cross-tenant, wrong state, or not found",
                        "success": False}), 403
    updated = svc.get(object_id, organization_id=organization_id,
                      identity_id=identity_id) if action != "permanent_delete" else None
    return jsonify({"success": True,
                    "action": action,
                    "state": updated})


# ---------------------------------------------------------------------------
# Read surfaces (GET)
#
# These close a real product defect: the frontend already reads
#   GET /api/v1/objects/types        (object inventory)
#   GET /api/v1/objects/<type>       (objects of one type)
#   GET /api/v1/objects?limit=|&q=   (collection / search)
# but only POST was mounted for those paths, so every one of them failed
# (405/404) and the workspace showed a FALSE EMPTY STATE - it told the human
# there was no data when data existed.
#
# Authorization is the canonical boundary: identity from the session,
# organization resolved by resolve_current_organization, and every read routed
# through ObjectService so workspace membership is enforced by the same
# predicate as writes. Missing context fails closed (403), never falls back to
# a default organization or workspace.
# ---------------------------------------------------------------------------

_MAX_LIMIT = 500


def _read_context():
    """(identity_id, organization_id) or an error response."""
    identity_id = _identity_id()
    if not identity_id:
        return None, None, (jsonify({"error": "Authentication required",
                                     "success": False}), 401)
    try:
        organization_id = resolve_current_organization(
            identity_id, request.headers.get("X-Organization-Id")
        )
    except OwnershipContextError as exc:
        return None, None, (_deny(exc),)
    return identity_id, organization_id, None


def _requested_limit(default: int = 100) -> int:
    try:
        limit = int(request.args.get("limit", default))
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, _MAX_LIMIT))


def _requested_offset() -> int:
    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0
    return max(0, offset)


@objects_bp.route("/types", methods=["GET"])
@require_permission("knowledge.view")
def types_inventory():
    """Object types the caller can see, with counts.

    Shape (consumed verbatim by the workspace, knowledge browser and living
    store): ``{"success": true, "data": {"<object_type>": <count>, ...}}``.
    """
    identity_id, organization_id, error = _read_context()
    if error:
        return error
    svc = get_object_service()
    try:
        counts = svc.count_by_type(organization_id=organization_id,
                                   identity_id=identity_id)
    except OwnershipContextError as exc:
        return _deny(exc)
    except ValueError:
        return jsonify({"error": "Ownership context incomplete", "success": False}), 400
    return jsonify({"success": True, "data": counts, "counts": counts,
                    "total": sum(counts.values())})


@objects_bp.route("/<object_type>", methods=["GET"])
@require_permission("knowledge.view")
def list_by_type(object_type):
    """Objects of one type within the caller's authorized workspaces.

    ``total`` is the exact count for the type from the canonical service (not
    ``len(objects)``), so a truncated page cannot be mistaken for a full list.
    """
    identity_id, organization_id, error = _read_context()
    if error:
        return error
    limit, offset = _requested_limit(), _requested_offset()
    svc = get_object_service()
    try:
        objects = svc.get_by_type(object_type, organization_id=organization_id,
                                  identity_id=identity_id, limit=limit, offset=offset)
        counts = svc.count_by_type(organization_id=organization_id,
                                   identity_id=identity_id)
    except OwnershipContextError as exc:
        return _deny(exc)
    except ValueError:
        return jsonify({"error": "Ownership context incomplete", "success": False}), 400
    total = counts.get(object_type, len(objects))
    payload = {"objects": objects, "total": total,
               "page": (offset // limit) + 1, "per_page": limit,
               "has_more": offset + len(objects) < total}
    return jsonify({"success": True, "data": payload, **payload})


@objects_bp.route("", methods=["GET"])
@objects_bp.route("/", methods=["GET"])
@require_permission("knowledge.view")
def collection():
    """List or search every object the caller may read.

    ``?q=`` searches by name (canonical ``ObjectService.search``); otherwise the
    authorized collection is returned by recency. ``data`` is an array (the
    search surface expects a list) and the same objects are also exposed as the
    top-level ``objects`` key (the export surface expects that).
    """
    identity_id, organization_id, error = _read_context()
    if error:
        return error
    limit, offset = _requested_limit(), _requested_offset()
    query = (request.args.get("q") or "").strip()
    svc = get_object_service()
    try:
        if query:
            objects = svc.search(query, organization_id=organization_id,
                                 identity_id=identity_id, limit=limit)
        else:
            objects = svc.list_authorized(organization_id=organization_id,
                                          identity_id=identity_id,
                                          limit=limit, offset=offset)
    except OwnershipContextError as exc:
        return _deny(exc)
    except ValueError:
        return jsonify({"error": "Ownership context incomplete", "success": False}), 400
    return jsonify({"success": True, "data": objects, "objects": objects,
                    "total": len(objects), "page": (offset // limit) + 1,
                    "per_page": limit, "query": query})
