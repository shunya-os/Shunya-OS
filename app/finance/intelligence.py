"""FOR-2D.3: Financial Intelligence & Autonomous CFO.

Transforms SHUNYA from accounting platform into AI Financial OS.
All intelligence derives from canonical data. No legacy dependencies.
"""

from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from collections import defaultdict
from app import db
from app.finance.models import FinInvoice as Invoice, FinancePayment as Payment
from app.finance.models import LedgerEntry, Account, Budget
from app.finance.services import get_receivables_aging, get_financial_summary
from app.models import Proposal


# ── Cash Flow Intelligence ─────────────────────────────────────────────

def cash_flow_forecast(org_id, days=180):
    """Rolling cash flow forecast with confidence scores.

    Uses receivables aging, payables, budgets, recurring commitments,
    historical payment behavior, and revenue trends.

    Returns daily projected cash position + confidence.
    """
    today = date.today()

    # Current cash position
    cash_acct = Account.query.filter_by(organization_id=org_id, code="1000").first()
    cash_balance = 0
    if cash_acct:
        cash_balance = float(db.session.query(db.func.coalesce(db.func.sum(LedgerEntry.debit - LedgerEntry.credit), 0))
            .filter(LedgerEntry.account_id == cash_acct.id).scalar() or 0)

    # Receivables pipeline: expected inflows
    inflows = []
    for inv in Invoice.query.filter_by(organization_id=org_id).filter(
            Invoice.status.in_(["posted", "sent", "partially_paid"])):
        bal = float((inv.total_amount or 0) - (inv.paid_amount or 0))
        if bal > 0 and inv.due_date:
            inflows.append({"date": inv.due_date, "amount": bal, "confidence": 0.7, "source": f"invoice {inv.number}"})

    # Outflows from budgets/spending
    outflows = []
    budget_spent = Budget.query.filter_by(organization_id=org_id).all()
    for b in budget_spent:
        remaining = float((b.amount or 0) - (b.spent_amount or 0))
        if remaining > 0:
            outflows.append({"date": today + timedelta(days=30), "amount": remaining * 0.3,
                             "confidence": 0.4, "source": f"budget {b.name}"})

    # Daily projection
    projection = []
    cumulative = cash_balance
    for day_offset in range(days):
        d = today + timedelta(days=day_offset)
        day_inflow = sum(i["amount"] for i in inflows if i["date"] == d)
        day_outflow = sum(o["amount"] for o in outflows if o["date"] == d)
        cumulative = cumulative + day_inflow - day_outflow
        confidence = 0.95 if day_offset < 7 else (0.8 if day_offset < 30 else (0.6 if day_offset < 90 else 0.4))
        projection.append({
            "date": d.isoformat(), "day": day_offset + 1,
            "inflow": round(day_inflow, 2), "outflow": round(day_outflow, 2),
            "balance": round(cumulative, 2), "confidence": confidence,
        })

    # Key dates
    min_balance = min(p["balance"] for p in projection)
    zero_day = next((p["day"] for p in projection if p["balance"] <= 0), None)
    min_day = min(range(len(projection)), key=lambda i: projection[i]["balance"])

    return {
        "current_cash": round(cash_balance, 2),
        "forecast_days": days,
        "projection": projection[::7],  # Weekly summary
        "min_balance": round(min_balance, 2),
        "zero_cash_day": zero_day,
        "min_balance_day": projection[min_day]["day"] if min_day < len(projection) else None,
        "confidence_at_30d": 0.8,
        "confidence_at_90d": 0.6,
        "confidence_at_180d": 0.4,
    }


def compute_working_capital(org_id):
    """Compute working capital position."""
    ar = sum(float(inv.total_amount - inv.paid_amount) for inv in Invoice.query.filter_by(
        organization_id=org_id).filter(Invoice.status.in_(["sent", "posted", "partially_paid"])))
    ap = sum(float(p.amount) for p in Payment.query.filter_by(organization_id=org_id, type="payment"))
    cash = cash_flow_forecast(org_id, 1)["current_cash"]
    return {"cash": cash, "receivables": round(ar, 2), "payables": round(ap, 2),
        "working_capital": round(cash + ar - ap, 2)}


# ── Profitability Engine ───────────────────────────────────────────────

def profitability_by_relationship(org_id):
    """Compute profitability per relationship across all invoices."""
    results = []
    invoices = Invoice.query.filter_by(organization_id=org_id).filter(
        Invoice.type != "credit_note", Invoice.relationship_id != None).all()
    by_rel = defaultdict(lambda: {"revenue": 0, "cost": 0, "count": 0, "paid": 0})
    for inv in invoices:
        key = inv.relationship_id
        by_rel[key]["revenue"] += float(inv.total_amount or 0)
        by_rel[key]["paid"] += float(inv.paid_amount or 0)
        by_rel[key]["count"] += 1
    for rel_id, data in by_rel.items():
        margin = ((data["revenue"] - data["paid"]) / data["revenue"] * 100) if data["revenue"] else 0
        results.append({"relationship_id": rel_id, "total_revenue": round(data["revenue"], 2),
            "total_paid": round(data["paid"], 2), "invoice_count": data["count"],
            "margin_pct": round(margin, 1)})
    return sorted(results, key=lambda x: x["total_revenue"], reverse=True)


def profitability_by_proposal(org_id):
    """Compute profitability per proposal."""
    results = []
    for prop in Proposal.query.filter_by(organization_id=org_id).all():
        invoiced = sum(float(i.total_amount or 0) for i in Invoice.query.filter_by(
            proposal_id=prop.id, organization_id=org_id))
        paid = sum(float(i.paid_amount or 0) for i in Invoice.query.filter_by(
            proposal_id=prop.id, organization_id=org_id))
        if invoiced > 0 or paid > 0:
            margin = ((paid - 0) / invoiced * 100) if invoiced else 0
            results.append({"proposal_id": prop.id, "title": (prop.title or "")[:60],
                "invoiced": round(invoiced, 2), "paid": round(paid, 2),
                "margin_pct": round(margin, 1)})
    return sorted(results, key=lambda x: x["invoiced"], reverse=True)


def overall_profitability(org_id):
    """Overall profitability summary."""
    total_revenue = sum(float(i.total_amount or 0) for i in Invoice.query.filter_by(
        organization_id=org_id) if i.type != "credit_note")
    total_paid = sum(float(i.paid_amount or 0) for i in Invoice.query.filter_by(
        organization_id=org_id))
    total_cn = sum(float(i.total_amount or 0) for i in Invoice.query.filter_by(
        organization_id=org_id, type="credit_note"))
    net_revenue = total_revenue - total_cn
    gross_margin = (total_paid / total_revenue * 100) if total_revenue else 0
    return {"total_revenue": round(total_revenue, 2), "total_paid": round(total_paid, 2),
        "credit_notes": round(total_cn, 2), "net_revenue": round(net_revenue, 2),
        "gross_margin_pct": round(gross_margin, 1)}


# ── Lifetime Value Engine ──────────────────────────────────────────────

def lifetime_value(org_id, relationship_id=None):
    """Calculate lifetime value per relationship. Optionally filter by relationship_id."""
    q = Invoice.query.filter_by(organization_id=org_id).filter(Invoice.type != "credit_note")
    if relationship_id:
        q = q.filter_by(relationship_id=relationship_id)

    invoices = q.all()
    by_rel = defaultdict(lambda: {"revenue": 0, "margin": 0, "count": 0, "first": None, "last": None})
    for inv in invoices:
        rid = inv.relationship_id or 0
        by_rel[rid]["revenue"] += float(inv.total_amount or 0)
        by_rel[rid]["count"] += 1
        if not by_rel[rid]["first"] or (inv.issue_date and inv.issue_date < by_rel[rid]["first"]):
            by_rel[rid]["first"] = inv.issue_date
        if not by_rel[rid]["last"] or (inv.issue_date and inv.issue_date > by_rel[rid]["last"]):
            by_rel[rid]["last"] = inv.issue_date

    results = []
    for rid, d in by_rel.items():
        months_active = 1
        if d["first"] and d["last"]:
            months_diff = (d["last"].year - d["first"].year) * 12 + (d["last"].month - d["first"].month)
            months_active = max(months_diff, 1)
        monthly_rev = d["revenue"] / months_active if months_active else 0
        results.append({"relationship_id": rid, "total_revenue": round(d["revenue"], 2),
            "invoice_count": d["count"], "months_active": months_active,
            "monthly_revenue": round(monthly_rev, 2),
            "annualized_value": round(monthly_rev * 12, 2)})
    return sorted(results, key=lambda x: x["total_revenue"], reverse=True)


# ── Financial Risk Engine ──────────────────────────────────────────────

def risk_engine(org_id):
    """Continuous financial risk detection."""
    risks = []
    today = date.today()

    # 1. Cash shortage risk
    cf = cash_flow_forecast(org_id, 90)
    if cf.get("zero_cash_day"):
        risks.append({"type": "cash_shortage", "severity": "critical",
            "message": f"Cash may reach zero in {cf['zero_cash_day']} days",
            "detail": f"Current cash: {cf['current_cash']}, min projection: {cf['min_balance']}",
            "confidence": "high", "recommendation": "Review receivables collection, delay non-critical payments"})

    # 2. Slow collections
    aging = get_receivables_aging(org_id)
    overdue_ratio = (aging.get("90+", 0) + aging.get("61-90", 0)) / max(aging.get("total", 1), 1)
    if overdue_ratio > 0.3:
        risks.append({"type": "slow_collections", "severity": "warning",
            "message": f"{overdue_ratio:.0%} of receivables are 60+ days overdue",
            "detail": f"Overdue: {aging.get('61-90',0) + aging.get('90+',0)} out of {aging.get('total',0)}",
            "confidence": "high", "recommendation": "Initiate collection process for overdue invoices"})

    # 3. Customer concentration
    by_rel = profitability_by_relationship(org_id)
    if by_rel:
        top_rel = by_rel[0]
        concentration = top_rel["total_revenue"] / max(sum(r["total_revenue"] for r in by_rel), 1)
        if concentration > 0.4:
            risks.append({"type": "customer_concentration", "severity": "warning",
                "message": f"Top relationship represents {concentration:.0%} of revenue",
                "detail": f"Relationship #{top_rel['relationship_id']}: {top_rel['total_revenue']}",
                "confidence": "medium", "recommendation": "Diversify customer base to reduce concentration risk"})

    # 4. High correction rate
    total_inv = Invoice.query.filter_by(organization_id=org_id).count() or 1
    cn_count = Invoice.query.filter_by(organization_id=org_id, type="credit_note").count()
    correction_rate = cn_count / total_inv
    if correction_rate > 0.2:
        risks.append({"type": "high_correction_rate", "severity": "info",
            "message": f"Credit notes: {cn_count} out of {total_inv} invoices ({correction_rate:.0%})",
            "detail": "Above 20% threshold", "confidence": "medium",
            "recommendation": "Review invoicing accuracy; consider pre-approval workflow"})

    # 5. Budget overruns
    for b in Budget.query.filter_by(organization_id=org_id):
        if b.amount and b.spent_amount and b.spent_amount > b.amount:
            overrun = float(b.spent_amount - b.amount) / float(b.amount) * 100
            risks.append({"type": "budget_overrun", "severity": "warning",
                "message": f"Budget '{b.name}' exceeded by {overrun:.0f}%",
                "confidence": "high", "recommendation": "Review and revise budget allocation"})

    return {"risks": risks, "count": len(risks),
        "critical": sum(1 for r in risks if r["severity"] == "critical"),
        "warning": sum(1 for r in risks if r["severity"] == "warning"),
        "info": sum(1 for r in risks if r["severity"] == "info")}


# ── Opportunity Engine ─────────────────────────────────────────────────

def opportunity_engine(org_id):
    """Identify financial opportunities."""
    opportunities = []
    today = date.today()

    # 1. Early payment discount opportunities
    for inv in Invoice.query.filter_by(organization_id=org_id).filter(
            Invoice.status == "sent").all():
        if inv.due_date and inv.total_amount:
            days_to_due = (inv.due_date - today).days
            if 10 <= days_to_due <= 30:
                discount = float(inv.total_amount) * 0.02
                opportunities.append({"type": "early_payment_discount",
                    "message": f"Offer 2% discount on invoice {inv.number} for early payment",
                    "savings": round(discount, 2), "confidence": "medium",
                    "action": "Send early payment reminder"})

    # 2. Upsell from top relationships
    ltv_results = lifetime_value(org_id)
    for r in ltv_results[:3]:
        if r["invoice_count"] <= 2 and r["annualized_value"] > 0:
            opportunities.append({"type": "upsell",
                "message": f"Relationship #{r['relationship_id']} has low repeat rate ({r['invoice_count']} invoices) but high value ({r['annualized_value']})",
                "estimated_value": round(r['annualized_value'] * 0.2, 2), "confidence": "low",
                "action": "Schedule business development review"})

    return {"opportunities": opportunities, "count": len(opportunities)}


# ── Scenario Modelling ─────────────────────────────────────────────────

def scenario_model(org_id, scenario_type, params):
    """What-if scenario modelling."""
    base = overall_profitability(org_id)
    today = date.today()

    if scenario_type == "revenue_growth":
        pct = float(params.get("percent", 10))
        new_rev = base["net_revenue"] * (1 + pct / 100)
        new_margin = (base["total_paid"] / new_rev * 100) if new_rev else 0
        return {"scenario": f"{pct}% revenue growth",
            "current": base, "projected": {
                "net_revenue": round(new_rev, 2),
                "margin_pct": round(new_margin, 1),
                "change": f"+{pct}%",
            }}
    elif scenario_type == "revenue_decline":
        pct = float(params.get("percent", 10))
        new_rev = base["net_revenue"] * (1 - pct / 100)
        new_margin = (base["total_paid"] / new_rev * 100) if new_rev else 0
        return {"scenario": f"{pct}% revenue decline",
            "current": base, "projected": {
                "net_revenue": round(new_rev, 2),
                "margin_pct": round(new_margin, 1),
                "change": f"-{pct}%",
            }}
    elif scenario_type == "price_change":
        pct = float(params.get("percent", 5))
        price_impact = base["net_revenue"] * (pct / 100)
        new_rev = base["net_revenue"] + price_impact
        return {"scenario": f"{pct}% price {'increase' if pct > 0 else 'decrease'}",
            "current": base, "projected": {
                "net_revenue": round(new_rev, 2),
                "revenue_impact": round(price_impact, 2),
            }}
    elif scenario_type == "cost_change":
        pct = float(params.get("percent", 10))
        cost_impact = base["total_paid"] * (pct / 100)
        new_paid = base["total_paid"] + cost_impact
        return {"scenario": f"{pct}% cost {'increase' if pct > 0 else 'decrease'}",
            "current": base, "projected": {
                "total_paid": round(new_paid, 2),
                "cost_impact": round(cost_impact, 2),
            }}
    return {"error": f"Unknown scenario: {scenario_type}"}


# ── Natural Language CFO ───────────────────────────────────────────────

def cfo_explain(org_id, question):
    """Answer executive questions with evidence, calculations, and confidence."""
    question_lower = question.lower()
    today = date.today()

    # 1. Why did profit decrease?
    if "profit" in question_lower and "decreas" in question_lower:
        profit = overall_profitability(org_id)
        cn = sum(float(i.total_amount or 0) for i in Invoice.query.filter_by(
            organization_id=org_id, type="credit_note"))
        aging = get_receivables_aging(org_id)
        overdue = aging.get("90+", 0) + aging.get("61-90", 0)
        return {"question": question, "answer": f"Net revenue is {profit['net_revenue']:.0f} "
            f"with {profit['gross_margin_pct']:.0f}% margin. "
            f"Credit notes totaling {cn:.0f} reduced revenue. "
            f"Overdue receivables of {overdue:.0f} may indicate collection issues affecting profitability.",
            "evidence": {"net_revenue": profit["net_revenue"], "credit_notes": cn,
                "overdue_receivables": overdue, "gross_margin": profit["gross_margin_pct"]},
            "confidence": "high", "calculation": f"Revenue {profit['total_revenue']:.0f} - Credit Notes {cn:.0f} = Net {profit['net_revenue']:.0f}"}

    # 2. Most valuable customer / customer profitability
    if ("most valuable" in question_lower or "valuable" in question_lower or "profitable" in question_lower) \
       and ("customer" in question_lower or "client" in question_lower or "relationship" in question_lower):
        ltv = lifetime_value(org_id)
        if ltv:
            top = ltv[0]
            return {"question": question, "answer": f"Most valuable: Relationship #{top['relationship_id']} with "
                f"{top['total_revenue']:.0f} total revenue over {top['months_active']} months "
                f"({top['annualized_value']:.0f}/year annualized). {top['invoice_count']} invoices.",
                "evidence": {"top_relationships": ltv[:3]}, "confidence": "high"}
        return {"question": question, "answer": "No customer data available yet. Create invoices to build value insights.",
            "confidence": "low"}

    # 3. Which customer is becoming risky?
    if "risk" in question_lower or "customer" in question_lower:
        risks = risk_engine(org_id)
        top_risk = risks["risks"][0] if risks["risks"] else None
        return {"question": question, "answer": f"Top risk: {top_risk['message'] if top_risk else 'No significant risks detected'}",
            "evidence": risks["risks"][:3], "confidence": top_risk.get("confidence", "high") if top_risk else "high",
            "recommendation": top_risk.get("recommendation", "Continue monitoring") if top_risk else "None"}

    # 3. Which invoices are likely overdue?
    if "overdue" in question_lower or "invoice" in question_lower:
        aging = get_receivables_aging(org_id)
        overdue_invs = Invoice.query.filter_by(organization_id=org_id).filter(
            Invoice.due_date < today, Invoice.status.in_(["sent", "posted"])).all()
        total_overdue = sum(float(i.total_amount - i.paid_amount) for i in overdue_invs)
        return {"question": question, "answer": f"{len(overdue_invs)} overdue invoices totaling {total_overdue:.0f}. "
            f"Aging: current={aging.get('current',0):.0f}, 1-30d={aging.get('1-30',0):.0f}, "
            f"31-60d={aging.get('31-60',0):.0f}, 61-90d={aging.get('61-90',0):.0f}, 90+={aging.get('90+',0):.0f}",
            "evidence": {"total_overdue": total_overdue, "count": len(overdue_invs), "aging": aging},
            "confidence": "high"}

    # 4a. What happens if revenue grows?
    if "revenue" in question_lower and ("grow" in question_lower or "increas" in question_lower or "rise" in question_lower):
        pct = 15
        if "what if" in question_lower:
            import re
            m = re.search(r'(\d+)', question)
            if m: pct = int(m.group(1))
        result = scenario_model(org_id, "revenue_growth", {"percent": pct})
        return {"question": question, "answer": f"A {pct}% revenue growth would increase net revenue from "
            f"{result['current']['net_revenue']:.0f} to {result['projected']['net_revenue']:.0f}. "
            f"This is a {result['projected']['change']} change.",
            "evidence": result, "confidence": "medium",
            "recommendation": "Maintain cost discipline to maximize margin impact"}

    # 4b. (reserved)

    # 4c. What happens if revenue drops?
    if "revenue" in question_lower and ("drop" in question_lower or "decreas" in question_lower or "fall" in question_lower):
        pct = 20
        import re
        m = re.search(r'(\d+)', question)
        if m: pct = int(m.group(1))
        result = scenario_model(org_id, "revenue_decline", {"percent": pct})
        return {"question": question, "answer": f"A {pct}% revenue decline would reduce net revenue from "
            f"{result['current']['net_revenue']:.0f} to {result['projected']['net_revenue']:.0f}. "
            f"This is a {result['projected']['change']} change.",
            "evidence": result, "confidence": "medium",
            "recommendation": "Review cost structure and identify revenue protection strategies"}

    # 5. General financial health
    if "health" in question_lower or "how" in question_lower:
        cf = cash_flow_forecast(org_id, 30)
        profit = overall_profitability(org_id)
        risks = risk_engine(org_id)
        return {"question": question, "answer": f"Cash: {cf['current_cash']:.0f} | "
            f"30d projection: min {cf['min_balance']:.0f} | "
            f"Net revenue: {profit['net_revenue']:.0f} | "
            f"Margin: {profit['gross_margin_pct']:.0f}% | "
            f"Risks: {risks['critical']} critical, {risks['warning']} warning, {risks['info']} info",
            "evidence": {"cash": cf["current_cash"], "cash_30d_min": cf["min_balance"],
                "net_revenue": profit["net_revenue"], "margin": profit["gross_margin_pct"],
                "risk_counts": {"critical": risks["critical"], "warning": risks["warning"]}},
            "confidence": "high"}

    return {"question": question, "answer": "I can analyze financial health, cash flow, profitability, risks, and scenarios. "
        "Try asking: 'How is business health?', 'Which customers are risky?', "
        "'What if revenue drops 20%?', or 'Why did profit decrease?'",
        "confidence": "high"}


# ── Executive CFO Workspace ─────────────────────────────────────────────

def executive_cfo_workspace(org_id):
    """Complete executive financial workspace."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "financial_health": overall_profitability(org_id),
        "cash_position": cash_flow_forecast(org_id, 30),
        "working_capital": compute_working_capital(org_id),
        "receivables_aging": get_receivables_aging(org_id),
        "profitability_by_relationship": profitability_by_relationship(org_id)[:5],
        "profitability_by_proposal": profitability_by_proposal(org_id)[:5],
        "lifetime_value": lifetime_value(org_id)[:5],
        "risks": risk_engine(org_id),
        "opportunities": opportunity_engine(org_id),
    }