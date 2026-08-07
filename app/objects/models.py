from datetime import datetime, timezone
from app import db

class Object(db.Model):
    __tablename__ = "objects"

    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String(100), nullable=False)
    state = db.Column(db.JSON, default={})
    context = db.Column(db.JSON, default={})

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
