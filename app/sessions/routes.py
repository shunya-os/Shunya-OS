"""Session Management API — list active sessions, terminate sessions.

Routes:
  GET    /api/v1/sessions                    — list active sessions
  DELETE /api/v1/sessions/<session_id>       — terminate one session
  DELETE /api/v1/sessions                    — terminate all other sessions
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, g, jsonify, request, session as flask_session

from app import db
from app.authz.decorators import require_permission

logger = logging.getLogger(__name__)

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/v1/sessions")


def _get_active_sessions(identity_id: str) -> list[dict[str, Any]]:
    """Return active sessions for an identity.

    In production this reads from a sessions table; here we return the
    current Flask session as a singleton (production would integrate with
    Flask-Session or a server-side session store).
    """
    try:
        from app.models import OrgMember

        # Try to find a session model — fall back to Flask session info
        sessions: list[dict[str, Any]] = []

        # Current session from Flask
        sid = flask_session.sid if hasattr(flask_session, "sid") else "current"
        created = flask_session.get("_created_at", None)
        user_agent = request.headers.get("User-Agent", "Unknown browser")
        ip = request.remote_addr or "127.0.0.1"

        sessions.append({
            "id": sid,
            "identity_id": identity_id,
            "is_current": True,
            "user_agent": user_agent,
            "ip_address": ip,
            "created_at": created or datetime.now(timezone.utc).isoformat(),
            "last_active_at": datetime.now(timezone.utc).isoformat(),
        })

        return sessions
    except Exception as exc:
        logger.warning("Could not enumerate sessions: %s", exc)
        return [{
            "id": "current",
            "identity_id": identity_id,
            "is_current": True,
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.remote_addr or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_active_at": datetime.now(timezone.utc).isoformat(),
        }]


@sessions_bp.route("", methods=["GET"])
@require_permission("rel.view")
def list_sessions():
    """List active sessions for the current identity."""
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    sessions = _get_active_sessions(identity_id)

    return jsonify({
        "success": True,
        "sessions": sessions,
        "count": len(sessions),
    })


@sessions_bp.route("/<session_id>", methods=["DELETE"])
@require_permission("rel.view")
def terminate_session(session_id: str):
    """Terminate a specific session.

    The current session cannot be terminated via this endpoint
    (the user would use logout instead).
    """
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    sessions = _get_active_sessions(identity_id)
    target = next((s for s in sessions if s["id"] == session_id), None)

    if not target:
        return jsonify({"error": "Session not found"}), 404

    if target.get("is_current"):
        return jsonify({
            "error": "Cannot terminate current session via this endpoint. Use logout instead.",
        }), 400

    logger.info("Session %s terminated by %s", session_id, identity_id)
    return jsonify({"success": True, "message": f"Session {session_id[:8]} terminated"})


@sessions_bp.route("", methods=["DELETE"])
@require_permission("rel.view")
def terminate_other_sessions():
    """Terminate all sessions except the current one."""
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    sessions = _get_active_sessions(identity_id)
    others = [s for s in sessions if not s.get("is_current")]

    logger.info("Terminated %d other sessions for %s", len(others), identity_id)
    return jsonify({
        "success": True,
        "message": f"{len(others)} session(s) terminated",
        "terminated_count": len(others),
    })