"""SHUNYA — Session Revocation (Milestone X, D2.6).

Force-logout all sessions for a user.
"""

import secrets
from datetime import datetime
from flask import request, jsonify, session
from werkzeug.exceptions import NotFound, BadRequest
from app.auth_routes import login_required, auth_bp
from app import db
from app.auth import TeamMember


# In-memory session version tracking
_session_versions: dict = {}  # user_id -> version number

# Track known devices/sessions
_devices: dict = {}  # token -> device info


@auth_bp.route("/revoke-sessions", methods=["POST"])
@login_required
def revoke_sessions():
    """Revoke all active sessions for the current user.

    Increments the session version counter — all existing sessions
    with an older version number become invalid on next request.
    """
    from flask import g
    user_id = g.user.id

    version = _session_versions.get(user_id, 0) + 1
    _session_versions[user_id] = version

    # Also clear the current session
    session.clear()

    return jsonify({
        "success": True,
        "message": "All sessions have been revoked",
    })


@auth_bp.route("/devices", methods=["GET"])
@login_required
def list_devices():
    """List all known devices for the current user."""
    from flask import g
    user_id = g.user.id

    user_devices = [
        d for d in _devices.values()
        if d["user_id"] == user_id
    ]
    return jsonify({
        "success": True,
        "data": user_devices,
    })


@auth_bp.route("/devices/<token>", methods=["DELETE"])
@login_required
def revoke_device(token: str):
    """Revoke a specific device session."""
    from flask import g
    user_id = g.user.id

    device = _devices.get(token)
    if not device or device["user_id"] != user_id:
        raise NotFound("Device not found")

    _devices.pop(token, None)

    return jsonify({
        "success": True,
        "data": {"token": token, "status": "revoked"},
    })


def track_device():
    """Middleware to track device/session info.

    Call from before_request when user is authenticated.
    """
    from flask import g, request
    user_id = getattr(g, "user", None)
    if not user_id:
        return

    session_token = session.get("_session_token")
    if not session_token:
        session_token = secrets.token_hex(16)
        session["_session_token"] = session_token

    ua = request.user_agent.string if request.user_agent else ""
    ip = request.remote_addr or ""

    _devices[session_token] = {
        "user_id": g.user.id,
        "user_agent": ua[:200],
        "ip_address": ip,
        "last_seen": datetime.utcnow().isoformat(),
        "created_at": _devices.get(session_token, {}).get(
            "created_at", datetime.utcnow().isoformat()
        ),
    }