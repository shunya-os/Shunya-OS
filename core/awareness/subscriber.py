"""
SHUNYA — Awareness EventBus Subscriber.

Gate 3.1: Connects AwarenessService to the canonical EventBus.

Every canonical event flows through:
    EVENT → EventBus → AwarenessSubscriber → AwarenessService
    → AwarenessSignal → awareness:* event → EventBus → SSE → frontend

No parallel event system.
No duplicate storage.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus
from core.awareness import AwarenessSignal, SignalType, SignalPriority, SignalStatus
from core.awareness.service import AwarenessService, get_awareness_service

logger = logging.getLogger(__name__)

# Subscription ID for later cleanup
_subscription_id: Optional[str] = None


def start_awareness_subscriber() -> str:
    """Subscribe the AwarenessService to the canonical EventBus.

    Returns the subscription ID for later cleanup.
    """
    global _subscription_id
    if _subscription_id is not None:
        return _subscription_id

    bus = get_event_bus()
    _subscription_id = bus.subscribe(
        "*",               # Subscribe to ALL events
        _handle_event,
        consumer_name="awareness_subscriber",
    )
    logger.info("Awareness subscriber started (sid=%s)", _subscription_id[:8])
    return _subscription_id


def stop_awareness_subscriber() -> None:
    """Unsubscribe from the EventBus."""
    global _subscription_id
    if _subscription_id is not None:
        bus = get_event_bus()
        bus.unsubscribe(_subscription_id)
        logger.info("Awareness subscriber stopped (sid=%s)", _subscription_id[:8])
        _subscription_id = None


def _handle_event(event: CanonicalEvent) -> None:
    """Handle a canonical event: evaluate, produce signal, emit awareness event.

    This is the core integration point — every canonical event flows
    through here to the awareness engine.
    """
    try:
        service = get_awareness_service()
        signal = service.process_event(
            event.event_type,
            _event_to_dict(event),
            tenant_id=event.tenant_id,
        )
        if signal is not None:
            # Emit a canonical awareness event — this flows through
            # the existing SSE infrastructure automatically since
            # SSEStreamManager subscribes to "*"
            _emit_awareness_event(signal, event)
    except Exception as e:
        logger.error("Awareness handler error: %s", e)


def _event_to_dict(event: CanonicalEvent) -> dict:
    """Convert a CanonicalEvent to the dict format AwarenessService expects."""
    return {
        "event_id": event.event_id,
        "timestamp": event.timestamp,
        "tenant_id": event.tenant_id,
        "workspace_id": event.workspace_id,
        "object_id": event.object_id,
        "object_type": event.object_type,
        "payload": event.payload,
        "title": event.payload.get("message", event.event_type),
        "description": event.payload.get("message", ""),
    }


def _emit_awareness_event(signal: AwarenessSignal, source_event: CanonicalEvent) -> None:
    """Emit a canonical awareness event through the EventBus."""
    bus = get_event_bus()
    awareness_event = CanonicalEvent(
        event_type=f"awareness:{signal.signal_type.value}",
        event_id=f"awr_{signal.signal_id}",
        tenant_id=signal.tenant_id,
        actor_id="shunya",
        actor_type="awareness",
        object_id=signal.affected_object_id,
        object_type=signal.affected_object_type,
        payload={
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type.value,
            "title": signal.title,
            "description": signal.description,
            "reason": signal.reason,
            "priority": signal.priority.value,
            "relevance": signal.relevance_score,
            "confidence": signal.confidence,
            "knowledge_status": signal.knowledge_status,
            "source_event_id": signal.source_event_id,
            "suggested_action": signal.suggested_action,
            "evidence": signal.evidence,
            "status": signal.status.value,
            "created_at": signal.created_at,
        },
    )
    bus.publish(awareness_event)