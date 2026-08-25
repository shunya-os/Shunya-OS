"""
WORKSPACE — Canonical Workspace Model for SHUNYA.

Architecture:

  Identity
    → WorkspaceMembership (identity_id, workspace_id, role)
      → Workspace (id, type, name, status)
        → CapabilityPolicy (workspace_type → [capability keys])
          → AuthorizationContext (identity, workspace, capabilities)

  Workspace Types:
    PERSONAL    — Individual life & productivity
    BUSINESS    — Company / organization
    TEAM        — Sub-team within a business
    PROJECT     — Time-bounded project
    FAMILY      — Family / household
    COMMUNITY   — Community / group
    NONPROFIT   — Nonprofit organization
    CREATOR     — Creator / freelancer / artist
    EDUCATION   — Educational institution
    OTHER       — Extensible future type

  Principles:
    - No scattered `if workspace_type == "business"` across the codebase.
    - Capabilities are governed by CapabilityPolicy per type.
    - AuthorizationContext is the result of resolving WHO + WHICH WORKSPACE + WHAT CAPABILITIES.
    - Every authenticated request resolves to an AuthorizationContext.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from flask import g, session
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship

from app import db


# ── Workspace Type Enum ────────────────────────────────────────────────


class WorkspaceType(str, enum.Enum):
    """Canonical workspace type taxonomy — extensible."""
    PERSONAL = "personal"
    BUSINESS = "business"
    TEAM = "team"
    PROJECT = "project"
    FAMILY = "family"
    COMMUNITY = "community"
    NONPROFIT = "nonprofit"
    CREATOR = "creator"
    EDUCATION = "education"
    OTHER = "other"

    @classmethod
    def default_for_signup(cls) -> "WorkspaceType":
        return cls.PERSONAL

    @classmethod
    def from_string(cls, s: str) -> "WorkspaceType":
        try:
            return cls(s.lower())
        except ValueError:
            return cls.OTHER


# ── Capability Policy ──────────────────────────────────────────────────

# Universal capabilities: available in ALL workspace types
UNIVERSAL_CAPABILITIES = frozenset({
    "core.ai",           # AI chat, intelligence, commands
    "core.memory",       # Memory storage and recall
    "core.people",       # Contact management
    "core.tasks",        # Task / work management
    "core.knowledge",    # Knowledge base
    "core.files",        # Document / file storage
    "core.search",       # Universal search
    "core.outputs",      # Generated outputs
    "core.reports",      # Reports and analytics
    "core.notifications",# Notifications
    "core.automation",   # Automation rules
})

# Business-specific capabilities
BUSINESS_CAPABILITIES = frozenset({
    "business.crm",          # Customer relationship management
    "business.invoicing",    # Invoicing and billing
    "business.ledger",       # Business ledger / accounting
    "business.commercial",   # Commercial pipeline
    "business.marketing",    # Marketing campaigns
    "business.sales",        # Sales pipeline
    "business.operations",   # Operations management
    "business.team",         # Team management
    "business.procurement",  # Procurement / purchasing
})

# Personal-specific capabilities
PERSONAL_CAPABILITIES = frozenset({
    "personal.finance",      # Personal budgeting & finance
    "personal.health",       # Health tracking
    "personal.goals",        # Goal tracking
})

# Contextual capabilities: available but adapted per context
CONTEXTUAL_CAPABILITIES = frozenset({
    "context.finance",       # Finance (personal vs business)
    "context.calendar",      # Calendar / time
    "context.content",       # Content generation
    "context.relationships", # Relationship network
    "context.planning",      # Planning / strategy
})

# ── Capability Policy Registry ────────────────────────────────────────

CAPABILITY_POLICY = {
    WorkspaceType.PERSONAL: {
        "universal": True,
        "includes": UNIVERSAL_CAPABILITIES | PERSONAL_CAPABILITIES,
        "excludes": BUSINESS_CAPABILITIES,
        "contextual": CONTEXTUAL_CAPABILITIES,
    },
    WorkspaceType.BUSINESS: {
        "universal": True,
        "includes": UNIVERSAL_CAPABILITIES | BUSINESS_CAPABILITIES,
        "excludes": PERSONAL_CAPABILITIES,
        "contextual": CONTEXTUAL_CAPABILITIES,
    },
    WorkspaceType.TEAM: {
        "universal": True,
        "includes": UNIVERSAL_CAPABILITIES - {"core.people"},
        "excludes": BUSINESS_CAPABILITIES - {"business.team", "business.operations"},
        "contextual": frozenset(),
    },
    WorkspaceType.PROJECT: {
        "universal": True,
        "includes": UNIVERSAL_CAPABILITIES - {"core.people"},
        "excludes": BUSINESS_CAPABILITIES,
        "contextual": frozenset({"context.calendar", "context.planning"}),
    },
    WorkspaceType.FAMILY: {
        "universal": True,
        "includes": UNIVERSAL_CAPABILITIES | PERSONAL_CAPABILITIES,
        "excludes": BUSINESS_CAPABILITIES,
        "contextual": CONTEXTUAL_CAPABILITIES - {"context.content"},
    },
    WorkspaceType.COMMUNITY: {
        "universal": True,
        "includes": UNIVERSAL_CAPABILITIES | PERSONAL_CAPABILITIES - {"personal.goals"},
        "excludes": BUSINESS_CAPABILITIES,
        "contextual": CONTEXTUAL_CAPABILITIES - {"context.finance"},
    },
    WorkspaceType.OTHER: {
        "universal": True,
        "includes": UNIVERSAL_CAPABILITIES,
        "excludes": BUSINESS_CAPABILITIES | PERSONAL_CAPABILITIES,
        "contextual": CONTEXTUAL_CAPABILITIES,
    },
}


def get_capabilities_for_type(workspace_type: WorkspaceType) -> frozenset:
    """Return the set of capability keys available for a workspace type."""
    policy = CAPABILITY_POLICY.get(workspace_type, CAPABILITY_POLICY[WorkspaceType.OTHER])
    caps = set(policy["includes"])
    caps |= policy["contextual"]
    return frozenset(caps)


def is_capability_allowed(workspace_type: WorkspaceType, capability_key: str) -> bool:
    """Check if a specific capability is allowed for a workspace type."""
    policy = CAPABILITY_POLICY.get(workspace_type, CAPABILITY_POLICY[WorkspaceType.OTHER])
    if capability_key in policy["excludes"]:
        return False
    if capability_key in policy["includes"]:
        return True
    if capability_key in policy["contextual"]:
        return True
    return False


# ── SQLAlchemy Models ──────────────────────────────────────────────────


class Workspace(db.Model):
    """
    A SHUNYA workspace — the container for all data and activity.

    Every workspace has a type, ownership, and lifecycle.
    Data isolation is by workspace_id.
    """
    __tablename__ = "user_workspaces"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    workspace_type = Column(String(30), nullable=False, default=WorkspaceType.PERSONAL.value)
    description = Column(Text, default="")
    owner_identity_id = Column(String(64), nullable=False, index=True)
    status = Column(String(30), default="active")  # active, archived, suspended
    organization_id = Column(Integer, nullable=True)  # FK to legacy organizations
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    memberships = relationship("WorkspaceMembership", backref="workspace",
                                 lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "workspace_type": self.workspace_type,
            "description": self.description,
            "owner_identity_id": self.owner_identity_id,
            "status": self.status,
            "capabilities": sorted(get_capabilities_for_type(WorkspaceType.from_string(self.workspace_type))),
        }


class WorkspaceMembership(db.Model):
    """
    Links an identity to a workspace with a role.

    One identity can belong to many workspaces.
    One workspace can have many members.
    """
    __tablename__ = "user_workspace_memberships"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("user_workspaces.id"), nullable=False)
    identity_id = Column(String(64), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), default="")
    role = Column(String(30), default="owner")  # owner, admin, member, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "identity_id": self.identity_id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "is_active": self.is_active,
        }


# ── Authorization Context ──────────────────────────────────────────────


class AuthorizationContext:
    """
    Resolved context for an authenticated request.

    Attributes:
        identity_id (str): The authenticated identity
        email (str): The identity's email
        name (str): The identity's display name
        current_workspace (Workspace): The workspace this request is for
        workspace_type (WorkspaceType): The type of the current workspace
        capabilities (frozenset): Allowed capabilities for this context
        permissions (dict): Additional permissions from authz layer
    """

    def __init__(
        self,
        identity_id: str,
        email: str = "",
        name: str = "",
        current_workspace: Optional[Workspace] = None,
        permissions: Optional[dict] = None,
    ):
        self.identity_id = identity_id
        self.email = email
        self.name = name
        self.current_workspace = current_workspace
        self.workspace_type = WorkspaceType.from_string(
            current_workspace.workspace_type if current_workspace else WorkspaceType.PERSONAL.value
        )
        self.capabilities = get_capabilities_for_type(self.workspace_type) if current_workspace else UNIVERSAL_CAPABILITIES
        self.permissions = permissions or {}

    def has_capability(self, key: str) -> bool:
        return key in self.capabilities

    def is_personal(self) -> bool:
        return self.workspace_type == WorkspaceType.PERSONAL

    def is_business(self) -> bool:
        return self.workspace_type == WorkspaceType.BUSINESS

    def to_dict(self):
        return {
            "identity_id": self.identity_id,
            "email": self.email,
            "name": self.name,
            "workspace_id": self.current_workspace.workspace_id if self.current_workspace else None,
            "workspace_name": self.current_workspace.name if self.current_workspace else None,
            "workspace_type": self.workspace_type.value if self.current_workspace else None,
            "capabilities": sorted(self.capabilities),
        }


def resolve_context(identity_id: str = None, workspace_id: str = None) -> AuthorizationContext:
    """
    Resolve the current AuthorizationContext from request context.

    Priority:
      1. If workspace_id is provided, use it
      2. If session has current_workspace_id, use it
      3. Fall back to the identity's default workspace (most recent)
    """
    from app.auth import TeamMember

    uid = identity_id or session.get("identity_id") or session.get("user_id", "")
    if not uid:
        return AuthorizationContext(identity_id="")

    # Resolve identity info
    member = TeamMember.query.filter_by(email=uid).first() if "@" in str(uid) else None
    email = member.email if member else ""
    name = member.name if member else ""

    # Find workspace
    ws = None
    wid = workspace_id or session.get("current_workspace_id")
    if wid:
        ws = Workspace.query.filter_by(workspace_id=wid, status="active").first()

    if not ws:
        # Find the identity's most recent active workspace
        membership = WorkspaceMembership.query.filter_by(
            identity_id=uid, is_active=True
        ).order_by(WorkspaceMembership.id.desc()).first()
        if membership:
            ws = Workspace.query.get(membership.workspace_id)
        if not ws:
            # Create personal workspace as fallback
            ws = _ensure_personal_workspace(uid, member)

    return AuthorizationContext(
        identity_id=uid,
        email=email,
        name=name,
        current_workspace=ws,
    )


def _ensure_personal_workspace(uid: str, member=None) -> Workspace:
    """Create a personal workspace for the identity if none exists."""
    existing = Workspace.query.filter_by(
        owner_identity_id=uid,
        workspace_type=WorkspaceType.PERSONAL.value,
        status="active",
    ).first()
    if existing:
        return existing

    ws = Workspace(
        workspace_id=f"ws_{uuid.uuid4().hex[:12]}",
        name=f"{member.name if member else 'Personal'}'s Space",
        workspace_type=WorkspaceType.PERSONAL.value,
        owner_identity_id=uid,
        status="active",
    )
    db.session.add(ws)
    db.session.flush()

    membership = WorkspaceMembership(
        workspace_id=ws.id,
        identity_id=uid,
        email=member.email if member else uid,
        name=member.name if member else "",
        role="owner",
        is_active=True,
    )
    db.session.add(membership)
    db.session.commit()
    return ws


# ── Convenience helpers ────────────────────────────────────────────────


def create_workspace(
    name: str,
    workspace_type: str,
    owner_identity_id: str,
    owner_email: str = "",
    owner_name: str = "",
    description: str = "",
) -> Workspace:
    """Create a workspace and its owner membership atomically."""
    ws = Workspace(
        workspace_id=f"ws_{uuid.uuid4().hex[:12]}",
        name=name,
        workspace_type=WorkspaceType.from_string(workspace_type).value,
        description=description,
        owner_identity_id=owner_identity_id,
        status="active",
    )
    db.session.add(ws)
    db.session.flush()

    membership = WorkspaceMembership(
        workspace_id=ws.id,
        identity_id=owner_identity_id,
        email=owner_email,
        name=owner_name,
        role="owner",
        is_active=True,
    )
    db.session.add(membership)
    db.session.commit()
    return ws


def get_workspaces_for_identity(identity_id: str) -> list[dict]:
    """Get all active workspaces for an identity."""
    memberships = WorkspaceMembership.query.filter_by(
        identity_id=identity_id, is_active=True
    ).all()
    workspace_ids = [m.workspace_id for m in memberships]
    workspaces = Workspace.query.filter(
        Workspace.id.in_(workspace_ids),
        Workspace.status == "active",
    ).all()
    return [ws.to_dict() for ws in workspaces]


def switch_workspace(identity_id: str, workspace_id: str) -> Optional[dict]:
    """
    Switch the current workspace for an identity.
    Returns workspace dict on success, None if not a member.
    """
    membership = WorkspaceMembership.query.filter_by(
        identity_id=identity_id,
        is_active=True,
    ).join(Workspace).filter(
        Workspace.workspace_id == workspace_id,
        Workspace.status == "active",
    ).first()

    if not membership:
        return None

    ws = Workspace.query.get(membership.workspace_id)
    if not ws:
        return None

    session["current_workspace_id"] = ws.workspace_id
    session["current_workspace_type"] = ws.workspace_type
    session.modified = True
    return ws.to_dict()