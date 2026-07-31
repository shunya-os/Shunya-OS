"""
Shunya — Auth/RBAC Layer (Phase 2)

Team accounts with role-based access control.
Roles: Admin, Manager, Agent.
Every request passes through permission check before accessing any resource.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from app import db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index


class UserRole(str, Enum):
    ADMIN = "admin"       # Full access to everything
    MANAGER = "manager"   # CRUD leads, payments, invoices, view reports
    AGENT = "agent"       # View assigned leads, add notes, update status


class TeamMember(db.Model):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True)
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

    def verify_token(self, token: str) -> Optional[TeamMember]:
        if not token:
            return None
        return TeamMember.query.filter_by(api_token=token, is_active=True).first()

    def verify_session(self, session_token: str) -> Optional[TeamMember]:
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