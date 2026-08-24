"""FOR-2D.1: Financial Governance — State Machines, Permissions, and Correction Engine.

Constitutional principle: Financial truth is immutable. Corrections create new events.
"""

from datetime import datetime, date, timezone
from decimal import Decimal
import json
from app import db
from app.finance.models import FinInvoice as Invoice, InvoiceItem, FinancePayment as Payment
from app.finance.models import JournalEntry, LedgerEntry, Account
from app.finance.accounting import create_journal_entry
from app.relationship.integration import record_event, update_ai_memory_from_event


# ── State Machine Definitions ──────────────────────────────────────────

INVOICE_STATES = {
    "draft":      {"next": ["under_review", "cancelled"],                      "label": "Draft"},
    "under_review": {"next": ["approved", "draft", "cancelled"],               "label": "Under Review"},
    "approved":   {"next": ["posted", "draft", "cancelled"],                   "label": "Approved"},
    "posted":     {"next": ["partially_paid", "paid", "cancelled", "void"],    "label": "Posted"},
    "partially_paid": {"next": ["paid", "cancelled", "void"],                  "label": "Partially Paid"},
    "paid":       {"next": ["void"],                                           "label": "Paid"},
    "cancelled":  {"next": ["draft"],                                         "label": "Cancelled"},
    "void":       {"next": [],                                                 "label": "Void"},
}

JOURNAL_STATES = {
    "draft":   {"next": ["posted", "cancelled"],                               "label": "Draft"},
    "posted":  {"next": ["reversed"],                                          "label": "Posted"},
    "reversed":{"next": [],                                                    "label": "Reversed"},
    "cancelled":{"next": [],                                                   "label": "Cancelled"},
}

PAYMENT_STATES = {
    "pending":     {"next": ["confirmed", "cancelled"],                        "label": "Pending"},
    "confirmed":   {"next": ["allocated", "reversed"],                         "label": "Confirmed"},
    "allocated":   {"next": ["reconciled", "reversed"],                        "label": "Allocated"},
    "reconciled":  {"next": ["reversed"],                                      "label": "Reconciled"},
    "reversed":    {"next": [],                                                "label": "Reversed"},
    "cancelled":   {"next": [],                                                "label": "Cancelled"},
}


def validate_transition(obj_type, current_state, target_state):
    """Validate a state machine transition. Returns (valid, error_msg)."""
    machine = {"invoice": INVOICE_STATES, "journal": JOURNAL_STATES, "payment": PAYMENT_STATES}.get(obj_type)
    if not machine:
        return False, f"Unknown object type: {obj_type}"
    rules = machine.get(current_state)
    if not rules:
        return False, f"Unknown state: {current_state}"
    if target_state not in rules["next"]:
        return False, f"Cannot transition from {current_state} to {target_state}"
    return True, None


def transition_invoice(invoice_id, target_state, organization_id, identity_id, reason=""):
    """Transition an invoice to a new state with full governance."""
    inv = db.session.get(Invoice, invoice_id)
    if not inv or inv.organization_id != organization_id:
        return {"error": "Invoice not found"}
    valid, err = validate_transition("invoice", inv.status, target_state)
    if not valid:
        return {"error": err}

    old_status = inv.status
    inv.status = target_state

    # Post to ledger when approved → posted
    if target_state == "posted" and old_status == "approved":
        ar = Account.query.filter_by(organization_id=organization_id, code="1100").first()
        rev = Account.query.filter_by(organization_id=organization_id, code="4000").first()
        tax = Account.query.filter_by(organization_id=organization_id, code="2100").first()
        if ar and rev:
            lines = [{"account_code": "1100", "debit": inv.total_amount, "credit": 0},
                     {"account_code": "4000", "credit": inv.subtotal, "debit": 0}]
            if inv.tax_amount > 0 and tax:
                lines.append({"account_code": "2100", "credit": inv.tax_amount, "debit": 0})
            result = create_journal_entry(organization_id, inv.issue_date, lines,
                description=f"Post Invoice {inv.number}", type="sales",
                reference_type="invoice", reference_id=inv.id, created_by=identity_id)
            if "journal_entry" in result:
                inv.journal_entry_id = result["journal_entry"]["id"]

    # Cancelled invoice → reverse ledger
    if target_state == "cancelled" and inv.journal_entry_id:
        _reverse_journal(inv.journal_entry_id, organization_id, identity_id,
                         f"Cancel invoice {inv.number}: {reason[:200]}" if reason else f"Cancel invoice {inv.number}")

    # Record timeline event
    event_type = f"invoice.{target_state}"
    if inv.relationship_id:
        record_event(relationship_id=inv.relationship_id, organization_id=organization_id,
            event_type=event_type, title=f"Invoice {inv.number} {target_state}",
            description=f"Status: {old_status} → {target_state}{f'. Reason: {reason[:200]}' if reason else ''}",
            reference_type="invoice", reference_id=inv.id, created_by=identity_id)
        update_ai_memory_from_event(relationship_id=inv.relationship_id,
            organization_id=organization_id, event_type=event_type,
            summary_fragment=f"Invoice {inv.number} transitioned: {old_status} → {target_state}")

    db.session.commit()
    return {"invoice": inv.to_dict(), "transition": {"from": old_status, "to": target_state}}


def create_credit_note(organization_id, original_invoice_id, reason, items=None, created_by=""):
    """Create a credit note against a posted invoice. Reverses the original journal."""
    inv = db.session.get(Invoice, original_invoice_id)
    if not inv or inv.organization_id != organization_id:
        return {"error": "Invoice not found"}
    if inv.status not in ("posted", "partially_paid", "paid"):
        return {"error": "Can only credit-note posted invoices"}

    # Reverse original journal
    reversal_result = None
    if inv.journal_entry_id:
        reversal_result = _reverse_journal(inv.journal_entry_id, organization_id, created_by,
                                           f"Credit note for invoice {inv.number}: {reason[:200]}")
        if "error" in reversal_result:
            return reversal_result

    # Create credit note invoice
    inv_count = Invoice.query.filter_by(organization_id=organization_id).count() + 1
    cn_number = f"CN-{date.today().strftime('%Y%m')}-{inv_count:04d}"
    cn = Invoice(organization_id=organization_id, relationship_id=inv.relationship_id,
        proposal_id=inv.proposal_id, number=cn_number, type="credit_note", status="posted",
        issue_date=date.today(), due_date=None, currency=inv.currency,
        subtotal=inv.subtotal, tax_amount=inv.tax_amount, total_amount=inv.total_amount,
        notes=f"Credit note for {inv.number}: {reason[:300]}", created_by=created_by)
    db.session.add(cn)
    db.session.flush()

    # Create credit note items (negative amounts)
    if not items:
        items_data = InvoiceItem.query.filter_by(invoice_id=original_invoice_id).all()
        for item in items_data:
            db.session.add(InvoiceItem(invoice_id=cn.id,
                description=f"Credit: {item.description}", quantity=-1 * item.quantity,
                unit_price=item.unit_price, total_amount=-1 * item.total_amount,
                tax_rate=item.tax_rate, tax_amount=-1 * item.tax_amount))

    # Reversal journal for credit entry
    ar = Account.query.filter_by(organization_id=organization_id, code="1100").first()
    rev = Account.query.filter_by(organization_id=organization_id, code="4000").first()
    tax = Account.query.filter_by(organization_id=organization_id, code="2100").first()
    if ar and rev:
        lines = [{"account_code": "1100", "credit": inv.total_amount, "debit": 0},
                 {"account_code": "4000", "debit": inv.subtotal, "credit": 0}]
        if inv.tax_amount > 0 and tax:
            lines.append({"account_code": "2100", "debit": inv.tax_amount, "credit": 0})
        result = create_journal_entry(organization_id, date.today(), lines,
            description=f"Credit note {cn_number} for {inv.number}",
            type="adjustment", reference_type="credit_note", reference_id=cn.id, created_by=created_by)
        if "journal_entry" in result:
            cn.journal_entry_id = result["journal_entry"]["id"]

    # Timeline
    if cn.relationship_id:
        record_event(relationship_id=cn.relationship_id, organization_id=organization_id,
            event_type="correction.credit_note", title=f"Credit note {cn_number} issued",
            description=reason, reference_type="credit_note", reference_id=cn.id, created_by=created_by)
        update_ai_memory_from_event(relationship_id=cn.relationship_id, organization_id=organization_id,
            event_type="correction.credit_note",
            summary_fragment=f"Credit note {cn_number} issued for invoice {inv.number}: {reason[:100]}")

    db.session.commit()
    return {"credit_note": cn.to_dict(), "reversal": reversal_result}


def _reverse_journal(journal_entry_id, organization_id, created_by, reason=""):
    """Reverse a posted journal entry. Creates a reversing entry."""
    original = db.session.get(JournalEntry, journal_entry_id)
    if not original or original.organization_id != organization_id:
        return {"error": "Journal not found"}
    if original.status != "posted":
        return {"error": "Can only reverse posted journals"}

    # Get original ledger lines
    lines = LedgerEntry.query.filter_by(journal_entry_id=journal_entry_id).all()
    reversal_lines = []
    for le in lines:
        reversal_lines.append({
            "account_code": Account.query.get(le.account_id).code,
            "debit": le.credit,
            "credit": le.debit,
        })

    if not reversal_lines:
        return {"error": "No ledger entries to reverse"}

    result = create_journal_entry(organization_id, date.today(), reversal_lines,
        description=f"Reversal: {reason[:400] if reason else original.description[:200]}",
        type="adjustment", reference_type="reversal", reference_id=original.id, created_by=created_by)
    if "error" in result:
        return result

    original.status = "reversed"
    original.reversed_at = datetime.now(timezone.utc)
    original.reversed_by = created_by
    reversal_id = result["journal_entry"]["id"]
    original.reversal_of = reversal_id

    db.session.flush()
    return result