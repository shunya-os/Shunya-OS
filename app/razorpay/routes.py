"""
Razorpay Integration — Payment Links (replaces Stripe).

Users configure their own Razorpay API keys via Settings → Payments.
Keys are encrypted at rest using Fernet symmetric encryption.

POST /api/v1/razorpay/create-link      — Create a payment link (optional invoice_id)
POST /api/v1/razorpay/save-keys        — Save/update Razorpay API keys
GET  /api/v1/razorpay/status           — Check if keys are configured
POST /api/v1/razorpay/test-connection  — Test saved keys against Razorpay API
POST /api/v1/payments/razorpay/webhook — Razorpay webhook: marks the linked
                                          FinInvoice paid and records a
                                          FinancePayment row (idempotent by
                                          razorpay payment_id, signature verified)

Identity is resolved from the Flask session first (the Settings → Payments UI
sends no identity headers — only cookies), falling back to the legacy
X-Identity-Id / X-User-Id headers.
"""
import os
import json
import base64
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app, g, session
from cryptography.fernet import Fernet
from sqlalchemy import text

from app import db
from app.authz.decorators import session_required

logger = logging.getLogger(__name__)

razorpay_bp = Blueprint("razorpay", __name__, url_prefix="/api/v1/razorpay")
# Separate blueprint so the webhook path matches the documented
# POST /api/v1/payments/razorpay/webhook contract.
razorpay_webhook_bp = Blueprint(
    "razorpay_webhook", __name__, url_prefix="/api/v1/payments"
)


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
    """Extract the identity ID — Flask session first, headers as a fallback.

    The Settings → Payments UI calls these endpoints with
    ``credentials: 'include'`` and NO identity headers, so identity MUST come
    from the session (set by ``session_required`` → ``g.identity_id`` or the
    signin route's ``session['identity_id']``). The legacy headers remain as a
    compatibility fallback for programmatic callers.
    """
    return (
        g.get("identity_id")
        or session.get("identity_id")
        or session.get("user_id")
        or request.headers.get("X-Identity-Id")
        or request.headers.get("X-User-Id")
    )


def _ensure_payment_links_table():
    """Create the payment_links table (link → invoice mapping for webhooks)."""
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_links (
            id SERIAL PRIMARY KEY,
            identity_id VARCHAR(64) NOT NULL,
            link_id VARCHAR(128) NOT NULL,
            invoice_id INTEGER,
            amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
            currency VARCHAR(10) DEFAULT 'INR',
            status VARCHAR(30) DEFAULT 'created',
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(link_id)
        )
    """))
    db.session.commit()


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
@session_required
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
@session_required
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
@session_required
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
@session_required
def create_payment_link():
    """Create a Razorpay payment link.

    Request JSON:
        amount         (int)  — Amount in smallest currency unit (paise for INR)
        description    (str)  — Description of the payment
        customer_name  (str)  — Customer name
        customer_email (str)  — Customer email
        customer_phone (str)  — Customer phone number
        invoice_id     (int)  — Optional FinInvoice id to auto-mark paid via webhook
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
    invoice_id = data.get("invoice_id")

    if not amount or amount <= 0:
        return jsonify({"success": False, "error": "Amount must be a positive integer"}), 400

    try:
        keys = _get_saved_keys(identity_id)
        if not keys:
            return jsonify({"success": False, "error": "Razorpay not configured. Save your API keys in Settings → Payments first."}), 400

        import razorpay
        client = razorpay.Client(auth=(keys["key_id"], keys["key_secret"]))

        base_url = os.environ.get(
            "SHUNYA_BASE_URL",
            current_app.config.get("SHUNYA_BASE_URL", "https://shunyaos.com"),
        ).rstrip("/")

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
            "notes": {
                "invoice_id": str(invoice_id) if invoice_id else "",
                "shunya_identity": identity_id,
            },
            # Real SPA page — the SPA shell serves index.html at /payment/success.
            "callback_url": f"{base_url}/payment/success",
            "callback_method": "get",
        }

        link = client.payment_link.create(payload)

        # Persist the link → invoice mapping so the webhook can resolve
        # the FinInvoice without trusting client-supplied data.
        _store_payment_link(identity_id, link.get("id"), invoice_id, int(amount), payload["currency"])

        return jsonify({
            "success": True,
            "short_url": link.get("short_url"),
            "id": link.get("id"),
            "status": link.get("status"),
            "amount": amount,
            "currency": "INR",
            "invoice_id": invoice_id,
        })
    except Exception as e:
        logger.exception("Razorpay payment link creation failed")
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Payment link store (link → invoice mapping, survives restart)
# ---------------------------------------------------------------------------

def _store_payment_link(identity_id: str, link_id, invoice_id, amount: int, currency: str):
    """Persist a created link so the webhook can resolve the FinInvoice."""
    if not link_id:
        return
    _ensure_payment_links_table()
    try:
        db.session.execute(
            text("""
                INSERT INTO payment_links (identity_id, link_id, invoice_id, amount, currency, status, created_at)
                VALUES (:identity_id, :link_id, :invoice_id, :amount, :currency, 'created', NOW())
                ON CONFLICT (link_id)
                DO UPDATE SET
                    invoice_id = :invoice_id2,
                    amount = :amount2,
                    status = 'created'
            """),
            {
                "identity_id": identity_id,
                "link_id": str(link_id),
                "invoice_id": invoice_id or None,
                "amount": amount,
                "currency": currency,
                "invoice_id2": invoice_id or None,
                "amount2": amount,
            },
        )
        db.session.commit()
    except Exception:
        logger.exception("Failed to persist payment link mapping")
        db.session.rollback()


# ---------------------------------------------------------------------------
# Razorpay webhook — real payment capture (no simulation)
# ---------------------------------------------------------------------------

def _verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """Verify the Razorpay webhook signature (HMAC-SHA256 over the raw body).

    Razorpay signs webhook payloads with ``base64(HMAC-SHA256(secret, body))``
    delivered in the ``X-Razorpay-Signature`` header.
    """
    import hashlib
    import hmac

    if not signature or not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    try:
        provided = base64.b64decode(signature)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(expected, provided)


def _resolve_webhook_secret(payload: dict) -> str | None:
    """Resolve the secret used to verify webhook signatures.

    Priority:
      1. RAZORPAY_WEBHOOK_SECRET env / app config (the operator-owned secret).
      2. The Razorpay API key secret saved for the identity that created the
         payment link (via Settings → Payments / save-keys) — a documented
         fallback so the flow works before the operator sets the env var.

    Returns None (→ honest refusal) when nothing can be resolved.
    """
    secret = (
        os.environ.get("RAZORPAY_WEBHOOK_SECRET")
        or current_app.config.get("RAZORPAY_WEBHOOK_SECRET")
    )
    if secret:
        return secret
    identity_id = _identity_for_event(payload)
    if identity_id:
        try:
            keys = _get_saved_keys(identity_id)
        except Exception:
            keys = None
        if keys:
            return keys["key_secret"]
    return None


def _identity_for_event(payload: dict) -> str | None:
    """Find the identity that created the link for this webhook event."""
    notes = {}
    entity = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
    notes = entity.get("notes") or {}
    if notes.get("shunya_identity"):
        return str(notes["shunya_identity"])
    link_entity = (payload.get("payload") or {}).get("payment_link", {}).get("payment_link") or {}
    notes = link_entity.get("notes") or {}
    if notes.get("shunya_identity"):
        return str(notes["shunya_identity"])
    link_id = link_entity.get("id") or entity.get("id")
    if link_id:
        try:
            row = db.session.execute(
                text("SELECT identity_id FROM payment_links WHERE link_id = :lid"),
                {"lid": str(link_id)},
            ).fetchone()
            if row:
                return row[0]
        except Exception:
            pass
    return None


def _lookup_link_id(payload: dict) -> str | None:
    """Extract the Razorpay payment-link id from a webhook payload."""
    entity = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
    link_id = (entity.get("notes") or {}).get("shunya_link_id")
    if link_id:
        return str(link_id)
    link_entity = (payload.get("payload") or {}).get("payment_link", {}).get("payment_link") or {}
    return link_entity.get("id")


def _lookup_invoice_id(payload: dict) -> int | None:
    """Resolve the linked FinInvoice id — notes win, DB mapping as backup."""
    entity = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
    notes = entity.get("notes") or {}
    raw = notes.get("invoice_id")
    if raw:
        try:
            return int(raw)
        except (TypeError, ValueError):
            pass
    link_id = _lookup_link_id(payload)
    if link_id:
        try:
            row = db.session.execute(
                text("SELECT invoice_id FROM payment_links WHERE link_id = :lid"),
                {"lid": str(link_id)},
            ).fetchone()
            if row and row[0]:
                return int(row[0])
        except Exception:
            pass
    return None


def _extract_payment_id(payload: dict) -> str | None:
    """Extract the real razorpay payment id (idempotency key)."""
    entity = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
    pid = entity.get("id")
    if pid:
        return str(pid)
    link_entity = (payload.get("payload") or {}).get("payment_link", {}).get("payment_link") or {}
    pid = link_entity.get("payment_id") or link_entity.get("id")
    return str(pid) if pid else None


@razorpay_webhook_bp.route("/razorpay/webhook", methods=["POST"])
def razorpay_webhook():
    """Handle Razorpay webhooks — mark linked invoices paid (idempotent).

    - Verifies the ``X-Razorpay-Signature`` (HMAC-SHA256 over the raw body).
    - On ``payment.captured`` / ``payment_link.paid``: marks the linked
      FinInvoice paid and records a FinancePayment row keyed by the real
      razorpay payment id (idempotent).
    - Never fabricates a successful payment: a bad signature returns 400, an
      unresolvable secret/link returns an honest error.
    """
    raw = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, ValueError):
        logger.warning("Razorpay webhook: unparseable body")
        return jsonify({"error": "Invalid JSON body"}), 400

    event = payload.get("event", "(unknown)")

    if event not in ("payment.captured", "payment_link.paid"):
        # Ack-and-ignore other events (payment.failed, link.expired, …).
        logger.info("Razorpay webhook: ignored event %s", event)
        return jsonify({"received": True, "event": event, "action": "ignored"}), 200

    secret = _resolve_webhook_secret(payload)
    if not secret:
        logger.error(
            "Razorpay webhook: no webhook secret resolvable for event %s — "
            "set RAZORPAY_WEBHOOK_SECRET or save keys. Refusing (no simulated success).",
            event,
        )
        return jsonify({
            "error": "Webhook secret not configured; event not processed",
            "event": event,
        }), 500

    if not _verify_webhook_signature(raw, signature, secret):
        logger.warning("Razorpay webhook: INVALID signature for event %s", event)
        return jsonify({"received": False, "error": "Invalid signature", "event": event}), 400

    return _process_paid_event(payload, event)


def _process_paid_event(payload: dict, event: str):
    """Record a real captured payment against the linked FinInvoice."""
    from app.finance.models import FinInvoice, FinancePayment
    from app.finance.services import record_payment

    invoice_id = _lookup_invoice_id(payload)
    if not invoice_id:
        logger.error(
            "Razorpay webhook %s: cannot resolve linked invoice (link=%s) — refusing to fabricate a payment",
            event, _lookup_link_id(payload),
        )
        return jsonify({
            "error": "No linked invoice found; payment not recorded",
            "event": event,
        }), 400

    invoice = db.session.get(FinInvoice, invoice_id)
    if not invoice:
        logger.error("Razorpay webhook %s: linked invoice %s not found", event, invoice_id)
        return jsonify({"error": "Linked invoice not found", "event": event}), 404

    payment_id = _extract_payment_id(payload)
    if not payment_id:
        logger.error("Razorpay webhook %s: no payment id in payload", event)
        return jsonify({"error": "No payment id in payload", "event": event}), 400

    # Idempotency: keyed by the real razorpay payment id.
    existing = FinancePayment.query.filter_by(reference_number=payment_id).first()
    if existing:
        logger.info("Razorpay webhook %s: payment %s already recorded (payment row %s)", event, payment_id, existing.id)
        return jsonify({
            "received": True, "event": event, "payment_id": payment_id,
            "invoice_id": invoice_id, "status": "already_recorded",
        }), 200

    entity = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
    amount_paise = entity.get("amount")
    if not amount_paise:
        link_entity = (payload.get("payload") or {}).get("payment_link", {}).get("payment_link") or {}
        amount_paise = link_entity.get("amount")
    amount = (int(amount_paise) / 100.0) if amount_paise else float(invoice.total_amount or 0)

    from datetime import date as _date
    result = record_payment(
        invoice.organization_id,
        invoice.id,
        amount,
        _date.today(),
        method="razorpay",
        reference=payment_id,
        created_by="razorpay_webhook",
    )
    if "error" in result:
        logger.error("Razorpay webhook %s: record_payment failed: %s", event, result["error"])
        return jsonify({"error": result["error"], "event": event}), 400

    logger.info("Razorpay webhook %s: invoice %s marked paid via payment %s", event, invoice_id, payment_id)
    return jsonify({
        "received": True,
        "event": event,
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "status": "recorded",
    }), 200