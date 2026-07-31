"""FOR-2C Relationship Intelligence Operating System — Data Models.

The Relationship is the universal, canonical representation of every human and
organizational interaction within an Organization. No future domain may introduce
another representation of a person or organization.

Everything connects to Relationship.
"""

from datetime import datetime
from app import db
from sqlalchemy import Index, Text, Numeric


# ── Relationship (canonical enhancement of legacy relationships) ──────────


class CanonicalRelationship(db.Model):
    """One relationship. One lifetime history. One AI memory.

    This is the canonical relationship model for SHUNYA.
    It supersedes the legacy Relationship model in app.models.
    
    Categories are configuration-driven (stored in RelationshipCategory).
    Core code must NEVER hardcode industry-specific relationship types.
    """
    __tablename__ = "rel_relationships"
    __table_args__ = (
        Index("ix_rel_org_type", "organization_id", "relationship_type"),
        Index("ix_rel_org_status", "organization_id", "status"),
        Index("ix_rel_email", "email"),
        Index("ix_rel_phone", "phone"),
        Index("ix_rel_name", "display_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False, index=True)

    # ── Identity ──
    display_name = db.Column(db.String(255), nullable=False, index=True)
    legal_name = db.Column(db.String(255), default="")
    preferred_name = db.Column(db.String(255), default="")
    relationship_type = db.Column(db.String(60), nullable=False, default="customer")
    is_organization = db.Column(db.Boolean, default=False)
    company_name = db.Column(db.String(255), default="")
    designation = db.Column(db.String(255), default="")

    # ── Contact ──
    email = db.Column(db.String(255), default="", index=True)
    email2 = db.Column(db.String(255), default="")
    email3 = db.Column(db.String(255), default="")
    phone = db.Column(db.String(60), default="", index=True)
    phone2 = db.Column(db.String(60), default="")
    phone3 = db.Column(db.String(60), default="")
    address_line1 = db.Column(db.String(500), default="")
    address_line2 = db.Column(db.String(500), default="")
    city = db.Column(db.String(120), default="")
    state = db.Column(db.String(120), default="")
    postal_code = db.Column(db.String(30), default="")
    country = db.Column(db.String(120), default="")
    website = db.Column(db.String(500), default="")
    social_linkedin = db.Column(db.String(500), default="")
    social_twitter = db.Column(db.String(500), default="")
    social_instagram = db.Column(db.String(500), default="")
    social_facebook = db.Column(db.String(500), default="")
    timezone = db.Column(db.String(60), default="")
    preferred_language = db.Column(db.String(10), default="en")
    preferred_currency = db.Column(db.String(10), default="")

    # ── Classification ──
    tags = db.Column(db.Text, default="")  # comma-separated
    segments = db.Column(db.Text, default="")  # comma-separated
    industries = db.Column(db.Text, default="")  # comma-separated
    source = db.Column(db.String(255), default="")
    referral_info = db.Column(db.Text, default="")

    # ── Business ──
    risk_level = db.Column(db.String(30), default="medium")
    priority = db.Column(db.Integer, default=0)
    internal_owner = db.Column(db.String(64), default="")  # identity_id of owner
    status = db.Column(db.String(30), default="active", index=True)
    notes = db.Column(db.Text, default="")

    # ── Custom attributes (JSON — organizations define their own fields) ──
    custom_attributes = db.Column(db.Text, default="{}")

    # ── Legacy linkage ──
    legacy_person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)
    legacy_relationship_id = db.Column(db.Integer, nullable=True)

    # ── Timestamps ──
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id, "organization_id": self.organization_id,
            "display_name": self.display_name, "legal_name": self.legal_name,
            "preferred_name": self.preferred_name,
            "relationship_type": self.relationship_type,
            "is_organization": self.is_organization,
            "company_name": self.company_name, "designation": self.designation,
            "email": self.email, "phone": self.phone,
            "address": self._format_address(),
            "city": self.city, "state": self.state, "country": self.country,
            "website": self.website,
            "timezone": self.timezone, "preferred_language": self.preferred_language,
            "preferred_currency": self.preferred_currency,
            "tags": [t.strip() for t in (self.tags or "").split(",") if t.strip()],
            "segments": [s.strip() for s in (self.segments or "").split(",") if s.strip()],
            "source": self.source,
            "risk_level": self.risk_level, "priority": self.priority,
            "internal_owner": self.internal_owner, "status": self.status,
            "notes": (self.notes or "")[:500],
            "custom_attributes": json.loads(self.custom_attributes or "{}"),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def _format_address(self):
        parts = [self.address_line1, self.address_line2, self.city,
                 self.state, self.postal_code, self.country]
        return ", ".join(p for p in parts if p)


# ── Relationship Category (config-driven types) ───────────────────────────


class RelationshipCategory(db.Model):
    """Configuration-driven relationship categories.

    Core code never hardcodes industry-specific types.
    Organizations and Industry Packs contribute categories here.
    """
    __tablename__ = "rel_categories"
    __table_args__ = (
        Index("ix_relcat_org_type", "organization_id", "type_key", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    type_key = db.Column(db.String(60), nullable=False)  # e.g. "customer", "supplier"
    display_label = db.Column(db.String(255), nullable=False)  # e.g. "Customer", "Supplier"
    icon = db.Column(db.String(60), default="person")
    color = db.Column(db.String(20), default="#6366f1")
    is_system = db.Column(db.Boolean, default=False)  # system-defined, user cannot delete
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "organization_id": self.organization_id,
            "type_key": self.type_key, "display_label": self.display_label,
            "icon": self.icon, "color": self.color,
            "is_system": self.is_system, "sort_order": self.sort_order,
        }


# ── Custom Field Definition (config-driven) ──────────────────────────────


class RelationshipField(db.Model):
    """Unlimited custom fields per organization — no code changes needed."""
    __tablename__ = "rel_custom_fields"
    __table_args__ = (
        Index("ix_relfield_org", "organization_id"),
        Index("ix_relfield_org_key", "organization_id", "field_key", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    field_key = db.Column(db.String(120), nullable=False)
    field_label = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.String(30), default="text")  # text, number, date, select, boolean
    field_options = db.Column(db.Text, default="[]")  # JSON array for select type
    is_required = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id, "organization_id": self.organization_id,
            "field_key": self.field_key, "field_label": self.field_label,
            "field_type": self.field_type,
            "field_options": json.loads(self.field_options or "[]"),
            "is_required": self.is_required, "sort_order": self.sort_order,
        }


# ── Lifetime Business Timeline ────────────────────────────────────────────


class TimelineEntry(db.Model):
    """Immutable historical record of every interaction with a Relationship.

    Nothing should ever be deleted — only appended.
    """
    __tablename__ = "rel_timeline"
    __table_args__ = (
        Index("ix_tl_rel", "relationship_id"),
        Index("ix_tl_org_time", "organization_id", "event_time"),
        Index("ix_tl_type", "event_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=False, index=True)
    event_type = db.Column(db.String(60), nullable=False, index=True)
    event_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    title = db.Column(db.String(500), default="")
    description = db.Column(db.Text, default="")
    reference_type = db.Column(db.String(60), default="")  # e.g. "proposal", "invoice", "note"
    reference_id = db.Column(db.Integer, nullable=True)
    metadata_json = db.Column(db.Text, default="{}")
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        import json
        return {
            "id": self.id, "organization_id": self.organization_id,
            "relationship_id": self.relationship_id,
            "event_type": self.event_type,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "title": self.title, "description": (self.description or "")[:500],
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "metadata": json.loads(self.metadata_json or "{}"),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── AI Memory ─────────────────────────────────────────────────────────────


class RelationshipMemory(db.Model):
    """Persistent AI memory for a single Relationship.

    The AI continuously builds understanding of this relationship.
    Memory belongs to the Organization — never globally, never across orgs.
    """
    __tablename__ = "rel_ai_memory"
    __table_args__ = (
        Index("ix_relmem_rel", "relationship_id", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=False, unique=True)
    memory_json = db.Column(db.Text, default="{}")  # full AI context
    summary = db.Column(db.Text, default="")  # AI-generated executive summary
    health_score = db.Column(db.Integer, default=50)  # 0-100
    engagement_score = db.Column(db.Integer, default=50)
    lifetime_value = db.Column(db.Numeric(15, 2), default=0)
    retention_risk = db.Column(db.Integer, default=50)
    last_ai_update = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id, "organization_id": self.organization_id,
            "relationship_id": self.relationship_id,
            "memory": json.loads(self.memory_json or "{}"),
            "summary": self.summary,
            "health_score": self.health_score,
            "engagement_score": self.engagement_score,
            "lifetime_value": float(self.lifetime_value or 0),
            "retention_risk": self.retention_risk,
            "last_ai_update": self.last_ai_update.isoformat() if self.last_ai_update else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Relationship Document (knowledge link) ───────────────────────────────


class RelationshipDocument(db.Model):
    """A document associated with a Relationship.

    Every uploaded document related to a relationship automatically connects here.
    """
    __tablename__ = "rel_documents"
    __table_args__ = (
        Index("ix_reldoc_rel", "relationship_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(60), default="general")
    file_path = db.Column(db.String(500), default="")
    file_type = db.Column(db.String(60), default="")
    file_size_bytes = db.Column(db.BigInteger, default=0)
    extracted_text = db.Column(db.Text, default="")
    uploaded_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "organization_id": self.organization_id,
            "relationship_id": self.relationship_id,
            "title": self.title, "category": self.category,
            "file_path": self.file_path, "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Duplicate Record (merge tracking) ────────────────────────────────────


class DuplicateGroup(db.Model):
    """Group of suspected duplicate relationships.

    Relationships within a group may be merged.
    Merges preserve complete history — no information is lost.
    """
    __tablename__ = "rel_duplicate_groups"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    primary_relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)
    merge_status = db.Column(db.String(30), default="pending")  # pending, merged, dismissed
    detection_method = db.Column(db.String(60), default="")  # email, phone, ai
    confidence = db.Column(db.Integer, default=0)
    resolved_by = db.Column(db.String(64), default="")
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class DuplicateCandidate(db.Model):
    """One relationship within a duplicate group."""
    __tablename__ = "rel_duplicate_candidates"
    __table_args__ = (
        Index("ix_dup_group", "group_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("rel_duplicate_groups.id"), nullable=False)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=False)
    match_reason = db.Column(db.String(255), default="")
    match_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)