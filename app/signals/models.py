from datetime import datetime, timezone
from app import db


class Signal(db.Model):
    __tablename__ = "signals"

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, nullable=False, index=True)
    type = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))