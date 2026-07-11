"""Shunya Executor — governed action execution through controlled adapters.

Every execution knows:
- WHAT is being executed
- WHY / which decision / which plan / which workflow / which task
- WHO authorized it
- WHICH policy allows it
- WHICH tool is used
- WHAT input was provided
- WHAT result was returned

The Reasoning engine must not secretly become Executor.
"""
import json, logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from enum import Enum
from dataclasses import dataclass, field, asdict
from app import db
from app.models import ActivityLog, Entity, EntityDefinition, Notification
from app.shunya.foundation import Result
from app.shunya.governance import GovernanceEngine, GovernanceLevel

logger = logging.getLogger("app.shunya.executor")


class ActionType(str, Enum):
    SEND_MESSAGE = "send_message"
    CREATE_ENTITY = "create_entity"
    UPDATE_ENTITY = "update_entity"
    UPDATE_STATUS = "update_status"
    SEND_EMAIL = "send_email"
    SEND_NOTIFICATION = "send_notification"
    CALL_API = "call_api"
    GENERATE_DOCUMENT = "generate_document"
    SCHEDULE_EVENT = "schedule_event"
    DELETE_ENTITY = "delete_entity"
    ARCHIVE_ENTITY = "archive_entity"
    ASSIGN_ENTITY = "assign_entity"


@dataclass
class ExecutionContext:
    """Full context for every execution."""
    action_type: ActionType
    tenant_id: int
    user_id: int
    user_role: str
    
    # Optional traceability links
    decision_id: Optional[int] = None
    plan_id: Optional[int] = None
    workflow_id: Optional[int] = None
    task_id: Optional[int] = None
    entity_id: Optional[int] = None
    
    # Policy
    policy_reference: Optional[str] = None
    governance_level: GovernanceLevel = GovernanceLevel.AUTO
    
    # Input/Output
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Timestamps
    requested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    executed_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    @property
    def duration_ms(self) -> Optional[float]:
        if self.executed_at and self.completed_at:
            from datetime import datetime
            start = datetime.fromisoformat(self.executed_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds() * 1000
        return None


class ToolRegistry:
    """Registry of controlled adapters for execution.
    
    Each adapter is a callable that takes (params, context) and returns a Result.
    """
    
    _adapters: Dict[str, Callable] = {}
    
    @classmethod
    def register(cls, action_type: ActionType, adapter: Callable):
        """Register an adapter for an action type."""
        cls._adapters[action_type.value] = adapter
        logger.info("Registered adapter: %s", action_type.value)
    
    @classmethod
    def get(cls, action_type: ActionType) -> Optional[Callable]:
        return cls._adapters.get(action_type.value)
    
    @classmethod
    def list_available(cls) -> list:
        return list(cls._adapters.keys())


class Executor:
    """Governed executor with full traceability."""

    @staticmethod
    def execute(
        tenant_id: int,
        user_id: int,
        user_role: str,
        action_type: ActionType,
        params: Dict[str, Any] = None,
        entity_id: Optional[int] = None,
        decision_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        workflow_id: Optional[int] = None,
        task_id: Optional[int] = None,
    ) -> Result:
        """Execute an action through governance + controlled adapter.
        
        Flow:
        1. Check governance level for this action + user
        2. Check if action is allowed by policy
        3. Look up adapter in registry
        4. Execute adapter
        5. Record execution
        6. Return result
        """
        params = params or {}
        ctx = ExecutionContext(
            action_type=action_type,
            tenant_id=tenant_id,
            user_id=user_id,
            user_role=user_role,
            entity_id=entity_id,
            decision_id=decision_id,
            plan_id=plan_id,
            workflow_id=workflow_id,
            task_id=task_id,
            params=params,
            requested_at=datetime.utcnow().isoformat(),
        )
        
        # Step 1: Check governance
        governance = GovernanceEngine.get_governance_level(action_type.value, user_role, tenant_id)
        ctx.governance_level = governance
        
        if governance == GovernanceLevel.DRAFT:
            # Draft = return for human confirmation
            return Result(
                success=False,
                error="DRAFT: Action requires human confirmation",
                data={"execution_context": asdict(ctx), "requires_approval": True}
            )
        
        # Step 2: Check policy
        if not GovernanceEngine.check_policy(action_type.value, user_role, tenant_id, params):
            return Result(
                success=False,
                error=f"Policy denied: {user_role} cannot execute {action_type.value}",
                data={"execution_context": asdict(ctx)}
            )
        
        # Step 3: Find adapter
        adapter = ToolRegistry.get(action_type)
        if not adapter:
            return Result(
                success=False,
                error=f"No adapter registered for {action_type.value}",
                data={"execution_context": asdict(ctx)}
            )
        
        # Step 4: Execute
        ctx.executed_at = datetime.utcnow().isoformat()
        try:
            result = adapter(params, ctx)
            ctx.completed_at = datetime.utcnow().isoformat()
            
            if result.success:
                ctx.result = result.data
                Executor._record_execution(ctx, "completed")
            else:
                ctx.error = result.error
                Executor._record_execution(ctx, "failed")
            
            return result
            
        except Exception as e:
            ctx.completed_at = datetime.utcnow().isoformat()
            ctx.error = str(e)
            Executor._record_execution(ctx, "error")
            logger.error("Execution failed: %s", e)
            return Result(success=False, error=str(e), data={"execution_context": asdict(ctx)})
    
    @staticmethod
    def _record_execution(ctx: ExecutionContext, status: str):
        """Record the execution in the activity log."""
        try:
            activity = ActivityLog(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                entity_id=ctx.entity_id,
                action=f"executor.{ctx.action_type.value}",
                detail=json.dumps({
                    "action_type": ctx.action_type.value,
                    "status": status,
                    "governance": ctx.governance_level.value,
                    "error": ctx.error,
                    "duration_ms": ctx.duration_ms,
                    "entity_id": ctx.entity_id,
                    "params_keys": list(ctx.params.keys()),
                }),
                governance_level=ctx.governance_level.value,
            )
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            logger.error("Failed to record execution: %s", e)
    
    @staticmethod
    def get_execution_history(tenant_id: int, limit: int = 50) -> list:
        """Get recent execution history."""
        logs = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.action.like("executor.%"),
        ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
        
        return [{
            "id": log.id,
            "action": log.action.replace("executor.", ""),
            "detail": log.detail,
            "governance": log.governance_level,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "entity_id": log.entity_id,
        } for log in logs]


# ---------------------------------------------------------------------------
# Built-in Adapters
# ---------------------------------------------------------------------------

def _adapter_update_status(params: dict, ctx: ExecutionContext) -> Result:
    """Update an entity's status."""
    entity_id = ctx.entity_id or params.get("entity_id")
    new_status = params.get("status", "")
    
    if not entity_id or not new_status:
        return Result(success=False, error="entity_id and status required")
    
    entity = db.session.get(Entity, entity_id)
    if not entity:
        return Result(success=False, error=f"Entity {entity_id} not found")
    
    old_status = entity.status
    entity.status = new_status
    
    activity = ActivityLog(
        tenant_id=ctx.tenant_id,
        entity_id=entity.id,
        user_id=ctx.user_id,
        action="status_changed",
        detail=f"Via executor: {old_status} → {new_status}",
        governance_level=ctx.governance_level.value,
    )
    db.session.add(activity)
    db.session.commit()
    
    return Result(success=True, data={
        "entity_id": entity.id,
        "old_status": old_status,
        "new_status": new_status,
    })


def _adapter_send_notification(params: dict, ctx: ExecutionContext) -> Result:
    """Send a notification to a user."""
    title = params.get("title", "")
    message = params.get("message", "")
    user_id = params.get("user_id", ctx.user_id)
    
    if not message:
        return Result(success=False, error="message required")
    
    notification = Notification(
        tenant_id=ctx.tenant_id,
        user_id=user_id,
        entity_id=ctx.entity_id,
        type="executor_action",
        title=title or "Action Completed",
        message=message,
        icon="⚡",
    )
    db.session.add(notification)
    db.session.commit()
    
    return Result(success=True, data={"notification_id": notification.id})


def _adapter_archive_entity(params: dict, ctx: ExecutionContext) -> Result:
    """Archive an entity."""
    entity_id = ctx.entity_id or params.get("entity_id")
    if not entity_id:
        return Result(success=False, error="entity_id required")
    
    entity = db.session.get(Entity, entity_id)
    if not entity:
        return Result(success=False, error=f"Entity {entity_id} not found")
    
    entity.is_archived = True
    
    activity = ActivityLog(
        tenant_id=ctx.tenant_id,
        entity_id=entity.id,
        user_id=ctx.user_id,
        action="archived",
        detail="Via executor",
        governance_level=ctx.governance_level.value,
    )
    db.session.add(activity)
    db.session.commit()
    
    return Result(success=True, data={"entity_id": entity.id, "status": "archived"})


def _adapter_assign_entity(params: dict, ctx: ExecutionContext) -> Result:
    """Assign an entity to a team member."""
    entity_id = ctx.entity_id or params.get("entity_id")
    assignee_id = params.get("assignee_id")
    
    if not entity_id or not assignee_id:
        return Result(success=False, error="entity_id and assignee_id required")
    
    entity = db.session.get(Entity, entity_id)
    if not entity:
        return Result(success=False, error=f"Entity {entity_id} not found")
    
    old_assignee = entity.assigned_to
    entity.assigned_to = assignee_id
    
    activity = ActivityLog(
        tenant_id=ctx.tenant_id,
        entity_id=entity.id,
        user_id=ctx.user_id,
        action="assigned",
        detail=f"Assigned to user {assignee_id} (was {old_assignee})",
        governance_level=ctx.governance_level.value,
    )
    db.session.add(activity)
    db.session.commit()
    
    return Result(success=True, data={
        "entity_id": entity.id,
        "assigned_to": assignee_id,
        "previous": old_assignee,
    })


# Register all built-in adapters
ToolRegistry.register(ActionType.UPDATE_STATUS, _adapter_update_status)
ToolRegistry.register(ActionType.SEND_NOTIFICATION, _adapter_send_notification)
ToolRegistry.register(ActionType.ARCHIVE_ENTITY, _adapter_archive_entity)
ToolRegistry.register(ActionType.ASSIGN_ENTITY, _adapter_assign_entity)

logger.info("Executor initialized with %d adapters: %s",
    len(ToolRegistry._adapters), list(ToolRegistry._adapters.keys()))