"""
SHUNYA Execution Engine — Action Execution, Delegation, and Monitoring

Executes actions, manages delegations, tracks progress, and monitors outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


class ExecutionStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Execution:
    execution_id: str
    action: str
    params: dict = field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None


class ExecutionEngine(Engine):
    """Canonical execution engine for action execution and monitoring."""

    engine_id: str = "execution"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._executions: dict[str, Execution] = {}
        self._handlers: dict[str, callable] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._executions.clear()
        self._handlers.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={"initialized": self._initialized, "active_executions": len(self._executions)},
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return ["execution.action.execute", "execution.progress.track", "execution.handler.register"]

    def register_handler(self, action: str, handler: callable) -> None:
        self._handlers[action] = handler

    def execute(self, action: str, params: dict | None = None) -> Execution:
        exec_id = f"exec-{len(self._executions) + 1}"
        execution = Execution(execution_id=exec_id, action=action, params=params or {})
        self._executions[exec_id] = execution

        handler = self._handlers.get(action)
        if handler:
            execution.status = ExecutionStatus.RUNNING
            try:
                result = handler(execution.params)
                execution.status = ExecutionStatus.COMPLETED
                execution.result = result
            except Exception as e:
                execution.status = ExecutionStatus.FAILED
                execution.error = str(e)
        execution.completed_at = datetime.now(timezone.utc)
        return execution

    def get(self, execution_id: str) -> Optional[Execution]:
        return self._executions.get(execution_id)

    def list(self) -> list[Execution]:
        return list(self._executions.values())

    def get_active(self) -> list[Execution]:
        return [e for e in self._executions.values() if e.status in (ExecutionStatus.QUEUED, ExecutionStatus.RUNNING)]