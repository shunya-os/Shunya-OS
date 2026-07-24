"""
SHUNYA Orchestration Runtime — SynchronizationPoint

Synchronization points across runtimes.
Planning, Organization, Temporal, Execution, Decision, Learning
all synchronize through orchestration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SynchronizationPoint:
    """A synchronization point across multiple runtimes."""

    sync_id: str
    runtimes: list[str]
    """The runtimes being synchronized: 'planning', 'organization',
       'temporal', 'execution', 'decision', 'learning'"""
    status: str = "pending"
    """'pending', 'syncing', 'completed', 'failed'"""
    created_at: str = ""
    completed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def complete(self) -> None:
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "sync_id": self.sync_id,
            "runtimes": self.runtimes,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class SyncManager:
    """Manages synchronization points across runtimes."""

    def __init__(self):
        self._points: list[SynchronizationPoint] = []
        self._counter: int = 0

    def create_sync(self, runtimes: list[str]) -> SynchronizationPoint:
        self._counter += 1
        sp = SynchronizationPoint(
            sync_id=f"sync_{self._counter}",
            runtimes=runtimes,
        )
        self._points.append(sp)
        return sp

    def complete_sync(self, sync_id: str) -> None:
        for sp in self._points:
            if sp.sync_id == sync_id:
                sp.complete()
                break

    def get_pending(self) -> list[SynchronizationPoint]:
        return [s for s in self._points if s.status == "pending"]

    def get_all(self, limit: int = 20) -> list[SynchronizationPoint]:
        return self._points[-limit:]

    @property
    def count(self) -> int:
        return len(self._points)

    def clear(self) -> None:
        self._points.clear()
        self._counter = 0


_manager: Optional[SyncManager] = None


def get_manager() -> SyncManager:
    global _manager
    if _manager is None:
        _manager = SyncManager()
    return _manager


def reset_manager() -> None:
    global _manager
    _manager = None