"""SHUNYA — Legacy LearningLayer (Backward Compatibility).

Wraps the canonical LearningEngine to provide backward-compatible
interfaces for existing call sites.

All new code SHOULD import from app.shunya.learning_engine directly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.shunya.learning_engine.engine import LearningEngine, get_learning_engine
from app.shunya.learning_engine.models import LearningInput


class LearningLayer:
    """Legacy LearningLayer wrapping LearningEngine for backward compatibility."""

    def __init__(self, observer=None, knowledge_store=None, session=None):
        self._engine = LearningEngine()
        self._observer = observer
        self._knowledge = knowledge_store
        self._session = session

    @property
    def engine(self) -> LearningEngine:
        return self._engine

    def analyze(self, observation_id: Any) -> Any:
        """Legacy analyze() API — wraps as a single signal learn cycle."""
        signal = {
            "signal_id": f"legacy_{observation_id}",
            "observation_id": str(observation_id),
            "signal_type": "observation",
            "description": f"Analyzing observation {observation_id}",
            "dimension": "legacy",
            "confidence": 0.5,
        }
        inp = LearningInput(
            signals=[signal],
            observation_ids=[str(observation_id)],
            tenant_id=1,
        )
        output = self._engine.learn(inp)
        return output

    def analyze_batch(self, since_hours: int = 1) -> List[Any]:
        """Legacy batch analyze — creates one signal per hour."""
        signal = {
            "signal_id": f"batch_{since_hours}h",
            "signal_type": "success",
            "description": f"Batch analysis of last {since_hours} hours",
            "dimension": "batch",
            "confidence": 0.5,
        }
        inp = LearningInput(
            signals=[signal],
            tenant_id=1,
        )
        output = self._engine.learn(inp)
        return output.recommendations

    def stats(self) -> Dict[str, Any]:
        return self._engine.stats