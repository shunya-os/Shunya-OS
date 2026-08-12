"""FDA22 — Admin & Permissions: Extended Models.

Extends the existing authorization architecture with:
- ServiceAccount: Connector/service credentials with scoped permissions
- Delegation: Approval delegation within scope
- TenantPolicy: Configurable tenant-level policies
- Extended permission keys for admin operations

No duplicate RBAC. All existing Role/OrgMemberRole architecture preserved.
"""

from datetime import datetime
from app import db
from sqlalchemy import Index


# =========================================================================
# Extended Permission Keys (additions to existing PERMISSIONS dict)
# =========================================================================

EXTENDED_PERMISSIONS = {
    # Service account / connector
    "connector.create": "Create API/service connectors",
    "connector.edit": "Edit API/service connectors",
    "connector.delete": "Delete API/service connectors",
    "connector.view": "View API/service connectors",
    # Delegation / approval
    "delegation.create": "Create approval delegations",
    "delegation.revoke": "Revoke approval delegations",
    "delegation.view": "View approval delegations",
    # Tenant configuration
    "tenant.edit": "Edit tenant configuration",
    "tenant.view": "View tenant configuration",
    # Admin operations
    "admin.manage_connectors": "Manage connector credentials",
    "admin.manage_delegations": "Manage approval delegations",
    "admin.manage_policies": "Manage tenant policies",
    "admin.manage_service_accounts": "Manage service accounts",
    "admin.view_audit": "View audit logs",
    "admin.manage_roles": "Manage roles and permissions",
    # Audit
    "audit.view": "View audit records",
    "audit.export": "Export audit records",
}


# =========================================================================
# Service Account
# =========================================================================


class ServiceAccount(db.Model):
    """Connector/service credentials with scoped permissions.

    Service accounts authenticate via API tokens and have specific
    permission scopes. They are NOT human identities.
    """

    __tablename__ = "auth_service_accounts"
    __table_args__ = (
        Index("ix_sa_org", "organization_id"),
        Index("ix_sa_token", "token_hash", unique=True),
        Index("ix_sa_name_org", "organization_id", "name", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    token_hash = db.Column(db.String(128), nullable=False)
    token_prefix = db.Column(db.String(8), nullable=False)  # First 8 chars for identification
    permissions = db.Column(db.Text, default="[]")  # JSON array of permission keys
    allowed_scopes = db.Column(db.Text, default='["organization"]')  # JSON array
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        import json
        return {
            "id": self.id, "organization_id": self.organization_id,
            "name": self.name, "description": self.description,
            "token_prefix": self.token_prefix,
            "permissions": json.loads(self.permissions or "[]"),
            "allowed_scopes": json.loads(self.allowed_scopes or '["organization"]'),
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


# =========================================================================
# Approval Delegation
# =========================================================================


class ApprovalDelegation(db.Model):
    """Delegation of approval authority from one member to another.

    Enables governed delegation within defined scope and time bounds.
    Every delegation is audited.
    """

    __tablename__ = "auth_delegations"
    __table_args__ = (
        Index("ix_ad_org", "organization_id"),
        Index("ix_ad_delegator", "delegator_id"),
        Index("ix_ad_delegate", "delegate_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    delegator_id = db.Column(db.Integer, db.ForeignKey("org_members.id"), nullable=False)
    delegate_id = db.Column(db.Integer, db.ForeignKey("org_members.id"), nullable=False)
    permission_keys = db.Column(db.Text, default="[]")  # Which permissions are delegated
    scope = db.Column(db.String(30), default="organization")
    scope_id = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="active")  # active, revoked, expired
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=True)
    revoked_by = db.Column(db.String(64), nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id, "organization_id": self.organization_id,
            "delegator_id": self.delegator_id, "delegate_id": self.delegate_id,
            "permission_keys": json.loads(self.permission_keys or "[]"),
            "scope": self.scope, "scope_id": self.scope_id,
            "reason": self.reason, "status": self.status,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "revoked_by": self.revoked_by, "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "created_by": self.created_by,
        }


# =========================================================================
# Tenant Policy
# =========================================================================


class TenantPolicy(db.Model):
    """Configurable tenant-level policies.

    Each tenant can have policies that govern:
    - Password requirements
    - Session duration
    - MFA requirements
    - Approval thresholds
    - Export controls
    - Data retention
    """

    __tablename__ = "auth_tenant_policies"
    __table_args__ = (
        Index("ix_tp_org_key", "organization_id", "policy_key", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    policy_key = db.Column(db.String(120), nullable=False)
    policy_value = db.Column(db.Text, nullable=False)
    policy_type = db.Column(db.String(30), default="string")  # string, number, boolean, json
    description = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "organization_id": self.organization_id,
            "policy_key": self.policy_key, "policy_value": self.policy_value,
            "policy_type": self.policy_type, "description": self.description,
            "is_active": self.is_active, "created_by": self.created_by,
        }