"""
SHUNYA Decision Runtime — Outcome Recording
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Outcome:
    outcome_id: str
    commitment_id: str
    decision_id: str
    label: str
    description: str
    quality: float = 0.0
    unexpected_effects: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    learning_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: int = 1
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "outcome_id": self.outcome_id,
            "commitment_id": self.commitment_id,
            "decision_id": self.decision_id,
            "label": self.label,
            "description": self.description,
            "quality": self.quality,
            "unexpected_effects": self.unexpected_effects,
            "evidence_ids": self.evidence_ids,
            "learning_id": self.learning_id,
            "created_at": self.created_at.isoformat(),
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }


class OutcomeStore:
    def __init__(self):
        self._outcomes: dict[str, Outcome] = {}

    def add(self, outcome: Outcome) -> None:
        self._outcomes[outcome.outcome_id] = outcome

    def get(self, outcome_id: str) -> Optional[Outcome]:
        return self._outcomes.get(outcome_id)

    def get_by_decision(self, decision_id: str) -> Optional[Outcome]:
        for o in self._outcomes.values():
            if o.decision_id == decision_id:
                return o
        return None

    def get_by_commitment(self, commitment_id: str) -> Optional[Outcome]:
        for o in self._outcomes.values():
            if o.commitment_id == commitment_id:
                return o
        return None

    @property
    def count(self) -> int:
        return len(self._outcomes)

    def clear(self) -> None:
        self._outcomes.clear()


_store: Optional[OutcomeStore] = None


def get_store() -> OutcomeStore:
    global _store
    if _store is None:
        _store = OutcomeStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None