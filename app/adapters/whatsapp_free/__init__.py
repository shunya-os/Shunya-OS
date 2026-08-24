"""
SHUNYA — WhatsApp Free Connect Adapter (Phase 3, receive-only, EXPERIMENTAL)
Bridge-client pattern: communicates with a sidecar bridge process.
"""
import json
from datetime import datetime, timezone
from app.communication.adapter import (
    CommunicationAdapter, AdapterCapabilities, NormalizedMessage, AttachmentData,
)


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
        return []

    def sync_incremental(self, source, cursor) -> list[NormalizedMessage]:
        return []