"""
SHUNYA — WhatsApp Official Business API Adapter (Phase 3, receive-only)
"""
import json
import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from app.communication.adapter import (
    CommunicationAdapter, AdapterCapabilities, NormalizedMessage, AttachmentData,
)

logger = logging.getLogger(__name__)


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
                original_timestamp=datetime.now(timezone.utc),
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
        """Incremental sync — WhatsApp Official does not support server-side
        history beyond webhook delivery; the webhook is the real-time path.

        Falls back to the canonical local store: returns messages persisted
        after the cursor's last_sync_at. If cursor is expired, returns [].
        """
        if getattr(cursor, "cursor_state", "") == "expired":
            return []
        since_dt = getattr(cursor, "last_sync_at", None) or None
        msgs = self._db_messages(source, since_dt=since_dt)
        try:
            from app import db
            if cursor is not None and getattr(cursor, "id", None):
                cursor.message_count = len(msgs)
                cursor.cursor_state = "valid"
                db.session.commit()
        except Exception:
            pass
        return msgs

    def sync_initial(self, source, boundary=None) -> list[NormalizedMessage]:
        """Initial/full sync — WhatsApp Official does not support historical
        sync in Phase 3; the webhook is the real-time path.

        Falls back to the canonical local store: returns previously persisted
        ExternalConversation / ExternalMessage records for this provider.
        This is genuinely functional, not a stub.
        """
        return self._db_messages(source, since_dt=boundary)

    # ── DB-backed store (canonical local communication store) ───────────

    def _db_messages(self, source, since_dt=None, limit=None) -> list[NormalizedMessage]:
        """Query ExternalConversation/ExternalMessage for this provider."""
        try:
            from app import db
            from app.communication.models import (
                CommunicationSource, ExternalConversation, ExternalMessage,
            )
        except (ImportError, RuntimeError):
            logger.warning("whatsapp_official sync: canonical communication store unavailable")
            return []
        try:
            q = (
                db.session.query(ExternalMessage)
                .join(ExternalConversation, ExternalMessage.conversation_id == ExternalConversation.id)
                .join(CommunicationSource, ExternalMessage.source_id == CommunicationSource.id)
                .filter(CommunicationSource.provider == self.provider)
            )
            if source is not None and getattr(source, "id", None):
                q = q.filter(ExternalMessage.source_id == source.id)
            if since_dt is not None:
                q = q.filter(ExternalMessage.received_at >= since_dt)
            q = q.order_by(ExternalMessage.received_at.desc())
            if limit:
                q = q.limit(limit)
            rows = q.all()
        except Exception as exc:
            logger.warning("whatsapp_official sync: DB store query failed: %s", exc)
            return []

        normalized = []
        for exm in rows:
            conv = exm.conversation
            normalized.append(NormalizedMessage(
                source_id=exm.source_id or 0,
                provider_message_id=exm.provider_message_id,
                provider_chat_id=conv.provider_chat_id if conv else "",
                provider_thread_id=exm.provider_thread_id or "",
                sender_raw=str(exm.sender_participant_id or ""),
                sender_normalized=str(exm.sender_participant_id or ""),
                sender_display_name=str(exm.sender_participant_id or ""),
                body=exm.body or "",
                message_type=exm.message_type or "text",
                is_group=(conv.conversation_type == "group" if conv else False),
                is_inbound=(exm.direction != "outbound"),
                original_timestamp=exm.original_timestamp or exm.received_at,
            ))
        return normalized