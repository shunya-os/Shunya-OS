"""
SHUNYA Autonomous Organization Runtime — Actor Model

Everything that performs work is an Actor.
Humans, AI, Teams, Departments, Vendors, Suppliers, Customers,
Robots, APIs, Government Agencies, Autonomous Agents — all are Actors.

Never hardcode "employee." Never hardcode "manager."
Never hardcode "salesperson."
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class CapacityStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    OVERLOADED = "overloaded"
    IDLE = "idle"


@dataclass
class ActorCapability:
    """A capability an actor possesses. Business agnostic."""

    capability_id: str
    name: str
    description: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class Actor:
    """A universal actor. Everything that performs work.

    Never hardcode actor types. The actor_type field is a string
    that can represent any kind of actor: 'human', 'ai_agent',
    'team', 'department', 'vendor', 'api', 'robot', etc.
    """

    actor_id: str
    name: str
    actor_type: str = "human"
    """Never hardcode specific types. Always a generic string."""

    capabilities: list[ActorCapability] = field(default_factory=list)
    capacity_status: CapacityStatus = CapacityStatus.AVAILABLE
    max_concurrent_responsibilities: int = 5
    current_responsibilities: int = 0
    metadata: dict = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self._recompute_capacity()

    @property
    def capacity_ratio(self) -> float:
        """0.0 = idle, 1.0 = fully loaded."""
        if self.max_concurrent_responsibilities == 0:
            return 1.0
        return min(1.0, self.current_responsibilities / self.max_concurrent_responsibilities)

    @property
    def can_accept_responsibility(self) -> bool:
        return self.current_responsibilities < self.max_concurrent_responsibilities and \
               self.capacity_status not in (CapacityStatus.BLOCKED, CapacityStatus.UNAVAILABLE, CapacityStatus.OVERLOADED)

    def assign_responsibility(self) -> None:
        self.current_responsibilities += 1
        self._recompute_capacity()

    def release_responsibility(self) -> None:
        self.current_responsibilities = max(0, self.current_responsibilities - 1)
        self._recompute_capacity()

    def _recompute_capacity(self) -> None:
        """Dynamically compute capacity status from current load."""
        ratio = self.capacity_ratio
        if ratio >= 1.0:
            self.capacity_status = CapacityStatus.OVERLOADED
        elif ratio >= 0.8:
            self.capacity_status = CapacityStatus.BUSY
        elif ratio >= 0.01:
            self.capacity_status = CapacityStatus.AVAILABLE
        else:
            self.capacity_status = CapacityStatus.IDLE

    def to_dict(self) -> dict:
        return {
            "actor_id": self.actor_id,
            "name": self.name,
            "actor_type": self.actor_type,
            "capabilities": [c.name for c in self.capabilities],
            "capacity_status": self.capacity_status.value,
            "capacity_ratio": self.capacity_ratio,
            "current_responsibilities": self.current_responsibilities,
            "max_concurrent": self.max_concurrent_responsibilities,
            "can_accept": self.can_accept_responsibility,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class ActorStore:
    def __init__(self):
        self._actors: dict[str, Actor] = {}

    def add(self, actor: Actor) -> None:
        self._actors[actor.actor_id] = actor

    def get(self, actor_id: str) -> Optional[Actor]:
        return self._actors.get(actor_id)

    def get_by_type(self, actor_type: str) -> list[Actor]:
        return [a for a in self._actors.values() if a.actor_type == actor_type]

    def get_available(self) -> list[Actor]:
        return [a for a in self._actors.values() if a.can_accept_responsibility]

    @property
    def count(self) -> int:
        return len(self._actors)

    def clear(self) -> None:
        self._actors.clear()


_store: Optional[ActorStore] = None


def get_store() -> ActorStore:
    global _store
    if _store is None:
        _store = ActorStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None