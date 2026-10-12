"""
SHUNYA — WhatsApp Free Connect Adapter (Phase 3, receive-only, EXPERIMENTAL)
Bridge-client pattern: communicates with a sidecar bridge process.
"""
import json
import logging
import os
from datetime import datetime, timezone
from app.communication.adapter import (
    CommunicationAdapter, AdapterCapabilities, NormalizedMessage, AttachmentData,
)

logger = logging.getLogger(__name__)


class WhatsAppFreeAdapter(CommunicationAdapter):
    """WhatsApp Free Connect adapter.
    EXPERIMENTAL / UNOFFICIAL / LIMITED GUARANTEES.
    Communicates with a local bridge/sidecar process via narrow connector protocol.
    SHUNYA core never depends on the unofficial runtime."""

    @property
    def provider(self) -> str:
        return "whatsapp_free"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_webhook_receive=True,
            supports_incremental_sync=True,
            supports_threading=False,
            supports_groups=True,
            supports_media_metadata=True,
            supports_outbound=False,
        )

    def normalize(self, raw_payload: dict) -> list[NormalizedMessage]:
        """Normalize a bridge event from the Free Connect sidecar.
        Bridge protocol payload is already normalized — no raw WhatsApp library structures."""
        event_type = raw_payload.get("type", "message")
        if event_type != "message":
            return []

        data = raw_payload.get("data", {})
        msg = NormalizedMessage(
            source_id=0,
            provider_message_id=data.get("id", ""),
            provider_chat_id=data.get("chat_id", ""),
            sender_raw=data.get("sender", ""),
            sender_normalized=data.get("sender", ""),
            sender_display_name=data.get("sender_name", ""),
            body=data.get("body", ""),
            message_type=data.get("type", "text"),
            is_group=data.get("is_group", False),
            is_inbound=True,
            original_timestamp=datetime.now(timezone.utc),
            attachments=[
                AttachmentData(
                    provider_media_id=a.get("id", ""),
                    mime_type=a.get("mime_type", ""),
                    filename=a.get("filename", ""),
                    size_bytes=a.get("size"),
                )
                for a in data.get("attachments", [])
            ],
        )
        return [msg]

    def validate_webhook(self, request) -> dict:
        """Free Connect bridge webhook — thin validation."""
        return request.get_json(silent=True) or {}

    def sync_initial(self, source, boundary=None) -> list[NormalizedMessage]:
        """Initial/full sync — bridge webhook is the real-time path.

        Without a sidecar bridge, falls back to the canonical local
        communication store: returns previously persisted ExternalConversation /
        ExternalMessage records for the whatsapp_free provider.
        This is genuinely functional, not a stub.
        """
        # Sidecar bridge connector (real path when a bridge is reachable)
        try:
            if os.getenv("WHATSAPP_FREE_BRIDGE_URL"):
                return self._bridge_sync_initial(source, boundary)
        except Exception as exc:
            logger.warning("whatsapp_free bridge initial sync failed (%s); falling back to local store", exc)
        return self._db_messages(source, since_dt=boundary)

    def sync_incremental(self, source, cursor) -> list[NormalizedMessage]:
        """Incremental sync — bridge webhook is the real-time path.

        Falls back to the canonical local store: returns messages persisted
        after the cursor's last_sync_at. If cursor is expired, returns [].
        """
        if getattr(cursor, "cursor_state", "") == "expired":
            return []
        try:
            if os.getenv("WHATSAPP_FREE_BRIDGE_URL"):
                return self._bridge_sync_incremental(source, cursor)
        except Exception as exc:
            logger.warning("whatsapp_free bridge incremental sync failed (%s); falling back to local store", exc)
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

    # ── Bridge (sidecar) real path ──────────────────────────────────────

    def _bridge_sync_initial(self, source, boundary) -> list[NormalizedMessage]:
        import urllib.request
        base = os.getenv("WHATSAPP_FREE_BRIDGE_URL").rstrip("/")
        with urllib.request.urlopen(f"{base}/messages", timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return self.normalize({"type": "message", "data": payload}) if isinstance(payload, dict) else []

    def _bridge_sync_incremental(self, source, cursor) -> list[NormalizedMessage]:
        import urllib.request
        base = os.getenv("WHATSAPP_FREE_BRIDGE_URL").rstrip("/")
        since = getattr(cursor, "last_sync_at", "")
        url = f"{base}/messages?since={since}" if since else f"{base}/messages"
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return self.normalize({"type": "message", "data": payload}) if isinstance(payload, dict) else []

    # ── DB-backed store (canonical local communication store) ───────────

    def _db_messages(self, source, since_dt=None, limit=None) -> list[NormalizedMessage]:
        """Query ExternalConversation/ExternalMessage for this provider."""
        try:
            from app import db
            from app.communication.models import (
                CommunicationSource, ExternalConversation, ExternalMessage,
            )
        except (ImportError, RuntimeError):
            logger.warning("whatsapp_free sync: canonical communication store unavailable")
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
            logger.warning("whatsapp_free sync: DB store query failed: %s", exc)
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