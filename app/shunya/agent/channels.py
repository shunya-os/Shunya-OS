"""Shunya Personal Agent — Channel Continuity Layer.

Every channel normalizes to AgentRequest → AgentLoop → AgentResponse → channel render.
Users can start on Web, continue on WhatsApp, the agent remembers.
"""
from __future__ import annotations
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json, logging

logger = logging.getLogger("app.shunya.agent.channels")


# ---------------------------------------------------------------------------
# Unified types
# ---------------------------------------------------------------------------

@dataclass
class AgentRequest:
    """Normalized request from any channel."""
    user_id: int
    tenant_id: int
    channel: str           # "web", "whatsapp", "telegram", "voice"
    text: str
    thread_id: str         # Channel-specific conversation ID
    user_name: str = ""
    attachments: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Normalized response to any channel."""
    text: str
    channel: str
    thread_id: str
    actions: list[dict] = field(default_factory=list)  # Buttons, quick replies
    attachments: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Session Continuity — maps channel identities to Shunya users
# ---------------------------------------------------------------------------

class SessionMapper:
    """
    Maps channel-specific identities (phone number, Telegram chat ID) to
    Shunya users. Enables cross-channel continuity: a user's session follows
    them from Web → WhatsApp → Telegram.
    """

    def __init__(self):
        self._cache: dict[str, dict] = {}  # channel:identity → {user_id, tenant_id}

    def resolve(self, channel: str, identity: str) -> Optional[dict]:
        """Resolve a channel identity to a Shunya user."""
        key = f"{channel}:{identity}"

        # Check hot cache
        cached = self._cache.get(key)
        if cached:
            return cached

        # Check database
        from app.models import TeamMember
        user = None
        if channel == "whatsapp":
            user = TeamMember.query.filter_by(phone=identity).first()
        elif channel == "telegram":
            user = TeamMember.query.filter_by(phone=identity).first()  # or telegram_id field
        elif channel == "web":
            # Web sessions are handled via Flask session — identity is user_id
            return None

        if not user:
            return None

        result = {"user_id": user.id, "tenant_id": user.tenant_id, "name": user.name}
        self._cache[key] = result
        return result

    def register(self, channel: str, identity: str, user_id: int, tenant_id: int):
        """Register a channel identity for a user."""
        key = f"{channel}:{identity}"
        self._cache[key] = {"user_id": user_id, "tenant_id": tenant_id}

    def generate_thread_id(self, channel: str, identity: str) -> str:
        """Generate a consistent thread ID for a channel+identity pair."""
        import hashlib
        raw = f"{channel}:{identity}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]


_session_mapper = SessionMapper()


def get_session_mapper() -> SessionMapper:
    return _session_mapper


# ---------------------------------------------------------------------------
# Channel Adapter — base class
# ---------------------------------------------------------------------------

class ChannelAdapter:
    """Base class for channel adapters. Each channel implements this."""

    channel_name: str = ""

    def request_from_incoming(self, payload: dict) -> Optional[AgentRequest]:
        """Parse incoming webhook payload into AgentRequest."""
        raise NotImplementedError

    def render_response(self, response: AgentResponse) -> dict:
        """Render AgentResponse into the channel's output format."""
        raise NotImplementedError

    def send(self, thread_id: str, text: str, actions: list[dict] = None) -> dict:
        """Send a message to a user on this channel."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Web Channel (already done via /api/agent/chat, but adapter for completeness)
# ---------------------------------------------------------------------------

class WebChannelAdapter(ChannelAdapter):
    channel_name = "web"

    def request_from_incoming(self, payload: dict) -> Optional[AgentRequest]:
        return AgentRequest(
            user_id=payload.get("user_id", 0),
            tenant_id=payload.get("tenant_id", 0),
            channel="web",
            text=payload.get("query", ""),
            thread_id=f"web:{payload.get('user_id', 0)}",
            user_name=payload.get("user_name", ""),
        )

    def render_response(self, response: AgentResponse) -> dict:
        return {"response": response.text}

    def send(self, thread_id: str, text: str, actions: list[dict] = None) -> dict:
        # Web is pull-based (Bird widget fetches on open), not push
        return {"status": "not_push"}


# ---------------------------------------------------------------------------
# WhatsApp Channel Adapter
# ---------------------------------------------------------------------------

class WhatsAppChannelAdapter(ChannelAdapter):
    channel_name = "whatsapp"

    def request_from_incoming(self, payload: dict) -> Optional[AgentRequest]:
        """Parse WhatsApp webhook payload into AgentRequest."""
        from_number = payload.get("from", "")
        text = payload.get("text", "")

        mapper = get_session_mapper()
        session = mapper.resolve("whatsapp", from_number)
        if not session:
            logger.info("Unknown WhatsApp user: %s — treating as new lead", from_number)
            return None  # Let existing lead handling take over

        thread_id = mapper.generate_thread_id("whatsapp", from_number)

        return AgentRequest(
            user_id=session["user_id"],
            tenant_id=session["tenant_id"],
            channel="whatsapp",
            text=text,
            thread_id=thread_id,
            user_name=session.get("name", ""),
            metadata={"from_number": from_number, "msg_id": payload.get("msg_id", "")},
        )

    def render_response(self, response: AgentResponse) -> dict:
        """Format as WhatsApp API payload."""
        return {"text": response.text}

    def send(self, thread_id: str, text: str, actions: list[dict] = None) -> dict:
        """Send a WhatsApp message on behalf of the agent."""
        # The actual sending is handled by WhatsAppChannel.send()
        # This just returns the payload format
        return {"type": "text", "text": {"body": text}}


# ---------------------------------------------------------------------------
# Agent Router — routes any channel's input through the AgentLoop
# ---------------------------------------------------------------------------

class AgentRouter:
    """Routes incoming messages from any channel through the same AgentLoop."""

    def __init__(self):
        self.adapters: dict[str, ChannelAdapter] = {
            "web": WebChannelAdapter(),
            "whatsapp": WhatsAppChannelAdapter(),
        }

    def register_adapter(self, channel: str, adapter: ChannelAdapter):
        self.adapters[channel] = adapter

    def process_message(self, channel: str, payload: dict) -> Optional[dict]:
        """
        Process an incoming message from any channel through the AgentLoop.
        
        Args:
            channel: "web", "whatsapp", "telegram"
            payload: Channel-specific payload dict
            
        Returns:
            Response dict formatted for the channel, or None if unprocessable
        """
        adapter = self.adapters.get(channel)
        if not adapter:
            logger.warning("No adapter for channel: %s", channel)
            return None

        # Parse into normalized request
        request = adapter.request_from_incoming(payload)
        if not request:
            logger.info("Could not parse request from %s channel", channel)
            return None

        # Route through AgentLoop
        from app.shunya.agent import AgentLoop

        agent = AgentLoop(request.user_id, request.tenant_id, channel)
        result = agent.process(request.text)

        # Build response
        response_text = result.get("response", "")

        # Add verification badge for WhatsApp (text-based)
        badge = result.get("verification_badge", "")
        if badge == "verified":
            response_text = "✅ " + response_text
        elif badge == "company":
            pass  # WhatsApp is text-only, badge not visible
        elif badge == "low_confidence":
            response_text = "❓ " + response_text

        # Send back through the channel
        response = AgentResponse(
            text=response_text,
            channel=channel,
            thread_id=request.thread_id,
        )

        # Store trace
        try:
            from app.shunya.agent import get_trace_store
            trace = get_trace_store().get_by_user(request.user_id, 1)
        except Exception:
            pass

        # Return formatted response
        return {
            "text": response_text,
            "channel": channel,
            "thread_id": request.thread_id,
            "user_id": request.user_id,
            "intent": result.get("intent", {}),
            "verification_badge": badge,
            "confidence": result.get("confidence", 0),
        }

    def get_proactive_for_channel(self, channel: str, user_id: int, tenant_id: int) -> list[dict]:
        """Get proactive messages formatted for a specific channel."""
        from app.shunya.agent.proactive import ProactiveEngine
        engine = ProactiveEngine(user_id, tenant_id)
        messages = engine.get_messages(3)

        result = []
        for m in messages:
            formatted = {
                "title": m.title,
                "body": m.body,
                "icon": m.icon,
                "priority": m.priority,
            }
            if channel == "whatsapp":
                formatted["text"] = f"{m.icon} *{m.title}*\n{m.body}"
            result.append(formatted)
        return result


# Global router instance
_router = AgentRouter()


def get_router() -> AgentRouter:
    return _router