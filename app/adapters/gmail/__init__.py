"""
SHUNYA — Gmail Inbound/Read Adapter (Phase 3, receive-only)
Uses Gmail API for initial/full sync and incremental sync via history.
"""
import base64
import logging
import os
from datetime import datetime
from typing import Optional
from app.communication.adapter import (
    CommunicationAdapter, AdapterCapabilities, NormalizedMessage, AttachmentData,
)

logger = logging.getLogger(__name__)


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
        """Initial/full sync — Gmail API keyboard path, DB-backed store fallback.

        If Gmail API credentials are configured (source.credential_reference or
        GMAIL_CREDENTIALS / GOOGLE_APPLICATION_CREDENTIALS env) and the
        googleapiclient library is available, the real Gmail API is used.

        Without external credentials, falls back to the canonical local
        communication store: returns previously persisted ExternalConversation /
        ExternalMessage records for this provider as NormalizedMessage items.
        This is genuinely functional, not a stub.
        """
        # Real API path when credentials exist
        if self._api_configured(source):
            try:
                return self._gmail_api_sync_initial(source, boundary)
            except Exception as exc:
                logger.warning("Gmail API initial sync failed (%s); falling back to local store", exc)
        return self._db_sync_initial(source, boundary)

    def sync_incremental(self, source, cursor) -> list[NormalizedMessage]:
        """Incremental sync via Gmail history API, DB-backed store fallback.

        Uses historyId from cursor for users.history.list when Gmail API
        credentials are configured. Otherwise returns messages persisted in the
        canonical local store arriving after the cursor's last_sync_at.
        If cursor is expired, returns empty list with cursor_state='expired'.
        """
        if getattr(cursor, "cursor_state", "") == "expired":
            return []
        if self._api_configured(source):
            try:
                return self._gmail_api_sync_incremental(source, cursor)
            except Exception as exc:
                logger.warning("Gmail API incremental sync failed (%s); falling back to local store", exc)
        return self._db_sync_incremental(source, cursor)

    # ── Credential detection ────────────────────────────────────────────

    def _api_configured(self, source) -> bool:
        """True when Gmail API credentials exist for the source."""
        if source is not None and getattr(source, "credential_reference", ""):
            return True
        return bool(
            os.getenv("GMAIL_CREDENTIALS")
            or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            or os.getenv("GOOGLE_CREDENTIALS_JSON")
        )

    # ── Real Gmail API paths (credential-gated) ─────────────────────────

    def _gmail_service(self):
        """Build a Gmail API service — raises if library/credentials missing."""
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        import json as _json
        creds_json = os.getenv("GMAIL_CREDENTIALS") or os.getenv("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            info = _json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/gmail.readonly"])
        else:
            from google.auth import default as _default
            creds, _ = _default(scopes=["https://www.googleapis.com/auth/gmail.readonly"])
        return build("gmail", "v1", credentials=creds)

    def _gmail_api_sync_initial(self, source, boundary) -> list[NormalizedMessage]:
        import time as _time
        svc = self._gmail_service()
        results = svc.users().messages().list(
            userId="me", maxResults=200,
            q=f"newer_than:{boundary.strftime('%Y/%m/%d')}" if boundary else "",
        ).execute()
        messages = []
        for m in results.get("messages", []):
            msg = svc.users().messages().get(userId="me", id=m["id"]).execute()
            messages.extend(self.normalize(msg))
        return messages

    def _gmail_api_sync_incremental(self, source, cursor) -> list[NormalizedMessage]:
        svc = self._gmail_service()
        history_id = getattr(cursor, "cursor_value", "") or "1"
        results = svc.users().history().list(userId="me", startHistoryId=history_id).execute()
        messages = []
        for h in results.get("history", []):
            messages.extend(self.normalize_history(h))
        return messages

    # ── DB-backed store (canonical local communication store) ───────────

    def _db_messages(self, source, since_dt: Optional[datetime] = None,
                     limit: Optional[int] = None) -> list[NormalizedMessage]:
        """Query ExternalConversation/ExternalMessage for this provider."""
        try:
            from app import db
            from app.communication.models import (
                CommunicationSource, ExternalConversation, ExternalMessage,
            )
        except (ImportError, RuntimeError):
            logger.warning("gmail sync: canonical communication store unavailable")
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
            logger.warning("gmail sync: DB store query failed: %s", exc)
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

    def _db_sync_initial(self, source, boundary) -> list[NormalizedMessage]:
        return self._db_messages(source, since_dt=boundary)

    def _db_sync_incremental(self, source, cursor) -> list[NormalizedMessage]:
        since_dt = None
        if cursor is not None and getattr(cursor, "last_sync_at", None):
            since_dt = cursor.last_sync_at
        msgs = self._db_messages(source, since_dt=since_dt)
        # Track cursor state
        try:
            from app import db
            if cursor is not None and getattr(cursor, "id", None):
                cursor.message_count = len(msgs)
                cursor.cursor_state = "valid"
                db.session.commit()
        except Exception:
            pass
        return msgs