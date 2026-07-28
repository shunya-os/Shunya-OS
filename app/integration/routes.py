"""SHUNYA M6 — Connected Business Routes.

Integration settings, notification management, and connectivity APIs.
"""
from flask import Blueprint, jsonify, request, session

integration_bp = Blueprint("integration", __name__, url_prefix="/api/v1/integration")


def _founder_required() -> bool:
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    return bool(user_id and identity_id)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@integration_bp.route("/notifications", methods=["GET"])
def api_get_notifications():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    from app.integration.service import get_notifications
    notifs = get_notifications(identity_id=identity_id, unread_only=unread_only)
    return jsonify({"success": True, "data": notifs, "count": len(notifs)})


@integration_bp.route("/notifications/unread-count", methods=["GET"])
def api_unread_count():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.integration.service import get_unread_count
    count = get_unread_count(identity_id=identity_id)
    return jsonify({"success": True, "data": {"unread_count": count}})


@integration_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
def api_mark_read(notif_id: int):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.integration.service import mark_as_read
    result = mark_as_read(notif_id)
    return jsonify({"success": result})


@integration_bp.route("/notifications/read-all", methods=["POST"])
def api_mark_all_read():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.integration.service import mark_all_as_read
    count = mark_all_as_read(identity_id=identity_id)
    return jsonify({"success": True, "data": {"marked_read": count}})


# ---------------------------------------------------------------------------
# Notification preferences
# ---------------------------------------------------------------------------

@integration_bp.route("/notifications/preferences", methods=["GET"])
def api_get_preferences():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.integration.service import get_preferences
    return jsonify({"success": True, "data": get_preferences(identity_id)})


@integration_bp.route("/notifications/preferences", methods=["PUT"])
def api_update_preferences():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    data = request.get_json(silent=True) or {}
    from app.integration.service import update_preferences
    result = update_preferences(
        identity_id=identity_id,
        email_notifications=data.get("email_notifications"),
        in_app_notifications=data.get("in_app_notifications"),
        digest_frequency=data.get("digest_frequency"),
        quiet_hours_start=data.get("quiet_hours_start"),
        quiet_hours_end=data.get("quiet_hours_end"),
    )
    return jsonify({"success": True, "data": result})


# ---------------------------------------------------------------------------
# Integrations
# ---------------------------------------------------------------------------

@integration_bp.route("/connections", methods=["GET"])
def api_get_connections():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.integration.service import get_connections
    return jsonify({"success": True, "data": get_connections(identity_id)})


@integration_bp.route("/connections/<provider>", methods=["DELETE"])
def api_remove_connection(provider: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.integration.service import remove_connection
    result = remove_connection(identity_id=identity_id, provider=provider)
    return jsonify({"success": result})


@integration_bp.route("/providers", methods=["GET"])
def api_list_providers():
    """List available integration providers."""
    return jsonify({
        "success": True,
        "data": [
            {"id": "gmail", "name": "Gmail", "type": "email", "icon": "✉️"},
            {"id": "outlook", "name": "Outlook", "type": "email", "icon": "📧"},
            {"id": "google_calendar", "name": "Google Calendar", "type": "calendar", "icon": "📅"},
            {"id": "outlook_calendar", "name": "Outlook Calendar", "type": "calendar", "icon": "📅"},
        ],
    })