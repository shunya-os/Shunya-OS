"""SHUNYA M7 — Automation Models.

Persistence for automation rules and execution history.
"""
from datetime import datetime

from app import db
from sqlalchemy import Index, Text


# ---------------------------------------------------------------------------
# Automation Rule
# ---------------------------------------------------------------------------

class AutomationRule(db.Model):
    """An automation rule: when trigger conditions match, execute actions.

    trigger_config: JSON with trigger type, conditions, filters.
    action_config: JSON with action type, parameters, targets.
    """

    __tablename__ = "m7_automation_rules"
    __table_args__ = (
        Index("ix_m7_rule_identity", "identity_id", "is_active"),
        Index("ix_m7_rule_type", "trigger_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    space_id = db.Column(db.String(64), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(Text, default="")
    trigger_type = db.Column(db.String(40), nullable=False)
    # entity_created, entity_updated, status_changed, schedule, conversation_new
    trigger_config = db.Column(Text, default="{}")
    # JSON: {"entity_type": "Lead", "field": "status", "from": "new", "to": "qualified"}
    action_type = db.Column(db.String(40), nullable=False)
    # notify, create_object, update_object, send_email, webhook
    action_config = db.Column(Text, default="{}")
    # JSON: {"notification_type": "...", "title": "...", "object_type": "Task", ...}
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    execution_count = db.Column(db.Integer, default=0)
    last_executed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "space_id": self.space_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "trigger_config": self.trigger_config,
            "action_type": self.action_type,
            "action_config": self.action_config,
            "is_active": self.is_active,
            "execution_count": self.execution_count,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Automation Execution Log
# ---------------------------------------------------------------------------

class AutomationLog(db.Model):
    """Immutable log of every automation rule execution."""

    __tablename__ = "m7_automation_logs"
    __table_args__ = (
        Index("ix_m7_log_rule", "rule_id", "created_at"),
        Index("ix_m7_log_object", "trigger_object_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey("m7_automation_rules.id"), nullable=False)
    rule_name = db.Column(db.String(255), default="")
    trigger_type = db.Column(db.String(40), default="")
    trigger_object_id = db.Column(db.String(64), nullable=True)
    trigger_summary = db.Column(db.String(500), default="")
    action_type = db.Column(db.String(40), default="")
    action_summary = db.Column(db.String(500), default="")
    status = db.Column(db.String(20), default="success")
    # success, failed, skipped
    error_message = db.Column(Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    rule = db.relationship("AutomationRule", backref="execution_logs", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "trigger_type": self.trigger_type,
            "trigger_object_id": self.trigger_object_id,
            "trigger_summary": self.trigger_summary,
            "action_type": self.action_type,
            "action_summary": self.action_summary,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Workflow Template (pre-built automation patterns)
# ---------------------------------------------------------------------------

WORKFLOW_TEMPLATES = [
    {
        "id": "lead_qualified_notify",
        "name": "Lead Qualified → Notify Team",
        "description": "When a lead status changes to 'Qualified', send an in-app notification",
        "trigger_type": "status_changed",
        "trigger_config_template": {"entity_type": "Lead", "field": "status", "to": "qualified"},
        "action_type": "notify",
        "action_config_template": {
            "notification_type": "automation_fired",
            "title": "Lead qualified: {object_name}",
            "body": "Lead {object_name} has been marked as qualified.",
        },
    },
    {
        "id": "task_overdue_remind",
        "name": "Task Overdue → Reminder",
        "description": "When a task becomes overdue, send a reminder notification",
        "trigger_type": "status_changed",
        "trigger_config_template": {"entity_type": "Task", "field": "status", "to": "overdue"},
        "action_type": "notify",
        "action_config_template": {
            "notification_type": "automation_fired",
            "title": "Task overdue: {object_name}",
            "body": "The task {object_name} is now overdue.",
        },
    },
    {
        "id": "conversation_unanswered",
        "name": "Unanswered Conversation → Follow-up",
        "description": "When a conversation has unanswered human messages for 24h, create a follow-up task",
        "trigger_type": "conversation_new",
        "trigger_config_template": {"min_unanswered_hours": 24},
        "action_type": "create_object",
        "action_config_template": {
            "object_type": "Task",
            "name": "Follow-up: {object_name}",
            "content": "Automatic follow-up task for unanswered conversation.",
        },
    },
]