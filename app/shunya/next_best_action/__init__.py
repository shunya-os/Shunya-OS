"""Next Best Action — context-aware, role-aware, priority-aware action engine.

Every screen, message, and workflow state should expose a recommended next action.
The system answers: What just happened? What should I do next? Why is this important?
"""
from typing import Optional, List
from datetime import datetime, timedelta
from app.shunya.foundation import NextAction, Priority
from app import db
from app.models import Entity, EntityDefinition, ActivityLog


class NextBestActionEngine:
    """Determines the most important next action for a user in context."""

    @staticmethod
    def get_for_user(tenant_id: int, user_id: int, role: str = "agent",
                     entity_id: Optional[int] = None) -> list:
        """Get priority-ordered next actions for a user."""
        actions = []

        # 1. Stale high-priority entities needing attention
        stale = NextBestActionEngine._get_stale_entities(tenant_id, role)
        actions.extend(stale)

        # 2. Pending approvals (for managers/admins)
        if role in ("admin", "manager"):
            approvals = NextBestActionEngine._get_pending_approvals(tenant_id)
            actions.extend(approvals)

        # 3. Recently created entities needing follow-up
        followups = NextBestActionEngine._get_followups(tenant_id, user_id)
        actions.extend(followups)

        # 4. Entity-specific actions if viewing a specific entity
        if entity_id:
            entity_actions = NextBestActionEngine._get_entity_actions(
                tenant_id, entity_id, role
            )
            actions.extend(entity_actions)

        # Sort by priority
        priority_order = {p.value: i for i, p in enumerate(Priority)}
        actions.sort(key=lambda a: priority_order.get(a.priority.value, 99))

        return actions[:10]

    @staticmethod
    def _get_stale_entities(tenant_id: int, role: str) -> list:
        """Find entities that haven't been updated and need attention."""
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        actions = []

        entities = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "pending", "proposal", "negotiation"]),
            Entity.updated_at < five_days_ago,
        ).limit(5).all()

        for e in entities:
            def_label = e.definition.label if e.definition else "Record"
            priority = Priority.HIGH if e.data.get("budget", 0) and float(e.data.get("budget", 0)) > 100000 else Priority.MEDIUM
            actions.append(NextAction(
                title=f"Follow up on {def_label}",
                description=f"{e.display_name} needs attention (status: {e.status})",
                action_type="view",
                target_url=f"/entities/{e.definition.type if e.definition else 'entity'}/{e.id}",
                priority=priority,
                reason=f"No activity in 5+ days. Risk of losing {def_label.lower()}.",
                expected_outcome="Re-engage and move forward",
                entity_id=e.id,
                entity_type=e.definition.type if e.definition else "",
            ))

        return actions

    @staticmethod
    def _get_pending_approvals(tenant_id: int) -> list:
        """Find actions pending governance approval."""
        from app.models import ActivityLog
        approvals = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.governance_level == "govern",
            ActivityLog.created_at >= datetime.utcnow() - timedelta(days=3),
        ).limit(5).all()

        return [NextAction(
            title=f"Approval needed: {a.action}",
            description=a.detail[:200] if a.detail else "Review pending action",
            action_type="approve",
            target_url="#",
            priority=Priority.HIGH,
            reason="Blocking further work until approved",
            expected_outcome="Unblock workflow",
        ) for a in approvals]

    @staticmethod
    def _get_followups(tenant_id: int, user_id: int) -> list:
        """Find recently created entities that need a first action."""
        yesterday = datetime.utcnow() - timedelta(days=1)
        entities = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status == "new",
            Entity.created_at >= yesterday,
        ).limit(5).all()

        return [NextAction(
            title=f"New {e.definition.label if e.definition else 'record'}",
            description=f"{e.display_name} just came in",
            action_type="view",
            target_url=f"/entities/{e.definition.type if e.definition else 'entity'}/{e.id}",
            priority=Priority.HIGH,
            reason="New leads need fast response",
            expected_outcome="First contact within SLA",
            entity_id=e.id,
            entity_type=e.definition.type if e.definition else "",
        ) for e in entities]

    @staticmethod
    def _get_entity_actions(tenant_id: int, entity_id: int, role: str) -> list:
        """Get actions specific to a single entity context."""
        entity = db.session.get(Entity, entity_id)
        if not entity or entity.tenant_id != tenant_id:
            return []

        actions = []

        # If status is new, suggest moving to next stage
        if entity.status == "new" and entity.definition:
            statuses = entity.definition.statuses or []
            if len(statuses) > 1:
                actions.append(NextAction(
                    title=f"Move to {statuses[1]}",
                    description=f"Update status from {entity.status} to {statuses[1]}",
                    action_type="edit",
                    target_url=f"/entities/{entity.definition.type}/{entity.id}/edit",
                    priority=Priority.MEDIUM,
                    reason="Moving forward in the pipeline",
                    expected_outcome="Progress the workflow",
                    entity_id=entity.id,
                    entity_type=entity.definition.type,
                ))

        # If budget is high, suggest manager attention
        budget = entity.data.get("budget", 0)
        if budget and float(budget) > 200000:
            actions.append(NextAction(
                title="High-value review recommended",
                description=f"Budget ₹{float(budget):,.0f} — may need senior review",
                action_type="view",
                target_url=f"/entities/{entity.definition.type if entity.definition else 'entity'}/{entity.id}",
                priority=Priority.HIGH,
                reason="High-value deals need careful handling",
                expected_outcome="Proper review and approval",
                entity_id=entity.id,
                entity_type=entity.definition.type if entity.definition else "",
            ))

        return actions