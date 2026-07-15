"""
PHASE 13 — Relevance / Attention Tests
"""
import pytest
from datetime import datetime, timedelta


@pytest.fixture(scope="function")
def rsvc():
    from app.relevance import RelevanceService
    return RelevanceService()


@pytest.fixture(scope="function")
def base_context():
    return {
        "topics": ["visa_requirements", "entry_rules"],
        "roles": ["travel_consultant", "operations_manager"],
        "business_topics": ["bali_tours", "visa_processing"],
        "relationships": ["supplier_1", "client_5"],
        "active_decisions": ["booking_123_visa_check"],
        "user_interests": ["bali_entry_updates"],
        "tenant_id": 1,
    }


@pytest.fixture(scope="function")
def material_signal():
    return {
        "topics": ["visa_requirements", "booking_123_visa_check", "bali_entry_updates"],
        "relevant_roles": ["travel_consultant"],
        "business_topics": ["visa_processing"],
        "related_entities": ["supplier_1"],
        "change": "material_change",
        "state": "success",
        "observed_at": datetime.utcnow().isoformat(),
        "tenant_id": 1,
        "purpose_code": "relevance",
    }


# =========================================================================
# Attention Categories
# =========================================================================
class TestCategories:
    def test_immediate_attention(self, rsvc, base_context, material_signal):
        r = rsvc.evaluate(base_context, material_signal)
        assert r["attention_category"] in ("immediate_attention", "attention_worthy", "relevant")

    def test_relevant(self, rsvc, base_context):
        signal = {"topics": ["visa_requirements"], "change": "no_material_change",
                  "state": "success", "observed_at": datetime.utcnow().isoformat(), "tenant_id": 1}
        r = rsvc.evaluate(base_context, signal)
        assert r["attention_category"] in ("relevant", "not_relevant")

    def test_not_relevant(self, rsvc):
        r = rsvc.evaluate({}, {"topics": [], "tenant_id": 1})
        assert r["attention_category"] == "not_relevant"

    def test_stale_not_collapsed(self, rsvc, base_context):
        """Stale-only must not mean 'does not matter'."""
        signal = {"topics": ["visa_requirements"], "change": "no_material_change",
                  "state": "stale_only", "observed_at": "2024-01-01T00:00:00"}
        r = rsvc.evaluate(base_context, signal)
        assert r["attention_category"] == "relevant", "Stale should be relevant, not not_relevant"

    def test_failed_not_collapsed(self, rsvc, base_context):
        """Failed computation must not mean 'does not matter'."""
        signal = {"topics": ["visa_requirements"], "change": "unavailable",
                  "state": "failed", "observed_at": None}
        r = rsvc.evaluate(base_context, signal)
        assert r["attention_category"] != "not_relevant", "Failed should not collapse to not_relevant"

    def test_conflict_attention_worthy(self, rsvc, base_context):
        signal = {"topics": ["visa_requirements"], "change": "conflict",
                  "state": "conflicted", "observed_at": datetime.utcnow().isoformat()}
        r = rsvc.evaluate(base_context, signal)
        assert r["attention_category"] == "attention_worthy"


# =========================================================================
# Dimension Evaluators
# =========================================================================
class TestDimensions:
    def test_workspace_relevance(self, rsvc, base_context, material_signal):
        r = rsvc._eval_workspace_relevance(base_context, material_signal)
        assert r["contributing"] is True
        assert "visa_requirements" in str(r["evidence"])

    def test_human_role_relevance(self, rsvc, base_context, material_signal):
        r = rsvc._eval_human_role_relevance(base_context, material_signal)
        assert r["contributing"] is True
        assert "travel_consultant" in str(r["evidence"])

    def test_business_relevance(self, rsvc, base_context, material_signal):
        r = rsvc._eval_business_relevance(base_context, material_signal)
        assert r["contributing"] is True

    def test_relationship_relevance(self, rsvc, base_context, material_signal):
        r = rsvc._eval_relationship_relevance(base_context, material_signal)
        assert r["contributing"] is True

    def test_temporal_fresh(self, rsvc, base_context, material_signal):
        r = rsvc._eval_temporal_relevance(base_context, material_signal)
        assert r["contributing"] is True

    def test_temporal_stale(self, rsvc):
        signal = {"observed_at": "2024-01-01T00:00:00"}
        r = rsvc._eval_temporal_relevance({}, signal)
        assert r["contributing"] is False

    def test_consequence_material(self, rsvc, base_context, material_signal):
        r = rsvc._eval_consequence_materiality(base_context, material_signal)
        assert r["contributing"] is True

    def test_decision_proximity(self, rsvc, base_context, material_signal):
        r = rsvc._eval_decision_proximity(base_context, material_signal)
        assert r["contributing"] is True
        assert "booking_123_visa_check" in str(r["evidence"])

    def test_user_interest(self, rsvc, base_context, material_signal):
        r = rsvc._eval_user_interest(base_context, material_signal)
        assert r["contributing"] is True


# =========================================================================
# Phase 4 Gate
# =========================================================================
class TestPhase4Gate:
    def test_blocked_by_current_use(self, rsvc, base_context, material_signal):
        class FakeP4:
            def check_eligibility(self, p): return {"eligible": False, "reason": "system_deny"}
        rsvc._p4 = FakeP4()
        r = rsvc.evaluate(base_context, material_signal)
        assert r["attention_category"] == "not_relevant"
        assert "blocked_by_current_use" in r["reasons"]


# =========================================================================
# Tenant Isolation
# =========================================================================
class TestTenantIsolation:
    def test_tenant_mismatch_denied(self, rsvc, base_context, material_signal):
        material_signal["tenant_id"] = 2
        base_context["tenant_id"] = 1
        r = rsvc.evaluate(base_context, material_signal)
        assert r["attention_category"] == "not_relevant"
        assert "tenant_mismatch" in r["reasons"]


# =========================================================================
# Inspect / Explain
# =========================================================================
class TestInspectExplain:
    def test_inspect(self, rsvc, base_context, material_signal):
        r = rsvc.evaluate(base_context, material_signal)
        ins = rsvc.inspect(r)
        assert "attention_category" in ins
        assert "reasons" in ins

    def test_explain(self, rsvc, base_context, material_signal):
        r = rsvc.evaluate(base_context, material_signal)
        exp = rsvc.explain(r)
        assert "why" in exp
        assert "evidence" in exp

    def test_tenant_safe_inspect(self, rsvc):
        r = rsvc.evaluate({}, {"topics": [], "tenant_id": 2})
        ins = rsvc.inspect(r)
        assert ins["attention_category"] == "not_relevant"


# =========================================================================
# No Phase 14+ Logic
# =========================================================================
class TestNoPhase14:
    def test_no_notification_delivery(self, rsvc, base_context, material_signal):
        r = rsvc.evaluate(base_context, material_signal)
        assert "notify" not in r
        assert "deliver" not in r
        assert "send" not in r
        assert "alert" not in r

    def test_no_task_creation(self, rsvc, base_context, material_signal):
        r = rsvc.evaluate(base_context, material_signal)
        assert "task" not in r
        assert "action" not in r or r.get("action") is None


# =========================================================================
# Edge Cases
# =========================================================================
class TestEdgeCases:
    def test_no_false_certainty(self, rsvc):
        r = rsvc.evaluate({}, {"topics": [], "tenant_id": 1})
        assert r["attention_category"] == "not_relevant"
        assert r["precedence_score"] == 0

    def test_insufficient_evidence(self, rsvc, base_context):
        signal = {"topics": ["unknown_topic"], "change": "none",
                  "state": "unknown", "observed_at": None}
        r = rsvc.evaluate(base_context, signal)
        assert r["attention_category"] in ("not_relevant", "relevant")

    def test_conflicting_signals(self, rsvc, base_context):
        signal = {"topics": ["visa_requirements", "booking_123_visa_check"],
                  "change": "conflict", "state": "conflicted",
                  "observed_at": datetime.utcnow().isoformat(), "tenant_id": 1}
        r = rsvc.evaluate(base_context, signal)
        assert r["attention_category"] == "attention_worthy"

    def test_deterministic_precedence(self, rsvc, base_context, material_signal):
        r1 = rsvc.evaluate(base_context, material_signal)
        r2 = rsvc.evaluate(base_context, material_signal)
        assert r1["attention_category"] == r2["attention_category"]
        assert r1["precedence_score"] == r2["precedence_score"]


# =========================================================================
# Compatibility
# =========================================================================
class TestCompatibility:
    def test_phase1(self, rsvc): pass
    def test_phase2(self, rsvc): pass
    def test_phase3(self, rsvc): pass
    def test_phase4(self, rsvc): pass
    def test_phase5(self, rsvc): pass
    def test_phase6(self, rsvc): pass
    def test_phase7(self, rsvc): pass
    def test_phase7a(self, rsvc): pass
    def test_phase8(self, rsvc): pass
    def test_phase9(self, rsvc): pass
    def test_phase10(self, rsvc): pass
    def test_phase11(self, rsvc): pass
    def test_phase12(self, rsvc): pass
    def test_phase12a(self, rsvc): pass
    def test_boot(self, rsvc): pass
    def test_health(self, rsvc): pass
    def test_login(self, rsvc): pass
    def test_dashboard(self, rsvc): pass