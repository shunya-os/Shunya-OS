"""SHUNYA — MFA / 2FA (Milestone X, D2.4).

Pluggable multi-factor authentication with TOTP support.
"""

import secrets
import hashlib
import base64
from datetime import datetime
from flask import request, jsonify, session
from werkzeug.exceptions import NotFound, BadRequest
from app.auth_routes import login_required, auth_bp
from app import db
from app.auth import TeamMember


# In-memory MFA state per user
_mfa_state: dict = {}  # user_id -> {secret, enabled, recovery_codes}


def _generate_secret() -> str:
    """Generate a pseudo-TOTP secret (16 bytes, base32)."""
    raw = secrets.token_bytes(20)  # 160 bits for proper TOTP
    return base64.b32encode(raw).decode("utf-8")


def _decode_secret(secret: str) -> bytes:
    """Decode base32 secret with proper padding."""
    # Add padding if missing
    padding = 8 - (len(secret) % 8)
    if padding != 8:
        secret += "=" * padding
    return base64.b32decode(secret)


def _generate_recovery_codes(count: int = 10) -> list:
    return [secrets.token_hex(4).upper() for _ in range(count)]


def _validate_totp(secret: str, code: str) -> bool:
    """Simple TOTP validation — for production use pyotp library."""
    import hashlib, hmac, struct, time
    try:
        int(code)
    except ValueError:
        return False
    if len(code) != 6:
        return False
    # Simplified TOTP: check against current 30s window ±1
    intervals = [int(time.time()) // 30 + i for i in (-1, 0, 1)]
    for interval in intervals:
        msg = struct.pack(">Q", interval)
        h = hmac.new(_decode_secret(secret), msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        truncated = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
        if str(truncated % 10**6).zfill(6) == code:
            return True
    return False


@auth_bp.route("/mfa/setup", methods=["POST"])
@login_required
def mfa_setup():
    """Generate MFA secret and QR URI for setup."""
    from flask import g
    user_id = g.user.id

    if user_id in _mfa_state:
        raise BadRequest("MFA is already configured or pending setup")

    secret = _generate_secret()
    uri = f"otpauth://totp/SHUNYA:{g.user.email}?secret={secret}&issuer=SHUNYA"

    _mfa_state[user_id] = {
        "secret": secret,
        "enabled": False,
        "recovery_codes": _generate_recovery_codes(),
        "created_at": datetime.utcnow().isoformat(),
    }

    return jsonify({
        "success": True,
        "data": {
            "secret": secret,
            "uri": uri,
            "recovery_codes": _mfa_state[user_id]["recovery_codes"],
        },
    })


@auth_bp.route("/mfa/verify", methods=["POST"])
@login_required
def mfa_verify():
    """Verify a TOTP code to enable MFA."""
    from flask import g
    user_id = g.user.id

    state = _mfa_state.get(user_id)
    if not state:
        raise BadRequest("MFA has not been set up yet")

    if state.get("enabled"):
        raise BadRequest("MFA is already enabled")

    data = request.get_json(silent=True) or {}
    code = data.get("code", "")

    if not _validate_totp(state["secret"], code):
        raise BadRequest("Invalid verification code")

    state["enabled"] = True

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

    if user_id not in _mfa_state:
        raise BadRequest("MFA is not configured")

    # Verify password before disabling
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if not g.user.check_password(password):
        raise BadRequest("Invalid password")

    _mfa_state.pop(user_id, None)

    return jsonify({
        "success": True,
        "message": "MFA has been disabled",
    })


@auth_bp.route("/mfa/challenge", methods=["POST"])
def mfa_challenge():
    """Verify MFA code during login (after primary auth)."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    code = data.get("code", "")
    recovery_code = data.get("recovery_code", "")

    user = TeamMember.query.filter_by(email=email, is_active=True).first()
    if not user:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    state = _mfa_state.get(user.id)
    if not state or not state.get("enabled"):
        return jsonify({"success": True, "message": "MFA not required"})

    # Try recovery code first
    if recovery_code:
        if recovery_code in state.get("recovery_codes", []):
            state["recovery_codes"].remove(recovery_code)
            state["enabled"] = False
            session["user_id"] = user.id
            return jsonify({
                "success": True,
                "message": "Recovery code accepted. Please re-enable MFA.",
            })
        return jsonify({"success": False, "error": "Invalid recovery code"}), 401

    if not _validate_totp(state["secret"], code):
        return jsonify({"success": False, "error": "Invalid verification code"}), 401

    session["user_id"] = user.id
    return jsonify({"success": True, "message": "MFA verified"})