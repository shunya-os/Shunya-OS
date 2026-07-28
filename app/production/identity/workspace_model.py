"""SHUNYA — Workspace SQLAlchemy model (Milestone X, D1).

A workspace belongs to exactly one organization (Tenant) and provides
an isolated collaboration space for users, objects, and conversations.
"""

import json
from datetime import datetime

from app import db
from sqlalchemy import Index


class Workspace(db.Model):
    """A workspace within an organization — isolated collaboration space."""
    __tablename__ = "workspaces"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, default="")
    settings = db.Column(db.Text, default="{}")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = db.relationship("Tenant", backref=db.backref("workspaces", lazy="dynamic"))

    __table_args__ = (
        Index("ix_workspaces_tenant_slug", "tenant_id", "slug", unique=True),
    )

    def __repr__(self):
        return f"<Workspace #{self.id} '{self.name}' org={self.tenant_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "settings": json.loads(self.settings) if self.settings else {},
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }