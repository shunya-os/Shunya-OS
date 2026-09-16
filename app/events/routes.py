"""
Continuous Intelligence Runtime — Delta Events Endpoint
Provides delta-polling and SSE streaming over sh_objects changes.

Authorization boundary (R6B-2.7 Window 6)
-----------------------------------------
The delta stream is tenant AND workspace scoped. It previously read
``sh_objects WHERE created_at > :since`` with no organization, no workspace and
no identity filter, on an authenticated, permission-gated route — i.e. it
returned every tenant's objects (including their ``data`` payload) to any caller
holding ``knowledge.view``.

Both endpoints now resolve the caller's canonical scope
(``app/authz/workspace_context.authorized_workspace_ids``) and filter on
``organization_id`` + ``workspace_id IN (authorized)``. When the caller has no
authorized workspace the request is DENIED (403); an empty workspace set can
never reach SQL.
"""

import time
import json
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request, Response, current_app, stream_with_context
from sqlalchemy import bindparam, text

from app import db
from app.authz.decorators import require_permission
from app.authz.workspace_context import authorized_workspace_ids

events_bp = Blueprint("events", __name__, url_prefix="/api/v1")


def _iso(value):
    """ISO-8601 for a datetime, passthrough for a string, None for null.

    `SELECT *` through ``text()`` carries no column type metadata, so a SQLite
    TEXT-stored timestamp arrives as ``str`` rather than ``datetime``. Calling
    ``.isoformat()`` on it raised AttributeError and turned the delta endpoints
    into 500s once a caller actually reached them.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def _serialize(obj) -> dict:
    """Serialize a SQLAlchemy row to a dict safe for JSON."""
    return {
        "id": obj.id,
        "object_id": obj.object_id,
        "workspace_id": obj.workspace_id,
        "object_type": obj.object_type,
        "name": obj.name,
        "status": obj.status,
        "data": obj.data or {},
        "created_by": obj.created_by,
        "created_at": _iso(obj.created_at),
        "updated_at": _iso(obj.updated_at),
    }


def _caller_scope():
    """The caller's canonical (organization_id, authorized workspace ids).

    Returns ``None`` when the authorization context is not establishable — no
    authenticated identity, no resolved organization, or no authorized
    workspace. Callers MUST treat ``None`` as a denial.
    """
    identity = getattr(g, "identity_id", None)
    org_id = getattr(g, "current_org_id", None)
    if not identity or not org_id:
        return None
    ws_ids = authorized_workspace_ids(str(identity), int(org_id))
    if not ws_ids:
        return None
    return int(org_id), ws_ids


def _get_delta_objects(since: datetime, organization_id: int, ws_ids: list):
    """Query sh_objects for the caller's objects changed after `since`."""
    created_stmt = text(
        "SELECT * FROM sh_objects WHERE created_at > :since "
        "AND organization_id = :org_id AND workspace_id IN :ws_ids "
        "AND is_deleted = false ORDER BY created_at ASC LIMIT 500"
    ).bindparams(bindparam("ws_ids", expanding=True))
    updated_stmt = text(
        "SELECT * FROM sh_objects WHERE updated_at > :since "
        "AND created_at <= :since "
        "AND organization_id = :org_id AND workspace_id IN :ws_ids "
        "AND is_deleted = false ORDER BY updated_at ASC LIMIT 500"
    ).bindparams(bindparam("ws_ids", expanding=True))
    params = {"since": since, "org_id": organization_id, "ws_ids": list(ws_ids)}
    created = db.session.execute(created_stmt, params).fetchall()
    updated = db.session.execute(updated_stmt, params).fetchall()
    return created, updated


@events_bp.route("/events", methods=["GET"])
@require_permission("knowledge.view")
def get_events():
    """
    GET /api/v1/events?since=<ISO timestamp>

    Returns delta objects created or updated after the given timestamp,
    restricted to the caller's authorized organization and workspaces.
    """
    since_str = request.args.get("since", "")
    try:
        since = datetime.fromisoformat(since_str) if since_str else datetime.min
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid 'since' timestamp"}), 400

    # Ensure timezone-naive for DB comparison (Postgres stores naive UTC)
    if since.tzinfo is not None:
        since = since.replace(tzinfo=None)

    scope = _caller_scope()
    if scope is None:
        # No canonical authorization context: DENY rather than widen the query.
        return jsonify({"success": False,
                        "error": "No authorized workspace for this identity",
                        "code": "no_authorized_workspace"}), 403
    org_id, ws_ids = scope

    try:
        created_rows, updated_rows = _get_delta_objects(since, org_id, ws_ids)
    except Exception as exc:
        current_app.logger.error("Events delta query failed: %s", exc)
        return jsonify({"success": False, "error": "Database query failed"}), 500

    now_str = datetime.now(timezone.utc).isoformat(timespec="seconds")

    return jsonify({
        "success": True,
        "data": {
            "created": [_serialize(r) for r in created_rows],
            "updated": [_serialize(r) for r in updated_rows],
        },
        "timestamp": now_str,
    })


@events_bp.route("/events/stream", methods=["GET"])
@require_permission("knowledge.view")
def stream_events():
    """
    GET /api/v1/events/stream

    Server-Sent Events (SSE) endpoint that polls the database every 5 seconds
    and sends the caller's delta events as JSON.
    """
    since_str = request.args.get("since", "")

    # Resolve the caller's canonical scope INSIDE the request context, before the
    # stream starts. The generator below runs outside the request's authorization
    # evaluation, so it must capture the authorized scope rather than re-derive it
    # (and must never fall back to an unscoped query).
    scope = _caller_scope()
    if scope is None:
        return jsonify({"success": False,
                        "error": "No authorized workspace for this identity",
                        "code": "no_authorized_workspace"}), 403
    org_id, ws_ids = scope

    def generate():
        last_since = since_str
        while True:
            try:
                since = (
                    datetime.fromisoformat(last_since)
                    if last_since
                    else datetime.min
                )
            except (ValueError, TypeError):
                since = datetime.min

            if since.tzinfo is not None:
                since = since.replace(tzinfo=None)

            try:
                created_rows, updated_rows = _get_delta_objects(since, org_id, ws_ids)
                now_str = datetime.now(timezone.utc).isoformat(timespec="seconds")

                payload = {
                    "created": [_serialize(r) for r in created_rows],
                    "updated": [_serialize(r) for r in updated_rows],
                    "timestamp": now_str,
                }

                yield f"data: {json.dumps(payload)}\n\n"

                if created_rows or updated_rows:
                    last_since = now_str
            except Exception as exc:
                current_app.logger.error("SSE poll error: %s", exc)
                yield f"data: {json.dumps({'error': str(exc), 'timestamp': datetime.now(timezone.utc).isoformat(timespec='seconds')})}\n\n"

            time.sleep(5)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )