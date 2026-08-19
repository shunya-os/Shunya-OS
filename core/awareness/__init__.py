"""
SHUNYA — Canonical Awareness Model.

Gate 3.1: The authoritative pipeline for turning real events into
governed user-facing awareness.

Pipeline:
    EVENT / CHANGE
        ↓
    CANONICAL EVENT
        ↓
    OBSERVATION / INTELLIGENCE
        ↓
    SIGNAL
        ↓
    RELEVANCE / PRIORITY
        ↓
    DEDUP / SUPPRESSION / COALESCING
        ↓
    ATTENTION
        ↓
    USER-FACING AWARENESS
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════
# Signal Types — business-agnostic categories
# ═══════════════════════════════════════════════════════════════════


class SignalType(str, Enum):
    CHANGE = "change"                   # Something important changed
    ATTENTION = "attention"             # Something needs attention
    RISK = "risk"                       # Risk is increasing
    COMMITMENT = "commitment"           # Commitment approaching
    OPPORTUNITY = "opportunity"         # Opportunity detected
    INFORMATION = "information"         # New relevant information
    PATTERN = "pattern"                 # Unusual pattern detected
    CONFLICT = "conflict"               # Conflicting information
    OVERDUE = "overdue"                 # Overdue responsibility
    BLOCKED = "blocked"                 # Execution blocked
    EXTERNAL = "external"               # External development relevant


# ═══════════════════════════════════════════════════════════════════
# Priority
# ═══════════════════════════════════════════════════════════════════


class SignalPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


# ═══════════════════════════════════════════════════════════════════
# Signal Lifecycle
# ═══════════════════════════════════════════════════════════════════


class SignalStatus(str, Enum):
    ACTIVE = "active"           # Visible and relevant
    ACKNOWLEDGED = "acknowledged"  # User has seen/acknowledged
    DISMISSED = "dismissed"     # User dismissed
    SNOOZED = "snoozed"         # Temporarily hidden
    EXPIRED = "expired"         # No longer relevant
    RESOLVED = "resolved"       # Underlying issue resolved


# ═══════════════════════════════════════════════════════════════════
# AwarenessSignal — the canonical awareness item
# ═══════════════════════════════════════════════════════════════════


@dataclass
class AwarenessSignal:
    """A single governed awareness item.

    Every signal has a reason, evidence, source, timestamp, affected
    object, priority, confidence, knowledge status, and suggested action.
    """
    signal_id: str = ""
    signal_type: SignalType = SignalType.ATTENTION
    title: str = ""
    description: str = ""
    reason: str = ""

    # Evidence and source
    source_event_id: str = ""
    source_type: str = ""            # "canonical_event" | "intelligence" | "external" | "system"
    evidence: list[dict] = field(default_factory=list)

    # Context
    affected_object_id: str = ""
    affected_object_type: str = ""
    tenant_id: int = 0

    # Priority
    priority: SignalPriority = SignalPriority.NORMAL
    relevance_score: float = 0.5     # [0, 1]
    confidence: Optional[float] = None

    # Knowledge classification
    knowledge_status: str = "inference"  # "fact" | "inference" | "unknown"

    # Lifecycle
    status: SignalStatus = SignalStatus.ACTIVE
    suggested_action: str = ""
    suggested_action_payload: dict = field(default_factory=dict)

    # Timestamps
    created_at: str = ""
    expires_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    snoozed_until: Optional[str] = None

    # Dedup
    dedup_key: str = ""

    def __post_init__(self) -> None:
        import uuid
        if not self.signal_id:
            self.signal_id = f"sig_{uuid.uuid4().hex[:16]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.dedup_key:
            self.dedup_key = f"{self.signal_type.value}:{self.affected_object_id}:{self.title[:50]}"


# ═══════════════════════════════════════════════════════════════════
# AwarenessState — snapshot of current awareness
# ═══════════════════════════════════════════════════════════════════


@dataclass
class AwarenessState:
    """Current awareness state — what matters right now."""
    signals: list[AwarenessSignal] = field(default_factory=list)
    total_count: int = 0
    active_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    normal_count: int = 0
    calm: bool = True               # True when nothing important is happening
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()


__all__ = [
    "SignalType",
    "SignalPriority",
    "SignalStatus",
    "AwarenessSignal",
    "AwarenessState",
]