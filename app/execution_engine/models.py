from datetime import datetime, timezone
from app import db


class Execution(db.Model):
    __tablename__ = "executions"

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, nullable=False)
    decision = db.Column(db.String(255))
    status = db.Column(db.String(50), default="pending")  # pending, running, completed

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class ExecutionLog(db.Model):
    """Execution history — every state change recorded as a time entry.

    Pure structural log: captures what changed, before and after, with no
    business interpretation. Non-actionable — observable history only.
    """

    __tablename__ = "execution_logs"

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, nullable=False)
    action_type = db.Column(db.String(255), nullable=False)
    payload = db.Column(db.JSON, default={})
    state_before = db.Column(db.JSON, default={})
    state_after = db.Column(db.JSON, default={})

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )