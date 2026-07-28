"""SHUNYA Phase A1A — Space Lifecycle.

Expanded lifecycle with 5 states:
Draft → Active → Dormant → Archived → Historical

Lifecycle affects permissions, visibility, AI attention,
search, retention, and analytics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class LifecycleState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DORMANT = "dormant"
    ARCHIVED = "archived"
    HISTORICAL = "historical"


# Valid transitions
LIFECYCLE_TRANSITIONS: Dict[LifecycleState, List[LifecycleState]] = {
    LifecycleState.DRAFT: [LifecycleState.ACTIVE, LifecycleState.ARCHIVED],
    LifecycleState.ACTIVE: [LifecycleState.DORMANT, LifecycleState.ARCHIVED],
    LifecycleState.DORMANT: [LifecycleState.ACTIVE, LifecycleState.ARCHIVED],
    LifecycleState.ARCHIVED: [LifecycleState.HISTORICAL, LifecycleState.ACTIVE],
    LifecycleState.HISTORICAL: [],
}


# Lifecycle effects on Space behavior
LIFECYCLE_EFFECTS: Dict[LifecycleState, Dict[str, Any]] = {
    LifecycleState.DRAFT: {
        "permissions": "restricted",
        "visibility": "owners_only",
        "ai_attention": "low",
        "search_visible": True,
        "retention": "normal",
        "analytics": "excluded",
        "description": "Space is being set up, not yet operational",
    },
    LifecycleState.ACTIVE: {
        "permissions": "normal",
        "visibility": "normal",
        "ai_attention": "high",
        "search_visible": True,
        "retention": "normal",
        "analytics": "included",
        "description": "Space is operational and actively used",
    },
    LifecycleState.DORMANT: {
        "permissions": "restricted",
        "visibility": "reduced",
        "ai_attention": "low",
        "search_visible": True,
        "retention": "normal",
        "analytics": "excluded",
        "description": "Space is inactive but preserved",
    },
    LifecycleState.ARCHIVED: {
        "permissions": "read_only",
        "visibility": "archived",
        "ai_attention": "none",
        "search_visible": False,
        "retention": "extended",
        "analytics": "excluded",
        "description": "Space is archived for reference",
    },
    LifecycleState.HISTORICAL: {
        "permissions": "read_only",
        "visibility": "historical",
        "ai_attention": "none",
        "search_visible": False,
        "retention": "permanent",
        "analytics": "excluded",
        "description": "Space is preserved as historical record",
    },
}


@dataclass
class SpaceLifecycle:
    """The lifecycle state of a Space.

    Lifecycle replaces the old SpaceStatus simple enum.
    Backward compatible: SpaceStatus.ACTIVE maps to LifecycleState.ACTIVE.
    """
    state: LifecycleState = LifecycleState.DRAFT
    entered_at: str = ""
    """When the current state was entered."""
    previous_state: Optional[LifecycleState] = None
    transitions: List[Dict[str, str]] = field(default_factory=list)
    """History of state transitions."""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.entered_at:
            self.entered_at = datetime.now(timezone.utc).isoformat()

    def can_transition_to(self, target: LifecycleState) -> bool:
        """Check if a transition to the target state is valid."""
        allowed = LIFECYCLE_TRANSITIONS.get(self.state, [])
        return target in allowed

    def transition_to(self, target: LifecycleState) -> "SpaceLifecycle":
        """Transition to a new lifecycle state.

        Returns a new SpaceLifecycle instance (immutable pattern).
        """
        if not self.can_transition_to(target):
            raise ValueError(
                f"Cannot transition from {self.state.value} to {target.value}"
            )
        now = datetime.now(timezone.utc).isoformat()
        transitions = list(self.transitions)
        transitions.append({
            "from": self.state.value,
            "to": target.value,
            "at": now,
        })
        return SpaceLifecycle(
            state=target,
            entered_at=now,
            previous_state=self.state,
            transitions=transitions,
            metadata=self.metadata,
        )

    def effects(self) -> Dict[str, Any]:
        """Get the effects of the current lifecycle state."""
        return LIFECYCLE_EFFECTS.get(self.state, {})

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "entered_at": self.entered_at,
            "previous_state": self.previous_state.value
            if self.previous_state else None,
            "transitions": self.transitions,
            "effects": self.effects(),
        }


# =========================================================================
# Lifecycle Manager
# =========================================================================


class LifecycleManager:
    """Manages Space lifecycle transitions.

    Integrates with the Space store to update lifecycle state.
    """

    def __init__(self, store=None):
        from app.space.store import get_store
        self._store = store or get_store()

    def transition(self, space_id: str,
                   target: LifecycleState) -> Optional[SpaceLifecycle]:
        """Transition a Space to a new lifecycle state."""
        space = self._store.get(space_id)
        if not space:
            return None
        try:
            new_lifecycle = space.lifecycle.transition_to(target)
            space.lifecycle = new_lifecycle
            return new_lifecycle
        except ValueError:
            return None

    def get_valid_transitions(self, space_id: str) -> List[str]:
        """Get valid next states for a Space."""
        space = self._store.get(space_id)
        if not space:
            return []
        allowed = LIFECYCLE_TRANSITIONS.get(space.lifecycle.state, [])
        return [s.value for s in allowed]

    def get_state_effects(self, space_id: str) -> Dict[str, Any]:
        """Get the effects of the current lifecycle state."""
        space = self._store.get(space_id)
        if not space:
            return {}
        return space.lifecycle.effects()


# =========================================================================
# Singleton
# =========================================================================

_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    global _manager
    if _manager is None:
        _manager = LifecycleManager()
    return _manager


def reset_lifecycle_manager() -> None:
    global _manager
    _manager = None