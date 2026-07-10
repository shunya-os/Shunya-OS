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