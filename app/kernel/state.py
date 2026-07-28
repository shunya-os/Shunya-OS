"""SHUNYA Kernel — Universal State Machine.

Implements the universal object lifecycle defined in:
    COGNITIVE_WORKSPACE_RUNTIME.md §6 — Universal Object Lifecycle
    UNIVERSAL_ONTOLOGY.md §11 — State

Every Object follows exactly one lifecycle. The lifecycle is governed
by the TypeRegistry which provides per-type-group transition validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from app.kernel.types import LifecycleState, get_registry


# ---------------------------------------------------------------------------
# State transition event
# ---------------------------------------------------------------------------

@dataclass
class StateTransition:
    """A recorded state transition.

    Attributes:
        object_id: The object that transitioned
        from_state: The previous state
        to_state: The new state
        timestamp: When the transition occurred
        actor: Who or what triggered the transition
        reason: Why the transition occurred
    """
    object_id: str
    from_state: LifecycleState
    to_state: LifecycleState
    timestamp: datetime
    actor: str = "system"
    reason: str = ""


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class StateMachine:
    """Universal state machine for all objects.

    Every Object uses exactly one StateMachine instance. The machine
    validates transitions against the type's registered lifecycle.

    Constitutional invariants enforced:
        O-01: Identity never changes (object_id is immutable)
        O-12: State transitions are valid
        O-18: State is singular (one state at a time)
        I-13: Object lifecycle is event-sourced (every transition emits an event)
    """

    def __init__(self, object_id: str, object_type: str):
        self._object_id = object_id
        self._object_type = object_type
        self._current_state: LifecycleState = LifecycleState.CREATE
        self._history: List[StateTransition] = []
        self._observers: List[callable] = []

    @property
    def current_state(self) -> LifecycleState:
        """The current state of the object (O-18: singular)."""
        return self._current_state

    @property
    def history(self) -> List[StateTransition]:
        """Immutable transition history (O-12: valid transitions)."""
        return list(self._history)

    @property
    def is_terminal(self) -> bool:
        """Whether the current state is terminal (absorbing)."""
        registry = get_registry()
        return registry.is_terminal(self._current_state)

    def can_transition_to(self, state: LifecycleState) -> bool:
        """Check if a transition to the given state is valid."""
        registry = get_registry()
        return registry.validate_transition(
            self._object_type, self._current_state, state
        )

    def transition(
        self,
        to_state: LifecycleState,
        actor: str = "system",
        reason: str = "",
    ) -> StateTransition:
        """Execute a state transition.

        Args:
            to_state: The target state
            actor: Who or what triggered the transition
            reason: Why the transition occurred

        Returns:
            The recorded StateTransition

        Raises:
            ValueError: If the transition is invalid
            RuntimeError: If the current state is terminal
        """
        if self.is_terminal:
            raise RuntimeError(
                f"Cannot transition from terminal state '{self._current_state.value}' "
                f"for object '{self._object_id}'"
            )

        if not self.can_transition_to(to_state):
            registry = get_registry()
            allowed = registry.get_lifecycle(self._object_type)
            valid_targets = (
                allowed.transitions.get(self._current_state, [])
                if allowed else []
            )
            raise ValueError(
                f"Invalid transition: '{self._current_state.value}' → "
                f"'{to_state.value}' for type '{self._object_type}'. "
                f"Allowed targets: {[s.value for s in valid_targets]}"
            )

        transition = StateTransition(
            object_id=self._object_id,
            from_state=self._current_state,
            to_state=to_state,
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            reason=reason,
        )

        self._history.append(transition)
        self._current_state = to_state

        # Notify observers (I-13: event-sourced)
        for observer in self._observers:
            try:
                observer(transition)
            except Exception:
                pass  # Observer failures must not break state consistency

        return transition

    def observe(self, callback: callable) -> None:
        """Register a transition observer.

        The callback receives a StateTransition on every transition.
        Observers must not raise exceptions.
        """
        self._observers.append(callback)

    def reset(self, state: LifecycleState = LifecycleState.CREATE) -> None:
        """Reset the state machine (for testing only)."""
        self._current_state = state
        self._history = []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the state machine for projection."""
        return {
            "object_id": self._object_id,
            "current_state": self._current_state.value,
            "is_terminal": self.is_terminal,
            "history_count": len(self._history),
            "history": [
                {
                    "from_state": t.from_state.value,
                    "to_state": t.to_state.value,
                    "timestamp": t.timestamp.isoformat(),
                    "actor": t.actor,
                    "reason": t.reason,
                }
                for t in self._history[-10:]  # Last 10 for projection
            ],
        }