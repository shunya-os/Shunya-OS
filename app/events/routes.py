"""
Continuous Intelligence Runtime — Delta Events Endpoint
Provides delta-polling and SSE streaming over sh_objects changes.
"""

import time
import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, Response, current_app
from sqlalchemy import text

from app import db

events_bp = Blueprint("events", __name__, url_prefix="/api/v1")


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
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
    }


def _get_delta_objects(since: datetime):
    """Query sh_objects for objects created or updated after `since`."""
    created = (
        db.session.execute(
            text(
                "SELECT * FROM sh_objects WHERE created_at > :since "
                "AND is_deleted = false ORDER BY created_at ASC LIMIT 500"
            ),
            {"since": since},
        )
        .fetchall()
    )
    updated = (
        db.session.execute(
            text(
                "SELECT * FROM sh_objects WHERE updated_at > :since "
                "AND created_at <= :since AND is_deleted = false "
                "ORDER BY updated_at ASC LIMIT 500"
            ),
            {"since": since},
        )
        .fetchall()
    )
    return created, updated


@events_bp.route("/events", methods=["GET"])
def get_events():
    """
    GET /api/v1/events?since=<ISO timestamp>

    Returns delta objects created or updated after the given timestamp.
    """
    since_str = request.args.get("since", "")
    try:
        since = datetime.fromisoformat(since_str) if since_str else datetime.min
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid 'since' timestamp"}), 400

    # Ensure timezone-naive for DB comparison (Postgres stores naive UTC)
    if since.tzinfo is not None:
        since = since.replace(tzinfo=None)

    try:
        created_rows, updated_rows = _get_delta_objects(since)
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
def stream_events():
    """
    GET /api/v1/events/stream

    Server-Sent Events (SSE) endpoint that polls the database every 5 seconds
    and sends delta events as JSON.
    """
    since_str = request.args.get("since", "")

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
                created_rows, updated_rows = _get_delta_objects(since)
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
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )