"""SHUNYA M7 — Automation Service and Trigger Evaluation Engine.

Handles rule CRUD, trigger evaluation, action dispatch, and execution logging.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app import db
from app.automation.models import AutomationLog, AutomationRule, WORKFLOW_TEMPLATES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rule CRUD
# ---------------------------------------------------------------------------

def create_rule(
    identity_id: str,
    name: str,
    trigger_type: str,
    trigger_config: dict[str, Any],
    action_type: str,
    action_config: dict[str, Any],
    description: str = "",
    space_id: str | None = None,
) -> dict[str, Any]:
    """Create a new automation rule."""
    rule = AutomationRule(
        identity_id=identity_id,
        space_id=space_id,
        name=name,
        description=description,
        trigger_type=trigger_type,
        trigger_config=json.dumps(trigger_config),
        action_type=action_type,
        action_config=json.dumps(action_config),
    )
    db.session.add(rule)
    db.session.commit()
    return rule.to_dict()


def get_rules(identity_id: str, include_inactive: bool = False) -> list[dict[str, Any]]:
    """Get all rules for an identity."""
    query = AutomationRule.query.filter_by(identity_id=identity_id)
    if not include_inactive:
        query = query.filter_by(is_active=True)
    rules = query.order_by(AutomationRule.created_at.desc()).all()
    return [r.to_dict() for r in rules]


def get_rule(rule_id: int) -> dict[str, Any] | None:
    """Get a single rule by ID."""
    rule = AutomationRule.query.get(rule_id)
    return rule.to_dict() if rule else None


def update_rule(rule_id: int, **kwargs) -> dict[str, Any] | None:
    """Update a rule. Only provided fields are updated."""
    rule = AutomationRule.query.get(rule_id)
    if not rule:
        return None

    for key, value in kwargs.items():
        if hasattr(rule, key) and key not in ("id", "identity_id", "created_at"):
            if key in ("trigger_config", "action_config") and isinstance(value, dict):
                value = json.dumps(value)
            setattr(rule, key, value)

    db.session.commit()
    return rule.to_dict()


def toggle_rule(rule_id: int, is_active: bool) -> dict[str, Any] | None:
    """Activate or deactivate a rule."""
    return update_rule(rule_id=rule_id, is_active=is_active)


def delete_rule(rule_id: int) -> bool:
    """Delete a rule and its execution logs."""
    rule = AutomationRule.query.get(rule_id)
    if not rule:
        return False
    AutomationLog.query.filter_by(rule_id=rule_id).delete()
    db.session.delete(rule)
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Execution Log
# ---------------------------------------------------------------------------

def get_execution_logs(rule_id: int | None = None,
                       identity_id: str | None = None,
                       limit: int = 50) -> list[dict[str, Any]]:
    """Get automation execution logs."""
    query = AutomationLog.query
    if rule_id:
        query = query.filter_by(rule_id=rule_id)
    if identity_id:
        query = query.join(AutomationRule).filter(
            AutomationRule.identity_id == identity_id
        )
    logs = query.order_by(AutomationLog.created_at.desc()).limit(limit).all()
    return [l.to_dict() for l in logs]


# ---------------------------------------------------------------------------
# Trigger Evaluation Engine
# ---------------------------------------------------------------------------

def evaluate_triggers(trigger_type: str,
                      trigger_object_id: str,
                      trigger_summary: str,
                      context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Evaluate all active rules matching a trigger type.

    Returns list of execution results for matched rules.

    Args:
        trigger_type: The type of trigger (entity_created, status_changed, etc.)
        trigger_object_id: The object that triggered the event.
        trigger_summary: Human-readable summary of what triggered it.
        context: Additional context for trigger evaluation (field changes, etc.).
    """
    results: list[dict[str, Any]] = []
    context = context or {}

    rules = AutomationRule.query.filter_by(
        is_active=True
    ).all()

    for rule in rules:
        if rule.trigger_type != trigger_type:
            continue

        try:
            trigger_cfg = json.loads(rule.trigger_config) if isinstance(rule.trigger_config, str) else rule.trigger_config
            action_cfg = json.loads(rule.action_config) if isinstance(rule.action_config, str) else rule.action_config
        except (json.JSONDecodeError, TypeError):
            continue

        # Evaluate conditions
        if not _evaluate_conditions(trigger_cfg, trigger_type, context):
            continue

        # Execute action
        result = _execute_action(
            rule=rule,
            action_type=rule.action_type,
            action_cfg=action_cfg,
            trigger_object_id=trigger_object_id,
            trigger_summary=trigger_summary,
            context=context,
        )
        results.append(result)

    return results


def _evaluate_conditions(trigger_cfg: dict, trigger_type: str,
                         context: dict[str, Any]) -> bool:
    """Evaluate trigger conditions against context.

    Returns True if all conditions match.
    """
    # Entity type filter
    entity_type = trigger_cfg.get("entity_type")
    if entity_type:
        actual_type = context.get("object_type", "")
        if actual_type.lower() != entity_type.lower():
            return False

    # Status change conditions
    if trigger_type == "status_changed":
        from_status = trigger_cfg.get("from")
        to_status = trigger_cfg.get("to")
        old_status = context.get("old_status")
        new_status = context.get("new_status")

        if from_status and old_status and old_status.lower() != from_status.lower():
            # Status changed FROM something specific — check
            return False
        if to_status and new_status and new_status.lower() != to_status.lower():
            return False

    # Schedule conditions handled by the caller

    return True


def _execute_action(rule: AutomationRule,
                    action_type: str,
                    action_cfg: dict[str, Any],
                    trigger_object_id: str,
                    trigger_summary: str,
                    context: dict[str, Any]) -> dict[str, Any]:
    """Execute a rule's action and log the result."""
    result = {"rule_id": rule.id, "action_type": action_type, "status": "success"}
    object_name = context.get("object_name", trigger_object_id)

    try:
        if action_type == "notify":
            from app.integration.service import create_notification

            title = action_cfg.get("title", "Automation triggered").format(
                object_name=object_name, object_id=trigger_object_id
            )
            body = action_cfg.get("body", "").format(
                object_name=object_name, object_id=trigger_object_id
            )

            create_notification(
                identity_id=rule.identity_id,
                notification_type=action_cfg.get("notification_type", "automation_fired"),
                title=title,
                body=body,
                object_id=trigger_object_id,
                space_id=rule.space_id,
            )
            result["action_summary"] = f"Notification sent: {title}"

        elif action_type == "create_object":
            from app.founder.models import FounderConversation, FounderObject, FounderSpace

            # Find a space for this identity
            space = FounderSpace.query.filter_by(
                identity_id=rule.identity_id, status="active"
            ).first()
            if not space:
                raise ValueError("No active space found for object creation")

            import uuid
            obj_id = f"auto_{uuid.uuid4().hex[:16]}"
            name = action_cfg.get("name", "Automated object").format(
                object_name=object_name, object_id=trigger_object_id
            )
            content = action_cfg.get("content", "").format(
                object_name=object_name, object_id=trigger_object_id
            )

            obj = FounderObject(
                object_id=obj_id,
                space_id=space.space_id,
                object_type=action_cfg.get("object_type", "Task"),
                name=name,
                content=content,
                created_by=rule.identity_id,
            )
            db.session.add(obj)
            result["action_summary"] = f"Object created: {name} ({obj_id})"

        else:
            result["status"] = "skipped"
            result["action_summary"] = f"Unknown action type: {action_type}"

        # Update rule execution count
        rule.execution_count = (rule.execution_count or 0) + 1
        rule.last_executed_at = datetime.now(timezone.utc)

        # Log execution
        log = AutomationLog(
            rule_id=rule.id,
            rule_name=rule.name,
            trigger_type=rule.trigger_type,
            trigger_object_id=trigger_object_id,
            trigger_summary=trigger_summary,
            action_type=action_type,
            action_summary=result.get("action_summary", ""),
            status=result["status"],
        )
        db.session.add(log)
        db.session.commit()

    except Exception as e:
        logger.error(f"Automation execution error: {e}")
        db.session.rollback()
        result["status"] = "failed"
        result["error_message"] = str(e)

        # Log failure
        log = AutomationLog(
            rule_id=rule.id,
            rule_name=rule.name,
            trigger_type=rule.trigger_type,
            trigger_object_id=trigger_object_id,
            trigger_summary=trigger_summary,
            action_type=action_type,
            action_summary="",
            status="failed",
            error_message=str(e),
        )
        db.session.add(log)
        db.session.commit()

    return result


# ---------------------------------------------------------------------------
# Workflow templates
# ---------------------------------------------------------------------------

def get_workflow_templates() -> list[dict[str, Any]]:
    """Return available workflow templates."""
    return WORKFLOW_TEMPLATES


def create_from_template(identity_id: str, template_id: str,
                         overrides: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Create a rule from a workflow template with optional overrides."""
    template = next((t for t in WORKFLOW_TEMPLATES if t["id"] == template_id), None)
    if not template:
        return None

    trigger_config = dict(template["trigger_config_template"])
    action_config = dict(template["action_config_template"])

    if overrides:
        trigger_config.update(overrides.get("trigger_config", {}))
        action_config.update(overrides.get("action_config", {}))

    return create_rule(
        identity_id=identity_id,
        name=template["name"],
        description=template["description"],
        trigger_type=template["trigger_type"],
        trigger_config=trigger_config,
        action_type=template["action_type"],
        action_config=action_config,
    )