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
from typing import Optional
from .conversation import ChannelType, Message, Conversation


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
        return []

    def history(self, conversation_id: str, limit: int = 50) -> list[Message]:
        return []

    def status(self) -> dict:
        return {"connected": self._connected, "channel": "email", "error": None}