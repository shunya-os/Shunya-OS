"""
WhatsApp Webhook — plug-and-play. Configure via Settings page.
When WhatsApp Business API credentials are set in env, this webhook
processes incoming WhatsApp messages just like Telegram.
"""

import os
import hashlib
import hmac
from flask import request, jsonify
from app import db
from app.models import Lead
from app.services import parse_inquiry_text, _cached_or_new_code, format_inquiry_reply


def verify_whatsapp_signature(payload: bytes, signature: str) -> bool:
    """Verify WhatsApp webhook signature if verify_token is configured."""
    token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    if not token:
        return True
    expected = hmac.new(token.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def handle_whatsapp_incoming(payload: dict) -> tuple:
    """Process incoming WhatsApp message and create lead."""
    entry = (payload.get("entry") or [{}])[0]
    changes = (entry.get("changes") or [{}])[0]
    value = changes.get("value") or {}
    messages = value.get("messages") or []
    contacts = value.get("contacts") or []

    if not messages:
        return jsonify({"status": "ignored"}), 200

    msg = messages[0]
    sender = msg.get("from", "")
    msg_type = msg.get("type", "text")

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
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "panchi_verify_2026")
    if mode == "subscribe" and token == verify_token:
        return challenge, 200
    return jsonify({"error": "Verification failed"}), 403
