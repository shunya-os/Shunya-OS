"""SHUNYA M9 — Enterprise Ready Models.

Multi-tenant isolation, RBAC, and immutable audit trail persistence.
"""
from datetime import datetime

from app import db
from sqlalchemy import Index, Text


# ---------------------------------------------------------------------------
# Audit Trail — Immutable Record of Every Pipeline Execution
# ---------------------------------------------------------------------------

class AuditRecord(db.Model):
    """Immutable audit record of every pipeline execution.

    Once written, records are never modified or deleted. This is enforced
    at the application layer — no update/delete operations are exposed.
    """

    __tablename__ = "m9_audit_records"
    __table_args__ = (
        Index("ix_m9_audit_time", "recorded_at"),
        Index("ix_m9_audit_actor", "actor_id", "recorded_at"),
        Index("ix_m9_audit_entity", "entity_id", "entity_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.String(64), nullable=False, index=True)
    actor_name = db.Column(db.String(255), default="")
    action = db.Column(db.String(40), nullable=False)
    # create, read, update, delete, sign_in, permission_change, invite
    entity_type = db.Column(db.String(40), nullable=False)
    # space, object, relationship, conversation, user, permission
    entity_id = db.Column(db.String(64), nullable=True)
    entity_name = db.Column(db.String(255), default="")
    details = db.Column(Text, default="")
    # JSON with action-specific details (before/after state, etc.)
    ip_address = db.Column(db.String(45), default="")
    organization_id = db.Column(db.String(64), nullable=True, index=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "details": self.details,
            "ip_address": self.ip_address,
            "organization_id": self.organization_id,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


# ---------------------------------------------------------------------------
# Role — Named Permission Set
# ---------------------------------------------------------------------------

class EnterpriseRole(db.Model):
    """Named role with associated permissions."""

    __tablename__ = "m9_roles"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(255), default="")
    permissions = db.Column(Text, default="[]")
    # JSON: [{"resource": "object", "actions": ["create", "read", "update", "delete"]}, ...]
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Team Member — Identity within an Organization
# ---------------------------------------------------------------------------

class EnterpriseTeamMember(db.Model):
    """A user's membership in an organization with a role."""

    __tablename__ = "m9_team_members"
    __table_args__ = (
        Index("ix_m9_member_identity", "identity_id"),
        Index("ix_m9_member_org", "organization_id"),
        db.UniqueConstraint("organization_id", "identity_id", name="uq_m9_org_member"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(64), nullable=False, index=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(255), default="")
    email = db.Column(db.String(255), default="")
    role_id = db.Column(db.Integer, db.ForeignKey("m9_roles.id"), nullable=True)
    status = db.Column(db.String(20), default="active")
    # active, invited, disabled
    invited_by = db.Column(db.String(64), nullable=True)
    joined_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    role = db.relationship("EnterpriseRole", backref="members", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "identity_id": self.identity_id,
            "name": self.name,
            "email": self.email,
            "role_id": self.role_id,
            "status": self.status,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }


# ---------------------------------------------------------------------------
# System Roles (seeded on first run)
# ---------------------------------------------------------------------------

SYSTEM_ROLES = [
    {
        "name": "Admin",
        "description": "Full access to all resources",
        "permissions": [
            {"resource": "*", "actions": ["create", "read", "update", "delete", "manage"]}
        ],
        "is_system": True,
    },
    {
        "name": "Member",
        "description": "Can create, read, and update resources",
        "permissions": [
            {"resource": "object", "actions": ["create", "read", "update"]},
            {"resource": "conversation", "actions": ["create", "read"]},
            {"resource": "space", "actions": ["read"]},
        ],
        "is_system": True,
    },
    {
        "name": "Viewer",
        "description": "Read-only access",
        "permissions": [
            {"resource": "object", "actions": ["read"]},
            {"resource": "conversation", "actions": ["read"]},
            {"resource": "space", "actions": ["read"]},
        ],
        "is_system": True,
    },
]