"""SHUNYA — Attention EventBus Subscriber.

Connects the canonical EventBus to the persistent attention system:

    BUSINESS EVENT → EventBus.publish(CanonicalEvent) → attention subscriber
    → AttentionItem (tenant / workspace / actor scoped, deduplicated)

No parallel event system. The subscriber acts ONLY on events that carry a
canonical owner — a real organization id AND a responsible identity. Events
without them are skipped (fail closed: no synthetic tenant, no invented
watchers). Repeated events for the same business object are deduplicated
against the active attention item.

Qualifying ingestion conditions (deterministic, no invented urgency):

  * outcome "rejected"                     → failed operation, needs review
  * outcome "partial" / "pending"          → incomplete processing, needs review
  * outcome "accepted" with unknown        → classification confidence unknown
    confidence                               (None, never fabricated), needs
                                             human review
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus

logger = logging.getLogger(__name__)

_subscription_id: Optional[str] = None

_REVIEW_OUTCOMES = {"rejected", "partial", "pending"}


def start_attention_subscriber() -> str:
    """Subscribe the attention bridge to canonical ingestion events (idempotent)."""
    global _subscription_id
    if _subscription_id is not None:
        return _subscription_id
    bus = get_event_bus()
    _subscription_id = bus.subscribe(
        "ingestion:*",
        _handle_event,
        consumer_name="attention_subscriber",
    )
    logger.info("Attention subscriber started (sid=%s)", _subscription_id[:8])
    return _subscription_id


def stop_attention_subscriber() -> None:
    """Unsubscribe from the EventBus (idempotent)."""
    global _subscription_id
    if _subscription_id is not None:
        get_event_bus().unsubscribe(_subscription_id)
        logger.info("Attention subscriber stopped (sid=%s)", _subscription_id[:8])
        _subscription_id = None


def _review_reason(event: CanonicalEvent) -> Optional[tuple]:
    """Return (reason, priority) when the event legitimately needs review."""
    payload = event.payload or {}
    outcome = str(payload.get("outcome") or "")
    ingestion_ref = payload.get("ingestion_id") or event.object_id or event.event_id

    if outcome == "rejected":
        return (f"Ingestion rejected — validation failed; review required "
                f"(ingestion {ingestion_ref})", 4)
    if outcome in ("partial", "pending"):
        return (f"Ingestion {outcome} — processing incomplete; review required "
                f"(ingestion {ingestion_ref})", 3)
    if outcome == "accepted" and payload.get("confidence_unknown") is True:
        return (f"Ingested data stored with unknown classification confidence — "
                f"confirm or correct it (ingestion {ingestion_ref})", 3)
    return None


def _handle_event(event: CanonicalEvent) -> None:
    """Turn qualifying business events into tenant-scoped attention items."""
    try:
        review = _review_reason(event)
        if review is None:
            return

        tenant_id = event.tenant_id
        actor_id = event.actor_id
        if not tenant_id or not actor_id:
            logger.info(
                "Attention skip: event %s carries no canonical owner "
                "(tenant=%s actor=%r) — fail closed",
                event.event_id, tenant_id, actor_id,
            )
            return

        from app.attention.models import AttentionItem, AttentionSource, AttentionState
        from app.attention.service import create_attention_item

        payload = event.payload or {}
        ingestion_id = str(payload.get("ingestion_id") or event.object_id
                           or event.event_id)

        existing = AttentionItem.query.filter(
            AttentionItem.organization_id == int(tenant_id),
            AttentionItem.state == AttentionState.ACTIVE.value,
            AttentionItem.source == AttentionSource.EVENT.value,
            AttentionItem.related_object_id == ingestion_id,
        ).first()
        if existing:
            return

        reason, priority = review
        workspace = event.workspace_id
        create_attention_item(
            identity_id=actor_id,
            organization_id=int(tenant_id),
            workspace_id=str(workspace) if workspace else None,
            source=AttentionSource.EVENT.value,
            related_object_type="ingestion",
            related_object_id=ingestion_id,
            reason=reason,
            priority=priority,
            confidence=payload.get("confidence"),
            provenance={
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "event_id": event.event_id,
                "event_type": event.event_type,
                "correlation_id": event.correlation_id,
                "source_type": payload.get("source_type"),
                "outcome": payload.get("outcome"),
                "method": "attention_event_subscriber",
            },
        )
        logger.info("Attention item created from event %s (%s)",
                    event.event_id, event.event_type)
    except Exception as e:  # never break the bus
        logger.error("Attention handler error: %s", e)
