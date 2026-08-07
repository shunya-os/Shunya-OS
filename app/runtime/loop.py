"""Continuous execution loop — observes objects, determines next action, executes, persists.

Emits pure observation signals: state_changed after update, no_action on noop.
Stateless, deterministic, no memory across cycles.
"""

import time
import logging

from app import db
from app.objects.models import Object
from app.runtime.decision_engine import get_next_action
from app.execution_engine.engine import execute_action
from app.signals.service import emit_signal

logger = logging.getLogger(__name__)

_LOOP_INTERVAL = 3


def run_cycle() -> dict:
    """Run one iteration of the execution loop.

    For each object:
    1. Determine next action via decision engine
    2. Execute action if update
    3. Emit pure observation signal
    """
    objects = Object.query.all()
    summary = {
        "total_objects": len(objects),
        "actions_taken": 0,
        "noops": 0,
        "signals_emitted": 0,
        "errors": [],
    }

    for obj in objects:
        try:
            action = get_next_action(obj)

            if action["type"] == "noop":
                emit_signal(obj.id, "no_action", {"state": obj.state})
                summary["noops"] += 1
                summary["signals_emitted"] += 1
                continue

            state_before = dict(obj.state or {})
            execute_action(obj, action)
            emit_signal(obj.id, "state_changed", {"from": state_before, "to": obj.state})
            summary["actions_taken"] += 1
            summary["signals_emitted"] += 1

        except Exception as e:
            logger.error("Loop error on object %d: %s", obj.id, e)
            summary["errors"].append({"object_id": obj.id, "error": str(e)})

    db.session.commit()
    return summary


def run_loop(interval: int = _LOOP_INTERVAL, cycles: int = None):
    """Run the execution loop continuously."""
    count = 0
    while cycles is None or count < cycles:
        count += 1
        try:
            summary = run_cycle()
            if summary["actions_taken"] > 0 or summary["signals_emitted"] > 0:
                logger.info(
                    "Loop cycle %d: %d objects, %d actions, %d signals",
                    count, summary["total_objects"],
                    summary["actions_taken"], summary["signals_emitted"],
                )
        except Exception as e:
            logger.error("Loop cycle %d failed: %s", count, e)

        time.sleep(interval)