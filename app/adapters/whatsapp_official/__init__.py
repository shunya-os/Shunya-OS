"""
SHUNYA — WhatsApp Official Business API Adapter (Phase 3, receive-only)
"""
import json
import hashlib
import hmac
import os
from datetime import datetime
from app.communication.adapter import (
    CommunicationAdapter, AdapterCapabilities, NormalizedMessage, AttachmentData,
)


class WhatsAppOfficialAdapter(CommunicationAdapter):
    """WhatsApp Official Business Platform adapter.
    Phase 3: receive-only via webhook. No outbound send."""

    @property
    def provider(self) -> str:
        return "whatsapp_official"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_webhook_receive=True,
            supports_incremental_sync=True,
            supports_threading=False,
            supports_groups=False,
            supports_media_metadata=True,
            supports_outbound=False,
        )

    def normalize(self, raw_payload: dict) -> list[NormalizedMessage]:
        """Normalize a WhatsApp Business API webhook payload."""
        messages = []
        entry = (raw_payload.get("entry") or [{}])[0]
        changes = (entry.get("changes") or [{}])[0]
        value = changes.get("value") or {}
        raw_messages = value.get("messages") or []
        contacts = value.get("contacts") or []

        # Build contact lookup
        contact_map = {}
        for c in contacts:
            wa_id = c.get("wa_id", "")
            profile = c.get("profile", {})
            contact_map[wa_id] = profile.get("name", "")

        for msg in raw_messages:
            sender = msg.get("from", "")
            msg_type = msg.get("type", "text")
            display_name = contact_map.get(sender, sender)

            text = ""
            if msg_type == "text":
                text = msg.get("text", {}).get("body", "")
            elif msg_type == "interactive":
                interactive = msg.get("interactive", {})
                btn_reply = interactive.get("button_reply", {})
                text = btn_reply.get("title", "") or interactive.get("list_reply", {}).get("title", "")

            attachments = []
            if msg_type in ("image", "document", "audio", "video"):
                media = msg.get(msg_type, {})
                attachments.append(AttachmentData(
                    provider_media_id=media.get("id", ""),
                    mime_type=media.get("mime_type", ""),
                    filename=media.get("filename", ""),
                    size_bytes=media.get("file_size"),
                ))

            normalized = NormalizedMessage(
                source_id=0,  # Set by caller
                provider_message_id=msg.get("id", ""),
                provider_chat_id=sender,
                sender_raw=sender,
                sender_normalized=sender,
                sender_display_name=display_name,
                body=text,
                message_type=msg_type,
                is_group=False,
                is_inbound=True,
                original_timestamp=datetime.utcnow(),
                attachments=attachments,
            )
            messages.append(normalized)

        return messages

    def validate_webhook(self, request) -> dict:
        """Validate WhatsApp webhook authenticity."""
        payload = request.get_data()
        signature = request.headers.get("X-Hub-Signature-256", "")
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "shunya_verify_2026")

        # GET = verification
        if request.method == "GET":
            mode = request.args.get("hub.mode", "")
            token = request.args.get("hub.verify_token", "")
            challenge = request.args.get("hub.challenge", "")
            if mode == "subscribe" and token == verify_token:
                return challenge, 200
            return {"error": "Verification failed"}, 403

        # POST = incoming message
        if signature:
            token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
            if token:
                expected = hmac.new(token.encode(), payload, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(f"sha256={expected}", signature):
                    return {"error": "Invalid signature"}, 403

        return request.get_json(silent=True) or {}, 200

    def sync_incremental(self, source, cursor) -> list[NormalizedMessage]:
        """WhatsApp Official does not support incremental sync in Phase 3
        beyond webhook delivery. Webhook is the real-time path."""
        return []

    def sync_initial(self, source, boundary=None) -> list[NormalizedMessage]:
        """WhatsApp Official does not support historical sync in Phase 3."""
        return []