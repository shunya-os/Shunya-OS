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
from app.reality_engine.sse_stream import get_sse_manager, serialize_event, serialize_heartbeat
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

    Non-blocking SSE stream delivering real-time events from the canonical
    event bus to authenticated frontend clients.

    *** SECURITY: Only session-authenticated identities are accepted. ***
    *** The X-Identity-Id header is NOT trusted for SSE.              ***

    Each client gets a thread-safe queue. Events are filtered by tenant_id
    for cross-tenant isolation. Heartbeats keep the connection alive when
    no events are flowing. Timeout after 120s of inactivity.

    This replaces the previous blocking-generator (time.sleep(5)) that
    caused gunicorn worker timeout deaths.
    """
    from flask import session, g

    # ---- Auth: ONLY trust session-authenticated identities --------------
    # X-Identity-Id header is NOT accepted for SSE — a client-supplied
    # header must not be treated as proof of identity without validation
    # by an already trusted authentication layer.
    identity_id = session.get("identity_id") or session.get("user_id")
    tenant_id = session.get("tenant_id") or session.get("current_org_id", 0)
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    workspace_id = request.args.get("workspace_id", None)
    if workspace_id:
        try:
            workspace_id = int(workspace_id)
        except (ValueError, TypeError):
            workspace_id = None

    manager = get_sse_manager()
    client = manager.register_client(tenant_id, identity_id, workspace_id=int(workspace_id) if workspace_id else None)

    def generate():
        last_heartbeat = time.time()
        try:
            while True:
                events = client.drain(timeout=30.0)
                if events:
                    for event in events:
                        yield serialize_event(event)
                    last_heartbeat = time.time()
                else:
                    # Send heartbeat every 15s to keep connection alive
                    if time.time() - last_heartbeat > 15:
                        yield serialize_heartbeat()
                        last_heartbeat = time.time()
        except GeneratorExit:
            pass
        finally:
            manager.unregister_client(client.client_id)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
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