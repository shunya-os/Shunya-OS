"""Universal Financial Intelligence — Runtime.

The FinancialIntelligenceRuntime is the canonical UCP-03 runtime.
Composes from frozen SHUNYA platform runtimes:

- Living Object Composer (core/kernel)
- Universal Execution Runtime (core/execution_runtime)
- Reality Runtime (core/event + notify pattern)
- Relationship Intelligence (UCP-02)
- Cognitive Runtime (core/cognitive_runtime)

No Financial Runtime. No Accounting Runtime. No ERP Runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.financial_intelligence.engine import FinancialIntelligenceEngine
from core.financial_intelligence.models import (
    Account,
    AccountType,
    Budget,
    BudgetPeriod,
    CashFlowSummary,
    FinancialGoal,
    FinancialGoalStatus,
    FinancialGoalType,
    FinancialInsight,
    FinancialProfile,
    FinancialRisk,
    Forecast,
    Invoice,
    InvoiceStatus,
    Money,
    Payment,
    Quotation,
    Transaction,
    TransactionStatus,
    TransactionType,
    _generate_id,
    _now_iso,
)

logger = logging.getLogger(__name__)


class FinancialIntelligenceRuntime:
    """Universal Financial Intelligence — single capability runtime.

    Orchestrates financial analysis, forecasting, risk detection,
    budget optimization, and Reality integration into one interface.

    Composes from frozen SHUNYA runtimes — never introduces a
    Financial Runtime, Accounting Runtime, or ERP Runtime.

    Usage:
        runtime = FinancialIntelligenceRuntime()
        profile = runtime.get_or_create_profile(owner_id="person_001")

        # Add accounts and transactions
        runtime.add_account(profile.profile_id, name="Checking", ...)
        runtime.record_transaction(profile.profile_id, ...)

        # Assess health
        health = runtime.assess_financial_health(profile.profile_id)

        # Get forecast
        forecast = runtime.forecast_cash_flow(profile.profile_id)
    """

    def __init__(self) -> None:
        self._engine = FinancialIntelligenceEngine()
        # In-memory profile store (replaced by persistent store in production)
        self._profiles: dict[str, FinancialProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    # ── Profile Management ──────────────────────────────────────────────

    def get_or_create_profile(
        self,
        owner_id: str,
        label: str = "",
    ) -> FinancialProfile:
        """Get or create a financial profile for an entity."""
        if owner_id in self._profiles:
            return self._profiles[owner_id]

        profile = FinancialProfile(
            owner_id=owner_id,
            label=label or f"Financial profile for {owner_id}",
        )
        self._profiles[profile.profile_id] = profile
        self._notify({
            "type": "financial_intelligence.profile_created",
            "profile_id": profile.profile_id,
            "owner_id": owner_id,
        })
        return profile

    def get_profile(self, profile_id: str) -> FinancialProfile | None:
        return self._profiles.get(profile_id)

    def get_profile_by_owner(self, owner_id: str) -> FinancialProfile | None:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        return None

    # ── Account Management ──────────────────────────────────────────────

    def add_account(
        self,
        profile_id: str,
        name: str,
        account_type: str = AccountType.CHECKING.value,
        balance: float = 0.0,
        currency: str = "INR",
        institution: str = "",
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Account | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        account = Account(
            name=name,
            account_type=account_type,
            balance=Money(amount=balance, currency=currency),
            currency=currency,
            institution=institution,
            owner_id=profile.owner_id,
            description=description,
            metadata=metadata or {},
        )
        profile.accounts.append(account)
        profile.updated_at = _now_iso()
        return account

    def get_account(self, profile_id: str, account_id: str) -> Account | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        for a in profile.accounts:
            if a.account_id == account_id:
                return a
        return None

    # ── Transaction Recording ───────────────────────────────────────────

    def record_transaction(
        self,
        profile_id: str,
        transaction_type: str = TransactionType.EXPENSE.value,
        amount: float = 0.0,
        currency: str = "INR",
        from_account_id: str = "",
        to_account_id: str = "",
        description: str = "",
        category: str = "",
        tags: list[str] | None = None,
        counterparty: str = "",
        occurred_at: str | None = None,
    ) -> Transaction | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        # Update account balances
        money = Money(amount=amount, currency=currency)
        if from_account_id:
            from_acct = self.get_account(profile_id, from_account_id)
            if from_acct:
                from_acct.balance -= money
                from_acct.updated_at = _now_iso()
        if to_account_id:
            to_acct = self.get_account(profile_id, to_account_id)
            if to_acct:
                to_acct.balance += money
                to_acct.updated_at = _now_iso()

        txn = Transaction(
            transaction_type=transaction_type,
            amount=money,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            description=description,
            category=category,
            tags=tags or [],
            counterparty=counterparty,
            occurred_at=occurred_at or _now_iso(),
        )
        profile.transactions.append(txn)
        profile.updated_at = _now_iso()

        self._notify({
            "type": "financial_intelligence.transaction_recorded",
            "profile_id": profile_id,
            "transaction_id": txn.transaction_id,
            "amount": amount,
            "transaction_type": transaction_type,
        })
        return txn

    # ── Budget Management ───────────────────────────────────────────────

    def create_budget(
        self,
        profile_id: str,
        name: str,
        total_planned: float,
        period: str = BudgetPeriod.MONTHLY.value,
        currency: str = "INR",
        categories: dict[str, dict[str, float]] | None = None,
        start_date: str = "",
        end_date: str = "",
    ) -> Budget | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        budget = Budget(
            name=name,
            total_planned=Money(amount=total_planned, currency=currency),
            period=period,
            categories=categories or {},
            owner_id=profile.owner_id,
            start_date=start_date or _now_iso()[:10],
            end_date=end_date or "",
        )
        profile.budgets.append(budget)
        profile.updated_at = _now_iso()
        return budget

    def update_budget_spending(self, profile_id: str, budget_id: str,
                               amount: float, currency: str = "INR") -> bool:
        """Update budget spending from a transaction."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        for budget in profile.budgets:
            if budget.budget_id == budget_id:
                money = Money(amount=amount, currency=currency)
                budget.total_spent += money
                budget.total_remaining = budget.total_planned - budget.total_spent
                budget.updated_at = _now_iso()
                return True
        return False

    # ── Invoice Management ──────────────────────────────────────────────

    def create_invoice(
        self,
        profile_id: str,
        invoice_number: str,
        issuer_id: str,
        recipient_id: str,
        line_items: list[dict[str, Any]],
        subtotal: float,
        tax_amount: float = 0.0,
        discount_amount: float = 0.0,
        total_amount: float = 0.0,
        currency: str = "INR",
        due_date: str = "",
        notes: str = "",
    ) -> Invoice | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        invoice = Invoice(
            invoice_number=invoice_number,
            issuer_id=issuer_id,
            recipient_id=recipient_id,
            line_items=line_items,
            subtotal=Money(amount=subtotal, currency=currency),
            tax_amount=Money(amount=tax_amount, currency=currency),
            discount_amount=Money(amount=discount_amount, currency=currency),
            total_amount=Money(amount=total_amount, currency=currency),
            amount_due=Money(amount=total_amount, currency=currency),
            currency=currency,
            due_date=due_date,
            issued_date=_now_iso()[:10],
            notes=notes,
        )
        profile.invoices.append(invoice)
        profile.updated_at = _now_iso()

        self._notify({
            "type": "financial_intelligence.invoice_created",
            "profile_id": profile_id,
            "invoice_id": invoice.invoice_id,
            "total_amount": total_amount,
        })
        return invoice

    def record_payment(
        self,
        profile_id: str,
        invoice_id: str,
        amount: float,
        currency: str = "INR",
        method: str = "bank_transfer",
        from_account_id: str = "",
        to_account_id: str = "",
    ) -> Payment | None:
        """Record a payment against an invoice."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        invoice = None
        for inv in profile.invoices:
            if inv.invoice_id == invoice_id:
                invoice = inv
                break
        if not invoice:
            return None

        payment = Payment(
            amount=Money(amount=amount, currency=currency),
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            method=method,
            reference=invoice_id,
            net_amount=Money(amount=amount, currency=currency),
        )
        profile.payments.append(payment)

        # Update invoice
        invoice.amount_paid += payment.amount
        invoice.amount_due = invoice.total_amount - invoice.amount_paid
        if invoice.amount_due.amount <= 0:
            invoice.status = InvoiceStatus.PAID.value
            invoice.paid_date = _now_iso()[:10]
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID.value
        invoice.updated_at = _now_iso()

        # Record as transaction
        self.record_transaction(
            profile_id=profile_id,
            transaction_type=TransactionType.INCOME.value,
            amount=amount,
            currency=currency,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            description=f"Payment for invoice {invoice.invoice_number}",
            category="invoice_payment",
            counterparty=invoice.issuer_id if invoice.issuer_id != profile.owner_id else invoice.recipient_id,
        )

        self._notify({
            "type": "financial_intelligence.payment_recorded",
            "profile_id": profile_id,
            "invoice_id": invoice_id,
            "payment_id": payment.payment_id,
            "amount": amount,
        })
        return payment

    def create_quotation(
        self,
        profile_id: str,
        quotation_number: str,
        issuer_id: str,
        recipient_id: str,
        line_items: list[dict[str, Any]],
        subtotal: float,
        total_amount: float,
        currency: str = "INR",
        valid_until: str = "",
        pricing_model: str = "fixed",
        terms: str = "",
        tax_amount: float = 0.0,
        discount_amount: float = 0.0,
    ) -> Quotation | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        quotation = Quotation(
            quotation_number=quotation_number,
            issuer_id=issuer_id,
            recipient_id=recipient_id,
            line_items=line_items,
            subtotal=Money(amount=subtotal, currency=currency),
            tax_amount=Money(amount=tax_amount, currency=currency),
            discount_amount=Money(amount=discount_amount, currency=currency),
            total_amount=Money(amount=total_amount, currency=currency),
            currency=currency,
            valid_until=valid_until,
            pricing_model=pricing_model,
            terms=terms,
        )
        profile.quotations.append(quotation)
        profile.updated_at = _now_iso()
        return quotation

    # ── Goal Management ─────────────────────────────────────────────────

    def create_goal(
        self,
        profile_id: str,
        name: str,
        target_amount: float,
        goal_type: str = FinancialGoalType.SAVINGS.value,
        currency: str = "INR",
        target_date: str = "",
        category: str = "",
    ) -> FinancialGoal | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        goal = FinancialGoal(
            name=name,
            goal_type=goal_type,
            target_amount=Money(amount=target_amount, currency=currency),
            currency=currency,
            target_date=target_date,
            owner_id=profile.owner_id,
            category=category,
        )
        profile.goals.append(goal)
        profile.updated_at = _now_iso()
        return goal

    # ── Financial Analysis ──────────────────────────────────────────────

    def assess_financial_health(self, profile_id: str) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        result = self._engine.assess_financial_health(profile)
        self._notify({
            "type": "financial_intelligence.health_assessed",
            "profile_id": profile_id,
            "score": result["overall_score"],
            "assessment": result["assessment"],
        })
        return result

    def compute_cash_flow(self, profile_id: str) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        cf = self._engine.compute_cash_flow(profile)
        return cf.to_dict()

    def forecast_cash_flow(self, profile_id: str,
                           horizon_months: int = 3) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        forecast = self._engine.forecast_cash_flow(profile, horizon_months)
        return forecast.to_dict()

    def detect_risks(self, profile_id: str) -> list[dict[str, Any]] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        risks = self._engine.detect_risks(profile)
        return [r.to_dict() for r in risks]

    def get_spending_insights(self, profile_id: str) -> list[dict[str, Any]] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        insights = self._engine.analyze_spending(profile)
        return [i.to_dict() for i in insights]

    def get_revenue_opportunities(self, profile_id: str) -> list[dict[str, Any]] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        opportunities = self._engine.detect_revenue_opportunities(profile)
        return [o.to_dict() for o in opportunities]

    def recommend_pricing(
        self,
        profile_id: str,
        base_cost: float,
        currency: str = "INR",
        desired_margin_pct: float = 20.0,
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.recommend_pricing(
            profile,
            Money(amount=base_cost, currency=currency),
            desired_margin_pct,
        )

    def analyze_goal(self, profile_id: str, goal_id: str) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        for goal in profile.goals:
            if goal.goal_id == goal_id:
                return self._engine.analyze_goal(goal)
        return None

    def get_ai_context(self, profile_id: str) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.prepare_ai_context(profile)

    # ── UCP-03A Financial Reasoning ─────────────────────────────────────

    def analyze_affordability(
        self, profile_id: str, item_name: str, item_cost: float,
        currency: str = "INR",
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        result = self._engine.analyze_affordability(
            profile, item_name, Money(amount=item_cost, currency=currency))
        return result.to_dict()

    def compute_opportunity_cost(
        self, profile_id: str, investment_a: float, investment_b: float,
        currency: str = "INR", time_horizon_months: int = 12,
        return_a: float = 4.0, return_b: float = 8.0,
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.compute_opportunity_cost(
            profile, Money(amount=investment_a, currency=currency),
            Money(amount=investment_b, currency=currency),
            time_horizon_months, return_a, return_b,
        )

    def simulate_scenario(
        self, profile_id: str, scenario_name: str, description: str,
        revenue_delta_pct: float = 0.0, expense_delta_pct: float = 0.0,
        horizon_months: int = 6, one_time_impact: float = 0.0,
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        result = self._engine.simulate_scenario(
            profile, scenario_name, description,
            revenue_delta_pct, expense_delta_pct, horizon_months, one_time_impact)
        return result.to_dict()

    def forecast_revenue(self, profile_id: str, horizon_months: int = 6) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.forecast_revenue(profile, horizon_months)

    def forecast_expenses(self, profile_id: str, horizon_months: int = 6) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.forecast_expenses(profile, horizon_months)

    def analyze_runway(self, profile_id: str) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.analyze_runway(profile)

    def analyze_hiring_impact(
        self, profile_id: str, role_name: str,
        annual_salary: float, currency: str = "INR", benefits_pct: float = 20.0,
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        result = self._engine.analyze_hiring_impact(
            profile, role_name, Money(amount=annual_salary, currency=currency), benefits_pct)
        return result.to_dict()

    def analyze_investment(
        self, profile_id: str, principal: float,
        annual_return_pct: float, currency: str = "INR",
        time_horizon_months: int = 36, monthly_contribution: float = 0.0,
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        mc = Money(amount=monthly_contribution, currency=currency) if monthly_contribution else None
        return self._engine.analyze_investment(
            profile, Money(amount=principal, currency=currency),
            annual_return_pct, time_horizon_months, mc,
        )

    def analyze_tradeoffs(
        self, profile_id: str, option_a_name: str, option_a_cost: float,
        option_a_benefit: str, option_b_name: str, option_b_cost: float,
        option_b_benefit: str, currency: str = "INR",
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        result = self._engine.analyze_tradeoffs(
            profile, option_a_name, Money(amount=option_a_cost, currency=currency),
            option_a_benefit, option_b_name, Money(amount=option_b_cost, currency=currency),
            option_b_benefit)
        return result.to_dict()

    def assess_customer_payment_risk(
        self, profile_id: str, customer_id: str, customer_name: str = "",
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        result = self._engine.assess_customer_payment_risk(profile, customer_id, customer_name)
        return result.to_dict()

    def optimize_supplier_payments(
        self, profile_id: str, supplier_id: str, supplier_name: str = "",
        total_payable: float = 0.0, currency: str = "INR", current_terms_days: int = 30,
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        payable = Money(amount=total_payable, currency=currency) if total_payable else None
        result = self._engine.optimize_supplier_payments(
            profile, supplier_id, supplier_name, payable, current_terms_days)
        return result.to_dict()

    def detect_commitment_conflicts(self, profile_id: str) -> list[dict[str, Any]] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        conflicts = self._engine.detect_commitment_conflicts(profile)
        return [c.to_dict() for c in conflicts]

    def decision_support(
        self, profile_id: str, title: str, context: str,
        options: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        result = self._engine.decision_support(profile, title, context, options)
        return result.to_dict()

    # ── Reality Integration ─────────────────────────────────────────────

    def notify(self, notification: dict[str, Any]) -> None:
        """Handle Reality notifications for financial intelligence.

        Single public interface for Reality integration.
        Unknown notification types are silently ignored (contract).
        """
        notification_type = notification.get("type", "")

        if notification_type == "execution.payment_received":
            profile_id = notification.get("profile_id", "")
            invoice_id = notification.get("invoice_id", "")
            amount = notification.get("amount", 0.0)
            if profile_id and invoice_id and amount:
                self.record_payment(
                    profile_id=profile_id,
                    invoice_id=invoice_id,
                    amount=amount,
                )

        elif notification_type == "execution.transaction_recorded":
            profile_id = notification.get("profile_id", "")
            if profile_id:
                self.record_transaction(
                    profile_id=profile_id,
                    transaction_type=notification.get("transaction_type", "expense"),
                    amount=notification.get("amount", 0.0),
                    description=notification.get("description", ""),
                    category=notification.get("category", ""),
                )
        # Unknown types silently ignored (contract)

    # ── Adaptive Execution Integration ──────────────────────────────────

    # ── Engine Lifecycle ────────────────────────────────────────────────

    def initialize(self) -> None:
        logger.info("FinancialIntelligenceRuntime initialized")

    def shutdown(self) -> None:
        self._profiles.clear()
        self._reality_listeners.clear()
        logger.info("FinancialIntelligenceRuntime shut down")

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": "financial_intelligence",
            "profile_count": len(self._profiles),
        }

    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict):
            self.notify(event)

    def get_capabilities(self) -> list[str]:
        return [
            "financial.profile",
            "financial.account",
            "financial.transaction",
            "financial.budget",
            "financial.invoice",
            "financial.payment",
            "financial.quotation",
            "financial.goal",
            "financial.health",
            "financial.cash_flow",
            "financial.forecast",
            "financial.risk_detection",
            "financial.spending_insights",
            "financial.revenue_opportunities",
            "financial.pricing",
            "financial.reality_integration",
            "financial.execution_integration",
        ]

    # ── Internal ────────────────────────────────────────────────────────

    def _notify(self, notification: dict[str, Any]) -> None:
        for listener in self._reality_listeners:
            try:
                listener(notification)
            except Exception:
                logger.exception("Reality listener failed for notification")

    def register_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        self._reality_listeners.append(listener)

    def unregister_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        if listener in self._reality_listeners:
            self._reality_listeners.remove(listener)