"""
Shunya — Auth/RBAC Layer (Phase 2)

GATE 2.2 BOUNDARY: TeamMember is AUTHENTICATION METADATA ONLY.
It is NOT a business identity authority.

TeamMember has a `person_id` foreign key to the canonical Person table.
All business identity resolution goes through the canonical identity path
(kernel/identity.py + production/identity_repository.py + persons table).

TeamMember is a login account with password hash, role, and session state.
It does not create independent identity data.
It does not resolve business identity.
It does not serve as a second person/identity truth.

Team accounts with role-based access control.
Roles: Admin, Manager, Agent.
Every request passes through permission check before accessing any resource.
"""

import hashlib
import secrets
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app import db
from app.tenant import Tenant  # noqa: F401 — needed for SQLAlchemy relationship resolution


class UserRole(str, Enum):
    ADMIN = "admin"       # Full access to everything
    MANAGER = "manager"   # CRUD leads, payments, invoices, view reports
    AGENT = "agent"       # View assigned leads, add notes, update status


class TeamMember(db.Model):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, default=1)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(30))
    role = Column(String(30), default=UserRole.AGENT.value)
    password_hash = Column(String(128))
    api_token = Column(String(128), unique=True)
    is_active = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verify_token = Column(String(128), nullable=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    person_id = Column(Integer, db.ForeignKey("persons.id"), nullable=True)
    person = db.relationship("Person", backref="team_members", lazy="select")

    def set_password(self, password: str):
        salt = secrets.token_hex(16)
        self.password_hash = f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"

    def check_password(self, password: str) -> bool:
        if not self.password_hash or "$" not in self.password_hash:
            return False
        salt, hsh = self.password_hash.split("$", 1)
        return hsh == hashlib.sha256((salt + password).encode()).hexdigest()

    def generate_token(self) -> str:
        self.api_token = secrets.token_hex(32)
        return self.api_token

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "email": self.email,
            "phone": self.phone, "role": self.role, "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class AuthLayer:
    def __init__(self):
        self._exempt_paths = {"/health", "/login", "/api/login"}

    def verify_token(self, token: str) -> TeamMember | None:
        if not token:
            return None
        return TeamMember.query.filter_by(api_token=token, is_active=True).first()

    def verify_session(self, session_token: str) -> TeamMember | None:
        return self.verify_token(session_token)

    def check_permission(self, user: TeamMember, resource: str, action: str = "read") -> bool:
        if user.role == UserRole.ADMIN.value:
            return True
        if user.role == UserRole.MANAGER.value:
            restricted = {"settings": ["delete"], "team": ["delete", "create"]}
            res_actions = restricted.get(resource, [])
            return action not in res_actions
        if user.role == UserRole.AGENT.value:
            allowed = {"lead": ["read", "update"], "payment": ["read"], "invoice": ["read"]}
            res_actions = allowed.get(resource, [])
            return action in res_actions
        return False


class PasswordResetToken(db.Model):
    """Persistent password reset tokens — survives gunicorn multi-worker restarts."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(Integer, db.ForeignKey("team_members.id"), nullable=False)
    email = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = db.relationship("TeamMember", backref="reset_tokens", lazy="select")


class EmailVerificationToken(db.Model):
    """Persistent email verification tokens."""
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(Integer, db.ForeignKey("team_members.id"), nullable=False)
    email = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = db.relationship("TeamMember", backref="verification_tokens", lazy="select")


class InvitationToken(db.Model):
    """Persistent invitation tokens for organization onboarding."""
    __tablename__ = "invitation_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(128), unique=True, nullable=False, index=True)
    org_id = Column(Integer, db.ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False)
    name = Column(String(255), default="")
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    org = db.relationship("Tenant", backref="invitations", lazy="select")

    @property
    def status(self) -> str:
        return "accepted" if self.accepted_at else "pending"