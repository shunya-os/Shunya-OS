"""UserProfile model — per-user profile and preferences."""

from __future__ import annotations

from datetime import datetime, timezone

from app import db


class UserProfile(db.Model):
    """Per-user profile with preferences and settings.

    One row per identity_id (PK). Auto-created on first GET /api/v1/profile.
    """

    __tablename__ = "user_profiles"

    identity_id = db.Column(db.String(128), primary_key=True)
    display_name = db.Column(db.String(256), default="", nullable=False)
    email = db.Column(db.String(320), default="", nullable=False)
    phone = db.Column(db.String(64), default="", nullable=False)
    avatar_url = db.Column(db.String(512), default="", nullable=False)
    timezone = db.Column(db.String(64), default="UTC", nullable=False)
    locale = db.Column(db.String(16), default="en-US", nullable=False)
    date_format = db.Column(db.String(16), default="YYYY-MM-DD", nullable=False)
    bio = db.Column(db.Text, default="", nullable=False)
    theme_preference = db.Column(
        db.String(16), default="system", nullable=False
    )  # light / dark / system
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "identity_id": self.identity_id,
            "display_name": self.display_name,
            "email": self.email,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "locale": self.locale,
            "date_format": self.date_format,
            "bio": self.bio,
            "theme_preference": self.theme_preference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def preferences_dict(self) -> dict:
        """Return only preference fields."""
        return {
            "timezone": self.timezone,
            "locale": self.locale,
            "date_format": self.date_format,
            "theme_preference": self.theme_preference,
        }

    def update_from_dict(self, data: dict) -> None:
        """Update allowed profile fields from a dict."""
        allowed = {
            "display_name",
            "email",
            "phone",
            "avatar_url",
            "timezone",
            "locale",
            "date_format",
            "bio",
            "theme_preference",
        }
        for key in allowed:
            if key in data:
                setattr(self, key, data[key])