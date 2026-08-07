"""EP-04 — Conversation Living Object.

A Conversation is a Living Object.
Every communication event belongs to exactly one Conversation.
Channels are interchangeable transports — Conversations are permanent.

SHUNYA does not organize communication by channel.
SHUNYA organizes communication by Conversation.
"""

import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    VOICE = "voice"
    VIDEO = "video"
    INTERNAL = "internal"
    CHAT = "chat"
    AI_SUMMARY = "ai_summary"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


@dataclass
class Message:
    """A single communication event within a Conversation.
    
    Channels are transport. The message is the content.
    """
    message_id: str
    conversation_id: str
    channel: ChannelType
    direction: MessageDirection
    sender: str
    body: str
    timestamp: str
    subject: str = ""
    attachments: list[dict] = field(default_factory=list)
    read: bool = False
    delivered: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Conversation:
    """A Conversation is a permanent Living Object.
    
    It connects people, companies, projects, commitments, and evidence.
    Channels are just transport — the conversation is the object.
    """
    conversation_id: str
    title: str
    participants: list[str] = field(default_factory=list)  # person ids
    company_ids: list[str] = field(default_factory=list)
    project_ids: list[str] = field(default_factory=list)
    object_ids: list[str] = field(default_factory=list)  # related Living Objects
    channel: ChannelType = ChannelType.EMAIL
    messages: list[Message] = field(default_factory=list)
    status: str = "active"  # active | archived | resolved
    created_at: str = ""
    updated_at: str = ""
    summary: str = ""
    ai_context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "participants": self.participants,
            "company_ids": self.company_ids,
            "project_ids": self.project_ids,
            "object_ids": self.object_ids,
            "channel": self.channel.value,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "summary": self.summary,
            "message_count": len(self.messages),
            "unread_count": sum(1 for m in self.messages if not m.read),
            "ai_context": self.ai_context,
        }

    def timeline(self) -> list[dict]:
        """Return the channel-independent timeline.
        
        The user sees work, not protocols.
        """
        timeline = []
        for msg in self.messages:
            kind = "reply" if msg.direction == MessageDirection.INBOUND else "sent"
            timeline.append({
                "timestamp": msg.timestamp,
                "kind": kind,
                "channel": msg.channel.value,
                "sender": msg.sender,
                "body": msg.body[:120],
                "subject": msg.subject,
            })
        timeline.sort(key=lambda x: x["timestamp"])
        return timeline


def create_conversation(title: str, participants: list[str] | None = None,
                        channel: ChannelType = ChannelType.EMAIL,
                        company_ids: list[str] | None = None,
                        project_ids: list[str] | None = None) -> Conversation:
    """Create a new Conversation Living Object."""
    now = datetime.now(timezone.utc).isoformat()
    return Conversation(
        conversation_id=f"conv_{uuid.uuid4().hex[:12]}",
        title=title,
        participants=participants or [],
        company_ids=company_ids or [],
        project_ids=project_ids or [],
        channel=channel,
        created_at=now,
        updated_at=now,
    )


def add_message(conversation: Conversation, channel: ChannelType,
                direction: MessageDirection, sender: str, body: str,
                subject: str = "", attachments: list[dict] | None = None) -> Message:
    """Attach a message to a conversation."""
    now = datetime.now(timezone.utc).isoformat()
    msg = Message(
        message_id=f"msg_{uuid.uuid4().hex[:12]}",
        conversation_id=conversation.conversation_id,
        channel=channel,
        direction=direction,
        sender=sender,
        body=body,
        subject=subject,
        attachments=attachments or [],
        timestamp=now,
    )
    conversation.messages.append(msg)
    conversation.updated_at = now
    return msg