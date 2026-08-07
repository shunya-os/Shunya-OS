"""
SHUNYA LX-02 — Reality Engine API Routes

Transport-agnostic endpoints for the Canonical Reality Engine.

Key routes:
    GET /api/v1/reality           — Full reality snapshot (polling mode)
    GET /api/v1/reality/stream    — SSE stream of reality events
    GET /api/v1/reality/projection/:workspace_type — Workspace-specific projection
    GET /api/v1/reality/object/:object_id — Full reality context for one object
"""

import json
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, Response, current_app, stream_with_context

from app.reality_engine.engine import get_reality_engine
from app.graph_universal.traversal import GraphQueryEngine
from app.graph_universal.entity import get_store as get_entity_store
from app.graph_universal.relationship import get_store as get_rel_store

reality_bp = Blueprint("reality", __name__, url_prefix="/api/v1/reality")


def _require_identity():
    """Extract identity from session or header."""
    from flask import session, g
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    identity_id = session.get("identity_id") or session.get("user_id")
    if identity_id:
        return identity_id
    identity_id = request.headers.get("X-Identity-Id")
    return identity_id


# ═════════════════════════════════════════════════════════════════════
# Reality Snapshot — The canonical endpoint
# ═════════════════════════════════════════════════════════════════════


DEMO_IDENTITY = "sid_demo_tenant"


@reality_bp.route("", methods=["GET"])
def get_reality():
    """GET /api/v1/reality

    Returns the canonical reality snapshot. Every frontend surface subscribes
    to this reality — not to individual APIs.

    Unauthenticated requests resolve to the Demonstration Tenant through the
    same Identity → Tenant → Reality pipeline used by authenticated users.
    The Reality Engine projects Reality from tenant data identically for all workspaces.

    Query params:
        workspace_type (optional): Filter projection for a specific workspace.
        workspace_id (optional): The workspace ID for the projection.
    """
    identity_id = _require_identity() or DEMO_IDENTITY
    engine = get_reality_engine()
    workspace_type = request.args.get("workspace_type", "founder")
    workspace_id = request.args.get("workspace_id", "default")

    if workspace_type:
        projection = engine.build_projection(
            workspace_type=workspace_type,
            workspace_id=workspace_id,
            identity_id=identity_id,
        )
        return jsonify({"success": True, "data": projection.to_dict()})
    else:
        snapshot = engine.build_snapshot(identity_id=identity_id)
        return jsonify({"success": True, "data": snapshot.to_dict()})


# ═════════════════════════════════════════════════════════════════════
# Reality SSE Stream — Continuous push
# ═════════════════════════════════════════════════════════════════════


@reality_bp.route("/stream", methods=["GET"])
def stream_reality():
    """GET /api/v1/reality/stream

    SSE stream of reality events. The frontend subscribes once and receives
    continuous updates. Falls back to polling without any frontend changes.

    This is a transport — the Reality Engine abstraction means the frontend
    never knows whether it's receiving data via SSE (this stream) or polling
    (the GET endpoint above).
    """
    identity_id = _require_identity()
    if not identity_id:
        identity_id = DEMO_IDENTITY

    workspace_type = request.args.get("workspace_type", "founder")
    workspace_id = request.args.get("workspace_id", "default")
    engine = get_reality_engine()

    def generate():
        last_data = None
        while True:
            try:
                projection = engine.build_projection(
                    workspace_type=workspace_type,
                    workspace_id=workspace_id,
                    identity_id=identity_id,
                )
                data = projection.to_dict()

                # Only push if something changed
                if data != last_data:
                    last_data = data
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    yield f": keepalive\n\n"
            except Exception as exc:
                yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

            time.sleep(5)  # Check every 5 seconds

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ═════════════════════════════════════════════════════════════════════
# Projection — Workspace-specific view
# ═════════════════════════════════════════════════════════════════════


@reality_bp.route("/projection/<workspace_type>", methods=["GET"])
def get_projection(workspace_type: str):
    """GET /api/v1/reality/projection/:workspace_type

    Get a workspace-specific projection of the canonical reality.
    The underlying reality is identical — only the projection changes.

    Example: /api/v1/reality/projection/finance
             /api/v1/reality/projection/travel
             /api/v1/reality/projection/founder
    """
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    workspace_id = request.args.get("workspace_id", "default")
    engine = get_reality_engine()

    projection = engine.build_projection(
        workspace_type=workspace_type,
        workspace_id=workspace_id,
        identity_id=identity_id,
    )
    return jsonify({"success": True, "data": projection.to_dict()})


# ═════════════════════════════════════════════════════════════════════
# Object Reality Context — Full context for one object
# ═════════════════════════════════════════════════════════════════════


@reality_bp.route("/object/<object_id>", methods=["GET"])
def get_object_reality(object_id: str):
    """GET /api/v1/reality/object/:object_id

    Returns the complete reality context for a single business object.

    This answers "What happened to my Bali proposal?" — SHUNYA reconstructs
    the entire execution history, relationships, commitments, and next actions
    for any object.

    This is LX-02 §10 (Outcome Continuity): every outcome persists until
    completed, cancelled, superseded, or permanently abandoned.
    """
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    engine = get_reality_engine()
    graph = GraphQueryEngine()
    rel_store = get_rel_store()
    entity_store = get_entity_store()

    # Get entity from universal graph
    entity = entity_store.get(object_id)
    entity_info = entity.to_dict() if entity else {"entity_id": object_id, "name": object_id, "entity_type": "unknown"}

    # Get relationships
    relationships = rel_store.get_for_entity(object_id)

    # Get neighborhood (depth 2)
    try:
        neighborhood = graph.neighbors(object_id, max_depth=2)
    except Exception:
        neighborhood = {}

    # Get reality events for this object
    snapshot = engine.build_snapshot(identity_id=identity_id)
    object_events = [
        e.to_dict() for e in snapshot.events
        if e.object_id == object_id
    ]

    return jsonify({
        "success": True,
        "data": {
            "entity": entity_info,
            "relationships": [r.to_dict() for r in relationships],
            "neighborhood": neighborhood,
            "events": object_events,
            "attention_items": [
                a for a in snapshot.attention_queue
                if a.get("source_id") == object_id
            ],
            "snapshot_timestamp": snapshot.timestamp,
        },
    })


# ═════════════════════════════════════════════════════════════════════
# Health check
# ═════════════════════════════════════════════════════════════════════


@reality_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "data": {
            "engine": "reality",
            "status": "active",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    })