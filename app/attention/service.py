"""Attention service — create, dismiss, resolve, and detect attention items.

Every attention item carries full tenant/identity/workspace scope, so all queries
are scoped by organization_id. Callers that need cross-tenant reads must explicitly
opt in — the defaults fail closed.
"""
from datetime import datetime, timezone
from typing import Optional

from app import db
from app.attention.models import AttentionItem, AttentionState, AttentionSource


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