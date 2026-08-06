"""Universal Financial Intelligence — Core Engine.

Pure computation engine for financial analysis:
- Cash flow forecasting
- Budget optimization
- Financial risk detection
- Pricing recommendations
- Spending insights
- Revenue opportunity detection
- Financial health assessment
- Goal tracking analysis

Pure computation — no storage, no side effects.
Thread-safe by design.
"""

from __future__ import annotations

from typing import Any

from core.financial_intelligence.models import (
    Account,
    AccountType,
    AffordabilityAnalysis,
    Budget,
    CashFlowDirection,
    CashFlowSummary,
    CommitmentConflict,
    CustomerPaymentRisk,
    DecisionSupport,
    FinancialGoal,
    FinancialInsight,
    FinancialProfile,
    FinancialRisk,
    FinancialTradeOff,
    Forecast,
    HiringImpact,
    Invoice,
    InvoiceStatus,
    Money,
    RiskLevel,
    ScenarioSimulation,
    SupplierPaymentOptimization,
    Transaction,
    TransactionType,
    _generate_id,
    _now_iso,
)


class FinancialIntelligenceEngine:
    """Pure computation engine for Universal Financial Intelligence.

    Every method is a pure function: input → output, no state.
    """

    # ── Cash Flow Analysis ──────────────────────────────────────────────

    def compute_cash_flow(
        self,
        profile: FinancialProfile,
        start_date: str = "",
        end_date: str = "",
    ) -> CashFlowSummary:
        """Compute cash flow summary for a period."""
        total_inflow = Money(currency=self._primary_currency(profile))
        total_outflow = Money(currency=self._primary_currency(profile))
        categories: dict[str, dict[str, float]] = {}

        for txn in profile.transactions:
            amt = txn.amount
            if txn.is_inflow and amt.amount > 0:
                total_inflow += amt
                cat = txn.category or "uncategorized"
                if cat not in categories:
                    categories[cat] = {"inflow": 0.0, "outflow": 0.0, "count": 0}
                categories[cat]["inflow"] += amt.amount
                categories[cat]["count"] += 1
            elif txn.is_outflow and amt.amount > 0:
                total_outflow += amt
                cat = txn.category or "uncategorized"
                if cat not in categories:
                    categories[cat] = {"inflow": 0.0, "outflow": 0.0, "count": 0}
                categories[cat]["outflow"] += amt.amount
                categories[cat]["count"] += 1

        net_flow = total_inflow - total_outflow
        closing = profile.total_balance

        return CashFlowSummary(
            owner_id=profile.owner_id,
            total_inflow=total_inflow,
            total_outflow=total_outflow,
            net_flow=net_flow,
            closing_balance=closing,
            categories=categories,
            start_date=start_date,
            end_date=end_date,
        )

    # ── Forecasting ─────────────────────────────────────────────────────

    def forecast_cash_flow(
        self,
        profile: FinancialProfile,
        horizon_months: int = 3,
    ) -> Forecast:
        """Project future cash flow based on historical patterns."""
        currency = self._primary_currency(profile)

        # Compute average monthly inflow and outflow
        monthly_inflow = Money(currency=currency)
        monthly_outflow = Money(currency=currency)
        month_count = 0

        # Simple approach: average over available transactions
        if profile.transactions:
            for txn in profile.transactions:
                if txn.is_inflow:
                    monthly_inflow += txn.amount
                elif txn.is_outflow:
                    monthly_outflow += txn.amount
            month_count = max(1, len(profile.transactions) // 10)

        avg_inflow = monthly_inflow / max(month_count, 1)
        avg_outflow = monthly_outflow / max(month_count, 1)

        projections = []
        running_balance = profile.total_balance.amount
        for month in range(1, horizon_months + 1):
            project_inflow = avg_inflow.amount * (1 + 0.02 * month)  # slight growth assumption
            project_outflow = avg_outflow.amount * (1 + 0.01 * month)  # slight expense inflation
            net = project_inflow - project_outflow
            running_balance += net
            projections.append({
                "month": month,
                "projected_inflow": round(project_inflow, 2),
                "projected_outflow": round(project_outflow, 2),
                "projected_net": round(net, 2),
                "projected_balance": round(running_balance, 2),
            })

        # Confidence based on data volume
        confidence = min(0.9, max(0.1, len(profile.transactions) / 100))

        return Forecast(
            owner_id=profile.owner_id,
            forecast_type="cash_flow",
            horizon_months=horizon_months,
            projections=projections,
            confidence=round(confidence, 2),
            assumptions=[
                "Historical average ±20%",
                f"Based on {len(profile.transactions)} transactions",
                "Expense inflation 1%/month assumed",
                "Revenue growth 2%/month assumed",
            ],
        )

    # ── Budget Analysis ─────────────────────────────────────────────────

    def analyze_budget(self, budget: Budget) -> list[FinancialInsight]:
        """Analyze budget performance and generate insights."""
        insights: list[FinancialInsight] = []

        if budget.is_over_budget:
            overshoot = budget.total_spent - budget.total_planned
            insights.append(FinancialInsight(
                owner_id=budget.owner_id,
                category="risk",
                title=f"Budget '{budget.name}' is over budget",
                description=f"Spent {budget.total_spent.amount:.2f} against {budget.total_planned.amount:.2f} planned",
                impact=overshoot,
                confidence=0.95,
                actionable=True,
                action_suggestion="Review spending categories and adjust budget allocation",
            ))

        if budget.utilization_pct > 80:
            insights.append(FinancialInsight(
                owner_id=budget.owner_id,
                category="optimization",
                title=f"Budget '{budget.name}' nearing limit ({budget.utilization_pct:.0f}%)",
                description="Budget utilization is high. Consider rebalancing before end of period.",
                confidence=0.85,
                actionable=True,
                action_suggestion="Review remaining budget and prioritize essential spending",
            ))

        if budget.utilization_pct < 30:
            insights.append(FinancialInsight(
                owner_id=budget.owner_id,
                category="observation",
                title=f"Budget '{budget.name}' underutilized ({budget.utilization_pct:.0f}%)",
                description="Budget is significantly underutilized. May indicate over-allocation.",
                confidence=0.70,
                actionable=True,
                action_suggestion="Review and reallocate to areas needing more resources",
            ))

        return insights

    def optimize_budget(
        self,
        profile: FinancialProfile,
        target_budget: Budget,
    ) -> list[dict[str, Any]]:
        """Generate budget optimization suggestions."""
        suggestions: list[dict[str, Any]] = []
        currency = self._primary_currency(profile)

        # Analyze spending by category
        category_spend: dict[str, float] = {}
        for txn in profile.transactions:
            if txn.is_outflow:
                cat = txn.category or "uncategorized"
                category_spend[cat] = category_spend.get(cat, 0) + txn.amount.amount

        if not category_spend:
            return suggestions

        total_spend = sum(category_spend.values())
        for cat, spent in sorted(category_spend.items(), key=lambda x: -x[1]):
            pct = (spent / total_spend) * 100 if total_spend else 0
            if pct > 30:
                suggestions.append({
                    "category": cat,
                    "current_pct": round(pct, 1),
                    "suggested_pct": round(min(pct * 0.8, 25.0), 1),
                    "potential_savings": round(spent * 0.2, 2),
                    "suggestion": f"Reduce spending in '{cat}' by 20%",
                })
            elif pct < 5 and cat != "uncategorized":
                suggestions.append({
                    "category": cat,
                    "current_pct": round(pct, 1),
                    "suggested_pct": round(pct, 1),
                    "potential_savings": 0.0,
                    "suggestion": f"'{cat}' spending is minimal — maintain current level",
                })

        return suggestions

    # ── Risk Detection ──────────────────────────────────────────────────

    def detect_risks(self, profile: FinancialProfile) -> list[FinancialRisk]:
        """Detect financial risks from profile data."""
        risks: list[FinancialRisk] = []
        currency = self._primary_currency(profile)

        # Risk: Low cash runway
        cash_balance = Money(currency=currency)
        for acct in profile.accounts:
            if acct.account_type in (
                AccountType.CHECKING.value, AccountType.SAVINGS.value,
                AccountType.CASH.value, AccountType.WALLET.value,
            ):
                if acct.balance.currency == currency:
                    cash_balance += acct.balance

        monthly_outflow = Money(currency=currency)
        recent_txns = profile.transactions[-30:] if len(profile.transactions) > 30 else profile.transactions
        for txn in recent_txns:
            if txn.is_outflow and txn.amount.currency == currency:
                monthly_outflow += txn.amount

        months_count = max(1, len(recent_txns) // 5)
        avg_monthly_outflow = monthly_outflow / months_count

        if avg_monthly_outflow.amount > 0 and cash_balance.amount > 0:
            runway = cash_balance.amount / avg_monthly_outflow.amount
            if runway < 3:
                risks.append(FinancialRisk(
                    owner_id=profile.owner_id,
                    risk_type="cash_flow_shortfall",
                    level=RiskLevel.CRITICAL.value if runway < 1 else RiskLevel.HIGH.value,
                    description=f"Low cash runway: {runway:.1f} months",
                    impact=f"Only {runway:.1f} months of operating expenses available",
                    probability=0.7 if runway < 1 else 0.4,
                    affected_amount=cash_balance,
                    triggers=["Low cash balance", "High monthly expenses"],
                    mitigations=["Reduce expenses", "Increase revenue", "Secure financing"],
                ))

        # Risk: High credit utilization
        total_credit_limit = Money(currency=currency)
        total_credit_used = Money(currency=currency)
        for acct in profile.accounts:
            if acct.account_type == AccountType.CREDIT_CARD.value:
                if acct.balance.currency == currency:
                    total_credit_used += acct.balance  # balance on credit cards is negative
                    total_credit_limit += Money(
                        amount=acct.metadata.get("credit_limit", 0.0),
                        currency=currency,
                    )

        if total_credit_limit.amount > 0:
            utilization = abs(total_credit_used.amount) / total_credit_limit.amount * 100
            if utilization > 70:
                risks.append(FinancialRisk(
                    owner_id=profile.owner_id,
                    risk_type="debt_overload",
                    level=RiskLevel.HIGH.value,
                    description=f"Credit utilization at {utilization:.0f}%",
                    impact=f"High credit utilization may affect credit score and borrowing capacity",
                    probability=0.6,
                    affected_amount=total_credit_used,
                    triggers=["High credit card balances"],
                    mitigations=["Pay down credit card balances", "Increase credit limits"],
                ))

        # Risk: Overdue invoices (for businesses)
        overdue_invoices = [inv for inv in profile.invoices if inv.status == InvoiceStatus.OVERDUE.value]
        if overdue_invoices:
            total_overdue = sum(inv.total_amount.amount for inv in overdue_invoices)
            risks.append(FinancialRisk(
                owner_id=profile.owner_id,
                risk_type="revenue_drop",
                level=RiskLevel.MEDIUM.value,
                description=f"{len(overdue_invoices)} overdue invoice(s) totaling {total_overdue:.2f}",
                impact="Delayed payments may affect cash flow",
                probability=0.5,
                affected_amount=Money(amount=total_overdue, currency=currency),
                triggers=["Overdue invoices"],
                mitigations=["Send payment reminders", "Review payment terms", "Follow up with clients"],
            ))

        return risks

    # ── Pricing Recommendations ─────────────────────────────────────────

    def recommend_pricing(
        self,
        profile: FinancialProfile,
        base_cost: Money,
        desired_margin_pct: float = 20.0,
    ) -> dict[str, Any]:
        """Generate pricing recommendations based on financial context."""
        currency = base_cost.currency

        # Calculate cost-plus pricing
        min_price = base_cost * (1 + desired_margin_pct / 100)

        # Calculate market-adjusted pricing (if we have comparable transactions)
        comparable_sales = [
            txn for txn in profile.transactions
            if txn.transaction_type == TransactionType.INCOME.value
        ]
        avg_sale = Money(currency=currency)
        if comparable_sales:
            for txn in comparable_sales:
                avg_sale += txn.amount
            avg_sale = avg_sale / len(comparable_sales)

        # Calculate profitability threshold
        total_revenue = Money(currency=currency)
        total_costs = Money(currency=currency)
        for txn in profile.transactions:
            if txn.is_inflow:
                total_revenue += txn.amount
            elif txn.is_outflow:
                total_costs += txn.amount

        profit_margin = 0.0
        if total_revenue.amount > 0:
            profit_margin = ((total_revenue.amount - total_costs.amount) / total_revenue.amount) * 100

        # Break-even analysis
        fixed_costs = total_costs.amount * 0.3  # assume 30% fixed costs
        variable_costs = total_costs.amount * 0.7  # 70% variable
        contribution_per_unit = base_cost.amount - (variable_costs / max(len(comparable_sales), 1))
        break_even_units = fixed_costs / max(contribution_per_unit, 1) if contribution_per_unit > 0 else float("inf")

        return {
            "base_cost": base_cost.to_dict(),
            "desired_margin_pct": desired_margin_pct,
            "min_price_cost_plus": round(min_price.amount, 2),
            "average_sale_price": round(avg_sale.amount, 2) if comparable_sales else None,
            "current_profit_margin_pct": round(profit_margin, 1),
            "recommended_price": max(round(min_price.amount, 2), round(avg_sale.amount, 2)),
            "break_even_units": round(break_even_units, 0),
            "pricing_models": ["fixed", "hourly", "subscription", "tiered"],
            "recommended_model": "fixed" if base_cost.amount < 10000 else "tiered",
            "assumptions": [
                f"Desired margin: {desired_margin_pct}%",
                f"Based on {len(comparable_sales)} comparable sales",
                "Fixed costs estimated at 30% of total costs",
            ],
        }

    # ── Spending Insights ───────────────────────────────────────────────

    def analyze_spending(self, profile: FinancialProfile) -> list[FinancialInsight]:
        """Generate spending insights from transaction history."""
        insights: list[FinancialInsight] = []
        currency = self._primary_currency(profile)

        if not profile.transactions:
            return insights

        # Top spending categories
        category_spend: dict[str, float] = {}
        for txn in profile.transactions:
            if txn.is_outflow:
                cat = txn.category or "uncategorized"
                category_spend[cat] = category_spend.get(cat, 0) + txn.amount.amount

        if category_spend:
            top_category = max(category_spend, key=category_spend.get)
            top_amount = category_spend[top_category]
            total = sum(category_spend.values())
            top_pct = (top_amount / total) * 100 if total > 0 else 0

            if top_pct > 40:
                insights.append(FinancialInsight(
                    owner_id=profile.owner_id,
                    category="spending_pattern",
                    title=f"High concentration in '{top_category}'",
                    description=f"{top_pct:.0f}% of spending is in '{top_category}' ({top_amount:.2f})",
                    impact=Money(amount=top_amount, currency=currency),
                    confidence=0.9,
                    actionable=True,
                    action_suggestion=f"Review '{top_category}' spending for optimization opportunities",
                ))

        # Recurring expenses
        recurring_categories = [cat for cat, amt in category_spend.items() if amt > 0]
        for cat in recurring_categories[:3]:
            cat_txns = [t for t in profile.transactions if t.category == cat and t.is_outflow]
            if len(cat_txns) >= 3:
                total_cat = sum(t.amount.amount for t in cat_txns)
                insights.append(FinancialInsight(
                    owner_id=profile.owner_id,
                    category="spending_pattern",
                    title=f"Recurring expense: '{cat}'",
                    description=f"Total {total_cat:.2f} across {len(cat_txns)} transactions in '{cat}'",
                    impact=Money(amount=total_cat, currency=currency),
                    confidence=0.75,
                    actionable=True,
                    action_suggestion=f"Audit '{cat}' subscriptions/services for cost optimization",
                ))

        # Income vs expense trend
        total_income = sum(t.amount.amount for t in profile.transactions if t.is_inflow)
        total_expenses = sum(t.amount.amount for t in profile.transactions if t.is_outflow)
        if total_income > 0:
            savings_rate = ((total_income - total_expenses) / total_income) * 100
            if savings_rate < 10:
                insights.append(FinancialInsight(
                    owner_id=profile.owner_id,
                    category="risk",
                    title=f"Low savings rate: {savings_rate:.0f}%",
                    description=f"Only {savings_rate:.0f}% of income is saved. Target: 20%+",
                    impact=Money(amount=total_income * 0.1, currency=currency),
                    confidence=0.85,
                    actionable=True,
                    action_suggestion="Review discretionary spending and increase savings rate",
                ))

        return insights

    # ── Revenue Opportunities ───────────────────────────────────────────

    def detect_revenue_opportunities(self, profile: FinancialProfile) -> list[FinancialInsight]:
        """Detect potential revenue opportunities."""
        insights: list[FinancialInsight] = []
        currency = self._primary_currency(profile)

        # Analyze for underutilized assets
        for acct in profile.accounts:
            if acct.account_type == AccountType.SAVINGS.value and acct.balance.amount > 50000:
                insights.append(FinancialInsight(
                    owner_id=profile.owner_id,
                    category="opportunity",
                    title=f"Large savings balance ({acct.balance.amount:.0f}) could earn more",
                    description=f"High-yield savings or short-term investments could generate additional income",
                    impact=Money(amount=acct.balance.amount * 0.04, currency=currency),
                    confidence=0.6,
                    actionable=True,
                    action_suggestion="Explore high-yield savings accounts or short-term FD/debt funds",
                ))

        # Check for unpaid invoices that could be collected
        unpaid = [inv for inv in profile.invoices if inv.status in (
            InvoiceStatus.SENT.value, InvoiceStatus.VIEWED.value,
            InvoiceStatus.PARTIALLY_PAID.value, InvoiceStatus.OVERDUE.value,
        )]
        if unpaid:
            total_unpaid = sum(inv.total_amount.amount - inv.amount_paid.amount for inv in unpaid)
            insights.append(FinancialInsight(
                owner_id=profile.owner_id,
                category="opportunity",
                title=f"Outstanding receivables: {total_unpaid:.2f}",
                description=f"{len(unpaid)} unpaid invoice(s) — potential immediate cash inflow",
                impact=Money(amount=total_unpaid, currency=currency),
                confidence=0.8,
                actionable=True,
                action_suggestion="Send payment reminders and follow up on outstanding invoices",
            ))

        return insights

    # ── Financial Health Assessment ─────────────────────────────────────

    def assess_financial_health(self, profile: FinancialProfile) -> dict[str, Any]:
        """Compute a composite financial health score.

        Evaluates:
        - Liquidity: cash vs monthly expenses
        - Solvency: assets vs liabilities
        - Efficiency: savings rate
        - Stability: income consistency
        - Growth: balance trend
        """
        currency = self._primary_currency(profile)

        # Liquidity score (0-100)
        cash_balance = Money(currency=currency)
        for acct in profile.accounts:
            if acct.account_type in (
                AccountType.CHECKING.value, AccountType.SAVINGS.value,
                AccountType.CASH.value, AccountType.WALLET.value,
            ):
                if acct.balance.currency == currency:
                    cash_balance += acct.balance
        monthly_expense = Money(currency=currency)
        for txn in profile.transactions:
            if txn.is_outflow and txn.amount.currency == currency:
                monthly_expense += txn.amount
        months = max(1, len(profile.transactions) // 5)
        avg_monthly = monthly_expense / months
        liquidity = min(100, (cash_balance.amount / max(avg_monthly.amount, 1)) * 10) if avg_monthly.amount > 0 else 50

        # Solvency score (0-100)
        assets = profile.total_assets.amount
        liabilities = abs(profile.total_liabilities.amount)
        solvency = 100 if liabilities == 0 else min(100, (assets / max(liabilities, 1)) * 50)

        # Efficiency score (0-100)
        total_income = sum(t.amount.amount for t in profile.transactions if t.is_inflow)
        total_expenses = sum(t.amount.amount for t in profile.transactions if t.is_outflow)
        savings_rate = ((total_income - total_expenses) / max(total_income, 1)) * 100
        efficiency = max(0, min(100, savings_rate * 2 + 50))

        # Stability score (0-100)
        income_months = {}
        for txn in profile.transactions:
            if txn.is_inflow:
                month = txn.occurred_at[:7] if len(txn.occurred_at) >= 7 else ""
                if month:
                    income_months[month] = income_months.get(month, 0) + txn.amount.amount
        stability = 50
        if len(income_months) >= 3:
            incomes = list(income_months.values())
            avg_income = sum(incomes) / len(incomes)
            variance = sum((i - avg_income) ** 2 for i in incomes) / len(incomes)
            stability = max(0, min(100, 100 - (variance / max(avg_income, 1)) * 10))

        # Growth
        balance_trend = 0
        if len(profile.transactions) >= 2:
            sorted_txns = sorted(profile.transactions, key=lambda t: t.occurred_at)
            recent = sorted_txns[-min(10, len(sorted_txns)):]
            net = sum(t.amount.amount for t in recent if t.is_inflow) - sum(t.amount.amount for t in recent if t.is_outflow)
            balance_trend = max(0, min(100, 50 + (net / max(abs(net), 1)) * 10))

        overall = (liquidity * 0.25 + solvency * 0.20 + efficiency * 0.20 + stability * 0.20 + balance_trend * 0.15)

        return {
            "overall_score": round(overall, 1),
            "dimensions": {
                "liquidity": round(liquidity, 1),
                "solvency": round(solvency, 1),
                "efficiency": round(efficiency, 1),
                "stability": round(stability, 1),
                "growth": round(balance_trend, 1),
            },
            "metrics": {
                "total_assets": profile.total_assets.to_dict(),
                "total_liabilities": profile.total_liabilities.to_dict(),
                "net_worth": profile.net_worth.to_dict(),
                "savings_rate_pct": round(savings_rate, 1),
                "monthly_expense": avg_monthly.to_dict(),
                "cash_runway_months": round(cash_balance.amount / max(avg_monthly.amount, 1), 1) if avg_monthly.amount > 0 else 0,
            },
            "assessment": "healthy" if overall >= 70 else "fair" if overall >= 40 else "at_risk",
        }

    # ── Goal Tracking ───────────────────────────────────────────────────

    def analyze_goal(self, goal: FinancialGoal) -> dict[str, Any]:
        """Analyze progress toward a financial goal."""
        progress = goal.progress_pct
        remaining = goal.remaining_amount

        # Estimate time to completion
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        try:
            target_dt = datetime.fromisoformat(goal.target_date.replace("Z", "+00:00"))
            days_remaining = (target_dt - now).days
        except (ValueError, AttributeError):
            days_remaining = 365

        # Daily saving rate needed
        daily_save_needed = remaining.amount / max(days_remaining, 1)

        # Status determination
        if progress >= 100:
            status = "achieved"
        elif days_remaining <= 0:
            status = "behind"
        elif progress >= 75:
            status = "on_track"
        elif progress >= 50:
            status = "on_track" if days_remaining > 90 else "at_risk"
        elif progress >= 25:
            status = "at_risk" if days_remaining < 60 else "on_track"
        else:
            status = "active"

        return {
            "goal_id": goal.goal_id,
            "name": goal.name,
            "progress_pct": round(progress, 1),
            "remaining_amount": remaining.to_dict(),
            "days_remaining": max(0, days_remaining),
            "daily_saving_needed": round(daily_save_needed, 2),
            "status": status,
            "is_on_track": status in ("on_track", "achieved"),
        }

    # ── AI Context ──────────────────────────────────────────────────────

    def prepare_ai_context(self, profile: FinancialProfile) -> dict[str, Any]:
        """Prepare structured context for AI understanding providers."""
        health = self.assess_financial_health(profile)
        cash_flow = self.compute_cash_flow(profile)
        risks = self.detect_risks(profile)
        spending = self.analyze_spending(profile)
        opportunities = self.detect_revenue_opportunities(profile)

        return {
            "financial_summary": {
                "owner_id": profile.owner_id,
                "label": profile.label or f"Financial profile for {profile.owner_id}",
            },
            "health": health,
            "cash_flow": {
                "total_inflow": cash_flow.total_inflow.to_dict(),
                "total_outflow": cash_flow.total_outflow.to_dict(),
                "net_flow": cash_flow.net_flow.to_dict(),
                "burn_rate": cash_flow.burn_rate.to_dict(),
                "runway_months": cash_flow.runway_months,
            },
            "accounts": {
                "total": len(profile.accounts),
                "total_balance": profile.total_balance.to_dict(),
                "total_assets": profile.total_assets.to_dict(),
                "total_liabilities": profile.total_liabilities.to_dict(),
                "net_worth": profile.net_worth.to_dict(),
            },
            "risks": [r.to_dict() for r in risks],
            "insights": [i.to_dict() for i in spending + opportunities],
            "goals": [
                self.analyze_goal(g) for g in profile.goals
            ],
            "transactions_count": len(profile.transactions),
            "invoices": {
                "total": len(profile.invoices),
                "paid": sum(1 for i in profile.invoices if i.is_paid),
                "overdue": sum(1 for i in profile.invoices if i.is_overdue),
                "pending": sum(1 for i in profile.invoices if not i.is_paid),
            },
        }

    def _primary_currency(self, profile: FinancialProfile) -> str:
        currencies = {a.balance.currency for a in profile.accounts if a.balance.amount != 0}
        return next(iter(currencies)) if currencies else "INR"


# ─────────────────────────────────────────────────────────────────────────────
# UCP-03A — Financial Reasoning
# ─────────────────────────────────────────────────────────────────────────────

    # ── Affordability Analysis ──────────────────────────────────────────

    def analyze_affordability(
        self,
        profile: FinancialProfile,
        item_name: str,
        item_cost: Money,
    ) -> AffordabilityAnalysis:
        """Determine whether an expenditure is affordable given current finances."""
        currency = item_cost.currency

        # Available liquid funds
        available = Money(currency=currency)
        for acct in profile.accounts:
            if acct.account_type in (
                AccountType.CHECKING.value, AccountType.SAVINGS.value,
                AccountType.CASH.value, AccountType.WALLET.value,
            ):
                if acct.balance.currency == currency and acct.balance.amount > 0:
                    available += acct.balance

        # Monthly cash flow
        cf = self.compute_cash_flow(profile)
        net_monthly = cf.net_flow.amount

        # Savings rate
        total_income = sum(t.amount.amount for t in profile.transactions
                           if t.is_inflow and t.amount.currency == currency)
        total_spend = sum(t.amount.amount for t in profile.transactions
                          if t.is_outflow and t.amount.currency == currency)
        savings_rate = ((total_income - total_spend) / max(total_income, 1)) * 100 if total_income > 0 else 0

        # Affordability scoring: 0-100
        # 40%: enough liquid cash without going below 3 months of runway
        runway_protection = 0.0
        post_runway = 0.0
        cf_outflow = abs(cf.total_outflow.amount)
        monthly_expense = cf_outflow / max(1, len(profile.transactions) // 5) if profile.transactions else 0
        post_purchase_cash = available.amount - item_cost.amount
        if monthly_expense > 0:
            post_runway = post_purchase_cash / monthly_expense
            runway_protection = min(1.0, max(0.0, post_runway / 3.0))

        # 30%: impact on monthly savings
        savings_impact = min(1.0, max(0.0, 1.0 - (item_cost.amount / max(net_monthly, 1))))

        # 30%: one-time vs recurring capacity
        one_time_capacity = min(1.0, max(0.0, available.amount / max(item_cost.amount, 1)))

        score = runway_protection * 40 + savings_impact * 30 + one_time_capacity * 30
        is_affordable = score >= 50

        # Months to recover (from net savings)
        months_to_recover = 0.0
        if net_monthly > 0:
            months_to_recover = item_cost.amount / net_monthly

        evidence = [
            {"type": "available_funds", "value": available.to_dict(),
             "detail": f"Liquid cash available across checking/savings/cash/wallet"},
            {"type": "monthly_net_flow", "value": round(net_monthly, 2),
             "detail": f"Monthly net cash flow"},
            {"type": "savings_rate", "value": round(savings_rate, 1),
             "detail": f"Current savings rate {savings_rate:.1f}%"},
            {"type": "post_purchase_runway", "value": round(post_runway, 1) if monthly_expense > 0 else 0,
             "detail": f"Months of runway after purchase"},
        ]

        recommendation = (
            f"Affordable — {item_name} at {item_cost.amount:.2f} can be absorbed "
            f"with {months_to_recover:.1f} months to recover"
            if is_affordable else
            f"Not currently affordable — {item_name} at {item_cost.amount:.2f} "
            f"exceeds comfortable capacity given available funds and cash flow"
        )

        return AffordabilityAnalysis(
            item_name=item_name,
            item_cost=item_cost,
            is_affordable=is_affordable,
            affordability_score=round(score, 1),
            available_funds=available,
            impact_on_cash_flow=Money(amount=item_cost.amount, currency=currency),
            impact_on_savings_rate=round(savings_impact * 100, 1),
            months_to_recover=round(months_to_recover, 1),
            evidence=evidence,
            recommendation=recommendation,
            confidence=round(0.6 + min(0.3, len(profile.transactions) / 200), 2),
        )

    # ── Opportunity Cost ────────────────────────────────────────────────

    def compute_opportunity_cost(
        self,
        profile: FinancialProfile,
        investment_a: Money,
        investment_b: Money,
        time_horizon_months: int = 12,
        annual_return_a_pct: float = 4.0,
        annual_return_b_pct: float = 8.0,
    ) -> dict[str, Any]:
        """Compute the opportunity cost of choosing one investment over another."""
        currency = investment_a.currency

        # Future value: FV = PV * (1 + r)^t
        future_a = investment_a.amount * (1 + annual_return_a_pct / 100 / 12) ** time_horizon_months
        future_b = investment_b.amount * (1 + annual_return_b_pct / 100 / 12) ** time_horizon_months

        opportunity_cost = future_b - future_a

        return {
            "investment_a": investment_a.to_dict(),
            "investment_b": investment_b.to_dict(),
            "return_a_pct": annual_return_a_pct,
            "return_b_pct": annual_return_b_pct,
            "time_horizon_months": time_horizon_months,
            "future_value_a": round(future_a, 2),
            "future_value_b": round(future_b, 2),
            "opportunity_cost": round(opportunity_cost, 2),
            "currency": currency,
            "recommendation": (
                f"Choose investment B — it yields {future_b - future_a:.2f} more "
                f"over {time_horizon_months} months"
                if opportunity_cost > 0 else
                f"Choose investment A — it is more favorable over {time_horizon_months} months"
            ),
            "evidence": [
                {"type": "future_value_a", "value": round(future_a, 2),
                 "detail": f"Future value of A at {annual_return_a_pct}%"},
                {"type": "future_value_b", "value": round(future_b, 2),
                 "detail": f"Future value of B at {annual_return_b_pct}%"},
            ],
        }

    # ── Scenario Simulation ─────────────────────────────────────────────

    def simulate_scenario(
        self,
        profile: FinancialProfile,
        scenario_name: str,
        description: str,
        revenue_delta_pct: float = 0.0,
        expense_delta_pct: float = 0.0,
        horizon_months: int = 6,
        one_time_impact: float = 0.0,
    ) -> ScenarioSimulation:
        """Simulate a financial 'what if' scenario and compare to baseline."""
        currency = self._primary_currency(profile)

        # Baseline
        baseline_balance = profile.total_balance.amount
        baseline_cf = self.compute_cash_flow(profile)
        baseline_net = baseline_cf.net_flow.amount

        # Projected
        projected_balance = baseline_balance
        projected_net = baseline_net * (1 + revenue_delta_pct / 100) - \
            (baseline_net * (expense_delta_pct / 100)) if baseline_net > 0 else baseline_net
        # Apply one-time impact
        projected_balance += one_time_impact

        # Forecast over horizon
        monthly_inflow = sum(t.amount.amount for t in profile.transactions
                             if t.is_inflow and t.amount.currency == currency)
        monthly_outflow = sum(t.amount.amount for t in profile.transactions
                              if t.is_outflow and t.amount.currency == currency)
        months = max(1, len(profile.transactions) // 5)
        avg_inflow = monthly_inflow / months
        avg_outflow = monthly_outflow / months

        projected_inflow = avg_inflow * (1 + revenue_delta_pct / 100)
        projected_outflow = avg_outflow * (1 + expense_delta_pct / 100)
        projected_net_monthly = projected_inflow - projected_outflow

        end_balance = baseline_balance + projected_net_monthly * horizon_months + one_time_impact

        delta = {
            "net_flow_delta": round(projected_net - baseline_net, 2),
            "balance_delta": round(end_balance - baseline_balance, 2),
            "inflow_delta_pct": revenue_delta_pct,
            "outflow_delta_pct": expense_delta_pct,
        }

        # Runway after scenario
        end_runway = end_balance / max(avg_outflow, 1) if avg_outflow > 0 else float("inf")

        risks = []
        if end_runway < 3:
            risks.append(f"Runway drops below 3 months ({end_runway:.1f} months)")
        if end_balance < 0:
            risks.append("Projected balance becomes negative")

        recommendation = ""
        recommendation_confidence = 0.0
        if end_balance < baseline_balance * 0.8:
            recommendation = "Scenario materially reduces financial position — consider mitigation"
            recommendation_confidence = 0.8
        elif end_balance > baseline_balance * 1.1:
            recommendation = "Scenario improves financial position — favorable to pursue"
            recommendation_confidence = 0.8
        else:
            recommendation = "Scenario has modest impact — acceptable within current risk tolerance"
            recommendation_confidence = 0.6

        evidence = [
            {"type": "baseline_balance", "value": round(baseline_balance, 2)},
            {"type": "projected_net_monthly", "value": round(projected_net_monthly, 2)},
            {"type": "end_balance", "value": round(end_balance, 2)},
            {"type": "end_runway_months", "value": round(end_runway, 1)},
        ]

        return ScenarioSimulation(
            scenario_name=scenario_name,
            description=description,
            baseline={
                "balance": round(baseline_balance, 2),
                "net_flow": round(baseline_net, 2),
                "runway_months": round(baseline_cf.runway_months, 1) if baseline_cf.burn_rate.amount > 0 else 0,
            },
            projected={
                "balance": round(end_balance, 2),
                "net_flow": round(projected_net, 2),
                "runway_months": round(end_runway, 1),
            },
            delta=delta,
            confidence=round(0.5 + min(0.4, len(profile.transactions) / 150), 2),
            assumptions=[
                f"Revenue change: {revenue_delta_pct:+.0f}%",
                f"Expense change: {expense_delta_pct:+.0f}%",
                f"Horizon: {horizon_months} months",
                f"One-time impact: {one_time_impact:+.2f}",
            ],
            risks=risks,
            evidence=evidence,
            recommendation=recommendation,
            recommendation_confidence=recommendation_confidence,
        )

    # ── Revenue & Expense Forecasting (component) ───────────────────────

    def forecast_revenue(self, profile: FinancialProfile, horizon_months: int = 6) -> dict[str, Any]:
        """Forecast revenue based on historical income patterns."""
        currency = self._primary_currency(profile)
        income_by_month: dict[str, float] = {}
        for txn in profile.transactions:
            if txn.is_inflow and txn.amount.currency == currency:
                month = txn.occurred_at[:7] if len(txn.occurred_at) >= 7 else ""
                if month:
                    income_by_month[month] = income_by_month.get(month, 0) + txn.amount.amount

        if not income_by_month:
            return {"error": "No income history", "currency": currency}

        months_data = sorted(income_by_month.items())
        recent = months_data[-min(6, len(months_data)):]
        values = [v for _, v in recent]

        # Simple trend: average growth between consecutive months
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                growth_rates.append((values[i] - values[i-1]) / values[i-1])
        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0

        last_value = values[-1]
        projections = []
        for month in range(1, horizon_months + 1):
            projected = last_value * (1 + avg_growth) ** month
            projections.append({
                "month": month,
                "projected_revenue": round(projected, 2),
            })

        return {
            "currency": currency,
            "historical_months": len(income_by_month),
            "avg_growth_pct": round(avg_growth * 100, 1),
            "last_month_revenue": round(last_value, 2),
            "projections": projections,
            "confidence": round(min(0.9, 0.5 + len(income_by_month) * 0.05), 2),
            "assumptions": [f"Average monthly growth: {avg_growth*100:.1f}%"],
        }

    def forecast_expenses(self, profile: FinancialProfile, horizon_months: int = 6) -> dict[str, Any]:
        """Forecast expenses based on historical spending patterns."""
        currency = self._primary_currency(profile)
        expense_by_month: dict[str, float] = {}
        for txn in profile.transactions:
            if txn.is_outflow and txn.amount.currency == currency:
                month = txn.occurred_at[:7] if len(txn.occurred_at) >= 7 else ""
                if month:
                    expense_by_month[month] = expense_by_month.get(month, 0) + txn.amount.amount

        if not expense_by_month:
            return {"error": "No expense history", "currency": currency}

        months_data = sorted(expense_by_month.items())
        recent = months_data[-min(6, len(months_data)):]
        values = [v for _, v in recent]
        avg_monthly = sum(values) / len(values)

        projections = []
        for month in range(1, horizon_months + 1):
            # Assume slight inflation (0.5% month over month)
            projected = avg_monthly * (1.005 ** month)
            projections.append({
                "month": month,
                "projected_expense": round(projected, 2),
            })

        return {
            "currency": currency,
            "avg_monthly_expense": round(avg_monthly, 2),
            "projections": projections,
            "confidence": round(min(0.85, 0.5 + len(expense_by_month) * 0.05), 2),
            "assumptions": ["Average monthly expense maintained", "0.5% monthly inflation assumed"],
        }

    # ── Runway Analysis ─────────────────────────────────────────────────

    def analyze_runway(self, profile: FinancialProfile) -> dict[str, Any]:
        """Analyze cash runway and how expenses affect it."""
        currency = self._primary_currency(profile)
        cash_balance = Money(currency=currency)
        for acct in profile.accounts:
            if acct.account_type in (
                AccountType.CHECKING.value, AccountType.SAVINGS.value,
                AccountType.CASH.value, AccountType.WALLET.value,
            ):
                if acct.balance.currency == currency and acct.balance.amount > 0:
                    cash_balance += acct.balance

        monthly_outflow = Money(currency=currency)
        for txn in profile.transactions:
            if txn.is_outflow and txn.amount.currency == currency:
                monthly_outflow += txn.amount
        months = max(1, len(profile.transactions) // 5)
        avg_monthly = monthly_outflow / months

        runway_months = cash_balance.amount / avg_monthly.amount if avg_monthly.amount > 0 else float("inf")

        # Sensitivity: how runway changes with expense reduction
        sensitivities = []
        for reduction in [5, 10, 20, 30]:
            reduced_expense = avg_monthly.amount * (1 - reduction / 100)
            new_runway = cash_balance.amount / reduced_expense if reduced_expense > 0 else float("inf")
            sensitivities.append({
                "expense_reduction_pct": reduction,
                "new_runway_months": round(new_runway, 1),
                "runway_extension": round(new_runway - runway_months, 1),
            })

        return {
            "cash_balance": cash_balance.to_dict(),
            "avg_monthly_expense": avg_monthly.to_dict(),
            "runway_months": round(runway_months, 1),
            "sensitivity": sensitivities,
            "recommendation": (
                f"Runway is {runway_months:.1f} months — {'critical, reduce expenses' if runway_months < 3 else 'adequate'}"
            ),
            "evidence": [
                {"type": "cash_balance", "value": cash_balance.amount},
                {"type": "avg_monthly_expense", "value": avg_monthly.amount},
                {"type": "runway_months", "value": round(runway_months, 1)},
            ],
        }

    # ── Hiring Impact ───────────────────────────────────────────────────

    def analyze_hiring_impact(
        self,
        profile: FinancialProfile,
        role_name: str,
        annual_salary: Money,
        benefits_pct: float = 20.0,
    ) -> HiringImpact:
        """Analyze financial impact of hiring a new role."""
        currency = annual_salary.currency
        total_cost = annual_salary * (1 + benefits_pct / 100)

        # Existing payroll estimate from salary expenses
        existing_payroll = Money(currency=currency)
        for txn in profile.transactions:
            if txn.category == "salaries" and txn.is_outflow and txn.amount.currency == currency:
                existing_payroll += txn.amount
        months = max(1, len(profile.transactions) // 5)
        avg_months_data = max(1, len([t for t in profile.transactions
                                      if t.category == "salaries" and t.is_outflow]) // 12)
        existing_payroll_annual = existing_payroll / max(1, avg_months_data) * 12 if existing_payroll.amount > 0 else Money(amount=0, currency=currency)

        payroll_increase_pct = (total_cost.amount / max(existing_payroll_annual.amount, 1)) * 100

        # Revenue per employee
        total_revenue = sum(t.amount.amount for t in profile.transactions
                            if t.is_inflow and t.amount.currency == currency)
        estimated_employees = 1 + (existing_payroll_annual.amount / max(800000, 1))
        revenue_per_employee = total_revenue / max(estimated_employees, 1)

        # Break-even revenue
        break_even_revenue = Money(amount=total_cost.amount, currency=currency)

        # Impact on runway
        runway = self.analyze_runway(profile)
        monthly_cost = total_cost.amount / 12
        avg_monthly_expense = runway["avg_monthly_expense"]["amount"]
        new_monthly = avg_monthly_expense + monthly_cost
        cash = runway["cash_balance"]["amount"]
        new_runway = cash / new_monthly if new_monthly > 0 else float("inf")
        impact_on_runway = new_runway - runway["runway_months"]

        evidence = [
            {"type": "total_cost", "value": total_cost.amount,
             "detail": f"Annual salary + {benefits_pct}% benefits"},
            {"type": "existing_payroll", "value": existing_payroll_annual.amount,
             "detail": "Annualized existing payroll"},
            {"type": "revenue_per_employee", "value": round(revenue_per_employee, 2)},
            {"type": "runway_impact", "value": round(impact_on_runway, 1),
             "detail": f"Runway change: {impact_on_runway:+.1f} months"},
        ]

        recommendation = (
            f"Feasible to hire {role_name} — cost {total_cost.amount:.0f}/yr is "
            f"{payroll_increase_pct:.0f}% of payroll, runway impact {impact_on_runway:+.1f} months"
            if impact_on_runway > -3 and payroll_increase_pct < 50 else
            f"Hiring {role_name} is risky — {payroll_increase_pct:.0f}% payroll increase "
            f"reduces runway by {abs(impact_on_runway):.1f} months"
        )

        return HiringImpact(
            role_name=role_name,
            annual_salary=annual_salary,
            total_cost=total_cost,
            existing_payroll=existing_payroll_annual,
            payroll_increase_pct=round(payroll_increase_pct, 1),
            revenue_per_employee=Money(amount=round(revenue_per_employee, 2), currency=currency),
            break_even_revenue=break_even_revenue,
            break_even_months=round(break_even_revenue.amount / max(revenue_per_employee, 1), 1),
            impact_on_runway=round(impact_on_runway, 1),
            evidence=evidence,
            recommendation=recommendation,
            confidence=round(0.6 + min(0.3, len(profile.transactions) / 200), 2),
        )

    # ── Investment Analysis ─────────────────────────────────────────────

    def analyze_investment(
        self,
        profile: FinancialProfile,
        principal: Money,
        annual_return_pct: float,
        time_horizon_months: int = 36,
        monthly_contribution: Money | None = None,
    ) -> dict[str, Any]:
        """Analyze an investment opportunity."""
        currency = principal.currency
        monthly = monthly_contribution or Money(amount=0, currency=currency)
        r = annual_return_pct / 100 / 12

        # Future value with monthly contributions
        future_value = principal.amount * (1 + r) ** time_horizon_months
        if monthly.amount > 0:
            # FV of annuity
            future_value += monthly.amount * (((1 + r) ** time_horizon_months - 1) / max(r, 0.0001))

        total_contributions = principal.amount + monthly.amount * time_horizon_months
        total_gain = future_value - total_contributions
        effective_annual_return = ((future_value / total_contributions) ** (12 / time_horizon_months) - 1) * 100 if total_contributions > 0 and time_horizon_months > 0 else 0

        # Risk assessment
        risk_level = "low" if annual_return_pct <= 6 else "medium" if annual_return_pct <= 10 else "high"

        return {
            "principal": principal.to_dict(),
            "annual_return_pct": annual_return_pct,
            "time_horizon_months": time_horizon_months,
            "monthly_contribution": monthly.to_dict(),
            "future_value": round(future_value, 2),
            "total_contributions": round(total_contributions, 2),
            "total_gain": round(total_gain, 2),
            "effective_annual_return_pct": round(effective_annual_return, 2),
            "risk_level": risk_level,
            "recommendation": (
                f"Investment projected to grow {total_contributions:.0f} to {future_value:.0f} "
                f"({total_gain:+.0f} gain) over {time_horizon_months} months"
            ),
            "evidence": [
                {"type": "future_value", "value": round(future_value, 2)},
                {"type": "total_gain", "value": round(total_gain, 2)},
                {"type": "effective_return", "value": round(effective_annual_return, 2)},
            ],
        }

    # ── Financial Trade-offs ────────────────────────────────────────────

    def analyze_tradeoffs(
        self,
        profile: FinancialProfile,
        option_a_name: str,
        option_a_cost: Money,
        option_a_benefit: str,
        option_b_name: str,
        option_b_cost: Money,
        option_b_benefit: str,
    ) -> FinancialTradeOff:
        """Analyze the trade-off between two financial options."""
        currency = option_a_cost.currency
        cost_delta = option_a_cost.amount - option_b_cost.amount

        # Opportunity cost of choosing higher-cost option
        higher = option_a_cost if option_a_cost.amount > option_b_cost.amount else option_b_cost
        lower = option_b_cost if option_a_cost.amount > option_b_cost.amount else option_a_cost
        opportunity_cost = higher - lower

        # Recommendation based on cost and benefit
        if option_a_cost.amount < option_b_cost.amount and "increase" in option_b_benefit.lower():
            recommended = option_a_name
            rationale = f"Lower cost ({option_a_cost.amount:.0f}) with comparable benefit"
        elif option_b_cost.amount < option_a_cost.amount and "increase" in option_a_benefit.lower():
            recommended = option_b_name
            rationale = f"Lower cost ({option_b_cost.amount:.0f}) with comparable benefit"
        else:
            # Default to lower cost option with risk caveat
            recommended = option_a_name if option_a_cost.amount <= option_b_cost.amount else option_b_name
            rationale = f"Lower immediate cost ({min(option_a_cost.amount, option_b_cost.amount):.0f})"

        evidence = [
            {"type": "option_a", "name": option_a_name, "cost": option_a_cost.amount,
             "benefit": option_a_benefit},
            {"type": "option_b", "name": option_b_name, "cost": option_b_cost.amount,
             "benefit": option_b_benefit},
            {"type": "cost_delta", "value": round(cost_delta, 2)},
            {"type": "opportunity_cost", "value": opportunity_cost.amount},
        ]

        return FinancialTradeOff(
            title=f"Trade-off: {option_a_name} vs {option_b_name}",
            description=f"Comparing {option_a_name} ({option_a_cost.amount:.0f}) against {option_b_name} ({option_b_cost.amount:.0f})",
            alternative_a={"name": option_a_name, "cost": option_a_cost.to_dict(), "benefit": option_a_benefit},
            alternative_b={"name": option_b_name, "cost": option_b_cost.to_dict(), "benefit": option_b_benefit},
            opportunity_cost=opportunity_cost,
            recommended_alternative=recommended,
            rationale=rationale,
            evidence=evidence,
            confidence=0.7,
        )

    # ── Customer Payment Risk ───────────────────────────────────────────

    def assess_customer_payment_risk(
        self,
        profile: FinancialProfile,
        customer_id: str,
        customer_name: str = "",
    ) -> CustomerPaymentRisk:
        """Assess the payment risk of a customer based on their invoices."""
        currency = self._primary_currency(profile)

        customer_invoices = [inv for inv in profile.invoices if inv.recipient_id == customer_id]
        total_outstanding = Money(currency=currency)
        overdue_amount = Money(currency=currency)
        overdue_count = 0
        total_count = len(customer_invoices)

        payment_delays: list[int] = []
        for inv in customer_invoices:
            if not inv.is_paid:
                total_outstanding += inv.amount_due
                if inv.is_overdue:
                    overdue_amount += inv.amount_due
                    overdue_count += 1
            elif inv.paid_date and inv.due_date:
                try:
                    from datetime import datetime
                    due = datetime.fromisoformat(inv.due_date.replace("Z", "+00:00"))
                    paid = datetime.fromisoformat(inv.paid_date.replace("Z", "+00:00"))
                    payment_delays.append((paid - due).days)
                except (ValueError, TypeError):
                    pass

        avg_delay = sum(payment_delays) / len(payment_delays) if payment_delays else 0.0

        # Risk scoring
        risk_score = 0.0
        if total_count > 0:
            overdue_ratio = overdue_count / total_count
            risk_score += overdue_ratio * 50
        if overdue_amount.amount > 0 and total_outstanding.amount > 0:
            risk_score += (overdue_amount.amount / total_outstanding.amount) * 30
        risk_score += min(20, max(0, avg_delay)) * 1.0
        risk_score = min(100, risk_score)

        risk_level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"

        evidence = [
            {"type": "total_outstanding", "value": total_outstanding.amount},
            {"type": "overdue_amount", "value": overdue_amount.amount},
            {"type": "overdue_ratio", "value": round(overdue_count / total_count, 2) if total_count else 0},
            {"type": "avg_payment_delay_days", "value": round(avg_delay, 1)},
        ]

        recommendation = (
            f"Customer {customer_name or customer_id} has {risk_level} payment risk — "
            f"{overdue_count}/{total_count} invoices overdue, {overdue_amount.amount:.0f} outstanding"
            if risk_level != "low" else
            f"Customer {customer_name or customer_id} has reliable payment history"
        )

        return CustomerPaymentRisk(
            customer_id=customer_id,
            customer_name=customer_name,
            risk_score=round(risk_score, 1),
            risk_level=risk_level,
            total_outstanding=total_outstanding,
            overdue_amount=overdue_amount,
            payment_history={"total_invoices": total_count, "paid": total_count - overdue_count, "overdue": overdue_count},
            avg_payment_delay_days=round(avg_delay, 1),
            evidence=evidence,
            recommendation=recommendation,
            confidence=round(0.6 + min(0.3, total_count * 0.05), 2),
        )

    # ── Supplier Payment Optimization ───────────────────────────────────

    def optimize_supplier_payments(
        self,
        profile: FinancialProfile,
        supplier_id: str,
        supplier_name: str = "",
        total_payable: Money | None = None,
        current_terms_days: int = 30,
    ) -> SupplierPaymentOptimization:
        """Optimize supplier payment terms to preserve cash flow."""
        currency = self._primary_currency(profile)
        payable = total_payable or Money(amount=0, currency=currency)

        # Determine recommended terms based on cash position
        runway = self.analyze_runway(profile)
        runway_months = runway["runway_months"]

        if runway_months < 3:
            recommended_days = min(90, current_terms_days + 30)
            risk = "high — runway under 3 months, extending terms essential"
            confidence = 0.8
        elif runway_months < 6:
            recommended_days = min(60, current_terms_days + 15)
            risk = "moderate — extend terms to protect cash buffer"
            confidence = 0.7
        else:
            recommended_days = current_terms_days
            risk = "low — healthy runway, maintain current terms"
            confidence = 0.6

        # Cash flow impact of extending terms
        extra_days = max(0, recommended_days - current_terms_days)
        daily_exposure = payable.amount / max(current_terms_days, 1)
        cash_flow_impact = daily_exposure * extra_days

        evidence = [
            {"type": "runway_months", "value": runway_months, "detail": "Current cash runway"},
            {"type": "total_payable", "value": payable.amount},
            {"type": "cash_flow_impact", "value": round(cash_flow_impact, 2),
             "detail": f"Cash retained by extending terms {extra_days} days"},
        ]

        return SupplierPaymentOptimization(
            supplier_id=supplier_id,
            supplier_name=supplier_name or supplier_id,
            total_payable=payable,
            current_terms_days=current_terms_days,
            recommended_terms_days=recommended_days,
            cash_flow_impact=Money(amount=round(cash_flow_impact, 2), currency=currency),
            risk_of_extension=risk,
            evidence=evidence,
            recommendation=(
                f"Extend {supplier_name} payment terms from {current_terms_days} to "
                f"{recommended_days} days, retaining {cash_flow_impact:.0f} in cash"
                if extra_days > 0 else
                f"Maintain {supplier_name} payment terms at {current_terms_days} days"
            ),
            confidence=confidence,
        )

    # ── Commitment Conflict Detection ───────────────────────────────────

    def detect_commitment_conflicts(self, profile: FinancialProfile) -> list[CommitmentConflict]:
        """Detect conflicts between financial commitments (goals, invoices, budgets)."""
        conflicts: list[CommitmentConflict] = []
        currency = self._primary_currency(profile)

        available = Money(currency=currency)
        for acct in profile.accounts:
            if acct.account_type in (
                AccountType.CHECKING.value, AccountType.SAVINGS.value,
                AccountType.CASH.value, AccountType.WALLET.value,
            ):
                if acct.balance.currency == currency and acct.balance.amount > 0:
                    available += acct.balance

        # 1. Active goals vs available funds
        active_goals = profile.active_goals
        if active_goals:
            total_goal_targets = sum(g.remaining_amount.amount for g in active_goals)
            if total_goal_targets > available.amount:
                conflicts.append(CommitmentConflict(
                    title="Active goals exceed available funds",
                    description=f"{len(active_goals)} active goals require {total_goal_targets:.0f} but only {available.amount:.0f} available",
                    commitments=[{"type": "goal", "name": g.name, "remaining": g.remaining_amount.amount} for g in active_goals],
                    conflict_type="goal_funding",
                    impact=f"Shortfall of {total_goal_targets - available.amount:.0f}",
                    severity="high" if (total_goal_targets - available.amount) > available.amount * 0.5 else "medium",
                    resolution="Prioritize goals, extend timelines, or reduce targets",
                    evidence=[{"type": "available_funds", "value": available.amount},
                              {"type": "goal_requirements", "value": total_goal_targets}],
                ))

        # 2. Overdue invoices + active expenses
        overdue_invoices = [inv for inv in profile.invoices if inv.is_overdue]
        if overdue_invoices:
            overdue_total = sum(inv.amount_due.amount for inv in overdue_invoices)
            if overdue_total > available.amount * 0.5:
                conflicts.append(CommitmentConflict(
                    title="Overdue invoices strain liquidity",
                    description=f"{len(overdue_invoices)} overdue invoices totaling {overdue_total:.0f}",
                    commitments=[{"type": "invoice", "number": i.invoice_number, "due": i.amount_due.amount} for i in overdue_invoices],
                    conflict_type="liquidity_pressure",
                    impact=f"Overdue {overdue_total:.0f} against {available.amount:.0f} available",
                    severity="high",
                    resolution="Prioritize collections, negotiate payment plans",
                    evidence=[{"type": "overdue_total", "value": overdue_total},
                              {"type": "available_funds", "value": available.amount}],
                ))

        # 3. Budget overruns conflicting with savings goals
        for budget in profile.budgets:
            if budget.is_over_budget:
                overshoot = budget.total_spent.amount - budget.total_planned.amount
                conflicts.append(CommitmentConflict(
                    title=f"Budget '{budget.name}' overrun conflicts with goals",
                    description=f"Budget overspent by {overshoot:.0f}",
                    commitments=[{"type": "budget", "name": budget.name, "overshoot": round(overshoot, 2)}],
                    conflict_type="budget_overrun",
                    impact=f"{overshoot:.0f} diverted from savings goals",
                    severity="medium",
                    resolution="Rebalance budget, reduce overspent categories",
                    evidence=[{"type": "budget_overshoot", "value": round(overshoot, 2)},
                              {"type": "utilization_pct", "value": budget.utilization_pct}],
                ))

        return conflicts

    # ── Financial Decision Support ──────────────────────────────────────

    def decision_support(
        self,
        profile: FinancialProfile,
        title: str,
        context: str,
        options: list[dict[str, Any]],
    ) -> DecisionSupport:
        """Provide structured decision support with evidence-backed recommendations.

        Each option: {name, upfront_cost, recurring_cost, benefit, risk}
        """
        currency = self._primary_currency(profile)
        alternatives = []
        analysis_options = []

        for opt in options:
            upfront = opt.get("upfront_cost", 0)
            recurring = opt.get("recurring_cost", 0)
            benefit = opt.get("benefit", 0)
            risk = opt.get("risk", "medium")

            # Total cost over 12 months
            total_cost = upfront + recurring * 12

            # Net benefit
            net_benefit = benefit - total_cost

            alternatives.append({
                "name": opt.get("name", "Option"),
                "upfront_cost": upfront,
                "recurring_cost": recurring,
                "benefit": benefit,
                "risk": risk,
                "total_cost_12m": round(total_cost, 2),
                "net_benefit_12m": round(net_benefit, 2),
                "roi_pct": round((net_benefit / max(total_cost, 1)) * 100, 1),
            })

        # Rank options by net benefit / ROI
        ranked = sorted(alternatives, key=lambda x: x["net_benefit_12m"], reverse=True)
        recommendation = ranked[0]["name"] if ranked else "none"
        best = ranked[0] if ranked else {}

        evidence = [
            {"type": "ranked_options", "value": [a["name"] for a in ranked]},
            {"type": "best_net_benefit", "value": best.get("net_benefit_12m", 0)},
            {"type": "best_roi", "value": best.get("roi_pct", 0)},
        ]

        risks = [opt.get("risk", "medium") for opt in options]

        return DecisionSupport(
            title=title,
            context=context,
            alternatives=alternatives,
            analysis={
                "best_option": recommendation,
                "best_net_benefit_12m": best.get("net_benefit_12m", 0),
                "best_roi_pct": best.get("roi_pct", 0),
                "option_count": len(options),
            },
            recommendation=f"Choose '{recommendation}' — highest net benefit ({best.get('net_benefit_12m', 0):.0f}) "
                          f"with {best.get('roi_pct', 0):.0f}% ROI over 12 months",
            recommendation_confidence=0.7,
            evidence=evidence,
            risks=risks,
            next_steps=[
                f"Validate estimates for '{recommendation}'",
                "Run scenario simulation before committing",
            ],
        )

    # ── Explainable Recommendations ─────────────────────────────────────

    def explain_recommendation(self, recommendation: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        """Package a recommendation with its evidence for explainability."""
        return {
            "recommendation": recommendation,
            "evidence": evidence,
            "explanation": "Recommendation is based on the following evidence-backed analysis:",
            "evidence_summary": [
                {"basis": e.get("type", ""), "value": e.get("value", ""), "detail": e.get("detail", "")}
                for e in evidence
            ],
        }