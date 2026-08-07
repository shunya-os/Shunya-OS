"""Continuous execution loop — observes objects, determines next action, executes, persists.

Emits pure observation signals: state_changed after update, no_action on noop.
Stateless, deterministic, no memory across cycles.

PROD-13: Relational execution graph propagation.
After a successful update, the loop checks for outbound relations and
propagates execution triggers to connected objects — one cycle, one chain.
No recursion, no business logic.
"""

import time
import logging

from app import db
from app.objects.models import Object
from app.runtime.decision_engine import get_next_action
from app.execution_engine.engine import execute_action
from app.signals.service import emit_signal
from app.graph.service import get_targets

logger = logging.getLogger(__name__)

_LOOP_INTERVAL = 3


def _propagate_to_targets(obj, summary: dict):
    """Propagate execution to all targets declared via object_relations.

    Pure structural propagation: every target gets one decision + execute
    cycle. Noop targets are skipped. Errors are recorded per-target.
    """
    relations = get_targets(obj.id)
    for rel in relations:
        try:
            target = Object.query.get(rel.target_object_id)
            if target is None:
                continue
            target_action = get_next_action(target)
            if target_action.get("type") == "noop":
                emit_signal(target.id, "no_action", {"state": target.state})
                summary["noops"] += 1
                summary["signals_emitted"] += 1
                continue
            state_before = dict(target.state or {})
            execute_action(target, target_action)
            emit_signal(
                target.id, "state_changed",
                {"from": state_before, "to": target.state},
            )
            summary["actions_taken"] += 1
            summary["signals_emitted"] += 1
        except Exception as e:
            logger.error(
                "Propagation error: source=%d target_id=%s: %s",
                obj.id, rel.target_object_id, e,
            )
            summary["errors"].append(
                {"object_id": rel.target_object_id, "error": str(e)},
            )


def run_cycle() -> dict:
    """Run one iteration of the execution loop.

    For each object:
    1. Determine next action via decision engine
    2. Execute action if update
    3. Propagate to relational targets
    4. Emit pure observation signal
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
            emit_signal(
                obj.id, "state_changed",
                {"from": state_before, "to": obj.state},
            )
            summary["actions_taken"] += 1
            summary["signals_emitted"] += 1

            # PROD-13: propagate to relational targets
            _propagate_to_targets(obj, summary)

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