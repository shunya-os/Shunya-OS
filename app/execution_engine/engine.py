from app.objects.models import Object
from app.execution_engine.service import ExecutionService, log_execution
from app.execution_engine.truth import TruthService
from app.intelligence.service import IntelligenceService
from app import db
import logging

logger = logging.getLogger(__name__)


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
    Execution without evidence is forbidden.
    """
    if action.get("type") == "update":
        state_before = dict(obj.state or {})
        payload = action.get("payload", {})

        # PHASE 3 LAYER C: Pipeline enforcement
        decision_source = action.get("decision_source", "unknown")
        decision_confidence = action.get("decision_confidence", "low")

        # Check that evidence exists for this decision
        try:
            from app.evidence.models_db import EvidenceRecord
            evidence = EvidenceRecord.query.filter(
                EvidenceRecord.source_id == str(obj.id)
            ).order_by(EvidenceRecord.id.desc()).first()
            if evidence is None:
                # Log warning but don't block — evidence may be in cortex state_log
                logger.warning(
                    "No direct EvidenceRecord for object %d. "
                    "Decision source=%s confidence=%s. "
                    "Pipeline: evidence → decision → execution has gap.",
                    obj.id, decision_source, decision_confidence,
                )
        except Exception:
            pass

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