from app.objects.models import Object
from app.execution_engine.service import log_execution
from app import db
import logging
import threading

logger = logging.getLogger(__name__)

# PHASE 3 LAYER D: Execution gate
# Set to True ONLY when called from app/runtime/entry.py
_execution_gate_open = False
_gate_lock = threading.Lock()
_gate_refcount = 0


def open_execution_gate():
    """Open the execution gate. Thread-safe refcounted open.

    Multiple concurrent callers can open the gate independently.
    The gate remains open until ALL openers have called close().
    This prevents one caller from closing the gate while another
    is still executing.
    """
    global _execution_gate_open, _gate_refcount
    with _gate_lock:
        _gate_refcount += 1
        _execution_gate_open = True


def close_execution_gate():
    """Close the execution gate. Thread-safe refcounted close.

    Only closes the gate when the last opener calls close.
    """
    global _execution_gate_open, _gate_refcount
    with _gate_lock:
        _gate_refcount -= 1
        if _gate_refcount <= 0:
            _gate_refcount = 0
            _execution_gate_open = False


def is_gate_open() -> bool:
    """Check whether the execution gate is currently open."""
    return _execution_gate_open


def _check_execution_gate():
    """Block execution if the gate is not open (not from entry.py)."""
    if not _execution_gate_open:
        raise RuntimeError(
            "Direct execution forbidden. All execution must go through "
            "app/runtime/entry.py process_event()."
        )

class ExecutionEngine:
    """Execution engine — provides evaluate() and execute_action().

    evaluate() is REMOVED from PROD-06. The canonical decision authority
    is get_next_action() in runtime/decision_engine.py, which derives
    structural decisions from Object.state only. Constitutional evaluation
    (State + Intent + Evidence + Time) is established at entry.py via
    DecisionContext — the sole orchestration entry point.

    Only execute_action() remains: the single mutation primitive, always
    gate-checked and evidence-checked.
    """
    pass


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
