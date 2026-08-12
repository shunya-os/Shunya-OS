"""SHUNYA Customer Model — canonical customer ownership.

Extended for FDA13: relationship_id, tenant_id, lead_id, status, timestamps.
"""
from datetime import datetime, timezone
from app import db


class Customer(db.Model):
    __tablename__ = "customer"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    # FDA13: Link to canonical relationship
    relationship_id = db.Column(
        db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True, index=True
    )
    lead_id = db.Column(
        db.Integer, db.ForeignKey("leads.id"), nullable=True, index=True
    )
    tenant_id = db.Column(
        db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True
    )
    status = db.Column(db.String(30), default="active")
    # active, at_risk, churned, former

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "relationship_id": self.relationship_id,
            "lead_id": self.lead_id,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }