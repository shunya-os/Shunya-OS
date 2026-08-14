"""SHUNYA — Founder Experience DB Models.

Persists kernel primitives to SQLAlchemy for the Founder Journey.
These are storage adapters, NOT kernel primitives.
"""
import json
from datetime import datetime

from app import db


class FounderSpace(db.Model):
    """Persists kernel Space to DB."""
    __tablename__ = "founder_spaces"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    space_type = db.Column(db.String(30), default="organization")
    description = db.Column(db.Text, default="")
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    member_count = db.Column(db.Integer, default=1)
    organization_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    objects = db.relationship("FounderObject", backref="space",
                              lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "space_id": self.space_id,
            "name": self.name,
            "space_type": self.space_type,
            "description": self.description,
            "identity_id": self.identity_id,
            "member_count": self.member_count,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "object_count": self.objects.count(),
        }


class FounderObject(db.Model):
    """Persists kernel UniversalObject to DB."""
    __tablename__ = "founder_objects"

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    space_id = db.Column(db.String(64), db.ForeignKey("founder_spaces.space_id"),
                         nullable=False, index=True)
    object_type = db.Column(db.String(60), default="Document")
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, default="")
    status = db.Column(db.String(30), default="active")
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = db.relationship("FounderConversation", backref="object",
                                    lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "object_id": self.object_id,
            "space_id": self.space_id,
            "object_type": self.object_type,
            "name": self.name,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "status": self.status,
            "created_by": self.created_by[:12] + "..." if self.created_by else "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "conversation_count": self.conversations.count(),
        }


class FounderConversation(db.Model):
    """A conversation attached to an object."""
    __tablename__ = "founder_conversations"

    id = db.Column(db.Integer, primary_key=True)
    conv_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    object_id = db.Column(db.String(64), db.ForeignKey("founder_objects.object_id"),
                          nullable=False, index=True)
    title = db.Column(db.String(255), default="")
    identity_id = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship("FounderMessage", backref="conversation",
                               lazy="dynamic", cascade="all, delete-orphan",
                               order_by="FounderMessage.created_at")

    def to_dict(self):
        return {
            "conv_id": self.conv_id,
            "object_id": self.object_id,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "message_count": self.messages.count(),
        }


class FounderMessage(db.Model):
    """A single message in a conversation."""
    __tablename__ = "founder_messages"

    id = db.Column(db.Integer, primary_key=True)
    conv_id = db.Column(db.String(64), db.ForeignKey("founder_conversations.conv_id"),
                         nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # "human" or "assistant"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "conv_id": self.conv_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BusinessRelationship(db.Model):
    """A lifetime business relationship — customer, supplier, partner, employee, vendor."""
    __tablename__ = "founder_relationships"

    id = db.Column(db.Integer, primary_key=True)
    rel_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    space_id = db.Column(db.String(64), db.ForeignKey("founder_spaces.space_id"),
                         nullable=False, index=True)
    rel_type = db.Column(db.String(30), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), default="")
    phone = db.Column(db.String(60), default="")
    company = db.Column(db.String(255), default="")
    notes = db.Column(db.Text, default="")
    tags = db.Column(db.String(500), default="")
    status = db.Column(db.String(30), default="active")
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "rel_id": self.rel_id,
            "space_id": self.space_id,
            "rel_type": self.rel_type,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "notes": self.notes[:200] + "..." if len(self.notes) > 200 else self.notes,
            "tags": [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else [],
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }