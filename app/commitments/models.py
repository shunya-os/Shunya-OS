from datetime import datetime, timezone
from app import db


class Commitment(db.Model):
    """A commitment represents a real-world promise to complete something.

    Pure structure:
    - what needs to be done
    - who owns it
    - when it is due
    - current status
    """

    __tablename__ = "commitments"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    owner = db.Column(db.String(100), nullable=True)

    due_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(
        db.String(50),
        default="pending"  # pending → in_progress → completed → failed
    )

    meta = db.Column(db.JSON, default={})

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )