"""SHUNYA — Identity lifecycle (Phase D).

GATE 2.1 CONSOLIDATION: QUARANTINED — Duplicate of canonical
kernel Identity contract. Kept for backward compatibility only.

Architectural authority: ES-010 (superseded by Gate 2.1)
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.shunya.identity.models import Identity, IdentityStatus


class InvalidTransitionError(Exception):
    """Raised when an invalid lifecycle transition is attempted."""


class LifecycleEngine:
    """Manages identity lifecycle transitions.

    States:
        ACTIVE → VERIFIED → SUPERSEDED | MERGED | ARCHIVED
        ACTIVE → SUPERSEDED | MERGED | ARCHIVED
        VERIFIED → SUPERSEDED | MERGED | ARCHIVED
        SUPERSEDED (terminal)
        MERGED (terminal)
        ARCHIVED (terminal)
    """

    _VALID_TRANSITIONS: Dict[str, List[str]] = {
        IdentityStatus.ACTIVE.value: [
            IdentityStatus.VERIFIED.value,
            IdentityStatus.SUPERSEDED.value,
            IdentityStatus.MERGED.value,
            IdentityStatus.ARCHIVED.value,
        ],
        IdentityStatus.VERIFIED.value: [
            IdentityStatus.SUPERSEDED.value,
            IdentityStatus.MERGED.value,
            IdentityStatus.ARCHIVED.value,
        ],
    }

    _TERMINAL_STATES = {
        IdentityStatus.SUPERSEDED.value,
        IdentityStatus.MERGED.value,
        IdentityStatus.ARCHIVED.value,
    }

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def transition(
        self,
        identity: Identity,
        target_status: str,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Identity:
        """Transition an identity to a new status.

        Args:
            identity: The identity to transition.
            target_status: The target status (IdentityStatus value).
            reason: Why the transition is occurring.
            metadata: Optional metadata to attach.

        Returns:
            The updated Identity.

        Raises:
            InvalidTransitionError: If the transition is not allowed.
        """
        with self._lock:
            current = identity.status
            if current in self._TERMINAL_STATES:
                raise InvalidTransitionError(
                    f"Cannot transition from terminal state '{current}' to '{target_status}'"
                )
            allowed = self._VALID_TRANSITIONS.get(current, [])
            if target_status not in allowed:
                raise InvalidTransitionError(
                    f"Invalid transition: '{current}' → '{target_status}'. "
                    f"Allowed: {allowed}"
                )

            identity.status = target_status
            identity.updated_at = datetime.now(timezone.utc)

            if target_status == IdentityStatus.SUPERSEDED.value:
                identity.superseded_at = identity.updated_at
            if metadata:
                identity.metadata.update(metadata)
            if reason:
                identity.metadata["transition_reason"] = reason

            return identity

    def verify(self, identity: Identity, method: str = "automated") -> Identity:
        """Mark an identity as verified."""
        return self.transition(
            identity, IdentityStatus.VERIFIED.value,
            reason=f"Verified via {method}",
            metadata={"verification_method": method},
        )

    def supersede(self, identity: Identity, replacement_id: str) -> Identity:
        """Supersede an identity with a replacement."""
        return self.transition(
            identity, IdentityStatus.SUPERSEDED.value,
            reason=f"Superseded by {replacement_id}",
            metadata={"superseded_by": replacement_id},
        )

    def merge(self, identity: Identity, target_id: str) -> Identity:
        """Merge an identity into another canonical identity."""
        result = self.transition(
            identity, IdentityStatus.MERGED.value,
            reason=f"Merged into {target_id}",
            metadata={"merged_into_id": target_id},
        )
        result.merged_into_id = target_id
        return result

    def archive(self, identity: Identity, reason: str = "Archived") -> Identity:
        """Archive an identity."""
        return self.transition(
            identity, IdentityStatus.ARCHIVED.value,
            reason=reason,
        )

    def is_terminal(self, status: str) -> bool:
        """Check if a status is terminal."""
        return status in self._TERMINAL_STATES

    def can_transition(self, current: str, target: str) -> bool:
        """Check if a transition is allowed without performing it."""
        if current in self._TERMINAL_STATES:
            return False
        allowed = self._VALID_TRANSITIONS.get(current, [])
        return target in allowed