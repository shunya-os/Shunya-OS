"""Workflow — Converts plans into explicit tasks, states, dependencies, and ownership.

Workflow is the bridge between intention and operational execution.
The frontend's next-best-action experience is powered by workflow state.
Shows what is pending, active, blocked, completed, or failed.
"""
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from app import db
from app.models import Entity, EntityDefinition, ActivityLog
from app.shunya.foundation import ActionStatus, Result


@dataclass
class WorkflowState:
    """Current state of a workflow for an entity."""
    entity_id: int
    entity_type: str
    current_status: str
    available_transitions: List[str] = field(default_factory=list)
    blocked: bool = False
    blocker_reason: str = ""
    pending_actions: List[dict] = field(default_factory=list)
    completed_actions: List[dict] = field(default_factory=list)


class WorkflowEngine:
    """Manages workflow states, transitions, and dependencies."""

    @staticmethod
    def get_state(tenant_id: int, entity_id: int) -> Optional[WorkflowState]:
        """Get the current workflow state for an entity."""
        entity = db.session.get(Entity, entity_id)
        if not entity or entity.tenant_id != tenant_id:
            return None

        definition = entity.definition
        statuses = definition.statuses if definition else []
        current_idx = statuses.index(entity.status) if entity.status in statuses else -1

        # Available transitions (next statuses)
        available = statuses[current_idx + 1:] if current_idx >= 0 else []

        # Check for blockers
        blocked = False
        blocker_reason = ""
        if entity.status == "new":
            blocked = True
            blocker_reason = "Requires initial review and assignment"

        # Get recent activities
        activities = ActivityLog.query.filter_by(
            tenant_id=tenant_id, entity_id=entity_id
        ).order_by(ActivityLog.created_at.desc()).limit(10).all()

        return WorkflowState(
            entity_id=entity.id,
            entity_type=definition.type if definition else "",
            current_status=entity.status,
            available_transitions=available,
            blocked=blocked,
            blocker_reason=blocker_reason,
            completed_actions=[{"action": a.action, "detail": a.detail,
                                "at": a.created_at.isoformat() if a.created_at else None}
                               for a in activities if a.action != "created"],
            pending_actions=[{"action": "initial_review", "label": "Initial review"},
                             {"action": "customer_contact", "label": "Contact customer"}],
        )

    @staticmethod
    def transition(tenant_id: int, entity_id: int, new_status: str,
                   user_id: int) -> Result:
        """Transition an entity to a new status with validation."""
        entity = db.session.get(Entity, entity_id)
        if not entity or entity.tenant_id != tenant_id:
            return Result.fail("Entity not found")

        definition = entity.definition
        statuses = definition.statuses if definition else []

        if new_status not in statuses:
            return Result.fail(f"Invalid status '{new_status}'")

        old_status = entity.status
        entity.status = new_status

        log = ActivityLog(
            tenant_id=tenant_id,
            entity_id=entity.id,
            user_id=user_id,
            action="status_changed",
            detail=f"Workflow transition: {old_status} → {new_status}",
            governance_level="auto",
        )
        db.session.add(log)
        db.session.commit()

        return Result.ok(data={
            "old_status": old_status,
            "new_status": new_status,
            "next_transitions": statuses[statuses.index(new_status) + 1:]
            if new_status in statuses else [],
        })

    @staticmethod
    def get_pipeline_overview(tenant_id: int, entity_type: str) -> dict:
        """Get a pipeline overview showing counts per status."""
        definition = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type=entity_type, is_active=True
        ).first()
        if not definition:
            return {}

        statuses = definition.statuses or []
        pipeline = {}
        for status in statuses:
            count = Entity.query.filter_by(
                tenant_id=tenant_id, definition_id=definition.id,
                status=status, is_archived=False
            ).count()
            pipeline[status] = count

        return {"pipeline": pipeline, "total": sum(pipeline.values())}