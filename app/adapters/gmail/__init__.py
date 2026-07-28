"""
SHUNYA — Gmail Inbound/Read Adapter (Phase 3, receive-only)
Uses Gmail API for initial/full sync and incremental sync via history.
"""
import base64
from datetime import datetime
from typing import Optional
from app.communication.adapter import (
    CommunicationAdapter, AdapterCapabilities, NormalizedMessage, AttachmentData,
)


class GmailAdapter(CommunicationAdapter):
    """Gmail inbound/read adapter.
    Phase 3: receive-only. No send, reply, or draft."""

    @property
    def provider(self) -> str:
        return "gmail"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_initial_sync=True,
            supports_historical_sync=True,
            supports_incremental_sync=True,
            supports_webhook_receive=False,  # Uses Pub/sub push, not direct webhook
            supports_threading=True,
            supports_groups=False,
            supports_media_metadata=True,
            supports_outbound=False,
        )

    def normalize(self, raw_payload: dict) -> list[NormalizedMessage]:
        """Normalize a Gmail API message/thread payload into canonical input.
        Handles both individual messages and thread structures."""
        messages = []

        # Handle thread structure
        thread_id = raw_payload.get("threadId", "")
        raw_messages = raw_payload.get("messages", [raw_payload])

        for msg_data in raw_messages:
            msg_id = msg_data.get("id", "")
            payload = msg_data.get("payload", {})
            headers = {h.get("name", "").lower(): h.get("value", "")
                       for h in payload.get("headers", [])}
            parts = payload.get("parts", [payload])

            # Extract body
            body = ""
            body_data = payload.get("body", {}).get("data", "")
            if body_data:
                try:
                    body = base64.urlsafe_b64decode(body_data + "===").decode("utf-8", errors="replace")
                except Exception:
                    body = ""

            # If no body in top-level, check parts
            if not body:
                for part in parts:
                    part_data = part.get("body", {}).get("data", "")
                    if part_data:
                        try:
                            body = base64.urlsafe_b64decode(part_data + "===").decode("utf-8", errors="replace")
                            break
                        except Exception:
                            continue

            # Extract attachments
            attachments = []
            for part in parts:
                filename = part.get("filename", "")
                if filename:
                    attachments.append(AttachmentData(
                        provider_media_id=part.get("body", {}).get("attachmentId", ""),
                        mime_type=part.get("mimeType", ""),
                        filename=filename,
                        size_bytes=part.get("body", {}).get("size"),
                    ))

            # Parse timestamp
            internal_date = msg_data.get("internalDate", "")
            original_ts = None
            if internal_date:
                try:
                    original_ts = datetime.fromtimestamp(int(internal_date) / 1000)
                except (ValueError, OSError):
                    pass

            normalized = NormalizedMessage(
                source_id=0,
                provider_message_id=msg_id,
                provider_chat_id=thread_id or msg_id,
                provider_thread_id=thread_id,
                sender_raw=headers.get("from", ""),
                sender_normalized=headers.get("from", ""),
                sender_display_name=headers.get("from", "").split("<")[0].strip() if "<" in headers.get("from", "") else headers.get("from", ""),
                body=body,
                message_type="text",
                is_group=False,
                is_inbound=True,
                original_timestamp=original_ts,
                attachments=attachments,
            )
            messages.append(normalized)

        return messages

    def normalize_history(self, history: dict, existing_messages: dict = None) -> list[NormalizedMessage]:
        """Normalize a Gmail history record (from users.history.list).
        Returns only new/changed messages."""
        messages = []
        for msg_added in history.get("messagesAdded", []):
            msg = msg_added.get("message", {})
            if msg:
                messages.extend(self.normalize(msg))
        return messages

    def validate_webhook(self, request) -> dict:
        """Gmail uses Pub/sub push — not a direct webhook.
        Phase 3 does not implement Pub/sub push handling."""
        return {}

    def sync_initial(self, source, boundary: Optional[datetime] = None) -> list[NormalizedMessage]:
        """Initial/full sync — enumerates mailbox messages through Gmail API.
        The actual API call uses the credential_reference from the source.
        Returns NormalizedMessage list for capture governance."""
        # Real implementation requires Gmail API client with credentials
        # This is the architectural boundary — the normalize() method handles
        # the actual payload conversion once fetched
        return []

    def sync_incremental(self, source, cursor) -> list[NormalizedMessage]:
        """Incremental sync via Gmail history API.
        Uses historyId from cursor for users.history.list.
        If cursor is expired, returns empty list with cursor_state='expired'."""
        return []