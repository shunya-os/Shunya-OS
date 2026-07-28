"""
SHUNYA — Message Normalizer (Phase 3)
Normalizes raw provider payloads into canonical ExternalMessage format.
Structural only — no Person, Relationship, Lead, LLM or intelligence inference.
"""
from datetime import datetime
from typing import Optional
from app import db
from app.communication.models import (
    ExternalConversation, ExternalMessage, ExternalParticipant,
    ExternalAttachmentReference,
)
from app.communication.adapter import NormalizedMessage, AttachmentData


class MessageNormalizer:
    """Normalizes inbound communication into canonical models.
    Normalization is structural and capture-governed."""

    def __init__(self, session=None):
        self._session = session or db.session

    def ensure_conversation(self, source_id: int, provider_chat_id: str,
                            tenant_id: Optional[int] = None,
                            conversation_type: str = "direct",
                            subject: str = "") -> ExternalConversation:
        """Find or create a conversation. Idempotent by source + provider_chat_id."""
        existing = self._session.query(ExternalConversation).filter_by(
            source_id=source_id,
            provider_chat_id=provider_chat_id,
        ).first()
        if existing:
            return existing
        conv = ExternalConversation(
            tenant_id=tenant_id,
            source_id=source_id,
            provider_chat_id=provider_chat_id,
            conversation_type=conversation_type,
            subject=subject,
            started_at=datetime.utcnow(),
        )
        self._session.add(conv)
        self._session.flush()
        return conv

    def ensure_participant(self, source_id: int, provider_participant_id: str,
                           display_name: str = "",
                           raw_identifier: str = "",
                           tenant_id: Optional[int] = None) -> ExternalParticipant:
        """Find or create a participant. Idempotent by source + provider_participant_id."""
        existing = self._session.query(ExternalParticipant).filter_by(
            source_id=source_id,
            provider_participant_id=provider_participant_id,
        ).first()
        if existing:
            return existing
        participant = ExternalParticipant(
            tenant_id=tenant_id,
            source_id=source_id,
            provider_participant_id=provider_participant_id,
            display_name=display_name,
            raw_identifier=raw_identifier,
            identity_resolution_status="unresolved",
        )
        self._session.add(participant)
        self._session.flush()
        return participant

    def normalize_message(self, normalized: NormalizedMessage,
                          tenant_id: Optional[int] = None,
                          capture_status: str = "allowed") -> ExternalMessage:
        """Create an ExternalMessage from a normalized communication input.
        If capture_status is denied/pending_review, body is None."""
        conv = self.ensure_conversation(
            source_id=normalized.source_id,
            provider_chat_id=normalized.provider_chat_id,
            tenant_id=tenant_id,
            conversation_type="group" if normalized.is_group else "direct",
        )

        participant = None
        if normalized.sender_raw:
            participant = self.ensure_participant(
                source_id=normalized.source_id,
                provider_participant_id=normalized.sender_raw,
                display_name=normalized.sender_display_name,
                raw_identifier=normalized.sender_normalized,
                tenant_id=tenant_id,
            )

        # Check for existing message by provider_message_id (idempotency)
        existing = self._session.query(ExternalMessage).filter_by(
            source_id=normalized.source_id,
            provider_message_id=normalized.provider_message_id,
        ).first()
        if existing:
            return existing

        body = normalized.body if capture_status == "allowed" else None

        msg = ExternalMessage(
            tenant_id=tenant_id,
            source_id=normalized.source_id,
            conversation_id=conv.id,
            provider_message_id=normalized.provider_message_id,
            sender_participant_id=participant.id if participant else None,
            body=body,
            capture_status=capture_status,
            message_type=normalized.message_type,
            direction="inbound" if normalized.is_inbound else "outbound",
            provider_thread_id=normalized.provider_thread_id,
            original_timestamp=normalized.original_timestamp,
            received_at=datetime.utcnow(),
        )
        self._session.add(msg)
        self._session.flush()

        # Update conversation metadata
        conv.message_count = (conv.message_count or 0) + 1
        conv.latest_message_at = datetime.utcnow()

        # Create attachment references (metadata only)
        for att in normalized.attachments:
            ref = ExternalAttachmentReference(
                message_id=msg.id,
                provider_media_id=att.provider_media_id,
                mime_type=att.mime_type,
                filename=att.filename,
                size_bytes=att.size_bytes,
                provider_metadata=att.provider_metadata,
            )
            self._session.add(ref)

        self._session.commit()
        return msg

    def normalize_batch(self, messages: list[NormalizedMessage],
                        tenant_id: Optional[int] = None,
                        capture_status: str = "allowed") -> list[ExternalMessage]:
        """Normalize a batch of messages."""
        result = []
        for m in messages:
            result.append(self.normalize_message(m, tenant_id, capture_status))
        return result