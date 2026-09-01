"""
Shunya — Observer + Learning Layers (Phase 2)

Observer records what actually happened vs what was planned.
Learning analyzes discrepancies and feeds improvements back into Knowledge.

This closes the compounding loop:
    Execute → Observe → Compare → Learn → Better Knowledge
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from app import db
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, Index, func


# ---------------------------------------------------------------------------
# SQLAlchemy Model
# ---------------------------------------------------------------------------


class Observation(db.Model):
    """Record of what actually happened — execution outcome.

    CANONICAL MODEL (reconciled with DB schema):
    Matches the actual physical schema in PostgreSQL.
    """

    __tablename__ = "observations"
    __table_args__ = (Index("ix_obs_lead_action", "lead_id", "action"), Index("ix_obs_created", "created_at"))

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, default=0)
    subject_type = Column(String(30), nullable=False)
    subject_id = Column(Integer, nullable=False)
    event = Column(String(60), nullable=False)
    source = Column(String(30), nullable=False)
    observer = Column(String(60), nullable=True)
    expected_state = Column(Text, nullable=True)
    actual_state = Column(Text, nullable=True)
    delta = Column(String(255), nullable=True)
    severity = Column(String(20), nullable=True)
    confidence = Column(String(20), nullable=True)  # DB is VARCHAR(20), not Float
    metadata_json = Column(db.JSON, nullable=True)  # DB is JSONB
    created_at = Column(DateTime, nullable=True)
    action = Column(String(255), nullable=True)
    channel = Column(String(255), nullable=True)
    discrepancy = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    actual_outcome = Column(Text, nullable=True)
    lead_id = Column(Integer, nullable=True, index=True)
    success = Column(db.Boolean, nullable=True)

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "event": self.event,
            "source": self.source,
            "observer": self.observer,
            "expected_state": self.expected_state,
            "actual_state": self.actual_state,
            "delta": self.delta,
            "severity": self.severity,
            "confidence": self.confidence,
            "metadata": self.metadata_json if isinstance(self.metadata_json, dict) else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "action": self.action,
            "channel": self.channel,
            "discrepancy": self.discrepancy,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "lead_id": self.lead_id,
            "success": self.success,
        }


class LearningEntry(db.Model):
    """A learning signal — what the system learned from an observation."""

    __tablename__ = "learning_entries"
    __table_args__ = (Index("ix_le_knowledge", "knowledge_fact_key"), Index("ix_le_created", "created_at"))

    id = Column(Integer, primary_key=True)
    observation_id = Column(Integer, nullable=True)
    knowledge_fact_key = Column(String(255), nullable=True)  # What knowledge was affected
    insight = Column(Text, nullable=False)                    # What was learned
    recommendation = Column(Text, default="")                 # What should change
    source = Column(String(60), default="observer")            # observer, manual, system
    applied = Column(Boolean, default=False)                  # Has this been applied to Knowledge?
    applied_at = Column(DateTime, nullable=True)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "observation_id": self.observation_id,
            "knowledge_fact_key": self.knowledge_fact_key,
            "insight": self.insight,
            "recommendation": self.recommendation,
            "source": self.source,
            "applied": self.applied,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Observer Layer
# ---------------------------------------------------------------------------


class ObserverLayer:
    """
    Records what actually happened vs what was planned.

    In the Shunya pipeline:
        Executor → Observer → Learning → Knowledge
    """

    def __init__(self, session=None):
        self._session = session or db.session

    def observe(self, action: str, outcome: str, *,
                lead_id: int = None,
                expected: str = "",
                channel: str = "internal",
                success: bool = True,
                confidence: float = 1.0,
                metadata: dict = None,
                # Execution-chain fields (optional)
                tenant_id: int = None,
                subject_type: str = None,
                subject_id: int = None,
                event: str = None,
                source: str = None,
                observer: str = None,
                severity: str = None,
                expected_state: str = None,
                actual_state: str = None) -> Observation:
        """
        Record an observation.

        Args:
            action: What action was taken (proposal_sent, booking_made...)
            outcome: What actually happened
            expected: What was expected/predicted (optional)
            success: Did it go as planned?
            confidence: Observer's confidence (0-1)
            tenant_id: Tenant isolation field
            subject_type: Type of subject being observed
            subject_id: ID of subject being observed
            event: Event name for the observation
            source: Source system identifier
            observer: Observer identifier
            severity: Severity level (info, warning, error)
            expected_state: Expected state in execution chain context
            actual_state: Actual state in execution chain context
        """
        discrepancy = ""
        if expected and outcome and expected != outcome:
            discrepancy = f"Expected: {expected[:200]} | Actual: {outcome[:200]}"

        obs = Observation(
            lead_id=lead_id,
            action=action,
            expected_outcome=str(expected)[:1000],
            actual_outcome=str(outcome)[:1000],
            discrepancy=str(discrepancy)[:1000],
            success=success,
            confidence=min(1.0, max(0.0, confidence)),
            channel=channel,
            metadata_json=metadata or {},
            # Execution-chain fields (pass through)
            tenant_id=tenant_id,
            subject_type=subject_type,
            subject_id=subject_id,
            event=event or action[:60],
            source=source,
            observer=observer,
            severity=severity or "info",
            expected_state=expected_state or "",
            actual_state=actual_state or "",
        )
        self._session.add(obs)
        self._session.commit()
        return obs

    def get_by_lead(self, lead_id: int, limit: int = 50) -> list[dict]:
        """Get all observations for a lead."""
        obs = (
            self._session.query(Observation)
            .filter(Observation.lead_id == lead_id)
            .order_by(Observation.created_at.desc())
            .limit(limit)
            .all()
        )
        return [o.to_dict() for o in obs]

    def get_anomalies(self, since_hours: int = 24) -> list[dict]:
        """Get observations flagged as unsuccessful (anomalies)."""
        since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        obs = (
            self._session.query(Observation)
            .filter(Observation.success == False, Observation.created_at >= since)
            .order_by(Observation.created_at.desc())
            .all()
        )
        return [o.to_dict() for o in obs]

    def get_discrepancies(self, since_hours: int = 24) -> list[dict]:
        """Get observations where reality differed from expectation."""
        since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        obs = (
            self._session.query(Observation)
            .filter(Observation.discrepancy != "", Observation.created_at >= since)
            .order_by(Observation.created_at.desc())
            .all()
        )
        return [o.to_dict() for o in obs]

    def stats(self) -> dict:
        """Return observer statistics."""
        total = self._session.query(func.count(Observation.id)).scalar() or 0
        successful = self._session.query(func.count(Observation.id)).filter(Observation.success == True).scalar() or 0
        anomalies = total - successful
        return {
            "total_observations": total,
            "successful": successful,
            "anomalies": anomalies,
            "success_rate": round(successful / total * 100, 1) if total else 0,
        }


# ---------------------------------------------------------------------------
# Learning Layer
# ---------------------------------------------------------------------------


class LearningLayer:
    """
    Analyzes observations and feeds improvements back into Knowledge.

    In the Shunya pipeline:
        Observer → Learning → Knowledge (immutable store)
    """

    def __init__(self, observer: ObserverLayer, knowledge_store=None, session=None):
        self._observer = observer
        self._knowledge = knowledge_store
        self._session = session or db.session

    def analyze(self, observation_id: int) -> LearningEntry | None:
        """Analyze a single observation and generate a learning signal."""
        obs = self._session.get(Observation, observation_id)
        if not obs:
            return None

        insights = []

        # Pattern: Failed delivery
        if obs.action.startswith("send_") and not obs.success:
            insights.append(f"Delivery failed for {obs.action}. Consider retry with different channel.")

        # Pattern: Discrepancy in proposal acceptance
        if obs.action == "proposal_sent" and obs.discrepancy:
            insights.append(f"Proposal expectation mismatch: {obs.discrepancy}. Review proposal generation logic.")

        # Pattern: Payment anomaly
        if obs.action == "payment_received" and not obs.success:
            insights.append("Payment processing failed. Check payment gateway configuration.")

        # Pattern: Booking discrepancy
        if obs.action == "booking_made" and obs.discrepancy:
            insights.append(f"Booking discrepancy: {obs.discrepancy}. Update supplier knowledge.")

        if not insights:
            insights.append(f"Observed {obs.action}: outcome matches expectation. No learning signal.")

        entry = LearningEntry(
            observation_id=observation_id,
            insight=insights[0][:1000] if insights else "Observation recorded.",
            source="observer",
            confidence=0.6 if not obs.success else 0.3,
        )
        self._session.add(entry)
        self._session.commit()
        return entry

    def analyze_batch(self, since_hours: int = 1) -> list[LearningEntry]:
        """Analyze all recent observations that haven't been analyzed yet."""
        since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        analyzed_ids = set(
            r[0] for r in
            self._session.query(LearningEntry.observation_id)
            .filter(LearningEntry.observation_id.isnot(None))
            .all()
        )
        obs_list = (
            self._session.query(Observation)
            .filter(
                Observation.created_at >= since,
                ~Observation.id.in_(analyzed_ids) if analyzed_ids else True,
            )
            .all()
        )
        entries = []
        for obs in obs_list:
            e = self.analyze(obs.id)
            if e:
                entries.append(e)
        return entries

    def apply_to_knowledge(self, entry_id: int) -> bool:
        """Apply a learning signal to the Knowledge Store."""
        if not self._knowledge:
            return False

        entry = self._session.get(LearningEntry, entry_id)
        if not entry or entry.applied:
            return False

        if entry.knowledge_fact_key and entry.recommendation:
            try:
                self._knowledge.store(
                    fact_key=entry.knowledge_fact_key,
                    value=entry.recommendation,
                    domain="travel",
                    category="learned",
                    confidence=entry.confidence,
                    evidence=entry.insight,
                    source="learning",
                    created_by="learning_layer",
                )
                entry.applied = True
                entry.applied_at = datetime.now(timezone.utc)
                self._session.commit()
                return True
            except Exception:
                self._session.rollback()
                return False
        return False

    def get_pending_applications(self) -> list[dict]:
        """Get learning entries that haven't been applied to Knowledge yet."""
        entries = (
            self._session.query(LearningEntry)
            .filter(LearningEntry.applied == False, LearningEntry.knowledge_fact_key.isnot(None))
            .order_by(LearningEntry.confidence.desc())
            .all()
        )
        return [e.to_dict() for e in entries]

    def stats(self) -> dict:
        """Return learning statistics."""
        total = self._session.query(func.count(LearningEntry.id)).scalar() or 0
        applied = self._session.query(func.count(LearningEntry.id)).filter(LearningEntry.applied == True).scalar() or 0
        return {
            "total_signals": total,
            "applied": applied,
            "pending": total - applied,
            "apply_rate": round(applied / total * 100, 1) if total else 0,
        }