"""
SHUNYA Orchestration Runtime — Bootstrap and Middleware
"""

from flask import request, jsonify
from datetime import datetime, timezone

from app.orchestration.signal import (
    SignalBus, Trigger, TriggerEvent, ActionType, get_bus,
)
from app.orchestration.cycle import OrchestratorEngine, get_engine
from app.orchestration.queue import get_queue
from app.orchestration.sync import get_manager


def register_orchestration_middleware(app) -> None:
    @app.before_request
    def _check_orch_inspect():
        if request.args.get("inspect_orch"):
            return jsonify(_inspect_orch())
        return None


def _inspect_orch() -> dict:
    engine = get_engine()
    bus = get_bus()
    queue = get_queue()
    sync = get_manager()

    return {
        "orchestrator": {
            "cycles": engine.cycle_count,
            "triggers": engine.trigger_count,
            "actions": engine.action_count,
            "recent_cycles": [c.to_dict() for c in engine.get_cycles(5)],
        },
        "signals": {
            "total": bus.count,
            "recent": [s.to_dict() for s in bus.get_signals(10)],
        },
        "queue": {
            "pending": queue.pending_count,
            "completed": queue.completed_count,
            "cancelled": queue.cancelled_count,
        },
        "synchronization": {
            "total": sync.count,
            "pending": len(sync.get_pending()),
        },
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_orchestration_data() -> None:
    engine = get_engine()
    bus = get_bus()

    # Register default triggers
    engine.register_trigger(Trigger(
        trigger_id="trg_checkpoint_fail",
        trigger_event=TriggerEvent.CHECKPOINT_FAILED,
        action_type=ActionType.ESCALATE,
        action_payload={"reason": "Checkpoint failed — escalation required"},
        priority=100,
    ))
    engine.register_trigger(Trigger(
        trigger_id="trg_health_decline",
        trigger_event=TriggerEvent.HEALTH_DECLINED,
        action_type=ActionType.NOTIFY,
        action_payload={"reason": "Organizational health declined"},
        priority=80,
    ))
    engine.register_trigger(Trigger(
        trigger_id="trg_execution_complete",
        trigger_event=TriggerEvent.EXECUTION_COMPLETED,
        action_type=ActionType.CAPTURE_SNAPSHOT,
        action_payload={"reason": "Execution completed — capturing state"},
        priority=50,
    ))

    # Publish initial signals
    bus.publish("orchestration", TriggerEvent.SNAPSHOT_CAPTURED, {"reason": "Orchestration runtime initialized"})

    # Execute first cycle
    engine.execute_cycle(bus)