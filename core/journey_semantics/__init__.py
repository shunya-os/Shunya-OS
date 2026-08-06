"""Journey Semantics — Internal Shared Primitive.

Journey Semantics eliminates duplicated lifecycle journey logic across all UCPs.

This is NOT a Universal Capability Package.
This is NOT a Runtime.
This is NOT user-visible.

It is an internal reusable primitive.

Principles:
- Journey Semantics never stores state — state stays on Living Objects
- Journey Semantics never replaces Reality Runtime
- Journey Semantics is stateless and pure
- Every result is derived from data, never mutated
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


# ── Core Stage Model ───────────────────────────────────────────────────
# The fundamental unit of journey progression is a Stage.
# A journey progresses through stages via validated transitions.


StageMap = dict[str, list[str]]
"""A mapping from current stage → list of valid next stages."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── Lifecycle Validation ────────────────────────────────────────────────
# Replaces duplicated `valid_transitions()` classmethod and `transition_to()`
# found in UCP-06 (AgreementStatus) and UCP-07 (AssetStatus).


def validate_transition(current: str, target: str, transitions: StageMap) -> bool:
    """Check if a transition from current to target is valid."""
    allowed = transitions.get(current, [])
    return target in allowed


def apply_transition(
    current: str,
    target: str,
    transitions: StageMap,
    on_transition: Callable[[str, str], None] | None = None,
) -> tuple[bool, str]:
    """Attempt a state transition. Returns (success, new_status_or_reason).

    on_transition(current, target) is called on success if provided.
    This lets the caller update timestamps, emit events, etc. without
    duplicating transition logic.
    """
    if not validate_transition(current, target, transitions):
        allowed = transitions.get(current, [])
        return False, f"Cannot transition from '{current}' to '{target}'. Allowed: {allowed}"

    if on_transition:
        on_transition(current, target)
    return True, target


# ── Milestone Progression ──────────────────────────────────────────────
# Replaces duplicated milestone logic across UCPs.
# A milestone is a named checkpoint in a journey.


class MilestoneStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

    @classmethod
    def valid_transitions(cls) -> StageMap:
        return {
            "pending": ["in_progress", "skipped", "cancelled"],
            "in_progress": ["completed", "delayed", "blocked", "cancelled"],
            "delayed": ["in_progress", "completed", "blocked", "cancelled"],
            "blocked": ["in_progress", "delayed", "cancelled"],
            "completed": [],
            "skipped": [],
            "cancelled": [],
        }


@dataclass
class Milestone:
    """A named checkpoint in a journey with status tracking."""
    milestone_id: str = ""
    title: str = ""
    description: str = ""
    status: str = MilestoneStatus.PENDING.value
    due_date: str = ""
    completed_date: str | None = None
    dependencies: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def advance_to(self, new_status: str) -> bool:
        valid = MilestoneStatus.valid_transitions().get(self.status, [])
        if new_status not in valid:
            return False
        self.status = new_status
        if new_status == MilestoneStatus.COMPLETED.value:
            self.completed_date = _now_iso()
        return True

    @property
    def is_terminal(self) -> bool:
        return self.status in (MilestoneStatus.COMPLETED.value, MilestoneStatus.SKIPPED.value,
                                MilestoneStatus.CANCELLED.value)

    @property
    def is_blocking(self) -> bool:
        return self.status in (MilestoneStatus.BLOCKED.value, MilestoneStatus.DELAYED.value)

    def to_dict(self) -> dict[str, Any]:
        return {"milestone_id": self.milestone_id, "title": self.title,
                "description": self.description, "status": self.status,
                "due_date": self.due_date, "completed_date": self.completed_date,
                "dependencies": list(self.dependencies),
                "evidence_ids": list(self.evidence_ids)}


# ── Journey Progress ───────────────────────────────────────────────────
# Replaces duplicated progress_pct, delayed/blocked milestones logic.


def compute_progress_pct(milestones: list[Milestone]) -> float:
    """Compute overall progress as percentage of completed milestones."""
    total = len(milestones)
    if total == 0:
        return 0.0
    completed = sum(1 for m in milestones if m.status == MilestoneStatus.COMPLETED.value)
    return round((completed / total) * 100, 1)


def find_delayed_milestones(milestones: list[Milestone]) -> list[Milestone]:
    """Find milestones that are past due or explicitly delayed."""
    delayed = [m for m in milestones if m.status == MilestoneStatus.DELAYED.value]
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    for m in milestones:
        if m.status in (MilestoneStatus.PENDING.value, MilestoneStatus.IN_PROGRESS.value) and m.due_date:
            try:
                due = datetime.fromisoformat(m.due_date.replace("Z", "+00:00"))
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                if now > due and m not in delayed:
                    delayed.append(m)
            except (ValueError, TypeError):
                pass
    return delayed


def find_blocked_milestones(milestones: list[Milestone]) -> list[Milestone]:
    """Find milestones that are blocked."""
    return [m for m in milestones if m.status == MilestoneStatus.BLOCKED.value]


# ── Disruption & Recovery ──────────────────────────────────────────────
# Replaces duplicated disruption detection logic across UCP-09, UCP-10, UCP-11.


@dataclass
class Disruption:
    """A disruption event that affects journey progression."""
    disruption_id: str = ""
    description: str = ""
    severity: str = "medium"
    affected_stages: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=_now_iso)
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"disruption_id": self.disruption_id, "description": self.description,
                "severity": self.severity, "affected_stages": list(self.affected_stages),
                "recommendations": list(self.recommendations),
                "timestamp": self.timestamp, "resolved": self.resolved}


def assess_disruption_impact(
    current_stage: str,
    disruption_severity: str,
    transitions: StageMap,
) -> dict[str, Any]:
    """Assess how a disruption affects journey progression."""
    allowed = transitions.get(current_stage, [])
    # A disruption may force regression or stall
    can_proceed = len(allowed) > 0
    if disruption_severity in ("critical", "high"):
        can_proceed = False

    return {
        "can_proceed": can_proceed,
        "current_stage": current_stage,
        "available_transitions": allowed if can_proceed else [],
        "recommendation": "Resolve disruption before proceeding" if not can_proceed else "Proceed with caution",
        "severity": disruption_severity,
    }


# ── Journey Health ──────────────────────────────────────────────────────
# Replaces duplicated health assessment patterns across UCPs.


def compute_stage_health(
    milestones: list[Milestone],
    delays_weight: float = 0.3,
    blocks_weight: float = 0.4,
) -> dict[str, Any]:
    """Compute health from milestone progression data."""
    total = len(milestones)
    if total == 0:
        return {"score": 0.5, "level": "fair", "assessment": "no_data"}

    progress = compute_progress_pct(milestones) / 100.0
    delayed = len(find_delayed_milestones(milestones))
    blocked = len(find_blocked_milestones(milestones))

    score = 0.5 + progress * 0.2
    score -= (delayed / max(total, 1)) * delays_weight
    score -= (blocked / max(total, 1)) * blocks_weight
    score = max(0.0, min(1.0, score))

    if score >= 0.7:
        level = "healthy"
    elif score >= 0.4:
        level = "fair"
    else:
        level = "at_risk"

    return {"score": round(score, 4), "level": level, "delayed": delayed,
            "blocked": blocked, "progress_pct": round(progress * 100, 1),
            "assessment": "on_track" if level == "healthy" else "needs_attention" if level == "fair" else "critical_intervention_needed"}


# ── Journey Lifecycle Builder ──────────────────────────────────────────
# Replaces duplicated valid_transitions() classmethod definition pattern.
# Usage:
#   MY_STATUS = journey_lifecycle("MyStatus", {
#       "discovered": ["registered", "archived"],
#       "registered": ["verified", "archived"],
#       ...
#   })


def journey_lifecycle(name: str, transitions: StageMap) -> type:
    """Create a status enum class with valid_transitions classmethod.

    This replaces the pattern of writing a full Status enum with
    valid_transitions() manually in every UCP.
    """
    # Collect all unique states
    all_states = set(transitions.keys())
    for targets in transitions.values():
        all_states.update(targets)

    members = {}
    for i, state in enumerate(sorted(all_states), start=1):
        members[state.upper().replace(" ", "_").replace("-", "_")] = state

    enum_cls = Enum(name, members)

    # Attach transitions data and methods
    enum_cls._transitions = transitions
    enum_cls.valid_transitions = classmethod(lambda cls: transitions)
    enum_cls.is_valid_transition = classmethod(
        lambda cls, current, target: validate_transition(current, target, transitions)
    )
    return enum_cls