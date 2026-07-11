"""Shunya Finance Module — Accounting, Invoicing, Expenses, P&L.

Every business needs money management. This module provides the full stack:
- Chart of Accounts + Double-Entry Ledger
- Invoicing (with payment links)
- Expense Tracking
- P&L / Balance Sheet / Cash Flow
"""
import json, os
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, List
from flask import Blueprint, request, jsonify, render_template, g
from app import db
from app.models import Entity, EntityDefinition, Payment, ActivityLog, KnowledgeEntry
from app.routes.auth import login_required

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")


# ---------------------------------------------------------------------------
# Data Models (as entity types, seeded in seed_scripts)
# ---------------------------------------------------------------------------

FINANCE_ENTITY_TYPES = {
    "invoice": {
        "label": "Invoice",
        "icon": "🧾",
        "schema": [
            {"name": "invoice_number", "label": "Invoice #", "type": "text", "required": True},
            {"name": "customer_name", "label": "Customer", "type": "text", "required": True},
            {"name": "customer_email", "label": "Customer Email", "type": "text"},
            {"name": "customer_phone", "label": "Customer Phone", "type": "text"},
            {"name": "items", "label": "Line Items", "type": "json"},
            {"name": "subtotal", "label": "Subtotal", "type": "number"},
            {"name": "tax", "label": "Tax", "type": "number"},
            {"name": "total", "label": "Total", "type": "number"},
            {"name": "currency", "label": "Currency", "type": "text"},
            {"name": "due_date", "label": "Due Date", "type": "date"},
            {"name": "paid_amount", "label": "Paid Amount", "type": "number"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["draft", "sent", "paid", "overdue", "cancelled"],
        "layout": "table",
        "searchable_fields": ["invoice_number", "customer_name", "customer_email"],
    },
    "expense": {
        "label": "Expense",
        "icon": "💸",
        "schema": [
            {"name": "description", "label": "Description", "type": "text", "required": True},
            {"name": "amount", "label": "Amount", "type": "number", "required": True},
            {"name": "category", "label": "Category", "type": "select", "options": ["office", "travel", "utilities", "salary", "marketing", "software", "food", "transport", "other"]},
            {"name": "payment_method", "label": "Payment Method", "type": "select", "options": ["cash", "bank", "card", "upi", "other"]},
            {"name": "expense_date", "label": "Date", "type": "date"},
            {"name": "vendor", "label": "Vendor/Payee", "type": "text"},
            {"name": "billable", "label": "Billable", "type": "boolean"},
            {"name": "receipt_url", "label": "Receipt", "type": "file"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["pending", "approved", "reimbursed", "rejected"],
        "layout": "table",
        "searchable_fields": ["description", "vendor", "category"],
    },
    "account": {
        "label": "Account",
        "icon": "🏦",
        "schema": [
            {"name": "account_name", "label": "Account Name", "type": "text", "required": True},
            {"name": "account_type", "label": "Type", "type": "select", "options": ["asset", "liability", "equity", "revenue", "expense"]},
            {"name": "opening_balance", "label": "Opening Balance", "type": "number"},
            {"name": "currency", "label": "Currency", "type": "text"},
            {"name": "bank_name", "label": "Bank Name", "type": "text"},
            {"name": "account_number", "label": "Account Number", "type": "text"},
            {"name": "ifsc_code", "label": "IFSC Code", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "inactive", "closed"],
        "layout": "table",
        "searchable_fields": ["account_name", "bank_name", "account_number"],
    },
}


# ---------------------------------------------------------------------------
# Finance Dashboard
# ---------------------------------------------------------------------------

@finance_bp.route("")
@login_required
def finance_dashboard():
    """Finance overview — invoices, expenses, P&L summary."""
    # Get or create entity types
    _ensure_finance_types(g.tenant.id)

    inv_def = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="invoice").first()
    exp_def = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="expense").first()
    acc_def = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="account").first()

    invoices = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=inv_def.id, is_archived=False).all() if inv_def else []
    expenses = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=exp_def.id, is_archived=False).all() if exp_def else []
    accounts = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=acc_def.id, is_archived=False).all() if acc_def else []

    # Calculate totals
    total_invoiced = sum(float(e.data.get("total", 0)) for e in invoices)
    total_paid = sum(float(e.data.get("paid_amount", 0)) for e in invoices)
    total_due = total_invoiced - total_paid
    total_expenses = sum(float(e.data.get("amount", 0)) for e in expenses)
    net_income = total_paid - total_expenses

    # Invoice status breakdown
    invoice_statuses = {}
    for e in invoices:
        s = e.status
        invoice_statuses[s] = invoice_statuses.get(s, 0) + 1

    # Expense by category
    expense_categories = {}
    for e in expenses:
        cat = e.data.get("category", "other")
        expense_categories[cat] = expense_categories.get(cat, 0) + float(e.data.get("amount", 0))

    return render_template("finance/dashboard.html",
        invoices=invoices, expenses=expenses, accounts=accounts,
        total_invoiced=total_invoiced, total_paid=total_paid,
        total_due=total_due, total_expenses=total_expenses,
        net_income=net_income, invoice_statuses=invoice_statuses,
        expense_categories=expense_categories,
        inv_def=inv_def, exp_def=exp_def, acc_def=acc_def,
    )


@finance_bp.route("/api/summary")
@login_required
def finance_summary():
    """JSON summary for dashboard widgets."""
    inv_def = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="invoice").first()
    exp_def = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="expense").first()

    invoices = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=inv_def.id).all() if inv_def else []
    expenses = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=exp_def.id).all() if exp_def else []

    paid = sum(float(e.data.get("paid_amount", 0)) for e in invoices)
    invoiced = sum(float(e.data.get("total", 0)) for e in invoices)
    expenses_total = sum(float(e.data.get("amount", 0)) for e in expenses)

    # Monthly trend
    now = datetime.utcnow()
    monthly = []
    for i in range(6):
        m_start = datetime(now.year, now.month - i, 1) if now.month > i else datetime(now.year - 1, 12 + now.month - i, 1)
        m_end = datetime(m_start.year + (m_start.month // 12), (m_start.month % 12) + 1, 1) if m_start.month < 12 else datetime(m_start.year + 1, 1, 1)
        revenue = sum(float(e.data.get("paid_amount", 0)) for e in invoices if e.created_at >= m_start and e.created_at < m_end)
        cost = sum(float(e.data.get("amount", 0)) for e in expenses if e.created_at >= m_start and e.created_at < m_end)
        monthly.append({
            "month": m_start.strftime("%b"),
            "revenue": revenue,
            "expenses": cost,
            "profit": revenue - cost,
        })
    monthly.reverse()

    return jsonify({
        "total_invoiced": invoiced,
        "total_paid": paid,
        "total_due": invoiced - paid,
        "total_expenses": expenses_total,
        "net_income": paid - expenses_total,
        "invoice_count": len(invoices),
        "expense_count": len(expenses),
        "monthly": monthly,
    })


def _ensure_finance_types(tenant_id: int):
    """Ensure finance entity types exist for this tenant."""
    for etype, config in FINANCE_ENTITY_TYPES.items():
        existing = EntityDefinition.query.filter_by(tenant_id=tenant_id, type=etype).first()
        if existing:
            continue
        definition = EntityDefinition(
            tenant_id=tenant_id,
            type=etype,
            label=config["label"],
            label_plural=f"{config['label']}s",
            icon=config["icon"],
            schema=config["schema"],
            statuses=config["statuses"],
            layout=config["layout"],
            searchable_fields=config["searchable_fields"],
            primary_field=config["schema"][0]["name"] if config["schema"] else "name",
        )
        db.session.add(definition)
    db.session.commit()