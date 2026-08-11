"""
SHUNYA OS — Data Layer

Five core models + ActivityLog for lead history tracking.
All tables use created_at + updated_at timestamps.
"""

import re
from datetime import date, datetime, timedelta
from enum import Enum as PyEnum
from typing import Optional
from app import db
from sqlalchemy import Numeric, func, Index, CheckConstraint, text


# ---------------------------------------------------------------------------
# Enums (string-based for DB compat, typed for code safety)
# ---------------------------------------------------------------------------

class LeadStatus(str, PyEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CONVERTED = "converted"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class InvoiceStatus(str, PyEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    VOID = "void"
    OVERDUE = "overdue"


class LeadSource(str, PyEnum):
    TELEGRAM = "telegram"
    MANUAL = "manual"
    API = "api"
    EMAIL = "email"


# ---------------------------------------------------------------------------
# Lead
# ---------------------------------------------------------------------------

class Lead(db.Model):
    """Customer inquiry / booking lead. Auto-coded with PC{DD}{MM}{YY}{##}."""

    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_status_created", "status", "created_at"),
        Index("ix_leads_source_created", "source", "created_at"),
        Index("ix_leads_destination", "destination"),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    source = db.Column(db.String(30), default=LeadSource.TELEGRAM.value)
    customer_name = db.Column(db.String(255), index=True)
    phone = db.Column(db.String(30), index=True)
    email = db.Column(db.String(255))
    destination = db.Column(db.String(255))
    pax = db.Column(db.String(100))
    dates = db.Column(db.String(255))
    budget = db.Column(Numeric(12, 2), default=0)
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default=LeadStatus.NEW.value, index=True)
    assigned_to = db.Column(db.String(120))
    # PROD-42: link lead to generic Entity
    entity_id = db.Column(db.Integer, nullable=True)
    # PROD-30: outcome of the lead execution
    outcome = db.Column(db.String(120), nullable=True)
    # PROD-31: lead lifecycle stage
    stage = db.Column(db.String(50), default="new")
    # Person compatibility (Phase 1)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)
    person = db.relationship("Person", backref="leads", lazy="select")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    activities = db.relationship("ActivityLog", backref="lead", lazy="dynamic", cascade="all,delete-orphan")

    def __repr__(self):
        return f"<Lead {self.code} [{self.status}] {self.customer_name or '?'}>"

    def to_dict(self, include_payments=False, include_invoices=False) -> dict:
        d = {
            "id": self.id,
            "code": self.code,
            "source": self.source,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "email": self.email,
            "destination": self.destination,
            "pax": self.pax,
            "dates": self.dates,
            "budget": float(self.budget or 0),
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
        }
        if include_payments:
            d["payments"] = [p.to_dict() for p in self.payments]
        if include_invoices:
            d["invoices"] = [i.to_dict() for i in self.invoices]
        return d

    @property
    def total_revenue(self) -> float:
        return float(
            db.session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.lead_id == self.id, Payment.type == PaymentType.GUEST.value)
            .scalar()
            or 0
        )
    def log_activity(self, action: str, detail: str = "", user: str = ""):
        """Helper: log an activity entry against this lead."""
        log = ActivityLog(lead_id=self.id, action=action, detail=detail, user=user)
        db.session.add(log)
        db.session.commit()


# PROD-42: auto-create Entity when a Lead is created
@db.event.listens_for(Lead, 'init')
def _lead_auto_create_entity(target, args, kwargs):
    """Auto-create a generic Entity for every new Lead."""
    from app.core.entity import Entity
    entity = Entity(type="lead", state=kwargs.get("stage", "new"), data={})
    target._pending_entity = entity


@db.event.listens_for(Lead, 'after_insert')
def _lead_attach_entity(mapper, connection, target):
    """Insert the pending Entity and link it to the Lead."""
    entity = getattr(target, '_pending_entity', None)
    if entity is not None:
        from app.core.entity import Entity as EntityClass
        # Insert entity via direct SQL
        result = connection.execute(
            EntityClass.__table__.insert().values(
                type=entity.type,
                state=entity.state,
                data=entity.data
            )
        )
        entity_id = result.inserted_primary_key[0]
        # Update lead's entity_id
        connection.execute(
            target.__table__.update().where(
                target.__table__.c.id == target.id
            ).values(entity_id=entity_id)
        )


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

class Supplier(db.Model):
    """Vendor catalog: hotels, transport, activities, vendors."""

    __tablename__ = "suppliers"
    __table_args__ = (
        Index("ix_suppliers_city_category", "city", "category"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    category = db.Column(db.String(120))  # hotel / flight / transport / activity / venue
    contact = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    city = db.Column(db.String(120))
    gstin = db.Column(db.String(50))  # GST number (India)
    payment_terms = db.Column(db.String(255))
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Supplier {self.name} [{self.category}] {self.city}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "contact": self.contact,
            "email": self.email,
            "phone": self.phone,
            "city": self.city,
            "gstin": self.gstin,
            "payment_terms": self.payment_terms,
            "rating": self.rating,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------

class TaskList(db.Model):
    """Grouped task lists for checklists, lead onboarding, and team workflows."""

    __tablename__ = "task_lists"
    __table_args__ = (
        Index("ix_task_lists_created", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True)
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tasks = db.relationship("Task", backref="task_list", lazy="dynamic",
                            cascade="all,delete-orphan",
                            order_by="Task.created_at")

    def __repr__(self):
        return f"<TaskList #{self.id} {self.name}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "lead_id": self.lead_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "task_count": self.tasks.count(),
        }


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task(db.Model):
    """Individual checklist item within a TaskList."""

    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_list_status", "task_list_id", "status"),
        Index("ix_tasks_assigned", "assigned_to"),
        Index("ix_tasks_due", "due_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    # PROD-27: link task to lead
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True)
    # PROD-43: link task to generic Entity
    entity_id = db.Column(db.Integer, nullable=True)
    task_list_id = db.Column(db.Integer, db.ForeignKey("task_lists.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    assigned_to = db.Column(db.String(120))
    priority = db.Column(db.String(20), default="medium")  # low / medium / high / urgent
    status = db.Column(db.String(30), default="pending")   # pending / in_progress / completed / cancelled
    sort_order = db.Column(db.Integer, default=0)
    due_date = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Task #{self.id} [{self.status}] {self.title}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_list_id": self.task_list_id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "priority": self.priority,
            "status": self.status,
            "sort_order": self.sort_order,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class NotificationType(str, PyEnum):
    LEAD_CREATED = "lead_created"
    PAYMENT_RECEIVED = "payment_received"
    STATUS_CHANGED = "status_changed"
    TASK_ASSIGNED = "task_assigned"
    CELEBRATION = "celebration"
    SYSTEM = "system"




class PersonIdentity(db.Model):
    """FDA4: Canonical identity claim storage.

    Every identity claim (email, phone, name, alias, external ID) is stored
    here with full provenance. Conflicting claims remain visible.
    """
    __tablename__ = "person_identities"
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"))
    identity_type = db.Column(db.String(32), nullable=False)
    identity_value = db.Column(db.String(255), nullable=False)
    normalized_value = db.Column(db.String(255), nullable=False, index=True)
    source = db.Column(db.String(60), nullable=True)
    source_id = db.Column(db.String(255), nullable=True)
    confidence = db.Column(db.Float, default=1.0)
    metadata_json = db.Column(db.Text, nullable=True)
    verification_state = db.Column(db.String(32), default="unverified")
    def __repr__(self):
        return f"<PersonIdentity #{self.id} {self.identity_type}:{self.identity_value}>"
class Notification(db.Model):
    """In-app notification for users, with optional lead/tenant scoping."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read", "created_at"),
        Index("ix_notifications_lead", "lead_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True)
    type = db.Column(db.String(30), default=NotificationType.SYSTEM.value, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, default="")
    icon = db.Column(db.String(50), default="🔔")
    link = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    lead = db.relationship("Lead", backref="notifications", lazy="select")

    def __repr__(self):
        return f"<Notification #{self.id} [{self.type}] {self.title[:50]}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "lead_id": self.lead_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "icon": self.icon,
            "link": self.link,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------



class Document(db.Model):
    """Uploaded documents with AI-extracted text and structured data."""

    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_lead", "lead_id"),
        Index("ix_documents_classification", "classification"),
        Index("ix_documents_created", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True, index=True)
    filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(1000), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # pdf / docx / image / text
    extracted_text = db.Column(db.Text, default="")
    structured_data = db.Column(db.Text, default="")  # JSON string
    classification = db.Column(db.String(50), default="other")
    uploaded_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    lead = db.relationship("Lead", backref=db.backref("documents", lazy="dynamic", cascade="all,delete-orphan"))

    def __repr__(self):
        return f"<Document #{self.id} {self.filename} [{self.classification}]>"

    def to_dict(self) -> dict:
        import json
        struct = {}
        try:
            if self.structured_data:
                struct = json.loads(self.structured_data)
        except (json.JSONDecodeError, TypeError):
            struct = {}
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "extracted_text": self.extracted_text,
            "structured_data": struct,
            "classification": self.classification,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# ActivityLog
# ---------------------------------------------------------------------------

class ActivityLog(db.Model):
    """Audit trail for every lead — captures state changes, notes, actions."""

    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_lead_created", "lead_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=False)
    action = db.Column(db.String(60), nullable=False)  # created / status_changed / payment_received / note_added / proposal_sent
    detail = db.Column(db.Text, default="")
    user = db.Column(db.String(120), default="")  # who performed the action
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ActivityLog {self.action} on lead #{self.lead_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "action": self.action,
            "detail": self.detail,
            "user": self.user,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Celebration — System-level wins and celebrations
# ---------------------------------------------------------------------------

class Celebration(db.Model):
    """A recorded win or celebration event, auto-detected or manually created."""

    __tablename__ = "celebrations"
    __table_args__ = (
        Index("ix_celebrations_type_created", "type", "created_at"),
        Index("ix_celebrations_lead", "lead_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(30), nullable=False, default="generic", index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, default="")
    icon = db.Column(db.String(20), default="🎉")
    animation = db.Column(db.String(30), default="woosh")
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True)
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    lead = db.relationship("Lead", backref="celebrations", lazy="select")

    def __repr__(self):
        return f"<Celebration #{self.id} [{self.type}] {self.title[:50]}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "icon": self.icon,
            "animation": self.animation,
            "lead_id": self.lead_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Person — Unified Human Identity (Phase 1)
# ---------------------------------------------------------------------------


class Person(db.Model):
    """Canonical human identity. One Person = one human."""
    __tablename__ = "persons"
    __table_args__ = (
        Index("ix_person_tenant", "tenant_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    canonical_name = db.Column(db.String(255), nullable=False, index=True)
    preferred_name = db.Column(db.String(255), default="", index=True)
    identity_type = db.Column(db.String(32), nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="active", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship





    def __repr__(self):
        return f"<Person #{self.id} {self.canonical_name}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "canonical_name": self.canonical_name,
            "preferred_name": self.preferred_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }







class IntakeSession(db.Model):
    """Lifecycle model for a data intake operation."""
    __tablename__ = "intake_sessions"
    __table_args__ = (
        Index("ix_intake_tenant", "tenant_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    source_type = db.Column(db.String(30), nullable=False, index=True)  # csv, xlsx, manual
    source_name = db.Column(db.String(255), default="")
    source_checksum = db.Column(db.String(64), default="")
    row_count = db.Column(db.Integer, default=0)
    column_names = db.Column(db.Text, default="")  # JSON array
    status = db.Column(db.String(30), default="received", index=True)
    summary = db.Column(db.Text, default="")  # JSON blob for import proposal
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Proposal versioning (Phase 1A hardening)
    proposal_version = db.Column(db.Integer, default=0)
    proposal_generated_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.String(120), default="")
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_proposal_version = db.Column(db.Integer, default=0)

    # Lifecycle states
    # RECEIVED → PROFILED → MAPPING_REQUIRED → READY_FOR_REVIEW → APPROVED → IMPORTING → COMPLETED
    #                                                                                      → FAILED
    # Any state → CANCELLED

    def __repr__(self):
        return f"<IntakeSession #{self.id} [{self.status}] {self.source_type}:{self.source_name}>"

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "source_checksum": self.source_checksum,
            "row_count": self.row_count,
            "column_names": json.loads(self.column_names) if self.column_names else [],
            "status": self.status,
            "summary": json.loads(self.summary) if self.summary else {},
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class IntakeCandidate(db.Model):
    """A single row candidate from an intake session, before governed commit."""
    __tablename__ = "intake_candidates"
    __table_args__ = (
        Index("ix_ic_session", "session_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("intake_sessions.id"), nullable=False, index=True)
    row_index = db.Column(db.Integer, default=0)
    raw_data = db.Column(db.Text, default="")  # JSON of original row
    normalized_data = db.Column(db.Text, default="")  # JSON of normalized fields
    classification = db.Column(db.String(30), default="unknown")  # customer, employee, unknown
    identity_status = db.Column(db.String(30), default="unknown")  # MATCHED, NO_MATCH, AMBIGUOUS, INSUFFICIENT_IDENTITY
    matched_person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)
    identity_conflict = db.Column(db.Text, default="")  # JSON describing conflict
    validation_status = db.Column(db.String(30), default="info")
    validation_messages = db.Column(db.Text, default="")  # JSON array
    duplicate_type = db.Column(db.String(30), default="")  # SOURCE_DUPLICATE, IDENTITY_DUPLICATE, etc.
    duplicate_group = db.Column(db.String(64), default="")
    import_status = db.Column(db.String(30), default="pending")  # pending, approved, blocked, imported, skipped
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    session = db.relationship("IntakeSession", backref="candidates", lazy="select")
    matched_person = db.relationship("Person", backref="intake_candidates", lazy="select")

    def __repr__(self):
        return f"<IntakeCandidate #{self.id} session={self.session_id} row={self.row_index}>"


class IntakeFieldMapping(db.Model):
    """Mapping from a source column to a canonical target field."""
    __tablename__ = "intake_field_mappings"
    __table_args__ = (
        Index("ix_ifm_session", "session_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("intake_sessions.id"), nullable=False)
    source_column = db.Column(db.String(255), nullable=False)
    target_field = db.Column(db.String(255), default="")  # canonical field path
    target_domain = db.Column(db.String(60), default="")  # person, identity, customer
    mapping_status = db.Column(db.String(30), default="unmapped")  # mapped, unmapped, ignored
    mapping_method = db.Column(db.String(30), default="auto")  # auto, manual, alias
    confidence = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IntakeFieldMapping #{self.id} {self.source_column} → {self.target_field}>"


# ---------------------------------------------------------------------------
# Inquiry Code Generator
# ---------------------------------------------------------------------------

def next_inquiry_code(session) -> str:
    """
    Generate space-free inquiry code: PC{DD}{MM}{YY}{##}

    Examples:
        PC10072601  (July 10, 2026 — first lead of the day)
        PC10072602  (second lead of the day)
        PC11072601  (next day, counter resets)
    """
    today = date.today()
    prefix = f"PC{today.day:02d}{today.month:02d}{today.year % 100:02d}"

    count = (
        session.query(func.count(Lead.id))
        .filter(
            Lead.created_at >= datetime(today.year, today.month, today.day),
            Lead.created_at < datetime(today.year, today.month, today.day) + timedelta(days=1),
        )
        .scalar()
        or 0
    ) + 1
    return f"{prefix}{count:02d}"


# ═══════════════════════════════════════════════════════════════════════════════
# FOR-2A Canonical Consolidation — Organization Models
# ═══════════════════════════════════════════════════════════════════════════════


class Organization(db.Model):
    """An organization (canonical successor to Tenant).

    Everything in SHUNYA belongs to an Organization.
    Industry-specific behaviour belongs in Industry Packs.
    """
    __tablename__ = "organizations"
    __table_args__ = (
        Index("ix_org_slug", "slug", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    business_type = db.Column(db.String(60), default="")

    # Branding
    logo_url = db.Column(db.String(500), default="")
    brand_color = db.Column(db.String(20), default="#2563eb")
    brand_color_secondary = db.Column(db.String(20), default="#7c3aed")
    brand_tagline = db.Column(db.String(500), default="")
    brand_description = db.Column(db.Text, default="")

    # Business info
    tax_id = db.Column(db.String(100), default="")
    registration_number = db.Column(db.String(100), default="")
    phone = db.Column(db.String(60), default="")
    email = db.Column(db.String(255), default="")
    website = db.Column(db.String(500), default="")
    address = db.Column(db.Text, default="")
    city = db.Column(db.String(120), default="")
    state = db.Column(db.String(120), default="")
    country = db.Column(db.String(120), default="")
    postal_code = db.Column(db.String(30), default="")

    # Settings
    timezone = db.Column(db.String(60), default="UTC")
    currency = db.Column(db.String(10), default="INR")
    date_format = db.Column(db.String(20), default="DD/MM/YYYY")
    is_active = db.Column(db.Boolean, default=True)
    max_members = db.Column(db.Integer, default=10)
    ai_enabled = db.Column(db.Boolean, default=True)
    ai_config = db.Column(db.Text, default="{}")

    # Legacy linkage
    legacy_tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)

    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "slug": self.slug,
            "business_type": self.business_type,
            "logo_url": self.logo_url, "brand_color": self.brand_color,
            "brand_color_secondary": self.brand_color_secondary,
            "brand_tagline": self.brand_tagline,
            "brand_description": self.brand_description,
            "tax_id": self.tax_id, "phone": self.phone, "email": self.email,
            "website": self.website, "city": self.city, "country": self.country,
            "currency": self.currency, "timezone": self.timezone,
            "is_active": self.is_active, "max_members": self.max_members,
            "ai_enabled": self.ai_enabled,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OrgMember(db.Model):
    """A person who belongs to an Organization.
    One SHUNYA Identity can be a member of multiple Organizations.
    Roles are per-organization.
    """
    __tablename__ = "org_members"
    __table_args__ = (
        Index("ix_orgmem_org", "organization_id"),
        Index("ix_orgmem_identity", "identity_id"),
        Index("ix_orgmem_org_identity", "organization_id", "identity_id", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    identity_id = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(255), default="")
    email = db.Column(db.String(255), default="")
    phone = db.Column(db.String(60), default="")
    role = db.Column(db.String(30), default="member")
    designation = db.Column(db.String(120), default="")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    invited_by = db.Column(db.String(64), default="")

    organization = db.relationship("Organization", backref="members", lazy="select")

    def to_dict(self):
        return {
            "id": self.id, "organization_id": self.organization_id,
            "identity_id": self.identity_id, "name": self.name,
            "email": self.email, "phone": self.phone, "role": self.role,
            "designation": self.designation, "department_id": self.department_id,
            "is_active": self.is_active,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }


class OrgInvitation(db.Model):
    """An invitation for a person to join an Organization."""
    __tablename__ = "org_invitations"
    __table_args__ = (
        Index("ix_orginvite_token", "token", unique=True),
        Index("ix_orginvite_email", "email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), default="")
    role = db.Column(db.String(30), default="member")
    token = db.Column(db.String(128), nullable=False, unique=True)
    status = db.Column(db.String(30), default="pending")
    invited_by = db.Column(db.String(64), default="")
    accepted_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "organization_id": self.organization_id,
            "email": self.email, "name": self.name, "role": self.role,
            "status": self.status, "invited_by": self.invited_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Department(db.Model):
    """A department or team within an Organization."""
    __tablename__ = "departments"
    __table_args__ = (
        Index("ix_dept_org", "organization_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    head_identity_id = db.Column(db.String(64), nullable=True)
    parent_department_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "organization_id": self.organization_id,
            "name": self.name, "description": self.description,
            "head_identity_id": self.head_identity_id,
            "parent_department_id": self.parent_department_id,
            "is_active": self.is_active,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FOR-1 Canonical Consolidation — Proposal & Knowledge Models
# ═══════════════════════════════════════════════════════════════════════════════


class Proposal(db.Model):
    """A business proposal / quotation for an opportunity.
    Lifecycle: draft → ai_generating → review → sent → accepted → booked → cancelled
    Linked to an organization and optionally a relationship.
    """
    __tablename__ = "proposals"
    __table_args__ = (
        Index("ix_proposals_org", "organization_id"),
        Index("ix_proposals_status", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True)
    version_number = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(30), default="draft", nullable=False)
    title = db.Column(db.String(500), default="")
    destination = db.Column(db.String(255), default="")
    duration_days = db.Column(db.Integer, default=0)
    pax = db.Column(db.String(100), default="")
    budget = db.Column(db.Numeric(12, 2), default=0)
    currency = db.Column(db.String(10), default="INR")
    itinerary_json = db.Column(db.Text, default="[]")
    pricing_json = db.Column(db.Text, default="{}")
    inclusions = db.Column(db.Text, default="")
    exclusions = db.Column(db.Text, default="")
    terms = db.Column(db.Text, default="")
    brand_color = db.Column(db.String(20), default="")
    brand_logo_url = db.Column(db.String(500), default="")
    cover_image_url = db.Column(db.String(500), default="")
    ai_generated = db.Column(db.Boolean, default=False)
    ai_model = db.Column(db.String(100), default="")
    ai_prompt = db.Column(db.Text, default="")
    generation_notes = db.Column(db.Text, default="")
    web_html = db.Column(db.Text, default="")
    pdf_path = db.Column(db.String(500), default="")
    sent_at = db.Column(db.DateTime, nullable=True)
    sent_via = db.Column(db.String(30), default="")
    viewed_at = db.Column(db.DateTime, nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_html=False):
        import json
        result = {
            "id": self.id, "organization_id": self.organization_id,
            "relationship_id": self.relationship_id,
            "version_number": self.version_number, "status": self.status,
            "title": self.title, "destination": self.destination,
            "duration_days": self.duration_days, "pax": self.pax,
            "budget": float(self.budget or 0), "currency": self.currency,
            "inclusions": self.inclusions, "exclusions": self.exclusions,
            "terms": self.terms, "brand_color": self.brand_color,
            "ai_generated": self.ai_generated, "ai_model": self.ai_model,
            "pdf_path": self.pdf_path,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "viewed_at": self.viewed_at.isoformat() if self.viewed_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        try:
            result["itinerary"] = json.loads(self.itinerary_json or "[]")
        except (json.JSONDecodeError, TypeError):
            result["itinerary"] = []
        try:
            result["pricing"] = json.loads(self.pricing_json or "{}")
        except (json.JSONDecodeError, TypeError):
            result["pricing"] = {}
        if include_html and self.web_html:
            result["web_html"] = self.web_html
        return result


class ProposalVersion(db.Model):
    """Immutable version history for proposals."""
    __tablename__ = "proposal_versions"

    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposals.id"), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)
    snapshot_json = db.Column(db.Text, default="{}")
    change_summary = db.Column(db.String(500), default="")
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class KnowledgeDocument(db.Model):
    """Uploaded knowledge document — brochures, SOPs, itineraries, contracts.
    Text is extracted and indexed for semantic search. Belongs to an organization.
    """
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index("ix_kd_org", "organization_id"),
        Index("ix_kd_category", "category"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    title = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(60), default="general")
    file_path = db.Column(db.String(500), default="")
    file_type = db.Column(db.String(60), default="")
    file_size_bytes = db.Column(db.BigInteger, default=0)
    extracted_text = db.Column(db.Text, default="")
    summary = db.Column(db.Text, default="")
    tags = db.Column(db.String(1000), default="")
    uploaded_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "organization_id": self.organization_id,
            "title": self.title, "category": self.category,
            "file_path": self.file_path, "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "summary": (self.summary or "")[:500],
            "tags": [t.strip() for t in (self.tags or "").split(",") if t.strip()],
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }