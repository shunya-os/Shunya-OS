"""Executor — Performs approved tasks through controlled adapters.

Executor does NOT reason about company strategy. It executes a valid workflow action.
Actions are constrained by capability, permission, and policy.
"""
from typing import Optional, Callable, Any
from app import db
from app.models import Entity, ActivityLog, Notification
from app.shunya.foundation import Result, PermissionError
from app.shunya.governance import GovernanceEngine, ActionType


class Executor:
    """Executes approved actions through controlled adapters."""

    @staticmethod
    def execute(tenant_id: int, user_id: int, user_role: str,
                action_type: ActionType, entity_id: Optional[int] = None,
                params: dict = None, execute_fn: Callable = None) -> Result:
        """Execute an action through governance, then perform it."""
        # 1. Check governance
        level = GovernanceEngine.get_level(action_type, user_role)

        if level.value == "govern":
            return Result.needs_governance(
                level="govern",
                message=f"Action '{action_type.value}' requires admin approval"
            )

        if level.value == "draft" and not params.get("confirmed"):
            return Result.needs_governance(
                level="draft",
                data=params,
                message="Review and confirm to execute"
            )

        # 2. Execute
        try:
            if execute_fn:
                result = execute_fn()
            else:
                result = Executor._default_execute(
                    tenant_id, user_id, action_type, entity_id, params or {}
                )
        except Exception as e:
            return Result.fail(str(e))

        # 3. Observe
        from app.shunya.observer import Observer
        Observer.record(
            tenant_id=tenant_id,
            entity_id=entity_id,
            user_id=user_id,
            action=action_type.value,
            detail=f"Executed via {action_type.value}",
            governance_level=level.value,
        )

        return Result.ok(data=result)

    @staticmethod
    def _default_execute(tenant_id: int, user_id: int,
                         action_type: ActionType, entity_id: Optional[int],
                         params: dict) -> Any:
        """Default execution logic for common action types."""
        if action_type == ActionType.CHANGE_STATUS and entity_id:
            entity = db.session.get(Entity, entity_id)
            if entity and entity.tenant_id == tenant_id:
                new_status = params.get("status")
                if new_status:
                    entity.status = new_status
                    db.session.commit()
                    return {"entity_id": entity_id, "new_status": new_status}

        elif action_type == ActionType.SEND_MESSAGE:
            from app.models import Message
            msg = Message(
                tenant_id=tenant_id,
                entity_id=entity_id,
                sender_type="team",
                sender_id=user_id,
                channel=params.get("channel", "app"),
                content=params.get("content", ""),
            )
            db.session.add(msg)
            db.session.commit()
            return {"message_id": msg.id}

        return {"status": "executed", "action": action_type.value}