"""
Recovery Hierarchy — 5 levels of recovery for the Outcome Runtime.

Level 1: Retry — retry the same operation
Level 2: Alternative implementation — switch to different provider/method
Level 3: Alternative workflow — use different approach to same outcome
Level 4: Partial completion — preserve completed work, report partial success
Level 5: Human assistance — only now ask the user
"""
import logging
import time
from typing import Any, Optional

from app.execution.models import Outcome

logger = logging.getLogger(__name__)

# ── Provider fallback chain ──
AI_PROVIDER_CHAIN = ["Groq", "Gemini", "OpenRouter", "Cloudflare", "HuggingFace", "Together", "Anthropic", "local"]


class RecoveryOrchestrator:
    """Orchestrates 5-level recovery for outcome execution."""

    def execute_with_hierarchy(
        self,
        action: dict,
        identity_id: str,
        step_idx: int,
        outcome_id: str,
    ) -> tuple[bool, dict, list]:
        """
        Execute an action with full recovery hierarchy.
        Returns (success, result_dict, recovery_log).
        """
        recovery_log = []
        action_type = action.get("action", "unknown")
        action_name = action.get("type", "")

        # Level 1: Retry (up to 2 attempts)
        for attempt in range(3):
            try:
                result = self._execute_action(action, identity_id)
                if self._validate_result(action_type, result):
                    if attempt > 0:
                        recovery_log.append({
                            "level": 1,
                            "attempt": attempt,
                            "strategy": "retry",
                            "success": True,
                            "timestamp": time.time(),
                        })
                    return True, result, recovery_log
            except Exception as e:
                error_msg = str(e)
                logger.warning("Outcome %s step %d attempt %d: %s", outcome_id, step_idx, attempt + 1, error_msg)
                if attempt < 2:
                    delay = 1.0 * (2 ** attempt)
                    time.sleep(delay)
                    recovery_log.append({
                        "level": 1,
                        "attempt": attempt + 1,
                        "strategy": "retry",
                        "success": False,
                        "error": error_msg,
                        "timestamp": time.time(),
                    })

        # Level 2: Alternative implementation
        if action_type in ("create_object", "update_object"):
            try:
                # Try with alternative field mapping
                alt_action = self._build_alternative(action)
                result = self._execute_action(alt_action, identity_id)
                if self._validate_result(action_type, result):
                    recovery_log.append({
                        "level": 2,
                        "attempt": 1,
                        "strategy": "alternative_implementation",
                        "success": True,
                        "timestamp": time.time(),
                    })
                    return True, result, recovery_log
            except Exception as e:
                logger.warning("Outcome %s step %d Level 2 failed: %s", outcome_id, step_idx, str(e))
                recovery_log.append({
                    "level": 2,
                    "attempt": 1,
                    "strategy": "alternative_implementation",
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time(),
                })

        # Level 3: Alternative workflow
        # (e.g. PDF generation failed → save HTML for later conversion)
        if "pdf" in action_type.lower() or "generate" in action_type.lower():
            try:
                result = self._execute_alt_workflow(action, identity_id)
                if result.get("success"):
                    recovery_log.append({
                        "level": 3,
                        "attempt": 1,
                        "strategy": "alternative_workflow",
                        "success": True,
                        "note": "Deferred to background conversion",
                        "timestamp": time.time(),
                    })
                    return True, result, recovery_log
            except Exception as e:
                logger.warning("Outcome %s step %d Level 3 failed: %s", outcome_id, step_idx, str(e))
                recovery_log.append({
                    "level": 3,
                    "attempt": 1,
                    "strategy": "alternative_workflow",
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time(),
                })

        # Level 4: Partial completion — return what we have
        recovery_log.append({
            "level": 4,
            "attempt": 1,
            "strategy": "partial_completion",
            "success": True,
            "timestamp": time.time(),
        })
        return False, {
            "success": False,
            "error": "All recovery strategies exhausted",
            "partial": True,
        }, recovery_log

    # ── Internal execution methods ──

    def _execute_action(self, action: dict, identity_id: str) -> dict:
        """Execute a single action using direct DB operations."""
        from app import db
        from app.objects.legacy_models import ShunyaObject
        import uuid
        
        action_type = action.get("action", "unknown")
        action_name = action.get("type", "")
        data = action.get("data", {})
        
        if action_type == "create_object":
            name = data.get("name", data.get("title", ""))
            obj = ShunyaObject(
                object_id=uuid.uuid4().hex[:24],
                workspace_id="spc_business",
                object_type=action_name or "document",
                name=name or f"{action_name}",
                status="active",
                data=data,
                created_by=identity_id,
            )
            db.session.add(obj)
            db.session.commit()
            return {"success": True, "data": {"object_id": obj.object_id, "name": obj.name, "id": obj.id}}
        
        if action_type == "update_object":
            from app.objects.legacy_models import ShunyaObject
            obj_id = action.get("id")
            obj = ShunyaObject.query.filter_by(id=obj_id).first() if obj_id else None
            if obj:
                for key, val in data.items():
                    if hasattr(obj, key):
                        setattr(obj, key, val)
                db.session.commit()
                return {"success": True, "data": {"object_id": obj.object_id, "name": obj.name}}
            return {"success": False, "error": f"Object #{obj_id} not found"}
        
        if action_type == "delete_object":
            obj_id = action.get("id")
            obj = ShunyaObject.query.filter_by(id=obj_id).first() if obj_id else None
            if obj:
                obj.is_deleted = True
                obj.status = "deleted"
                db.session.commit()
                return {"success": True}
            return {"success": False, "error": f"Object #{obj_id} not found"}
        
        return {"success": False, "error": f"Unknown action: {action_type}"}

    def _build_alternative(self, action: dict) -> dict:
        """Build an alternative version of the action for Level 2 recovery."""
        # Simplified field mapping
        alt = dict(action)
        data = alt.get("data", {})
        if "name" not in data and "title" in data:
            data["name"] = data.pop("title")
        alt["data"] = data
        return alt

    def _execute_alt_workflow(self, action: dict, identity_id: str) -> dict:
        """Execute alternative workflow for Level 3 recovery."""
        raise NotImplementedError("Subclass must implement _execute_alt_workflow")

    def _validate_result(self, action_type: str, result: dict) -> bool:
        """Validate that the result is complete and correct."""
        if not result:
            return False
        if action_type in ("create_object",):
            data = result.get("data", result)
            if not data.get("object_id") and not data.get("id"):
                return False
        return True


# ── Default action implementations (used by routes) ──

def execute_action_direct(action: dict, identity_id: str) -> dict:
    """Execute an action directly via Flask test client or direct DB access."""
    from flask import current_app
    from app import create_app

    action_type = action.get("action", "unknown")
    action_name = action.get("type", "")

    if action_type == "create_object":
        from app import db
        from app.objects.legacy_models import ShunyaObject
        import uuid
        data = action.get("data", {})
        name = data.get("name", data.get("title", ""))
        # Build minimal object data
        obj_data = {
            "name": name or f"{action_name}",
            "data": data,
        }
        if "customer_name" in data:
            obj_data["customer_name"] = data["customer_name"]
        if "title" in data or "name" in data:
            obj_data["title"] = data.get("title", data.get("name", ""))

        # Try direct DB insert
        import uuid
        from app.objects.legacy_models import ShunyaObject
        obj = ShunyaObject(
            object_id=uuid.uuid4().hex[:24],
            workspace_id="spc_business",
            object_type=action_name,
            name=obj_data.get("name", ""),
            status="active",
            data=data,
            created_by=identity_id,
        )
        db.session.add(obj)
        db.session.commit()
        return {"success": True, "data": {"object_id": obj.object_id, "name": obj.name, "id": obj.id}}

    return {"success": False, "error": f"Unknown action: {action_type}"}