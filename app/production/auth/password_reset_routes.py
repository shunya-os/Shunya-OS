"""SHUNYA — Password Reset (Milestone X, D2.2).

Email-based password reset with secure tokens.
"""

import secrets
from datetime import datetime, timedelta

from flask import request, jsonify
from werkzeug.exceptions import NotFound, BadRequest

from app import db
from app.auth import TeamMember
from app.auth_routes import login_required, auth_bp


# In-memory token store for now
_reset_tokens: dict = {}  # token -> {user_id, email, expires_at, used}


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Request a password reset email."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()

    if not email:
        raise BadRequest("'email' is required")

    user = TeamMember.query.filter_by(email=email).first()
    if not user:
        # Don't reveal whether email exists — return 200 regardless
        return jsonify({
            "success": True,
            "message": "If the email exists, a reset link has been sent.",
        })

    token = _generate_token()
    _reset_tokens[token] = {
        "user_id": user.id,
        "email": email,
        "expires_at": datetime.utcnow() + timedelta(hours=1),
        "used": False,
        "created_at": datetime.utcnow(),
    }

    # In production, send email here
    # For now, return the token in the response for testing
    return jsonify({
        "success": True,
        "message": "If the email exists, a reset link has been sent.",
        # TODO: Remove this in production — only for development/testing
        "_reset_token": token,
    })


@auth_bp.route("/reset-password/<token>", methods=["GET"])
def verify_reset_token(token: str):
    """Verify a password reset token."""
    entry = _reset_tokens.get(token)
    if not entry:
        raise NotFound("Invalid or expired reset token")

    if entry["used"]:
        raise NotFound("Reset token has already been used")

    if datetime.utcnow() > entry["expires_at"]:
        _reset_tokens.pop(token, None)
        raise NotFound("Reset token has expired")

    return jsonify({
        "success": True,
        "message": "Token is valid",
        "data": {"email": entry["email"]},
    })


@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token: str):
    """Reset password using a valid token."""
    entry = _reset_tokens.get(token)
    if not entry:
        raise NotFound("Invalid or expired reset token")

    if entry["used"]:
        raise NotFound("Reset token has already been used")

    if datetime.utcnow() > entry["expires_at"]:
        _reset_tokens.pop(token, None)
        raise NotFound("Reset token has expired")

    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if not password or len(password) < 6:
        raise BadRequest("'password' must be at least 6 characters")

    user = db.session.get(TeamMember, entry["user_id"])
    if not user:
        raise NotFound("User not found")

    user.set_password(password)
    entry["used"] = True
    db.session.commit()

    # Clean up used token
    _reset_tokens.pop(token, None)

    return jsonify({
        "success": True,
        "message": "Password has been reset successfully",
    })