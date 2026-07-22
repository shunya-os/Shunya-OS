"""SHUNYA — Authorization Middleware & Permissions (Milestone X, D3).

Enforces role-based permissions, organization boundaries, and Governance
Engine evaluation across all API routes.

No authorization logic in the frontend — all enforcement is server-side.
"""

from __future__ import annotations

import functools
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from flask import g, request, jsonify
from werkzeug.exceptions import Forbidden

from app.auth import TeamMember, UserRole as AuthUserRole
from app import db


# =========================================================================
# Permission Definitions
# =========================================================================

class Action(str, Enum):
    """Standard CRUD + administrative actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    APPROVE = "approve"
    ADMIN = "admin"


Resource = str  # e.g. "org", "workspace", "user", "invitation"


# =========================================================================
# Permission Registry
# =========================================================================

# Default permission map: role -> resource -> allowed actions
# Inheritance: admin includes manager, manager includes agent
_PERMISSION_MAP: Dict[str, Dict[str, Set[str]]] = {
    "admin": {
        "org": {"create", "read", "update", "delete", "admin"},
        "workspace": {"create", "read", "update", "delete", "list"},
        "user": {"create", "read", "update", "delete", "list", "admin"},
        "invitation": {"create", "read", "delete", "list"},
        "settings": {"read", "update", "admin"},
    },
    "manager": {
        "org": {"read", "update"},
        "workspace": {"create", "read", "update", "list"},
        "user": {"create", "read", "update", "list"},
        "invitation": {"create", "read", "list"},
        "settings": {"read"},
    },
    "agent": {
        "org": {"read"},
        "workspace": {"read"},
        "user": {"read"},
        "settings": {"read"},
    },
}


def get_permitted_actions(role: str, resource: str) -> Set[str]:
    """Get permitted actions for a role on a resource.

    Includes inherited permissions from parent roles.
    """
    actions: Set[str] = set()

    # Role hierarchy (admin > manager > agent)
    roles_to_check = []
    if role == "admin":
        roles_to_check = ["admin", "manager", "agent"]
    elif role == "manager":
        roles_to_check = ["manager", "agent"]
    else:
        roles_to_check = [role]

    for r in roles_to_check:
        resource_perms = _PERMISSION_MAP.get(r, {})
        actions.update(resource_perms.get(resource, set()))

    return actions


def check_permission(user: TeamMember, resource: str, action: str) -> bool:
    """Check if a user has permission to perform an action on a resource."""
    permitted = get_permitted_actions(user.role, resource)
    return action in permitted


# =========================================================================
# Authorization Decorator
# =========================================================================

def require_permission(resource: str, action: str):
    """Decorator: require a specific permission on a resource.

    Usage:
        @require_permission("workspace", "create")
        def create_workspace(org_id):
            ...
    """
    def decorator(view: Callable) -> Callable:
        @functools.wraps(view)
        def wrapped_view(*args: Any, **kwargs: Any) -> Any:
            user: Optional[TeamMember] = getattr(g, "user", None)
            if not user:
                return jsonify({"error": "Authentication required"}), 401

            if not check_permission(user, resource, action):
                return jsonify({
                    "error": "Forbidden",
                    "detail": f"Missing required permission: {action} on {resource}",
                }), 403

            return view(*args, **kwargs)
        return wrapped_view
    return decorator


# =========================================================================
# Organization Boundary Middleware
# =========================================================================

def enforce_org_boundary():
    """Middleware to ensure cross-org data isolation.

    Call in before_request. Sets g.current_org_id from session.
    All queries should filter by g.current_org_id.
    """
    from flask import session

    org_id = session.get("current_org_id")
    if org_id:
        from app.tenant import Tenant
        org = db.session.get(Tenant, org_id)
        if org and org.is_active:
            g.current_org_id = org.id
            return

    g.current_org_id = None


# =========================================================================
# Governance Engine Integration
# =========================================================================

def evaluate_governance(action_type: str, context: dict) -> dict:
    """Evaluate a proposed action against the Governance Engine.

    Args:
        action_type: Type of action (e.g. "data_mutation", "financial", "admin")
        context: Context dict with action details

    Returns:
        {"approved": bool, "verdict": str, "violations": list}
    """
    try:
        from app.shunya.governance_engine import GovernanceEngine
        from app.shunya.governance_engine.models import (
            GovernanceInput, ActionType,
        )

        # Map string to ActionType enum
        at_map = {
            "data_mutation": ActionType.DATA_MUTATION,
            "financial": ActionType.FINANCIAL,
            "admin": ActionType.ADMIN,
            "communication": ActionType.COMMUNICATION,
            "read": ActionType.READ,
        }
        action_type_enum = at_map.get(action_type, ActionType.READ)

        engine = GovernanceEngine()
        gov_input = GovernanceInput(
            action_type=action_type_enum,
            actor_id=str(context.get("user_id", "")),
            actor_type="user",
            tenant_id=context.get("tenant_id", 0),
            resource_type=context.get("resource_type", ""),
            resource_id=context.get("resource_id", ""),
            payload=context.get("payload", {}),
        )
        verdict = engine.evaluate(gov_input)

        return {
            "approved": verdict.decision.value == "approved",
            "verdict": verdict.decision.value,
            "violations": [v.to_dict() for v in verdict.violations],
        }
    except ImportError:
        # Governance Engine not available — allow by default
        return {"approved": True, "verdict": "approved", "violations": []}
    except Exception as e:
        return {"approved": False, "verdict": "error", "violations": [str(e)]}


def require_governance(action_type: str):
    """Decorator: require Governance Engine approval before executing an action.

    Usage:
        @require_governance("data_mutation")
        def update_sensitive_data():
            ...
    """
    def decorator(view: Callable) -> Callable:
        @functools.wraps(view)
        def wrapped_view(*args: Any, **kwargs: Any) -> Any:
            user: Optional[TeamMember] = getattr(g, "user", None)
            if not user:
                return jsonify({"error": "Authentication required"}), 401

            context = {
                "user_id": str(user.id),
                "user_role": user.role,
                "tenant_id": getattr(g, "current_org_id", None),
                "resource_type": request.path,
                "resource_id": kwargs.get("org_id") or kwargs.get("ws_id", ""),
                "payload": request.get_json(silent=True) or {},
            }
            result = evaluate_governance(action_type, context)

            if not result["approved"]:
                return jsonify({
                    "error": "Governance policy violation",
                    "detail": result["violations"],
                }), 403

            return view(*args, **kwargs)
        return wrapped_view
    return decorator