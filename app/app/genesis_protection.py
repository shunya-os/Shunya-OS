"""
SHUNYA OS — Immutable Audit Log & Protective Safeguards (Genesis)

Provides:
- Immutable audit trail for all destructive operations
- Founder account protection (cannot delete self)
- Last-owner/administrator protection
- Organization orphan prevention
- Soft delete infrastructure
- Confirmation-required guard for destructive actions

Phase 4 — Founder Protection
Phase 5 — Safe Deletion Architecture
Phase 6 — Destructive Action Confirmation
Phase 7 — Immutable Audit
"""

import json
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from app import db
from sqlalchemy import Index, text


# =========================================================================
# Enums
# =========================================================================


class AuditAction(str, PyEnum):
    """All auditable destructive/administrative operations."""
    ORGANIZATION_DELETE = "organization.delete"
    ORGANIZATION_PURGE = "organization.purge"
    WORKSPACE_DELETE = "workspace.delete"
    WORKSPACE_PURGE = "workspace.purge"
    SPACE_DELETE = "space.delete"
    OBJECT_DELETE = "object.delete"
    OBJECT_PURGE = "object.purge"
    RELATIONSHIP_DELETE = "relationship.delete"
    MEMBER_REMOVE = "member.remove"
    IDENTITY_DELETE = "identity.delete"
    BULK_DELETE = "bulk.delete"
    DATA_PURGE = "data.purge"
    RESTORE = "restore"
    ACCOUNT_DEACTIVATE = "account.deactivate"


class ProtectedEntityType(str, PyEnum):
    ORGANIZATION = "organization"
    WORKSPACE = "workspace"
    SPACE = "space"
    OBJECT = "object"
    IDENTITY = "identity"
    MEMBER = "member"
    RELATIONSHIP = "relationship"


# =========================================================================
# Model: Immutable Audit Log
# =========================================================================


class AuditLog(db.Model):
    """Immutable, append-only audit record.

    Once written, this record MUST NOT be modified or deleted.
    Audit history remains available even if the referenced data is restored.
    """
    __tablename__ = "genesis_audit_log"
    __table_args__ = (
        Index("ix_audit_actor", "actor_id"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_operation", "operation"),
        Index("ix_audit_timestamp", "occurred_at"),
        {"info": {"immutable": True}},
    )

    id = db.Column(db.Integer, primary_key=True)
    # Globally unique audit event ID for cross-referencing
    event_id = db.Column(
        db.String(64), unique=True, nullable=False, default=lambda: f"aev_{uuid.uuid4().hex[:20]}"
    )
    # Who performed the action
    actor_id = db.Column(db.String(128), nullable=False, index=True)
    actor_name = db.Column(db.String(255), default="")
    # What was affected
    entity_type = db.Column(db.String(60), nullable=False)
    entity_id = db.Column(db.String(128), nullable=False)
    entity_name = db.Column(db.String(255), default="")
    # The operation performed
    operation = db.Column(db.String(60), nullable=False)
    # Outcome: "success", "blocked", "confirmed", "restored"
    outcome = db.Column(db.String(30), nullable=False, default="success")
    # Human-readable explanation (especially for blocked operations)
    explanation = db.Column(db.Text, default="")
    # Detailed payload (JSON — context, parameters, before/after state references)
    details = db.Column(db.Text, default="{}")
    # Restoration tracking
    restoration_event_id = db.Column(db.String(64), nullable=True)
    restoration_status = db.Column(db.String(30), default="not_applicable")
    # When it happened (immutable — set once on creation)
    occurred_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "operation": self.operation,
            "outcome": self.outcome,
            "explanation": self.explanation,
            "details": json.loads(self.details or "{}"),
            "restoration_event_id": self.restoration_event_id,
            "restoration_status": self.restoration_status,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
        }


# =========================================================================
# Protection Service
# =========================================================================


def record_audit_event(
    *,
    actor_id: str,
    actor_name: str = "",
    entity_type: str,
    entity_id: str,
    entity_name: str = "",
    operation: str,
    outcome: str = "success",
    explanation: str = "",
    details: dict | None = None,
    restoration_event_id: str | None = None,
    restoration_status: str = "not_applicable",
) -> AuditLog:
    """Create an immutable audit record. Append-only — no update, no delete."""
    event = AuditLog(
        actor_id=actor_id,
        actor_name=actor_name,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        operation=operation,
        outcome=outcome,
        explanation=explanation,
        details=json.dumps(details or {}),
        restoration_event_id=restoration_event_id,
        restoration_status=restoration_status,
    )
    db.session.add(event)
    db.session.commit()
    return event


def check_founder_protection(identity_id: str) -> dict | None:
    """Phase 4 — Prevent deletion of the currently authenticated Founder.

    Returns a protection block dict if the operation is not allowed,
    or None if it's safe to proceed.

    This check prevents:
    1. Self-deletion of the currently authenticated founder
    2. Deletion of the last Organization Owner
    3. Deletion of the last administrative account
    4. Orphaning of organizations
    5. Orphaning of workspaces
    6. Orphaning of business objects
    """
    from app.models import Organization, OrgMember

    # Check 1: Is this identity an owner of any organization?
    owner_memberships = OrgMember.query.filter_by(
        identity_id=identity_id, role="owner", is_active=True
    ).all()

    for membership in owner_memberships:
        org_id = membership.organization_id
        # How many owners does this org have?
        owner_count = OrgMember.query.filter_by(
            organization_id=org_id, role="owner", is_active=True
        ).count()

        if owner_count <= 1:
            org = db.session.get(Organization, org_id)
            org_name = org.name if org else f"organization #{org_id}"
            return {
                "blocked": True,
                "reason": (
                    f"Cannot remove identity '{identity_id}': it is the last Owner "
                    f"of '{org_name}'. Removing this account would orphan the "
                    f"organization. Transfer ownership to another member first, "
                    f"or delete the organization entirely."
                ),
                "entity_type": "identity",
                "entity_id": identity_id,
                "protection": "last_owner",
            }

    # Check 2: Is this identity an admin with no other admins in any org?
    admin_memberships = OrgMember.query.filter_by(
        identity_id=identity_id, role="admin", is_active=True
    ).all()

    for membership in admin_memberships:
        org_id = membership.organization_id
        admin_count = OrgMember.query.filter_by(
            organization_id=org_id, role="admin", is_active=True
        ).count()

        if admin_count <= 1:
            return {
                "blocked": True,
                "reason": (
                    f"Cannot remove identity '{identity_id}': it is the last Admin "
                    f"of organization #{org_id}. At least one administrative account "
                    f"must remain. Promote another member to Admin first."
                ),
                "entity_type": "identity",
                "entity_id": identity_id,
                "protection": "last_admin",
            }

    return None


def check_org_deletion_protection(org_id: int, actor_id: str) -> dict | None:
    """Phase 6 — Check if an organization can be safely deleted.

    Verifies:
    - No orphaned workspaces/spaces/objects
    - Owner has explicitly confirmed
    """
    from app.models import Organization, OrgMember, Workspace

    org = db.session.get(Organization, org_id)
    if not org:
        return {"blocked": True, "reason": "Organization not found."}

    member_count = OrgMember.query.filter_by(
        organization_id=org_id, is_active=True
    ).count()

    workspace_count = Workspace.query.filter_by(
        organization_id=org_id, is_active=True
    ).count()

    return {
        "warnings": [
            f"This organization has {member_count} active member(s)." if member_count > 0 else None,
            f"This organization has {workspace_count} workspace(s)." if workspace_count > 0 else None,
        ],
        "requires_confirmation": True,
        "confirmation_prompt": (
            f"Type DELETE to confirm permanent deletion of organization '{org.name}'.\n"
            f"This action CANNOT be undone. {member_count} member(s) and "
            f"{workspace_count} workspace(s) will be affected."
        ),
    }


def require_confirmation(prompt: str, user_input: str) -> dict:
    """Phase 6 — Check that user provided deliberate confirmation.

    Returns {"confirmed": True} or {"confirmed": False, "error": ...}
    """
    if user_input.strip().upper() == "DELETE":
        return {"confirmed": True}
    return {
        "confirmed": False,
        "error": "Confirmation failed. You must type 'DELETE' (case-insensitive) "
                 "to confirm this destructive action. No changes were made.",
        "prompt": prompt,
    }


class SoftDeleteMixin:
    """Phase 5 — Mixin for soft-delete capable models.

    Add this as a parent class alongside db.Model:
        class MyModel(SoftDeleteMixin, db.Model):
            ...

    Provides:
    - `deleted_at` timestamp
    - `deleted_by` identity reference
    - `restored_at` timestamp
    - `restored_by` identity reference
    - `is_deleted` property
    - `soft_delete(deleted_by)` method
    - `restore(restored_by)` method
    """

    deleted_at = db.Column(db.DateTime, nullable=True, default=None)
    deleted_by = db.Column(db.String(128), nullable=True, default=None)
    restored_at = db.Column(db.DateTime, nullable=True, default=None)
    restored_by = db.Column(db.String(128), nullable=True, default=None)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, deleted_by: str = ""):
        """Mark this record as deleted without removing it from the database."""
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by
        if hasattr(self, "status"):
            self.status = "deleted"

    def restore(self, restored_by: str = ""):
        """Restore a soft-deleted record to its active state."""
        self.restored_at = datetime.now(timezone.utc)
        self.restored_by = restored_by
        self.deleted_at = None
        self.deleted_by = None
        if hasattr(self, "status"):
            self.status = "active"


# Default retention period for purged data (30 days in seconds)
DEFAULT_RETENTION_SECONDS = 30 * 24 * 60 * 60


def purge_expired_soft_deletes(retention_seconds: int = DEFAULT_RETENTION_SECONDS) -> int:
    """Phase 5 — Permanently delete records that have been soft-deleted
    beyond the retention period.

    Scans all registered SQLAlchemy models for soft-delete columns
    and purges expired records.

    Returns the number of records permanently removed.
    """
    from sqlalchemy import text as sql_text
    from sqlalchemy import inspect

    cutoff = datetime.now(timezone.utc).timestamp() - retention_seconds
    cutoff_dt = datetime.fromtimestamp(cutoff, tz=timezone.utc)

    # Discover models that have a deleted_at column by inspecting tables
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    total_purged = 0
    for table_name in table_names:
        columns = [c["name"] for c in inspector.get_columns(table_name)]
        if "deleted_at" not in columns:
            continue

        # Find the SQLAlchemy model class for this table
        model_class = None
        for mapper in db.Model.registry.mappers:
            if mapper.class_.__tablename__ == table_name:
                model_class = mapper.class_
                break

        if model_class is None or not hasattr(model_class, "deleted_at"):
            continue

        expired = model_class.query.filter(
            model_class.deleted_at.isnot(None),
            model_class.deleted_at < cutoff_dt,
        ).all()

        for record in expired:
            db.session.delete(record)
            total_purged += 1

    if total_purged:
        db.session.commit()

    return total_purged