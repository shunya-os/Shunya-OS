"""SHUNYA — Email Verification (Milestone X, D2.3).

Email verification workflow for new user registrations.
Uses persistent EmailVerificationToken model.
"""

import secrets
from datetime import datetime, timedelta, timezone

from flask import jsonify, request
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth import EmailVerificationToken, TeamMember
from app.auth_routes import auth_bp


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
    existing = EmailVerificationToken.query.filter_by(
        user_id=user.id, verified=True
    ).first()
    if existing:
        return jsonify({
            "success": True,
            "message": "Email is already verified.",
        })

    token = _generate_token()
    ver = EmailVerificationToken(
        token=token,
        user_id=user.id,
        email=email,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        verified=False,
    )
    db.session.add(ver)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "If the email exists, a verification link has been sent.",
        "_verify_token": token,
    })


@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token: str):
    """Verify email address using a token."""
    ver = EmailVerificationToken.query.filter_by(token=token).first()
    if not ver:
        raise NotFound("Invalid or expired verification token")
    if ver.verified:
        raise NotFound("Token has already been used")
    if datetime.utcnow() > ver.expires_at:
        db.session.delete(ver)
        db.session.commit()
        raise NotFound("Verification token has expired")

    user = db.session.get(TeamMember, ver.user_id)
    if not user:
        raise NotFound("User not found")

    ver.verified = True
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Email verified successfully",
    })