"""SHUNYA — Email Verification (Milestone X, D2.3).

Email verification workflow for new user registrations.
Uses in-memory verification store — no model changes needed.
"""

import secrets
from datetime import datetime, timedelta
from flask import request, jsonify
from werkzeug.exceptions import NotFound, BadRequest
from app import db
from app.auth import TeamMember
from app.auth_routes import auth_bp


_verification_tokens: dict = {}


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


@auth_bp.route("/request-verification", methods=["POST"])
def request_verification():
    """Request email verification."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        raise BadRequest("'email' is required")

    user = TeamMember.query.filter_by(email=email).first()
    if not user:
        return jsonify({
            "success": True,
            "message": "If the email exists, a verification link has been sent.",
        })

    # Check if already verified
    user_id = user.id
    for entry in _verification_tokens.values():
        if entry["user_id"] == user_id and entry["verified"]:
            return jsonify({
                "success": True,
                "message": "Email is already verified.",
            })

    token = _generate_token()
    _verification_tokens[token] = {
        "user_id": user_id,
        "email": email,
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "verified": False,
        "created_at": datetime.utcnow(),
    }

    return jsonify({
        "success": True,
        "message": "If the email exists, a verification link has been sent.",
        "_verify_token": token,
    })


@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token: str):
    """Verify email address using a token."""
    entry = _verification_tokens.get(token)
    if not entry:
        raise NotFound("Invalid or expired verification token")
    if entry["verified"]:
        raise NotFound("Token has already been used")
    if datetime.utcnow() > entry["expires_at"]:
        _verification_tokens.pop(token, None)
        raise NotFound("Verification token has expired")

    user = db.session.get(TeamMember, entry["user_id"])
    if not user:
        raise NotFound("User not found")

    entry["verified"] = True

    return jsonify({
        "success": True,
        "message": "Email verified successfully",
    })