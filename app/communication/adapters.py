"""EP-04 — Provider Adapter Interface.

Every communication provider must implement this interface.
Providers are interchangeable — the workspace never knows provider-specific APIs.

Supported adapters (planned):
  - IMAP/SMTP (email)
  - Gmail API
  - Microsoft Graph API
  - WhatsApp Business API
  - Twilio-compatible SMS
  - SIP / VoIP
  - Video providers (Jitsi, etc.)
  - Internal notes
"""

from abc import ABC, abstractmethod
import logging
from datetime import datetime
from typing import Optional
from .conversation import ChannelType, Message, Conversation

logger = logging.getLogger(__name__)


class ProviderAdapter(ABC):
    """Abstract base for all communication providers.
    
    Every adapter exposes identical capabilities.
    The workspace code must never know provider-specific APIs.
    """

    @property
    @abstractmethod
    def channel_type(self) -> ChannelType:
        """The channel this adapter handles."""
        ...

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the provider.
        
        Returns True if connected successfully.
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close the provider connection."""
        ...

    @abstractmethod
    def send(self, conversation: Conversation, body: str,
             subject: str = "") -> Optional[Message]:
        """Send a message through this provider."""
        ...

    @abstractmethod
    def receive(self, conversation_id: str,
                since: Optional[str] = None) -> list[Message]:
        """Receive new messages for a conversation."""
        ...

    @abstractmethod
    def history(self, conversation_id: str,
                limit: int = 50) -> list[Message]:
        """Get message history for a conversation."""
        ...

    @abstractmethod
    def status(self) -> dict:
        """Return provider connection status.
        
        Returns: { connected: bool, channel: str, error: str | None }
        """
        ...


class InternalNotesAdapter(ProviderAdapter):
    """Internal notes / comments — the simplest adapter.
    
    This is the reference implementation all other adapters should mirror.
    """

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.INTERNAL

    def __init__(self):
        self._connected = True
        self._message_store: dict[str, list[Message]] = {}

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def send(self, conversation: Conversation, body: str,
             subject: str = "") -> Optional[Message]:
        from .conversation import add_message, MessageDirection
        msg = add_message(
            conversation=conversation,
            channel=ChannelType.INTERNAL,
            direction=MessageDirection.OUTBOUND,
            sender="system",
            body=body,
            subject=subject,
        )
        cid = conversation.conversation_id
        if cid not in self._message_store:
            self._message_store[cid] = []
        self._message_store[cid].append(msg)
        return msg

    def receive(self, conversation_id: str,
                since: Optional[str] = None) -> list[Message]:
        return self._message_store.get(conversation_id, [])

    def history(self, conversation_id: str, limit: int = 50) -> list[Message]:
        msgs = self._message_store.get(conversation_id, [])
        return msgs[-limit:]

    def status(self) -> dict:
        return {"connected": self._connected, "channel": "internal", "error": None}


class EmailAdapter(ProviderAdapter):
    """Email adapter via IMAP/SMTP. Reference implementation.
    
    In production, this would connect to real IMAP/SMTP servers.
    Currently a stub — the adapter interface is the contract.
    """

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.EMAIL

    def __init__(self, imap_host: str = "", smtp_host: str = ""):
        self._connected = False
        self._imap_host = imap_host
        self._smtp_host = smtp_host

    def connect(self) -> bool:
        # In production: IMAP4_SSL(self._imap_host).login()
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def send(self, conversation: Conversation, body: str,
             subject: str = "") -> Optional[Message]:
        from .conversation import add_message, MessageDirection
        return add_message(
            conversation=conversation,
            channel=ChannelType.EMAIL,
            direction=MessageDirection.OUTBOUND,
            sender="system",
            body=body,
            subject=subject,
        )

    def receive(self, conversation_id: str,
                since: Optional[str] = None) -> list[Message]:
        """Receive new inbound messages for a conversation.

        Queries the canonical local communication store (ExternalConversation /
        ExternalMessage tables) for messages matching conversation_id.
        In production with IMAP configured, this would poll the mail server;
        the DB-backed store is the genuine fallback that returns persisted
        inbound messages instead of silently returning [].
        """
        try:
            rows = self._db_messages(conversation_id, inbound_only=True, since=since)
        except Exception:
            logger.warning("EmailAdapter.receive: DB store query failed", exc_info=True)
            return []
        return rows

    def history(self, conversation_id: str, limit: int = 50) -> list[Message]:
        """Get message history for a conversation from the canonical store.

        Returns up to `limit` most recent messages (both directions) for the
        conversation, ordered newest-first, from ExternalConversation /
        ExternalMessage records. Falls back gracefully when the store is empty.
        """
        try:
            rows = self._db_messages(conversation_id, inbound_only=False, limit=limit)
        except Exception:
            logger.warning("EmailAdapter.history: DB store query failed", exc_info=True)
            return []
        return rows[:limit]

    def _db_messages(self, conversation_id: str, inbound_only: bool,
                     since: Optional[str] = None,
                     limit: Optional[int] = None) -> list[Message]:
        """Query ExternalMessage/ExternalConversation for a conversation."""
        from .conversation import Message as ConvMessage, ChannelType, MessageDirection
        from app import db
        from app.communication.models import ExternalConversation, ExternalMessage

        conv_id = conversation_id
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                if since_dt.tzinfo is None:
                    from datetime import timezone
                    since_dt = since_dt.replace(tzinfo=timezone.utc)
            except ValueError:
                since_dt = None
        else:
            since_dt = None

        q = (
            db.session.query(ExternalMessage)
            .join(ExternalConversation, ExternalMessage.conversation_id == ExternalConversation.id)
            .filter(
                (ExternalConversation.provider_chat_id == conv_id)
                | (ExternalConversation.subject == conv_id)
            )
        )
        if inbound_only:
            q = q.filter(ExternalMessage.direction == "inbound")
        if since_dt is not None:
            q = q.filter(ExternalMessage.received_at >= since_dt)
        q = q.order_by(ExternalMessage.received_at.desc())
        if limit:
            q = q.limit(limit)
        rows = q.all()

        messages = []
        for exm in rows:
            messages.append(ConvMessage(
                message_id=f"msg_ext_{exm.id}" if exm.id else exm.provider_message_id,
                conversation_id=conv_id,
                channel=ChannelType.EMAIL,
                direction=MessageDirection.INBOUND if exm.direction != "outbound" else MessageDirection.OUTBOUND,
                sender=str(exm.sender_participant_id or ""),
                body=exm.body or "",
                subject=exm.conversation.subject if exm.conversation else "",
                timestamp=(exm.received_at or exm.original_timestamp).isoformat() if (exm.received_at or exm.original_timestamp) else "",
                read=True,
            ))
        return messages

    def status(self) -> dict:
        return {"connected": self._connected, "channel": "email", "error": None}