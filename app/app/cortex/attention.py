"""
SHUNYA Organizational Cortex — Executive Attention Engine

The attention engine is responsible for prioritization, not reporting.
Every active object competes for executive attention.

Attention is computed using universal signals:
  Impact, Urgency, Commitment Risk, Evidence Confidence,
  Execution Delay, Policy Severity, Dependency Weight,
  Opportunity Window, Learning Confidence, Organizational Reach
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class AttentionStatus(Enum):
    DETECTED = "detected"
    RANKED = "ranked"
    ASSIGNED = "assigned"
    OBSERVED = "observed"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


ATTENTION_TRANSITIONS = {
    AttentionStatus.DETECTED: {AttentionStatus.RANKED, AttentionStatus.ARCHIVED},
    AttentionStatus.RANKED: {AttentionStatus.ASSIGNED, AttentionStatus.ARCHIVED},
    AttentionStatus.ASSIGNED: {AttentionStatus.OBSERVED, AttentionStatus.ARCHIVED},
    AttentionStatus.OBSERVED: {AttentionStatus.RESOLVED, AttentionStatus.RANKED, AttentionStatus.ARCHIVED},
    AttentionStatus.RESOLVED: {AttentionStatus.ARCHIVED},
    AttentionStatus.ARCHIVED: set(),
}


@dataclass
class AttentionItem:
    """An item competing for executive attention.

    Priority is computed from universal signals.
    """

    item_id: str
    label: str
    description: str
    source_type: str  # 'risk', 'opportunity', 'decision', 'commitment', 'observation', 'learning'
    source_id: str
    priority_score: float = 0.0
    """0.0 = lowest priority, 1.0 = highest priority."""

    impact: float = 0.5
    urgency: float = 0.5
    commitment_risk: float = 0.0
    evidence_confidence: float = 0.5
    execution_delay: float = 0.0
    policy_severity: float = 0.0
    dependency_weight: float = 0.0
    opportunity_window: float = 0.0
    learning_confidence: float = 0.0
    organizational_reach: float = 0.0

    status: AttentionStatus = AttentionStatus.DETECTED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ranked_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    observed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)

    def transition_to(self, new_status: AttentionStatus) -> None:
        allowed = ATTENTION_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        now = datetime.now(timezone.utc)
        if new_status == AttentionStatus.RANKED:
            self.ranked_at = now
        elif new_status == AttentionStatus.ASSIGNED:
            self.assigned_at = now
        elif new_status == AttentionStatus.OBSERVED:
            self.observed_at = now
        elif new_status == AttentionStatus.RESOLVED:
            self.resolved_at = now

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "label": self.label,
            "description": self.description,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "priority_score": round(self.priority_score, 4),
            "signals": {
                "impact": self.impact,
                "urgency": self.urgency,
                "commitment_risk": self.commitment_risk,
                "evidence_confidence": self.evidence_confidence,
                "execution_delay": self.execution_delay,
                "policy_severity": self.policy_severity,
                "dependency_weight": self.dependency_weight,
                "opportunity_window": self.opportunity_window,
                "learning_confidence": self.learning_confidence,
                "organizational_reach": self.organizational_reach,
            },
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "ranked_at": self.ranked_at.isoformat() if self.ranked_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata,
        }


# ─── Attention weights (universal, tunable) ───
ATTENTION_WEIGHTS = {
    "impact": 0.20,
    "urgency": 0.15,
    "commitment_risk": 0.15,
    "evidence_confidence": 0.10,
    "execution_delay": 0.10,
    "policy_severity": 0.10,
    "dependency_weight": 0.05,
    "opportunity_window": 0.05,
    "learning_confidence": 0.05,
    "organizational_reach": 0.05,
}


def compute_priority(item: AttentionItem) -> float:
    """Compute a priority score from an attention item's signals.

    Returns a float between 0.0 and 1.0.
    """
    score = 0.0
    total_weight = 0.0

    signals = {
        "impact": item.impact,
        "urgency": item.urgency,
        "commitment_risk": item.commitment_risk,
        "evidence_confidence": item.evidence_confidence,
        "execution_delay": item.execution_delay,
        "policy_severity": item.policy_severity,
        "dependency_weight": item.dependency_weight,
        "opportunity_window": item.opportunity_window,
        "learning_confidence": item.learning_confidence,
        "organizational_reach": item.organizational_reach,
    }

    for name, value in signals.items():
        weight = ATTENTION_WEIGHTS.get(name, 0.0)
        score += value * weight
        total_weight += weight

    return score / total_weight if total_weight > 0 else 0.0


class AttentionEngine:
    """The Executive Attention Engine.

    Responsible for continuously evaluating the organization state
    and producing an ordered attention queue.
    """

    def __init__(self):
        self._items: dict[str, AttentionItem] = {}
        self._item_id_counter: int = 0

    def add_item(self, item: AttentionItem) -> AttentionItem:
        item.priority_score = compute_priority(item)
        self._items[item.item_id] = item
        return item

    def get_item(self, item_id: str) -> Optional[AttentionItem]:
        return self._items.get(item_id)

    def get_attention_queue(self, limit: int = 20) -> list[AttentionItem]:
        """Return the ordered attention queue, highest priority first.

        Only includes items that are not resolved or archived.
        """
        active = [
            item for item in self._items.values()
            if item.status not in (AttentionStatus.RESOLVED, AttentionStatus.ARCHIVED)
        ]
        active.sort(key=lambda i: i.priority_score, reverse=True)
        return active[:limit]

    def get_by_source(self, source_type: str, source_id: str) -> Optional[AttentionItem]:
        for item in self._items.values():
            if item.source_type == source_type and item.source_id == source_id:
                return item
        return None

    def reorder(self) -> None:
        """Recompute all priority scores and reorder."""
        for item in self._items.values():
            item.priority_score = compute_priority(item)

    @property
    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()


_engine: Optional[AttentionEngine] = None


def get_engine() -> AttentionEngine:
    global _engine
    if _engine is None:
        _engine = AttentionEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None