"""Universal Personal Operating System — Models.

The Personal OS is the orchestration layer. It does not duplicate
Living Objects from existing UCPs. It composes them.

Only Personal-OS-specific models live here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def _uid() -> str:
    import uuid; return str(uuid.uuid4())


@dataclass
class LivingContextSnapshot:
    """A point-in-time composite view across ALL UCP Living Objects."""
    snapshot_id: str = field(default_factory=_uid)
    timestamp: str = field(default_factory=_now_iso)
    owner_id: str = ""
    context_type: str = "auto"

    # Composed from frozen UCPs — IDs only, never full objects
    active_initiatives: list[str] = field(default_factory=list)
    active_agreements: list[str] = field(default_factory=list)
    active_assets: list[str] = field(default_factory=list)
    recent_decisions: list[str] = field(default_factory=list)
    relevant_relationships: list[str] = field(default_factory=list)
    financial_commitments: list[dict[str, Any]] = field(default_factory=list)
    health_concerns: list[str] = field(default_factory=list)
    learning_paths: list[str] = field(default_factory=list)
    operations_issues: list[str] = field(default_factory=list)
    knowledge_items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != 'snapshot_id'}


@dataclass
class AttentionSignal:
    """What matters right now — a single prioritized signal."""
    signal_id: str = field(default_factory=_uid)
    timestamp: str = field(default_factory=_now_iso)
    owner_id: str = ""
    priority: float = 0.0  # 0.0 - 1.0
    signal_type: str = ""
    description: str = ""
    source_ucp: str = ""
    source_id: str = ""
    recommendation: str = ""
    requires_action: bool = False
    can_automate: bool = False
    can_delegate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"signal_id": self.signal_id, "timestamp": self.timestamp,
                "priority": self.priority, "signal_type": self.signal_type,
                "description": self.description, "source_ucp": self.source_ucp,
                "recommendation": self.recommendation,
                "requires_action": self.requires_action,
                "can_automate": self.can_automate, "can_delegate": self.can_delegate}


@dataclass
class ExecutableRecommendation:
    """A recommendation that can be executed."""
    rec_id: str = field(default_factory=_uid)
    timestamp: str = field(default_factory=_now_iso)
    title: str = ""
    description: str = ""
    reasoning: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    expected_impact: str = ""
    execution_type: str = ""  # communicate, generate, schedule, remind, automate, approve
    can_execute: bool = False
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


@dataclass
class MemoryRecord:
    """A single memory entry — short or long term."""
    memory_id: str = field(default_factory=_uid)
    timestamp: str = field(default_factory=_now_iso)
    owner_id: str = ""
    memory_type: str = "short_term"  # short_term, long_term, organizational
    content: str = ""
    source: str = ""
    tags: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    importance: float = 0.5  # 0.0 - 1.0
    access_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__