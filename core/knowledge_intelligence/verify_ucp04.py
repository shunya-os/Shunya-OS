"""UCP-04 Verification — Universal Knowledge Intelligence.

Verifies 7 knowledge scenarios through the same capability:
1. Personal knowledge
2. Organizational SOPs
3. Research reasoning
4. Policy management
5. Contradictory knowledge detection
6. Knowledge graph construction
7. Missing knowledge recommendation

No Knowledge Runtime. No Wiki Runtime. No Note Runtime.
"""

from __future__ import annotations

from typing import Any

from core.knowledge_intelligence import (
    KnowledgeIntelligenceRuntime,
    KnowledgeType,
    KnowledgeRelationship,
    ConfidenceLevel,
    SourceType,
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. PERSONAL KNOWLEDGE
# ═══════════════════════════════════════════════════════════════════════════

def test_personal_knowledge() -> dict[str, Any]:
    """Demonstrate personal knowledge management."""
    runtime = KnowledgeIntelligenceRuntime()
    profile = runtime.get_or_create_profile("person_rita", "Rita — Personal Knowledge",
                                             domains=["personal", "cooking", "fitness"])

    # Add personal knowledge
    runtime.add_knowledge(profile.profile_id, KnowledgeType.FACT.value,
        "Best cooking temperature for eggs",
        "Low heat (medium-low) produces creamy scrambled eggs",
        summary="Use medium-low heat for creamy scrambled eggs",
        tags=["cooking", "eggs", "technique"], domain="cooking",
        source_type=SourceType.EXPERIENCE.value, source_name="Personal kitchen experiments",
        confidence_score=0.7)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.PROCEDURE.value,
        "Morning workout routine",
        "1. Warm up 5 min. 2. Strength 30 min. 3. Cardio 20 min. 4. Cool down 5 min.",
        summary="Daily 60-minute workout routine",
        tags=["fitness", "routine", "health"], domain="fitness",
        source_type=SourceType.EXPERIENCE.value,
        confidence_score=0.6)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.CONCEPT.value,
        "Mediterranean diet principle",
        "Emphasizes plant foods, healthy fats, and moderate dairy",
        summary="Healthy eating pattern based on Mediterranean foods",
        tags=["nutrition", "health", "diet"], domain="fitness",
        source_type=SourceType.RESEARCH_PAPER.value,
        source_name="Journal of Nutrition",
        confidence_score=0.8)

    # Add a question
    runtime.add_knowledge(profile.profile_id, KnowledgeType.QUESTION.value,
        "Best time to exercise for fat loss?",
        "Is morning or evening exercise better for fat loss?",
        tags=["fitness", "question"], domain="fitness",
        confidence_score=0.3)

    # Search personal knowledge
    results = runtime.search(profile.profile_id, "scrambled eggs cooking")
    assert len(results) >= 1

    # Search by tag
    fitness_results = runtime.search(profile.profile_id, "fitness", tags=["fitness"])
    assert len(fitness_results) >= 1

    # Knowledge graph
    graph = runtime.build_knowledge_graph(profile.profile_id)
    assert graph is not None
    assert graph["node_count"] >= 3

    return {
        "scenario": "1. Personal Knowledge",
        "entity": "Rita — Personal Knowledge",
        "knowledge_count": profile.total_knowledge,
        "search_results": len(results),
        "fitness_results": len(fitness_results),
        "graph_nodes": graph["node_count"],
        "graph_edges": graph["edge_count"],
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. ORGANIZATIONAL SOPs
# ═══════════════════════════════════════════════════════════════════════════

def test_organizational_sops() -> dict[str, Any]:
    """Demonstrate organizational SOP management."""
    runtime = KnowledgeIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_operations", "Operations Dept",
                                             domains=["operations", "safety", "it"])

    # SOPs
    runtime.add_knowledge(profile.profile_id, KnowledgeType.SOP.value,
        "Onboarding new employee SOP",
        "1. IT setup. 2. HR orientation. 3. Team introduction. 4. Training. 5. 90-day check-in.",
        summary="Standard procedure for onboarding new hires",
        tags=["sop", "hr", "onboarding"], domain="operations",
        source_type=SourceType.HUMAN.value, source_name="HR Department",
        confidence_score=0.9)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.SOP.value,
        "Server deployment SOP",
        "1. Backup. 2. Deploy. 3. Test. 4. Monitor. 5. Rollback plan.",
        summary="Standard deployment procedure",
        tags=["sop", "it", "deployment"], domain="operations",
        source_type=SourceType.DOCUMENT.value, source_name="IT Runbook",
        confidence_score=0.85)

    # Procedures referenced by SOPs
    runtime.add_knowledge(profile.profile_id, KnowledgeType.PROCEDURE.value,
        "IT equipment provisioning procedure",
        "Detailed steps for setting up new employee hardware including laptop, access, and accounts",
        tags=["procedure", "it", "onboarding"], domain="operations",
        source_type=SourceType.DOCUMENT.value,
        confidence_score=0.8)

    # Link SOP to procedure
    sop = runtime.get_knowledge(profile.profile_id, profile.knowledge_objects[0].knowledge_id)
    proc = runtime.get_knowledge(profile.profile_id, profile.knowledge_objects[2].knowledge_id)
    linked = runtime.link_knowledge(profile.profile_id, sop.knowledge_id, proc.knowledge_id,
                                    KnowledgeRelationship.REFERENCES.value,
                                    evidence="Onboarding SOP references IT provisioning procedure")
    assert linked

    # Search SOPs
    sop_results = runtime.search(profile.profile_id, "onboarding", types=[KnowledgeType.SOP.value])
    assert len(sop_results) >= 1

    # Source attribution
    sources = runtime.attribute_sources(profile.profile_id)
    assert sources is not None
    assert sources["source_coverage_pct"] > 0

    return {
        "scenario": "2. Organizational SOPs",
        "entity": "Operations Dept",
        "sop_count": sum(1 for k in profile.knowledge_objects if k.knowledge_type == "sop"),
        "procedure_count": sum(1 for k in profile.knowledge_objects if k.knowledge_type == "procedure"),
        "sop_search_results": len(sop_results),
        "source_coverage_pct": sources["source_coverage_pct"],
        "linked": linked,
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. RESEARCH REASONING
# ═══════════════════════════════════════════════════════════════════════════

def test_research_reasoning() -> dict[str, Any]:
    """Demonstrate research reasoning with evidence and hypotheses."""
    runtime = KnowledgeIntelligenceRuntime()
    profile = runtime.get_or_create_profile("researcher_dr_mehta", "Dr. Mehta — Research Lab",
                                             domains=["biotech", "immunology"])

    # Research findings
    runtime.add_knowledge(profile.profile_id, KnowledgeType.RESEARCH.value,
        "mRNA vaccine immune response",
        "mRNA vaccines produce strong T-cell and antibody responses with 95% efficacy",
        summary="Key finding on mRNA vaccine efficacy",
        tags=["mrna", "vaccine", "immunology"], domain="immunology",
        source_type=SourceType.RESEARCH_PAPER.value,
        source_name="Nature Medicine", source_author="Dr. Chen",
        confidence_score=0.9)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.EVIDENCE.value,
        "Clinical trial data — trial 4721",
        "Double-blind trial of 40,000 participants showed 94% efficacy in 6-month follow-up",
        summary="Supporting clinical trial data",
        tags=["mrna", "clinical_trial", "evidence"], domain="immunology",
        source_type=SourceType.RESEARCH_PAPER.value,
        confidence_score=0.95)

    # Hypothesis
    hypothesis = runtime.add_knowledge(profile.profile_id, KnowledgeType.HYPOTHESIS.value,
        "Booster interval affects longevity",
        "Extending the interval between mRNA doses improves long-term immunity",
        summary="Hypothesis about booster timing",
        tags=["mrna", "booster", "hypothesis"], domain="immunology",
        source_type=SourceType.INFERENCE.value,
        confidence_score=0.4)

    # Link evidence to research finding
    finding = runtime.get_knowledge(profile.profile_id, profile.knowledge_objects[0].knowledge_id)
    evidence = runtime.get_knowledge(profile.profile_id, profile.knowledge_objects[1].knowledge_id)
    runtime.link_knowledge(profile.profile_id, evidence.knowledge_id, finding.knowledge_id,
                           KnowledgeRelationship.EVIDENCE_FOR.value,
                           evidence="Clinical trial confirms mRNA efficacy")

    # Evidence reasoning
    reasoning = runtime.reason_with_evidence(profile.profile_id, finding.knowledge_id)
    assert reasoning is not None
    assert reasoning["assessment"] == "well_supported"
    assert reasoning["supporting_evidence"]

    # Confidence scoring
    confidence = runtime.compute_confidence(profile.profile_id, finding.knowledge_id,
                                             source_reliability=0.9, evidence_count=1,
                                             corroboration_count=1)
    assert confidence is not None
    assert confidence["score"] > 0.3  # moderate confidence with evidence

    return {
        "scenario": "3. Research Reasoning",
        "entity": "Dr. Mehta — Research Lab",
        "knowledge_count": profile.total_knowledge,
        "reasoning_assessment": reasoning["assessment"],
        "supporting_evidence": len(reasoning["supporting_evidence"]),
        "confidence_score": confidence["score"],
        "confidence_level": confidence["level"],
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. POLICY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def test_policy_management() -> dict[str, Any]:
    """Demonstrate organizational policy management."""
    runtime = KnowledgeIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_compliance", "Compliance Team",
                                             domains=["compliance", "security", "hr"])

    # Policies
    runtime.add_knowledge(profile.profile_id, KnowledgeType.POLICY.value,
        "Data privacy policy",
        "All customer data must be encrypted at rest and in transit. Access requires role-based permission.",
        summary="Data protection and privacy policy",
        tags=["policy", "privacy", "security"], domain="compliance",
        source_type=SourceType.DOCUMENT.value, source_name="Legal Department",
        confidence_score=0.95)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.POLICY.value,
        "Remote work policy",
        "Employees may work remotely up to 3 days per week with manager approval.",
        summary="Remote work flexibility policy",
        tags=["policy", "hr", "remote"], domain="hr",
        source_type=SourceType.DOCUMENT.value, source_name="HR Department",
        confidence_score=0.9)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.POLICY.value,
        "Expense reimbursement policy",
        "Expenses over 5000 INR require pre-approval. Receipts required for all claims.",
        summary="Expense claim and reimbursement rules",
        tags=["policy", "finance", "expenses"], domain="compliance",
        source_type=SourceType.DOCUMENT.value,
        confidence_score=0.88)

    # Best practice
    runtime.add_knowledge(profile.profile_id, KnowledgeType.BEST_PRACTICE.value,
        "Password security best practice",
        "Use a password manager and 2FA for all accounts. Never reuse passwords.",
        summary="Recommended password security practices",
        tags=["security", "best_practice"], domain="security",
        source_type=SourceType.EXPERIENCE.value,
        confidence_score=0.85)

    # Search policies
    policy_results = runtime.search(profile.profile_id, "privacy data",
                                    types=[KnowledgeType.POLICY.value])
    assert len(policy_results) >= 1

    # Search by domain
    compliance = runtime.search(profile.profile_id, "compliance", domains=["compliance"])
    assert len(compliance) >= 1

    # Knowledge by type
    by_type = profile.knowledge_by_type
    assert KnowledgeType.POLICY.value in by_type

    return {
        "scenario": "4. Policy Management",
        "entity": "Compliance Team",
        "policy_count": len(by_type.get(KnowledgeType.POLICY.value, [])),
        "best_practice_count": len(by_type.get(KnowledgeType.BEST_PRACTICE.value, [])),
        "policy_search_results": len(policy_results),
        "compliance_results": len(compliance),
        "domains": profile.domains,
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. CONTRADICTORY KNOWLEDGE DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def test_contradictory_knowledge() -> dict[str, Any]:
    """Demonstrate contradiction detection between knowledge objects."""
    runtime = KnowledgeIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_nutrition", "Nutrition Research",
                                             domains=["nutrition", "health"])

    # Contradictory knowledge
    runtime.add_knowledge(profile.profile_id, KnowledgeType.FACT.value,
        "Eggs and cholesterol",
        "Eating eggs is not associated with increased heart disease risk",
        summary="Eggs are heart-healthy",
        tags=["nutrition", "eggs", "heart"], domain="nutrition",
        source_type=SourceType.RESEARCH_PAPER.value, source_name="Harvard Study",
        confidence_score=0.8)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.FACT.value,
        "Eggs increase cholesterol",
        "Eating eggs does increase bad cholesterol levels and heart disease risk",
        summary="Eggs increase cholesterol risk",
        tags=["nutrition", "eggs", "heart"], domain="nutrition",
        source_type=SourceType.RESEARCH_PAPER.value, source_name="Legacy Study",
        confidence_score=0.6)

    # Explicit contradiction link
    egg_safe = runtime.get_knowledge(profile.profile_id, profile.knowledge_objects[0].knowledge_id)
    egg_risky = runtime.get_knowledge(profile.profile_id, profile.knowledge_objects[1].knowledge_id)
    runtime.link_knowledge(profile.profile_id, egg_safe.knowledge_id, egg_risky.knowledge_id,
                           KnowledgeRelationship.CONTRADICTS.value,
                           evidence="Conflicting claims about eggs and heart disease")

    # Detect contradictions
    contradictions = runtime.detect_contradictions(profile.profile_id)
    assert len(contradictions) >= 1

    # Resolve contradiction
    resolved = runtime.resolve_contradiction(
        profile.profile_id, contradictions[0]["contradiction_id"],
        "Modern research supersedes legacy study; eggs are safe in moderation")
    assert resolved

    # Verify resolution
    resolved_obj = profile.contradictions[0]
    assert resolved_obj.resolved

    return {
        "scenario": "5. Contradictory Knowledge Detection",
        "entity": "Nutrition Research",
        "contradictions_detected": len(contradictions),
        "contradiction_type": contradictions[0]["contradiction_type"],
        "resolved": resolved,
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 6. KNOWLEDGE GRAPH CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════════

def test_knowledge_graph_construction() -> dict[str, Any]:
    """Demonstrate automatic knowledge graph construction."""
    runtime = KnowledgeIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_learning", "Learning Hub",
                                             domains=["programming", "data"])

    # Related knowledge with shared tags
    runtime.add_knowledge(profile.profile_id, KnowledgeType.CONCEPT.value,
        "Python programming language",
        "Python is a high-level, interpreted programming language emphasizing readability",
        summary="Python language overview",
        tags=["programming", "python", "language"], domain="programming",
        confidence_score=0.9)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.CONCEPT.value,
        "Python data structures",
        "Lists, dicts, sets, and tuples are core Python data structures",
        summary="Core Python data structures",
        tags=["programming", "python", "data_structures"], domain="programming",
        confidence_score=0.85)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.CONCEPT.value,
        "Machine learning basics",
        "Machine learning builds models that learn patterns from data",
        summary="ML introduction",
        tags=["machine_learning", "data", "python"], domain="data",
        confidence_score=0.8)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.FACT.value,
        "Python for ML",
        "Python is the most popular language for machine learning",
        summary="Python dominance in ML",
        tags=["python", "machine_learning"], domain="data",
        confidence_score=0.9)

    # Build graph
    graph = runtime.build_knowledge_graph(profile.profile_id)
    assert graph is not None
    assert graph["node_count"] == 4
    assert graph["edge_count"] >= 2  # auto-linked via shared tags/domain

    return {
        "scenario": "6. Knowledge Graph Construction",
        "entity": "Learning Hub",
        "nodes": graph["node_count"],
        "edges": graph["edge_count"],
        "auto_linked": graph["edge_count"] >= 2,
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 7. MISSING KNOWLEDGE RECOMMENDATION
# ═══════════════════════════════════════════════════════════════════════════

def test_missing_knowledge_recommendation() -> dict[str, Any]:
    """Demonstrate recommendation of missing knowledge."""
    runtime = KnowledgeIntelligenceRuntime()
    profile = runtime.get_or_create_profile("org_new_team", "New Product Team",
                                             domains=["product", "engineering"])

    # Sparse knowledge base — only facts, no procedures/policies
    runtime.add_knowledge(profile.profile_id, KnowledgeType.FACT.value,
        "Product uses React",
        "The frontend is built with React",
        tags=["product", "react"], domain="product",
        confidence_score=0.7)

    runtime.add_knowledge(profile.profile_id, KnowledgeType.FACT.value,
        "Backend uses Python",
        "The backend is built with Python FastAPI",
        tags=["product", "python"], domain="engineering",
        confidence_score=0.7)

    # Low confidence knowledge
    runtime.add_knowledge(profile.profile_id, KnowledgeType.ASSUMPTION.value,
        "Market size assumption",
        "Assuming a 10 billion INR TAM",
        tags=["product", "market"], domain="product",
        confidence_score=0.2)

    # Unanswered question
    runtime.add_knowledge(profile.profile_id, KnowledgeType.QUESTION.value,
        "What is the target customer segment?",
        "Which customer segments should we prioritize?",
        tags=["product", "question"], domain="product",
        confidence_score=0.3)

    # Detect gaps
    gaps = runtime.detect_gaps(profile.profile_id, "product")
    assert len(gaps) >= 1

    # Get recommendations
    recs = runtime.recommend_knowledge(profile.profile_id, "product")
    assert len(recs) >= 1

    # Evidence-backed recommendations
    assert all("evidence" in r for r in recs)

    return {
        "scenario": "7. Missing Knowledge Recommendation",
        "entity": "New Product Team",
        "knowledge_count": profile.total_knowledge,
        "gaps_detected": len(gaps),
        "recommendations": len(recs),
        "evidence_backed": all(len(r.get("evidence", [])) > 0 for r in recs),
        "high_priority": any(r["priority"] == "high" for r in recs),
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Run All Verifications
# ═══════════════════════════════════════════════════════════════════════════

def run_all_verifications() -> list[dict[str, Any]]:
    tests = [
        ("Personal Knowledge", test_personal_knowledge),
        ("Organizational SOPs", test_organizational_sops),
        ("Research Reasoning", test_research_reasoning),
        ("Policy Management", test_policy_management),
        ("Contradictory Knowledge Detection", test_contradictory_knowledge),
        ("Knowledge Graph Construction", test_knowledge_graph_construction),
        ("Missing Knowledge Recommendation", test_missing_knowledge_recommendation),
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
    print("UCP-04 — Universal Knowledge Intelligence: Verification Report")
    print("=" * 80)
    print()

    results = run_all_verifications()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"  {status} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("knowledge_count") is not None:
            print(f"         Knowledge objects: {r['knowledge_count']}")
        if r.get("graph_nodes") is not None:
            print(f"         Graph: {r['graph_nodes']} nodes, {r['graph_edges']} edges")
        if r.get("contradictions_detected") is not None:
            print(f"         Contradictions: {r['contradictions_detected']} detected, resolved={r.get('resolved', 'N/A')}")
        if r.get("gaps_detected") is not None:
            print(f"         Gaps: {r['gaps_detected']} | Recommendations: {r['recommendations']} (evidence-backed: {r.get('evidence_backed', 'N/A')})")
        if r.get("reasoning_assessment") is not None:
            print(f"         Evidence reasoning: {r['reasoning_assessment']} (confidence: {r.get('confidence_score', 'N/A')})")
        if r.get("error"):
            print(f"         ERROR: {r['error']}")
        print()

    print("-" * 80)
    print(f"  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    print()

    if not failed:
        print("  ✅ UCP-04 VERIFICATION PASSED: All 7 knowledge scenarios execute")
        print("     through the same Universal Knowledge Intelligence capability.")
        print()
        print("  No Knowledge Runtime introduced.")
        print("  No Wiki Runtime introduced.")
        print("  No Note Runtime introduced.")
        print()
        print("  Every conclusion exposes supporting evidence.")
        print("  Knowledge are Living Knowledge Objects connected to Reality.")
        print("=" * 80)
    else:
        print("  ❌ UCP-04 VERIFICATION FAILED")
        print("=" * 80)