"""SHUNYA — MFA / 2FA Models (Milestone X, D2.4).

Persistent MFA state for TOTP-based two-factor authentication.
"""

from __future__ import annotations
from datetime import datetime
from app import db


class MFAConfig(db.Model):
    """Per-user MFA configuration stored in the database.

    Unlike the in-memory MFA state, this persists across server restarts.
    """

    __tablename__ = "shunya_mfa_configs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("team_members.id"), nullable=False, unique=True, index=True)
    secret = db.Column(db.String(64), nullable=False)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    recovery_codes = db.Column(db.JSON, default=list, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "enabled": self.enabled,
            "recovery_codes_count": len(self.recovery_codes or []),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }