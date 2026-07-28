"""SHUNYA — Legacy ObserverLayer (Backward Compatibility).

Wraps the canonical ObserverEngine to provide backward-compatible
interfaces for existing call sites.

All new code SHOULD import from app.shunya.observer_engine directly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.shunya.observer_engine.engine import ObserverEngine, get_observer_engine
from app.shunya.observer_engine.models import ObserverInput


class ObserverLayer:
    """Legacy ObserverLayer wrapping ObserverEngine for backward compatibility."""

    def __init__(self, session=None):
        self._engine = ObserverEngine()
        self._session = session  # Preserved for API compatibility

    @property
    def engine(self) -> ObserverEngine:
        return self._engine

    def observe(self, action: str, outcome: str, *,
                lead_id: int = None,
                expected: str = "",
                channel: str = "internal",
                success: bool = True,
                confidence: float = 1.0,
                metadata: dict = None) -> 'LegacyObservation':
        """Legacy observe() API — wraps into ObserverInput and delegates."""
        inp = ObserverInput(
            workflow_id=f"legacy-{action}-{lead_id or 0}",
            tenant_id=lead_id or 1,
            observation_type="passive",
            tasks=[{
                "task_id": f"legacy_{action}",
                "action": action,
                "state": "completed" if success else "failed",
                "target": channel,
                "payload": metadata or {},
            }],
            evidence=[{
                "evidence_id": f"ev_{action}",
                "task_id": f"legacy_{action}",
                "action": action,
                "channel": channel,
                "success": success,
                "response": {"outcome": outcome},
            }],
        )

        output = self._engine.observe(inp)
        return LegacyObservation(
            id=output.observation_id,
            action=action,
            actual_outcome=outcome,
            expected_outcome=expected,
            success=success,
            confidence=output.observation.confidence if output.observation else confidence,
            channel=channel,
            metadata=metadata or {},
        )

    def get_by_lead(self, lead_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        return self._engine.list_observations(limit)

    def get_anomalies(self, since_hours: int = 24) -> List[Dict[str, Any]]:
        return self._engine.list_anomalies(limit=50)

    def get_discrepancies(self, since_hours: int = 24) -> List[Dict[str, Any]]:
        return self._engine.list_deviations(limit=50)

    def stats(self) -> Dict[str, Any]:
        return self._engine.stats


class LegacyObservation:
    """Backward-compatible observation result shape."""
    def __init__(self, id: str, action: str, actual_outcome: str,
                 expected_outcome: str, success: bool, confidence: float,
                 channel: str, metadata: dict):
        self.id = id
        self.action = action
        self.actual_outcome = actual_outcome
        self.expected_outcome = expected_outcome
        self.success = success
        self.confidence = confidence
        self.channel = channel
        self.metadata = metadata
        self.discrepancy = ""
        if expected_outcome and actual_outcome and expected_outcome != actual_outcome:
            self.discrepancy = f"Expected: {expected_outcome[:200]} | Actual: {actual_outcome[:200]}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "actual_outcome": self.actual_outcome,
            "expected_outcome": self.expected_outcome,
            "discrepancy": self.discrepancy,
            "success": self.success,
            "confidence": self.confidence,
            "channel": self.channel,
            "metadata": self.metadata,
        }