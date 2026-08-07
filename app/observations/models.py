from datetime import datetime, timezone
from app import db


class Observation(db.Model):
    __tablename__ = "commitment_observations"

    id = db.Column(db.Integer, primary_key=True)

    commitment_id = db.Column(
        db.Integer,
        db.ForeignKey("commitments.id"),
        nullable=False
    )

    entity_id = db.Column(db.Integer, nullable=True, index=True)

    observed_value = db.Column(db.JSON, nullable=False)
    expected_value = db.Column(db.JSON, nullable=True)

    context = db.Column(db.JSON, nullable=True)

    status = db.Column(
        db.String(50),
        default="recorded"  # recorded → matched → deviated
    )

    recorded_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )