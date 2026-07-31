"""
SHUNYA Explainable Intelligence — Observation Lifecycle

Every observation has a lifecycle:
  Detected → Validated → Active → Superseded → Archived

Insights update automatically when observations change.
No stale intelligence.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ObservationStatus(Enum):
    DETECTED = "detected"
    VALIDATED = "validated"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


# Valid transitions
VALID_TRANSITIONS = {
    ObservationStatus.DETECTED: {ObservationStatus.VALIDATED, ObservationStatus.ARCHIVED},
    ObservationStatus.VALIDATED: {ObservationStatus.ACTIVE, ObservationStatus.ARCHIVED},
    ObservationStatus.ACTIVE: {ObservationStatus.SUPERSEDED, ObservationStatus.ARCHIVED},
    ObservationStatus.SUPERSEDED: {ObservationStatus.ARCHIVED},
    ObservationStatus.ARCHIVED: set(),  # Terminal state
}


@dataclass
class Observation:
    """A single observation about an object or event.

    Each observation has a lifecycle and carries provenance references.
    """

    observation_id: str
    object_id: str
    event_id: str
    label: str
    description: str
    status: ObservationStatus = ObservationStatus.DETECTED
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validated_at: Optional[datetime] = None
    superseded_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)

    def transition_to(self, new_status: ObservationStatus) -> None:
        """Transition this observation to a new status.

        Validates the transition is allowed and updates timestamps.
        """
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}. "
                f"Allowed transitions: {[s.value for s in allowed]}"
            )

        self.status = new_status
        now = datetime.now(timezone.utc)
        if new_status == ObservationStatus.VALIDATED:
            self.validated_at = now
        elif new_status == ObservationStatus.SUPERSEDED:
            self.superseded_at = now
        elif new_status == ObservationStatus.ARCHIVED:
            self.archived_at = now

    @property
    def is_active(self) -> bool:
        return self.status == ObservationStatus.ACTIVE

    @property
    def age_hours(self) -> float:
        """Hours since this observation was detected."""
        delta = datetime.now(timezone.utc) - self.detected_at
        return delta.total_seconds() / 3600.0

    def to_dict(self) -> dict:
        return {
            "observation_id": self.observation_id,
            "object_id": self.object_id,
            "event_id": self.event_id,
            "label": self.label,
            "description": self.description,
            "status": self.status.value,
            "detected_at": self.detected_at.isoformat(),
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "superseded_at": self.superseded_at.isoformat() if self.superseded_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "evidence_ids": self.evidence_ids,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class ObservationStore:
    """In-memory store of observations.

    In production, this would be backed by a database.
    """

    def __init__(self):
        self._observations: dict[str, Observation] = {}

    def add(self, observation: Observation) -> None:
        self._observations[observation.observation_id] = observation

    def get(self, observation_id: str) -> Optional[Observation]:
        return self._observations.get(observation_id)

    def get_by_object(self, object_id: str) -> list[Observation]:
        return [
            o for o in self._observations.values()
            if o.object_id == object_id
        ]

    def get_active(self) -> list[Observation]:
        return [
            o for o in self._observations.values()
            if o.is_active
        ]

    def get_active_by_object(self, object_id: str) -> list[Observation]:
        return [
            o for o in self._observations.values()
            if o.object_id == object_id and o.is_active
        ]

    def supersede_object_observations(self, object_id: str) -> list[Observation]:
        """Supersede all active observations for an object."""
        superseded = []
        for obs in self._observations.values():
            if obs.object_id == object_id and obs.is_active:
                obs.transition_to(ObservationStatus.SUPERSEDED)
                superseded.append(obs)
        return superseded

    @property
    def count(self) -> int:
        return len(self._observations)

    def clear(self) -> None:
        self._observations.clear()


# ─── Global store ───
_store: Optional[ObservationStore] = None


def get_store() -> ObservationStore:
    global _store
    if _store is None:
        _store = ObservationStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None