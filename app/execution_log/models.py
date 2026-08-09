"""ExecutionLog — structured execution trace, single source of truth."""

from datetime import datetime, timezone

from app import db


class ExecutionLog(db.Model):
    __tablename__ = "act_execution_logs"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey("objects.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    payload = db.Column(db.JSON, default=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "object_id": self.object_id,
            "timestamp": self.timestamp.replace(tzinfo=timezone.utc).isoformat(),
            "event_type": self.event_type,
            "payload": self.payload or {},
        }


def log_execution(object_id: int, event_type: str, payload: dict = None):
    """Create an ExecutionLog entry and flush to DB."""
    entry = ExecutionLog(
        object_id=object_id,
        event_type=event_type,
        payload=payload or {},
    )
    db.session.add(entry)
    db.session.flush()