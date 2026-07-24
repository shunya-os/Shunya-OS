"""
SHUNYA Orchestration Runtime — OrchestrationCycle

Each orchestration cycle performs:
  Observe runtime signals → Detect changes → Evaluate all runtimes →
  Publish next actions → Repeat.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.orchestration.signal import (
    SignalBus, Trigger, RuntimeSignal, OrchestrationAction, ActionType, TriggerEvent,
    get_bus,
)
from app.orchestration.queue import get_queue, ExecutionQueue


@dataclass
class OrchestrationCycle:
    """A single orchestration cycle. Immutable after completion."""

    cycle_id: str
    started_at: str
    completed_at: Optional[str] = None
    signals_processed: int = 0
    triggers_evaluated: int = 0
    actions_produced: int = 0
    actions_queued: int = 0
    duration_ms: float = 0.0
    status: str = "running"

    def to_dict(self) -> dict:
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "signals_processed": self.signals_processed,
            "triggers_evaluated": self.triggers_evaluated,
            "actions_produced": self.actions_produced,
            "actions_queued": self.actions_queued,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
        }


class OrchestratorEngine:
    """The core orchestration engine.

    Continuously evaluates runtime signals and produces actions.
    No runtime directly controls another runtime. The Orchestrator
    evaluates state changes and determines what should happen next.
    """

    def __init__(self):
        self._triggers: list[Trigger] = []
        self._cycles: list[OrchestrationCycle] = []
        self._actions: list[OrchestrationAction] = []
        self._counter: int = 0

    def register_trigger(self, trigger: Trigger) -> None:
        self._triggers.append(trigger)
        self._triggers.sort(key=lambda t: t.priority, reverse=True)

    def execute_cycle(self, signal_bus: SignalBus = None) -> OrchestrationCycle:
        """Execute one orchestration cycle."""
        import time
        bus = signal_bus or get_bus()
        start = time.time()
        self._counter += 1

        cycle = OrchestrationCycle(
            cycle_id=f"cycle_{self._counter}",
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # 1. Observe signals
        signals = bus.get_signals(limit=100)
        cycle.signals_processed = len(signals)

        # 2. Evaluate triggers against signals
        actions_produced = 0
        for signal in signals:
            for trigger in self._triggers:
                result = trigger.evaluate(signal)
                if result is not None:
                    self._counter += 1
                    action = OrchestrationAction(
                        action_id=f"act_{self._counter}",
                        trigger_id=trigger.trigger_id,
                        action_type=result,
                        signal_id=signal.signal_id,
                        payload=trigger.action_payload,
                    )
                    self._actions.append(action)
                    actions_produced += 1
                    # Queue the action
                    get_queue().enqueue(action)

        cycle.actions_produced = actions_produced
        cycle.actions_queued = actions_produced
        cycle.triggers_evaluated = len(self._triggers) * len(signals)

        # 3. Complete
        duration = (time.time() - start) * 1000
        cycle.duration_ms = duration
        cycle.completed_at = datetime.now(timezone.utc).isoformat()
        cycle.status = "completed"
        self._cycles.append(cycle)

        return cycle

    def get_cycles(self, limit: int = 20) -> list[OrchestrationCycle]:
        return self._cycles[-limit:]

    def get_actions(self, limit: int = 20) -> list[OrchestrationAction]:
        return self._actions[-limit:]

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)

    @property
    def action_count(self) -> int:
        return len(self._actions)

    @property
    def trigger_count(self) -> int:
        return len(self._triggers)

    def clear(self) -> None:
        self._triggers.clear()
        self._cycles.clear()
        self._actions.clear()
        self._counter = 0


_engine: Optional[OrchestratorEngine] = None


def get_engine() -> OrchestratorEngine:
    global _engine
    if _engine is None:
        _engine = OrchestratorEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None