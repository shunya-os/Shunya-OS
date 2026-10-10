"""Action Classification Registry — READ/ANALYZE/CREATE/UPDATE/DELETE/EXECUTE.

Maps user intents to action classification levels so the runtime can apply
appropriate RBAC gates. Each action class carries the minimum permission
required to perform it.

G3 Phase 2.5 convergence: every AI entry point classifies the requested
action before dispatch, and the RBAC gate (Phase 2.6) enforces the
minimum required permission.
"""

from __future__ import annotations

import enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ActionClass(str, enum.Enum):
    """Classification of what the user wants to do with data."""

    READ = "read"           # View / retrieve information
    ANALYZE = "analyze"     # Process / derive insights (no persistence)
    CREATE = "create"       # Create a new record
    UPDATE = "update"       # Modify an existing record
    DELETE = "delete"       # Remove / archive a record
    EXECUTE = "execute"     # Perform an action (may cover multiple records)


# Minimum permission required for each action class.
# The permission system (app/authz/) maps these to domain-specific keys.
ACTION_CLASS_PERMISSIONS: dict[ActionClass, str] = {
    ActionClass.READ: "org.view",
    ActionClass.ANALYZE: "org.view",
    ActionClass.CREATE: "rel.create",
    ActionClass.UPDATE: "rel.edit",
    ActionClass.DELETE: "rel.delete",
    ActionClass.EXECUTE: "rel.create",
}


def classify_action(intent: str, object_type: str = "") -> ActionClass:
    """Classify a user-facing intent string into an ActionClass.

    Uses keyword/pattern matching on the intent. The classification is
    deterministic — no AI model involved.

    Args:
        intent: The user's stated intent or action description.
        object_type: The type of object the action targets.

    Returns:
        ActionClass: the classified action level.
    """
    if not intent:
        return ActionClass.READ

    lowered = intent.lower()

    # DELETE checks first (higher specificity)
    if any(word in lowered for word in
           ["delete", "remove", "trash", "archive", "purge", "erase"]):
        return ActionClass.DELETE

    # CREATE checks
    if any(word in lowered for word in
           ["create", "add", "new", "make", "build", "generate", "insert",
            "register", "onboard"]):
        return ActionClass.CREATE

    # UPDATE checks
    if any(word in lowered for word in
           ["update", "edit", "modify", "change", "rename", "correct",
            "adjust", "set", "assign", "mark"]):
        return ActionClass.UPDATE

    # EXECUTE checks
    if any(word in lowered for word in
           ["execute", "run", "send", "approve", "confirm", "submit",
            "publish", "start", "stop", "trigger"]):
        return ActionClass.EXECUTE

    # ANALYZE checks
    if any(word in lowered for word in
           ["analyze", "summarize", "compare", "investigate", "research",
            "explain", "find", "search", "lookup", "insight", "trend",
            "forecast", "predict"]):
        return ActionClass.ANALYZE

    # Default: READ
    return ActionClass.READ


def required_permission(action_class: ActionClass, object_type: str = "") -> str:
    """Resolve the minimum permission key for an action class.

    Domain-specific overrides can be added per object_type. The default
    mapping uses ACTION_CLASS_PERMISSIONS.

    Args:
        action_class: The classified action.
        object_type: Optional domain override (e.g. "finance", "proposal").

    Returns:
        Permission key string (e.g. "rel.create", "finance.view").
    """
    # Domain-specific overrides
    type_prefix = {
        "proposal": "proposal",
        "finance": "finance",
        "invoice": "finance",
        "knowledge": "knowledge",
        "task": "task",
        "document": "knowledge",
        "campaign": "marketing",
    }

    prefix = type_prefix.get(object_type.lower(), "rel")

    perms = {
        ActionClass.READ: f"{prefix}.view",
        ActionClass.ANALYZE: f"{prefix}.view",
        ActionClass.CREATE: f"{prefix}.create",
        ActionClass.UPDATE: f"{prefix}.edit",
        ActionClass.DELETE: f"{prefix}.delete",
        ActionClass.EXECUTE: f"{prefix}.create",
    }

    return perms.get(action_class, ACTION_CLASS_PERMISSIONS.get(action_class, "org.view"))