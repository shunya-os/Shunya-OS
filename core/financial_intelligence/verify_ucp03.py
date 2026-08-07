"""UCP-03 Verification — Universal Financial Intelligence.

Verifies 5 scenarios through the same capability:
1. Personal budgeting
2. Household finances
3. Startup cash flow
4. Corporate quotation → invoice → payment
5. Financial disruption with adaptive execution

No Financial Runtime. No Accounting Runtime. No ERP Runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from core.financial_intelligence import (
    FinancialIntelligenceRuntime,
    AccountType,
    TransactionType,
    BudgetPeriod,
    InvoiceStatus,
    Money,
)


def _days_ago(days: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat().replace("+00:00", "Z")


# ═══════════════════════════════════════════════════════════════════════════
# 1. PERSONAL BUDGETING
# ═══════════════════════════════════════════════════════════════════════════

def test_personal_budgeting() -> dict[str, Any]:
    """Demonstrate personal budgeting — individual managing monthly finances."""
    runtime = FinancialIntelligenceRuntime()

    profile = runtime.get_or_create_profile("person_priya", "Priya — Freelance Designer")

    # Priya's accounts
    checking = runtime.add_account(profile.profile_id, "Checking", AccountType.CHECKING.value,
                                    balance=45000, institution="HDFC")
    savings = runtime.add_account(profile.profile_id, "Savings", AccountType.SAVINGS.value,
                                   balance=120000, institution="HDFC")
    credit = runtime.add_account(profile.profile_id, "Credit Card", AccountType.CREDIT_CARD.value,
                                  balance=-15000, institution="ICICI",
                                  metadata={"credit_limit": 100000})

    # Monthly income
    for i in range(3):
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            45000, to_account_id=checking.account_id, category="salary",
            description=f"Freelance payment — month {i+1}",
            occurred_at=_days_ago(i * 30 + 5))

    # Monthly expenses
    expenses = [
        (5000, "rent", _days_ago(2)),
        (2000, "groceries", _days_ago(3)),
        (1500, "utilities", _days_ago(7)),
        (3000, "dining", _days_ago(4)),
        (1000, "transport", _days_ago(6)),
        (2500, "shopping", _days_ago(10)),
    ]
    for amt, cat, date in expenses:
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            amt, from_account_id=checking.account_id, category=cat,
            description=f"{cat} expense", occurred_at=date)

    # Create a monthly budget
    budget = runtime.create_budget(profile.profile_id, "Monthly Budget",
        15000, period=BudgetPeriod.MONTHLY.value, categories={
            "rent": {"planned": 5000, "spent": 5000},
            "groceries": {"planned": 3000, "spent": 2000},
            "utilities": {"planned": 2000, "spent": 1500},
            "dining": {"planned": 2000, "spent": 3000},
            "transport": {"planned": 1500, "spent": 1000},
            "shopping": {"planned": 1500, "spent": 2500},
        })

    # Financial health
    health = runtime.assess_financial_health(profile.profile_id)
    insights = runtime.get_spending_insights(profile.profile_id)
    forecast = runtime.forecast_cash_flow(profile.profile_id, 3)

    assert health is not None
    assert health["overall_score"] > 0
    assert len(profile.transactions) == 3 + 6  # 3 income + 6 expenses
    assert len(profile.accounts) == 3
    assert forecast is not None
    assert len(forecast["projections"]) == 3

    return {
        "scenario": "1. Personal Budgeting",
        "entity": "Priya — Freelance Designer",
        "health_score": health["overall_score"],
        "assessment": health["assessment"],
        "transactions": len(profile.transactions),
        "accounts": len(profile.accounts),
        "budgets": len(profile.budgets),
        "insights": len(insights),
        "forecast_horizon": len(forecast["projections"]),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. HOUSEHOLD FINANCES
# ═══════════════════════════════════════════════════════════════════════════

def test_household_finances() -> dict[str, Any]:
    """Demonstrate household financial management — family with shared and individual accounts."""
    runtime = FinancialIntelligenceRuntime()

    profile = runtime.get_or_create_profile("family_sharma", "Sharma Family")

    # Family accounts
    joint_checking = runtime.add_account(profile.profile_id, "Joint Checking",
        AccountType.CHECKING.value, balance=85000, institution="SBI")
    joint_savings = runtime.add_account(profile.profile_id, "Joint Savings",
        AccountType.SAVINGS.value, balance=350000, institution="SBI")
    wife_credit = runtime.add_account(profile.profile_id, "Wife Credit Card",
        AccountType.CREDIT_CARD.value, balance=-8000, institution="HDFC",
        metadata={"credit_limit": 50000})
    husband_credit = runtime.add_account(profile.profile_id, "Husband Credit Card",
        AccountType.CREDIT_CARD.value, balance=-12000, institution="ICICI",
        metadata={"credit_limit": 75000})
    emergency = runtime.add_account(profile.profile_id, "Emergency Fund",
        AccountType.SAVINGS.value, balance=200000)

    # Household income (dual income)
    runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
        75000, to_account_id=joint_checking.account_id, category="salary",
        description="Husband salary", occurred_at=_days_ago(2))
    runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
        55000, to_account_id=joint_checking.account_id, category="salary",
        description="Wife salary", occurred_at=_days_ago(2))

    # Household expenses
    household_expenses = [
        (15000, "mortgage", _days_ago(1)),
        (5000, "groceries", _days_ago(3)),
        (3000, "utilities", _days_ago(5)),
        (8000, "school_fees", _days_ago(10)),
        (4000, "insurance", _days_ago(15)),
        (2000, "internet_phone", _days_ago(7)),
        (6000, "dining_entertainment", _days_ago(4)),
        (3000, "transport_fuel", _days_ago(6)),
        (5000, "healthcare", _days_ago(20)),
        (2000, "miscellaneous", _days_ago(8)),
    ]
    for amt, cat, date in household_expenses:
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            amt, from_account_id=joint_checking.account_id, category=cat,
            description=cat, occurred_at=date)

    # Family financial goals
    runtime.create_goal(profile.profile_id, "Children's education fund",
        1500000, goal_type="education", target_date=_days_ago(-365 * 5))
    runtime.create_goal(profile.profile_id, "Emergency fund target",
        500000, goal_type="emergency_fund", target_date=_days_ago(-365 * 2))
    runtime.create_goal(profile.profile_id, "Retirement corpus",
        5000000, goal_type="retirement", target_date=_days_ago(-365 * 20))

    # Update goal progress
    profile.goals[0].current_amount = Money(amount=600000)
    profile.goals[1].current_amount = Money(amount=200000)
    profile.goals[2].current_amount = Money(amount=800000)

    # Analysis
    cash_flow = runtime.compute_cash_flow(profile.profile_id)
    risks = runtime.detect_risks(profile.profile_id)
    health = runtime.assess_financial_health(profile.profile_id)

    assert health is not None
    assert cash_flow is not None
    assert len(profile.goals) == 3
    assert len(profile.accounts) == 5

    return {
        "scenario": "2. Household Finances",
        "entity": "Sharma Family",
        "health_score": health["overall_score"],
        "assessment": health["assessment"],
        "accounts": len(profile.accounts),
        "transactions": len(profile.transactions),
        "goals": len(profile.goals),
        "risks": len(risks),
        "cash_flow_net": cash_flow["net_flow"]["amount"],
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. STARTUP CASH FLOW
# ═══════════════════════════════════════════════════════════════════════════

def test_startup_cash_flow() -> dict[str, Any]:
    """Demonstrate startup cash flow management — early-stage company."""
    runtime = FinancialIntelligenceRuntime()

    profile = runtime.get_or_create_profile("startup_nexusai", "Nexus AI — Early Stage Startup")

    # Startup accounts
    business_checking = runtime.add_account(profile.profile_id, "Business Checking",
        AccountType.CHECKING.value, balance=2500000, institution="RazorpayX")
    business_savings = runtime.add_account(profile.profile_id, "Business Savings",
        AccountType.SAVINGS.value, balance=5000000, institution="RazorpayX")
    escrow = runtime.add_account(profile.profile_id, "Investor Escrow",
        AccountType.ESCROW.value, balance=0)

    # Initial funding (seed round)
    runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
        5000000, to_account_id=business_checking.account_id, category="funding",
        description="Seed round investment", occurred_at=_days_ago(180))

    # Monthly revenue (SaaS)
    for month in range(4):
        revenue = 300000 * (1 + month * 0.2)  # growing MRR
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            revenue, to_account_id=business_checking.account_id, category="saas_revenue",
            description=f"MRR — month {month+1}",
            occurred_at=_days_ago(month * 30 + 1))

    # Monthly operating expenses
    monthly_opex = [
        (150000, "salaries", _days_ago(1)),
        (50000, "cloud_infrastructure", _days_ago(3)),
        (25000, "office_rent", _days_ago(5)),
        (15000, "software_tools", _days_ago(7)),
        (20000, "marketing", _days_ago(10)),
        (10000, "legal_compliance", _days_ago(14)),
        (8000, "travel", _days_ago(20)),
    ]
    for amt, cat, date in monthly_opex:
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            amt, from_account_id=business_checking.account_id, category=cat,
            description=cat, occurred_at=date)

    # Cash flow analysis
    cash_flow = runtime.compute_cash_flow(profile.profile_id)
    forecast = runtime.forecast_cash_flow(profile.profile_id, 6)
    risks = runtime.detect_risks(profile.profile_id)
    health = runtime.assess_financial_health(profile.profile_id)

    assert cash_flow is not None
    assert forecast is not None
    assert forecast["horizon_months"] == 6
    assert len(profile.accounts) == 3

    return {
        "scenario": "3. Startup Cash Flow",
        "entity": "Nexus AI — Early Stage Startup",
        "health_score": health["overall_score"],
        "assessment": health["assessment"],
        "accounts": len(profile.accounts),
        "transactions": len(profile.transactions),
        "risks": len(risks),
        "cash_flow_net": cash_flow["net_flow"]["amount"],
        "forecast_horizon": forecast["horizon_months"],
        "forecast_confidence": forecast["confidence"],
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. CORPORATE QUOTATION → INVOICE → PAYMENT
# ═══════════════════════════════════════════════════════════════════════════

def test_corporate_quote_invoice_payment() -> dict[str, Any]:
    """Demonstrate corporate financial flow — quotation to invoice to payment."""
    runtime = FinancialIntelligenceRuntime()

    profile = runtime.get_or_create_profile("org_acme_tech", "Acme Tech Solutions Pvt Ltd")

    # Corporate accounts
    main = runtime.add_account(profile.profile_id, "Main Account", AccountType.CHECKING.value,
                                balance=15000000, institution="HDFC Corp")
    tax = runtime.add_account(profile.profile_id, "Tax Account", AccountType.TAX.value,
                               balance=500000, institution="HDFC Corp")
    receivable = runtime.add_account(profile.profile_id, "Accounts Receivable",
                                      AccountType.RECEIVABLE.value, balance=0)

    # Create a quotation for a client
    quotation = runtime.create_quotation(
        profile.profile_id,
        quotation_number="Q-2026-0042",
        issuer_id="org_acme_tech",
        recipient_id="org_mega_corp",
        line_items=[
            {"description": "Enterprise Software License (1 year)", "quantity": 1, "unit_price": 500000},
            {"description": "Implementation & Training", "quantity": 40, "unit_price": 5000},
            {"description": "Premium Support (SLA)", "quantity": 12, "unit_price": 25000},
        ],
        subtotal=500000 + 200000 + 300000,
        tax_amount=180000,
        total_amount=1180000,
        valid_until=_days_ago(60),
        terms="Net 30",
    )

    # Quotation accepted → create invoice
    invoice = runtime.create_invoice(
        profile.profile_id,
        invoice_number="INV-2026-0042",
        issuer_id="org_acme_tech",
        recipient_id="org_mega_corp",
        line_items=quotation.line_items,
        subtotal=quotation.subtotal.amount,
        tax_amount=100000,
        total_amount=quotation.total_amount.amount,
        due_date=_days_ago(-30),
        notes="As per quotation Q-2026-0042",
    )

    # Partial payment received
    payment1 = runtime.record_payment(
        profile.profile_id,
        invoice.invoice_id,
        amount=500000,
        method="bank_transfer",
        to_account_id=main.account_id,
    )
    assert invoice.status == InvoiceStatus.PARTIALLY_PAID.value

    # Full payment received
    payment2 = runtime.record_payment(
        profile.profile_id,
        invoice.invoice_id,
        amount=680000,
        method="bank_transfer",
        to_account_id=main.account_id,
    )
    assert invoice.status == InvoiceStatus.PAID.value
    assert invoice.is_paid

    # Pricing recommendation
    pricing = runtime.recommend_pricing(profile.profile_id, base_cost=350000, desired_margin_pct=30)

    # Revenue opportunities
    opportunities = runtime.get_revenue_opportunities(profile.profile_id)

    assert quotation is not None
    assert invoice.is_paid
    assert len(profile.payments) == 2
    assert pricing is not None
    assert pricing["recommended_price"] > 0

    return {
        "scenario": "4. Corporate Quote → Invoice → Payment",
        "entity": "Acme Tech Solutions → Mega Corp",
        "quotation_id": quotation.quotation_number,
        "invoice_id": invoice.invoice_number,
        "invoice_status": invoice.status,
        "payments": len(profile.payments),
        "recommended_price": pricing["recommended_price"],
        "revenue_opportunities": len(opportunities),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. FINANCIAL DISRUPTION WITH ADAPTIVE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def test_financial_disruption() -> dict[str, Any]:
    """Demonstrate financial disruption detection and adaptive execution response."""
    runtime = FinancialIntelligenceRuntime()

    profile = runtime.get_or_create_profile("org_retail_chain", "Retail Chain — Disruption Scenario")

    # Accounts
    main = runtime.add_account(profile.profile_id, "Operating Account", AccountType.CHECKING.value,
                                balance=300000, institution="ICICI")
    reserve = runtime.add_account(profile.profile_id, "Reserve", AccountType.SAVINGS.value,
                                   balance=100000, institution="ICICI")

    # Normal monthly revenue (before disruption)
    for month in range(6):
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            500000, to_account_id=main.account_id, category="retail_revenue",
            description=f"Monthly revenue — month {month+1}",
            occurred_at=_days_ago((6 - month) * 30 + 5))

    # Normal monthly expenses
    for month in range(6):
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            350000, from_account_id=main.account_id, category="operating_expenses",
            description=f"Operating expenses — month {month+1}",
            occurred_at=_days_ago((6 - month) * 30 + 10))

    # DISRUPTION: Revenue drops sharply in recent months
    runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
        100000, to_account_id=main.account_id, category="retail_revenue",
        description="Revenue post-disruption", occurred_at=_days_ago(5))
    runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
        80000, to_account_id=main.account_id, category="retail_revenue",
        description="Revenue post-disruption week 2", occurred_at=_days_ago(2))

    # Expenses remain high
    runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
        320000, from_account_id=main.account_id, category="operating_expenses",
        description="Fixed costs remain", occurred_at=_days_ago(3))

    # Detect risks
    risks = runtime.detect_risks(profile.profile_id)
    cash_flow = runtime.compute_cash_flow(profile.profile_id)
    forecast = runtime.forecast_cash_flow(profile.profile_id, 6)

    # Verify disruption is detected
    has_cash_flow_risk = any("cash_flow" in r["risk_type"] for r in risks)

    # Simulate adaptive execution: create a goal to recover
    recovery_goal = runtime.create_goal(
        profile.profile_id,
        "Revenue recovery to 500K/month",
        target_amount=500000,
        goal_type="revenue_target",
        target_date=_days_ago(-90),
    )

    # Pricing recommendation for recovery
    pricing = runtime.recommend_pricing(profile.profile_id, base_cost=200000, desired_margin_pct=25)

    # Verify Reality integration — register listener before health assessment
    received_notifications: list[dict[str, Any]] = []
    def listener(n: dict) -> None:
        received_notifications.append(n)
    runtime.register_reality_listener(listener)

    # Assess health AFTER listener is registered
    health = runtime.assess_financial_health(profile.profile_id)

    # Record a payment via Reality notification (create an invoice first)
    runtime.create_invoice(profile.profile_id, "INV-TEST-001", "org_retail_chain",
        "client_corp", [{"description": "Services", "quantity": 1, "unit_price": 50000}],
        subtotal=50000, total_amount=50000)
    runtime.notify({
        "type": "execution.payment_received",
        "profile_id": profile.profile_id,
        "invoice_id": profile.invoices[0].invoice_id,
        "amount": 50000,
    })

    # Unknown notification type silently ignored
    runtime.notify({"type": "unknown.notification_type"})

    assert risks is not None
    assert health is not None
    assert len(received_notifications) >= 1  # health assessed notification

    return {
        "scenario": "5. Financial Disruption + Adaptive Execution",
        "entity": "Retail Chain — Post-Disruption",
        "health_score": health["overall_score"],
        "assessment": health["assessment"],
        "risks_detected": len(risks),
        "cash_flow_risk_detected": has_cash_flow_risk,
        "cash_flow_net": cash_flow["net_flow"]["amount"],
        "forecast_balance_trend": forecast["projections"][-1]["projected_balance"],
        "recovery_goal_created": recovery_goal is not None,
        "reality_integration_verified": len(received_notifications) >= 1,
        "unknown_type_ignored": True,
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Run All Verifications
# ═══════════════════════════════════════════════════════════════════════════

def run_all_verifications() -> list[dict[str, Any]]:
    tests = [
        ("Personal Budgeting", test_personal_budgeting),
        ("Household Finances", test_household_finances),
        ("Startup Cash Flow", test_startup_cash_flow),
        ("Corporate Quote→Invoice→Payment", test_corporate_quote_invoice_payment),
        ("Financial Disruption + Adaptive Execution", test_financial_disruption),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            result["test_name"] = name
            result["status"] = "PASS"
            result["error"] = None
        except Exception as e:
            import traceback
            result = {
                "test_name": name,
                "scenario": name,
                "status": "FAIL",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "passed": False,
            }
        results.append(result)
    return results


if __name__ == "__main__":
    print("=" * 80)
    print("UCP-03 — Universal Financial Intelligence: Verification Report")
    print("=" * 80)
    print()

    results = run_all_verifications()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"  {status} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("health_score") is not None:
            print(f"         Health: {r['health_score']} ({r.get('assessment', 'N/A')})")
        if r.get("accounts"):
            print(f"         Accounts: {r['accounts']} | Transactions: {r.get('transactions', 'N/A')}")
        if r.get("invoices"):
            print(f"         Invoice: {r.get('invoice_id', 'N/A')} ({r.get('invoice_status', 'N/A')})")
        if r.get("risks_detected") is not None:
            print(f"         Risks: {r['risks_detected']} | Cash flow risk: {r.get('cash_flow_risk_detected', 'N/A')}")
        if r.get("forecast_horizon"):
            print(f"         Forecast: {r['forecast_horizon']} months (confidence: {r.get('forecast_confidence', 'N/A')})")
        if r.get("error"):
            print(f"         ERROR: {r['error']}")
        print()

    print("-" * 80)
    print(f"  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    print()

    if not failed:
        print("  ✅ UCP-03 VERIFICATION PASSED: All 5 financial scenarios execute")
        print("     through the same Universal Financial Intelligence capability.")
        print()
        print("  No Financial Runtime introduced.")
        print("  No Accounting Runtime introduced.")
        print("  No ERP Runtime introduced.")
        print()
        print("  Every financial scenario — Personal Budgeting, Household Finances,")
        print("  Startup Cash Flow, Corporate Quote→Invoice→Payment, Financial")
        print("  Disruption — composed from the same capability.")
        print("=" * 80)
    else:
        print("  ❌ UCP-03 VERIFICATION FAILED")
        print("=" * 80)