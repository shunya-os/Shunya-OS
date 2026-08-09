"""
SHUNYA — Communication Models (Phase 3)
CommunicationSource, CapturePolicy, CaptureScope, ExternalConversation, ExternalMessage,
ExternalParticipant, ExternalAttachmentReference, SyncCursor
"""
from datetime import datetime, timezone
from app import db
from sqlalchemy import Index, Text as SA_Text


# ---------------------------------------------------------------------------
# CommunicationSource
# ---------------------------------------------------------------------------

class CommunicationSource(db.Model):
    """A configured communication provider account (Gmail, WhatsApp, etc.)."""
    __tablename__ = "communication_sources"
    __table_args__ = (
        Index("ix_comm_source_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    provider = db.Column(db.String(60), nullable=False)  # "gmail", "whatsapp_official", "whatsapp_free", "telegram"
    account_identifier = db.Column(db.String(255), nullable=False)  # email, phone_number_id
    account_mode = db.Column(db.String(30), nullable=False, default="business_dedicated")  # business_dedicated, mixed_use
    credential_reference = db.Column(db.String(255), default="")
    capabilities_json = db.Column(db.Text, default="{}")
    metadata_json = db.Column(db.Text, default="{}")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CommunicationSource #{self.id} {self.provider}:{self.account_identifier}>"


# ---------------------------------------------------------------------------
# CapturePolicy
# ---------------------------------------------------------------------------

class CommunicationCapturePolicy(db.Model):
    """Capture governance rules for a communication source."""
    __tablename__ = "communication_capture_policies"
    __table_args__ = (
        Index("ix_ccp_source", "source_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey("communication_sources.id"), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)

    account_mode = db.Column(db.String(30), nullable=False, default="business_dedicated")

    default_chat_policy = db.Column(db.String(30), default="pending_review")  # allowed, denied, pending_review
    default_group_policy = db.Column(db.String(30), default="pending_review")
    unknown_contact_policy = db.Column(db.String(30), default="pending_review")
    media_policy = db.Column(db.String(30), default="metadata_only")  # metadata_only, content_routing

    historical_sync_boundary = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = db.relationship("CommunicationSource", backref="capture_policies", lazy="select")

    def __repr__(self):
        return f"<CapturePolicy #{self.id} source={self.source_id} mode={self.account_mode}>"


# ---------------------------------------------------------------------------
# CaptureScope
# ---------------------------------------------------------------------------

class CommunicationCaptureScope(db.Model):
    """Per-chat/conversation capture allow/deny decision."""
    __tablename__ = "communication_capture_scopes"
    __table_args__ = (
        Index("ix_ccs_source_chat", "source_id", "external_chat_id"),
        Index("ix_ccs_status", "status"),
        Index("ix_ccs_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    source_id = db.Column(db.Integer, db.ForeignKey("communication_sources.id"), nullable=False, index=True)
    external_chat_id = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending_review")  # allowed, denied, pending_review
    approved_by = db.Column(db.String(120), default="")
    approved_at = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = db.relationship("CommunicationSource", backref="capture_scopes", lazy="select")

    def __repr__(self):
        return f"<CaptureScope #{self.id} chat={self.external_chat_id} status={self.status}>"


# ---------------------------------------------------------------------------
# ExternalConversation
# ---------------------------------------------------------------------------

class ExternalConversation(db.Model):
    """Normalized conversation from any communication source."""
    __tablename__ = "external_conversations"
    __table_args__ = (
        Index("ix_extconv_source", "source_id"),
        Index("ix_extconv_tenant", "tenant_id"),
        Index("ix_extconv_provider_chat", "source_id", "provider_chat_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    source_id = db.Column(db.Integer, db.ForeignKey("communication_sources.id"), nullable=False, index=True)
    provider_chat_id = db.Column(db.String(255), nullable=False)
    conversation_type = db.Column(db.String(30), default="direct")  # direct, group, channel
    subject = db.Column(db.String(500), default="")
    message_count = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, nullable=True)
    latest_message_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = db.relationship("CommunicationSource", backref="conversations", lazy="select")

    def __repr__(self):
        return f"<ExternalConversation #{self.id} {self.provider_chat_id[:30]}>"


# ---------------------------------------------------------------------------
# ExternalMessage
# ---------------------------------------------------------------------------

class ExternalMessage(db.Model):
    """Normalized message from any communication source.
    DENIED/PENDING messages have body=None."""
    __tablename__ = "external_messages"
    __table_args__ = (
        Index("ix_extmsg_conversation", "conversation_id"),
        Index("ix_extmsg_provider", "source_id", "provider_message_id"),
        Index("ix_extmsg_received", "received_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    source_id = db.Column(db.Integer, db.ForeignKey("communication_sources.id"), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey("external_conversations.id"), nullable=False, index=True)
    provider_message_id = db.Column(db.String(255), nullable=False)
    sender_participant_id = db.Column(db.Integer, db.ForeignKey("external_participants.id"), nullable=True)
    body = db.Column(db.Text, nullable=True)  # None if DENIED/PENDING
    capture_status = db.Column(db.String(30), default="allowed")  # allowed, denied, pending_review
    message_type = db.Column(db.String(30), default="text")
    direction = db.Column(db.String(10), default="inbound")  # inbound, outbound
    provider_thread_id = db.Column(db.String(255), default="")
    original_timestamp = db.Column(db.DateTime, nullable=True)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversation = db.relationship("ExternalConversation", backref="messages", lazy="select")

    def __repr__(self):
        return f"<ExternalMessage #{self.id} [{self.capture_status}] conv={self.conversation_id}>"


# ---------------------------------------------------------------------------
# ExternalParticipant
# ---------------------------------------------------------------------------

class ExternalParticipant(db.Model):
    """Normalized participant in an external conversation.
    May remain unresolved — no canonical Person required."""
    __tablename__ = "external_participants"
    __table_args__ = (
        Index("ix_extpart_source", "source_id"),
        Index("ix_extpart_person", "person_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    source_id = db.Column(db.Integer, db.ForeignKey("communication_sources.id"), nullable=False)
    provider_participant_id = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), default="")
    raw_identifier = db.Column(db.String(255), default="")

    # Optional canonical linking
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)
    identity_resolution_status = db.Column(db.String(30), default="unresolved")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    source = db.relationship("CommunicationSource", backref="participants", lazy="select")
    person = db.relationship("Person", backref="external_participants", lazy="select")

    def __repr__(self):
        return f"<ExternalParticipant #{self.id} {self.display_name} [{self.identity_resolution_status}]>"


# ---------------------------------------------------------------------------
# ExternalAttachmentReference
# ---------------------------------------------------------------------------

class ExternalAttachmentReference(db.Model):
    """Metadata-only reference for media attached to a message.
    No body storage in Phase 3."""
    __tablename__ = "external_attachment_references"
    __table_args__ = (
        Index("ix_extatt_message", "message_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("external_messages.id"), nullable=False, index=True)
    provider_media_id = db.Column(db.String(255), default="")
    mime_type = db.Column(db.String(120), default="")
    filename = db.Column(db.String(500), default="")
    size_bytes = db.Column(db.BigInteger, nullable=True)
    routing_status = db.Column(db.String(30), default="pending_review")
    provider_metadata = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    message = db.relationship("ExternalMessage", backref="attachments", lazy="select")

    def __repr__(self):
        return f"<AttachmentRef #{self.id} {self.mime_type} msg={self.message_id}>"


# ---------------------------------------------------------------------------
# SyncCursor
# ---------------------------------------------------------------------------

class SyncCursor(db.Model):
    """Resumable sync state for a communication source."""
    __tablename__ = "sync_cursors"
    __table_args__ = (
        Index("ix_sync_source", "source_id"),
        Index("ix_sync_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    source_id = db.Column(db.Integer, db.ForeignKey("communication_sources.id"), nullable=False, index=True)
    sync_type = db.Column(db.String(30), nullable=False)  # initial, incremental
    cursor_value = db.Column(db.Text, default="")
    cursor_state = db.Column(db.String(30), default="valid")  # valid, expired, recovering
    last_sync_at = db.Column(db.DateTime, nullable=True)
    message_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = db.relationship("CommunicationSource", backref="sync_cursors", lazy="select")

    def __repr__(self):
        return f"<SyncCursor #{self.id} {self.sync_type} source={self.source_id} [{self.cursor_state}]>"


# ---------------------------------------------------------------------------
# OAuthState — OAuth flow state tracking for CSRF protection
# ---------------------------------------------------------------------------


class OAuthState(db.Model):
    """Tracks pending OAuth states for CSRF protection during flow."""

    __tablename__ = "oauth_states"
    __table_args__ = (
        Index("ix_oauth_state_provider", "provider"),
        Index("ix_oauth_state_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    provider = db.Column(db.String(60), nullable=False)  # "gmail", "whatsapp", etc.
    state = db.Column(db.String(128), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tenant = db.relationship("Tenant", backref="oauth_states", lazy="select")

    def __repr__(self):
        return f"<OAuthState #{self.id} {self.provider}:{self.state[:16]}...>"


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    entity_id = db.Column(db.Integer, index=True, nullable=False)

    direction = db.Column(db.String(20))  # inbound / outbound
    channel = db.Column(db.String(50))    # whatsapp / email / system

    content = db.Column(db.Text)

    status = db.Column(db.String(50), default="pending")  # pending / sent / failed

    metadata_json = db.Column(db.JSON, default={})

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class MessageLog(db.Model):
    __tablename__ = "message_logs"

    id = db.Column(db.Integer, primary_key=True)
    to = db.Column(db.String(64), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)