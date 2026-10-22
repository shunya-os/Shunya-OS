"""SHUNYA — MFA / 2FA (Milestone X, D2.4).

Pluggable multi-factor authentication with TOTP support.
Persistent MFA state via MFAConfig model (shunya_mfa_configs table).
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import datetime, timezone

from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest

from app import db, limiter
from app.auth import TeamMember
from app.auth_routes import auth_bp, login_required
from app.production.auth.mfa_models import MFAConfig


def _generate_secret() -> str:
    """Generate a pseudo-TOTP secret (16 bytes, base32)."""
    raw = secrets.token_bytes(20)
    return base64.b32encode(raw).decode("utf-8")


def _decode_secret(secret: str) -> bytes:
    """Decode base32 secret with proper padding."""
    padding = 8 - (len(secret) % 8)
    if padding != 8:
        secret += "=" * padding
    return base64.b32decode(secret)


def _generate_recovery_codes(count: int = 10) -> list:
    return [secrets.token_hex(4).upper() for _ in range(count)]


def _validate_totp(secret: str, code: str) -> bool:
    """Simple TOTP validation — for production use pyotp library."""
    try:
        int(code)
    except ValueError:
        return False
    if len(code) != 6:
        return False
    intervals = [int(time.time()) // 30 + i for i in (-1, 0, 1)]
    for interval in intervals:
        msg = struct.pack(">Q", interval)
        h = hmac.new(_decode_secret(secret), msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        truncated = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
        if str(truncated % 10**6).zfill(6) == code:
            return True
    return False


@auth_bp.route("/mfa/status", methods=["GET"])
@login_required
def mfa_status():
    """Check MFA status for the current user."""
    from flask import g
    config = MFAConfig.query.filter_by(user_id=g.user.id).first()
    if config and config.enabled:
        return jsonify({"success": True, "data": {"enabled": True, "configured": True}})
    if config:
        return jsonify({"success": True, "data": {"enabled": False, "configured": True}})
    return jsonify({"success": True, "data": {"enabled": False, "configured": False}})


@auth_bp.route("/mfa/setup", methods=["POST"])
@login_required
def mfa_setup():
    """Generate MFA secret and QR URI for setup."""
    from flask import g
    user_id = g.user.id

    existing = MFAConfig.query.filter_by(user_id=user_id).first()
    if existing and existing.enabled:
        raise BadRequest("MFA is already enabled")

    secret = _generate_secret()
    uri = f"otpauth://totp/SHUNYA:{g.user.email}?secret={secret}&issuer=SHUNYA"

    recovery_codes = _generate_recovery_codes()

    if existing:
        existing.secret = secret
        existing.enabled = False
        existing.recovery_codes = recovery_codes
        existing.updated_at = datetime.utcnow()
    else:
        config = MFAConfig(
            user_id=user_id,
            secret=secret,
            enabled=False,
            recovery_codes=recovery_codes,
        )
        db.session.add(config)

    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "secret": secret,
            "uri": uri,
            "recovery_codes": recovery_codes,
        },
    })


@auth_bp.route("/mfa/verify", methods=["POST"])
@login_required
def mfa_verify():
    """Verify a TOTP code to enable MFA."""
    from flask import g
    user_id = g.user.id

    config = MFAConfig.query.filter_by(user_id=user_id).first()
    if not config:
        raise BadRequest("MFA has not been set up yet")

    if config.enabled:
        raise BadRequest("MFA is already enabled")

    data = request.get_json(silent=True) or {}
    code = data.get("code", "")

    if not _validate_totp(config.secret, code):
        raise BadRequest("Invalid verification code")

    config.enabled = True
    config.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "MFA has been enabled successfully",
    })


@auth_bp.route("/mfa/disable", methods=["POST"])
@login_required
def mfa_disable():
    """Disable MFA for the current user."""
    from flask import g
    user_id = g.user.id

    config = MFAConfig.query.filter_by(user_id=user_id).first()
    if not config:
        raise BadRequest("MFA is not configured")

    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if not g.user.check_password(password):
        raise BadRequest("Invalid password")

    config.enabled = False
    config.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "MFA has been disabled",
    })


@auth_bp.route("/mfa/challenge", methods=["POST"])
@limiter.limit("5 per 5 minutes")
def mfa_challenge():
    """Second factor for a login that already passed primary authentication.

    G1.29: the session comes only from a pending transaction that the password
    step opened (``mfa_state.begin``). The request body cannot name a different
    user, cannot upgrade a pending transaction by claiming one, and cannot replay a
    completed one. Attempts are capped inside the transaction, and the endpoint is
    rate limited per client as well.
    """
    from app.production.auth import mfa_state

    data = request.get_json(silent=True) or {}
    code = str(data.get("code", "") or "")
    recovery_code = str(data.get("recovery_code", "") or "")
    claimed_email = str(data.get("email", "") or "").strip().lower()

    pending_id = mfa_state.pending_user_id()
    if not pending_id:
        return jsonify({
            "success": False,
            "mfa_required": False,
            "error": "Your sign-in expired. Enter your password again.",
        }), 403

    user = TeamMember.query.filter_by(id=pending_id, is_active=True).first()
    if not user:
        mfa_state.clear()
        return jsonify({"success": False, "error": "Invalid request"}), 401

    # The transaction is bound to the pending user; a body naming someone else is
    # refused rather than followed.
    if claimed_email and claimed_email != (user.email or "").lower():
        mfa_state.clear()
        return jsonify({"success": False, "error": "Your sign-in expired. Enter your password again."}), 403

    config = MFAConfig.query.filter_by(user_id=user.id).first()
    if not config or not config.enabled:
        # Nothing to satisfy: the pending transaction was opened for an account
        # that no longer has a factor. Authenticate it rather than trap the user.
        mfa_state.consume()
        session["user_id"] = user.id
        return jsonify({"success": True, "message": "MFA not required"})

    if recovery_code:
        codes = list(config.recovery_codes or [])
        if recovery_code not in codes:
            if not mfa_state.register_failure():
                return jsonify({"success": False, "error": "Too many attempts. Sign in again."}), 429
            return jsonify({"success": False, "error": "Invalid recovery code"}), 401
        codes.remove(recovery_code)
        config.recovery_codes = codes
        config.enabled = False  # a used recovery code invalidates the factor
        config.updated_at = datetime.utcnow()
        db.session.commit()
        mfa_state.consume()
        session["user_id"] = user.id
        return jsonify({
            "success": True,
            "message": "Recovery code accepted. Please re-enable MFA.",
        })

    if not _validate_totp(config.secret, code):
        if not mfa_state.register_failure():
            return jsonify({"success": False, "error": "Too many attempts. Sign in again."}), 429
        return jsonify({"success": False, "error": "Invalid verification code"}), 401

    mfa_state.consume()  # single use: a replay has no transaction left
    session["user_id"] = user.id
    return jsonify({"success": True, "message": "MFA verified"})