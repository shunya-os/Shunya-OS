"""Shunya OS — All database models."""
import uuid, hashlib, secrets, json
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional
from app import db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TenantPlan(str, PyEnum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class UserRole(str, PyEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"

class GovernanceLevel(str, PyEnum):
    DRAFT = "draft"
    AUTO = "auto"
    GOVERN = "govern"

class NotificationType(str, PyEnum):
    ENTITY_CREATED = "entity_created"
    STATUS_CHANGED = "status_changed"
    PAYMENT_RECEIVED = "payment_received"
    TASK_ASSIGNED = "task_assigned"
    CELEBRATION = "celebration"
    SYSTEM = "system"

# ---------------------------------------------------------------------------
# Tenant / Multi-Brand
# ---------------------------------------------------------------------------

class Tenant(db.Model):
    """A company using Shunya OS. Completely isolated data namespace."""
    __tablename__ = "tenants"
    __table_args__ = (Index("ix_tenants_slug", "slug", unique=True),)

    id = Column(Integer, primary_key=True)
    company_name = Column(String(255), nullable=False)
    slug = Column(String(120), unique=True, nullable=False)
    business_type = Column(String(60), default="other")  # travel, hospital, school, retail...
    parent_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    domain = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    plan = Column(String(30), default=TenantPlan.FREE.value)
    max_team_members = Column(Integer, default=5)
    max_storage_mb = Column(Integer, default=500)
    max_ai_calls_daily = Column(Integer, default=100)
    logo_url = Column(String(500), default="")
    theme_config = Column(JSONB, default=dict)  # primary_color, accent, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    children = relationship("Tenant", backref="parent", remote_side=[id], lazy="select")
    team_members = relationship("TeamMember", backref="tenant", lazy="select", cascade="all,delete-orphan")
    entity_definitions = relationship("EntityDefinition", backref="tenant", lazy="select", cascade="all,delete-orphan")
    entities = relationship("Entity", backref="tenant", lazy="select", cascade="all,delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "company_name": self.company_name, "slug": self.slug,
            "business_type": self.business_type, "parent_id": self.parent_id,
            "is_active": self.is_active, "plan": self.plan, "logo_url": self.logo_url,
            "theme_config": self.theme_config or {},
        }

# ---------------------------------------------------------------------------
# Team Members & Auth
# ---------------------------------------------------------------------------

class TeamMember(db.Model):
    """A user belonging to a tenant."""
    __tablename__ = "team_members"
    __table_args__ = (
        Index("ix_team_members_email", "email"),
        Index("ix_team_members_tenant_email", "tenant_id", "email", unique=True),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    password_hash = Column(String(128), nullable=True)
    role = Column(String(30), default=UserRole.AGENT.value)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String(500), default="")
    preferences = Column(JSONB, default=dict)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("UserSession", backref="user", lazy="dynamic", cascade="all,delete-orphan")
    oauth_accounts = relationship("OAuthAccount", backref="user", lazy="dynamic", cascade="all,delete-orphan")

    def set_password(self, password: str):
        salt = secrets.token_hex(16)
        self.password_hash = f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"

    def check_password(self, password: str) -> bool:
        if not self.password_hash or "$" not in self.password_hash:
            return False
        salt, hsh = self.password_hash.split("$", 1)
        return hsh == hashlib.sha256((salt + password).encode()).hexdigest()

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "phone": self.phone,
                "role": self.role, "is_active": self.is_active, "avatar_url": self.avatar_url}

class OAuthAccount(db.Model):
    """Linked OAuth accounts (Google, Apple, etc.)"""
    __tablename__ = "oauth_accounts"
    __table_args__ = (Index("ix_oauth_provider_id", "provider", "provider_id", unique=True),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("team_members.id"), nullable=False)
    provider = Column(String(30), nullable=False)  # google, apple
    provider_id = Column(String(255), nullable=False)
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSession(db.Model):
    """Active user sessions (multi-session support)."""
    __tablename__ = "user_sessions"
    # token index handled by unique + index on column

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("team_members.id"), nullable=False)
    token = Column(String(128), unique=True, nullable=False, index=True)
    device_info = Column(String(500), default="")
    ip_address = Column(String(45), default="")
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class LoginCode(db.Model):
    """One-time codes for OTP and magic link auth."""
    __tablename__ = "login_codes"
    # code index handled by column(index=True)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    code = Column(String(64), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # otp, magic_link
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Entity Model (Generic — all business types)
# ---------------------------------------------------------------------------

class EntityDefinition(db.Model):
    """Schema definition for a business entity type."""
    __tablename__ = "entity_definitions"
    __table_args__ = (Index("ix_entity_def_type_tenant", "tenant_id", "type", unique=True),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    type = Column(String(60), nullable=False)  # lead, patient, student, order...
    label = Column(String(120), nullable=False)  # "Lead", "Patient", "Student"
    label_plural = Column(String(120), default="")
    icon = Column(String(10), default="📋")
    schema = Column(JSONB, default=list)  # field definitions
    statuses = Column(JSONB, default=list)  # status flow
    layout = Column(String(30), default="table")  # table, kanban, calendar, cards
    primary_field = Column(String(60), default="name")  # field used in summaries
    searchable_fields = Column(JSONB, default=list)  # fields included in search
    default_sort = Column(String(60), default="created_at")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entities = relationship("Entity", backref="definition", lazy="dynamic",
                            foreign_keys="Entity.definition_id", cascade="all,delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "type": self.type, "label": self.label,
            "label_plural": self.label_plural, "icon": self.icon,
            "schema": self.schema, "statuses": self.statuses,
            "layout": self.layout, "primary_field": self.primary_field,
            "searchable_fields": self.searchable_fields, "is_active": self.is_active,
        }

class Entity(db.Model):
    """A single record of any entity type (lead, patient, student, order...)."""
    __tablename__ = "entities"
    __table_args__ = (
        Index("ix_entities_tenant_type", "tenant_id", "definition_id"),
        Index("ix_entities_status", "status"),
        Index("ix_entities_assigned", "assigned_to"),
        Index("ix_entities_created", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    definition_id = Column(Integer, ForeignKey("entity_definitions.id"), nullable=False)
    code = Column(String(30), nullable=True)  # e.g. PC11072601
    status = Column(String(30), default="new")
    assigned_to = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    data = Column(JSONB, default=dict)  # ALL field values here
    ai_summary = Column(Text, default="")
    tags = Column(JSONB, default=list)
    is_archived = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Dynamic code prefix per tenant
    code_prefix = Column(String(10), default="PC")

    activities = relationship("ActivityLog", backref="entity", lazy="dynamic", cascade="all,delete-orphan")
    files = relationship("File", backref="entity", lazy="dynamic", cascade="all,delete-orphan")
    messages = relationship("Message", backref="entity", lazy="dynamic", cascade="all,delete-orphan")

    @property
    def display_name(self) -> str:
        """Return the primary field value for display."""
        if self.definition and self.definition.primary_field:
            return self.data.get(self.definition.primary_field, self.code or f"#{self.id}")
        return self.code or f"#{self.id}"

    def to_dict(self):
        return {
            "id": self.id, "code": self.code, "entity_type": self.definition.type if self.definition else None,
            "status": self.status, "assigned_to": self.assigned_to, "data": self.data,
            "ai_summary": self.ai_summary, "tags": self.tags, "is_archived": self.is_archived,
            "created_by": self.created_by, "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# ---------------------------------------------------------------------------
# Entity Code Generator
# ---------------------------------------------------------------------------

def next_entity_code(session, tenant_id: int, prefix: str = "PC") -> str:
    """Generate space-free entity code: PC{DD}{MM}{YY}{##}"""
    today = date.today()
    date_part = f"{today.day:02d}{today.month:02d}{today.year % 100:02d}"
    prefix_full = f"{prefix}{date_part}"

    count = session.query(db.func.count(Entity.id)).filter(
        Entity.tenant_id == tenant_id,
        Entity.created_at >= datetime(today.year, today.month, today.day),
        Entity.created_at < datetime(today.year, today.month, today.day + 1),
    ).scalar() or 0

    return f"{prefix_full}{count + 1:02d}"

# ---------------------------------------------------------------------------
# Activity Log
# ---------------------------------------------------------------------------

class ActivityLog(db.Model):
    """Cross-entity audit trail."""
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_entity", "entity_id"),
        Index("ix_activity_tenant", "tenant_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    action = Column(String(60), nullable=False)  # created, updated, status_changed, message_sent...
    detail = Column(Text, default="")
    metadata_json = Column(JSONB, default=dict)
    governance_level = Column(String(20), default="auto")  # draft, auto, govern
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Files / Documents
# ---------------------------------------------------------------------------

class File(db.Model):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(60), default="")
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), default="")
    extracted_text = Column(Text, default="")
    uploaded_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Messages (client <-> team)
# ---------------------------------------------------------------------------

class Message(db.Model):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # team, client, system, ai
    sender_id = Column(Integer, nullable=True)
    channel = Column(String(30), default="app")  # app, whatsapp, telegram, email
    content = Column(Text, nullable=False)
    is_from_client = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notification(db.Model):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, default="")
    icon = Column(String(10), default="🔔")
    link = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Knowledge Base (compounding intelligence)
# ---------------------------------------------------------------------------

class KnowledgeEntry(db.Model):
    """Stored knowledge from AI interactions."""
    __tablename__ = "knowledge_entries"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source = Column(String(30), default="ai_generated")  # internal, web, ai_generated
    source_url = Column(String(500), nullable=True)
    confidence = Column(Float, default=0.0)
    verified_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    use_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ---------------------------------------------------------------------------
# Feedback / Corrections
# ---------------------------------------------------------------------------

class AIFeedback(db.Model):
    """User feedback on AI responses."""
    __tablename__ = "ai_feedback"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1 (thumbs up) or -1 (thumbs down)
    correction = Column(Text, nullable=True)
    knowledge_entry_id = Column(Integer, ForeignKey("knowledge_entries.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Entity Modules (user-created via Module Builder)
# ---------------------------------------------------------------------------

class EntityModule(db.Model):
    """A module created by the user via Module Builder."""
    __tablename__ = "entity_modules"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(Text, default="")
    definition_schema = Column(JSONB, default=dict)  # entity definition payload
    is_official = Column(Boolean, default=False)  # true for built-in modules
    is_published = Column(Boolean, default=False)  # published to marketplace
    install_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    created_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Automations
# ---------------------------------------------------------------------------

class Automation(db.Model):
    """User-configured automations triggered by events."""
    __tablename__ = "automations"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(120), nullable=False)
    trigger_event = Column(String(60), nullable=False)  # status_changed, payment_received, etc.
    trigger_filters = Column(JSONB, default=dict)
    actions = Column(JSONB, nullable=False)  # [{type: "send_message", ...}]
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Supplier / Payment Models
# ---------------------------------------------------------------------------

class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(60), default="")
    contact = Column(String(255), default="")
    email = Column(String(255), default="")
    phone = Column(String(30), default="")
    city = Column(String(120), default="")
    gstin = Column(String(30), default="")
    payment_terms = Column(String(120), default="")
    notes = Column(Text, default="")
    rating = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(db.Model):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    amount = Column(Numeric(12, 2), default=0)
    currency = Column(String(10), default="INR")
    type = Column(String(30), default="guest_payment")  # guest_payment, supplier_payment
    gateway = Column(String(30), default="")
    gateway_ref = Column(String(255), default="")
    status = Column(String(30), default="pending")
    notes = Column(Text, default="")
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    invoice_number = Column(String(60), nullable=False)
    total_amount = Column(Numeric(12, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax = Column(Numeric(12, 2), default=0)
    discount = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), default=0)
    currency = Column(String(10), default="INR")
    status = Column(String(30), default="pending")  # pending, paid, cancelled
    pdf_path = Column(String(500), default="")
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# Client Portal
# ---------------------------------------------------------------------------

class ClientUser(db.Model):
    __tablename__ = "client_users"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    otp_hash = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
