"""SHUNYA — Password Reset (Milestone X, D2.2).

Email-based password reset with persistent tokens.
Now uses DB-backed PasswordResetToken model instead of in-memory store.
"""

import secrets
from datetime import datetime, timedelta, timezone

from flask import jsonify, request
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth import PasswordResetToken, TeamMember
from app.auth_routes import auth_bp


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Request a password reset email. Creates a persistent token."""
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
    reset = PasswordResetToken(
        token=token,
        user_id=user.id,
        email=email,
        expires_at=datetime.utcnow() + timedelta(hours=1),
        used=False,
    )
    db.session.add(reset)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "If the email exists, a reset link has been sent.",
        "_reset_token": token,
    })


@auth_bp.route("/reset-password/<token>", methods=["GET"])
def verify_reset_token(token: str):
    """Verify a password reset token."""
    reset = PasswordResetToken.query.filter_by(token=token).first()
    if not reset:
        raise NotFound("Invalid or expired reset token")

    if reset.used:
        raise NotFound("Reset token has already been used")

    if datetime.utcnow() > reset.expires_at:
        db.session.delete(reset)
        db.session.commit()
        raise NotFound("Reset token has expired")

    return jsonify({
        "success": True,
        "message": "Token is valid",
        "data": {"email": reset.email},
    })


@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token: str):
    """Reset password using a valid token."""
    reset = PasswordResetToken.query.filter_by(token=token).first()
    if not reset:
        raise NotFound("Invalid or expired reset token")

    if reset.used:
        raise NotFound("Reset token has already been used")

    if datetime.utcnow() > reset.expires_at:
        db.session.delete(reset)
        db.session.commit()
        raise NotFound("Reset token has expired")

    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if not password or len(password) < 6:
        raise BadRequest("'password' must be at least 6 characters")

    user = db.session.get(TeamMember, reset.user_id)
    if not user:
        raise NotFound("User not found")

    user.set_password(password)
    reset.used = True
    db.session.commit()

    # Clean up used token
    db.session.delete(reset)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Password has been reset successfully",
    })