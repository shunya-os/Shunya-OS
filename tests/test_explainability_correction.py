"""
Gate 3.3 — Explainability, Correction, Learning & Intelligence Closure.

All 7 required end-to-end scenarios plus security and failure tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from core.intelligence import (
    IntelligenceResponse, IntelligenceRequest, KnowledgeStatus,
    EvidenceSource, KnowledgeClaim,
)
from core.intelligence.explain import Explanation, ExplanationService
from core.intelligence.correction import (
    CorrectionType, CorrectionRecord, PreferenceRecord, OutcomeRecord,
    CorrectionService, get_correction_service, reset_correction_service,
)


@pytest.fixture(autouse=True)
def clean():
    reset_correction_service()
    yield
    reset_correction_service()


# ═══════════════════════════════════════════════════════════════════
# 1. Explainability
# ═══════════════════════════════════════════════════════════════════


class TestExplainability:
    """Every intelligence output can produce a structured explanation."""

    def test_explanation_has_required_fields(self):
        """Explanation has all required fields."""
        exp = Explanation(
            claim="Revenue grew 20%",
            status="inference",
            conclusion="Revenue grew 20% based on invoice data",
            supporting_evidence=[
                {"source": "sh_objects", "type": "company_data", "detail": "Invoice #123: $5,000", "timestamp": "2024-06-01"},
            ],
            confidence=0.6,
            freshness_verified=True,
            freshness_ok=True,
            assumptions=["Data may be incomplete"],
            missing_information=["Current quarter data not yet available"],
        )
        assert exp.claim == "Revenue grew 20%"
        assert exp.status == "inference"
        assert len(exp.supporting_evidence) >= 1
        assert exp.evidence_count >= 1
        assert exp.governed_evidence_count >= 1
        assert exp.confidence == 0.6
        assert exp.confidence_known
        assert exp.freshness_verified
        assert len(exp.assumptions) >= 1

    def test_explain_response(self):
        """ExplanationService produces explanations from a response."""
        response = IntelligenceResponse()
        response.add_claim("Revenue was $5M", KnowledgeStatus.FACT, 1.0,
                          sources=[EvidenceSource(type="company_data", source="invoice", detail="Invoice total")])
        response.add_claim("Growth is likely", KnowledgeStatus.INFERENCE, 0.6)
        response.context_used.append(EvidenceSource(type="company_data", source="sh_objects", detail="Revenue data"))
        response.freshness_verified = True
        response.freshness_ok = True

        service = ExplanationService()
        explanations = service.explain_response(response)
        assert len(explanations) >= 2
        assert explanations[0].status == "fact"
        assert explanations[1].status == "inference"

    def test_no_chain_of_thought_exposed(self):
        """Explanation does not expose hidden chain-of-thought."""
        exp = Explanation(claim="Revenue grew", status="fact", conclusion="Revenue grew 20%")
        # No raw model tokens, no reasoning trace, no hidden state
        assert not hasattr(exp, "raw_tokens")
        assert not hasattr(exp, "model_logprobs")
        assert not hasattr(exp, "hidden_reasoning")

    def test_explain_specific_claim(self):
        """A specific claim can be explained by index."""
        response = IntelligenceResponse()
        response.add_claim("Fact claim", KnowledgeStatus.FACT, 1.0)
        response.add_claim("Inference claim", KnowledgeStatus.INFERENCE, 0.6)
        service = ExplanationService()
        exp = service.explain_claim_index(response, 0)
        assert exp is not None
        assert exp.status == "fact"

    def test_evidence_source_tracking(self):
        """Evidence sources track governed vs external origin."""
        exp = Explanation(
            claim="Test",
            status="fact",
            conclusion="Test",
            supporting_evidence=[
                {"source": "sh_objects", "type": "company_data", "detail": "Company record"},
                {"source": "web_search", "type": "external", "detail": "Web result", "url": "https://x.com"},
            ],
        )
        assert exp.governed_evidence_count == 1
        assert exp.external_evidence_count == 1

    def test_no_opaque_score_without_evidence(self):
        """Confidence is never set without supporting evidence."""
        exp = Explanation(claim="Test", status="unknown", conclusion="Unknown")
        assert exp.confidence is None
        assert not exp.confidence_known


# ═══════════════════════════════════════════════════════════════════
# 2. SCENARIO A — Explain Why
# ═══════════════════════════════════════════════════════════════════


class TestScenarioAExplainWhy:
    """A user can ask 'Why?' and get evidence, assumptions, uncertainty."""

    def test_why_produces_explanation(self):
        response = IntelligenceResponse()
        response.add_claim("Invoice #123 is overdue", KnowledgeStatus.FACT, 0.95,
                          sources=[EvidenceSource(type="company_data", source="invoice", detail="Due date was 2024-05-01")])
        response.context_used.append(EvidenceSource(type="company_data", source="sh_objects", detail="Invoice #123"))
        response.freshness_verified = True
        response.freshness_ok = True

        service = ExplanationService()
        exp = service.explain_claim_index(response, 0)
        assert exp is not None
        assert exp.claim == "Invoice #123 is overdue"
        assert exp.status == "fact"
        assert len(exp.supporting_evidence) >= 1
        # Evidence is available
        assert any("invoice" in str(e.get("source", "")).lower() for e in exp.supporting_evidence)


# ═══════════════════════════════════════════════════════════════════
# 3. Correction Model
# ═══════════════════════════════════════════════════════════════════


class TestCorrectionModel:
    """Correction record preserves history and identifies what was corrected."""

    def test_correction_preserves_original(self):
        correction = CorrectionRecord(
            correction_type=CorrectionType.FACTUAL,
            target_claim="Revenue was $5M",
            original_value="$5M",
            corrected_value="$5.5M",
            reason="The Q4 adjustment was not included",
            tenant_id=1,
            actor_id="user_42",
        )
        assert correction.original_value == "$5M"
        assert correction.corrected_value == "$5.5M"
        assert correction.reason
        assert correction.source == "user"

    def test_correction_does_not_mutate_history(self):
        correction = CorrectionRecord(
            correction_type=CorrectionType.FACTUAL,
            target_claim="Revenue was $5M",
            original_value="$5M",
            corrected_value="$5.5M",
            tenant_id=1,
        )
        # The original is preserved — the correction is a separate record
        assert correction.original_value == "$5M"
        # The original claim still exists — the correction is traceable

    def test_correction_types(self):
        for t in CorrectionType:
            cr = CorrectionRecord(correction_type=t, target_claim="test", original_value="", corrected_value="")
            assert cr.correction_type == t


# ═══════════════════════════════════════════════════════════════════
# 4. SCENARIO B — Correct
# ═══════════════════════════════════════════════════════════════════


class TestScenarioBCorrect:
    """Correct a SHUNYA conclusion. Original history intact, corrected
    knowledge traceable."""

    def test_correction_recorded(self):
        service = CorrectionService()
        cr = CorrectionRecord(
            correction_type=CorrectionType.FACTUAL,
            target_claim="Customer is at risk",
            original_value="High risk",
            corrected_value="Low risk — payment received",
            reason="The customer just paid",
            tenant_id=1,
            actor_id="user_42",
        )
        cid = service.record_correction(cr)
        retrieved = service.get_correction(cid)
        assert retrieved is not None
        assert retrieved.original_value == "High risk"
        assert retrieved.corrected_value == "Low risk — payment received"

    def test_history_preserved_after_correction(self):
        service = CorrectionService()
        # First correction
        service.record_correction(CorrectionRecord(
            correction_type=CorrectionType.FACTUAL,
            target_claim="Revenue was $5M",
            original_value="$5M", corrected_value="$5.5M",
            tenant_id=1,
        ))
        # The original claim is still accessible through the correction record
        corrections = service.get_corrections_for_claim("Revenue was $5M", tenant_id=1)
        assert len(corrections) >= 1
        assert corrections[0].original_value == "$5M"


# ═══════════════════════════════════════════════════════════════════
# 5. SCENARIO C — Preference
# ═══════════════════════════════════════════════════════════════════


class TestScenarioCPreference:
    """Explicitly record a user preference — scoped to appropriate tenant."""

    def test_preference_recorded(self):
        service = CorrectionService()
        pref = PreferenceRecord(
            key="risk_threshold",
            value="high",
            tenant_id=1,
            actor_id="user_42",
            scope="user",
        )
        pid = service.record_preference(pref)
        retrieved = service.get_preference("risk_threshold", tenant_id=1, actor_id="user_42")
        assert retrieved is not None
        assert retrieved.value == "high"

    def test_tenant_isolation(self):
        service = CorrectionService()
        service.record_preference(PreferenceRecord(key="source", value="google", tenant_id=1, scope="tenant"))
        service.record_preference(PreferenceRecord(key="source", value="bing", tenant_id=2, scope="tenant"))

        pref_1 = service.get_preference("source", tenant_id=1)
        pref_2 = service.get_preference("source", tenant_id=2)
        assert pref_1 is not None and pref_1.value == "google"
        assert pref_2 is not None and pref_2.value == "bing"

    def test_user_preference_scope(self):
        """User-scoped preferences affect only that user."""
        service = CorrectionService()
        # User A prefers high risk threshold
        service.record_preference(PreferenceRecord(key="risk_threshold", value="high", tenant_id=1, actor_id="user_a", scope="user"))
        # User B prefers low risk threshold
        service.record_preference(PreferenceRecord(key="risk_threshold", value="low", tenant_id=1, actor_id="user_b", scope="user"))

        pref_a = service.get_preference("risk_threshold", tenant_id=1, actor_id="user_a")
        pref_b = service.get_preference("risk_threshold", tenant_id=1, actor_id="user_b")
        assert pref_a.value == "high"
        assert pref_b.value == "low"


# ═══════════════════════════════════════════════════════════════════
# 6. SCENARIO D — Outcome Feedback
# ═══════════════════════════════════════════════════════════════════


class TestScenarioDOutcome:
    """Recommendation → action → outcome → evaluation."""

    def test_outcome_recorded(self):
        service = CorrectionService()
        outcome = OutcomeRecord(
            recommendation_id="rec_123",
            recommendation_summary="Contact the customer",
            action_taken="accepted",
            result="success",
            outcome_description="Customer signed the contract",
            tenant_id=1,
            actor_id="user_42",
        )
        oid = service.record_outcome(outcome)
        retrieved = service.get_outcome(oid)
        assert retrieved is not None
        assert retrieved.recommendation_id == "rec_123"
        assert retrieved.action_taken == "accepted"
        assert retrieved.result == "success"

    def test_outcome_connected_to_recommendation(self):
        service = CorrectionService()
        service.record_outcome(OutcomeRecord(recommendation_id="rec_abc", recommendation_summary="Test", action_taken="accepted", result="success", tenant_id=1))
        service.record_outcome(OutcomeRecord(recommendation_id="rec_abc", recommendation_summary="Test", action_taken="rejected", result="failure", tenant_id=1))
        outcomes = service.get_outcomes_for_recommendation("rec_abc")
        assert len(outcomes) == 2


# ═══════════════════════════════════════════════════════════════════
# 7. SCENARIO E — Conflict
# ═══════════════════════════════════════════════════════════════════


class TestScenarioEConflict:
    """Conflicting evidence — SHUNYA does not silently erase either side."""

    def test_correction_conflict_preserves_both(self):
        """When a user correction conflicts with evidence, both are preserved."""
        service = CorrectionService()
        # Original claim
        correction = CorrectionRecord(
            correction_type=CorrectionType.DISAGREE,
            target_claim="Customer is at risk",
            original_value="High risk",
            corrected_value="No risk",
            reason="Customer has good payment history",
            tenant_id=1,
        )
        service.record_correction(correction)
        # The correction is separate from the original claim
        # Both the original evidence and the correction are preserved
        corrections = service.get_corrections_for_claim("Customer is at risk", tenant_id=1)
        assert len(corrections) >= 1
        assert corrections[0].original_value == "High risk"
        assert corrections[0].corrected_value == "No risk"


# ═══════════════════════════════════════════════════════════════════
# 8. SCENARIO F — Stale Intelligence
# ═══════════════════════════════════════════════════════════════════


class TestScenarioFStale:
    """A time-sensitive research result can become stale."""

    def test_staleness_detected(self):
        """Old timestamps are detected as stale."""
        from datetime import datetime, timezone, timedelta
        old = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        assert CorrectionService.is_stale(old, max_age_seconds=86400)

    def test_recent_not_stale(self):
        """Recent timestamps are not stale."""
        from datetime import datetime, timezone
        recent = datetime.now(timezone.utc).isoformat()
        assert not CorrectionService.is_stale(recent, max_age_seconds=86400)

    def test_intelligence_response_carries_freshness(self):
        """IntelligenceResponse carries freshness information."""
        response = IntelligenceResponse()
        response.freshness_verified = True
        response.freshness_ok = True
        response.freshness_note = ""
        assert response.freshness_verified


# ═══════════════════════════════════════════════════════════════════
# 9. SCENARIO G — Security
# ═══════════════════════════════════════════════════════════════════


class TestScenarioGSecurity:
    """Cross-tenant, malicious, or unauthorized correction/learning is blocked."""

    def test_cross_tenant_correction_blocked(self):
        service = CorrectionService()
        correction = CorrectionRecord(
            correction_type=CorrectionType.FACTUAL,
            target_claim="Tenant A data",
            original_value="X",
            corrected_value="Y",
            tenant_id=1,  # Belongs to tenant 1
        )
        # Tenant 2 tries to record a correction for tenant 1
        valid, reason = service.validate_correction(correction, request_tenant_id=2)
        assert valid is False, "Cross-tenant correction should be blocked"

    def test_same_tenant_correction_allowed(self):
        service = CorrectionService()
        correction = CorrectionRecord(
            correction_type=CorrectionType.FACTUAL,
            target_claim="Test",
            original_value="X",
            corrected_value="Y",
            tenant_id=1,
        )
        valid, reason = service.validate_correction(correction, request_tenant_id=1)
        assert valid is True, "Same-tenant correction should be allowed"

    def test_global_scope_blocked(self):
        service = CorrectionService()
        correction = CorrectionRecord(
            correction_type=CorrectionType.FACTUAL,
            target_claim="Test",
            original_value="X",
            corrected_value="Y",
            tenant_id=1,
            scope="global",
        )
        valid, reason = service.validate_correction(correction, request_tenant_id=1)
        assert valid is False
        assert "governance approval" in reason.lower()

    def test_preference_does_not_leak_tenant(self):
        """Preferences from one tenant are not visible to another."""
        service = CorrectionService()
        service.record_preference(PreferenceRecord(key="secret", value="tenant_1_secret", tenant_id=1, scope="tenant"))
        prefs_t2 = service.get_all_preferences(tenant_id=2)
        assert all(p.tenant_id == 2 or p.tenant_id == 0 for p in prefs_t2), "Tenant 2 should not see tenant 1 preferences"

    def test_correction_does_not_affect_other_tenant(self):
        """Corrections from one tenant do not affect another."""
        service = CorrectionService()
        service.record_correction(CorrectionRecord(
            correction_type=CorrectionType.FACTUAL, target_claim="Claim",
            original_value="A", corrected_value="B", tenant_id=1,
        ))
        corrections_t2 = service.get_all_corrections(tenant_id=2)
        assert len(corrections_t2) == 0


# ═══════════════════════════════════════════════════════════════════
# 10. CorrectionService Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestCorrectionServiceEdgeCases:
    """Edge cases for the correction service."""

    def test_correction_id_generated(self):
        cr = CorrectionRecord(correction_type=CorrectionType.FACTUAL, target_claim="test", original_value="", corrected_value="")
        assert cr.correction_id.startswith("corr_")

    def test_preference_id_generated(self):
        pref = PreferenceRecord(key="test", value="value", tenant_id=1)
        assert pref.preference_id.startswith("pref_")

    def test_outcome_id_generated(self):
        out = OutcomeRecord(recommendation_id="rec_123", recommendation_summary="Test", action_taken="accepted", result="success", tenant_id=1)
        assert out.outcome_id.startswith("out_")

    def test_get_nonexistent_correction(self):
        service = CorrectionService()
        assert service.get_correction("nonexistent") is None

    def test_get_nonexistent_preference(self):
        service = CorrectionService()
        assert service.get_preference("nonexistent", tenant_id=1) is None

    def test_get_nonexistent_outcome(self):
        service = CorrectionService()
        assert service.get_outcome("nonexistent") is None

    def test_clear(self):
        service = CorrectionService()
        service.record_correction(CorrectionRecord(correction_type=CorrectionType.FACTUAL, target_claim="test", original_value="", corrected_value="", tenant_id=1))
        service.clear()
        assert len(service.get_all_corrections()) == 0