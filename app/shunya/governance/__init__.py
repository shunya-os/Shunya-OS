"""Shunya OS — Governance Tiers (Draft / Auto / Govern).

Every AI-initiated action passes through governance:
- Draft: needs user confirmation before execution
- Auto: executes immediately, logged, reversible
- Govern: needs second-user approval (admin/manager)
"""
from enum import Enum
from typing import Optional
from flask import g
from app import db
from app.models import GovernanceLevel, ActivityLog, TeamMember


class ActionType(str, Enum):
    CREATE_ENTITY = "create_entity"
    UPDATE_ENTITY = "update_entity"
    DELETE_ENTITY = "delete_entity"
    CHANGE_STATUS = "change_status"
    SEND_MESSAGE = "send_message"
    GENERATE_INVOICE = "generate_invoice"
    CREATE_MODULE = "create_module"
    MODIFY_RULES = "modify_rules"
    DELETE_PERMANENT = "delete_permanent"


# Rules: which actions require what governance level
GOVERNANCE_RULES = {
    ActionType.CREATE_ENTITY: GovernanceLevel.AUTO,
    ActionType.UPDATE_ENTITY: GovernanceLevel.AUTO,
    ActionType.DELETE_ENTITY: GovernanceLevel.DRAFT,
    ActionType.CHANGE_STATUS: GovernanceLevel.AUTO,
    ActionType.SEND_MESSAGE: GovernanceLevel.DRAFT,
    ActionType.GENERATE_INVOICE: GovernanceLevel.AUTO,
    ActionType.CREATE_MODULE: GovernanceLevel.GOVERN,
    ActionType.MODIFY_RULES: GovernanceLevel.GOVERN,
    ActionType.DELETE_PERMANENT: GovernanceLevel.GOVERN,
}

# Higher roles can override to lower governance
ROLE_AUTO_OVERRIDE = {"admin", "manager"}
ROLE_GOVERN_OVERRIDE = {"admin"}


class GovernanceEngine:
    """Determines what level of governance an action needs."""

    @staticmethod
    def get_level(action: ActionType, user_role: str = "agent") -> GovernanceLevel:
        """Determine the governance level for an action by a given user."""
        default_level = GOVERNANCE_RULES.get(action, GovernanceLevel.GOVERN)

        # Role-based overrides
        if default_level == GovernanceLevel.GOVERN and user_role in ROLE_GOVERN_OVERRIDE:
            return GovernanceLevel.AUTO
        if default_level == GovernanceLevel.DRAFT and user_role in ROLE_AUTO_OVERRIDE:
            return GovernanceLevel.AUTO

        return default_level

    @staticmethod
    def execute_or_draft(action: ActionType, entity_id: Optional[int],
                         details: str, user_id: int, tenant_id: int,
                         execute_fn, user_role: str = "agent"):
        """Execute an action or create a draft based on governance level."""
        level = GovernanceEngine.get_level(action, user_role)

        if level == GovernanceLevel.AUTO:
            result = execute_fn()
            _log_action(tenant_id, entity_id, user_id, action.value, details, "auto")
            return {"status": "auto_executed", "level": "auto", "result": result}

        elif level == GovernanceLevel.DRAFT:
            _log_action(tenant_id, entity_id, user_id, action.value, f"DRAFT: {details}", "draft")
            return {
                "status": "draft_created",
                "level": "draft",
                "message": "Review and confirm to execute",
                "details": details,
                "execute": execute_fn,  # Caller invokes this on confirmation
            }

        else:  # GOVERN
            _log_action(tenant_id, entity_id, user_id, action.value, f"PENDING: {details}", "govern")
            return {
                "status": "needs_approval",
                "level": "govern",
                "message": "Requires admin/manager approval",
                "details": details,
                "execute": execute_fn,
            }

    @staticmethod
    def get_governance_level(action_type_name, user_role, tenant_id=None) -> 'GovernanceLevel':
        """Get the governance level for a given action type and user role.
        
        Admins get AUTO for most actions.
        Agents get the configured level from GOVERNANCE_RULES.
        """
        # action_type_name is a string like "update_status", "send_message"
        action_map = {
            "update_status": ActionType.CHANGE_STATUS,
            "send_message": ActionType.SEND_MESSAGE,
            "create_entity": ActionType.CREATE_ENTITY,
            "delete_entity": ActionType.DELETE_ENTITY,
            "archive_entity": ActionType.DELETE_ENTITY,
            "send_notification": ActionType.SEND_MESSAGE,
            "assign_entity": ActionType.CHANGE_STATUS,
        }
        
        gov_action = action_map.get(action_type_name, ActionType.UPDATE_ENTITY)
        level = GOVERNANCE_RULES.get(gov_action, GovernanceLevel.DRAFT)
        
        if user_role == "admin":
            return GovernanceLevel.AUTO
        
        return level

    @staticmethod
    def check_policy(action_type_name, user_role, tenant_id, params=None) -> bool:
        """Check if an action is allowed by policy for this user role."""
        role_hierarchy = {"admin": 3, "manager": 2, "agent": 1, "viewer": 0}
        user_level = role_hierarchy.get(user_role, 0)
        
        action_requirements = {
            "delete_permanent": 3,
            "modify_rules": 3,
            "create_module": 2,
            "delete_entity": 1,
            "archive_entity": 1,
        }
        
        required = action_requirements.get(action_type_name, 0)
        return user_level >= required


def _log_action(tenant_id, entity_id, user_id, action, detail, governance_level):
    log = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity_id,
        user_id=user_id,
        action=action,
        detail=detail[:500],
        governance_level=governance_level,
    )
    db.session.add(log)
    db.session.commit()