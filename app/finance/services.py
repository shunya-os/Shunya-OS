"""FOR-2D: Finance Intelligence — Services."""
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
from app import db
from app.finance.models import FinInvoice as Invoice, InvoiceItem
from app.finance.models import FinancePayment as Payment, TaxProfile, Account, Budget
from app.finance.accounting import create_journal_entry, get_trial_balance
from app.models import Proposal
from app.relationship.integration import record_event, update_ai_memory_from_event


def create_invoice_from_proposal(organization_id, proposal_id, issue_date=None, due_date=None, created_by=""):
    """Create an invoice from a proposal."""
    proposal = db.session.get(Proposal, proposal_id)
    if not proposal or proposal.organization_id != organization_id:
        return {"error": "Proposal not found"}

    if not issue_date:
        issue_date = date.today()
    if not due_date:
        due_date = date.today() + timedelta(days=30)

    pricing = json.loads(proposal.pricing_json or "{}")
    subtotal = Decimal(str(pricing.get("total", pricing.get("grand_total", 0))))
    tax_amount = Decimal(str(pricing.get("tax", 0)))
    total = subtotal + tax_amount

    inv_count = Invoice.query.filter_by(organization_id=organization_id).count() + 1
    inv_number = f"INV-{issue_date.strftime('%Y%m')}-{inv_count:04d}"

    inv = Invoice(organization_id=organization_id, relationship_id=proposal.relationship_id,
        proposal_id=proposal_id, number=inv_number, type="sales", status="draft",
        issue_date=issue_date, due_date=due_date, currency=proposal.currency or "INR",
        subtotal=subtotal, tax_amount=tax_amount, total_amount=total, created_by=created_by)
    db.session.add(inv)
    db.session.flush()

    breakdown = pricing.get("breakdown", [])
    if breakdown:
        for item in breakdown:
            db.session.add(InvoiceItem(invoice_id=inv.id,
                description=item.get("item", ""), quantity=1,
                unit_price=Decimal(str(item.get("amount", 0))),
                total_amount=Decimal(str(item.get("amount", 0)))))

    ar = Account.query.filter_by(organization_id=organization_id, code="1100").first()
    rev = Account.query.filter_by(organization_id=organization_id, code="4000").first()
    tax = Account.query.filter_by(organization_id=organization_id, code="2100").first()

    if ar and rev:
        lines = [{"account_code": "1100", "debit": total, "credit": 0},
                 {"account_code": "4000", "credit": subtotal, "debit": 0}]
        if tax_amount > 0 and tax:
            lines.append({"account_code": "2100", "credit": tax_amount, "debit": 0})
        result = create_journal_entry(organization_id, issue_date, lines,
            description=f"Invoice {inv_number}", type="sales",
            reference_type="invoice", reference_id=inv.id, created_by=created_by)
        if "journal_entry" in result:
            inv.journal_entry_id = result["journal_entry"]["id"]

    if inv.relationship_id:
        record_event(relationship_id=inv.relationship_id, organization_id=organization_id,
            event_type="invoice.created", title=f"Invoice {inv_number} created",
            description=f"Amount: {float(total)}", reference_type="invoice", reference_id=inv.id,
            created_by=created_by)
        update_ai_memory_from_event(relationship_id=inv.relationship_id,
            organization_id=organization_id, event_type="invoice.created",
            summary_fragment=f"Invoice {inv_number} for {float(total)}")

    db.session.commit()
    return {"invoice": inv.to_dict()}


def record_payment(organization_id, invoice_id, amount, payment_date, method="", reference="", created_by=""):
    """Record a payment against an invoice."""
    inv = db.session.get(Invoice, invoice_id)
    if not inv or inv.organization_id != organization_id:
        return {"error": "Invoice not found"}
    amount = Decimal(str(amount))
    if amount <= 0:
        return {"error": "Amount must be positive"}
    new_paid = Decimal(str(inv.paid_amount or 0)) + amount
    if new_paid > inv.total_amount:
        return {"error": "Payment exceeds total"}

    pay = Payment(organization_id=organization_id, invoice_id=invoice_id,
        relationship_id=inv.relationship_id, type="receipt", amount=amount,
        currency=inv.currency, payment_date=payment_date, method=method,
        reference_number=reference, created_by=created_by)
    db.session.add(pay)
    db.session.flush()

    inv.paid_amount = new_paid
    if new_paid >= inv.total_amount:
        inv.status = "paid"
        inv.paid_at = datetime.utcnow()

    cash = Account.query.filter_by(organization_id=organization_id, code="1000").first()
    ar = Account.query.filter_by(organization_id=organization_id, code="1100").first()
    if cash and ar:
        result = create_journal_entry(organization_id, payment_date,
            [{"account_code": "1000", "debit": amount, "credit": 0},
             {"account_code": "1100", "credit": amount, "debit": 0}],
            description=f"Payment for {inv.number}", type="receipt",
            reference_type="payment", reference_id=pay.id, created_by=created_by)
        if "journal_entry" in result:
            pay.journal_entry_id = result["journal_entry"]["id"]

    if inv.relationship_id:
        record_event(relationship_id=inv.relationship_id, organization_id=organization_id,
            event_type="payment.received", title=f"Payment received: {float(amount)}",
            description=f"Invoice {inv.number}", reference_type="payment", reference_id=pay.id,
            created_by=created_by)
        update_ai_memory_from_event(relationship_id=inv.relationship_id,
            organization_id=organization_id, event_type="payment.received",
            summary_fragment=f"Payment of {float(amount)} for invoice {inv.number}")

    db.session.commit()
    return {"payment": pay.to_dict(), "invoice": inv.to_dict()}


def get_receivables_aging(organization_id):
    """Get accounts receivable aging."""
    today = date.today()
    aging = {"current": 0, "1-30": 0, "31-60": 0, "61-90": 0, "90+": 0, "total": 0}
    for inv in Invoice.query.filter_by(organization_id=organization_id):
        bal = float((inv.total_amount or 0) - (inv.paid_amount or 0))
        if bal > 0 and inv.status not in ("paid", "void", "cancelled"):
            days = (today - inv.due_date).days if inv.due_date and inv.due_date < today else 0
            if days <= 0: aging["current"] += bal
            elif days <= 30: aging["1-30"] += bal
            elif days <= 60: aging["31-60"] += bal
            elif days <= 90: aging["61-90"] += bal
            else: aging["90+"] += bal
            aging["total"] += bal
    return aging


def get_financial_summary(organization_id):
    """Get financial health summary."""
    today = date.today()
    total_rev = db.session.query(db.func.coalesce(db.func.sum(Invoice.total_amount), 0)).filter(
        Invoice.organization_id == organization_id).scalar() or 0
    total_paid = db.session.query(db.func.coalesce(db.func.sum(Invoice.paid_amount), 0)).filter(
        Invoice.organization_id == organization_id).scalar() or 0
    overdue = db.session.query(db.func.coalesce(db.func.sum(Invoice.total_amount - Invoice.paid_amount), 0)).filter(
        Invoice.organization_id == organization_id,
        Invoice.due_date < today, Invoice.status.in_(["sent", "overdue"])).scalar() or 0
    inv_count = Invoice.query.filter_by(organization_id=organization_id).count()
    paid_count = Invoice.query.filter_by(organization_id=organization_id, status="paid").count()

    return {"total_revenue": float(total_rev), "total_paid": float(total_paid),
        "outstanding": float(total_rev - total_paid),
        "overdue": float(overdue), "invoice_count": inv_count, "paid_count": paid_count}