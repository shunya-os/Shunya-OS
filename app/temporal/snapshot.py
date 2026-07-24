"""
SHUNYA Temporal Intelligence — TemporalSnapshot & SnapshotStore

A TemporalSnapshot captures OrganizationState at a point in time.
Snapshots are immutable. They become the authoritative historical record.

Each snapshot records:
  Timestamp, OrganizationState, Health, Attention Queue,
  Critical Metrics, Execution Metrics, Decision Metrics, Learning Metrics
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.cortex.state import OrganizationState, get_synthesizer
from app.cortex.attention import get_engine as get_attention_engine
from app.cortex.health import compute_health


@dataclass(frozen=True)
class TemporalSnapshot:
    """An immutable snapshot of organizational state at a point in time.

    Frozen dataclass — once created, cannot be modified.
    """

    snapshot_id: str
    timestamp: str  # ISO format
    organization_name: str = ""

    # ─── Core state ───
    state: dict = field(default_factory=dict)
    health: dict = field(default_factory=dict)
    overall_health: float = 0.0

    # ─── Attention ───
    attention_queue: list = field(default_factory=list)
    attention_count: int = 0
    top_priority_score: float = 0.0

    # ─── Metrics ───
    total_decisions: int = 0
    active_commitments: int = 0
    active_observations: int = 0
    total_insights: int = 0
    learning_signals: int = 0
    waiting_approval: int = 0
    critical_risks: int = 0

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "organization_name": self.organization_name,
            "state": self.state,
            "health": self.health,
            "overall_health": self.overall_health,
            "attention_queue": self.attention_queue,
            "attention_count": self.attention_count,
            "top_priority_score": self.top_priority_score,
            "metrics": {
                "total_decisions": self.total_decisions,
                "active_commitments": self.active_commitments,
                "active_observations": self.active_observations,
                "total_insights": self.total_insights,
                "learning_signals": self.learning_signals,
                "waiting_approval": self.waiting_approval,
                "critical_risks": self.critical_risks,
            },
        }


class SnapshotStore:
    """Immutable store of snapshots. Snapshots can only be added, never modified."""

    def __init__(self):
        self._snapshots: dict[str, TemporalSnapshot] = {}
        self._ordered_ids: list[str] = []

    def add(self, snapshot: TemporalSnapshot) -> None:
        if snapshot.snapshot_id in self._snapshots:
            raise ValueError(f"Snapshot {snapshot.snapshot_id} already exists")
        self._snapshots[snapshot.snapshot_id] = snapshot
        self._ordered_ids.append(snapshot.snapshot_id)

    def get(self, snapshot_id: str) -> Optional[TemporalSnapshot]:
        return self._snapshots.get(snapshot_id)

    def get_all(self, limit: int = 50) -> list[TemporalSnapshot]:
        ids = self._ordered_ids[-limit:]
        return [self._snapshots[i] for i in ids]

    def get_range(self, start: int, end: int) -> list[TemporalSnapshot]:
        ids = self._ordered_ids[start:end]
        return [self._snapshots[i] for i in ids]

    def get_latest(self, n: int = 2) -> list[TemporalSnapshot]:
        """Get the N most recent snapshots."""
        ids = self._ordered_ids[-n:]
        return [self._snapshots[i] for i in ids]

    @property
    def latest(self) -> Optional[TemporalSnapshot]:
        if self._ordered_ids:
            return self._snapshots[self._ordered_ids[-1]]
        return None

    @property
    def count(self) -> int:
        return len(self._snapshots)

    def clear(self) -> None:
        self._snapshots.clear()
        self._ordered_ids.clear()


def capture_snapshot(org_name: str = "Organization") -> TemporalSnapshot:
    """Capture a snapshot of the current organizational state.

    This is the canonical way to create snapshots.
    It reads from the Cortex and records everything immutably.
    """
    synth = get_synthesizer(org_name)
    state = synth.synthesize()
    attention = get_attention_engine()
    queue = attention.get_attention_queue(limit=20)
    now = datetime.now(timezone.utc)
    sid = now.strftime("snap_%Y%m%d_%H%M%S_%f")

    snapshot = TemporalSnapshot(
        snapshot_id=sid,
        timestamp=now.isoformat(),
        organization_name=org_name,
        state=state.to_dict(),
        health=state.health_scores,
        overall_health=state.overall_health,
        attention_queue=[item.to_dict() for item in queue],
        attention_count=len(queue),
        top_priority_score=queue[0].priority_score if queue else 0.0,
        total_decisions=state.total_decisions,
        active_commitments=state.active_commitments,
        active_observations=state.active_observations,
        total_insights=state.total_insights,
        learning_signals=state.learning_signals,
        waiting_approval=state.waiting_approval,
        critical_risks=state.critical_risks,
    )
    return snapshot


_store: Optional[SnapshotStore] = None


def get_store() -> SnapshotStore:
    global _store
    if _store is None:
        _store = SnapshotStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None