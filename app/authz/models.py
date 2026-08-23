"""FOR-2C.2: Authorization Engine — Data Models."""

from datetime import datetime
from app import db
from sqlalchemy import Index


PERMISSIONS = {
    "org.view": "View organization settings",
    "org.edit": "Edit organization settings",
    "org.delete": "Delete organization",
    "org.manage_members": "Manage team members",
    "org.manage_billing": "Manage billing and plans",
    "org.export_data": "Export organization data",
    "rel.view": "View relationships",
    "rel.create": "Create relationships",
    "rel.edit": "Edit relationships",
    "rel.delete": "Archive relationships",
    "rel.merge": "Merge duplicate relationships",
    "rel.view_timeline": "View relationship timeline",
    "rel.edit_memory": "Edit AI memory",
    "proposal.view": "View proposals",
    "proposal.create": "Create proposals",
    "proposal.edit": "Edit proposals",
    "proposal.delete": "Delete proposals",
    "proposal.send": "Send proposals",
    "proposal.approve": "Approve proposals",
    "proposal.ai_generate": "Use AI to generate proposals",
    "knowledge.view": "View knowledge documents",
    "knowledge.upload": "Upload knowledge documents",
    "knowledge.edit": "Edit knowledge documents",
    "knowledge.delete": "Delete knowledge documents",
    "knowledge.search": "Search knowledge base",
    "finance.view": "View financial records",
    "finance.create_invoice": "Create invoices",
    "finance.edit_invoice": "Edit invoices",
    "finance.record_payment": "Record payments",
    "finance.reconcile": "Reconcile accounts",
    "finance.view_reports": "View financial reports",
    "task.view": "View tasks",
    "task.create": "Create tasks",
    "task.edit": "Edit tasks",
    "task.assign": "Assign tasks to others",
    "task.complete": "Mark tasks complete",
    "ai.use": "Use AI features",
    "ai.edit_memory": "Edit AI memory",
    "ai.manage_prompts": "Manage AI prompts",
    "admin.view_audit": "View audit logs",
    "admin.manage_roles": "Manage roles and permissions",
    "admin.manage_industry_packs": "Manage industry packs",
    "admin.manage_integrations": "Manage integrations",
}


DEFAULT_ROLES = {
    "owner": {"display_name": "Owner", "description": "Full control", "permissions": list(PERMISSIONS.keys()) + [
        "connector.create","connector.edit","connector.delete","connector.view",
        "delegation.create","delegation.revoke","delegation.view",
        "tenant.edit","tenant.view",
        "admin.manage_connectors","admin.manage_delegations","admin.manage_policies",
        "admin.manage_service_accounts","admin.view_audit","admin.manage_roles",
        "audit.view","audit.export",
    ], "is_system": True},
    "admin": {"display_name": "Admin", "description": "Manage settings, members, data",
        "permissions": ["org.edit","org.manage_members","rel.view","rel.create","rel.edit","rel.merge","rel.view_timeline","rel.edit_memory",
            "proposal.view","proposal.create","proposal.edit","proposal.send","proposal.approve","proposal.ai_generate",
            "knowledge.view","knowledge.upload","knowledge.edit","knowledge.search",
            "finance.view","finance.create_invoice","finance.edit_invoice","finance.record_payment","finance.view_reports",
            "task.view","task.create","task.edit","task.assign","task.complete","ai.use","ai.edit_memory","admin.view_audit",
            "people.view","people.manage"],
        "is_system": True},
    "manager": {"display_name": "Manager", "description": "Operations, approvals",
        "permissions": ["rel.view","rel.create","rel.edit","rel.view_timeline",
            "proposal.view","proposal.create","proposal.edit","proposal.send","proposal.approve","proposal.ai_generate",
            "knowledge.view","knowledge.upload","knowledge.search",
            "finance.view","finance.view_reports","task.view","task.create","task.edit","task.assign","task.complete",
            "people.view",
            "ai.use"],
        "is_system": True},
    "member": {"display_name": "Member", "description": "Create and edit own data",
        "permissions": ["rel.view","rel.create","rel.edit","rel.view_timeline",
            "proposal.view","proposal.create","proposal.edit","proposal.ai_generate",
            "knowledge.view","knowledge.upload","knowledge.search",
            "task.view","task.create","task.edit",
            "people.view",
            "ai.use"],
        "is_system": True},
    "viewer": {"display_name": "Viewer", "description": "Read-only",
        "permissions": ["rel.view","rel.view_timeline","proposal.view","knowledge.view","knowledge.search"],
        "is_system": True},
}


class Role(db.Model):
    __tablename__ = "auth_roles"
    __table_args__ = (Index("ix_auth_role_org", "organization_id"), Index("ix_auth_role_org_name", "organization_id", "name", unique=True))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    permissions = db.Column(db.Text, default="[]")
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        import json
        return {"id": self.id, "organization_id": self.organization_id, "name": self.name,
            "display_name": self.display_name, "description": self.description,
            "permissions": json.loads(self.permissions or "[]"), "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None}

    def has_permission(self, permission: str) -> bool:
        import json
        return permission in json.loads(self.permissions or "[]")


class OrgMemberRole(db.Model):
    __tablename__ = "auth_member_roles"
    __table_args__ = (Index("ix_auth_mr_member", "member_id"), Index("ix_auth_mr_role", "role_id"),
        Index("ix_auth_mr_unique", "member_id", "role_id", unique=True))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("org_members.id"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("auth_roles.id"), nullable=False)
    scope = db.Column(db.String(30), default="organization")
    scope_id = db.Column(db.Integer, nullable=True)
    granted_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "organization_id": self.organization_id,
            "member_id": self.member_id, "role_id": self.role_id,
            "scope": self.scope, "scope_id": self.scope_id, "granted_by": self.granted_by}