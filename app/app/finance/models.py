"""FOR-2D: Finance Intelligence — Domain Models.

Every financial entity belongs to exactly one Organization.
Every entity supports Timeline, Authorization, AI Memory, and Business Execution.
No industry-specific assumptions. No travel-specific code.
"""

from datetime import datetime, date
from decimal import Decimal
from app import db
from sqlalchemy import Index, Numeric


class Account(db.Model):
    __tablename__ = "fin_accounts"
    __table_args__ = (Index("ix_fin_acct_org", "organization_id"),
        Index("ix_fin_acct_code", "organization_id", "code", unique=True))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    code = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    subtype = db.Column(db.String(60), default="")
    is_active = db.Column(db.Boolean, default=True)
    is_control = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("fin_accounts.id"), nullable=True)
    currency = db.Column(db.String(10), default="INR")
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "organization_id": self.organization_id, "code": self.code,
            "name": self.name, "type": self.type, "subtype": self.subtype,
            "is_active": self.is_active, "is_control": self.is_control,
            "parent_id": self.parent_id, "currency": self.currency}


class JournalEntry(db.Model):
    __tablename__ = "fin_journal_entries"
    __table_args__ = (Index("ix_fin_journal_org", "organization_id"),
        Index("ix_fin_journal_date", "entry_date"))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    number = db.Column(db.String(60), default="")
    type = db.Column(db.String(30), default="general")
    status = db.Column(db.String(30), default="draft")
    description = db.Column(db.Text, default="")
    reference_type = db.Column(db.String(60), default="")
    reference_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.String(64), default="")
    posted_at = db.Column(db.DateTime, nullable=True)
    reversed_by = db.Column(db.String(64), default="")
    reversed_at = db.Column(db.DateTime, nullable=True)
    reversal_of = db.Column(db.Integer, db.ForeignKey("fin_journal_entries.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "organization_id": self.organization_id,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "number": self.number, "type": self.type, "status": self.status,
            "description": (self.description or "")[:200],
            "reference_type": self.reference_type, "reference_id": self.reference_id,
            "created_by": self.created_by, "posted_at": self.posted_at.isoformat() if self.posted_at else None}


class LedgerEntry(db.Model):
    __tablename__ = "fin_ledger"
    __table_args__ = (Index("ix_fin_ledger_org", "organization_id"),
        Index("ix_fin_ledger_account", "account_id"),
        Index("ix_fin_ledger_date", "entry_date"),
        Index("ix_fin_ledger_journal", "journal_entry_id"))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("fin_accounts.id"), nullable=False)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey("fin_journal_entries.id"), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    debit = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    credit = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    reference_type = db.Column(db.String(60), default="")
    reference_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, default="")
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "organization_id": self.organization_id,
            "account_id": self.account_id, "journal_entry_id": self.journal_entry_id,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "debit": float(self.debit or 0), "credit": float(self.credit or 0),
            "reference_type": self.reference_type, "reference_id": self.reference_id,
            "created_by": self.created_by}


class FinInvoice(db.Model):
    __tablename__ = "fin_invoices"
    __table_args__ = (Index("ix_fin_inv_org", "organization_id"),
        Index("ix_fin_inv_rel", "relationship_id"),
        Index("ix_fin_inv_number", "organization_id", "number", unique=True),
        Index("ix_fin_inv_status", "status"))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposals.id"), nullable=True)
    number = db.Column(db.String(60), nullable=False)
    type = db.Column(db.String(30), default="sales")
    status = db.Column(db.String(30), default="draft")
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    currency = db.Column(db.String(10), default="INR")
    subtotal = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    discount_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    paid_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    notes = db.Column(db.Text, default="")
    terms = db.Column(db.Text, default="")
    journal_entry_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.String(64), default="")
    sent_at = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "organization_id": self.organization_id,
            "relationship_id": self.relationship_id, "proposal_id": self.proposal_id,
            "number": self.number, "type": self.type, "status": self.status,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "currency": self.currency,
            "subtotal": float(self.subtotal or 0), "tax_amount": float(self.tax_amount or 0),
            "total_amount": float(self.total_amount or 0),
            "paid_amount": float(self.paid_amount or 0),
            "balance_due": float((self.total_amount or 0) - (self.paid_amount or 0)),
            "created_by": self.created_by}


class InvoiceItem(db.Model):
    __tablename__ = "fin_invoice_items"
    __table_args__ = (Index("ix_fin_invitem_inv", "invoice_id"),)
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("fin_invoices.id"), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(Numeric(12, 2), default=Decimal("1.00"))
    unit_price = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    tax_rate = db.Column(Numeric(5, 2), default=Decimal("0.00"))
    tax_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    discount_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    account_id = db.Column(db.Integer, nullable=True)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {"id": self.id, "invoice_id": self.invoice_id, "description": self.description,
            "quantity": float(self.quantity or 0), "unit_price": float(self.unit_price or 0),
            "tax_rate": float(self.tax_rate or 0), "tax_amount": float(self.tax_amount or 0),
            "discount_amount": float(self.discount_amount or 0),
            "total_amount": float(self.total_amount or 0)}


class FinancePayment(db.Model):
    __tablename__ = "fin_payments"
    __table_args__ = (Index("ix_fin_pay_org", "organization_id"),
        Index("ix_fin_pay_inv", "invoice_id"),
        Index("ix_fin_pay_rel", "relationship_id"))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey("fin_invoices.id"), nullable=True)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)
    type = db.Column(db.String(30), default="receipt")
    amount = db.Column(Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(10), default="INR")
    payment_date = db.Column(db.Date, nullable=False)
    method = db.Column(db.String(60), default="")
    reference_number = db.Column(db.String(255), default="")
    notes = db.Column(db.Text, default="")
    journal_entry_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "organization_id": self.organization_id,
            "invoice_id": self.invoice_id, "relationship_id": self.relationship_id,
            "type": self.type, "amount": float(self.amount or 0), "currency": self.currency,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "method": self.method, "reference_number": self.reference_number,
            "created_by": self.created_by}


class TaxProfile(db.Model):
    __tablename__ = "fin_tax_profiles"
    __table_args__ = (Index("ix_fin_tax_org", "organization_id"),)
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    rate = db.Column(Numeric(5, 2), nullable=False)
    type = db.Column(db.String(30), default="sales")
    is_active = db.Column(db.Boolean, default=True)
    account_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "organization_id": self.organization_id,
            "name": self.name, "rate": float(self.rate or 0),
            "type": self.type, "is_active": self.is_active}


class PurchaseOrder(db.Model):
    __tablename__ = "fin_purchase_orders"
    __table_args__ = (Index("ix_fin_po_org", "organization_id"),
        Index("ix_fin_po_rel", "relationship_id"))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)
    number = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(30), default="draft")
    order_date = db.Column(db.Date, nullable=False)
    expected_date = db.Column(db.Date, nullable=True)
    currency = db.Column(db.String(10), default="INR")
    total_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    notes = db.Column(db.Text, default="")
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Budget(db.Model):
    __tablename__ = "fin_budgets"
    __table_args__ = (Index("ix_fin_budget_org", "organization_id"),)
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    fiscal_year = db.Column(db.Integer, nullable=False)
    period = db.Column(db.String(30), default="yearly")
    amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    spent_amount = db.Column(Numeric(15, 2), default=Decimal("0.00"))
    account_id = db.Column(db.Integer, nullable=True)
    department_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)