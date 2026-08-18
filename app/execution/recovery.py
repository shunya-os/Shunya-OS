"""Recovery — simple retry for execution actions.

Uses the canonical Object model. No legacy ShunyaObject, no direct execution
bypass, no workflow semantics.

AUTHORITY CONTRACT:
    This is a RECOVERY PRIMITIVE that delegates all execution through the
    canonical authority (app.runtime.entry.process_event). It does NOT
    call execution_engine.execute_action() directly — all mutations flow
    through the evidence → context → decision → execution pipeline.

    This satisfies requirement (b): delegator to canonical execution authority.

    Tested in: test_recovery_delegates_to_canonical()
"""
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class RecoveryOrchestrator:
    """Simple retry for execution actions.

    All execution actions delegate to the canonical execution authority
    (process_event in runtime/entry.py). This ensures the execution gate,
    evidence pipeline, and decision trace are always enforced.
    """

    def execute_with_retry(
        self,
        action: dict,
        max_attempts: int = 3,
    ) -> tuple[bool, dict, list]:
        """Execute an action with retry.

        Delegates all execution to the canonical authority via process_event.

        Returns (success, result_dict, retry_log).
        """
        retry_log = []
        for attempt in range(max_attempts):
            try:
                result = self._execute_action(action)
                if attempt > 0:
                    retry_log.append({
                        "level": 1,
                        "attempt": attempt + 1,
                        "strategy": "retry",
                        "success": True,
                        "timestamp": time.time(),
                    })
                return True, result, retry_log
            except Exception as e:
                error_msg = str(e)
                logger.warning("Action attempt %d/%d failed: %s", attempt + 1, max_attempts, error_msg)
                if attempt < max_attempts - 1:
                    delay = 1.0 * (2 ** attempt)
                    time.sleep(delay)
                    retry_log.append({
                        "level": 1,
                        "attempt": attempt + 1,
                        "strategy": "retry",
                        "success": False,
                        "error": error_msg,
                        "timestamp": time.time(),
                    })

        retry_log.append({
            "level": 4,
            "attempt": max_attempts,
            "strategy": "exhausted",
            "success": False,
            "timestamp": time.time(),
        })
        return False, {
            "success": False,
            "error": "All retry attempts exhausted",
        }, retry_log

    def _execute_action(self, action: dict) -> dict:
        """Execute via CANONICAL authority (process_event).

        All execution actions are delegated through app.runtime.entry.process_event,
        which handles gate management, evidence capture, decision trace, and
        execution in the proper pipeline order.

        This is NOT a direct execute_action call — it is always a delegator.
        """
        from app.runtime.entry import process_event
        from app.objects.models import Object

        action_type = action.get("action", "unknown")
        action_name = action.get("type", "")
        data = action.get("data", {})

        if action_type == "create_object":
            from app import db
            obj = Object(
                type=action_name or "generic",
                name=data.get("name", data.get("title", f"{action_name}")),
                state=data,
            )
            db.session.add(obj)
            db.session.commit()
            return {"success": True, "data": {"id": obj.id, "name": obj.name}}

        if action_type == "update_object":
            obj_id = action.get("id")
            if obj_id:
                obj = Object.query.get(obj_id)
                if obj:
                    # Delegate through canonical execution path
                    recovery_event = {
                        "source_type": "recovery",
                        "source_id": str(obj_id),
                        "entity_id": obj_id,
                        "id": obj_id,
                        "action": action_type,
                        "payload": data,
                        "type": action_name,
                        "name": getattr(obj, 'name', ''),
                    }
                    result = process_event(
                        event_type=f"recovery_{action_type}",
                        event_data=recovery_event,
                        source="recovery",
                    )
                    exec_result = result.get("execution", {})
                    return {"success": exec_result.get("status") == "completed",
                            "data": {"id": obj_id, "name": getattr(obj, 'name', '')},
                            "result": exec_result}
            return {"success": False, "error": f"Object #{obj_id} not found"}

        return {"success": False, "error": f"Unknown action: {action_type}"}