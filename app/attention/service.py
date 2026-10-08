"""Attention service — create, dismiss, resolve, and detect attention items.

Every attention item carries full tenant/identity/workspace scope, so all queries
are scoped by organization_id. Callers that need cross-tenant reads must explicitly
opt in — the defaults fail closed.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app import db
from app.attention.models import AttentionItem, AttentionState, AttentionSource

logger = logging.getLogger(__name__)


def create_attention_item(
    *,
    identity_id: str,
    organization_id: int,
    workspace_id: Optional[str] = None,
    source: str = AttentionSource.INTENTION_ENGINE.value,
    related_object_type: Optional[str] = None,
    related_object_id: Optional[str] = None,
    reason: str = "",
    priority: int = 3,
    confidence: Optional[float] = None,
    provenance: Optional[dict] = None,
) -> AttentionItem:
    """Create a new active attention item. Used by the intention engine and
    any internal component that wants to surface something to the user.

    Returns the created item.
    """
    item = AttentionItem(
        identity_id=identity_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        source=source,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        reason=reason,
        priority=priority,
        confidence=confidence,
        provenance=provenance or {},
    )
    db.session.add(item)
    db.session.commit()
    return item


def dismiss(item_id: int, *, dismissed_by: str, reason: Optional[str] = None) -> Optional[AttentionItem]:
    """Dismiss an active attention item. Returns the updated item or None if not found."""
    item = db.session.get(AttentionItem, item_id)
    if not item:
        return None
    if item.state != AttentionState.ACTIVE.value:
        return item  # Already terminal — no-op
    item.state = AttentionState.DISMISSED.value
    item.dismissed_at = datetime.now(timezone.utc)
    item.dismissed_by = dismissed_by
    if reason:
        item.reason = reason
    db.session.commit()
    return item


def resolve(item_id: int, *, resolved_by: str) -> Optional[AttentionItem]:
    """Resolve an active attention item. Returns the updated item or None if not found."""
    item = db.session.get(AttentionItem, item_id)
    if not item:
        return None
    if item.state != AttentionState.ACTIVE.value:
        return item  # No-op for terminal states
    item.state = AttentionState.RESOLVED.value
    item.resolved_at = datetime.now(timezone.utc)
    item.resolved_by = resolved_by
    db.session.commit()
    return item


def confirm_review(item_id: int, *, reviewed_by: str, note: str = "") -> Optional[AttentionItem]:
    """Record a human review decision on an active event-sourced item.

    This is the review/decision action required by the M9 human-action contract:
    the decision itself IS the canonical business-state transition for an
    ingestion-review item (the ingestion is a transient event, so there is no
    other persistent row to mutate). The decision is persisted canonically on
    the item (``provenance.review_decision``), the item resolves, and a
    canonical ``attention:review_confirmed`` event is emitted (non-fatal).

    Returns None when the item does not exist or is not active.
    """
    item = db.session.get(AttentionItem, item_id)
    if not item or item.state != AttentionState.ACTIVE.value:
        return None

    now = datetime.now(timezone.utc)
    provenance = dict(item.provenance or {})
    provenance["review_decision"] = {
        "decision": "confirmed",
        "decided_by": reviewed_by,
        "decided_at": now.isoformat(),
        "note": note or "",
        "source_event_id": provenance.get("event_id"),
    }
    item.provenance = provenance
    item.state = AttentionState.RESOLVED.value
    item.resolved_at = now
    item.resolved_by = reviewed_by
    db.session.commit()

    # Canonical event record of the human decision (never fatal).
    try:
        from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus
        get_event_bus().publish(CanonicalEvent(
            event_type="attention:review_confirmed",
            tenant_id=item.organization_id,
            workspace_id=None,
            actor_id=reviewed_by,
            actor_type="human",
            object_id=item.related_object_id or str(item.id),
            object_type=item.related_object_type or "attention_item",
            payload={
                "attention_item_id": item.id,
                "decision": "confirmed",
                "note": note or "",
                "related_object_id": item.related_object_id,
                "related_object_type": item.related_object_type,
            },
        ))
    except Exception as e:  # never fail the decision because the bus failed
        logger.warning("Review-confirmed event emission failed: %s", e)

    return item


def list_active(
    organization_id: int,
    *,
    identity_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    limit: int = 50,
) -> list[AttentionItem]:
    """List active attention items for a tenant, optionally scoped to identity
    or workspace. Fails closed — organization_id is required.
    """
    query = AttentionItem.query.filter(
        AttentionItem.organization_id == organization_id,
        AttentionItem.state == AttentionState.ACTIVE.value,
    )
    if identity_id:
        query = query.filter(AttentionItem.identity_id == identity_id)
    if workspace_id:
        query = query.filter(AttentionItem.workspace_id == workspace_id)
    return query.order_by(AttentionItem.priority.desc(), AttentionItem.created_at.desc()).limit(limit).all()


def get(item_id: int) -> Optional[AttentionItem]:
    """Get a single attention item by id."""
    return db.session.get(AttentionItem, item_id)


def detect_attention_from_signals(
    *,
    identity_id: str,
    organization_id: int,
    workspace_id: Optional[str] = None,
) -> list[AttentionItem]:
    """Scan existing Signal records and create attention items for recent signals
    that don't already have a corresponding active attention item.

    This bridges the legacy Signal table into the attention system.
    """
    from app.signals.models import Signal
    from datetime import datetime, timezone, timedelta

    created: list[AttentionItem] = []
    recent = datetime.now(timezone.utc) - timedelta(hours=24)

    signals = Signal.query.filter(
        Signal.created_at >= recent,
    ).order_by(Signal.created_at.desc()).limit(50).all()

    for sig in signals:
        # Skip if an active attention item already exists for this signal
        existing = AttentionItem.query.filter(
            AttentionItem.organization_id == organization_id,
            AttentionItem.state == AttentionState.ACTIVE.value,
            AttentionItem.related_object_id == str(sig.id),
            AttentionItem.source == AttentionSource.SIGNAL.value,
        ).first()
        if existing:
            continue

        item = create_attention_item(
            identity_id=identity_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            source=AttentionSource.SIGNAL.value,
            related_object_type=sig.type,
            related_object_id=str(sig.id),
            reason=sig.payload.get("reason", f"Signal detected: {sig.type}"),
            priority=sig.payload.get("priority", 3),
            confidence=sig.payload.get("confidence", None),
            provenance={
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "signal_id": sig.id,
                "method": "detect_attention_from_signals",
            },
        )
        created.append(item)

    return created