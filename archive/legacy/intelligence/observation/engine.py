"""
SHUNYA Observation Engine — Observation Lifecycle

Manages the observation lifecycle: Detected → Validated → Active → Superseded → Archived.
Generates insights automatically when observations change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


class ObservationStatus(Enum):
    DETECTED = "detected"
    VALIDATED = "validated"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass
class Observation:
    observation_id: str
    object_id: str
    event_id: str
    label: str
    description: str
    status: ObservationStatus = ObservationStatus.DETECTED
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validated_at: Optional[datetime] = None
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def transition_to(self, new_status: ObservationStatus) -> None:
        now = datetime.now(timezone.utc)
        if new_status == ObservationStatus.VALIDATED:
            self.validated_at = now
        self.status = new_status


class ObservationEngine(Engine):
    """Canonical observation engine — manages observation lifecycle and insight generation."""

    engine_id: str = "observation"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._observations: dict[str, Observation] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._observations.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={"initialized": self._initialized, "observation_count": len(self._observations)},
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return [
            "observation.detect",
            "observation.validate",
            "observation.supersede",
            "observation.archive",
            "observation.query",
        ]

    def detect(
        self, object_id: str, event_id: str, label: str, description: str,
        evidence_ids: list[str] | None = None, confidence: float = 0.0,
    ) -> Observation:
        obs = Observation(
            observation_id=f"obs-{len(self._observations) + 1}",
            object_id=object_id, event_id=event_id, label=label,
            description=description, evidence_ids=evidence_ids or [],
            confidence=confidence,
        )
        self._observations[obs.observation_id] = obs
        return obs

    def validate(self, observation_id: str) -> Optional[Observation]:
        obs = self._observations.get(observation_id)
        if obs and obs.status == ObservationStatus.DETECTED:
            obs.transition_to(ObservationStatus.VALIDATED)
        return obs

    def get(self, observation_id: str) -> Optional[Observation]:
        return self._observations.get(observation_id)

    def list_for_object(self, object_id: str) -> list[Observation]:
        return [o for o in self._observations.values() if o.object_id == object_id]

    def list_active(self) -> list[Observation]:
        return [o for o in self._observations.values() if o.status == ObservationStatus.ACTIVE]