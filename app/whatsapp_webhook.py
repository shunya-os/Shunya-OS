"""
WhatsApp Webhook — plug-and-play. Configure via Settings page.
When WhatsApp Business API credentials are set in env, this webhook
processes incoming WhatsApp messages just like Telegram.

Gate 2.2: Wired through canonical IngestionService for provenance,
evidence, event emission, and idempotency.
"""

import os
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from flask import request, jsonify
from app import db
from app.models import Lead
from app.services import parse_inquiry_text, _cached_or_new_code, format_inquiry_reply

logger = logging.getLogger(__name__)


# ── Webhook Verification ──────────────────────────────────────────────


def verify_whatsapp_signature(payload: bytes, signature: str) -> bool:
    """Verify WhatsApp webhook signature if verify_token is configured."""
    token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    if not token:
        return True
    expected = hmac.new(token.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


_CACHED_IDS: set[str] = set()
"""In-memory idempotency set for webhook message IDs.
Cleared on restart — acceptable for webhook dedup (WhatsApp will retry)."""


def handle_whatsapp_incoming(payload: dict) -> tuple:
    """Process incoming WhatsApp message through canonical ingestion pipeline."""
    entry = (payload.get("entry") or [{}])[0]
    changes = (entry.get("changes") or [{}])[0]
    value = changes.get("value") or {}
    messages = value.get("messages") or []
    contacts = value.get("contacts") or []

    if not messages:
        return jsonify({"status": "ignored"}), 200

    msg = messages[0]
    msg_id = msg.get("id", "")
    sender = msg.get("from", "")
    msg_type = msg.get("type", "text")

    # ── Idempotency: deduplicate by WhatsApp message ID ──
    if msg_id:
        if msg_id in _CACHED_IDS:
            logger.info("Duplicate WhatsApp message skipped: %s", msg_id)
            return jsonify({"status": "duplicate", "message_id": msg_id}), 200
        _CACHED_IDS.add(msg_id)

    text = ""
    if msg_type == "text":
        text = msg.get("text", {}).get("body", "")
    elif msg_type == "interactive":
        interactive = msg.get("interactive", {})
        btn_reply = interactive.get("button_reply", {})
        text = btn_reply.get("title", "") or interactive.get("list_reply", {}).get("title", "")

    if not text:
        return jsonify({"status": "ignored"}), 200

    sender_name = ""
    if contacts:
        profile = contacts[0].get("profile", {})
        sender_name = profile.get("name", "")

    parsed = parse_inquiry_text(text)

    # ── Canonical ingestion pipeline ──
    try:
        from core.ingestion import IngestionRecord, SourceType, InformationClass
        from core.ingestion.service import get_ingestion_service

        record = IngestionRecord(
            idempotency_key=f"whatsapp:{msg_id}" if msg_id else "",
            tenant_id=0,
            source=SourceType.WEBHOOK,
            source_identity=sender,
            provider="whatsapp",
            normalized_payload={
                "message_id": msg_id,
                "sender": sender,
                "sender_name": sender_name,
                "text": text,
                "parsed": parsed,
            },
            information_class=InformationClass.USER_PROVIDED,
            confidence=None,  # Unknown — user message, no measurable confidence
        )
        result = get_ingestion_service().process(record)
        logger.info(
            "WhatsApp ingestion: id=%s outcome=%s event=%s",
            result.ingestion_id, result.outcome.value, result.canonical_event_id[:12] if result.canonical_event_id else "none",
        )
    except Exception as e:
        logger.warning("Ingestion pipeline failed (non-blocking): %s", e)

    # ── Downstream projection: Lead + activity log ──
    with db.session.no_autoflush:
        code = _cached_or_new_code(db.session)

    lead = Lead(
        code=code, source="whatsapp",
        customer_name=parsed.get("name") or sender_name or sender,
        phone=sender, destination=parsed.get("destination"),
        pax=(f"{parsed.get('adults') or 0} adults, {parsed.get('kids') or 0} kids"
             if parsed.get("adults") or parsed.get("kids") else None),
        dates=parsed.get("dates"), notes=text, status="new",
        )
    db.session.add(lead)
    db.session.commit()

    from app.routes import _log_activity
    _log_activity(lead.id, "created", f"Lead created via WhatsApp: {text[:200]}")

    reply_text = format_inquiry_reply(parsed, code)
    return jsonify({
        "messaging_product": "whatsapp", "to": sender,
        "type": "text", "text": {"body": reply_text},
    }), 200


def handle_whatsapp_verification() -> tuple:
    """Handle WhatsApp webhook verification (GET request)."""
    mode = request.args.get("hub.mode", "")
    token = request.args.get("hub.verify_token", "")
    challenge = request.args.get("hub.challenge", "")
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "shunya_verify_2026")
    if mode == "subscribe" and token == verify_token:
        return challenge, 200
    return jsonify({"error": "Verification failed"}), 403