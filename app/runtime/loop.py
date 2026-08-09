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
from app.runtime.decision_engine import decide_lead_task
from app.runtime.decision_engine import decide_lead_stage
from app.runtime.decision_engine import decide_entity
from app.communication.service import MessageService
from app.output.generator import generate_output
from app.communication.processor import process_inbound
from app.communication.delivery import deliver_messages
from app.core.entity import Entity
from app.models import Lead
from app.execution_log.models import log_execution

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
            print(f"[ACT-01] Processing Entity: {obj.id} (type={obj.object_type})")
            print(f"[ACT-01] Decision: {json.dumps(action, default=str)}")

            log_execution(obj.id, "ENTITY_SEEN", {"object_type": obj.object_type, "state": obj.state})

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

            # PROD-52: after state update — generate output and create message
            output = generate_output(obj)
            MessageService.create(
                entity_id=obj.id,
                content=str(output),
                direction="outbound",
                channel="system"
            )

            # PROD-13: propagate to relational targets
            _propagate_to_targets(obj, summary)

        except Exception as e:
            logger.error("Loop error on object %d: %s", obj.id, e)
            summary["errors"].append({"object_id": obj.id, "error": str(e)})
            log_execution(obj.id, "ERROR", {"error": str(e)})

    # PROD-17: process all commitments — gap-aware decision → apply
    commitments = Commitment.query.all()
    for c in commitments:
        decision = decide_next_from_commitment(c)
        apply_decision(c, decision)

    # PROD-28/30: process leads — task creation + outcome
    leads = Lead.query.all()
    for lead in leads:
        task_dec = decide_lead_task(lead)
        if task_dec.get("type") == "update":
            lead.outcome = "attempted"

        # PROD-32-34: stage progression
        stage_dec = decide_lead_stage(lead)
        # PROD-40: support multi-action list decisions
        if isinstance(stage_dec, list):
            for dec in stage_dec:
                if dec.get("type") == "update":
                    for k, v in dec.get("payload", {}).items():
                        setattr(lead, k, v)
        elif stage_dec.get("type") == "update":
            for k, v in stage_dec.get("payload", {}).items():
                setattr(lead, k, v)

    # PROD-59: process inbound events before entity processing
    process_inbound()

    # PROD-45: process all Entities — generic state transitions
    entities = Entity.query.all()
    for e in entities:
        ed = decide_entity(e)
        if ed.get("type") == "update":
            for k, v in ed.get("payload", {}).items():
                setattr(e, k, v)

    # PROD-59: deliver pending messages at end of cycle
    deliver_messages()

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