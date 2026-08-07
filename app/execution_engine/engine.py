from app.objects.models import Object
from app.execution_engine.service import ExecutionService, log_execution
from app.execution_engine.truth import TruthService
from app.intelligence.service import IntelligenceService
from app import db


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


def execute_action(obj: Object, action: dict):
    """Apply an action payload to an object's state and log the mutation.

    Only 'update' type actions produce state changes. Noop actions are
    returned as-is with no side effects and no log entry.
    """
    if action.get("type") == "update":
        state_before = dict(obj.state or {})
        payload = action.get("payload", {})
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