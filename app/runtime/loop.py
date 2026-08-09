"""Continuous execution loop — observes objects and commitments, determines next action, executes, persists.

Emits pure observation signals: state_changed after update, no_action on noop.
Stateless, deterministic, no memory across cycles.

PROD-13: Relational execution graph propagation.
After a successful update, the loop checks for outbound relations and
propagates execution triggers to connected objects — one cycle, one chain.
No recursion, no business logic.

PROD-17: Autonomous execution loop — commitments.
The same cycle processes all commitments: gap-aware decision from the
latest observation, then applies it. Continuous processing, one cycle.

ACTIVATION-R2: Single source of truth — Object model only.
Lead and Entity legacy models removed from loop execution.
All entity processing uses Object (app/objects/models.py).
"""

import time
import json
import logging

from app import db
from app.objects.models import Object
from app.runtime.decision_engine import get_next_action
from app.execution_engine.engine import execute_action
from app.signals.service import emit_signal
from app.graph.service import get_targets
from app.commitments.models import Commitment
from app.runtime.decision_engine import decide_next_from_commitment
from app.commitments.service import apply_decision
from app.communication.service import MessageService
from app.output.generator import generate_output
from app.communication.processor import process_inbound
from app.communication.delivery import deliver_messages
from app.execution_log.models import log_execution
from app.execution.effects import execute_effects
from sqlalchemy.exc import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)

_LOOP_INTERVAL = 3


def _safe_rollback(summary: dict = None):
    """Rollback a failed transaction without throwing.

    Only rolls back if the session has a failed transaction (aborted).
    Does NOT rollback healthy uncommitted changes — they preserve their
    pending state until the final commit in run_cycle().

    Idempotent -- safe to call when no transaction is active.
    """
    try:
        db.session.execute(db.text("SELECT 1"))
    except (OperationalError, ProgrammingError) as e:
        msg = str(e)
        if "aborted" in msg.lower() or "current transaction" in msg.lower():
            try:
                db.session.rollback()
            except Exception:
                pass


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


def _run_objects(summary: dict):
    """Process all Object entities — crash-isolated section."""
    try:
        objects = Object.query.all()
        summary["total_objects"] = len(objects)
        for obj in objects:
            try:
                # ACTIVATION-03B: Schema validation — skip malformed entities
                if not hasattr(obj, 'type') or obj.type is None:
                    logger.warning("Skipping entity %d: invalid schema (type=None)", obj.id)
                    summary["errors"].append({"object_id": obj.id, "error": "invalid schema: type is None"})
                    continue

                action = get_next_action(obj)
                print(f"[ACT-01] Processing Entity: {obj.id} (type={obj.type})")
                print(f"[ACT-01] Decision: {json.dumps(action, default=str)}")

                log_execution(obj.id, "ENTITY_SEEN", {"object_type": obj.type, "state": obj.state})

                if action["type"] == "noop":
                    emit_signal(obj.id, "no_action", {"state": obj.state})
                    summary["noops"] += 1
                    summary["signals_emitted"] += 1
                    log_execution(obj.id, "NOOP", {"state": obj.state})
                    continue

                log_execution(obj.id, "DECISION", action)

                state_before = dict(obj.state or {})
                execute_action(obj, action)
                emit_signal(
                    obj.id, "state_changed",
                    {"from": state_before, "to": obj.state},
                )
                summary["actions_taken"] += 1
                summary["signals_emitted"] += 1
                log_execution(obj.id, "ACTION", {
                    "action": action,
                    "state_before": state_before,
                    "state_after": obj.state,
                })

                # PROD-52: after state update -- generate output and create message
                output = generate_output(obj)
                MessageService.create(
                    entity_id=obj.id,
                    content=str(output),
                    direction="outbound",
                    channel="system"
                )

                # ACTIVATION-08B: Effects now create MessageProposal objects.
                effects = action.get("effects", [])
                if effects:
                    execute_effects(effects, obj.id)

                # PROD-13: propagate to relational targets
                _propagate_to_targets(obj, summary)

            except Exception as e:
                logger.error("Loop error on object %d: %s", obj.id, e)
                summary["errors"].append({"object_id": obj.id, "error": str(e)})
                log_execution(obj.id, "ERROR", {"error": str(e)})
    except Exception as e:
        logger.error("Objects section crashed: %s", e)
        summary["errors"].append({"section": "objects", "error": str(e)})


def _run_commitments(summary: dict):
    """Process all commitments -- crash-isolated section."""
    try:
        commitments = Commitment.query.all()
        for c in commitments:
            try:
                decision = decide_next_from_commitment(c)
                apply_decision(c, decision)
            except Exception as e:
                logger.error("Commitment %d error: %s", c.id if hasattr(c, 'id') else 0, e)
                summary["errors"].append({"section": "commitments", "id": getattr(c, 'id', None), "error": str(e)})
    except Exception as e:
        logger.error("Commitments section crashed: %s", e)
        summary["errors"].append({"section": "commitments", "error": str(e)})


def run_cycle() -> dict:
    """Run one iteration of the execution loop with crash isolation.

    Every section is individually wrapped in try/except so a failure
    in one processing domain never blocks another. db.session.commit()
    ALWAYS executes to prevent orphaned transactions.

    ACTIVATION-R2: Only Object and Commitment models are processed.
    Lead and Entity legacy models removed.
    """
    summary = {
        "status": "completed",
        "total_objects": 0,
        "actions_taken": 0,
        "noops": 0,
        "signals_emitted": 0,
        "errors": [],
    }

    # ----- Crash-isolated sections -----
    _run_objects(summary)
    _safe_rollback(summary)

    _run_commitments(summary)
    _safe_rollback(summary)

    try:
        process_inbound()
    except Exception as e:
        logger.error("process_inbound failed: %s", e)
        summary["errors"].append({"section": "process_inbound", "error": str(e)})
        _safe_rollback(summary)

    try:
        deliver_messages()
    except Exception as e:
        logger.error("deliver_messages failed: %s", e)
        summary["errors"].append({"section": "deliver_messages", "error": str(e)})
        _safe_rollback(summary)

    # ----- Completion guarantee: commit ALWAYS executes -----
    try:
        db.session.commit()
    except Exception as e:
        logger.error("Final commit failed: %s", e)
        summary["errors"].append({"section": "commit", "error": str(e)})
        summary["status"] = "partial" if summary["errors"] else "completed"

    summary["status"] = "completed" if not summary["errors"] else "partial"

    # PHASE 2A: Evidence log for this cycle
    try:
        from app.evidence.service import log_evidence
        log_evidence(
            action="run_cycle",
            source="execution_loop",
            confidence=0.92 if not summary["errors"] else 0.35,
            evidence_type="execution",
            inputs={"cycle_start": None},
            outputs={
                "actions_taken": summary["actions_taken"],
                "noops": summary["noops"],
                "errors": len(summary["errors"]),
                "status": summary["status"],
            },
        )
    except Exception:
        pass

    # PHASE 2B: Cortex observer (read-only, no control)
    try:
        from app.intelligence.cortex_bridge import observe_execution_summary
        observe_execution_summary(summary)
    except Exception:
        pass

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