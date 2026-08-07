from datetime import datetime, timezone
from app import db


class InboundEvent(db.Model):
    __tablename__ = "inbound_events"

    id = db.Column(db.Integer, primary_key=True)

    source = db.Column(db.String(100))  # whatsapp / email / webhook
    payload = db.Column(db.JSON)

    processed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))