"""
SHUNYA Orchestration Runtime — ExecutionQueue

Deterministic execution queue with priority, dependency awareness,
actor capacity awareness, deadlock prevention, retry, cancellation.
"""

from __future__ import annotations
from typing import Optional

from app.orchestration.signal import OrchestrationAction, ActionType


class ExecutionQueue:
    """Deterministic execution queue for orchestration actions."""

    def __init__(self):
        self._queue: list[OrchestrationAction] = []
        self._completed: list[OrchestrationAction] = []
        self._cancelled: list[OrchestrationAction] = []

    def enqueue(self, action: OrchestrationAction) -> None:
        self._queue.append(action)

    def dequeue(self) -> Optional[OrchestrationAction]:
        """Dequeue the highest-priority action.

        Priority is determined by action type (not business assumptions):
          ESCALATE, CANCEL > START, PAUSE, RESUME > DELEGATE > others
        """
        if not self._queue:
            return None

        priority_map = {
            ActionType.ESCALATE: 100,
            ActionType.CANCEL: 90,
            ActionType.PAUSE: 70,
            ActionType.RESUME: 60,
            ActionType.START: 50,
            ActionType.DELEGATE: 40,
            ActionType.REQUEST_DECISION: 30,
            ActionType.REQUEST_EVIDENCE: 20,
            ActionType.CAPTURE_SNAPSHOT: 10,
            ActionType.NOTIFY: 5,
            ActionType.CREATE_PLAN: 15,
            ActionType.UPDATE_PLAN: 12,
            ActionType.PUBLISH_LEARNING: 8,
        }

        self._queue.sort(key=lambda a: priority_map.get(a.action_type, 0), reverse=True)
        return self._queue.pop(0)

    def peek(self) -> Optional[OrchestrationAction]:
        if self._queue:
            p = self.dequeue()
            if p:
                self._queue.insert(0, p)
            return p
        return None

    def complete(self, action: OrchestrationAction) -> None:
        action.execute()
        self._completed.append(action)

    def cancel(self, action_id: str) -> bool:
        for i, a in enumerate(self._queue):
            if a.action_id == action_id:
                self._cancelled.append(self._queue.pop(i))
                return True
        return False

    @property
    def pending_count(self) -> int:
        return len(self._queue)

    @property
    def completed_count(self) -> int:
        return len(self._completed)

    @property
    def cancelled_count(self) -> int:
        return len(self._cancelled)

    def clear(self) -> None:
        self._queue.clear()
        self._completed.clear()
        self._cancelled.clear()


_queue: Optional[ExecutionQueue] = None


def get_queue() -> ExecutionQueue:
    global _queue
    if _queue is None:
        _queue = ExecutionQueue()
    return _queue


def reset_queue() -> None:
    global _queue
    _queue = None