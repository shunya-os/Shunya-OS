"""FOR-2D: Double-Entry Accounting Engine.

Validates that every journal entry balances (total debits = total credits).
Once posted, entries are immutable. Adjustments via reversing entries.
"""

from datetime import datetime, date
from decimal import Decimal
from app import db
from app.finance.models import Account, LedgerEntry, JournalEntry


DEFAULT_ACCOUNTS = {
    "1000": {"name": "Cash", "type": "asset"},
    "1100": {"name": "Accounts Receivable", "type": "asset"},
    "1200": {"name": "Bank Account", "type": "asset"},
    "2000": {"name": "Accounts Payable", "type": "liability"},
    "2100": {"name": "Tax Payable", "type": "liability"},
    "3000": {"name": "Owner's Equity", "type": "equity"},
    "4000": {"name": "Revenue", "type": "revenue"},
    "5000": {"name": "Cost of Goods Sold", "type": "expense"},
    "6000": {"name": "Operating Expenses", "type": "expense"},
    "7000": {"name": "Tax Expense", "type": "expense"},
}


def seed_default_accounts(organization_id: int):
    """Seed the chart of accounts for a new organization."""
    if Account.query.filter_by(organization_id=organization_id).count() > 0:
        return
    for code, cfg in DEFAULT_ACCOUNTS.items():
        acct = Account(organization_id=organization_id, code=code,
                       name=cfg["name"], type=cfg["type"], is_control=True)
        db.session.add(acct)
    db.session.commit()


def create_journal_entry(organization_id: int, entry_date: date, lines: list,
                          description: str = "", type: str = "general",
                          reference_type: str = "", reference_id: int = None,
                          created_by: str = "") -> dict:
    """Create and post a journal entry with double-entry validation.

    Args:
        lines: list of {"account_code": str, "debit": Decimal, "credit": Decimal}
    
    Returns:
        dict with "journal_entry" and "ledger_entries" on success,
        or {"error": message} on validation failure.
    
    Raises: ValueError if entries don't balance.
    """
    # Validate accounts exist
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    resolved_lines = []

    for line in lines:
        code = line.get("account_code", "")
        acct = Account.query.filter_by(organization_id=organization_id, code=code).first()
        if not acct:
            return {"error": f"Account code '{code}' not found"}
        debit = Decimal(str(line.get("debit", 0)))
        credit = Decimal(str(line.get("credit", 0)))
        if debit < 0 or credit < 0:
            return {"error": "Negative amounts not allowed"}
        if debit > 0 and credit > 0:
            return {"error": "Line cannot have both debit and credit"}
        if debit == 0 and credit == 0:
            return {"error": "Line must have debit or credit"}
        total_debit += debit
        total_credit += credit
        resolved_lines.append({"account": acct, "debit": debit, "credit": credit})

    if total_debit != total_credit:
        return {"error": f"Journal entry does not balance: debits={total_debit} credits={total_credit}"}

    # Create journal entry
    journal = JournalEntry(
        organization_id=organization_id,
        entry_date=entry_date,
        number=_next_journal_number(organization_id, entry_date),
        type=type,
        status="posted",
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
        posted_at=datetime.utcnow(),
    )
    db.session.add(journal)
    db.session.flush()

    # Create ledger entries
    ledger_entries = []
    for rl in resolved_lines:
        le = LedgerEntry(
            organization_id=organization_id,
            account_id=rl["account"].id,
            journal_entry_id=journal.id,
            entry_date=entry_date,
            debit=rl["debit"],
            credit=rl["credit"],
            reference_type=reference_type,
            reference_id=reference_id,
            description=description[:500],
            created_by=created_by,
        )
        db.session.add(le)
        ledger_entries.append(le)

    db.session.commit()
    return {
        "journal_entry": journal.to_dict(),
        "ledger_entries": [le.to_dict() for le in ledger_entries],
    }


def get_account_balance(organization_id: int, account_code: str, as_of: date = None) -> Decimal:
    """Get the balance of a specific account.

    For asset/expense accounts: balance = total debits - total credits
    For liability/equity/revenue accounts: balance = total credits - total debits
    """
    acct = Account.query.filter_by(organization_id=organization_id, code=account_code).first()
    if not acct:
        return Decimal("0.00")

    q = LedgerEntry.query.filter_by(organization_id=organization_id, account_id=acct.id)
    if as_of:
        q = q.filter(LedgerEntry.entry_date <= as_of)

    total_debit = db.session.query(db.func.coalesce(db.func.sum(LedgerEntry.debit), 0)).filter(
        LedgerEntry.id.in_([e.id for e in q.all()]) if q.count() > 0 else [0]
    ).scalar() or Decimal("0.00")
    total_credit = db.session.query(db.func.coalesce(db.func.sum(LedgerEntry.credit), 0)).filter(
        LedgerEntry.id.in_([e.id for e in q.all()]) if q.count() > 0 else [0]
    ).scalar() or Decimal("0.00")

    if acct.type in ("asset", "expense"):
        return total_debit - total_credit
    else:
        return total_credit - total_debit


def get_trial_balance(organization_id: int, as_of: date = None) -> list:
    """Get trial balance: all accounts with their debit/credit balances."""
    accounts = Account.query.filter_by(organization_id=organization_id, is_active=True).order_by(Account.code).all()
    result = []
    for acct in accounts:
        q = LedgerEntry.query.filter_by(organization_id=organization_id, account_id=acct.id)
        if as_of:
            q = q.filter(LedgerEntry.entry_date <= as_of)
        total_debit = db.session.query(db.func.coalesce(db.func.sum(LedgerEntry.debit), 0)).filter(
            LedgerEntry.account_id == acct.id
        ).scalar() or Decimal("0.00")
        total_credit = db.session.query(db.func.coalesce(db.func.sum(LedgerEntry.credit), 0)).filter(
            LedgerEntry.account_id == acct.id
        ).scalar() or Decimal("0.00")

        result.append({
            "code": acct.code,
            "account": acct.name,
            "type": acct.type,
            "debit": float(total_debit),
            "credit": float(total_credit),
            "balance": float(total_debit - total_credit) if acct.type in ("asset", "expense") else float(total_credit - total_debit),
        })
    return result


def _next_journal_number(organization_id: int, entry_date: date) -> str:
    """Generate the next journal number for a date."""
    prefix = f"JE-{entry_date.strftime('%Y%m%d')}-"
    last = JournalEntry.query.filter(
        JournalEntry.organization_id == organization_id,
        JournalEntry.number.like(f"{prefix}%"),
    ).order_by(JournalEntry.id.desc()).first()
    if last and last.number:
        try:
            seq = int(last.number.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"