"""Recovery — simple retry for execution actions.

Uses the canonical Object model. No legacy ShunyaObject, no direct execution
bypass, no workflow semantics.
"""
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class RecoveryOrchestrator:
    """Simple retry for execution actions.

    Removed: 5-level recovery hierarchy, ShunyaObject usage, execute_action_direct.
    Removed: step-based progression, workflow assumptions.
    Kept: simple retry with exponential backoff.
    """

    def execute_with_retry(
        self,
        action: dict,
        max_attempts: int = 3,
    ) -> tuple[bool, dict, list]:
        """Execute an action with retry.

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
        """Execute via canonical execution engine.

        Uses the canonical execution path. No legacy ShunyaObject.
        The execution gate must be opened by the caller.
        """
        from app.execution_engine.engine import execute_action
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
                    from app.execution_engine.engine import execute_action as _exec
                    _exec(obj, {"type": "update", "payload": data, "decision_source": "recovery", "decision_confidence": "high"})
                    return {"success": True, "data": {"id": obj.id, "name": obj.name}}
            return {"success": False, "error": f"Object #{obj_id} not found"}

        return {"success": False, "error": f"Unknown action: {action_type}"}