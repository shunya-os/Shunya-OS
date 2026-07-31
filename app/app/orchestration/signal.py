"""
SHUNYA Orchestration Runtime — RuntimeSignal, Trigger, Condition, Action

Every runtime publishes state. The Orchestrator detects changes
via signals and triggers. Triggers evaluate conditions and produce actions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Callable


class TriggerEvent(Enum):
    DECISION_APPROVED = "decision_approved"
    EVIDENCE_RECEIVED = "evidence_received"
    EXECUTION_COMPLETED = "execution_completed"
    CHECKPOINT_FAILED = "checkpoint_failed"
    HEALTH_DECLINED = "health_declined"
    CAPACITY_CHANGED = "capacity_changed"
    RISK_INCREASED = "risk_increased"
    FORECAST_CHANGED = "forecast_changed"
    PLAN_UPDATED = "plan_updated"
    OBJECTIVE_ACTIVATED = "objective_activated"
    MILESTONE_COMPLETED = "milestone_completed"
    DELEGATION_ACCEPTED = "delegation_accepted"
    ESCALATION_TRIGGERED = "escalation_triggered"
    SNAPSHOT_CAPTURED = "snapshot_captured"


class ActionType(Enum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    REQUEST_EVIDENCE = "request_evidence"
    REQUEST_DECISION = "request_decision"
    CREATE_PLAN = "create_plan"
    UPDATE_PLAN = "update_plan"
    CAPTURE_SNAPSHOT = "capture_snapshot"
    PUBLISH_LEARNING = "publish_learning"
    NOTIFY = "notify"


@dataclass
class RuntimeSignal:
    """A signal emitted by a runtime, carrying state change information."""

    signal_id: str
    source_runtime: str
    """'decision', 'execution', 'organization', 'temporal', 'planning', 'cortex'"""
    trigger_event: TriggerEvent
    payload: dict = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "source_runtime": self.source_runtime,
            "trigger_event": self.trigger_event.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class Trigger:
    """A trigger watches for specific signals and evaluates conditions."""

    trigger_id: str
    trigger_event: TriggerEvent
    condition_fn: Optional[Callable] = None
    """(signal, runtime_state) -> bool. If True, the action is produced."""
    action_type: ActionType = ActionType.NOTIFY
    action_payload: dict = field(default_factory=dict)
    priority: int = 0
    metadata: dict = field(default_factory=dict)

    def evaluate(self, signal: RuntimeSignal, runtime_state: dict = None) -> Optional[ActionType]:
        if signal.trigger_event != self.trigger_event:
            return None
        if self.condition_fn:
            if not self.condition_fn(signal, runtime_state or {}):
                return None
        return self.action_type


@dataclass
class OrchestrationAction:
    """An action produced by the orchestration loop."""

    action_id: str
    trigger_id: str
    action_type: ActionType
    signal_id: str
    target_runtime: str = ""
    payload: dict = field(default_factory=dict)
    created_at: str = ""
    is_executed: bool = False
    executed_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def execute(self) -> None:
        self.is_executed = True
        self.executed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "trigger_id": self.trigger_id,
            "action_type": self.action_type.value,
            "signal_id": self.signal_id,
            "target_runtime": self.target_runtime,
            "payload": self.payload,
            "created_at": self.created_at,
            "is_executed": self.is_executed,
            "executed_at": self.executed_at,
        }


class SignalBus:
    """Publish-subscribe signal bus for runtime signals."""

    def __init__(self):
        self._signals: list[RuntimeSignal] = []
        self._counter: int = 0

    def publish(self, source: str, event: TriggerEvent, payload: dict = None) -> RuntimeSignal:
        self._counter += 1
        signal = RuntimeSignal(
            signal_id=f"sig_{self._counter}",
            source_runtime=source,
            trigger_event=event,
            payload=payload or {},
        )
        self._signals.append(signal)
        return signal

    def get_signals(self, limit: int = 50) -> list[RuntimeSignal]:
        return self._signals[-limit:]

    @property
    def count(self) -> int:
        return len(self._signals)

    def clear(self) -> None:
        self._signals.clear()
        self._counter = 0


_bus: Optional[SignalBus] = None


def get_bus() -> SignalBus:
    global _bus
    if _bus is None:
        _bus = SignalBus()
    return _bus


def reset_bus() -> None:
    global _bus
    _bus = None