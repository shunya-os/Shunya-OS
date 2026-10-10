"""Profile Blueprint — user profile management API.

Endpoints:
  GET    /api/v1/profile              — get (or auto-create) current user's profile
  PUT    /api/v1/profile              — update profile fields
  PUT    /api/v1/profile/password     — change password
  POST   /api/v1/profile/avatar       — upload avatar image
  GET    /api/v1/profile/preferences  — get user preferences
  PUT    /api/v1/profile/preferences  — update user preferences
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify, request, g, session, current_app

from app import db
from app.runtime_config import uploads_dir

logger = logging.getLogger(__name__)

profile_bp = Blueprint("profile", __name__, url_prefix="/api/v1/profile")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_identity() -> str:
    """Extract the canonical identity_id from request context."""
    return str(
        session.get("identity_id")
        or session.get("user_id")
        or getattr(g, "identity_id", None)
        or request.headers.get("X-Identity-Id", "")
    )


def _get_or_create_profile(identity_id: str):
    """Return the profile for identity_id, creating a default one if absent."""
    from .models import UserProfile

    profile = db.session.get(UserProfile, identity_id)
    if profile is None:
        profile = UserProfile(identity_id=identity_id)
        db.session.add(profile)
        db.session.commit()
    return profile


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@profile_bp.route("", methods=["GET"])
def api_get_profile():
    """GET /api/v1/profile — return current user's profile (auto-create)."""
    identity_id = _resolve_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    profile = _get_or_create_profile(identity_id)
    return jsonify({"success": True, "data": profile.to_dict()})


@profile_bp.route("", methods=["PUT"])
def api_update_profile():
    """PUT /api/v1/profile — update profile fields."""
    identity_id = _resolve_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    from .models import UserProfile

    profile = _get_or_create_profile(identity_id)
    profile.update_from_dict(data)
    db.session.commit()

    return jsonify({"success": True, "data": profile.to_dict()})


@profile_bp.route("/password", methods=["PUT"])
def api_change_password():
    """PUT /api/v1/profile/password — change password.

    Requires old_password + new_password. Identity must have a TeamMember
    record with a valid password hash.
    """
    identity_id = _resolve_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    old_password = (data.get("old_password") or "").strip()
    new_password = (data.get("new_password") or "").strip()

    if not old_password or not new_password:
        return jsonify(
            {"success": False, "error": "old_password and new_password are required"}
        ), 400

    if len(new_password) < 8:
        return jsonify(
            {"success": False, "error": "New password must be at least 8 characters"}
        ), 400

    # Resolve TeamMember from the current user
    from app.auth import TeamMember
    from werkzeug.security import check_password_hash, generate_password_hash

    user_id = session.get("user_id")
    if user_id:
        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
        tm = db.session.get(TeamMember, user_id) if user_id else None
    else:
        tm = TeamMember.query.filter_by(identity_id=identity_id).first()

    if not tm:
        return jsonify(
            {"success": False, "error": "User account not found"}
        ), 404

    if not check_password_hash(tm.password_hash, old_password):
        return jsonify(
            {"success": False, "error": "Current password is incorrect"}
        ), 403

    tm.password_hash = generate_password_hash(new_password)
    db.session.commit()

    logger.info("Password changed for identity=%s", identity_id)
    return jsonify({"success": True, "message": "Password updated successfully"})


@profile_bp.route("/avatar", methods=["POST"])
def api_upload_avatar():
    """POST /api/v1/profile/avatar — upload avatar image (multipart)."""
    identity_id = _resolve_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    if "avatar" not in request.files:
        return jsonify({"success": False, "error": "No avatar file provided"}), 400

    file = request.files["avatar"]
    if file.filename == "" or not file.filename:
        return jsonify({"success": False, "error": "Empty filename"}), 400

    # Validate file type
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        return jsonify(
            {
                "success": False,
                "error": "File type not allowed. Use JPEG, PNG, WebP, or GIF.",
            }
        ), 400

    # Save to uploads/avatar_ID.ext
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".png"  # safe fallback

    avatar_filename = f"avatar_{identity_id}{ext}"
    avatar_dir = uploads_dir()
    avatar_path = os.path.join(avatar_dir, avatar_filename)
    file.save(avatar_path)

    # Update profile with avatar_url pointing to the static serve
    avatar_url = f"/uploads/{avatar_filename}"
    from .models import UserProfile

    profile = _get_or_create_profile(identity_id)
    profile.avatar_url = avatar_url
    db.session.commit()

    logger.info("Avatar uploaded for identity=%s: %s", identity_id, avatar_filename)
    return jsonify({"success": True, "data": {"avatar_url": avatar_url}})


@profile_bp.route("/preferences", methods=["GET"])
def api_get_preferences():
    """GET /api/v1/profile/preferences — return user preferences."""
    identity_id = _resolve_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    profile = _get_or_create_profile(identity_id)
    return jsonify({"success": True, "data": profile.preferences_dict()})


@profile_bp.route("/preferences", methods=["PUT"])
def api_update_preferences():
    """PUT /api/v1/profile/preferences — update preferences."""
    identity_id = _resolve_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    prefs = {}
    for key in ("timezone", "locale", "date_format", "theme_preference"):
        if key in data:
            prefs[key] = data[key]

    if not prefs:
        return jsonify(
            {"success": False, "error": "No preference fields provided"}
        ), 400

    from .models import UserProfile

    profile = _get_or_create_profile(identity_id)
    for key, value in prefs.items():
        setattr(profile, key, value)
    db.session.commit()

    return jsonify({"success": True, "data": profile.preferences_dict()})