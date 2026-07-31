"""SHUNYA — Collaboration & Multi-user models (Milestone IX).

All collaboration entities are derived intelligence — never canonical state.
WorkspaceSession never stores business truth.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================================================
# Enums
# =========================================================================

class AssignmentRole(str, Enum):
    RESPONSIBLE = "responsible"
    SUPPORTING = "supporting"
    APPROVER = "approver"
    OBSERVER = "observer"
    EXECUTIVE_SPONSOR = "executive_sponsor"
    ESCALATION_OWNER = "escalation_owner"


class ActivityEventType(str, Enum):
    VIEWED = "viewed"
    EDITED = "edited"
    COMMENTED = "commented"
    EVIDENCE_ADDED = "evidence_added"
    PREDICTION_UPDATED = "prediction_updated"
    DECISION_APPROVED = "decision_approved"
    EXECUTION_CHANGED = "execution_changed"
    LEARNING_GENERATED = "learning_generated"
    EXECUTIVE_ATTENTION_CHANGED = "executive_attention_changed"
    ASSIGNMENT_CHANGED = "assignment_changed"
    PRESENCE_CHANGED = "presence_changed"


class ConflictType(str, Enum):
    CONCURRENT_EDIT = "concurrent_edit"
    APPROVAL_CONFLICT = "approval_conflict"
    EXECUTION_CONFLICT = "execution_conflict"
    DECISION_CONFLICT = "decision_conflict"
    EVIDENCE_CONFLICT = "evidence_conflict"


class VoteValue(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    REQUEST_CHANGES = "request_changes"


class UserRole(str, Enum):
    EXECUTIVE = "executive"
    MANAGER = "manager"
    OPERATOR = "operator"
    FINANCE = "finance"
    SALES = "sales"
    OPERATIONS = "operations"
    GUEST = "guest"


# =========================================================================
# 1. Presence
# =========================================================================

@dataclass
class PresenceEntry:
    """Who is currently viewing or editing an object."""
    user_id: int = 0
    user_name: str = ""
    user_role: str = ""
    object_type: str = ""
    object_id: str = ""
    action: str = "viewing"          # viewing, editing
    session_id: str = ""
    last_seen: str = ""

    def __post_init__(self) -> None:
        if not self.last_seen:
            self.last_seen = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id, "user_name": self.user_name,
            "user_role": self.user_role, "action": self.action,
            "object_type": self.object_type, "object_id": self.object_id[:12],
            "last_seen": self.last_seen,
        }


# =========================================================================
# 2. Workspace Session
# =========================================================================

@dataclass
class WorkspaceSession:
    """Temporary UI state — never stores business truth."""
    session_id: str = ""
    user_id: int = 0
    focused_object_type: str = ""
    focused_object_id: str = ""
    conversation_position: int = 0
    attention_layer: str = "executive"
    executive_mode: str = "brief"
    pinned_objects: List[str] = field(default_factory=list)
    navigation_history: List[str] = field(default_factory=list)
    created_at: str = ""
    last_active: str = ""

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if not self.session_id:
            raw = f"ws:{self.user_id}:{now}"
            self.session_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = now
        if not self.last_active:
            self.last_active = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id[:12], "user_id": self.user_id,
            "focused_object": f"{self.focused_object_type}/{self.focused_object_id}",
            "executive_mode": self.executive_mode,
            "attention_layer": self.attention_layer,
            "pinned_count": len(self.pinned_objects),
            "nav_history_depth": len(self.navigation_history),
            "last_active": self.last_active,
        }


# =========================================================================
# 3. Role Definition
# =========================================================================

@dataclass
class RoleDefinition:
    """Runtime role definition — permissions derive from Governance."""
    role: str = UserRole.OPERATOR.value
    can_view_all_objects: bool = False
    can_edit_objects: bool = False
    can_approve_decisions: bool = False
    can_assign_users: bool = False
    can_escalate: bool = False
    can_view_executive: bool = False
    max_priority_visibility: int = 10

    def can_view(self, object_type: str, object_state: str = "") -> bool:
        if self.can_view_all_objects:
            return True
        if self.role == UserRole.EXECUTIVE.value:
            return True
        return False


# =========================================================================
# 4. Conversation Message
# =========================================================================

@dataclass
class ConversationMessage:
    """A message in shared conversation — organizational memory."""
    message_id: str = ""
    object_type: str = ""
    object_id: str = ""
    user_id: int = 0
    user_name: str = ""
    text: str = ""
    linked_evidence: List[str] = field(default_factory=list)
    linked_reasoning: List[str] = field(default_factory=list)
    linked_decision: str = ""
    linked_prediction: str = ""
    linked_commitment: str = ""
    linked_execution: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.message_id:
            raw = f"msg:{self.object_type}:{self.object_id}:{self.user_id}:{datetime.now(timezone.utc).isoformat()}"
            self.message_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id[:12], "user_name": self.user_name,
            "text": self.text[:80], "created_at": self.created_at,
            "has_evidence": len(self.linked_evidence) > 0,
            "has_reasoning": len(self.linked_reasoning) > 0,
        }


# =========================================================================
# 5. Decision Collaboration
# =========================================================================

@dataclass
class DecisionVote:
    """A single vote in a decision discussion."""
    user_id: int = 0
    user_name: str = ""
    vote: str = VoteValue.ABSTAIN.value
    rationale: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_name": self.user_name, "vote": self.vote,
            "rationale": self.rationale[:40],
        }


@dataclass
class DecisionDiscussion:
    """A structured discussion around a decision."""
    discussion_id: str = ""
    decision_id: str = ""
    tenant_id: int = 0
    title: str = ""
    alternatives: List[str] = field(default_factory=list)
    tradeoffs: List[str] = field(default_factory=list)
    votes: List[DecisionVote] = field(default_factory=list)
    objections: List[str] = field(default_factory=list)
    resolution: str = ""
    resolved: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.discussion_id and self.decision_id:
            raw = f"dd:{self.decision_id}:{self.tenant_id}"
            self.discussion_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discussion_id": self.discussion_id[:12],
            "decision_id": self.decision_id[:12],
            "vote_count": len(self.votes), "resolved": self.resolved,
            "resolution": self.resolution[:40] if self.resolution else "",
            "objection_count": len(self.objections),
        }


# =========================================================================
# 6. Assignment
# =========================================================================

@dataclass
class Assignment:
    """An assignment attached to a BusinessExecutionInstance."""
    assignment_id: str = ""
    object_type: str = ""
    object_id: str = ""
    tenant_id: int = 0
    user_id: int = 0
    user_name: str = ""
    role: str = AssignmentRole.RESPONSIBLE.value
    assigned_by: str = ""
    created_at: str = ""
    active: bool = True

    def __post_init__(self) -> None:
        if not self.assignment_id:
            raw = f"asgn:{self.object_type}:{self.object_id}:{self.user_id}:{self.role}"
            self.assignment_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assignment_id": self.assignment_id[:12],
            "object_id": self.object_id[:12], "user_name": self.user_name,
            "role": self.role, "active": self.active,
        }


# =========================================================================
# 7. Activity Event
# =========================================================================

@dataclass
class ActivityEvent:
    """An immutable activity event on an object."""
    event_id: str = ""
    object_type: str = ""
    object_id: str = ""
    user_id: int = 0
    user_name: str = ""
    event_type: str = ActivityEventType.VIEWED.value
    detail: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.event_id:
            raw = f"aev:{self.object_type}:{self.object_id}:{self.event_type}:{datetime.now(timezone.utc).isoformat()}"
            self.event_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id[:12], "user_name": self.user_name,
            "event_type": self.event_type, "detail": self.detail[:60],
            "created_at": self.created_at,
        }


# =========================================================================
# 8. Collaboration Event (live updates)
# =========================================================================

@dataclass
class CollaborationEvent:
    """A runtime event for live collaboration updates."""
    event_id: str = ""
    event_type: str = ""           # presence, comment, assignment, approval, focus, executive_update
    object_type: str = ""
    object_id: str = ""
    user_id: int = 0
    user_name: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.event_id:
            raw = f"ce:{self.event_type}:{self.object_type}:{self.object_id}:{datetime.now(timezone.utc).isoformat()}"
            self.event_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id[:12], "event_type": self.event_type,
            "user_name": self.user_name,
            "object": f"{self.object_type}/{self.object_id[:12]}",
        }


# =========================================================================
# 9. Conflict Record
# =========================================================================

@dataclass
class ConflictRecord:
    """A deterministic conflict resolution record."""
    conflict_id: str = ""
    conflict_type: str = ConflictType.CONCURRENT_EDIT.value
    object_type: str = ""
    object_id: str = ""
    user_ids: List[int] = field(default_factory=list)
    description: str = ""
    resolution: str = ""
    resolved: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.conflict_id:
            raw = f"conf:{self.object_type}:{self.object_id}:{datetime.now(timezone.utc).isoformat()}"
            self.conflict_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id[:12],
            "conflict_type": self.conflict_type,
            "object_id": self.object_id[:12],
            "resolved": self.resolved,
            "resolution": self.resolution[:60],
        }


# =========================================================================
# 10. Runtime Types
# =========================================================================

@dataclass
class CollaborationConfig:
    """Configuration for the Collaboration Runtime."""
    presence_timeout_seconds: int = 60
    max_history_depth: int = 50
    enable_live_updates: bool = True
    conflict_auto_resolve: bool = True
    version: str = "mi9.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "presence_timeout_seconds": self.presence_timeout_seconds,
            "enable_live_updates": self.enable_live_updates,
            "version": self.version,
        }


@dataclass
class CollaborationFilter:
    """Filter for querying collaboration data."""
    object_type: Optional[str] = None
    object_id: Optional[str] = None
    user_id: Optional[int] = None
    limit: int = 50


@dataclass
class CollaborationStats:
    """Collaboration runtime statistics."""
    active_sessions: int = 0
    total_messages: int = 0
    total_assignments: int = 0
    total_decisions: int = 0
    total_events: int = 0
    total_conflicts: int = 0
    resolved_conflicts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_sessions": self.active_sessions,
            "total_messages": self.total_messages,
            "total_assignments": self.total_assignments,
            "total_decisions": self.total_decisions,
            "total_events": self.total_events,
            "total_conflicts": self.total_conflicts,
            "resolved_conflicts": self.resolved_conflicts,
        }