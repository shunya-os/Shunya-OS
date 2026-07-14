"""
Panchi Club Travel OS — Data Layer (Unit 2)

Five core models + ActivityLog for lead history tracking.
All tables use created_at + updated_at timestamps.
"""

import re
from datetime import datetime, date
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


class PaymentType(str, PyEnum):
    GUEST = "guest_payment"
    SUPPLIER = "supplier_payment"
    REFUND = "refund"
    DEPOSIT = "deposit"


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
    # Person compatibility (Phase 1)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)
    person = db.relationship("Person", backref="leads", lazy="select")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = db.relationship("Payment", backref="lead", lazy="dynamic", cascade="all,delete-orphan")
    invoices = db.relationship("Invoice", backref="lead", lazy="dynamic", cascade="all,delete-orphan")
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

    @property
    def total_supplier_payout(self) -> float:
        return float(
            db.session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.lead_id == self.id, Payment.type == PaymentType.SUPPLIER.value)
            .scalar()
            or 0
        )

    @property
    def profit_margin(self) -> float:
        return self.total_revenue - self.total_supplier_payout

    def log_activity(self, action: str, detail: str = "", user: str = ""):
        """Helper: log an activity entry against this lead."""
        log = ActivityLog(lead_id=self.id, action=action, detail=detail, user=user)
        db.session.add(log)
        db.session.commit()


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class Payment(db.Model):
    """Dual-ledger payment: guest revenue vs supplier expense."""

    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_lead_type", "lead_id", "type"),
        Index("ix_payments_paid_at", "paid_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True)
    type = db.Column(db.String(30), default=PaymentType.GUEST.value, nullable=False)
    amount = db.Column(Numeric(12, 2), default=0, nullable=False)
    method = db.Column(db.String(80))
    ref_number = db.Column(db.String(120), index=True)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment #{self.id} {self.type} ₹{self.amount:.0f}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "type": self.type,
            "amount": float(self.amount or 0),
            "method": self.method,
            "ref_number": self.ref_number,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Supplier
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

class Invoice(db.Model):
    """Invoices with PDF generation. Lifecycle: draft → sent → paid / void."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_lead", "lead_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    total_amount = db.Column(Numeric(12, 2), default=0)
    tax = db.Column(Numeric(12, 2), default=0)
    tax_rate = db.Column(Numeric(5, 2), default=0)  # e.g. 18.00 for 18%
    discount = db.Column(Numeric(12, 2), default=0)
    grand_total = db.Column(Numeric(12, 2), default=0)
    currency = db.Column(db.String(10), default="INR")
    pdf_path = db.Column(db.String(500))
    status = db.Column(db.String(30), default=InvoiceStatus.DRAFT.value)
    due_date = db.Column(db.Date)
    raised_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<Invoice {self.invoice_number} [{self.status}] ₹{self.grand_total:.0f}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "invoice_number": self.invoice_number,
            "total_amount": float(self.total_amount or 0),
            "tax": float(self.tax or 0),
            "tax_rate": float(self.tax_rate or 0),
            "discount": float(self.discount or 0),
            "grand_total": float(self.grand_total or 0),
            "currency": self.currency,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "raised_at": self.raised_at.isoformat() if self.raised_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }


# ---------------------------------------------------------------------------
# ItineraryRef
# ---------------------------------------------------------------------------

class ItineraryRef(db.Model):
    """Reference archive: past executed trips for knowledge base."""

    __tablename__ = "itinerary_refs"

    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(255), index=True)
    destination = db.Column(db.String(255), index=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    pax = db.Column(db.String(100))
    highlights = db.Column(db.Text)
    day_count = db.Column(db.Integer, default=0)
    file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ItineraryRef {self.guest_name} → {self.destination} ({self.day_count}d)>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "guest_name": self.guest_name,
            "destination": self.destination,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "pax": self.pax,
            "day_count": self.day_count,
            "highlights": self.highlights,
            "file_path": self.file_path,
        }


# ---------------------------------------------------------------------------
# TaskList
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
# ClientUser — Client Portal Accounts
# ---------------------------------------------------------------------------

class ClientUser(db.Model):
    """Client portal user account. Created when a lead registers or is invited."""

    __tablename__ = "client_users"
    __table_args__ = (
        Index("ix_client_users_email", "email"),
        Index("ix_client_users_lead", "lead_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), default="")
    password_hash = db.Column(db.String(128), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    lead = db.relationship("Lead", backref="client_users", lazy="select")

    def set_password(self, password: str):
        import hashlib, secrets
        salt = secrets.token_hex(16)
        self.password_hash = f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"

    def check_password(self, password: str) -> bool:
        import hashlib
        if not self.password_hash or "$" not in self.password_hash:
            return False
        salt, hsh = self.password_hash.split("$", 1)
        return hsh == hashlib.sha256((salt + password).encode()).hexdigest()

    def __repr__(self):
        return f"<ClientUser #{self.id} {self.email}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "lead_id": self.lead_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


# ---------------------------------------------------------------------------
# ClientMessage — Client <-> Team Messaging
# ---------------------------------------------------------------------------

class ClientMessage(db.Model):
    """Messages between clients and the Panchi team."""

    __tablename__ = "client_messages"
    __table_args__ = (
        Index("ix_client_messages_lead", "lead_id"),
        Index("ix_client_messages_created", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=False)
    client_user_id = db.Column(db.Integer, db.ForeignKey("client_users.id"), nullable=True)
    sender = db.Column(db.String(20), nullable=False)  # 'client' or 'team'
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    lead = db.relationship("Lead", backref="client_messages", lazy="select")
    client_user = db.relationship("ClientUser", backref="messages", lazy="select")

    def __repr__(self):
        return f"<ClientMessage #{self.id} [{self.sender}] on lead #{self.lead_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "client_user_id": self.client_user_id,
            "sender": self.sender,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Document — AI Document Reading
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
    status = db.Column(db.String(30), default="active", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    identities = db.relationship("PersonIdentity", backref="person", lazy="select", cascade="all, delete-orphan")
    employee_profile = db.relationship("EmployeeProfile", uselist=False, backref="person", lazy="select")
    customer_profile = db.relationship("CustomerProfile", uselist=False, backref="person", lazy="select")
    supplier_contact_profile = db.relationship("SupplierContactProfile", uselist=False, backref="person", lazy="select")
    client_user_profile = db.relationship("ClientUserProfile", uselist=False, backref="person", lazy="select")

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


class PersonIdentity(db.Model):
    """Normalized identity values for a Person (email, phone, channel IDs)."""
    __tablename__ = "person_identities"
    __table_args__ = (
        Index("ix_pi_type_value", "identity_type", "normalized_value"),
        Index("ix_pi_person", "person_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    identity_type = db.Column(db.String(60), nullable=False, index=True)
    identity_value = db.Column(db.String(255), nullable=False)
    normalized_value = db.Column(db.String(255), nullable=False, index=True)
    verification_state = db.Column(db.String(30), default="unverified")

    def __repr__(self):
        return f"<PersonIdentity #{self.id} {self.identity_type}:{self.normalized_value}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "person_id": self.person_id,
            "identity_type": self.identity_type,
            "identity_value": self.identity_value,
            "normalized_value": self.normalized_value,
            "verification_state": self.verification_state,
        }


# ---------------------------------------------------------------------------
# Role / Business Projections (Phase 1)
# ---------------------------------------------------------------------------


class EmployeeProfile(db.Model):
    """Employee role projection over Person."""
    __tablename__ = "employee_profiles"
    __table_args__ = (
        Index("ix_emp_profile_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False, unique=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    employee_code = db.Column(db.String(60), unique=True, nullable=True)
    department = db.Column(db.String(120), default="")
    manager_person_id = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(60), default="")
    status = db.Column(db.String(30), default="active")
    joined_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EmployeeProfile #{self.id} person={self.person_id}>"


class CustomerProfile(db.Model):
    """Customer role projection over Person."""
    __tablename__ = "customer_profiles"
    __table_args__ = (
        Index("ix_cust_profile_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False, unique=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    lifetime_value = db.Column(db.Numeric(14, 2), default=0)
    segment = db.Column(db.String(60), default="")
    preferred_channel = db.Column(db.String(30), default="")
    preferred_channel_provenance = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CustomerProfile #{self.id} person={self.person_id}>"


class SupplierContactProfile(db.Model):
    """Supplier contact role projection over Person."""
    __tablename__ = "supplier_contact_profiles"
    __table_args__ = (
        Index("ix_sc_profile_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False, unique=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    supplier_id = db.Column(db.Integer, nullable=True)
    role_in_organization = db.Column(db.String(120), default="")
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SupplierContactProfile #{self.id} person={self.person_id}>"


class ClientUserProfile(db.Model):
    """Client portal user role projection over Person."""
    __tablename__ = "client_user_profiles"
    __table_args__ = (
        Index("ix_cu_profile_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False, unique=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    portal_access_granted = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ClientUserProfile #{self.id} person={self.person_id}>"


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
            Lead.created_at < datetime(today.year, today.month, today.day + 1),
        )
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:02d}"