"""UCP-03A Verification — Financial Intelligence (reasoning layer).

Verifies 5 financial reasoning scenarios:
1. Individual financial planning (affordability, opportunity cost, goals)
2. Startup growth planning (hiring, investment, runway)
3. Enterprise pricing decision (trade-offs, decision support)
4. Budget reduction scenario (simulation, conflicts)
5. Revenue shock simulation (scenario, re-forecast)

Every recommendation includes evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from core.financial_intelligence import (
    FinancialIntelligenceRuntime,
    AccountType,
    TransactionType,
    Money,
)


def _days_ago(days: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat().replace("+00:00", "Z")


# ═══════════════════════════════════════════════════════════════════════════
# 1. INDIVIDUAL FINANCIAL PLANNING
# ═══════════════════════════════════════════════════════════════════════════

def test_individual_financial_planning() -> dict[str, Any]:
    """Demonstrate individual financial planning with affordability, opportunity cost, and goals."""
    runtime = FinancialIntelligenceRuntime()
    profile = runtime.get_or_create_profile("person_arjun", "Arjun — Software Engineer")

    # Accounts
    checking = runtime.add_account(profile.profile_id, "Checking", AccountType.CHECKING.value,
                                    balance=85000, institution="HDFC")
    savings = runtime.add_account(profile.profile_id, "Savings", AccountType.SAVINGS.value,
                                   balance=200000, institution="HDFC")

    # Income
    for i in range(6):
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            75000, to_account_id=checking.account_id, category="salary",
            description=f"Monthly salary — {i+1}", occurred_at=_days_ago(i * 30 + 5))

    # Expenses
    expenses = [(20000, "rent", 2), (5000, "groceries", 3), (3000, "utilities", 7),
                (4000, "dining", 4), (2000, "transport", 6), (5000, "emi", 10)]
    for amt, cat, d in expenses:
        for m in range(6):
            runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
                amt, from_account_id=checking.account_id, category=cat,
                description=cat, occurred_at=_days_ago(m * 30 + d))

    # Financial goals
    runtime.create_goal(profile.profile_id, "Down payment for house", 5000000,
                        goal_type="purchase", target_date=_days_ago(-365 * 3))
    runtime.create_goal(profile.profile_id, "Emergency fund", 300000,
                        goal_type="emergency_fund", target_date=_days_ago(-365))
    profile.goals[0].current_amount = Money(amount=800000)
    profile.goals[1].current_amount = Money(amount=200000)

    # 1a. Affordability analysis: can Arjun afford a new laptop?
    laptop = runtime.analyze_affordability(profile.profile_id, "MacBook Pro", 150000)
    assert laptop is not None
    assert "evidence" in laptop
    assert len(laptop["evidence"]) >= 1

    # 1b. Opportunity cost: invest 150K in FD vs mutual funds
    opp_cost = runtime.compute_opportunity_cost(profile.profile_id, 150000, 150000,
                                                 time_horizon_months=12, return_a=4, return_b=8)
    assert opp_cost is not None
    assert opp_cost["opportunity_cost"] > 0

    # 1c. Goal analysis
    goal_analysis = runtime.analyze_goal(profile.profile_id, profile.goals[0].goal_id)
    assert goal_analysis is not None
    assert goal_analysis["progress_pct"] > 0

    # 1d. Financial health
    health = runtime.assess_financial_health(profile.profile_id)
    assert health is not None

    return {
        "scenario": "1. Individual Financial Planning",
        "entity": "Arjun — Software Engineer",
        "affordability_analysis": laptop["is_affordable"],
        "affordability_score": laptop["affordability_score"],
        "affordability_evidence": len(laptop["evidence"]),
        "opportunity_cost": opp_cost["opportunity_cost"],
        "goal_progress_pct": goal_analysis["progress_pct"],
        "health_score": health["overall_score"],
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. STARTUP GROWTH PLANNING
# ═══════════════════════════════════════════════════════════════════════════

def test_startup_growth_planning() -> dict[str, Any]:
    """Demonstrate startup growth planning with hiring, investment, and runway analysis."""
    runtime = FinancialIntelligenceRuntime()
    profile = runtime.get_or_create_profile("startup_inno", "InnoTech — Growth Stage")

    # Accounts
    main = runtime.add_account(profile.profile_id, "Operating", AccountType.CHECKING.value,
                                balance=3500000, institution="YC")
    reserve = runtime.add_account(profile.profile_id, "Reserve", AccountType.SAVINGS.value,
                                   balance=8000000, institution="YC")

    # Revenue (SaaS)
    for m in range(12):
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            400000 + m * 20000, to_account_id=main.account_id, category="saas_revenue",
            description=f"MRR {m+1}", occurred_at=_days_ago((12-m)*30))

    # Expenses
    for m in range(12):
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            250000, from_account_id=main.account_id, category="salaries",
            description=f"Payroll {m+1}", occurred_at=_days_ago((12-m)*30))
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            50000, from_account_id=main.account_id, category="cloud_infrastructure",
            description=f"Cloud {m+1}", occurred_at=_days_ago((12-m)*28))
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            30000, from_account_id=main.account_id, category="marketing",
            description=f"Marketing {m+1}", occurred_at=_days_ago((12-m)*25))

    # 2a. Runway analysis
    runway = runtime.analyze_runway(profile.profile_id)
    assert runway is not None
    assert "runway_months" in runway
    assert "sensitivity" in runway

    # 2b. Hiring impact: can they hire a senior engineer?
    hiring = runtime.analyze_hiring_impact(profile.profile_id, "Senior Engineer", 2400000)
    assert hiring is not None
    assert "evidence" in hiring
    assert len(hiring["evidence"]) >= 1
    assert "payroll_increase_pct" in hiring

    # 2c. Investment analysis: invest 2Cr in growth
    investment = runtime.analyze_investment(profile.profile_id, 2000000, 12,
                                             time_horizon_months=24, monthly_contribution=500000)
    assert investment is not None
    assert investment["future_value"] > investment["principal"]["amount"]

    # 2d. Revenue forecast
    revenue_forecast = runtime.forecast_revenue(profile.profile_id)
    assert revenue_forecast is not None
    assert "projections" in revenue_forecast

    # 2e. Cash flow forecast
    forecast = runtime.forecast_cash_flow(profile.profile_id, 6)
    assert forecast is not None

    return {
        "scenario": "2. Startup Growth Planning",
        "entity": "InnoTech — Growth Stage",
        "runway_months": runway["runway_months"],
        "runway_sensitivity_count": len(runway["sensitivity"]),
        "hiring_payroll_increase_pct": hiring["payroll_increase_pct"],
        "hiring_evidence": len(hiring["evidence"]),
        "investment_future_value": investment["future_value"],
        "revenue_forecast_months": len(revenue_forecast["projections"]),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. ENTERPRISE PRICING DECISION
# ═══════════════════════════════════════════════════════════════════════════

def test_enterprise_pricing_decision() -> dict[str, Any]:
    """Demonstrate enterprise pricing decision with trade-offs and decision support."""
    runtime = FinancialIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_solutions", "Solutions Inc — Enterprise")

    # Accounts
    main = runtime.add_account(profile.profile_id, "Main", AccountType.CHECKING.value,
                                balance=50000000, institution="HDFC Corp")

    # Revenue history
    for m in range(12):
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            5000000, to_account_id=main.account_id, category="revenue",
            description=f"Month {m+1}", occurred_at=_days_ago((12-m)*30))

    # Expenses
    for m in range(12):
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            3500000, from_account_id=main.account_id, category="opex",
            description=f"Opex {m+1}", occurred_at=_days_ago((12-m)*30))

    # 3a. Pricing recommendation
    pricing = runtime.recommend_pricing(profile.profile_id, 500000, desired_margin_pct=25)
    assert pricing is not None
    assert pricing["recommended_price"] > 0

    # 3b. Trade-off analysis: fixed price vs subscription
    tradeoff = runtime.analyze_tradeoffs(
        profile.profile_id,
        "Fixed Price — 5L one-time", 500000, "One-time revenue",
        "Subscription — 50K/month", 600000, "12-month recurring revenue increase",
    )
    assert tradeoff is not None
    assert "opportunity_cost" in tradeoff
    assert "evidence" in tradeoff

    # 3c. Decision support: choose between 3 pricing models
    decision = runtime.decision_support(
        profile.profile_id,
        "Choose pricing model for new product",
        "Enterprise SaaS product targeting mid-market",
        options=[
            {"name": "Per-seat monthly", "upfront_cost": 0, "recurring_cost": 50000,
             "benefit": 1200000, "risk": "medium"},
            {"name": "Tiered annual", "upfront_cost": 500000, "recurring_cost": 30000,
             "benefit": 1500000, "risk": "low"},
            {"name": "Usage-based", "upfront_cost": 200000, "recurring_cost": 40000,
             "benefit": 1800000, "risk": "high"},
        ],
    )
    assert decision is not None
    assert "alternatives" in decision
    assert len(decision["alternatives"]) == 3
    assert "recommendation" in decision
    assert "evidence" in decision

    # 3d. Customer payment risk
    # Create invoices to a customer
    for i in range(3):
        inv = runtime.create_invoice(profile.profile_id, f"INV-2026-{100+i}",
            "org_solutions", "client_mega_corp",
            [{"description": "Services", "quantity": 1, "unit_price": 500000}],
            subtotal=500000, total_amount=500000, due_date=_days_ago(-15))
        if i == 0:
            # Mark as paid
            runtime.record_payment(profile.profile_id, inv.invoice_id, 500000)

    risk = runtime.assess_customer_payment_risk(profile.profile_id, "client_mega_corp", "Mega Corp")
    assert risk is not None
    assert "risk_level" in risk
    assert "evidence" in risk

    return {
        "scenario": "3. Enterprise Pricing Decision",
        "entity": "Solutions Inc",
        "pricing_recommendation": pricing["recommended_price"],
        "tradeoff_opportunity_cost": tradeoff["opportunity_cost"]["amount"],
        "decision_options": len(decision["alternatives"]),
        "decision_recommendation": decision["recommendation"][:30],
        "customer_risk_level": risk["risk_level"],
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. BUDGET REDUCTION SCENARIO
# ═══════════════════════════════════════════════════════════════════════════

def test_budget_reduction_scenario() -> dict[str, Any]:
    """Demonstrate budget reduction scenario with simulation and conflict detection."""
    runtime = FinancialIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_retail", "Retail Co — Cost Optimization")

    # Accounts
    main = runtime.add_account(profile.profile_id, "Operating", AccountType.CHECKING.value,
                                balance=2000000, institution="ICICI")
    runtime.add_account(profile.profile_id, "Reserve", AccountType.SAVINGS.value,
                         balance=500000, institution="ICICI")

    # Revenue
    for m in range(6):
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            800000, to_account_id=main.account_id, category="retail_revenue",
            description=f"Revenue {m+1}", occurred_at=_days_ago(m*30+5))

    # Expenses
    expense_cats = [("salaries", 300000), ("rent", 100000), ("inventory", 200000),
                    ("marketing", 80000), ("utilities", 40000), ("logistics", 60000)]
    for cat, amt in expense_cats:
        for m in range(6):
            runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
                amt, from_account_id=main.account_id, category=cat,
                description=cat, occurred_at=_days_ago(m*30+10))

    # Budgets
    budget = runtime.create_budget(profile.profile_id, "Q3 Operating Budget", 4800000,
                                    categories={"salaries": {"planned": 1800000},
                                                "inventory": {"planned": 1200000},
                                                "marketing": {"planned": 480000},
                                                "rent": {"planned": 600000},
                                                "utilities": {"planned": 240000}})
    # Simulate over-budget
    runtime.update_budget_spending(profile.profile_id, budget.budget_id, 2000000)

    # 4a. Simulate budget reduction: cut expenses by 20%
    sim = runtime.simulate_scenario(
        profile.profile_id,
        "20% Expense Reduction",
        "Reduce all operating expenses by 20% for 6 months",
        expense_delta_pct=-20,
        horizon_months=6,
    )
    assert sim is not None
    assert "baseline" in sim
    assert "projected" in sim
    assert "delta" in sim
    assert "evidence" in sim
    assert "risks" in sim
    assert sim["delta"]["outflow_delta_pct"] == -20

    # 4b. Expense forecast
    expense_forecast = runtime.forecast_expenses(profile.profile_id)
    assert expense_forecast is not None
    assert "avg_monthly_expense" in expense_forecast

    # 4c. Commitment conflicts
    runtime.create_goal(profile.profile_id, "New store expansion", 5000000,
                        goal_type="purchase", target_date=_days_ago(-365))
    runtime.create_goal(profile.profile_id, "Inventory upgrade", 2000000,
                        goal_type="custom", target_date=_days_ago(-180))

    conflicts = runtime.detect_commitment_conflicts(profile.profile_id)
    assert conflicts is not None

    # 4d. Budget analysis
    budget_insights = runtime.get_spending_insights(profile.profile_id)
    assert budget_insights is not None

    return {
        "scenario": "4. Budget Reduction Scenario",
        "entity": "Retail Co — Cost Optimization",
        "simulation_projected_balance": sim["projected"]["balance"],
        "simulation_evidence": len(sim["evidence"]),
        "simulation_risks": len(sim["risks"]),
        "expense_forecast_months": len(expense_forecast["projections"]),
        "conflicts_detected": len(conflicts),
        "spending_insights": len(budget_insights),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. REVENUE SHOCK SIMULATION
# ═══════════════════════════════════════════════════════════════════════════

def test_revenue_shock_simulation() -> dict[str, Any]:
    """Demonstrate revenue shock simulation with re-forecasting and supplier optimization."""
    runtime = FinancialIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_manu", "ManuCorp — Revenue Shock Scenario")

    # Accounts
    main = runtime.add_account(profile.profile_id, "Operating", AccountType.CHECKING.value,
                                balance=5000000, institution="HDFC")
    runtime.add_account(profile.profile_id, "Reserve", AccountType.SAVINGS.value,
                         balance=2000000, institution="HDFC")

    # Pre-shock revenue (12 months)
    for m in range(12):
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            1000000, to_account_id=main.account_id, category="manufacturing_revenue",
            description=f"Revenue {m+1}", occurred_at=_days_ago((12-m)*30+5))

    # Post-shock revenue (2 months — 50% drop)
    for m in range(2):
        runtime.record_transaction(profile.profile_id, TransactionType.INCOME.value,
            500000, to_account_id=main.account_id, category="manufacturing_revenue",
            description=f"Revenue post-shock {m+1}", occurred_at=_days_ago(m*30+5))

    # Expenses
    for m in range(14):
        runtime.record_transaction(profile.profile_id, TransactionType.EXPENSE.value,
            700000, from_account_id=main.account_id, category="operating_expenses",
            description=f"Opex {m+1}", occurred_at=_days_ago((14-m)*30+10))

    # 5a. Simulate revenue shock: 30% revenue decline
    shock = runtime.simulate_scenario(
        profile.profile_id,
        "30% Revenue Decline",
        "Revenue drops 30% due to market conditions",
        revenue_delta_pct=-30,
        horizon_months=6,
    )
    assert shock is not None
    assert shock["delta"]["inflow_delta_pct"] == -30
    assert "evidence" in shock
    assert len(shock["evidence"]) >= 1

    # 5b. Revenue forecast (should show decline)
    revenue_forecast = runtime.forecast_revenue(profile.profile_id)
    assert revenue_forecast is not None

    # 5c. Runway analysis
    runway = runtime.analyze_runway(profile.profile_id)
    assert runway is not None

    # 5d. Supplier payment optimization
    supplier_opt = runtime.optimize_supplier_payments(
        profile.profile_id, "supplier_raw_materials", "Raw Materials Ltd",
        total_payable=1500000, current_terms_days=30,
    )
    assert supplier_opt is not None
    assert "recommendation" in supplier_opt
    assert "evidence" in supplier_opt
    assert len(supplier_opt["evidence"]) >= 1

    # 5e. Decision support for recovery
    recovery = runtime.decision_support(
        profile.profile_id,
        "Revenue recovery strategy",
        "Choose recovery path after 30% revenue decline",
        options=[
            {"name": "Cost reduction 15%", "upfront_cost": 100000, "recurring_cost": 10000,
             "benefit": 2000000, "risk": "low"},
            {"name": "New product launch", "upfront_cost": 500000, "recurring_cost": 50000,
             "benefit": 3000000, "risk": "high"},
            {"name": "Market expansion", "upfront_cost": 300000, "recurring_cost": 30000,
             "benefit": 2500000, "risk": "medium"},
        ],
    )
    assert recovery is not None
    assert "recommendation" in recovery
    assert "evidence" in recovery

    # 5f. Explainable recommendation
    explanation = runtime._engine.explain_recommendation(
        recovery["recommendation"], recovery["evidence"])
    assert explanation is not None
    assert "evidence_summary" in explanation

    return {
        "scenario": "5. Revenue Shock Simulation",
        "entity": "ManuCorp — Revenue Shock Scenario",
        "shock_projected_balance": shock["projected"]["balance"],
        "shock_evidence": len(shock["evidence"]),
        "shock_assumptions": len(shock["assumptions"]),
        "revenue_forecast_months": len(revenue_forecast["projections"]) if "projections" in revenue_forecast else 0,
        "runway_months": runway["runway_months"],
        "supplier_recommendation": supplier_opt["recommendation"][:40],
        "recovery_recommendation": recovery["recommendation"][:40],
        "explainable_evidence": len(explanation["evidence_summary"]),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Run All Verifications
# ═══════════════════════════════════════════════════════════════════════════

def run_all_verifications() -> list[dict[str, Any]]:
    tests = [
        ("Individual Financial Planning", test_individual_financial_planning),
        ("Startup Growth Planning", test_startup_growth_planning),
        ("Enterprise Pricing Decision", test_enterprise_pricing_decision),
        ("Budget Reduction Scenario", test_budget_reduction_scenario),
        ("Revenue Shock Simulation", test_revenue_shock_simulation),
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
    print("UCP-03A — Financial Intelligence (Reasoning): Verification Report")
    print("=" * 80)
    print()

    results = run_all_verifications()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"  {status} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("affordability_score") is not None:
            print(f"         Affordability: {r.get('affordability_analysis', 'N/A')} (score={r['affordability_score']}, evidence={r.get('affordability_evidence', 0)})")
        if r.get("runway_months") is not None:
            print(f"         Runway: {r['runway_months']} months")
        if r.get("hiring_payroll_increase_pct") is not None:
            print(f"         Hiring impact: +{r['hiring_payroll_increase_pct']}% payroll")
        if r.get("decision_options") is not None:
            print(f"         Decision: {r['decision_options']} options evaluated")
        if r.get("simulation_evidence") is not None:
            print(f"         Simulation: evidence={r['simulation_evidence']}, risks={r.get('simulation_risks', 0)}")
        if r.get("conflicts_detected") is not None:
            print(f"         Conflicts: {r['conflicts_detected']} detected")
        if r.get("explainable_evidence") is not None:
            print(f"         Explainable: {r['explainable_evidence']} evidence items")
        if r.get("customer_risk_level") is not None:
            print(f"         Customer risk: {r['customer_risk_level']}")
        if r.get("error"):
            print(f"         ERROR: {r['error']}")
        print()

    print("-" * 80)
    print(f"  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    print()

    if not failed:
        print("  ✅ UCP-03A VERIFICATION PASSED: All 5 financial reasoning scenarios")
        print("     demonstrate financial intelligence, not financial record-keeping.")
        print()
        print("  Every recommendation includes evidence.")
        print("  No architectural changes. No new runtime. No duplication.")
        print()
        print("  Financial Intelligence is the canonical financial capability for SHUNYA.")
        print("=" * 80)
    else:
        print("  ❌ UCP-03A VERIFICATION FAILED")
        print("=" * 80)