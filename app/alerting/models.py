"""Alert event persistence — the durable audit trail for E1 alerting."""
from datetime import datetime

from app import db


class AlertEvent(db.Model):
    """A single alert lifecycle: fired → active → recovered.

    Cross-worker dedup uses the DB (gunicorn sync workers each hold their own
    memory): the engine consults the latest event per (rule, alert_key) before
    firing, and marks recovery against persisted rows. Delivery state is
    truthful — pending | delivered | failed | unconfigured — so a delivery
    failure is observable, not silent.
    """

    __tablename__ = "sh_alert_events"

    id = db.Column(db.Integer, primary_key=True)
    rule = db.Column(db.String(50), nullable=False, index=True)
    alert_key = db.Column(db.String(200), nullable=False, index=True)
    severity = db.Column(db.String(10), default="P2")
    status = db.Column(db.String(20), default="active", index=True)  # active | recovered
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, default="")
    first_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    recovered_at = db.Column(db.DateTime, nullable=True)
    occurrences = db.Column(db.Integer, default=0, nullable=False)
    delivery_state = db.Column(db.String(20), default="pending")  # pending | delivered | failed | unconfigured
    delivered_at = db.Column(db.DateTime, nullable=True)
    details = db.Column(db.JSON, default=dict)