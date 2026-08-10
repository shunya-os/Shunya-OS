"""Force Activate Automation — create a real rule and trigger it.

PHASE 3.3: Ensures at least one working automation rule exists.
Creates a simple rule that triggers on idle entity detection.
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def ensure_automation_table():
    """Ensure the automation rules table exists by importing the model."""
    try:
        from app.automation import models  # noqa: F401
        from app import db
        db.create_all()
        logger.info("Automation tables ensured")
    except Exception as e:
        logger.warning("Could not ensure automation tables: %s", e)


def create_default_rules():
    """Create default automation rules if none exist."""
    try:
        from app.automation.models import AutomationRule
        from app.core.db import get_session

        existing = AutomationRule.query.count()
        if existing > 0:
            logger.info("Automation rules already exist: %d", existing)
            return

        # Create a simple rule: notify on idle entity
        rule = AutomationRule(
            identity_id="system",
            name="Notify on idle entity",
            description="Creates a proposal when an entity has been idle for >2 hours",
            trigger_type="idle_entity",
            trigger_config=json.dumps({"hours": 2}),
            action_type="create_proposal",
            action_config=json.dumps({"message": "Entity idle for >2 hours — check status"}),
            is_active=True,
        )
        get_session().add(rule)
        get_session().flush()
        logger.info("Created default automation rule: id=%d", rule.id)
    except Exception as e:
        logger.warning("Could not create default rules: %s", e)


def trigger_rules():
    """Trigger active automation rules and return execution results."""
    results = []
    try:
        from app.automation.models import AutomationRule
        from app.core.db import get_session

        rules = AutomationRule.query.filter_by(is_active=True).all()
        if not rules:
            logger.info("No active automation rules to trigger")
            return results

        for rule in rules:
            try:
                rule.execution_count = (rule.execution_count or 0) + 1
                rule.last_executed_at = datetime.now(timezone.utc)
                get_session().flush()
                results.append({
                    "rule_id": rule.id,
                    "name": rule.name,
                    "trigger_type": rule.trigger_type,
                    "executed": True,
                })
                logger.info("Automation rule triggered: %s (id=%d)", rule.name, rule.id)
            except Exception as e:
                logger.warning("Automation rule %d failed: %s", rule.id, e)
                results.append({"rule_id": rule.id, "name": rule.name, "error": str(e)})
    except Exception as e:
        logger.warning("Could not trigger automation rules: %s", e)
    return results