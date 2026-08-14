from datetime import datetime, timezone
from app import db

class Object(db.Model):
    __tablename__ = "objects"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column("object_type", db.String(100), nullable=False)
    state = db.Column(db.JSON, default={})
    context = db.Column(db.JSON, default={})
    tenant_id = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    @property
    def object_type(self):
        """Backward-compat alias for .type (ACTIVATION-03B)."""
        return self.type

    @object_type.setter
    def object_type(self, value):
        self.type = value
