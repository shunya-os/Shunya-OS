"""
SHUNYA Decision Runtime — Structured Learning
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class LearningRecord:
    learning_id: str
    decision_id: str
    outcome_id: str
    commitment_id: str
    expected_outcome: str = ""
    actual_outcome: str = ""
    variance: str = ""
    variance_magnitude: float = 0.0
    reason: str = ""
    improvement_opportunity: str = ""
    learning_confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: int = 1
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "learning_id": self.learning_id,
            "decision_id": self.decision_id,
            "outcome_id": self.outcome_id,
            "commitment_id": self.commitment_id,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "variance": self.variance,
            "variance_magnitude": self.variance_magnitude,
            "reason": self.reason,
            "improvement_opportunity": self.improvement_opportunity,
            "learning_confidence": self.learning_confidence,
            "created_at": self.created_at.isoformat(),
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }


class LearningStore:
    def __init__(self):
        self._records: dict[str, LearningRecord] = {}

    def add(self, record: LearningRecord) -> None:
        self._records[record.learning_id] = record

    def get(self, learning_id: str) -> Optional[LearningRecord]:
        return self._records.get(learning_id)

    def get_by_decision(self, decision_id: str) -> Optional[LearningRecord]:
        for r in self._records.values():
            if r.decision_id == decision_id:
                return r
        return None

    def get_all(self) -> list[LearningRecord]:
        return list(self._records.values())

    @property
    def count(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()


_store: Optional[LearningStore] = None


def get_store() -> LearningStore:
    global _store
    if _store is None:
        _store = LearningStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None