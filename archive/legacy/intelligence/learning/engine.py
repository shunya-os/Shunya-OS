"""
SHUNYA Learning Engine — Pattern Detection, Model Refinement, and Intelligence Improvement

Extracts lessons from outcomes, detects patterns across decisions,
refines models, and strengthens the intelligence substrate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


@dataclass
class LearningObservation:
    observation_id: str
    data: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LearningEngine(Engine):
    """Canonical learning engine for pattern detection and model refinement."""

    engine_id: str = "learning"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._observations: list[LearningObservation] = []
        self._patterns: dict[str, list[dict]] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._observations.clear()
        self._patterns.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={
                "initialized": self._initialized,
                "observation_count": len(self._observations),
                "pattern_count": len(self._patterns),
            },
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return ["learning.observe", "learning.pattern.detect", "learning.insight.extract"]

    def observe(self, data: dict) -> LearningObservation:
        obs = LearningObservation(observation_id=f"lrn-{len(self._observations) + 1}", data=data)
        self._observations.append(obs)
        return obs

    def detect_patterns(self) -> list[dict]:
        results = []
        for pid, items in self._patterns.items():
            results.append({"pattern_id": pid, "count": len(items), "items": items[:5]})
        return results

    def register_pattern(self, pattern_id: str, observation_data: list[dict]) -> None:
        self._patterns[pattern_id] = observation_data

    def extract_insights(self) -> list[dict]:
        return [
            {"type": "observation_count", "value": len(self._observations)},
            {"type": "pattern_count", "value": len(self._patterns)},
        ]