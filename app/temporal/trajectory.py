"""
SHUNYA Temporal Intelligence — Trajectory Engine

The Trajectory Engine compares snapshots and computes:
  Direction, Velocity, Acceleration, Stability, Volatility,
  Recovery, Decline, Growth, Regression, Momentum
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from app.temporal.snapshot import TemporalSnapshot


@dataclass
class ChangeRecord:
    """A first-class change between two snapshots for a single metric."""

    metric_name: str
    current_value: float
    previous_value: float
    absolute_change: float
    percentage_change: float  # INF if previous was 0
    direction: str  # 'up', 'down', 'stable'

    @property
    def is_significant(self, threshold: float = 0.05) -> bool:
        return abs(self.percentage_change) > threshold if self.previous_value != 0 else abs(self.absolute_change) > 0


@dataclass
class Trajectory:
    """The computed trajectory between two snapshots."""

    snapshot_previous_id: str
    snapshot_current_id: str
    time_interval_seconds: float

    # Direction of key metrics
    overall_health_direction: str = "stable"
    execution_direction: str = "stable"
    decision_direction: str = "stable"
    knowledge_direction: str = "stable"
    evidence_direction: str = "stable"

    # Composite
    growth: bool = False
    decline: bool = False
    recovery: bool = False
    regression: bool = False
    momentum: float = 0.0
    volatility: float = 0.0

    # Changes
    changes: list[ChangeRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "snapshot_previous_id": self.snapshot_previous_id,
            "snapshot_current_id": self.snapshot_current_id,
            "time_interval_seconds": self.time_interval_seconds,
            "overall_health_direction": self.overall_health_direction,
            "execution_direction": self.execution_direction,
            "decision_direction": self.decision_direction,
            "knowledge_direction": self.knowledge_direction,
            "evidence_direction": self.evidence_direction,
            "growth": self.growth,
            "decline": self.decline,
            "recovery": self.recovery,
            "regression": self.regression,
            "momentum": round(self.momentum, 4),
            "volatility": round(self.volatility, 4),
            "changes": [
                {
                    "metric": c.metric_name,
                    "from": c.previous_value,
                    "to": c.current_value,
                    "absolute": round(c.absolute_change, 4),
                    "percentage": round(c.percentage_change * 100, 2) if c.percentage_change != float('inf') else None,
                    "direction": c.direction,
                }
                for c in self.changes
            ],
        }


def _direction(current: float, previous: float) -> str:
    if current > previous:
        return "up"
    elif current < previous:
        return "down"
    return "stable"


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return float('inf') if current != 0 else 0.0
    return (current - previous) / abs(previous)


def compute_trajectory(previous: TemporalSnapshot, current: TemporalSnapshot) -> Trajectory:
    """Compute the trajectory between two snapshots.

    Pure mathematical comparison. No business assumptions.
    """
    import math
    prev_metrics = previous.to_dict().get("metrics", {})
    curr_metrics = current.to_dict().get("metrics", {})

    traj = Trajectory(
        snapshot_previous_id=previous.snapshot_id,
        snapshot_current_id=current.snapshot_id,
        time_interval_seconds=0.0,  # Calculated below
    )

    # Time interval
    try:
        from datetime import datetime
        t1 = datetime.fromisoformat(previous.timestamp)
        t2 = datetime.fromisoformat(current.timestamp)
        traj.time_interval_seconds = (t2 - t1).total_seconds()
    except (ValueError, TypeError):
        traj.time_interval_seconds = 0.0

    # ─── Metric changes ───
    metric_pairs = [
        ("overall_health", previous.overall_health, current.overall_health),
        ("total_decisions",
         prev_metrics.get("total_decisions", 0),
         curr_metrics.get("total_decisions", 0)),
        ("active_commitments",
         prev_metrics.get("active_commitments", 0),
         curr_metrics.get("active_commitments", 0)),
        ("active_observations",
         prev_metrics.get("active_observations", 0),
         curr_metrics.get("active_observations", 0)),
        ("total_insights",
         prev_metrics.get("total_insights", 0),
         curr_metrics.get("total_insights", 0)),
        ("learning_signals",
         prev_metrics.get("learning_signals", 0),
         curr_metrics.get("learning_signals", 0)),
        ("waiting_approval",
         prev_metrics.get("waiting_approval", 0),
         curr_metrics.get("waiting_approval", 0)),
        ("critical_risks",
         prev_metrics.get("critical_risks", 0),
         curr_metrics.get("critical_risks", 0)),
    ]

    changes = []
    for name, prev_val, curr_val in metric_pairs:
        pv = float(prev_val)
        cv = float(curr_val)
        changes.append(ChangeRecord(
            metric_name=name,
            current_value=cv,
            previous_value=pv,
            absolute_change=cv - pv,
            percentage_change=_pct_change(cv, pv),
            direction=_direction(cv, pv),
        ))
    traj.changes = changes

    # ─── Direction ───
    traj.overall_health_direction = _direction(current.overall_health, previous.overall_health)
    health_prev = previous.health
    health_curr = current.health
    traj.execution_direction = _direction(
        health_curr.get("execution_health", 0.5),
        health_prev.get("execution_health", 0.5),
    )
    traj.decision_direction = _direction(
        health_curr.get("decision_health", 0.5),
        health_prev.get("decision_health", 0.5),
    )
    traj.knowledge_direction = _direction(
        health_curr.get("knowledge_health", 0.5),
        health_prev.get("knowledge_health", 0.5),
    )
    traj.evidence_direction = _direction(
        health_curr.get("evidence_health", 0.5),
        health_prev.get("evidence_health", 0.5),
    )

    # ─── Composite flags ───
    up_count = sum(1 for c in changes if c.direction == "up")
    down_count = sum(1 for c in changes if c.direction == "down")
    total = len(changes)
    traj.growth = up_count > down_count
    traj.decline = down_count > up_count
    traj.recovery = traj.overall_health_direction == "up" and previous.overall_health < 0.5
    traj.regression = traj.overall_health_direction == "down" and previous.overall_health >= 0.5

    # ─── Momentum (average absolute change across all metrics) ───
    if changes:
        traj.momentum = sum(abs(c.absolute_change) for c in changes) / len(changes)

    # ─── Volatility (standard deviation of metric changes) ───
    if len(changes) > 1:
        mean = sum(c.absolute_change for c in changes) / len(changes)
        variance = sum((c.absolute_change - mean) ** 2 for c in changes) / len(changes)
        traj.volatility = math.sqrt(variance)

    return traj


class TrajectoryStore:
    """Stores computed trajectories between snapshots."""

    def __init__(self):
        self._trajectories: list[Trajectory] = []

    def add(self, trajectory: Trajectory) -> None:
        self._trajectories.append(trajectory)

    def get_all(self, limit: int = 20) -> list[Trajectory]:
        return self._trajectories[-limit:]

    def get_latest(self) -> Optional[Trajectory]:
        if self._trajectories:
            return self._trajectories[-1]
        return None

    @property
    def count(self) -> int:
        return len(self._trajectories)

    def clear(self) -> None:
        self._trajectories.clear()


_store: Optional[TrajectoryStore] = None


def get_store() -> TrajectoryStore:
    global _store
    if _store is None:
        _store = TrajectoryStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None