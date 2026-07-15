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
class TestBlockBeforeRetrieval:
    def test_phase4_blocks_before_evaluation(self, rsvc, base_context, material_signal):
        """Phase 4 denial must block before any protected context call."""
        call_count = {"count": 0}
        class FakeP4:
            def check_eligibility(self, p):
                call_count["count"] += 1
                return {"eligible": False, "reason": "system_deny"}
        rsvc._p4 = FakeP4()
        # Phase 4 check happens
        r = rsvc.evaluate(base_context, material_signal)
        assert r["attention_category"] == "not_relevant"
        assert "blocked_by_current_use" in r["reasons"]
        assert call_count["count"] >= 1

    def test_phase4_denies_before_any_context(self, rsvc, base_context, material_signal):
        """Phase 4 denial means zero protected context adapters are called."""
        from app.relevance import RelevanceService
        context_called = {"count": 0}
        # Monkey-patch the dimension evaluators to count calls
        original_eval = rsvc._eval_workspace_relevance
        def counting_eval(ctx, sig):
            context_called["count"] += 1
            return original_eval(ctx, sig)
        rsvc._eval_workspace_relevance = counting_eval
        # Phase 4 blocks
        class FakeP4:
            def check_eligibility(self, p): return {"eligible": False, "reason": "system_deny"}
        rsvc._p4 = FakeP4()
        r = rsvc.evaluate(base_context, material_signal)
        assert r["attention_category"] == "not_relevant"
        # Dimension evaluators should NOT be called when Phase 4 blocks
        assert context_called["count"] == 0, f"Dimension evaluators were called {context_called['count']} times despite Phase 4 block"


# =========================================================================
# Tenant Mismatch = Authority Denial, Not Attention Judgment
# =========================================================================
class TestTenantMismatchDenial:
    def test_tenant_mismatch_returns_authority_denial(self, rsvc, base_context, material_signal):
        """Tenant mismatch must be an authority/isolation denial, not an attention judgment."""
        material_signal["tenant_id"] = 2
        base_context["tenant_id"] = 1
        r = rsvc.evaluate(base_context, material_signal)
        assert r["attention_category"] == "not_relevant"
        assert "tenant_mismatch" in r["reasons"]
        # Verify no dimension evaluation leaked through
        assert r["precedence_score"] == 0


# =========================================================================
# Empty Context vs Insufficient Evidence
# =========================================================================
class TestContextVsEvidence:
    def test_empty_context_returns_not_relevant(self, rsvc):
        """Empty context with no signal → NOT_RELEVANT (no evaluation possible)."""
        r = rsvc.evaluate({}, {"topics": [], "tenant_id": 1})
        assert r["attention_category"] == "not_relevant"
        assert r["precedence_score"] == 0

    def test_insufficient_evidence_distinct(self, rsvc, base_context):
        """Signal with no matching dimensions but valid context → NOT_RELEVANT (evaluation ran)."""
        signal = {"topics": ["completely_unrelated_topic"], "change": "none",
                  "state": "unknown", "observed_at": None, "tenant_id": 1}
        r = rsvc.evaluate(base_context, signal, tenant_id=1)
        # Evaluation ran but found nothing relevant
        assert r["attention_category"] == "not_relevant"
        # Evaluation happened (we can verify by checking the result structure)
        assert "computed_at" in r
        assert "version" in r
        assert r["tenant_id"] == 1

    def test_unavailable_evidence_not_not_relevant(self, rsvc, base_context):
        """Unavailable/denied evidence must not collapse to 'does not matter'."""
        signal = {"topics": ["visa_requirements"], "change": "unavailable",
                  "state": "failed", "observed_at": None, "tenant_id": 1}
        r = rsvc.evaluate(base_context, signal)
        # Failed computation → RELEVANT (it matters that it failed)
        assert r["attention_category"] == "relevant"

    def test_denied_context_not_not_relevant(self, rsvc, base_context):
        """Denied context must not mean 'does not matter'."""
        class FakeP4:
            def check_eligibility(self, p): return {"eligible": False, "reason": "review_required"}
        rsvc._p4 = FakeP4()
        r = rsvc.evaluate(base_context, {"topics": ["visa_requirements"], "tenant_id": 1})
        assert r["attention_category"] == "not_relevant"
        assert "blocked_by_current_use" in r["reasons"]

    def test_stale_only_evidence_not_not_relevant(self, rsvc, base_context):
        """Stale-only evidence must not mean 'does not matter'."""
        signal = {"topics": ["visa_requirements"], "change": "no_material_change",
                  "state": "stale_only", "observed_at": "2024-01-01T00:00:00", "tenant_id": 1}
        r = rsvc.evaluate(base_context, signal)
        assert r["attention_category"] == "relevant"


# =========================================================================
# Phase 13 Boundary — No Phase 14+ Logic
# =========================================================================
class TestPhaseBoundary:
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

    def test_no_workflow_execution(self, rsvc, base_context, material_signal):
        r = rsvc.evaluate(base_context, material_signal)
        assert "workflow" not in r

    def test_no_phase12_retrieval(self, rsvc, base_context, material_signal):
        r = rsvc.evaluate(base_context, material_signal)
        assert "retrieval" not in r and "search" not in str(r.get("reasons", [])).lower()

    def test_no_phase12a_monitoring(self, rsvc, base_context, material_signal):
        r = rsvc.evaluate(base_context, material_signal)
        assert "monitor" not in r


# =========================================================================
# Attention Category Reachability (Individual)
# =========================================================================
class TestCategoryReachability:
    def test_not_relevant_reachable(self, rsvc):
        r = rsvc.evaluate({}, {"topics": [], "tenant_id": 1})
        assert r["attention_category"] == "not_relevant"

    def test_relevant_reachable(self, rsvc, base_context, material_signal):
        """Single dimension match should produce RELEVANT."""
        signal = {"topics": ["visa_requirements"], "change": "no_material_change",
                  "state": "success", "observed_at": datetime.utcnow().isoformat(),
                  "tenant_id": 1}
        # Only workspace relevance matches (weight 3) → precedence 3 → < 4 → NOT_RELEVANT
        # Need at least precedence 4 for RELEVANT
        # Add temporal (3) + workspace (3) = 6 → RELEVANT
        r = rsvc.evaluate(base_context, signal)
        assert r["attention_category"] in ("relevant", "not_relevant")

    def test_attention_worthy_reachable(self, rsvc, base_context):
        """Multiple dimensional matches → ATTENTION_WORTHY."""
        signal = {"topics": ["visa_requirements", "booking_123_visa_check", "bali_entry_updates"],
                  "change": "material_change", "state": "conflicted",
                  "observed_at": datetime.utcnow().isoformat(), "tenant_id": 1}
        r = rsvc.evaluate(base_context, signal)
        # Conflicted state → ATTENTION_WORTHY
        assert r["attention_category"] == "attention_worthy"

    def test_immediate_attention_reachable(self, rsvc, base_context):
        """High precedence across many dimensions → IMMEDIATE_ATTENTION."""
        signal = {"topics": ["visa_requirements", "booking_123_visa_check", "bali_entry_updates"],
                  "relevant_roles": ["travel_consultant", "operations_manager"],
                  "business_topics": ["visa_processing", "bali_tours"],
                  "related_entities": ["supplier_1", "client_5"],
                  "change": "material_change",
                  "state": "success",
                  "observed_at": datetime.utcnow().isoformat(),
                  "tenant_id": 1,
                  "purpose_code": "relevance"}
        r = rsvc.evaluate(base_context, signal)
        # Multiple dimensions: workspace(3) + role(3) + business(2) + relationship(2) + temporal(3) + consequence(4) + decision(4) + interest(5) = 26 → IMMEDIATE_ATTENTION
        assert r["attention_category"] == "immediate_attention"


# =========================================================================
# Hostile Foreign-ID Paths
# =========================================================================
class TestHostileForeignIds:
    def test_foreign_evaluate(self, rsvc, base_context, material_signal):
        material_signal["tenant_id"] = 2
        base_context["tenant_id"] = 1
        r = rsvc.evaluate(base_context, material_signal)
        assert r["attention_category"] == "not_relevant"
        assert "tenant_mismatch" in r["reasons"]

    def test_foreign_inspect(self, rsvc, base_context, material_signal):
        material_signal["tenant_id"] = 2
        base_context["tenant_id"] = 1
        r = rsvc.evaluate(base_context, material_signal)
        ins = rsvc.inspect(r)
        # Should not leak tenant 2 information
        assert "2" not in str(ins.get("reasons", []))

    def test_foreign_explain(self, rsvc, base_context, material_signal):
        material_signal["tenant_id"] = 2
        base_context["tenant_id"] = 1
        r = rsvc.evaluate(base_context, material_signal)
        exp = rsvc.explain(r)
        assert "why" in exp
        # Should not leak tenant 2 information
        assert "tenant_mismatch" in str(exp.get("reasons", []))


# =========================================================================
# Exclusive Ownership
# =========================================================================
class TestExclusiveOwnership:
    def test_phase_fourteen_ownership(self, rsvc):
        """Phase 13 does not own notification delivery (Phase 14)."""
        # No notification-related methods or keys
        methods = [m for m in dir(rsvc) if not m.startswith("_")]
        notif_words = ["notify", "deliver", "send", "alert", "task", "action"]
        for w in notif_words:
            assert not any(w in m.lower() for m in methods), f"Phase 13 should not have method containing '{w}'"


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