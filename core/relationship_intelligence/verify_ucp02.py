"""UCP-02 Verification — Universal Relationship Intelligence.

Verifies that all 7 relationship types execute through the same capability:
1. Personal relationships
2. Business relationships
3. Family relationships
4. Healthcare relationships
5. Educational relationships
6. Supplier relationships
7. Investor relationships

Each demonstration uses the same RelationshipIntelligenceRuntime.
No CRM module. No HR module. No Customer Success module.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from core.relationship_intelligence import (
    RelationshipIntelligenceRuntime,
    RelationshipProfile,
    TrustLevel,
    SentimentTrend,
    RelationshipRole,
    CommitmentStatus,
)


def _days_ago(days: int) -> str:
    """Return an ISO timestamp *days* ago."""
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat().replace("+00:00", "Z")


# ═══════════════════════════════════════════════════════════════════════════
# 1. PERSONAL RELATIONSHIP
# ═══════════════════════════════════════════════════════════════════════════

def test_personal_relationship() -> dict[str, Any]:
    """Demonstrate personal friendship relationship intelligence."""
    runtime = RelationshipIntelligenceRuntime()

    # Create a personal friendship profile
    profile = runtime.get_or_create_profile(
        source_id="person_alice",
        target_id="person_bob",
        role=RelationshipRole.FRIEND.value,
        label="Alice and Bob — lifelong friends",
    )

    # Record communication history
    runtime.record_communication(
        profile.profile_id,
        channel="message",
        direction="bidirectional",
        subject="Weekend plans",
        summary="Alice and Bob discussed meeting for coffee this weekend",
        sentiment_score=0.8,
        occurred_at=_days_ago(2),
    )
    runtime.record_communication(
        profile.profile_id,
        channel="call",
        direction="bidirectional",
        subject="Catch up call",
        summary="Long catch-up call about recent life updates",
        sentiment_score=0.9,
        duration_minutes=45,
        occurred_at=_days_ago(14),
    )

    # Record sentiment
    runtime.record_sentiment(profile.profile_id, score=0.85, source="human_feedback",
                             context="Alice feels very positive about Bob")

    # Add shared journey
    runtime.add_journey(
        profile.profile_id,
        name="Friendship journey",
        phase="mature",
        description="10+ years of friendship through school and careers",
        milestones=[{"name": "Met in college", "year": "2015"},
                    {"name": "Started business together", "year": "2020"}],
    )

    # Add shared commitments (simple promises)
    runtime.add_commitment(
        profile.profile_id,
        title="Help with move",
        description="Bob promised to help Alice move apartments",
        commitment_type="promise",
        due_date=_days_ago(-30),  # 30 days from now
    )

    # Assess health
    health = runtime.assess_relationship_health(profile.profile_id)
    trust = runtime.compute_trust(profile.profile_id)
    recs = runtime.get_recommendations(profile.profile_id)

    assert profile is not None
    assert health is not None
    assert trust is not None
    assert len(profile.communications) == 2
    assert trust.score > 0.3  # cautious trust for early-stage friendship

    return {
        "type": "Personal (Friend)",
        "entities": "Alice ↔ Bob",
        "profile_id": profile.profile_id,
        "trust_level": trust.level.value,
        "trust_score": trust.score,
        "health_score": health["overall_score"],
        "risk_level": health["risk_level"],
        "trend": health["trend"],
        "communications": len(profile.communications),
        "sentiments": len(profile.sentiment_history),
        "journeys": len(profile.journeys),
        "commitments": len(profile.commitments),
        "recommendations": len(recs),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. BUSINESS RELATIONSHIP (Customer)
# ═══════════════════════════════════════════════════════════════════════════

def test_business_relationship() -> dict[str, Any]:
    """Demonstrate business customer relationship intelligence."""
    runtime = RelationshipIntelligenceRuntime()

    profile = runtime.get_or_create_profile(
        source_id="org_acme_corp",
        target_id="person_jane",
        role=RelationshipRole.CUSTOMER.value,
        label="Acme Corp — Jane (Enterprise Customer)",
    )

    # Business communications
    runtime.record_communication(profile.profile_id, channel="email", direction="outbound",
        subject="Quarterly business review", summary="Q3 performance review meeting",
        sentiment_score=0.7, occurred_at=_days_ago(5))
    runtime.record_communication(profile.profile_id, channel="meeting", direction="bidirectional",
        subject="Product roadmap discussion", summary="Discussed upcoming features and timeline",
        sentiment_score=0.6, duration_minutes=60, occurred_at=_days_ago(12))
    runtime.record_communication(profile.profile_id, channel="email", direction="inbound",
        subject="Support ticket: feature request", summary="Jane requested new integration",
        sentiment_score=0.4, occurred_at=_days_ago(3))

    # Business commitments (deals, SLAs)
    runtime.add_commitment(profile.profile_id, title="Enterprise license renewal",
        description="Annual renewal of enterprise license", commitment_type="contract",
        due_date=_days_ago(-45), value="$50,000")
    runtime.add_commitment(profile.profile_id, title="Integration delivery",
        description="Deliver API integration for Jane's team", commitment_type="agreement",
        due_date=_days_ago(-60))

    # Fulfill one commitment
    runtime.update_commitment_status(profile.profile_id, profile.commitments[0].commitment_id,
        "fulfilled", fulfilled_date=_days_ago(10))

    # Business journey
    runtime.add_journey(profile.profile_id, name="Customer lifecycle",
        phase="growth", description="Enterprise customer journey from trial to expansion",
        milestones=[{"name": "Signed trial", "date": "2025-01"},
                    {"name": "Converted to paid", "date": "2025-03"},
                    {"name": "Expanded license", "date": "2025-09"}])

    # Sentiment
    runtime.record_sentiment(profile.profile_id, score=0.6, source="ai_analysis",
        context="Generally positive but recent support ticket shows frustration")
    runtime.record_sentiment(profile.profile_id, score=0.7, source="ai_analysis",
        context="QBR meeting was productive and positive")

    # Shared documents
    runtime.add_document(profile.profile_id, title="Q3 Business Review Deck",
        doc_type="presentation", url="/docs/q3-review.pdf", shared_by="acme_sales")

    # Assess
    health = runtime.assess_relationship_health(profile.profile_id)
    trust = runtime.compute_trust(profile.profile_id)
    recs = runtime.get_recommendations(profile.profile_id)

    assert trust.score > 0.3
    assert len(profile.commitments) == 2

    return {
        "type": "Business (Customer)",
        "entities": "Acme Corp ↔ Jane",
        "profile_id": profile.profile_id,
        "trust_level": trust.level.value,
        "trust_score": trust.score,
        "health_score": health["overall_score"],
        "risk_level": health["risk_level"],
        "trend": health["trend"],
        "communications": len(profile.communications),
        "sentiments": len(profile.sentiment_history),
        "journeys": len(profile.journeys),
        "commitments": len(profile.commitments),
        "documents": len(profile.documents),
        "recommendations": len(recs),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. FAMILY RELATIONSHIP
# ═══════════════════════════════════════════════════════════════════════════

def test_family_relationship() -> dict[str, Any]:
    """Demonstrate family relationship intelligence."""
    runtime = RelationshipIntelligenceRuntime()

    profile = runtime.get_or_create_profile(
        source_id="person_sarah",
        target_id="person_mike",
        role=RelationshipRole.FAMILY.value,
        label="Sarah and Mike — siblings",
    )

    # Family communications
    runtime.record_communication(profile.profile_id, channel="call", direction="bidirectional",
        subject="Weekly family call", summary="Regular check-in about family matters",
        sentiment_score=0.9, duration_minutes=30, occurred_at=_days_ago(1))
    runtime.record_communication(profile.profile_id, channel="message", direction="bidirectional",
        subject="Holiday plans", summary="Coordinating holiday travel plans",
        sentiment_score=0.8, occurred_at=_days_ago(7))

    # Family commitments
    runtime.add_commitment(profile.profile_id, title="Pick up groceries",
        description="Mike promised to pick up groceries for family dinner",
        commitment_type="promise", due_date=_days_ago(-3))
    runtime.update_commitment_status(profile.profile_id, profile.commitments[0].commitment_id,
        "fulfilled", fulfilled_date=_days_ago(2))

    # Family journey
    runtime.add_journey(profile.profile_id, name="Family history",
        phase="mature", description="Growing up together",
        milestones=[{"name": "Childhood", "years": "1990-2005"},
                    {"name": "College years", "years": "2005-2009"},
                    {"name": "Adult lives", "years": "2010-present"}])

    # Sentiment
    runtime.record_sentiment(profile.profile_id, score=0.95, source="human_feedback",
        context="Sarah feels very close to her brother")
    runtime.record_sentiment(profile.profile_id, score=0.85, source="human_feedback",
        context="Mike appreciates Sarah's support")

    # Shared creative assets
    runtime.add_creative_asset(profile.profile_id, title="Family photo album",
        asset_type="photo_collection", url="/family/photos/2025",
        contributors=["sarah", "mike"])

    health = runtime.assess_relationship_health(profile.profile_id)
    trust = runtime.compute_trust(profile.profile_id)
    recs = runtime.get_recommendations(profile.profile_id)

    assert trust.score > 0.5
    assert health["overall_score"] > 0.5

    return {
        "type": "Family (Siblings)",
        "entities": "Sarah ↔ Mike",
        "profile_id": profile.profile_id,
        "trust_level": trust.level.value,
        "trust_score": trust.score,
        "health_score": health["overall_score"],
        "risk_level": health["risk_level"],
        "trend": health["trend"],
        "communications": len(profile.communications),
        "sentiments": len(profile.sentiment_history),
        "journeys": len(profile.journeys),
        "commitments": len(profile.commitments),
        "creative_assets": len(profile.creative_assets),
        "recommendations": len(recs),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. HEALTHCARE RELATIONSHIP
# ═══════════════════════════════════════════════════════════════════════════

def test_healthcare_relationship() -> dict[str, Any]:
    """Demonstrate healthcare relationship intelligence."""
    runtime = RelationshipIntelligenceRuntime()

    profile = runtime.get_or_create_profile(
        source_id="person_patient",
        target_id="person_dr_wilson",
        role=RelationshipRole.DOCTOR.value,
        label="Patient — Dr. Wilson (Primary Care)",
    )

    # Healthcare interactions
    runtime.record_communication(profile.profile_id, channel="visit", direction="bidirectional",
        subject="Annual checkup", summary="Routine annual physical examination",
        sentiment_score=0.7, duration_minutes=30, occurred_at=_days_ago(30))
    runtime.record_communication(profile.profile_id, channel="visit", direction="bidirectional",
        subject="Follow-up appointment", summary="Follow-up on blood test results",
        sentiment_score=0.6, duration_minutes=20, occurred_at=_days_ago(7))
    runtime.record_communication(profile.profile_id, channel="message", direction="inbound",
        subject="Prescription refill request", summary="Requested prescription refill via portal",
        sentiment_score=0.5, occurred_at=_days_ago(2))

    # Healthcare commitments (care plans, follow-ups)
    runtime.add_commitment(profile.profile_id, title="Blood test follow-up",
        description="Patient to complete blood work and return for results",
        commitment_type="care_plan", due_date=_days_ago(-14))
    runtime.update_commitment_status(profile.profile_id, profile.commitments[0].commitment_id,
        "fulfilled", fulfilled_date=_days_ago(7))

    runtime.add_commitment(profile.profile_id, title="Medication adherence",
        description="Patient committed to daily medication schedule",
        commitment_type="care_plan", due_date=_days_ago(-90))

    # Healthcare journey
    runtime.add_journey(profile.profile_id, name="Patient care journey",
        phase="active", description="Ongoing primary care relationship",
        milestones=[{"name": "First visit", "date": "2024-01"},
                    {"name": "Health assessment", "date": "2024-06"},
                    {"name": "Treatment plan established", "date": "2024-09"}])

    # Sentiment
    runtime.record_sentiment(profile.profile_id, score=0.65, source="human_feedback",
        context="Patient feels comfortable with Dr. Wilson")
    runtime.record_sentiment(profile.profile_id, score=0.7, source="ai_analysis",
        context="Communication is professional and caring")

    health = runtime.assess_relationship_health(profile.profile_id)
    trust = runtime.compute_trust(profile.profile_id)
    recs = runtime.get_recommendations(profile.profile_id)

    assert trust.score > 0.3
    assert health["overall_score"] > 0.0

    return {
        "type": "Healthcare (Doctor-Patient)",
        "entities": "Patient ↔ Dr. Wilson",
        "profile_id": profile.profile_id,
        "trust_level": trust.level.value,
        "trust_score": trust.score,
        "health_score": health["overall_score"],
        "risk_level": health["risk_level"],
        "trend": health["trend"],
        "communications": len(profile.communications),
        "sentiments": len(profile.sentiment_history),
        "journeys": len(profile.journeys),
        "commitments": len(profile.commitments),
        "recommendations": len(recs),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. EDUCATIONAL RELATIONSHIP
# ═══════════════════════════════════════════════════════════════════════════

def test_educational_relationship() -> dict[str, Any]:
    """Demonstrate educational relationship intelligence."""
    runtime = RelationshipIntelligenceRuntime()

    # Create a student-teacher relationship
    profile = runtime.get_or_create_profile(
        source_id="person_student",
        target_id="person_prof_kumar",
        role=RelationshipRole.STUDENT.value,
        label="Student — Prof. Kumar (Mentor)",
    )

    # Educational interactions
    runtime.record_communication(profile.profile_id, channel="meeting", direction="bidirectional",
        subject="Office hours — thesis guidance",
        summary="Student attended office hours for thesis research guidance",
        sentiment_score=0.8, duration_minutes=45, occurred_at=_days_ago(3))
    runtime.record_communication(profile.profile_id, channel="email", direction="bidirectional",
        subject="Thesis draft review",
        summary="Prof. Kumar reviewed and provided feedback on thesis draft",
        sentiment_score=0.75, occurred_at=_days_ago(10))
    runtime.record_communication(profile.profile_id, channel="meeting", direction="bidirectional",
        subject="Research methodology discussion",
        summary="Discussed research methodology and data collection approach",
        sentiment_score=0.85, duration_minutes=60, occurred_at=_days_ago(21))

    # Educational commitments
    runtime.add_commitment(profile.profile_id, title="Thesis submission deadline",
        description="Student to submit final thesis by end of semester",
        commitment_type="academic", due_date=_days_ago(-60))
    runtime.add_commitment(profile.profile_id, title="Reference letter",
        description="Prof. Kumar agreed to write reference letter for PhD applications",
        commitment_type="academic", due_date=_days_ago(-30))

    # Educational journey
    runtime.add_journey(profile.profile_id, name="Academic mentorship",
        phase="growth", description="Master's thesis supervision and mentorship",
        milestones=[{"name": "Started supervision", "date": "2025-09"},
                    {"name": "Thesis proposal approved", "date": "2025-11"},
                    {"name": "Research completed", "date": "2026-03"}])

    # Shared documents
    runtime.add_document(profile.profile_id, title="Master's Thesis Draft v3",
        doc_type="thesis", url="/docs/thesis-draft-v3.pdf",
        shared_by="student", shared_with=["prof_kumar"])
    runtime.add_document(profile.profile_id, title="Research Paper — Co-authored",
        doc_type="publication", url="/papers/research-2026.pdf",
        shared_by="prof_kumar", shared_with=["student"])

    # Sentiment
    runtime.record_sentiment(profile.profile_id, score=0.85, source="human_feedback",
        context="Student feels well-supported in research journey")
    runtime.record_sentiment(profile.profile_id, score=0.8, source="human_feedback",
        context="Prof. Kumar impressed by student's progress")

    health = runtime.assess_relationship_health(profile.profile_id)
    trust = runtime.compute_trust(profile.profile_id)
    recs = runtime.get_recommendations(profile.profile_id)

    assert trust.score > 0.4  # cautious trust for mentorship relationship
    assert len(profile.documents) == 2

    return {
        "type": "Educational (Student-Teacher)",
        "entities": "Student ↔ Prof. Kumar",
        "profile_id": profile.profile_id,
        "trust_level": trust.level.value,
        "trust_score": trust.score,
        "health_score": health["overall_score"],
        "risk_level": health["risk_level"],
        "trend": health["trend"],
        "communications": len(profile.communications),
        "sentiments": len(profile.sentiment_history),
        "journeys": len(profile.journeys),
        "commitments": len(profile.commitments),
        "documents": len(profile.documents),
        "recommendations": len(recs),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 6. SUPPLIER RELATIONSHIP
# ═══════════════════════════════════════════════════════════════════════════

def test_supplier_relationship() -> dict[str, Any]:
    """Demonstrate supplier relationship intelligence."""
    runtime = RelationshipIntelligenceRuntime()

    profile = runtime.get_or_create_profile(
        source_id="org_our_company",
        target_id="org_raw_materials_inc",
        role=RelationshipRole.SUPPLIER.value,
        label="Our Company — Raw Materials Inc (Key Supplier)",
    )

    # Supply chain communications
    runtime.record_communication(profile.profile_id, channel="email", direction="bidirectional",
        subject="Q4 supply agreement", summary="Negotiating Q4 supply terms and pricing",
        sentiment_score=0.6, occurred_at=_days_ago(5))
    runtime.record_communication(profile.profile_id, channel="meeting", direction="bidirectional",
        subject="Quarterly supplier review", summary="Performance review meeting with supplier",
        sentiment_score=0.7, duration_minutes=45, occurred_at=_days_ago(15))
    runtime.record_communication(profile.profile_id, channel="email", direction="outbound",
        subject="Urgent: Supply shortage alert",
        summary="Alerted about potential supply chain disruption",
        sentiment_score=0.3, occurred_at=_days_ago(2))

    # Supplier commitments (purchase orders, contracts)
    runtime.add_commitment(profile.profile_id, title="Raw material PO #3847",
        description="Purchase order for 10,000 units of raw material",
        commitment_type="purchase_order", due_date=_days_ago(-20), value="$250,000")
    runtime.update_commitment_status(profile.profile_id, profile.commitments[0].commitment_id,
        "fulfilled", fulfilled_date=_days_ago(-15))

    runtime.add_commitment(profile.profile_id, title="Annual supply contract",
        description="Annual contract for raw material supply",
        commitment_type="contract", due_date=_days_ago(-90))
    runtime.add_commitment(profile.profile_id, title="Expedited shipment",
        description="Supplier agreed to expedite critical shipment",
        commitment_type="agreement", due_date=_days_ago(-7))
    runtime.update_commitment_status(profile.profile_id, profile.commitments[2].commitment_id,
        "fulfilled", fulfilled_date=_days_ago(-6))

    # Supplier journey
    runtime.add_journey(profile.profile_id, name="Supplier relationship",
        phase="mature", description="5-year strategic supplier partnership",
        milestones=[{"name": "Contract signed", "date": "2021-01"},
                    {"name": "Volume increased 3x", "date": "2023-06"},
                    {"name": "Strategic partnership", "date": "2025-01"}])

    # Sentiment
    runtime.record_sentiment(profile.profile_id, score=0.5, source="ai_analysis",
        context="Overall positive but recent supply alert created tension")

    health = runtime.assess_relationship_health(profile.profile_id)
    trust = runtime.compute_trust(profile.profile_id)
    recs = runtime.get_recommendations(profile.profile_id)

    assert trust.score > 0.3
    assert len(profile.commitments) == 3

    return {
        "type": "Supplier (Business)",
        "entities": "Our Company ↔ Raw Materials Inc",
        "profile_id": profile.profile_id,
        "trust_level": trust.level.value,
        "trust_score": trust.score,
        "health_score": health["overall_score"],
        "risk_level": health["risk_level"],
        "trend": health["trend"],
        "communications": len(profile.communications),
        "sentiments": len(profile.sentiment_history),
        "journeys": len(profile.journeys),
        "commitments": len(profile.commitments),
        "recommendations": len(recs),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 7. INVESTOR RELATIONSHIP
# ═══════════════════════════════════════════════════════════════════════════

def test_investor_relationship() -> dict[str, Any]:
    """Demonstrate investor relationship intelligence."""
    runtime = RelationshipIntelligenceRuntime()

    profile = runtime.get_or_create_profile(
        source_id="org_startup",
        target_id="person_vc_partner",
        role=RelationshipRole.INVESTOR.value,
        label="Startup — VC Partner (Lead Investor)",
    )

    # Investor communications
    runtime.record_communication(profile.profile_id, channel="meeting", direction="bidirectional",
        subject="Monthly board meeting", summary="Board meeting with investor updates",
        sentiment_score=0.7, duration_minutes=90, occurred_at=_days_ago(10))
    runtime.record_communication(profile.profile_id, channel="email", direction="inbound",
        subject="Due diligence materials", summary="Requested additional DD documents",
        sentiment_score=0.5, occurred_at=_days_ago(20))
    runtime.record_communication(profile.profile_id, channel="meeting", direction="bidirectional",
        subject="Strategic review", summary="Q3 strategic review and growth planning",
        sentiment_score=0.8, duration_minutes=60, occurred_at=_days_ago(45))
    runtime.record_communication(profile.profile_id, channel="message", direction="outbound",
        subject="Monthly metrics update", summary="Shared monthly KPI dashboard",
        sentiment_score=0.75, occurred_at=_days_ago(3))

    # Investor commitments
    runtime.add_commitment(profile.profile_id, title="Series A investment",
        description="$2M Series A investment commitment",
        commitment_type="investment", due_date=_days_ago(-180), value="$2,000,000")
    runtime.update_commitment_status(profile.profile_id, profile.commitments[0].commitment_id,
        "fulfilled", fulfilled_date=_days_ago(-150))

    runtime.add_commitment(profile.profile_id, title="Revenue milestone",
        description="Startup committed to $5M ARR by Q4",
        commitment_type="milestone", due_date=_days_ago(-90))

    # Investor journey
    runtime.add_journey(profile.profile_id, name="Investment journey",
        phase="growth", description="From first meeting to post-investment partnership",
        milestones=[{"name": "First meeting", "date": "2025-06"},
                    {"name": "Term sheet signed", "date": "2025-08"},
                    {"name": "Series A closed", "date": "2025-10"},
                    {"name": "First board meeting", "date": "2025-11"}])

    # Shared documents
    runtime.add_document(profile.profile_id, title="Series A Pitch Deck",
        doc_type="presentation", url="/investor/series-a-deck.pdf",
        shared_by="startup", shared_with=["vc_partner"])
    runtime.add_document(profile.profile_id, title="Monthly Board Report — Oct",
        doc_type="report", url="/investor/board-report-oct.pdf",
        shared_by="startup", shared_with=["vc_partner"])

    # Sentiment
    runtime.record_sentiment(profile.profile_id, score=0.75, source="ai_analysis",
        context="Investor is confident in startup's trajectory")
    runtime.record_sentiment(profile.profile_id, score=0.65, source="ai_analysis",
        context="Some concern about revenue milestone timeline")

    health = runtime.assess_relationship_health(profile.profile_id)
    trust = runtime.compute_trust(profile.profile_id)
    recs = runtime.get_recommendations(profile.profile_id)

    assert trust.score > 0.4
    assert len(profile.documents) == 2

    return {
        "type": "Investor (Startup-VC)",
        "entities": "Startup ↔ VC Partner",
        "profile_id": profile.profile_id,
        "trust_level": trust.level.value,
        "trust_score": trust.score,
        "health_score": health["overall_score"],
        "risk_level": health["risk_level"],
        "trend": health["trend"],
        "communications": len(profile.communications),
        "sentiments": len(profile.sentiment_history),
        "journeys": len(profile.journeys),
        "commitments": len(profile.commitments),
        "documents": len(profile.documents),
        "recommendations": len(recs),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Reality Integration Test
# ═══════════════════════════════════════════════════════════════════════════

def test_reality_integration() -> dict[str, Any]:
    """Demonstrate Reality integration via notify(notification)."""
    runtime = RelationshipIntelligenceRuntime()

    profile = runtime.get_or_create_profile(
        source_id="entity_a",
        target_id="entity_b",
        role="partner",
    )

    # Simulate Reality notifications arriving
    received_notifications: list[dict[str, Any]] = []
    def reality_listener(notification: dict[str, Any]) -> None:
        received_notifications.append(notification)

    runtime.register_reality_listener(reality_listener)

    # Record a commitment (should fire notification)
    commitment = runtime.add_commitment(
        profile.profile_id, title="Test commitment",
        description="Testing Reality integration",
    )
    assert commitment is not None

    # Send a Reality notification about commitment fulfillment
    runtime.notify({
        "type": "execution.commitment_fulfilled",
        "profile_id": profile.profile_id,
        "commitment_id": commitment.commitment_id,
    })

    # Verify the commitment was updated
    updated_commitment = None
    for c in profile.commitments:
        if c.commitment_id == commitment.commitment_id:
            updated_commitment = c
            break
    assert updated_commitment is not None
    assert updated_commitment.status == CommitmentStatus.FULFILLED.value

    # Unknown notification types should be silently ignored
    runtime.notify({"type": "unknown.notification_type"})
    # Should not crash — that's the contract

    return {
        "type": "Reality Integration",
        "entities": "entity_a ↔ entity_b",
        "profile_id": profile.profile_id,
        "commitment_updated": updated_commitment.status == "fulfilled",
        "notifications_fired": len(received_notifications) >= 1,
        "unknown_type_ignored": True,
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Run All Verifications
# ═══════════════════════════════════════════════════════════════════════════

def run_all_verifications() -> list[dict[str, Any]]:
    """Run all 7 relationship type verifications + Reality integration."""

    tests = [
        ("Personal", test_personal_relationship),
        ("Business", test_business_relationship),
        ("Family", test_family_relationship),
        ("Healthcare", test_healthcare_relationship),
        ("Educational", test_educational_relationship),
        ("Supplier", test_supplier_relationship),
        ("Investor", test_investor_relationship),
        ("Reality Integration", test_reality_integration),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            result["test_name"] = name
            result["status"] = "PASS"
            result["error"] = None
        except Exception as e:
            result = {
                "test_name": name,
                "type": name,
                "status": "FAIL",
                "error": str(e),
                "passed": False,
            }
        results.append(result)

    return results


if __name__ == "__main__":
    print("=" * 80)
    print("UCP-02 — Universal Relationship Intelligence: Verification Report")
    print("=" * 80)
    print()

    results = run_all_verifications()

    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"  {status} | {r.get('test_name', r['type'])}")
        print(f"         Entities: {r.get('entities', 'N/A')}")
        print(f"         Trust: {r.get('trust_level', 'N/A')} ({r.get('trust_score', 'N/A')})")
        print(f"         Health: {r.get('health_score', 'N/A')} ({r.get('risk_level', 'N/A')}, {r.get('trend', 'N/A')})")
        print(f"         Comms: {r.get('communications', 0)} | Sentiments: {r.get('sentiments', 0)} | Journeys: {r.get('journeys', 0)}")
        print(f"         Commitments: {r.get('commitments', 0)} | Documents: {r.get('documents', 0)} | Creative: {r.get('creative_assets', 0)}")
        print(f"         Recommendations: {r.get('recommendations', 0)}")
        if r.get("error"):
            print(f"         ERROR: {r['error']}")
        print()

    print("-" * 80)
    print(f"  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    print()

    if not failed:
        print("  ✅ UCP-02 VERIFICATION PASSED: All relationship types execute through")
        print("     the same Universal Relationship Intelligence capability.")
        print()
        print("  No CRM runtime introduced.")
        print("  No HR runtime introduced.")
        print("  No Customer Success modules introduced.")
        print()
        print("  Every relationship type — Personal, Business, Family, Healthcare,")
        print("  Educational, Supplier, Investor — composed from the same capability.")
        print("=" * 80)
    else:
        print("  ❌ UCP-02 VERIFICATION FAILED")
        print("=" * 80)