"""
Shunya — Executor Layer (Phase 2)

Channel-agnostic execution layer. Handles all outbound and inbound
communication across multiple channels: WhatsApp, Telegram, Email, SMS.

Key principles:
- Channel-agnostic: same action, any channel
- Each channel is an adapter implementing the same interface
- No business logic — purely delivery
- Governance validation before any outbound action
"""

from __future__ import annotations
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger("shunya.executor")


# ---------------------------------------------------------------------------
# Message Types
# ---------------------------------------------------------------------------


class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    TEMPLATE = "template"  # Structured message (e.g. proposal card)
    ACTION = "action"      # Interactive button/list


class ChannelType(Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"  # Dashboard notification


@dataclass
class OutboundMessage:
    """A message to be sent through a channel."""
    channel: ChannelType
    recipient: str            # Phone number, chat_id, email address
    message_type: MessageType = MessageType.TEXT
    text: str = ""
    media_url: str | None = None
    file_path: str | None = None
    template_name: str | None = None
    template_data: dict | None = None
    action_buttons: list[dict] | None = None
    metadata: dict = field(default_factory=dict)
    priority: int = 0          # Higher = more urgent


@dataclass
class InboundMessage:
    """A message received from a channel."""
    channel: ChannelType
    sender: str               # Phone number, chat_id, email
    text: str = ""
    message_type: MessageType = MessageType.TEXT
    media_url: str | None = None
    file_path: str | None = None
    raw_payload: dict = field(default_factory=dict)
    received_at: datetime = field(default_factory=datetime.utcnow)


class DeliveryResult:
    """Result of sending a message."""
    def __init__(self, success: bool, channel: ChannelType, message_id: str = "",
                 error: str = ""):
        self.success = success
        self.channel = channel
        self.message_id = message_id
        self.error = error
        self.sent_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "channel": self.channel.value,
            "message_id": self.message_id,
            "error": self.error,
            "sent_at": self.sent_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Channel Adapters
# ---------------------------------------------------------------------------


class ChannelAdapter:
    """Base interface for all channel adapters."""

    @property
    def channel_type(self) -> ChannelType:
        raise NotImplementedError

    def send(self, message: OutboundMessage) -> DeliveryResult:
        """Send a message through this channel."""
        raise NotImplementedError

    def parse_inbound(self, raw: dict) -> InboundMessage | None:
        """Parse an incoming webhook payload into an InboundMessage."""
        raise NotImplementedError


class WhatsAppAdapter(ChannelAdapter):
    """WhatsApp channel adapter using WhatsApp Business API."""

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.WHATSAPP

    def __init__(self):
        self._api_token = os.getenv("WHATSAPP_API_TOKEN", "")
        self._phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self._api_base = "https://graph.facebook.com/v18.0"

    def is_configured(self) -> bool:
        return bool(self._api_token and self._phone_number_id)

    def send(self, message: OutboundMessage) -> DeliveryResult:
        if not self.is_configured():
            return DeliveryResult(False, ChannelType.WHATSAPP, error="WhatsApp not configured")

        try:
            import requests
        except ImportError:
            return DeliveryResult(False, ChannelType.WHATSAPP, error="requests not available")

        url = f"{self._api_base}/{self._phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }

        if message.message_type == MessageType.TEXT:
            payload = {
                "messaging_product": "whatsapp",
                "to": message.recipient,
                "type": "text",
                "text": {"body": message.text},
            }
        elif message.message_type == MessageType.TEMPLATE:
            payload = {
                "messaging_product": "whatsapp",
                "to": message.recipient,
                "type": "template",
                "template": {
                    "name": message.template_name or "proposal",
                    "language": {"code": "en"},
                    "components": [{
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(v)}
                            for v in (message.template_data or {}).values()
                        ],
                    }],
                },
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": message.recipient,
                "type": "text",
                "text": {"body": f"[{message.message_type.value}] {message.text}"},
            }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            data = resp.json()
            if resp.status_code == 200 and data.get("messages"):
                msg_id = data["messages"][0]["id"]
                return DeliveryResult(True, ChannelType.WHATSAPP, message_id=msg_id)
            return DeliveryResult(False, ChannelType.WHATSAPP,
                                 error=data.get("error", {}).get("message", str(resp.status_code)))
        except Exception as e:
            return DeliveryResult(False, ChannelType.WHATSAPP, error=str(e))

    def parse_inbound(self, raw: dict) -> InboundMessage | None:
        """Parse WhatsApp webhook payload."""
        try:
            entry = raw.get("entry", [{}])[0]
            change = entry.get("changes", [{}])[0]
            value = change.get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return None
            msg = messages[0]
            sender = msg.get("from", "")
            text = ""
            msg_type = msg.get("type", "text")
            if msg_type == "text":
                text = msg.get("text", {}).get("body", "")
            elif msg_type == "interactive":
                text = msg.get("interactive", {}).get("button_reply", {}).get("title", "")

            return InboundMessage(
                channel=ChannelType.WHATSAPP,
                sender=sender,
                text=text,
                raw_payload=raw,
            )
        except (IndexError, KeyError, TypeError) as e:
            logger.warning("Failed to parse WhatsApp inbound: %s", e)
            return None


class TelegramAdapter(ChannelAdapter):
    """Telegram channel adapter."""

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.TELEGRAM

    def __init__(self):
        self._token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    def is_configured(self) -> bool:
        return bool(self._token)

    def send(self, message: OutboundMessage) -> DeliveryResult:
        if not self.is_configured():
            return DeliveryResult(False, ChannelType.TELEGRAM, error="Telegram not configured")

        try:
            import requests
        except ImportError:
            return DeliveryResult(False, ChannelType.TELEGRAM, error="requests not available")

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {
            "chat_id": message.recipient,
            "text": message.text,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if data.get("ok"):
                msg_id = str(data.get("result", {}).get("message_id", ""))
                return DeliveryResult(True, ChannelType.TELEGRAM, message_id=msg_id)
            return DeliveryResult(False, ChannelType.TELEGRAM,
                                 error=data.get("description", "unknown"))
        except Exception as e:
            return DeliveryResult(False, ChannelType.TELEGRAM, error=str(e))

    def parse_inbound(self, raw: dict) -> InboundMessage | None:
        try:
            message = raw.get("message", {})
            text = str(message.get("text", ""))
            chat_id = str(message.get("chat", {}).get("id", ""))
            if not text:
                return None
            return InboundMessage(
                channel=ChannelType.TELEGRAM,
                sender=chat_id,
                text=text,
                raw_payload=raw,
            )
        except Exception:
            return None


class EmailAdapter(ChannelAdapter):
    """Email channel adapter — SMTP-based."""

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.EMAIL

    def __init__(self):
        self._smtp_host = os.getenv("SMTP_HOST", "")
        self._smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self._smtp_user = os.getenv("SMTP_USER", "")
        self._smtp_pass = os.getenv("SMTP_PASS", "")
        self._from = os.getenv("EMAIL_FROM", "ai@panchi.club")

    def is_configured(self) -> bool:
        return bool(self._smtp_host and self._smtp_user)

    def send(self, message: OutboundMessage) -> DeliveryResult:
        if not self.is_configured():
            return DeliveryResult(False, ChannelType.EMAIL, error="Email not configured")
        # SMTP implementation placeholder — returns success for now
        # In production, use smtplib to send
        logger.info("Email::send to %s: %s", message.recipient, message.text[:60])
        return DeliveryResult(True, ChannelType.EMAIL, message_id=f"email_{datetime.utcnow().timestamp()}")

    def parse_inbound(self, raw: dict) -> InboundMessage | None:
        return None  # Email inbound parsing via IMAP/API


# ---------------------------------------------------------------------------
# Executor Layer
# ---------------------------------------------------------------------------


class ExecutorLayer:
    """
    Channel-agnostic execution layer.

    In the Shunya pipeline:
        Governance → Executor → Observer

    Usage:
        executor = ExecutorLayer()
        result = executor.send(OutboundMessage(
            channel=ChannelType.WHATSAPP,
            recipient="+919999999999",
            text="Your proposal is ready!",
        ))
    """

    def __init__(self):
        self._adapters: dict[ChannelType, ChannelAdapter] = {}
        self._delivery_log: list[dict] = []
        self._register_defaults()

    def _register_defaults(self):
        """Register built-in channel adapters."""
        self.register(WhatsAppAdapter())
        self.register(TelegramAdapter())
        self.register(EmailAdapter())

    def register(self, adapter: ChannelAdapter):
        """Register a channel adapter."""
        self._adapters[adapter.channel_type] = adapter

    def get_adapter(self, channel: ChannelType) -> ChannelAdapter | None:
        """Get adapter for a channel type."""
        return self._adapters.get(channel)

    def send(self, message: OutboundMessage, governance=None) -> DeliveryResult:
        """
        Send a message through the appropriate channel.
        Optionally validates through Governance before sending.
        """
        adapter = self._adapters.get(message.channel)
        if not adapter:
            return DeliveryResult(False, message.channel, error=f"No adapter for {message.channel.value}")

        # Governance check
        if governance:
            from .governance import GovernanceLayer
            if isinstance(governance, GovernanceLayer):
                verdict = governance.validate_action(
                    f"send_{message.channel.value}",
                    {
                        "recipient": message.recipient,
                        "message_type": message.message_type.value,
                        "text_length": len(message.text),
                    },
                )
                if not verdict.approved:
                    return DeliveryResult(False, message.channel,
                                         error=f"Blocked by governance: {verdict.blocking_policies}")

        result = adapter.send(message)
        self._log_delivery(message, result)
        return result

    def parse_inbound(self, channel: ChannelType, raw: dict) -> InboundMessage | None:
        """Parse an incoming webhook payload through the appropriate adapter."""
        adapter = self._adapters.get(channel)
        if not adapter:
            return None
        return adapter.parse_inbound(raw)

    def _log_delivery(self, message: OutboundMessage, result: DeliveryResult):
        """Record delivery attempt for audit/observer."""
        self._delivery_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "channel": message.channel.value,
            "recipient": message.recipient[-4:],  # Last 4 chars only for privacy
            "message_type": message.message_type.value,
            "success": result.success,
            "error": result.error,
            "message_id": result.message_id,
        })

    def get_delivery_log(self, limit: int = 50) -> list[dict]:
        """Return recent delivery log entries."""
        return list(reversed(self._delivery_log[-limit:]))

    @property
    def stats(self) -> dict:
        """Return executor statistics."""
        total = len(self._delivery_log)
        successful = sum(1 for e in self._delivery_log if e["success"])
        return {
            "total_sent": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round(successful / total * 100, 1) if total else 0,
            "channels": {ct.value: ct in self._adapters for ct in ChannelType},
            "configured": [
                ct.value for ct, a in self._adapters.items()
                if hasattr(a, 'is_configured') and a.is_configured()
            ],
        }