from app.objects.models import Object
from app.execution_engine.service import ExecutionService, log_execution
from app.execution_engine.truth import TruthService
from app.intelligence.service import IntelligenceService
from app import db
import logging

logger = logging.getLogger(__name__)

# PHASE 3 LAYER D: Execution gate
# Set to True ONLY when called from app/runtime/entry.py
_execution_gate_open = False


def open_execution_gate():
    """Open the execution gate. Called ONLY by entry.py."""
    global _execution_gate_open
    _execution_gate_open = True


def close_execution_gate():
    """Close the execution gate."""
    global _execution_gate_open
    _execution_gate_open = False


def _check_execution_gate():
    """Block execution if the gate is not open (not from entry.py)."""
    if not _execution_gate_open:
        raise RuntimeError(
            "Direct execution forbidden. All execution must go through "
            "app/runtime/entry.py process_event()."
        )


class ExecutionEngine:

    @staticmethod
    def evaluate(obj: Object):
        state = obj.state or {}
        if state.get("status") == "new":
            return "activate"
        return "noop"

    @staticmethod
    def execute(obj: Object):
        decision = ExecutionEngine.evaluate(obj)
        trigger_state = dict(obj.state or {})

        exe = ExecutionService.create_execution(
            object_id=obj.id,
            decision=decision
        )
        ExecutionService.update_status(exe, "running")

        if decision == "activate":
            TruthService.apply_truth(obj, {"status": "active"})
            log_execution(
                object_id=obj.id,
                action_type=decision,
                payload={"status": "active"},
                state_before=trigger_state,
                state_after=dict(obj.state or {}),
            )

        ExecutionService.update_status(exe, "completed")

        IntelligenceService.learn_from_execution(obj, decision, trigger_state)

        return {
            "execution_id": exe.id,
            "decision": decision,
            "object_id": obj.id,
            "final_state": obj.state
        }


def execute_action(obj: "Object", action: dict):
    """Apply an action payload to an object's state and log the mutation.

    Only 'update' type actions produce state changes. Noop actions are
    returned as-is with no side effects and no log entry.

    PHASE 3 LAYER C: Enforces evidence → decision → execution pipeline.
    PHASE 3 LAYER D: Blocks direct execution outside entry.py.
    """
    # PHASE 3 LAYER D: Block direct execution
    _check_execution_gate()

    if action.get("type") == "update":
        state_before = dict(obj.state or {})
        payload = action.get("payload", {})

        # PHASE 3 LAYER C: Hard pipeline enforcement
        # No execution without evidence. This is a hard block.
        decision_source = action.get("decision_source", "unknown")
        decision_confidence = action.get("decision_confidence", "low")

        try:
            from app.evidence.models_db import EvidenceRecord
            evidence = EvidenceRecord.query.filter(
                EvidenceRecord.source_id == str(obj.id)
            ).order_by(EvidenceRecord.id.desc()).first()
            if evidence is None:
                # Check cortex state_log as secondary evidence source
                from app.cortex.state_log import query
                cortex_records = query(observation_type="execution_summary", entity_id=obj.id, limit=1)
                if not cortex_records:
                    raise RuntimeError(
                        f"Execution without evidence forbidden. "
                        f"Object {obj.id} has no EvidenceRecord and no cortex observation. "
                        f"Decision source={decision_source} confidence={decision_confidence}. "
                        f"Pipeline: evidence → decision → execution violated."
                    )
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(
                f"Execution without evidence forbidden. "
                f"Evidence check failed for object {obj.id}: {e}"
            ) from e

        obj.state = {**(obj.state or {}), **payload}
        db.session.commit()
        log_execution(
            object_id=obj.id,
            action_type="update",
            payload=payload,
            state_before=state_before,
            state_after=dict(obj.state or {}),
        )
    return obj