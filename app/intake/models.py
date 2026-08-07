from datetime import datetime, timezone
from app import db


class IntakeSignal(db.Model):
    __tablename__ = "intake_signals"

    id = db.Column(db.Integer, primary_key=True)

    # Raw input
    raw_input = db.Column(db.Text, nullable=False)

    # Input type: text / file / api / system
    input_type = db.Column(db.String(50), nullable=False)

    # Extracted structured data (JSON)
    structured_data = db.Column(db.JSON, nullable=True)

    # Status: received / processed
    status = db.Column(db.String(20), default="received")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
