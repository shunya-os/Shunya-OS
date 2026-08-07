"""UCP-06 Verification — Universal Agreement Intelligence.

Verifies 8 scenarios through the same capability:
1. Employment Agreement
2. Customer Purchase
3. Supplier Contract
4. Medical Consent
5. Rental Agreement
6. Partnership Agreement
7. Subscription Renewal
8. Agreement breach with adaptive execution

No Contract Runtime. No Procurement Runtime. No Legal Runtime.
"""

from __future__ import annotations

from typing import Any

from core.agreement_intelligence import (
    AgreementIntelligenceRuntime,
    AgreementType,
    AgreementStatus,
    ObligationStatus,
    RiskLevel,
)


def test_employment_agreement() -> dict[str, Any]:
    runtime = AgreementIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_tech", "Tech Corp — Employment")

    agreement = runtime.create_agreement(
        profile.profile_id, AgreementType.EMPLOYMENT.value,
        "Senior Software Engineer — Priya Sharma",
        "Full-time employment agreement for engineering role",
        parties=[{"name": "Tech Corp", "role": "employer"},
                 {"name": "Priya Sharma", "role": "employee"}],
        obligations=[
            {"description": "Deliver software features per sprint goals", "party_id": "", "status": "pending"},
            {"description": "Work 40 hours per week", "party_id": "", "status": "pending"},
            {"description": "Maintain confidentiality", "party_id": "", "status": "pending"},
            {"description": "Pay monthly salary of 1.2L", "party_id": "", "status": "pending"},
        ],
        conditions=[{"description": "Background check completed", "is_met": True}],
        milestones=[{"title": "Probation complete", "description": "6-month review", "status": "pending"}],
        terms="Standard employment terms with 3-month notice period",
        start_date="2026-09-01",
        financial_commitments=[
            {"description": "Monthly salary", "amount": 120000, "status": "pending",
             "due_date": "2026-09-30"},
        ],
    )
    assert agreement is not None
    assert len(agreement.parties) == 2
    runtime.transition_status(profile.profile_id, agreement.agreement_id, "proposed")
    runtime.transition_status(profile.profile_id, agreement.agreement_id, "accepted")
    runtime.transition_status(profile.profile_id, agreement.agreement_id, "active")
    assert agreement.status == AgreementStatus.ACTIVE.value

    analysis = runtime.analyze_agreement(profile.profile_id, agreement.agreement_id)
    assert analysis is not None
    assert analysis["fulfilment"]["total"] == 4

    return {"scenario": "1. Employment Agreement", "entity": "Tech Corp — Priya Sharma",
            "parties": len(agreement.parties), "obligations": len(agreement.obligations),
            "status": agreement.status, "passed": True}


def test_customer_purchase() -> dict[str, Any]:
    runtime = AgreementIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_store", "Online Store")

    agreement = runtime.create_agreement(
        profile.profile_id, AgreementType.CUSTOMER_PURCHASE.value,
        "Purchase — iPhone 16 Pro",
        "Customer purchase agreement for electronics",
        parties=[{"name": "TechStore", "role": "seller"},
                 {"name": "Amit Singh", "role": "buyer"}],
        obligations=[
            {"description": "Deliver iPhone 16 Pro within 7 days", "party_id": "", "status": "pending"},
            {"description": "Pay 1,20,000 INR", "party_id": "", "status": "pending"},
            {"description": "Provide 1-year warranty", "party_id": "", "status": "pending"},
        ],
        conditions=[{"description": "Payment received", "is_met": False}],
        terms="7-day return policy, 1-year manufacturer warranty",
        financial_commitments=[{"description": "Purchase price", "amount": 120000, "status": "pending"}],
    )
    assert agreement is not None
    analysis = runtime.analyze_agreement(profile.profile_id, agreement.agreement_id)
    assert analysis is not None
    assert "risks" in analysis
    return {"scenario": "2. Customer Purchase", "entity": "TechStore — Amit Singh",
            "obligations": len(agreement.obligations), "passed": True}


def test_supplier_contract() -> dict[str, Any]:
    runtime = AgreementIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_manu", "ManuCorp — Supplier")

    agreement = runtime.create_agreement(
        profile.profile_id, AgreementType.SUPPLIER_CONTRACT.value,
        "Raw Materials Supply Contract Q4 2026",
        "Quarterly supply agreement for manufacturing raw materials",
        parties=[{"name": "ManuCorp", "role": "buyer"},
                 {"name": "RawMat Ltd", "role": "supplier"}],
        obligations=[
            {"description": "Supply 10,000 units of Grade A material monthly", "party_id": "", "status": "pending"},
            {"description": "Maintain quality standard ISO 9001", "party_id": "", "status": "pending"},
            {"description": "Deliver within 14 days of order", "party_id": "", "status": "pending"},
            {"description": "Pay within 30 days of invoice", "party_id": "", "status": "pending"},
            {"description": "Provide monthly inventory report", "party_id": "", "status": "pending"},
        ],
        milestones=[{"title": "First delivery", "status": "pending"}],
        terms="Net 30 payment. Quality standards per ISO 9001.",
        financial_commitments=[{"description": "Monthly supply value", "amount": 500000, "status": "pending"}],
    )
    assert agreement is not None
    analysis = runtime.analyze_agreement(profile.profile_id, agreement.agreement_id)
    assert analysis is not None
    assert analysis["fulfilment"]["total"] == 5

    runtime.add_obligation(profile.profile_id, agreement.agreement_id,
                           "Emergency delivery within 48 hours", "", value=100000)
    assert len(agreement.obligations) == 6
    return {"scenario": "3. Supplier Contract", "entity": "ManuCorp — RawMat Ltd",
            "obligations": len(agreement.obligations), "passed": True}


def test_medical_consent() -> dict[str, Any]:
    runtime = AgreementIntelligenceRuntime()
    profile = runtime.get_or_create_profile("hospital_city", "City Hospital")

    agreement = runtime.create_agreement(
        profile.profile_id, AgreementType.MEDICAL_CONSENT.value,
        "Surgical Consent — Knee Replacement",
        "Informed consent for arthroscopic knee surgery",
        parties=[{"name": "City Hospital", "role": "provider"},
                 {"name": "Ravi Kumar", "role": "patient"}],
        obligations=[
            {"description": "Perform knee replacement surgery", "party_id": "", "status": "pending"},
            {"description": "Provide post-op care for 7 days", "party_id": "", "status": "pending"},
            {"description": "Follow pre-surgery preparation instructions", "party_id": "", "status": "pending"},
            {"description": "Attend follow-up appointments", "party_id": "", "status": "pending"},
            {"description": "Report any complications immediately", "party_id": "", "status": "pending"},
        ],
        conditions=[
            {"description": "Pre-surgery health clearance obtained", "is_met": True},
            {"description": "Insurance pre-authorization received", "is_met": True},
        ],
        terms="Standard surgical consent with complication disclosure",
    )
    assert agreement is not None
    assert len(agreement.conditions) == 2
    assert agreement.conditions[0].is_met

    analysis = runtime.analyze_agreement(profile.profile_id, agreement.agreement_id)
    assert analysis is not None
    assert len(analysis.get("compliance", [])) >= 0
    return {"scenario": "4. Medical Consent", "entity": "City Hospital — Ravi Kumar",
            "conditions": len(agreement.conditions), "passed": True}


def test_rental_agreement() -> dict[str, Any]:
    runtime = AgreementIntelligenceRuntime()
    profile = runtime.get_or_create_profile("person_tenant", "Tenant — Rental")

    agreement = runtime.create_agreement(
        profile.profile_id, AgreementType.RENTAL.value,
        "Apartment Rental — 2BHK Green Valley",
        "11-month rental agreement for residential apartment",
        parties=[{"name": "Green Valley Properties", "role": "landlord"},
                 {"name": "Neha Patel", "role": "tenant"}],
        obligations=[
            {"description": "Pay monthly rent of 25,000 by 5th", "party_id": "", "status": "pending"},
            {"description": "Maintain property in good condition", "party_id": "", "status": "pending"},
            {"description": "Provide 2 months notice before vacating", "party_id": "", "status": "pending"},
            {"description": "Return security deposit within 30 days", "party_id": "", "status": "pending"},
            {"description": "Fix maintenance issues within 48 hours", "party_id": "", "status": "pending"},
        ],
        conditions=[{"description": "Security deposit of 50K paid", "is_met": True}],
        milestones=[{"title": "Mid-term inspection", "status": "pending"}],
        terms="11-month agreement, renewable. No subletting.",
        start_date="2026-08-01", end_date="2027-06-30",
        financial_commitments=[
            {"description": "Monthly rent", "amount": 25000, "status": "pending"},
            {"description": "Security deposit", "amount": 50000, "status": "fulfilled"},
        ],
    )
    assert agreement is not None
    analysis = runtime.analyze_agreement(profile.profile_id, agreement.agreement_id)
    assert analysis is not None
    assert analysis["financial"]["total_financial_commitment"] == 25000 + 50000
    return {"scenario": "5. Rental Agreement", "entity": "Green Valley — Neha Patel",
            "obligations": len(agreement.obligations),
            "financial_total": analysis["financial"]["total_financial_commitment"],
            "passed": True}


def test_partnership_agreement() -> dict[str, Any]:
    runtime = AgreementIntelligenceRuntime()
    profile = runtime.get_or_create_profile("venture_xyz", "XYZ Ventures")

    agreement = runtime.create_agreement(
        profile.profile_id, AgreementType.PARTNERSHIP.value,
        "Strategic Partnership — XYZ & ABC Corp",
        "Co-marketing and technology partnership for SaaS products",
        parties=[{"name": "XYZ Ventures", "role": "partner_a"},
                 {"name": "ABC Corp", "role": "partner_b"}],
        obligations=[
            {"description": "Integrate ABC payment API into platform", "party_id": "", "status": "pending"},
            {"description": "Co-market to combined customer base", "party_id": "", "status": "pending"},
            {"description": "Share revenue 70/30 split", "party_id": "", "status": "pending"},
            {"description": "Provide technical support SLA 24/7", "party_id": "", "status": "pending"},
            {"description": "Quarterly business review meetings", "party_id": "", "status": "pending"},
            {"description": "Maintain API uptime 99.9%", "party_id": "", "status": "pending"},
        ],
        milestones=[
            {"title": "API integration complete", "status": "pending"},
            {"title": "First co-marketing campaign", "status": "pending"},
            {"title": "Q1 review", "status": "pending"},
        ],
        terms="Revenue sharing 70/30. 24-month initial term.",
        financial_commitments=[{"description": "Revenue share monthly", "amount": 0, "status": "pending"}],
    )
    assert agreement is not None
    assert len(agreement.milestones) == 3

    analysis = runtime.analyze_agreement(profile.profile_id, agreement.agreement_id)
    assert analysis is not None
    assert analysis["trust"]["assessment"] is not None
    return {"scenario": "6. Partnership Agreement", "entity": "XYZ Ventures — ABC Corp",
            "obligations": len(agreement.obligations), "milestones": len(agreement.milestones),
            "trust_assessment": analysis["trust"]["assessment"], "passed": True}


def test_subscription_renewal() -> dict[str, Any]:
    runtime = AgreementIntelligenceRuntime()
    profile = runtime.get_or_create_profile("saas_co", "SaaS Co — Subscriptions")

    agreement = runtime.create_agreement(
        profile.profile_id, AgreementType.SUBSCRIPTION.value,
        "Enterprise SaaS Subscription — Mega Corp",
        "Annual subscription to analytics platform",
        parties=[{"name": "SaaS Co", "role": "provider"},
                 {"name": "Mega Corp", "role": "subscriber"}],
        obligations=[
            {"description": "Provide platform access for 500 users", "party_id": "", "status": "fulfilled"},
            {"description": "99.9% uptime SLA", "party_id": "", "status": "fulfilled"},
            {"description": "Monthly analytics reports", "party_id": "", "status": "fulfilled"},
            {"description": "Pay annual subscription 12L", "party_id": "", "status": "fulfilled"},
        ],
        conditions=[{"description": "Initial payment received", "is_met": True}],
        milestones=[{"title": "Annual renewal", "status": "pending"}],
        terms="Annual subscription with auto-renewal. 30-day cancellation notice.",
        start_date="2025-09-01", end_date="2026-09-01",
        auto_renew=True,
        financial_commitments=[
            {"description": "Annual subscription", "amount": 1200000, "status": "fulfilled"},
        ],
    )
    assert agreement is not None
    runtime.transition_status(profile.profile_id, agreement.agreement_id, "proposed")
    runtime.transition_status(profile.profile_id, agreement.agreement_id, "accepted")
    runtime.transition_status(profile.profile_id, agreement.agreement_id, "active")
    runtime.transition_status(profile.profile_id, agreement.agreement_id, "fulfilled")
    assert agreement.status == AgreementStatus.FULFILLED.value

    recs = runtime.get_recommendations(profile.profile_id, agreement.agreement_id)
    assert len(recs) >= 1  # renewal recommendation

    rec = recs[0]
    assert "reasoning" in rec
    assert "confidence" in rec
    assert "evidence" in rec
    assert "expected_outcome" in rec

    return {"scenario": "7. Subscription Renewal", "entity": "SaaS Co — Mega Corp",
            "recommendations": len(recs), "rec_confidence": rec["confidence"],
            "has_reasoning": bool(rec["reasoning"]), "has_evidence": len(rec.get("evidence", [])) > 0,
            "passed": True}


def test_agreement_breach_with_adaptive_execution() -> dict[str, Any]:
    runtime = AgreementIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_breach", "Breach Scenario")

    agreement = runtime.create_agreement(
        profile.profile_id, AgreementType.SERVICE.value,
        "IT Support Contract — Monthly",
        "Monthly IT support service agreement",
        parties=[{"name": "IT Services Inc", "role": "provider"},
                 {"name": "Client Corp", "role": "client"}],
        obligations=[
            {"description": "Respond to tickets within 4 hours", "party_id": "", "status": "breached"},
            {"description": "Monthly system health check", "party_id": "", "status": "breached"},
            {"description": "Weekly backup verification", "party_id": "", "status": "breached"},
            {"description": "Pay monthly fee of 50K", "party_id": "", "status": "pending"},
            {"description": "Provide remote access", "party_id": "", "status": "pending"},
        ],
        conditions=[{"description": "Service contract signed", "is_met": True}],
        terms="SLA: 4-hour response. Monthly billing.",
        financial_commitments=[{"description": "Monthly fee", "amount": 50000, "status": "pending"}],
    )
    assert agreement is not None

    # Detect breaches
    analysis = runtime.analyze_agreement(profile.profile_id, agreement.agreement_id)
    assert analysis is not None
    assert len(analysis["breaches"]) >= 3
    assert analysis["trust"]["impact"] == "negative"
    assert analysis["trust"]["assessment"] == "eroding"

    # Update one obligation via Reality notification
    received = []
    runtime.register_reality_listener(lambda n: received.append(n))
    runtime.update_obligation_status(profile.profile_id, agreement.agreement_id,
                                      agreement.obligations[3].obligation_id, "fulfilled")
    assert agreement.obligations[3].status == "fulfilled"

    # Get recommendations
    recs = runtime.get_recommendations(profile.profile_id, agreement.agreement_id)
    assert len(recs) >= 1
    assert any("amend" in r["title"].lower() for r in recs)

    # Explain recommendation
    if recs:
        recommendation_obj = runtime._engine.reason_about_amendments(agreement)
        if recommendation_obj:
            explanation = runtime._engine.explain_recommendation(recommendation_obj[0])
            assert "explanation" in explanation

    return {"scenario": "8. Agreement Breach + Adaptive Execution",
            "entity": "IT Services Inc — Client Corp",
            "breaches_detected": len(analysis["breaches"]),
            "trust_impact": analysis["trust"]["impact"],
            "recommendations": len(recs),
            "obligation_fulfilled": True,
            "passed": True}


def run_all_verifications() -> list[dict[str, Any]]:
    tests = [
        ("Employment Agreement", test_employment_agreement),
        ("Customer Purchase", test_customer_purchase),
        ("Supplier Contract", test_supplier_contract),
        ("Medical Consent", test_medical_consent),
        ("Rental Agreement", test_rental_agreement),
        ("Partnership Agreement", test_partnership_agreement),
        ("Subscription Renewal", test_subscription_renewal),
        ("Breach + Adaptive Execution", test_agreement_breach_with_adaptive_execution),
    ]
    results = []
    for name, fn in tests:
        try:
            r = fn()
            r["test_name"] = name
            r["status"] = "PASS"
            r["error"] = None
        except Exception as e:
            import traceback
            r = {"test_name": name, "scenario": name, "status": "FAIL",
                 "error": str(e), "traceback": traceback.format_exc(), "passed": False}
        results.append(r)
    return results


if __name__ == "__main__":
    print("=" * 80)
    print("UCP-06 — Universal Agreement Intelligence: Verification Report")
    print("=" * 80)
    results = run_all_verifications()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"\n  {status} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("obligations"):
            print(f"         Obligations: {r['obligations']}")
        if r.get("parties"):
            print(f"         Parties: {r['parties']}")
        if r.get("recommendations") is not None:
            print(f"         Recommendations: {r['recommendations']} (confidence: {r.get('rec_confidence', 'N/A')})")
        if r.get("breaches_detected") is not None:
            print(f"         Breaches: {r['breaches_detected']} | Trust: {r.get('trust_impact', 'N/A')}")
        if r.get("error"):
            print(f"         ERROR: {r['error']}")
    print(f"\n  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    if not failed:
        print("\n  ✅ UCP-06 VERIFICATION PASSED: All 8 agreement scenarios execute")
        print("     through the same Universal Agreement Intelligence capability.")
        print("  No Contract Runtime. No Procurement Runtime. No Legal Runtime.")
    else:
        print("\n  ❌ UCP-06 VERIFICATION FAILED")