from flask import Blueprint, request, jsonify, session, g, current_app
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
        "provenance": obj.get("provenance"),
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
        # ``_deny`` already returns ``(response, 403)``. The previous
        # ``(_deny(exc),)`` wrapped that in a 1-tuple, so ``return error`` handed
        # Flask an invalid view return value: every ambiguity/denial on this path
        # surfaced as HTTP 500 instead of the intended 403 (measured with a two-
        # organization identity and no selected organization).
        return None, None, _deny(exc)
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
    from app.objects.provenance import annotate
    objects = [annotate(o) for o in objects]
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
    from app.objects.provenance import annotate
    objects = [annotate(o) for o in objects]
    return jsonify({"success": True, "data": objects, "objects": objects,
                    "total": len(objects), "page": (offset // limit) + 1,
                    "per_page": limit, "query": query})


@objects_bp.route("/first-object-state", methods=["GET"])
@require_permission("knowledge.view")
def first_object_state():
    """Authoritative empty-workspace predicate for the first-object CTA (G1.18).

    Organization-level existence read, not a workspace listing: an organization
    that exists but has no provisioned workspace must still get a truthful
    answer instead of an authorization error that the UI would have to treat as
    "unknown". ``require_permission`` has already validated an active membership
    and the permission, and set ``g.current_org_id`` (organization resolution
    does not require a workspace).

    Status contract — the caller can distinguish every case:
      200 — authoritative answer, ``has_business_data`` true or false
      400 — no organization context (unknown; the UI must not claim empty)
      401 — unauthenticated
      403 — authenticated but not entitled
      503 — the read failed (never reported as an empty workspace)

    The definition of the predicate, the stores it reads and the lifecycle
    semantics live in ``app/objects/first_object_state.py``. This route performs
    no writes and creates no projection of any record.
    """
    from app.objects.first_object_state import get_first_object_state

    organization_id = getattr(g, "current_org_id", None)
    if not organization_id:
        return jsonify({
            "success": False,
            "code": "no_organization_context",
            "error": "No organization context — first-object state unknown",
        }), 400

    try:
        state = get_first_object_state(int(organization_id))
    except Exception:  # noqa: BLE001 — a failed read is not an empty workspace
        current_app.logger.exception(
            "first-object-state read failed for organization %s", organization_id
        )
        return jsonify({
            "success": False,
            "error": "First-object state unavailable",
        }), 503

    return jsonify({"success": True, **state})


# ---------------------------------------------------------------------------
# Object read surfaces keyed by the STRING object_id (legacy living workspace
# ids like UUIDs). The living-workspace viewer previously called
#   GET /api/v1/workspace/<object_id>
# which is a workspace route — object ids are not workspace ids, so every
# open failed ("Failed to load workspace"). These routes resolve through
# ObjectService (get_by_object_id, with integer fallback) so authorization
# stays on the canonical boundary.
# ---------------------------------------------------------------------------


def _resolve_object_for_read(object_id: str, svc, identity_id: str | None, organization_id: int | None):
    """Resolve an object by int id or string object_id, scoped + authorized."""
    if not identity_id or not organization_id:
        return None
    if str(object_id).isdigit():
        return svc.get(int(object_id), organization_id=organization_id,
                       identity_id=identity_id)
    return svc.get_by_object_id(str(object_id), organization_id=organization_id,
                                identity_id=identity_id)


@objects_bp.route("/by-id/<object_id>", methods=["GET"])
@require_permission("knowledge.view")
def get_by_object_id(object_id: str):
    """Read a canonical object by its string object_id (or numeric id)."""
    identity_id, organization_id, error = _read_context()
    if error:
        return error
    assert identity_id is not None and organization_id is not None
    svc = get_object_service()
    obj = _resolve_object_for_read(object_id, svc, identity_id, organization_id)
    if not obj:
        return jsonify({"error": "Not found", "success": False}), 404
    from app.objects.provenance import annotate
    return jsonify({"success": True, "data": annotate(obj)})


def _object_edge_payload(obj: dict) -> dict:
    """Cannonical node payload for graph/insight consumers."""
    return {
        "id": obj.get("object_id") or str(obj.get("id", "")),
        "type": obj.get("object_type", ""),
        "name": obj.get("name", ""),
        "status": obj.get("status", ""),
        "createdAt": obj.get("created_at") or "",
        "updatedAt": obj.get("updated_at") or "",
    }


@objects_bp.route("/<object_id>/graph", methods=["GET"])
@require_permission("knowledge.view")
def object_graph(object_id: str):
    """Relationship edges for an object.

    There is no canonical object-to-object edge store yet; edges are derived
    from relationship hints persisted on the object's metadata (``data`` dict
    or legacy ``relationships`` list). Empty arrays are returned honestly when
    no edges exist — the graph runtime treats that as a valid empty graph
    instead of 404ing.
    """
    identity_id, organization_id, error = _read_context()
    if error:
        return error
    assert identity_id is not None and organization_id is not None
    svc = get_object_service()
    obj = _resolve_object_for_read(object_id, svc, identity_id, organization_id)
    if not obj:
        return jsonify({"error": "Not found", "success": False}), 404

    nodes = [_object_edge_payload(obj)]
    edges = []

    metadata = obj.get("data") or {}
    stored_rels = metadata.get("relationships", []) if isinstance(metadata, dict) else []
    if not stored_rels and isinstance(obj.get("relationships"), list):
        stored_rels = obj["relationships"]

    for rel in stored_rels or []:
        if not isinstance(rel, dict):
            continue
        target_id = rel.get("object_id") or rel.get("id")
        if not target_id:
            continue
        target_type = rel.get("object_type") or rel.get("type") or ""
        target_name = rel.get("name") or ""
        nodes.append({
            "id": str(target_id), "type": target_type, "name": target_name,
            "status": rel.get("status", ""), "createdAt": "", "updatedAt": "",
        })
        edges.append({
            "id": f"edge_{obj.get('object_id')}_{rel.get('relation_type', 'relates_to')}_{target_id}",
            "fromId": obj.get("object_id") or str(obj.get("id", "")),
            "fromType": obj.get("object_type", ""),
            "toId": str(target_id),
            "toType": target_type,
            "type": rel.get("relation_type", "relates_to"),
            "confidence": float(rel.get("confidence", 1.0) or 1.0),
            "source": rel.get("source", "system"),
            "createdAt": obj.get("created_at") or "",
        })

    return jsonify({"success": True, "data": {"nodes": nodes, "edges": edges},
                    "nodes": nodes, "edges": edges})


@objects_bp.route("/<object_id>/timeline", methods=["GET"])
@require_permission("knowledge.view")
def object_timeline(object_id: str):
    """Timeline events for an object.

    Sources (honest, real): legacy ActivityLog rows whose lead_id matches the
    object id (proposal/invoice objects map to leads), rel_timeline entries
    referencing this object, plus synthetic created/updated events from the
    object row itself. Returns [] when nothing exists.
    """
    identity_id, organization_id, error = _read_context()
    if error:
        return error
    assert identity_id is not None and organization_id is not None
    svc = get_object_service()
    obj = _resolve_object_for_read(object_id, svc, identity_id, organization_id)
    if not obj:
        return jsonify({"error": "Not found", "success": False}), 404

    events = []
    obj_pk = obj.get("id")

    try:
        from app.models import ActivityLog
        rows = (ActivityLog.query
                .filter_by(lead_id=obj_pk)
                .order_by(ActivityLog.created_at.desc())
                .limit(50).all()) if obj_pk else []
        for r in rows:
            events.append({
                "id": f"activity_{r.id}", "type": "activity",
                "title": r.action, "description": r.detail or "",
                "timestamp": r.created_at.isoformat() if r.created_at else "",
                "source": "system",
                "commitment_impact": None,
            })
    except Exception:
        pass  # legacy table unavailable — timeline degrades to synthetic events

    try:
        from app.relationship.models import TimelineEntry
        trefs = (TimelineEntry.query
                 .filter_by(reference_id=obj_pk)
                 .order_by(TimelineEntry.event_time.desc())
                 .limit(50).all()) if obj_pk else []
        for t in trefs:
            events.append({
                "id": f"rel_{t.id}", "type": t.event_type,
                "title": t.title or t.event_type,
                "description": t.description or "",
                "timestamp": t.event_time.isoformat() if t.event_time else "",
                "source": "system",
                "commitment_impact": None,
            })
    except Exception:
        pass

    created_at = obj.get("created_at")
    updated_at = obj.get("updated_at")
    if created_at:
        events.append({
            "id": "created", "type": "created", "title": "Object created",
            "description": "", "timestamp": created_at, "source": "system",
            "commitment_impact": None,
        })
    if updated_at and updated_at != created_at:
        events.append({
            "id": "updated", "type": "updated", "title": "Object updated",
            "description": "", "timestamp": updated_at, "source": "system",
            "commitment_impact": None,
        })

    events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    events = events[:100]
    return jsonify({"success": True, "events": events, "data": events})


@objects_bp.route("/<object_id>/insights", methods=["GET"])
@require_permission("knowledge.view")
def object_insights(object_id: str):
    """Deterministic insights for an object.

    Aggregates real data: object counts by type in the caller's organization,
    same-type recency, and timeline activity. No fabricated AI text — this is
    a summary surface the intelligence runtime can consume.
    """
    identity_id, organization_id, error = _read_context()
    if error:
        return error
    assert identity_id is not None and organization_id is not None
    svc = get_object_service()
    obj = _resolve_object_for_read(object_id, svc, identity_id, organization_id)
    if not obj:
        return jsonify({"error": "Not found", "success": False}), 404

    insights = []
    try:
        counts = svc.count_by_type(organization_id=organization_id,
                                   identity_id=identity_id)
    except Exception:
        counts = {}
    total = sum(counts.values()) if counts else 0
    type_count = counts.get(obj.get("object_type"), 0)

    created_at = obj.get("created_at") or ""
    updated_at = obj.get("updated_at") or ""

    insights.append({
        "type": "summary", "confidence": "high", "source": "system",
        "title": f"{obj.get('name', 'Object')} overview",
        "body": (f"{obj.get('object_type', 'object')} in {obj.get('status', 'active')} "
                 f"state"
                 + (f", created {created_at[:10]}" if created_at else "")),
        "timestamp": updated_at or created_at,
    })

    if total:
        insights.append({
            "type": "observation", "confidence": "high", "source": "system",
            "title": "Organization footprint",
            "body": (f"This object is one of {total} objects across this "
                     f"organization ({type_count} of type "
                     f"'{obj.get('object_type')}')."),
            "timestamp": updated_at or created_at,
        })

    try:
        from app.models import ActivityLog
        activity_count = ActivityLog.query.filter_by(lead_id=obj.get("id")).count() if obj.get("id") else 0
    except Exception:
        activity_count = 0

    insights.append({
        "type": "recommendation", "confidence": "medium", "source": "system",
        "title": activity_count and "Activity detected" or "No tracked activity",
        "body": (f"{activity_count} tracked activity event(s) for this object."
                 if activity_count else
                 "No lifecycle events are tracked for this object yet. "),
        "timestamp": updated_at or created_at,
    })

    return jsonify({"success": True, "insights": insights, "data": insights})
