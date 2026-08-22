"""EP-04 — Universal Communication Runtime.

SHUNYA does not organize communication by channel.
SHUNYA organizes communication by Conversation.

The runtime:
  - Creates Conversation Living Objects
  - Attaches messages from any channel
  - Attaches participants
  - Emits Reality events
  - Generates AI summaries
  - Generates Commitments
  - Relates Conversations to Companies, People, Projects
  - Exposes unified search
  - Exposes unified timeline
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from .conversation import (
    Conversation, Message, ChannelType, MessageDirection,
    create_conversation, add_message,
)
from .adapters import ProviderAdapter

logger = logging.getLogger(__name__)


class CommunicationRuntime:
    """The single canonical communication runtime for SHUNYA."""

    def __init__(self):
        self._adapters: dict[ChannelType, ProviderAdapter] = {}
        self._conversations: dict[str, Conversation] = {}
        self._register_builtin_adapters()

    def _register_builtin_adapters(self) -> None:
        """Register built-in provider adapters."""
        from .adapters import InternalNotesAdapter, EmailAdapter
        self.register_adapter(InternalNotesAdapter())
        self.register_adapter(EmailAdapter())

    def register_adapter(self, adapter: ProviderAdapter) -> None:
        """Register a provider adapter.
        
        Adding a new provider requires only calling this method.
        No provider-specific UI ever needed.
        """
        self._adapters[adapter.channel_type] = adapter
        adapter.connect()

    def get_adapter(self, channel: ChannelType) -> Optional[ProviderAdapter]:
        return self._adapters.get(channel)

    def get_or_create_conversation(
        self, title: str, participants: list[str] | None = None,
        channel: ChannelType = ChannelType.EMAIL,
        company_ids: list[str] | None = None,
        project_ids: list[str] | None = None,
    ) -> Conversation:
        """Find or create a conversation by title + participants.
        
        In production, this would search existing conversations first.
        """
        conv = create_conversation(
            title=title,
            participants=participants,
            channel=channel,
            company_ids=company_ids,
            project_ids=project_ids,
        )
        self._conversations[conv.conversation_id] = conv
        self._emit_reality(conv, "conversation_created")
        return conv

    def send_message(self, conversation_id: str, body: str,
                     subject: str = "", channel: ChannelType | None = None) -> Optional[Message]:
        """Send a message through the appropriate provider.
        
        The workspace never knows provider-specific APIs.
        """
        conv = self._conversations.get(conversation_id)
        if not conv:
            logger.error(f"Conversation {conversation_id} not found")
            return None

        channel = channel or conv.channel
        adapter = self.get_adapter(channel)
        if not adapter:
            logger.error(f"No adapter for channel {channel}")
            return None

        msg = adapter.send(conv, body, subject=subject)
        if msg:
            self._emit_reality(conv, "message_sent", msg)
        return msg

    def receive_messages(self, conversation_id: str,
                         channel: ChannelType | None = None) -> list[Message]:
        """Receive messages from a provider."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return []

        channel = channel or conv.channel
        adapter = self.get_adapter(channel)
        if not adapter:
            return []

        messages = adapter.receive(conversation_id)
        for msg in messages:
            self._emit_reality(conv, "message_received", msg)
        return messages

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    def list_conversations(self, limit: int = 50) -> list[Conversation]:
        """List all conversations, sorted by most recent."""
        convs = sorted(
            self._conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        return convs[:limit]

    def search(self, query: str) -> list[dict]:
        """Unified search across all conversations.
        
        Searches: messages, summaries, participants, subjects.
        """
        results = []
        q = query.lower()
        for conv in self._conversations.values():
            score = 0
            if q in conv.title.lower():
                score += 10
            for p in conv.participants:
                if q in p.lower():
                    score += 5
            if q in conv.summary.lower():
                score += 3
            for msg in conv.messages:
                if q in msg.body.lower():
                    score += 2
                if q in msg.subject.lower():
                    score += 1
            if score > 0:
                results.append({"conversation": conv.to_dict(), "score": score})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:20]

    def get_unified_timeline(self, conversation_id: str) -> list[dict]:
        """Channel-independent timeline.
        
        The user sees work, not protocols.
        Every channel renders identically in the timeline.
        """
        conv = self._conversations.get(conversation_id)
        if not conv:
            return []
        return conv.timeline()

    def generate_summary(self, conversation_id: str) -> str:
        """Generate an AI summary of the conversation.
        
        The AI summarizes Conversations, not individual messages.
        """
        conv = self._conversations.get(conversation_id)
        if not conv:
            return ""

        message_count = len(conv.messages)
        participants = ", ".join(str(p) for p in conv.participants) if conv.participants else "Unknown"
        last_message = conv.messages[-1].body[:200] if conv.messages else "No messages"

        summary = (
            f"Conversation: {conv.title}. "
            f"{message_count} messages across {conv.channel.value}. "
            f"Participants: {participants}. "
            f"Last message: {last_message}"
        )
        conv.summary = summary
        return summary

    def _emit_reality(self, conv: Conversation, event_type: str,
                      msg: Message | None = None) -> None:
        """Emit a Reality Event for this communication event."""
        try:
            from app.reality_engine.engine import get_reality_engine
            engine = get_reality_engine()
            engine.notify({
                "type": event_type,
                "identity_id": "system",
                "conversation_id": conv.conversation_id,
                "title": conv.title,
                "participants": conv.participants,
            })
        except Exception:
            pass


# ── Singleton ────────────────────────────────────────────────────

_RUNTIME_INSTANCE: Optional[CommunicationRuntime] = None


def get_communication_runtime() -> CommunicationRuntime:
    global _RUNTIME_INSTANCE
    if _RUNTIME_INSTANCE is None:
        _RUNTIME_INSTANCE = CommunicationRuntime()
    return _RUNTIME_INSTANCE