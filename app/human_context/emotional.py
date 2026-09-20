"""
SHUNYA — Emotional/Human Context Intelligence (GATE 12)

Never diagnoses, never manipulates, never creates fear, artificial urgency,
or emotional dependency. Human authority always overrides inference.

Temporal rule: PAST FEELING ≠ CURRENT FEELING
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from app import db
from app.human_context.models import HumanContextItem
from sqlalchemy import Index


class ExpressionType:
    """Canonical expression types — neutral descriptors of human communication."""
    FRUSTRATION = "frustration"
    UNCERTAINTY = "uncertainty"
    EXCITEMENT = "excitement"
    URGENT = "urgent"
    DEFER = "defer"

    ALL = {FRUSTRATION, UNCERTAINTY, EXCITEMENT, URGENT, DEFER}


class EmotionalStatus:
    """Status flow: PROPOSED → ACTIVE → CORRECTED → STALE → EXPIRED."""
    PROPOSED = "proposed"
    ACTIVE = "active"
    CORRECTED = "corrected"
    STALE = "stale"
    EXPIRED = "expired"

    FLOW = (PROPOSED, ACTIVE, CORRECTED, STALE, EXPIRED)


# Sensitive fields that require auth boundary checks when reading
SENSITIVE_FIELDS = {"context", "provenance"}


class EmotionalContextItem(db.Model):
    """A recorded emotional/human-context observation.

    Stores what a person communicated about their state — never inferred
    or diagnosed. Correction-aware, staleness-aware, and auth-gated.
    """
    __tablename__ = "emotional_context_items"
    __table_args__ = (
        Index("ix_eci_tenant", "tenant_id"),
        Index("ix_eci_person", "person_id"),
        Index("ix_eci_expression", "expression_type"),
        Index("ix_eci_status", "status"),
        Index("ix_eci_timestamp", "observed_at"),
        Index("ix_eci_correction", "correction_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False, index=True)
    workspace_id = db.Column(db.String(64), nullable=True, index=True)

    # The emotional expression
    source = db.Column(db.String(120), nullable=False, default="human")
    expression_type = db.Column(db.String(30), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    observed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Human-readable context about the expression (NOT a diagnosis)
    context = db.Column(db.Text, nullable=True)

    # Related object/event that the expression pertains to
    related_object_id = db.Column(db.Integer, nullable=True)
    related_object_type = db.Column(db.String(60), nullable=True)

    # Status flow
    status = db.Column(db.String(30), nullable=False, default=EmotionalStatus.PROPOSED)

    # Correction tracking — links to the corrected entry
    correction_id = db.Column(db.Integer, nullable=True)
    corrected_by = db.Column(db.String(120), default="")
    corrected_at = db.Column(db.DateTime, nullable=True)
    correction_note = db.Column(db.Text, nullable=True)

    # Provenance and retention
    provenance = db.Column(db.Text, nullable=True)
    retention = db.Column(db.String(30), nullable=True)

    # Timestamps
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return (
            f"<EmotionalContextItem #{self.id} "
            f"{self.expression_type} [{self.status}]>"
        )


# ---------------------------------------------------------------------------
# Staleness threshold
# ---------------------------------------------------------------------------
EMOTIONAL_STALE_AFTER_HOURS = 24  # Context older than 24h is stale by default
EMOTIONAL_STALE_AFTER_URGENT_HOURS = 4  # Urgency decays faster


class EmotionalContextService:
    """Service for recording, correcting, and querying emotional context.

    Designed as an extension to HumanContextService — not a replacement.
    """

    def __init__(self, session=None):
        self._session = session or db.session

    # ------------------------------------------------------------------
    # Record
    # ------------------------------------------------------------------

    def record(self, *, expression_type: str, source: str = "human",
               person_id: Optional[int] = None, tenant_id: Optional[int] = None,
               workspace_id: Optional[str] = None,
               context: str = "", confidence: float = 1.0,
               related_object_id: Optional[int] = None,
               related_object_type: Optional[str] = None,
               provenance: Optional[str] = None,
               retention: Optional[str] = None,
               created_by: str = "") -> dict:
        """Record an emotional context observation.

        The system stores what was communicated — it does NOT diagnose
        or manipulate. Human authority overrides inference.
        """
        if expression_type not in ExpressionType.ALL:
            return {"success": False, "error": f"Unknown expression_type: {expression_type}",
                    "valid_types": sorted(ExpressionType.ALL)}

        now = datetime.now(timezone.utc)

        item = EmotionalContextItem(
            source=source,
            expression_type=expression_type,
            confidence=confidence,
            observed_at=now,
            context=context or "",
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            status=EmotionalStatus.ACTIVE,
            person_id=person_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            provenance=provenance,
            retention=retention,
            created_by=created_by,
        )
        self._session.add(item)
        self._session.commit()

        return {
            "success": True,
            "item_id": item.id,
            "expression_type": expression_type,
            "status": EmotionalStatus.ACTIVE,
            "observed_at": item.observed_at.isoformat(),
        }

    # ------------------------------------------------------------------
    # Correction
    # ------------------------------------------------------------------

    def correct(self, item_id: int, *, corrected_by: str = "",
                correction_note: str = "",
                tenant_id: Optional[int] = None,
                new_expression_type: Optional[str] = None,
                new_context: Optional[str] = None,
                new_confidence: Optional[float] = None) -> dict:
        """Correct a previously recorded emotional context entry.

        Creates a new entry linked to the original via correction_id.
        The original is marked CORRECTED but NOT deleted — correction
        creates a traceable lineage.
        """
        original = self._session.get(EmotionalContextItem, item_id)
        if not original:
            return {"success": False, "error": "Emotional context item not found"}
        if tenant_id is not None and original.tenant_id != tenant_id:
            return {"success": False, "error": "Emotional context item not found"}
        if original.status in (EmotionalStatus.STALE, EmotionalStatus.EXPIRED):
            return {"success": False, "error": f"Cannot correct a {original.status} entry"}

        now = datetime.now(timezone.utc)

        # Mark original as corrected
        original.status = EmotionalStatus.CORRECTED
        original.updated_at = now

        # Create correction entry
        correction = EmotionalContextItem(
            source=original.source,
            expression_type=new_expression_type or original.expression_type,
            confidence=new_confidence if new_confidence is not None else original.confidence,
            observed_at=now,
            context=new_context if new_context is not None else original.context,
            related_object_id=original.related_object_id,
            related_object_type=original.related_object_type,
            status=EmotionalStatus.ACTIVE,
            correction_id=original.id,
            person_id=original.person_id,
            tenant_id=original.tenant_id,
            workspace_id=original.workspace_id,
            provenance=original.provenance,
            retention=original.retention,
            created_by=corrected_by,
        )
        self._session.add(correction)

        # Record correction metadata on original
        original.corrected_by = corrected_by
        original.corrected_at = now
        original.correction_note = correction_note

        self._session.commit()

        return {
            "success": True,
            "original_id": original.id,
            "correction_id": correction.id,
            "original_status": EmotionalStatus.CORRECTED,
            "new_status": EmotionalStatus.ACTIVE,
            "corrected_at": now.isoformat(),
        }

    # ------------------------------------------------------------------
    # Staleness detection
    # ------------------------------------------------------------------

    def detect_stale_contexts(self, *, tenant_id: Optional[int] = None,
                              person_id: Optional[int] = None) -> dict:
        """Mark old active emotional context entries as STALE.

        PAST FEELING ≠ CURRENT FEELING — context older than the staleness
        threshold is marked stale. Urgency decays faster than other types.
        Handles both offset-aware and offset-naive datetimes (SQLite stores
        datetimes as naive strings).
        """
        now = datetime.now(timezone.utc)
        # SQLite returns naive datetimes — make now naive for comparison
        now_naive = now.replace(tzinfo=None)
        q = self._session.query(EmotionalContextItem).filter(
            EmotionalContextItem.status == EmotionalStatus.ACTIVE
        )
        if tenant_id is not None:
            q = q.filter(EmotionalContextItem.tenant_id == tenant_id)
        if person_id is not None:
            q = q.filter(EmotionalContextItem.person_id == person_id)

        items = q.all()
        stale_count = 0
        for item in items:
            threshold_hours = EMOTIONAL_STALE_AFTER_URGENT_HOURS \
                if item.expression_type == ExpressionType.URGENT \
                else EMOTIONAL_STALE_AFTER_HOURS
            observed = item.observed_at
            # Strip tzinfo if present for comparison with naive now
            if hasattr(observed, 'tzinfo') and observed.tzinfo is not None:
                observed = observed.replace(tzinfo=None)
            age = now_naive - observed
            if age >= timedelta(hours=threshold_hours):
                item.status = EmotionalStatus.STALE
                item.updated_at = datetime.now(timezone.utc)
                stale_count += 1

        if stale_count > 0:
            self._session.commit()

        return {"success": True, "stale_count": stale_count}

    # ------------------------------------------------------------------
    # Expiry
    # ------------------------------------------------------------------

    def expire(self, item_id: int, *, tenant_id: Optional[int] = None,
               reason: str = "") -> dict:
        """Expire an emotional context entry (manual or automatic)."""
        item = self._session.get(EmotionalContextItem, item_id)
        if not item:
            return {"success": False, "error": "Emotional context item not found"}
        if tenant_id is not None and item.tenant_id != tenant_id:
            return {"success": False, "error": "Emotional context item not found"}

        item.status = EmotionalStatus.EXPIRED
        item.updated_at = datetime.now(timezone.utc)
        self._session.commit()

        return {"success": True, "item_id": item.id, "status": EmotionalStatus.EXPIRED}

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list(self, *, tenant_id: Optional[int] = None,
             person_id: Optional[int] = None,
             workspace_id: Optional[str] = None,
             expression_type: Optional[str] = None,
             status: Optional[str] = None,
             include_sensitive: bool = False,
             limit: int = 100, offset: int = 0) -> dict:
        """List emotional context with auth-boundary filtering.

        Sensitive fields (context, provenance) are only returned when
        include_sensitive=True — the caller must have appropriate auth.
        """
        q = self._session.query(EmotionalContextItem)
        if tenant_id is not None:
            q = q.filter(EmotionalContextItem.tenant_id == tenant_id)
        if person_id is not None:
            q = q.filter(EmotionalContextItem.person_id == person_id)
        if workspace_id is not None:
            q = q.filter(EmotionalContextItem.workspace_id == workspace_id)
        if expression_type is not None:
            q = q.filter(EmotionalContextItem.expression_type == expression_type)
        if status is not None:
            q = q.filter(EmotionalContextItem.status == status)

        total = q.count()
        items = q.order_by(EmotionalContextItem.observed_at.desc()).offset(offset).limit(limit).all()

        return {
            "success": True,
            "total": total,
            "items": [self._to_dict(it, include_sensitive) for it in items],
        }

    def get(self, item_id: int, *, tenant_id: Optional[int] = None,
            include_sensitive: bool = False) -> dict:
        """Get a single emotional context item by ID."""
        item = self._session.get(EmotionalContextItem, item_id)
        if not item:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and item.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        return {"success": True, "item": self._to_dict(item, include_sensitive)}

    # ------------------------------------------------------------------
    # Provider failure simulation (for graceful handling tests)
    # ------------------------------------------------------------------

    def record_with_provider_failure(self, *, expression_type: str,
                                     fail_on: str = "commit",
                                     **kwargs) -> dict:
        """Simulate a provider failure during recording.

        Used to test graceful handling — the service never relies on
        external provider availability to record emotional context.
        """
        if fail_on == "commit":
            # Simulate commit failure by rolling back
            self._session.rollback()
            return {"success": False, "error": "Provider unavailable: database write failed",
                    "action": "rollback_completed"}
        return self.record(expression_type=expression_type, **kwargs)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_dict(item: EmotionalContextItem, include_sensitive: bool = False) -> dict:
        d = {
            "id": item.id,
            "source": item.source,
            "expression_type": item.expression_type,
            "confidence": item.confidence,
            "observed_at": item.observed_at.isoformat() if item.observed_at else None,
            "related_object_id": item.related_object_id,
            "related_object_type": item.related_object_type,
            "correction_id": item.correction_id,
            "status": item.status,
            "person_id": item.person_id,
            "tenant_id": item.tenant_id,
            "workspace_id": item.workspace_id,
            "retention": item.retention,
            "created_by": item.created_by,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        if include_sensitive:
            d["context"] = item.context
            d["provenance"] = item.provenance
        else:
            d["context"] = None
            d["provenance"] = None

        if item.corrected_by:
            d["corrected_by"] = item.corrected_by
            d["corrected_at"] = item.corrected_at.isoformat() if item.corrected_at else None
            d["correction_note"] = item.correction_note

        return d