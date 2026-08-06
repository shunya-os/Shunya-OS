"""Universal Financial Intelligence — Data Models.

Living Object dataclasses for the universal financial capability.
Every model has to_dict() for serialization, designed for composition
by domain-specific modules (personal finance, corporate finance, etc.)

UCP-03 — Universal Financial Intelligence.
UCP-03A — Financial Intelligence (reasoning layer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ── Enums ─────────────────────────────────────────────────────────────────

class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    WALLET = "wallet"
    INVESTMENT = "investment"
    LOAN = "loan"
    MORTGAGE = "mortgage"
    RECEIVABLE = "receivable"
    PAYABLE = "payable"
    CASH = "cash"
    ESCROW = "escrow"
    TAX = "tax"
    BUDGET = "budget"
    REVENUE = "revenue"
    EXPENSE = "expense"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"
    INVESTMENT = "investment"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    FEE = "fee"
    INTEREST = "interest"
    TAX = "tax"
    ADJUSTMENT = "adjustment"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    CLEARED = "cleared"
    RECONCILED = "reconciled"
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BudgetPeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class FinancialGoalType(str, Enum):
    SAVINGS = "savings"
    DEBT_REPAYMENT = "debt_repayment"
    INVESTMENT = "investment"
    EMERGENCY_FUND = "emergency_fund"
    REVENUE_TARGET = "revenue_target"
    PROFIT_TARGET = "profit_target"
    EXPENSE_REDUCTION = "expense_reduction"
    RETIREMENT = "retirement"
    EDUCATION = "education"
    PURCHASE = "purchase"
    CUSTOM = "custom"


class FinancialGoalStatus(str, Enum):
    ACTIVE = "active"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BEHIND = "behind"
    ACHIEVED = "achieved"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CashFlowDirection(str, Enum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class PricingModel(str, Enum):
    FIXED = "fixed"
    HOURLY = "hourly"
    SUBSCRIPTION = "subscription"
    TIERED = "tiered"
    USAGE_BASED = "usage_based"
    CONSULTATION = "consultation"
    PERFORMANCE_BASED = "performance_based"
    EQUITY = "equity"
    BARTER = "barter"


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class Money:
    amount: float = 0.0
    currency: str = "INR"

    def to_dict(self) -> dict[str, Any]:
        return {"amount": self.amount, "currency": self.currency}

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: float) -> Money:
        return Money(amount=self.amount * factor, currency=self.currency)

    def __truediv__(self, divisor: float) -> Money:
        return Money(amount=self.amount / divisor, currency=self.currency) if divisor else self

    @property
    def is_positive(self) -> bool:
        return self.amount > 0

    @property
    def is_negative(self) -> bool:
        return self.amount < 0

    @property
    def abs(self) -> Money:
        return Money(amount=abs(self.amount), currency=self.currency)


@dataclass
class Account:
    account_id: str = field(default_factory=_generate_id)
    name: str = ""
    account_type: str = AccountType.CHECKING.value
    balance: Money = field(default_factory=lambda: Money())
    currency: str = "INR"
    institution: str = ""
    owner_id: str = ""
    is_active: bool = True
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "name": self.name,
            "account_type": self.account_type,
            "balance": self.balance.to_dict(),
            "currency": self.currency,
            "institution": self.institution,
            "owner_id": self.owner_id,
            "is_active": self.is_active,
            "description": self.description,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Wallet:
    wallet_id: str = field(default_factory=_generate_id)
    name: str = ""
    owner_id: str = ""
    accounts: list[str] = field(default_factory=list)
    primary_currency: str = "INR"
    total_balance: Money = field(default_factory=lambda: Money())
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "accounts": list(self.accounts),
            "primary_currency": self.primary_currency,
            "total_balance": self.total_balance.to_dict(),
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Transaction:
    transaction_id: str = field(default_factory=_generate_id)
    transaction_type: str = TransactionType.EXPENSE.value
    amount: Money = field(default_factory=lambda: Money())
    from_account_id: str = ""
    to_account_id: str = ""
    description: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = TransactionStatus.CLEARED.value
    reference: str = ""
    counterparty: str = ""
    notes: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: str = field(default_factory=_now_iso)
    recorded_at: str = field(default_factory=_now_iso)

    @property
    def is_inflow(self) -> bool:
        return self.transaction_type in (
            TransactionType.INCOME.value, TransactionType.DEPOSIT.value,
            TransactionType.REFUND.value, TransactionType.INTEREST.value,
        )

    @property
    def is_outflow(self) -> bool:
        return self.transaction_type in (
            TransactionType.EXPENSE.value, TransactionType.WITHDRAWAL.value,
            TransactionType.FEE.value, TransactionType.TAX.value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount.to_dict(),
            "from_account_id": self.from_account_id,
            "to_account_id": self.to_account_id,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
            "status": self.status,
            "reference": self.reference,
            "counterparty": self.counterparty,
            "notes": self.notes,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "occurred_at": self.occurred_at,
            "recorded_at": self.recorded_at,
        }


@dataclass
class Budget:
    budget_id: str = field(default_factory=_generate_id)
    name: str = ""
    period: str = BudgetPeriod.MONTHLY.value
    total_planned: Money = field(default_factory=lambda: Money())
    total_spent: Money = field(default_factory=lambda: Money())
    total_remaining: Money = field(default_factory=lambda: Money())
    categories: dict[str, dict[str, float]] = field(default_factory=dict)
    owner_id: str = ""
    is_active: bool = True
    start_date: str = ""
    end_date: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def utilization_pct(self) -> float:
        if self.total_planned.amount == 0:
            return 0.0
        return (self.total_spent.amount / self.total_planned.amount) * 100.0

    @property
    def is_over_budget(self) -> bool:
        return self.total_spent.amount > self.total_planned.amount

    def to_dict(self) -> dict[str, Any]:
        return {
            "budget_id": self.budget_id,
            "name": self.name,
            "period": self.period,
            "total_planned": self.total_planned.to_dict(),
            "total_spent": self.total_spent.to_dict(),
            "total_remaining": self.total_remaining.to_dict(),
            "categories": dict(self.categories),
            "owner_id": self.owner_id,
            "is_active": self.is_active,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "utilization_pct": self.utilization_pct,
            "is_over_budget": self.is_over_budget,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Invoice:
    invoice_id: str = field(default_factory=_generate_id)
    invoice_number: str = ""
    status: str = InvoiceStatus.DRAFT.value
    issuer_id: str = ""
    recipient_id: str = ""
    line_items: list[dict[str, Any]] = field(default_factory=list)
    subtotal: Money = field(default_factory=lambda: Money())
    tax_amount: Money = field(default_factory=lambda: Money())
    discount_amount: Money = field(default_factory=lambda: Money())
    total_amount: Money = field(default_factory=lambda: Money())
    amount_paid: Money = field(default_factory=lambda: Money())
    amount_due: Money = field(default_factory=lambda: Money())
    currency: str = "INR"
    due_date: str = ""
    issued_date: str = ""
    paid_date: str | None = None
    notes: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_paid(self) -> bool:
        return self.status == InvoiceStatus.PAID.value

    @property
    def is_overdue(self) -> bool:
        return self.status == InvoiceStatus.OVERDUE.value

    @property
    def is_partially_paid(self) -> bool:
        return self.status == InvoiceStatus.PARTIALLY_PAID.value

    @property
    def payment_progress_pct(self) -> float:
        if self.total_amount.amount == 0:
            return 0.0
        return (self.amount_paid.amount / self.total_amount.amount) * 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "status": self.status,
            "issuer_id": self.issuer_id,
            "recipient_id": self.recipient_id,
            "line_items": list(self.line_items),
            "subtotal": self.subtotal.to_dict(),
            "tax_amount": self.tax_amount.to_dict(),
            "discount_amount": self.discount_amount.to_dict(),
            "total_amount": self.total_amount.to_dict(),
            "amount_paid": self.amount_paid.to_dict(),
            "amount_due": self.amount_due.to_dict(),
            "currency": self.currency,
            "due_date": self.due_date,
            "issued_date": self.issued_date,
            "paid_date": self.paid_date,
            "notes": self.notes,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_paid": self.is_paid,
            "is_overdue": self.is_overdue,
            "payment_progress_pct": self.payment_progress_pct,
        }


@dataclass
class Payment:
    payment_id: str = field(default_factory=_generate_id)
    amount: Money = field(default_factory=lambda: Money())
    from_account_id: str = ""
    to_account_id: str = ""
    method: str = ""
    reference: str = ""
    status: str = TransactionStatus.PENDING.value
    fee: Money = field(default_factory=lambda: Money())
    net_amount: Money = field(default_factory=lambda: Money())
    description: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    initiated_at: str = field(default_factory=_now_iso)
    completed_at: str | None = None

    @property
    def is_completed(self) -> bool:
        return self.status == TransactionStatus.CLEARED.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "amount": self.amount.to_dict(),
            "from_account_id": self.from_account_id,
            "to_account_id": self.to_account_id,
            "method": self.method,
            "reference": self.reference,
            "status": self.status,
            "fee": self.fee.to_dict(),
            "net_amount": self.net_amount.to_dict(),
            "description": self.description,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "initiated_at": self.initiated_at,
            "completed_at": self.completed_at,
        }


@dataclass
class Quotation:
    quotation_id: str = field(default_factory=_generate_id)
    quotation_number: str = ""
    status: str = "draft"
    issuer_id: str = ""
    recipient_id: str = ""
    line_items: list[dict[str, Any]] = field(default_factory=list)
    subtotal: Money = field(default_factory=lambda: Money())
    tax_amount: Money = field(default_factory=lambda: Money())
    discount_amount: Money = field(default_factory=lambda: Money())
    total_amount: Money = field(default_factory=lambda: Money())
    currency: str = "INR"
    valid_until: str = ""
    pricing_model: str = PricingModel.FIXED.value
    terms: str = ""
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "quotation_id": self.quotation_id,
            "quotation_number": self.quotation_number,
            "status": self.status,
            "issuer_id": self.issuer_id,
            "recipient_id": self.recipient_id,
            "line_items": list(self.line_items),
            "subtotal": self.subtotal.to_dict(),
            "tax_amount": self.tax_amount.to_dict(),
            "discount_amount": self.discount_amount.to_dict(),
            "total_amount": self.total_amount.to_dict(),
            "currency": self.currency,
            "valid_until": self.valid_until,
            "pricing_model": self.pricing_model,
            "terms": self.terms,
            "notes": self.notes,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CashFlowSummary:
    summary_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    period: str = "monthly"
    start_date: str = ""
    end_date: str = ""
    total_inflow: Money = field(default_factory=lambda: Money())
    total_outflow: Money = field(default_factory=lambda: Money())
    net_flow: Money = field(default_factory=lambda: Money())
    opening_balance: Money = field(default_factory=lambda: Money())
    closing_balance: Money = field(default_factory=lambda: Money())
    categories: dict[str, dict[str, float]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_positive(self) -> bool:
        return self.net_flow.amount >= 0

    @property
    def burn_rate(self) -> Money:
        if self.net_flow.amount < 0:
            return Money(amount=abs(self.net_flow.amount), currency=self.net_flow.currency)
        return Money(amount=0.0, currency=self.net_flow.currency)

    @property
    def runway_months(self) -> float:
        if self.burn_rate.amount <= 0:
            return float("inf")
        return self.closing_balance.amount / self.burn_rate.amount

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "owner_id": self.owner_id,
            "period": self.period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_inflow": self.total_inflow.to_dict(),
            "total_outflow": self.total_outflow.to_dict(),
            "net_flow": self.net_flow.to_dict(),
            "opening_balance": self.opening_balance.to_dict(),
            "closing_balance": self.closing_balance.to_dict(),
            "categories": dict(self.categories),
            "metadata": dict(self.metadata),
            "burn_rate": self.burn_rate.to_dict(),
            "runway_months": self.runway_months,
        }


@dataclass
class FinancialGoal:
    goal_id: str = field(default_factory=_generate_id)
    name: str = ""
    goal_type: str = FinancialGoalType.SAVINGS.value
    target_amount: Money = field(default_factory=lambda: Money())
    current_amount: Money = field(default_factory=lambda: Money())
    currency: str = "INR"
    status: str = FinancialGoalStatus.ACTIVE.value
    target_date: str = ""
    owner_id: str = ""
    category: str = ""
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def progress_pct(self) -> float:
        if self.target_amount.amount == 0:
            return 0.0
        return min(100.0, (self.current_amount.amount / self.target_amount.amount) * 100.0)

    @property
    def remaining_amount(self) -> Money:
        return Money(
            amount=max(0.0, self.target_amount.amount - self.current_amount.amount),
            currency=self.currency,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "name": self.name,
            "goal_type": self.goal_type,
            "target_amount": self.target_amount.to_dict(),
            "current_amount": self.current_amount.to_dict(),
            "currency": self.currency,
            "status": self.status,
            "target_date": self.target_date,
            "owner_id": self.owner_id,
            "category": self.category,
            "notes": self.notes,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "progress_pct": self.progress_pct,
            "remaining_amount": self.remaining_amount.to_dict(),
        }


@dataclass
class FinancialRisk:
    risk_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    risk_type: str = ""
    level: str = RiskLevel.MEDIUM.value
    description: str = ""
    impact: str = ""
    probability: float = 0.5
    affected_amount: Money = field(default_factory=lambda: Money())
    triggers: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "owner_id": self.owner_id,
            "risk_type": self.risk_type,
            "level": self.level,
            "description": self.description,
            "impact": self.impact,
            "probability": self.probability,
            "affected_amount": self.affected_amount.to_dict(),
            "triggers": list(self.triggers),
            "mitigations": list(self.mitigations),
            "metadata": dict(self.metadata),
            "detected_at": self.detected_at,
        }


@dataclass
class Forecast:
    forecast_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    forecast_type: str = "cash_flow"
    period: str = "monthly"
    horizon_months: int = 3
    projections: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    assumptions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "forecast_id": self.forecast_id,
            "owner_id": self.owner_id,
            "forecast_type": self.forecast_type,
            "period": self.period,
            "horizon_months": self.horizon_months,
            "projections": list(self.projections),
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class FinancialInsight:
    insight_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    impact: Money = field(default_factory=lambda: Money())
    confidence: float = 0.0
    actionable: bool = False
    action_suggestion: str = ""
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "owner_id": self.owner_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "impact": self.impact.to_dict(),
            "confidence": self.confidence,
            "actionable": self.actionable,
            "action_suggestion": self.action_suggestion,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class FinancialProfile:
    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    accounts: list[Account] = field(default_factory=list)
    wallets: list[Wallet] = field(default_factory=list)
    transactions: list[Transaction] = field(default_factory=list)
    budgets: list[Budget] = field(default_factory=list)
    invoices: list[Invoice] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list)
    quotations: list[Quotation] = field(default_factory=list)
    goals: list[FinancialGoal] = field(default_factory=list)
    risks: list[FinancialRisk] = field(default_factory=list)
    forecasts: list[Forecast] = field(default_factory=list)
    insights: list[FinancialInsight] = field(default_factory=list)
    cash_flows: list[CashFlowSummary] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def total_balance(self) -> Money:
        total = Money(currency=self._primary_currency())
        for a in self.accounts:
            if a.balance.currency == total.currency:
                total += a.balance
        return total

    @property
    def total_assets(self) -> Money:
        total = Money(currency=self._primary_currency())
        for a in self.accounts:
            if a.account_type in (
                AccountType.CHECKING.value, AccountType.SAVINGS.value,
                AccountType.INVESTMENT.value, AccountType.CASH.value,
                AccountType.WALLET.value,
            ):
                if a.balance.currency == total.currency:
                    total += a.balance
        return total

    @property
    def total_liabilities(self) -> Money:
        total = Money(currency=self._primary_currency())
        for a in self.accounts:
            if a.account_type in (
                AccountType.CREDIT_CARD.value, AccountType.LOAN.value,
                AccountType.MORTGAGE.value, AccountType.PAYABLE.value,
            ):
                if a.balance.currency == total.currency:
                    total += a.balance
        return total

    @property
    def net_worth(self) -> Money:
        return self.total_assets - self.total_liabilities

    @property
    def active_goals(self) -> list[FinancialGoal]:
        active_stati = {FinancialGoalStatus.ACTIVE.value, FinancialGoalStatus.ON_TRACK.value,
                        FinancialGoalStatus.AT_RISK.value, FinancialGoalStatus.BEHIND.value}
        return [g for g in self.goals if g.status in active_stati]

    def _primary_currency(self) -> str:
        currencies = {a.balance.currency for a in self.accounts if a.balance.amount != 0}
        return next(iter(currencies)) if currencies else "INR"

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "owner_id": self.owner_id,
            "label": self.label,
            "accounts": [a.to_dict() for a in self.accounts],
            "wallets": [w.to_dict() for w in self.wallets],
            "transactions": [t.to_dict() for t in self.transactions],
            "budgets": [b.to_dict() for b in self.budgets],
            "invoices": [i.to_dict() for i in self.invoices],
            "payments": [p.to_dict() for p in self.payments],
            "quotations": [q.to_dict() for q in self.quotations],
            "goals": [g.to_dict() for g in self.goals],
            "risks": [r.to_dict() for r in self.risks],
            "forecasts": [f.to_dict() for f in self.forecasts],
            "insights": [i.to_dict() for i in self.insights],
            "cash_flows": [c.to_dict() for c in self.cash_flows],
            "total_balance": self.total_balance.to_dict(),
            "total_assets": self.total_assets.to_dict(),
            "total_liabilities": self.total_liabilities.to_dict(),
            "net_worth": self.net_worth.to_dict(),
            "active_goals_count": len(self.active_goals),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── UCP-03A Reasoning Models ────────────────────────────────────────────────

@dataclass
class ScenarioSimulation:
    simulation_id: str = field(default_factory=_generate_id)
    scenario_name: str = ""
    description: str = ""
    baseline: dict[str, Any] = field(default_factory=dict)
    projected: dict[str, Any] = field(default_factory=dict)
    delta: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.5
    assumptions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    recommendation_confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "scenario_name": self.scenario_name,
            "description": self.description,
            "baseline": dict(self.baseline),
            "projected": dict(self.projected),
            "delta": dict(self.delta),
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "risks": list(self.risks),
            "evidence": list(self.evidence),
            "recommendation": self.recommendation,
            "recommendation_confidence": self.recommendation_confidence,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class FinancialTradeOff:
    tradeoff_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    alternative_a: dict[str, Any] = field(default_factory=dict)
    alternative_b: dict[str, Any] = field(default_factory=dict)
    opportunity_cost: Money = field(default_factory=lambda: Money())
    recommended_alternative: str = ""
    rationale: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tradeoff_id": self.tradeoff_id,
            "title": self.title,
            "description": self.description,
            "alternative_a": dict(self.alternative_a),
            "alternative_b": dict(self.alternative_b),
            "opportunity_cost": self.opportunity_cost.to_dict(),
            "recommended_alternative": self.recommended_alternative,
            "rationale": self.rationale,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class DecisionSupport:
    decision_id: str = field(default_factory=_generate_id)
    title: str = ""
    context: str = ""
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    analysis: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    recommendation_confidence: float = 0.0
    evidence: list[dict[str, Any]] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "context": self.context,
            "alternatives": list(self.alternatives),
            "analysis": dict(self.analysis),
            "recommendation": self.recommendation,
            "recommendation_confidence": self.recommendation_confidence,
            "evidence": list(self.evidence),
            "risks": list(self.risks),
            "next_steps": list(self.next_steps),
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class AffordabilityAnalysis:
    analysis_id: str = field(default_factory=_generate_id)
    item_name: str = ""
    item_cost: Money = field(default_factory=lambda: Money())
    is_affordable: bool = False
    affordability_score: float = 0.0
    available_funds: Money = field(default_factory=lambda: Money())
    impact_on_cash_flow: Money = field(default_factory=lambda: Money())
    impact_on_savings_rate: float = 0.0
    months_to_recover: float = 0.0
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "item_name": self.item_name,
            "item_cost": self.item_cost.to_dict(),
            "is_affordable": self.is_affordable,
            "affordability_score": self.affordability_score,
            "available_funds": self.available_funds.to_dict(),
            "impact_on_cash_flow": self.impact_on_cash_flow.to_dict(),
            "impact_on_savings_rate": self.impact_on_savings_rate,
            "months_to_recover": self.months_to_recover,
            "evidence": list(self.evidence),
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class HiringImpact:
    analysis_id: str = field(default_factory=_generate_id)
    role_name: str = ""
    annual_salary: Money = field(default_factory=lambda: Money())
    total_cost: Money = field(default_factory=lambda: Money())
    existing_payroll: Money = field(default_factory=lambda: Money())
    payroll_increase_pct: float = 0.0
    revenue_per_employee: Money = field(default_factory=lambda: Money())
    break_even_revenue: Money = field(default_factory=lambda: Money())
    break_even_months: float = 0.0
    impact_on_runway: float = 0.0
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "role_name": self.role_name,
            "annual_salary": self.annual_salary.to_dict(),
            "total_cost": self.total_cost.to_dict(),
            "existing_payroll": self.existing_payroll.to_dict(),
            "payroll_increase_pct": self.payroll_increase_pct,
            "revenue_per_employee": self.revenue_per_employee.to_dict(),
            "break_even_revenue": self.break_even_revenue.to_dict(),
            "break_even_months": self.break_even_months,
            "impact_on_runway": self.impact_on_runway,
            "evidence": list(self.evidence),
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class CustomerPaymentRisk:
    risk_id: str = field(default_factory=_generate_id)
    customer_id: str = ""
    customer_name: str = ""
    risk_score: float = 0.0
    risk_level: str = "low"
    total_outstanding: Money = field(default_factory=lambda: Money())
    overdue_amount: Money = field(default_factory=lambda: Money())
    payment_history: dict[str, Any] = field(default_factory=dict)
    avg_payment_delay_days: float = 0.0
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "total_outstanding": self.total_outstanding.to_dict(),
            "overdue_amount": self.overdue_amount.to_dict(),
            "payment_history": dict(self.payment_history),
            "avg_payment_delay_days": self.avg_payment_delay_days,
            "evidence": list(self.evidence),
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class SupplierPaymentOptimization:
    optimization_id: str = field(default_factory=_generate_id)
    supplier_id: str = ""
    supplier_name: str = ""
    total_payable: Money = field(default_factory=lambda: Money())
    current_terms_days: int = 30
    recommended_terms_days: int = 45
    cash_flow_impact: Money = field(default_factory=lambda: Money())
    risk_of_extension: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "optimization_id": self.optimization_id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "total_payable": self.total_payable.to_dict(),
            "current_terms_days": self.current_terms_days,
            "recommended_terms_days": self.recommended_terms_days,
            "cash_flow_impact": self.cash_flow_impact.to_dict(),
            "risk_of_extension": self.risk_of_extension,
            "evidence": list(self.evidence),
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class CommitmentConflict:
    conflict_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    commitments: list[dict[str, Any]] = field(default_factory=list)
    conflict_type: str = ""
    impact: str = ""
    severity: str = "medium"
    resolution: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "title": self.title,
            "description": self.description,
            "commitments": list(self.commitments),
            "conflict_type": self.conflict_type,
            "impact": self.impact,
            "severity": self.severity,
            "resolution": self.resolution,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
            "detected_at": self.detected_at,
        }