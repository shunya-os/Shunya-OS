"""
SHUNYA — Communication Adapter Contract (Phase 3)
Receive-only inbound communication adapters.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AdapterCapabilities:
    """Declared capabilities of a communication adapter.
    Phase 3: receive-only. supports_outbound is declaration only."""
    supports_initial_sync: bool = False
    supports_historical_sync: bool = False
    supports_incremental_sync: bool = False
    supports_webhook_receive: bool = False
    supports_threading: bool = False
    supports_groups: bool = False
    supports_media_metadata: bool = False
    supports_outbound: bool = False  # Declaration only — Phase 16A


@dataclass
class NormalizedMessage:
    """Canonical inbound communication input after normalization.
    Provider-specific payloads must not leak into this structure."""
    source_id: int
    provider_message_id: str
    provider_chat_id: str
    provider_thread_id: str = ""
    sender_raw: str = ""
    sender_normalized: str = ""
    sender_display_name: str = ""
    body: str = ""
    message_type: str = "text"  # text, image, video, document, audio, template
    is_group: bool = False
    is_inbound: bool = True
    original_timestamp: Optional[datetime] = None
    attachments: list = field(default_factory=list)  # list of AttachmentData


@dataclass
class AttachmentData:
    """Metadata-only attachment data. No body in Phase 3."""
    provider_media_id: str = ""
    mime_type: str = ""
    filename: str = ""
    size_bytes: Optional[int] = None
    provider_metadata: str = "{}"


class CommunicationAdapter:
    """Base contract for all communication source adapters.
    Phase 3: receive-only. No outbound execution."""

    @property
    def capabilities(self) -> AdapterCapabilities:
        raise NotImplementedError

    @property
    def provider(self) -> str:
        raise NotImplementedError

    def normalize(self, raw_payload: dict) -> list[NormalizedMessage]:
        """Normalize a raw provider payload into canonical communication input.
        Must not create Person, Relationship, Lead, or call LLM."""
        raise NotImplementedError

    def sync_initial(self, source: "CommunicationSource", boundary: Optional[datetime] = None) -> list[NormalizedMessage]:
        """Initial/full sync of eligible messages. Only if supports_initial_sync."""
        raise NotImplementedError

    def sync_incremental(self, source: "CommunicationSource", cursor: "SyncCursor") -> list[NormalizedMessage]:
        """Incremental sync. Only if supports_incremental_sync."""
        raise NotImplementedError

    def validate_webhook(self, request) -> dict:
        """Validate webhook authenticity. Returns parsed payload dict."""
        raise NotImplementedError

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "capabilities": {
                "initial_sync": self.capabilities.supports_initial_sync,
                "historical_sync": self.capabilities.supports_historical_sync,
                "incremental_sync": self.capabilities.supports_incremental_sync,
                "webhook_receive": self.capabilities.supports_webhook_receive,
                "threading": self.capabilities.supports_threading,
                "groups": self.capabilities.supports_groups,
                "media_metadata": self.capabilities.supports_media_metadata,
                "outbound": self.capabilities.supports_outbound,
            },
        }