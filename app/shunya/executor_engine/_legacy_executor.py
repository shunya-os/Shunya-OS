"""SHUNYA — Legacy ExecutorLayer (Backward Compatibility).

Wraps the canonical ExecutorEngine to provide backward-compatible
interfaces for existing call sites.

All new code SHOULD import from app.shunya.executor_engine directly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.shunya.executor_engine.engine import ExecutorEngine
from app.shunya.executor_engine.models import (
    ExecutorInput, Task, ExecutionType, TaskState,
)

# Re-export existing types from legacy executor.py where needed
try:
    from app.shunya.executor import (
        OutboundMessage, InboundMessage, DeliveryResult,
        ChannelType, MessageType,
        WhatsAppAdapter, TelegramAdapter, EmailAdapter,
        ChannelAdapter,
    )
    _legacy_available = True
except ImportError:
    _legacy_available = False
    OutboundMessage = None
    InboundMessage = None
    DeliveryResult = None
    ChannelType = None
    MessageType = None
    WhatsAppAdapter = None
    TelegramAdapter = None
    EmailAdapter = None
    ChannelAdapter = None


class ExecutorLayer:
    """Legacy ExecutorLayer wrapping ExecutorEngine for backward compatibility.

    Provides the same send() API as the original ExecutorLayer but routes
    through the canonical ExecutorEngine for workflow management.
    """

    def __init__(self):
        self._engine = ExecutorEngine()
        # Register legacy adapters if available
        if _legacy_available:
            for adapter_cls in [WhatsAppAdapter, TelegramAdapter, EmailAdapter]:
                if adapter_cls:
                    try:
                        adapter = adapter_cls()
                        self._engine.register_adapter_from_legacy(adapter)
                    except Exception:
                        pass

    @property
    def engine(self) -> ExecutorEngine:
        return self._engine

    # ------------------------------------------------------------------
    # Legacy API
    # ------------------------------------------------------------------

    def send(self, message: Any, governance: Any = None) -> Any:
        """Legacy send() API — wraps a message as a single task workflow."""
        if not _legacy_available or OutboundMessage is None:
            return None  # Cannot operate without legacy module

        channel = message.channel.value if hasattr(message.channel, 'value') else str(message.channel)

        task = Task(
            action="send_message",
            target=channel,
            payload={
                "recipient": message.recipient,
                "text": message.text,
                "message_type": message.message_type.value if hasattr(message.message_type, 'value') else str(message.message_type),
                "template_name": message.template_name,
                "template_data": message.template_data,
            },
            type=ExecutionType.SYNCHRONOUS.value,
        )

        inp = ExecutorInput(
            governance_approved=(governance is None or getattr(governance, 'approved', True)),
            tenant_id=getattr(message, 'tenant_id', 1),
            tasks=[task],
        )

        output = self._engine.execute(inp)

        # Return DeliveryResult compatible shape
        if output.success and output.outcome and output.outcome.evidence:
            ev = output.outcome.evidence[0]
            return DeliveryResult(True, channel, message_id=ev.message_id)
        return DeliveryResult(False, channel, error="; ".join(output.errors) if output.errors else "Execution failed")

    def register(self, adapter: Any) -> None:
        """Register a channel adapter."""
        self._engine.register_adapter_from_legacy(adapter)

    def get_delivery_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return outcome log entries."""
        return self._engine.list_outcomes(limit)

    @property
    def stats(self) -> Dict[str, Any]:
        return self._engine.stats