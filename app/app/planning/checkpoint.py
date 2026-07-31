"""
SHUNYA Universal Planning Runtime — Checkpoint Engine

Each plan defines checkpoints. Each checkpoint requires evidence.
Checkpoints determine whether execution continues, pauses, reroutes, or escalates.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class CheckpointStatus(Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"


@dataclass
class Checkpoint:
    checkpoint_id: str
    milestone_id: str
    label: str
    description: str = ""
    evidence_required: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    status: CheckpointStatus = CheckpointStatus.PENDING
    action_on_fail: str = "pause"
    """'pause', 'reroute', 'escalate', 'continue'"""
    alternative_path_id: str = ""
    created_at: str = ""
    resolved_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def pass_checkpoint(self, evidence_id: str = "") -> None:
        self.status = CheckpointStatus.PASSED
        self.resolved_at = datetime.now(timezone.utc).isoformat()
        if evidence_id:
            self.evidence_ids.append(evidence_id)

    def fail_checkpoint(self, reason: str = "") -> None:
        self.status = CheckpointStatus.FAILED
        self.resolved_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "milestone_id": self.milestone_id,
            "label": self.label,
            "description": self.description,
            "evidence_required": self.evidence_required,
            "evidence_ids": self.evidence_ids,
            "status": self.status.value,
            "action_on_fail": self.action_on_fail,
            "alternative_path_id": self.alternative_path_id,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


class CheckpointEngine:
    def __init__(self):
        self._checkpoints: dict[str, Checkpoint] = {}

    def add(self, cp: Checkpoint) -> None:
        self._checkpoints[cp.checkpoint_id] = cp

    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        return self._checkpoints.get(checkpoint_id)

    def get_for_milestone(self, milestone_id: str) -> list[Checkpoint]:
        return [c for c in self._checkpoints.values() if c.milestone_id == milestone_id]

    def all_passed(self, milestone_id: str) -> bool:
        cps = self.get_for_milestone(milestone_id)
        if not cps:
            return True
        return all(c.status == CheckpointStatus.PASSED or c.status == CheckpointStatus.WAIVED for c in cps)

    @property
    def count(self) -> int:
        return len(self._checkpoints)

    def clear(self) -> None:
        self._checkpoints.clear()


_engine: Optional[CheckpointEngine] = None


def get_engine() -> CheckpointEngine:
    global _engine
    if _engine is None:
        _engine = CheckpointEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None