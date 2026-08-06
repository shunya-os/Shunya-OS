"""
Razorpay Integration — Payment Links (replaces Stripe).

Users configure their own Razorpay API keys via Settings → Payments.
Keys are encrypted at rest using Fernet symmetric encryption.

POST /api/v1/razorpay/create-link     — Create a payment link
POST /api/v1/razorpay/save-keys       — Save/update Razorpay API keys
GET  /api/v1/razorpay/status          — Check if keys are configured
POST /api/v1/razorpay/test-connection  — Test saved keys against Razorpay API
"""
import os
import base64
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from cryptography.fernet import Fernet
from sqlalchemy import text

from app import db

logger = logging.getLogger(__name__)

razorpay_bp = Blueprint("razorpay", __name__, url_prefix="/api/v1/razorpay")


# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

def _get_fernet() -> Fernet:
    """Derive a Fernet key from app.config['SECRET_KEY'] (padded to 32 bytes)."""
    secret = current_app.config.get("SECRET_KEY", "dev-secret-change-in-production")
    # Pad or truncate to exactly 32 bytes for Fernet
    key_bytes = secret.encode("utf-8")
    if len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b"\0")
    elif len(key_bytes) > 32:
        key_bytes = key_bytes[:32]
    # Fernet keys must be base64-encoded 32-byte values
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def _encrypt_value(plaintext: str) -> str:
    """Encrypt a string value using Fernet."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def _decrypt_value(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _ensure_payment_providers_table():
    """Create the payment_providers table if it doesn't exist."""
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_providers (
            id SERIAL PRIMARY KEY,
            identity_id VARCHAR(64) NOT NULL,
            provider VARCHAR(32) NOT NULL DEFAULT 'razorpay',
            api_key_encrypted TEXT NOT NULL,
            api_secret_encrypted TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(identity_id, provider)
        )
    """))
    db.session.commit()


def _get_identity_id() -> str | None:
    """Extract the identity ID from request headers."""
    return request.headers.get("X-Identity-Id") or request.headers.get("X-User-Id")


def _get_saved_keys(identity_id: str) -> dict | None:
    """Retrieve saved Razorpay keys for the given identity."""
    _ensure_payment_providers_table()
    row = db.session.execute(
        text("SELECT api_key_encrypted, api_secret_encrypted FROM payment_providers "
             "WHERE identity_id = :identity_id AND provider = 'razorpay' AND is_active = TRUE"),
        {"identity_id": identity_id},
    ).fetchone()
    if not row:
        return None
    return {
        "key_id": _decrypt_value(row[0]),
        "key_secret": _decrypt_value(row[1]),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@razorpay_bp.route("/status", methods=["GET"])
def status():
    """Check whether the current user has saved Razorpay keys."""
    identity_id = _get_identity_id()
    if not identity_id:
        return jsonify({"configured": False, "error": "Not authenticated"}), 401

    try:
        keys = _get_saved_keys(identity_id)
        return jsonify({"configured": keys is not None})
    except Exception as e:
        logger.exception("Failed to check Razorpay status")
        return jsonify({"configured": False, "error": str(e)})


@razorpay_bp.route("/save-keys", methods=["POST"])
def save_keys():
    """Save or update Razorpay API keys for the current user.

    Request JSON:
        key_id     (str) — Razorpay API Key ID
        key_secret (str) — Razorpay API Key Secret
    """
    identity_id = _get_identity_id()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    key_id = (data.get("key_id") or "").strip()
    key_secret = (data.get("key_secret") or "").strip()

    if not key_id or not key_secret:
        return jsonify({"success": False, "error": "Missing required fields: key_id, key_secret"}), 400

    try:
        encrypted_key_id = _encrypt_value(key_id)
        encrypted_key_secret = _encrypt_value(key_secret)

        _ensure_payment_providers_table()

        # Upsert: insert or update
        db.session.execute(
            text("""
                INSERT INTO payment_providers (identity_id, provider, api_key_encrypted, api_secret_encrypted, is_active, created_at)
                VALUES (:identity_id, 'razorpay', :api_key_encrypted, :api_secret_encrypted, TRUE, NOW())
                ON CONFLICT (identity_id, provider)
                DO UPDATE SET
                    api_key_encrypted = :api_key_encrypted2,
                    api_secret_encrypted = :api_secret_encrypted2,
                    is_active = TRUE,
                    created_at = NOW()
            """),
            {
                "identity_id": identity_id,
                "api_key_encrypted": encrypted_key_id,
                "api_secret_encrypted": encrypted_key_secret,
                "api_key_encrypted2": encrypted_key_id,
                "api_secret_encrypted2": encrypted_key_secret,
            },
        )
        db.session.commit()

        return jsonify({"success": True, "message": "Razorpay keys saved successfully"})
    except Exception as e:
        logger.exception("Failed to save Razorpay keys")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@razorpay_bp.route("/test-connection", methods=["POST"])
def test_connection():
    """Test the saved Razorpay keys by fetching account balance."""
    identity_id = _get_identity_id()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        keys = _get_saved_keys(identity_id)
        if not keys:
            return jsonify({"success": False, "error": "No Razorpay keys configured"}), 400

        import razorpay
        client = razorpay.Client(auth=(keys["key_id"], keys["key_secret"]))

        # Try to fetch payments list to validate keys (a simple read-only call)
        client.payment_link.all(count=1)
        return jsonify({"success": True, "message": "Connection successful"})
    except Exception as e:
        logger.exception("Razorpay connection test failed")
        return jsonify({"success": False, "error": str(e)})


@razorpay_bp.route("/create-link", methods=["POST"])
def create_payment_link():
    """Create a Razorpay payment link.

    Request JSON:
        amount         (int)  — Amount in smallest currency unit (paise for INR)
        description    (str)  — Description of the payment
        customer_name  (str)  — Customer name
        customer_email (str)  — Customer email
        customer_phone (str)  — Customer phone number
    """
    identity_id = _get_identity_id()
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    amount = data.get("amount")
    description = data.get("description", "")
    customer_name = data.get("customer_name", "")
    customer_email = data.get("customer_email", "")
    customer_phone = data.get("customer_phone", "")

    if not amount or amount <= 0:
        return jsonify({"success": False, "error": "Amount must be a positive integer"}), 400

    try:
        keys = _get_saved_keys(identity_id)
        if not keys:
            return jsonify({"success": False, "error": "Razorpay not configured. Save your API keys in Settings → Payments first."}), 400

        import razorpay
        client = razorpay.Client(auth=(keys["key_id"], keys["key_secret"]))

        payload = {
            "amount": int(amount),
            "currency": "INR",
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone,
            },
            "notify": {
                "sms": bool(customer_phone),
                "email": bool(customer_email),
            },
            "callback_url": "https://shunya.os/payment-success",
            "callback_method": "get",
        }

        link = client.payment_link.create(payload)

        return jsonify({
            "success": True,
            "short_url": link.get("short_url"),
            "id": link.get("id"),
            "status": link.get("status"),
            "amount": amount,
            "currency": "INR",
        })
    except Exception as e:
        logger.exception("Razorpay payment link creation failed")
        return jsonify({"success": False, "error": str(e)}), 500