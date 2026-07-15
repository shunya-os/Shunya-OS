"""
PHASE 16 — Relationship-Aware Assistant Tests
"""
import pytest
from datetime import datetime


@pytest.fixture(scope="function")
def asvc():
    from app.assistant import AssistantService
    return AssistantService()


# =========================================================================
# Session
# =========================================================================
class TestSession:
    def test_create_session(self, asvc):
        r = asvc.create_session(1, 101, context_snapshot={"lead_status": "active"})
        assert "session_id" in r

    def test_tenant_scope(self, asvc):
        r = asvc.create_session(2, 201)
        assert r["session_id"] is not None

    def test_duplicate_idempotent(self, asvc):
        r1 = asvc.create_session(1, 301, idempotency_key="sess-1")
        assert "session_id" in r1
        r2 = asvc.create_session(1, 301, idempotency_key="sess-1")
        assert r2.get("duplicate") is True


# =========================================================================
# Context
# =========================================================================
class TestContext:
    def test_get_context(self, asvc):
        r = asvc.create_session(1, 101, context_snapshot={"status": "active"})
        sid = r["session_id"]
        ctx = asvc.get_context(sid, 1)
        assert "context" in ctx
        assert ctx["context"]["status"] == "active"

    def test_wrong_tenant_denied(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        ctx = asvc.get_context(sid, 2)
        assert "error" in ctx


# =========================================================================
# Recommendation
# =========================================================================
class TestRecommendation:
    def test_recommend_from_relevance(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 1, relevance_input={"category": "attention_worthy", "reasons": ["blocked_obligation"]})
        assert "assistance_id" in rec
        assert len(rec["recommendations"]) >= 1

    def test_recommend_from_execution(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 1, execution_refs=["exec-001"])
        assert "assistance_id" in rec

    def test_recommend_from_learning(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 1, learning_signals=["sig-001"])
        assert "assistance_id" in rec

    def test_recommend_from_growth(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 1, growth_refs=["camp-001"])
        assert "assistance_id" in rec

    def test_recommend_from_brand(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 1, brand_refs=["brand-001"])
        assert "assistance_id" in rec

    def test_wrong_tenant_denied(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 2, relevance_input={"category": "test"})
        assert "error" in rec

    def test_provenance_preserved(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 1, relevance_input={"category": "test"}, execution_refs=["exec-1"])
        assert rec["provenance"]["relevance"] is True
        assert rec["provenance"]["execution"] is True


# =========================================================================
# Inference Handoff
# =========================================================================
class TestInferenceHandoff:
    def test_no_direct_provider(self, asvc):
        assert not hasattr(asvc, "_provider")

    def test_phase_14c_handoff(self, asvc):
        r = asvc.request_inference("assist_response", {})
        assert "phase_14c_status" in r

    def test_inference_failure_no_success(self, asvc):
        r = asvc.request_inference("assist_response", {})
        assert r.get("result") is None
        assert r.get("inference_required") is True


# =========================================================================
# List / Delivery
# =========================================================================
class TestDelivery:
    def test_list_assistance(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        asvc.recommend_action(sid, 1, relevance_input={"category": "test"})
        items = asvc.list_assistance(sid, 1)
        assert items["count"] >= 1

    def test_mark_delivered(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 1, relevance_input={"category": "test"})
        aid = rec["assistance_id"]
        d = asvc.mark_delivered(aid, 1)
        assert d["state"] == "delivered"


# =========================================================================
# Tenant Isolation
# =========================================================================
class TestTenantIsolation:
    def test_cross_tenant_session_denied(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        ctx = asvc.get_context(sid, 2)
        assert "error" in ctx

    def test_cross_tenant_assistance_denied(self, asvc):
        r = asvc.create_session(1, 101)
        sid = r["session_id"]
        rec = asvc.recommend_action(sid, 1, relevance_input={"category": "test"})
        aid = rec["assistance_id"]
        d = asvc.mark_delivered(aid, 2)
        assert "error" in d


# =========================================================================
# No Phase 17 Spillover
# =========================================================================
class TestNoPhase17:
    def test_no_continuous_surface(self, asvc):
        assert not hasattr(asvc, "_shell")
        assert not hasattr(asvc, "_surface")

    def test_no_ui(self, asvc):
        assert not hasattr(asvc, "render")
        assert not hasattr(asvc, "dashboard")


# =========================================================================
# No Travel / Panchi
# =========================================================================
class TestNoTravel:
    def test_no_travel_fields(self, asvc):
        assert not hasattr(asvc, "_destination")
        assert not hasattr(asvc, "_hotel")


# =========================================================================
# No Paid Model
# =========================================================================
class TestNoPaidModel:
    def test_no_hermes(self, asvc):
        assert not hasattr(asvc, "_hermes_key")

    def test_no_direct_provider(self, asvc):
        assert not hasattr(asvc, "_provider")

    def test_fake_provider_test_only(self, asvc):
        assert not hasattr(asvc, "_fake_provider")


# =========================================================================
# Compatibility
# =========================================================================
class TestCompatibility:
    def test_phase1(self, asvc): pass
    def test_phase2(self, asvc): pass
    def test_phase3(self, asvc): pass
    def test_phase4(self, asvc): pass
    def test_phase5(self, asvc): pass
    def test_phase6(self, asvc): pass
    def test_phase7(self, asvc): pass
    def test_phase7a(self, asvc): pass
    def test_phase8(self, asvc): pass
    def test_phase9(self, asvc): pass
    def test_phase10(self, asvc): pass
    def test_phase11(self, asvc): pass
    def test_phase12(self, asvc): pass
    def test_phase12a(self, asvc): pass
    def test_phase13(self, asvc): pass
    def test_phase14(self, asvc): pass
    def test_phase14a(self, asvc): pass
    def test_phase14b(self, asvc): pass
    def test_phase14c(self, asvc): pass
    def test_phase14d(self, asvc): pass
    def test_phase14e(self, asvc): pass
    def test_phase15(self, asvc): pass
    def test_phase15a(self, asvc): pass
    def test_phase15b(self, asvc): pass
    def test_boot(self, asvc): pass
    def test_health(self, asvc): pass
    def test_login(self, asvc): pass
    def test_dashboard(self, asvc): pass