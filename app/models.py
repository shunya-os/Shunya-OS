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
    brand_tagline = Column(String(500), default="")
    brand_description = Column(Text, default="")
    brand_color = Column(String(7), default="#2563eb")  # Primary brand color (hex)
    brand_color_secondary = Column(String(7), default="#7c3aed")  # Secondary brand color
    onboarding_completed = Column(Boolean, default=False)
    theme_config = Column(JSONB, default=dict)
    ai_config = Column(JSONB, default=dict)  # web_search_enabled, confidence_threshold, etc.
    business_type = Column(String(60), default="other")  # travel, hospital, school, retail...
    vertical_config = Column(JSONB, default=dict)  # vertical-specific defaults
    created_at = Column(DateTime, default=datetime.utcnow)

    # Business hierarchy
    owner_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)

    # Relationships
    children = relationship("Tenant", backref="parent", remote_side=[id], lazy="select")
    team_members = relationship("TeamMember", backref="tenant", lazy="select", cascade="all,delete-orphan",
                                foreign_keys="TeamMember.tenant_id")
    entity_definitions = relationship("EntityDefinition", backref="tenant", lazy="select", cascade="all,delete-orphan")
    entities = relationship("Entity", backref="tenant", lazy="select", cascade="all,delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "company_name": self.company_name, "slug": self.slug,
            "business_type": self.business_type, "parent_id": self.parent_id,
            "is_active": self.is_active, "plan": self.plan, "logo_url": self.logo_url,
            "theme_config": self.theme_config or {},
            "brand_tagline": self.brand_tagline or "",
            "vertical_config": self.vertical_config or {},
        }

# ---------------------------------------------------------------------------
# Business Hierarchy — Universal OS Structure
# ---------------------------------------------------------------------------
# A Person owns Businesses. A Business may belong to a BusinessGroup.
# A Business has Brands. A Brand gets a Tenant (Shunya OS instance).
#
# Person → BusinessGroup (optional, e.g. Reliance)
#        → Business (e.g. Jio)
#              → Brand (e.g. JioFiber)
#                    → Tenant (Shunya OS instance, data isolated)

class BusinessGroup(db.Model):
    """A collection of businesses under common ownership (e.g. Reliance Industries)."""
    __tablename__ = "business_groups"
    __table_args__ = (Index("ix_business_group_owner", "owner_id"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("team_members.id"), nullable=False)
    description = Column(Text, default="")
    industry = Column(String(60), default="")  # conglomerate, holding, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    businesses = relationship("Business", backref="group", lazy="select",
                               foreign_keys="Business.group_id")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "industry": self.industry}


class Business(db.Model):
    """A single business entity. Belongs to a Person or a BusinessGroup."""
    __tablename__ = "businesses"
    __table_args__ = (Index("ix_business_owner", "owner_id"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("team_members.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("business_groups.id"), nullable=True)
    business_type = Column(String(60), nullable=False)  # travel, hospital, legal, retail...
    description = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    brands = relationship("Brand", backref="business", lazy="select",
                           foreign_keys="Brand.business_id", cascade="all,delete-orphan")

    @property
    def tenant_count(self):
        return len([b for b in self.brands if b.tenants])

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "business_type": self.business_type,
            "group_id": self.group_id, "is_active": self.is_active,
            "brand_count": len(self.brands),
        }


class Brand(db.Model):
    """A brand under a Business. Gets its own Tenant (Shunya OS instance)."""
    __tablename__ = "brands"
    __table_args__ = (Index("ix_brand_business", "business_id"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    is_default = Column(Boolean, default=False)  # first brand = default
    description = Column(Text, default="")
    logo_url = Column(String(500), default="")
    brand_color = Column(String(7), default="#2563eb")
    brand_tagline = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    tenants = relationship("Tenant", backref="brand_rel", lazy="select",
                            foreign_keys="Tenant.brand_id")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "business_id": self.business_id,
            "is_default": self.is_default, "logo_url": self.logo_url,
            "tenant_count": len(self.tenants),
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
    code_prefix = Column(String(10), default="")  # auto-computed unique prefix for entity codes
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

# Special prefixes for built-in entity types (PC for Lead by user specification)
_BUILTIN_PREFIX_OVERRIDE = {
    "lead": "PC",
}

def _compute_entity_prefix(entity_type: str, existing_types: list[str]) -> str:
    """Compute a unique 2+ letter prefix for an entity type.
    
    Priority:
    1. Built-in override (e.g. lead → PC)
    2. First 2 letters of entity_type
    3. If conflict with any existing type, add 3rd letter
    4. Continue until unique or full name exhausted
    
    Example: lead → PC, opportunity → OPP, operations → OPE
    """
    if entity_type in _BUILTIN_PREFIX_OVERRIDE:
        return _BUILTIN_PREFIX_OVERRIDE[entity_type]
    
    normalized = entity_type.replace("_", "").replace("-", "")
    if not normalized:
        return entity_type[:4].upper()
    
    # Compute ALL prefixes atomically to avoid conflicts
    all_prefixes = compute_all_prefixes(existing_types + [entity_type])
    return all_prefixes.get(entity_type, normalized[:4].upper())


def compute_all_prefixes(entity_types: list[str]) -> dict[str, str]:
    """Compute unique prefixes for ALL entity types atomically.
    
    This ensures no two entity types get the same prefix.
    Built-in overrides (lead→PC) are applied first.
    Remaining types get first 2+ unique chars, shorter names first.
    """
    result = {}
    taken = set()
    
    # First pass: built-in overrides
    for et in entity_types:
        if et in _BUILTIN_PREFIX_OVERRIDE:
            p = _BUILTIN_PREFIX_OVERRIDE[et]
            result[et] = p
            taken.add(p)
    
    # Remaining: sort by length (shorter names first → less likely to conflict)
    remaining = sorted(
        [et for et in entity_types if et not in result],
        key=lambda x: (len(x), x)
    )
    
    for et in remaining:
        normalized = et.replace("_", "").replace("-", "")
        if not normalized:
            normalized = et[:4]
        
        prefix = None
        for length in range(2, min(len(normalized), 8) + 1):
            candidate = normalized[:length].upper()
            if candidate not in taken:
                prefix = candidate
                taken.add(candidate)
                break
        
        if prefix is None:
            prefix = normalized[:4].upper()
            # Make unique by appending number if still taken
            n = 1
            while prefix in taken:
                prefix = f"{normalized[:3].upper()}{n}"
                n += 1
            taken.add(prefix)
        
        result[et] = prefix
    
    return result


def ensure_entity_prefixes(session, tenant_id: int) -> None:
    """Compute and persist code_prefix for all entity definitions without one."""
    from app.models import EntityDefinition
    defs = session.query(EntityDefinition).filter(
        EntityDefinition.tenant_id == tenant_id,
    ).all()
    types = [d.type for d in defs]
    
    for d in defs:
        if not d.code_prefix:
            d.code_prefix = _compute_entity_prefix(d.type, types)
    
    session.commit()


def get_code_prefix(session, entity_type: str, tenant_id: int) -> str:
    """Get the unique code prefix for an entity type, computing it if missing."""
    from app.models import EntityDefinition
    d = session.query(EntityDefinition).filter(
        EntityDefinition.tenant_id == tenant_id,
        EntityDefinition.type == entity_type,
    ).first()
    
    if d:
        if not d.code_prefix:
            types = [row[0] for row in session.query(EntityDefinition.type).filter(
                EntityDefinition.tenant_id == tenant_id).all()]
            d.code_prefix = _compute_entity_prefix(entity_type, types)
            session.commit()
        return d.code_prefix
    
    return _compute_entity_prefix(entity_type, [entity_type])


def next_entity_code(session, tenant_id: int, entity_type: str = "lead", ref_date: date = None) -> str:
    """Generate entity code: {PREFIX}{DD}{MM}{YY}{##}
    
    Prefix derived from entity type (Lead → PC, others → first 2+ unique letters).
    Sequence is per type per day.
    """
    prefix = get_code_prefix(session, entity_type, tenant_id)
    today = ref_date or date.today()
    date_part = f"{today.day:02d}{today.month:02d}{today.year % 100:02d}"
    prefix_full = f"{prefix}{date_part}"

    count = session.query(db.func.count(Entity.id)).filter(
        Entity.tenant_id == tenant_id,
        Entity.definition.has(type=entity_type),
        Entity.created_at >= datetime(today.year, today.month, today.day),
        Entity.created_at < datetime(today.year, today.month, today.day + 1),
    ).scalar() or 0

    return f"{prefix_full}{count + 1:02d}"

# ---------------------------------------------------------------------------
# API Keys (Public API Key Management)
# ---------------------------------------------------------------------------

class ApiKey(db.Model):
    """API key for programmatic access to Shunya APIs."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(120), nullable=False)  # label like "Zapier", "Mobile App"
    key_hash = Column(String(64), nullable=False)  # SHA256 of the key
    key_prefix = Column(String(8), nullable=False)  # first 8 chars of key for display
    scopes = Column(JSONB, default=list)  # ["read:lead", "write:lead", "read:*"]
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)

    tenant = relationship("Tenant", backref="api_keys",
                          foreign_keys=[tenant_id])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "key_prefix": f"{self.key_prefix}...",
            "scopes": self.scopes or [],
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

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
    category = Column(String(50), default="general")
    meta_data = Column(Text, nullable=True)  # JSON blob
    file_type = Column(String(20), nullable=True)


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


# ---------------------------------------------------------------------------
# Webhook Engine
# ---------------------------------------------------------------------------

class WebhookLog(db.Model):
    """Delivery log of a webhook call."""
    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    event = Column(String(60), nullable=False)
    payload = Column(JSONB, default=dict)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, default="")
    duration_ms = Column(Integer, default=0)
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# User Mood / Health Check-in
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

class Webhook(db.Model):
    """Outgoing webhook — sends HTTP POST when events fire."""
    __tablename__ = "webhooks"
    __table_args__ = (Index("ix_webhook_tenant_event", "tenant_id", "event"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(120), nullable=False)
    url = Column(String(500), nullable=False)
    event = Column(String(60), nullable=False)
    entity_type = Column(String(60), default="*")
    headers = Column(JSONB, default=dict)
    secret = Column(String(64), default="")
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime, nullable=True)
    last_status = Column(Integer, nullable=True)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "url": self.url,
            "event": self.event, "entity_type": self.entity_type,
            "headers": self.headers, "is_active": self.is_active,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None,
            "last_status": self.last_status, "failure_count": self.failure_count,
        }
# RelationShip & Person Models — Compounding Relationship Intelligence
# ---------------------------------------------------------------------------
# Canonical: A customer relationship is continuous. A booking is temporary.
# An opportunity has a lifecycle. RELATIONSHIP is the deepest domain object.
# ---------------------------------------------------------------------------

class Person(db.Model):
    """An individual human — identity independent of any organization.

    A person exists whether or not they have a relationship with any Shunya tenant.
    The same person may have relationships with multiple tenants (multi-tenant Shunya).
    """
    __tablename__ = "persons"
    __table_args__ = (Index("ix_persons_email", "email"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    alternate_phone = Column(String(30), nullable=True)
    photo_url = Column(String(500), default="")
    birthdate = Column(String(20), nullable=True)  # YYYY-MM-DD
    passport = Column(String(60), nullable=True)
    govt_id = Column(String(60), nullable=True)
    nationality = Column(String(60), default="IN")
    preferred_language = Column(String(10), default="en")
    is_test = Column(Boolean, default=False)
    tags = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "email": self.email,
            "phone": self.phone, "photo_url": self.photo_url,
            "nationality": self.nationality, "tags": self.tags,
        }


class Relationship(db.Model):
    """The institutional bond between a Person and a Tenant (organization).

    THIS is the unit of compounding relationship intelligence.
    A person can have one relationship per tenant. The relationship outlives
    any single booking, opportunity, or employee. It carries lifetime memory.
    """
    __tablename__ = "relationships"
    __table_args__ = (
        Index("ix_rel_person_tenant", "person_id", "tenant_id", unique=True),
        Index("ix_rel_phone", "tenant_id", "phone"),
        Index("ix_rel_email", "tenant_id", "email"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)

    # Identity (may differ from Person — e.g. preferred name for this org)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)

    # Relationship metadata
    tenure_years = Column(Integer, default=0)
    health = Column(String(20), default="new")
    # new → learning → established → strong → at_risk → lapsed
    advisor_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    total_experiences = Column(Integer, default=0)
    total_referrals = Column(Integer, default=0)
    last_meaningful_interaction = Column(DateTime, nullable=True)

    # Communication
    preferred_channel = Column(String(20), default="whatsapp")
    communication_style = Column(String(60), default="")  # concise, detailed, formal, casual

    # Traveller graph — who travels under this relationship
    traveller_graph = Column(JSONB, default=dict)
    # {"self": {"person_id": 1, "name": "...", "birthdate": "..."},
    #  "spouse": {"person_id": 2, ...},
    #  "children": [{"name": "...", "birthdate": "..."}],
    #  "parents": [{"name": "..."}]}

    # Household / Family
    household_id = Column(Integer, ForeignKey("households.id"), nullable=True)

    # Status
    status = Column(String(20), default="active")  # active, inactive, lapsed, churned
    tags = Column(JSONB, default=list)

    created_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # FK relationships
    person = relationship("Person", backref="relationships", lazy="joined",
                          foreign_keys=[person_id])
    opportunities = relationship("Opportunity", backref="relationship", lazy="select",
                                 cascade="all,delete-orphan",
                                 foreign_keys="Opportunity.relationship_id")

    def to_dict(self):
        return {
            "id": self.id,
            "display_name": self.display_name or (self.person.name if self.person else ""),
            "email": self.email,
            "phone": self.phone,
            "tenure_years": self.tenure_years,
            "health": self.health,
            "total_experiences": self.total_experiences,
            "total_referrals": self.total_referrals,
            "preferred_channel": self.preferred_channel,
            "status": self.status,
            "tags": self.tags,
            "person": self.person.to_dict() if self.person else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Household(db.Model):
    """A family or household — multiple persons who travel/share together.

    Enables: family preferences, group booking patterns, referral networks,
    multi-person relationships that compound as a unit.
    """
    __tablename__ = "households"
    __table_args__ = (Index("ix_household_tenant", "tenant_id"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=True)  # e.g. "Nishesh Family"
    head_relationship_id = Column(Integer, ForeignKey("relationships.id"), nullable=True)
    members = Column(JSONB, default=list)
    # [{"relationship_id": 1, "role": "head", "since": "2020"},
    #  {"person_id": 2, "role": "spouse", "since": "2020"},
    #  {"person_id": 3, "role": "child", "since": "2022"}]
    shared_preferences = Column(JSONB, default=list)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RelationshipPreference(db.Model):
    """A stored preference for a relationship, with evidence and confidence.

    "Last time you preferred..." not "You always prefer..."
    Preferences belong to the relationship, not the person — they reflect
    how this person relates to this organization.
    """
    __tablename__ = "relationship_preferences"
    __table_args__ = (Index("ix_rel_pref_type", "relationship_id", "preference_type"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("relationships.id"), nullable=False)

    preference_type = Column(String(60), nullable=False)
    # hotel_location, travel_pace, budget_range, airline, room_category,
    # transfer_preference, decision_style, communication_style

    value = Column(Text, nullable=False)
    confidence = Column(String(20), default="medium")  # low, medium, high
    source = Column(String(30), default="observed")  # stated, observed, inferred, imported

    evidence = Column(JSONB, default=list)
    # [{"opportunity": "Thailand 2022", "action": "selected city centre hotel"},
    #  {"opportunity": "Dubai 2023", "action": "selected Downtown hotel"}]

    contradictions = Column(JSONB, default=list)
    # [{"opportunity": "Europe 2024", "note": "selected outskirts — budget constraint"}]

    last_confirmed = Column(DateTime, nullable=True)
    confirmed_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    notes = Column(Text, default="")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "preference_type": self.preference_type,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
            "evidence": self.evidence,
            "contradictions": self.contradictions,
            "last_confirmed": self.last_confirmed.isoformat() if self.last_confirmed else None,
        }


# ---------------------------------------------------------------------------
# Opportunity Domain — Current Intent Container
# ---------------------------------------------------------------------------

class Opportunity(db.Model):
    """A customer's current travel intent. Has a defined lifecycle.

    One relationship can have simultaneous opportunities: personal holiday,
    parents' pilgrimage, corporate offsite. The Opportunity carries current
    intent; the Relationship carries lifetime memory.

    Lifecycle: ENQUIRY → DISCOVERY → PLANNING → PROPOSAL → NEGOTIATION
              → BOOKING → EXPERIENCE → OUTCOME → CLOSED
              ↘ LOST at any stage
    """
    __tablename__ = "opportunities"
    __table_args__ = (
        Index("ix_opp_relationship", "relationship_id", "status"),
        Index("ix_opp_tenant_stage", "tenant_id", "status"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("relationships.id"), nullable=False)

    code = Column(String(30), nullable=True, index=True)

    # Core intent
    title = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=True)
    intent_description = Column(Text, default="")  # What the customer actually wants
    experience_mood = Column(String(60), default="")  # exploring, relaxing, adventure, luxury, cultural
    notes = Column(Text, default="")

    # Lifecycle
    stage = Column(String(30), default="enquiry", index=True)
    # enquiry, discovery, planning, proposal, negotiation, booking,
    # experience, outcome, closed, lost
    status = Column(String(20), default="open")  # open, won, lost, abandoned

    # Timeline
    target_dates = Column(JSONB, default=dict)
    duration_days = Column(Integer, nullable=True)

    # Budget
    estimated_budget = Column(Numeric(12, 2), nullable=True)
    actual_cost = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), default="INR")

    # People — with typed roles
    participants = Column(JSONB, default=list)
    # [{"person_id": 1, "role": "traveller", "name": "Nishesh"},
    #  {"person_id": 2, "role": "traveller", "name": "Spouse"},
    #  {"person_id": null, "role": "decision_maker", "name": "Nishesh"},
    #  {"person_id": null, "role": "payer", "name": "Nishesh"},
    #  {"person_id": 3, "role": "beneficiary", "name": "Parents"}]
    traveller_count = Column(Integer, default=1)
    decision_maker = Column(String(255), nullable=True)
    payer = Column(String(255), nullable=True)
    referrer = Column(String(255), nullable=True)

    # Progress
    assigned_to = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    probability = Column(Integer, default=50)  # 0-100
    risk = Column(String(20), default="low")  # low, medium, high

    # Decisions, quotes, bookings (JSONB for flexibility)
    decisions = Column(JSONB, default=list)
    quotes = Column(JSONB, default=list)
    bookings = Column(JSONB, default=list)

    # Key dates
    enquiry_date = Column(DateTime, nullable=True)
    booking_date = Column(DateTime, nullable=True)
    experience_start = Column(DateTime, nullable=True)
    experience_end = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    created_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    activities = relationship("OpportunityActivity", backref="opportunity", lazy="dynamic",
                              cascade="all,delete-orphan")
    experiences = relationship("Experience", backref="opportunity", lazy="select",
                               cascade="all,delete-orphan",
                               foreign_keys="Experience.opportunity_id")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "destination": self.destination,
            "stage": self.stage,
            "status": self.status,
            "experience_mood": self.experience_mood,
            "estimated_budget": float(self.estimated_budget) if self.estimated_budget else None,
            "actual_cost": float(self.actual_cost) if self.actual_cost else None,
            "traveller_count": self.traveller_count,
            "priority": self.priority,
            "probability": self.probability,
            "risk": self.risk,
            "assigned_to": self.assigned_to,
            "enquiry_date": self.enquiry_date.isoformat() if self.enquiry_date else None,
            "booking_date": self.booking_date.isoformat() if self.booking_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OpportunityActivity(db.Model):
    """Timeline entries for an opportunity."""
    __tablename__ = "opportunity_activities"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)

    activity_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    metadata_json = Column(JSONB, default=dict)

    created_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Experience Domain — WHAT THE CUSTOMER LIVED (not what we sold)
# ---------------------------------------------------------------------------
# Canonical: BOOKING = what we sold. EXPERIENCE = what the customer lived.
# These are not the same thing. The learning loop needs both.

class Experience(db.Model):
    """What the customer actually lived through during a trip.

    BOOKING records what was sold. EXPERIENCE records what happened.
    The gap between them is where learning lives.
    """
    __tablename__ = "experiences"
    __table_args__ = (Index("ix_exp_opportunity", "opportunity_id"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("relationships.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)

    title = Column(String(255), nullable=False)
    experience_type = Column(String(30), default="trip")  # trip, day_trip, event, service

    # Expectations (from the Booking)
    expectations = Column(JSONB, default=dict)
    # {"hotels": "Marriott Downtown", "flights": "EK507 09:00", "transfers": "Private"}

    # What actually happened
    delivered_reality = Column(JSONB, default=dict)
    # {"hotels": "Marriott Downtown (upgraded)", "flights": "EK507 (delayed 1hr)",
    #  "transfers": "Driver arrived 35min late"}

    # Events during experience
    events = Column(JSONB, default=list)
    # [{"date": "...", "type": "checkin", "status": "smooth"},
    #  {"date": "...", "type": "transfer", "status": "issue", "detail": "35min delay"}]

    # Exceptions and recovery
    exceptions = Column(JSONB, default=list)
    # [{"component": "transfer", "issue": "delay", "severity": "medium", "recovery": "compensated"}]
    recovery_actions = Column(JSONB, default=list)

    # Feedback
    feedback = Column(Text, default="")
    satisfaction_signals = Column(JSONB, default=list)
    # [{"source": "survey", "metric": "overall", "score": 4},
    #  {"source": "message", "text": "transfer was late", "sentiment": "negative"}]

    overall_rating = Column(Integer, nullable=True)  # 1-5
    would_recommend = Column(Boolean, nullable=True)

    # Timing
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    created_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    outcomes = relationship("Outcome", backref="experience", lazy="select",
                            cascade="all,delete-orphan",
                            foreign_keys="Outcome.experience_id")


# ---------------------------------------------------------------------------
# Observation Domain — Structured Expected vs Actual
# ---------------------------------------------------------------------------

class Observation(db.Model):
    """A structured observation: what was expected vs what actually happened.

    ActivityLog is an audit trail. Observation is intelligence input.
    Every execution should create an observation opportunity.
    """
    __tablename__ = "observations"
    __table_args__ = (Index("ix_obs_subject", "subject_type", "subject_id"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    subject_type = Column(String(30), nullable=False)  # opportunity, experience, task, execution
    subject_id = Column(Integer, nullable=False)

    event = Column(String(60), nullable=False)
    source = Column(String(30), nullable=False)  # system, human, ai, integration
    observer = Column(String(60), nullable=True)  # who/what observed it

    expected_state = Column(Text, default="")
    actual_state = Column(Text, default="")
    delta = Column(String(255), default="")  # the difference

    severity = Column(String(20), default="info")  # info, minor, medium, major, critical
    confidence = Column(String(20), default="high")  # low, medium, high

    metadata_json = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Outcome Domain — Compared Intent
# ---------------------------------------------------------------------------

class Outcome(db.Model):
    """The result of an experience or execution.

    Every meaningful process should answer:
    WHAT WERE WE TRYING TO ACHIEVE? WHAT ACTUALLY HAPPENED? WHAT WAS DIFFERENT? WHY?
    """
    __tablename__ = "outcomes"
    __table_args__ = (Index("ix_outcome_subject", "subject_type", "subject_id"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    subject_type = Column(String(30), nullable=False)  # opportunity, experience, execution
    subject_id = Column(Integer, nullable=False)
    experience_id = Column(Integer, ForeignKey("experiences.id"), nullable=True)

    goal = Column(Text, default="")
    expected_outcome = Column(Text, default="")
    actual_outcome = Column(Text, default="")

    result = Column(String(20), default="unknown")  # success, partial, failure, unknown
    reason = Column(Text, default="")

    customer_impact = Column(Text, default="")
    business_impact = Column(Text, default="")
    financial_impact = Column(Text, default="")

    lessons = Column(JSONB, default=list)
    # [{"lesson": "Confirm transfers in advance", "category": "ops", "priority": "high"}]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Learning Domain — Pattern → Proposal → Governance → Knowledge
# ---------------------------------------------------------------------------

class LearningCandidate(db.Model):
    """A detected pattern that MAY become organizational knowledge.

    OBSERVATION ≠ LEARNING. AI-detected pattern ≠ company truth.
    Learning proposes. Governance evaluates. Humans approve.
    """
    __tablename__ = "learning_candidates"
    __table_args__ = (Index("ix_learn_tenant_status", "tenant_id", "status"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    pattern = Column(Text, nullable=False)
    evidence = Column(JSONB, default=list)
    confidence = Column(Float, default=0.0)
    category = Column(String(60), default="pattern")  # pattern, anomaly, improvement, risk

    proposed_knowledge = Column(Text, default="")
    proposed_rule = Column(Text, default="")
    proposed_policy_change = Column(Text, default="")
    proposed_workflow_change = Column(Text, default="")

    status = Column(String(20), default="candidate")  # candidate, proposed, under_review, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, default="")

    source_observations = Column(JSONB, default=list)  # observation IDs
    related_outcomes = Column(JSONB, default=list)  # outcome IDs

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# User Mood / Check-in Tracker
# ---------------------------------------------------------------------------

class UserMoodCheckin(db.Model):
    """A daily mood/energy check-in from a team member.

    Stored as individual rows for trend analysis.
    """
    __tablename__ = "user_mood_checkins"
    __table_args__ = (
        Index("ix_mood_user_date", "tenant_id", "user_id", "created_at"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("team_members.id"), nullable=False)

    mood = Column(String(20), nullable=False)  # great, good, okay, rough, tough
    energy = Column(Integer, nullable=False)  # 1-5
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "mood": self.mood,
            "energy": self.energy,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
