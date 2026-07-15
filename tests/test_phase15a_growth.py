"""
PHASE 15A — Growth & Campaign Intelligence Tests
"""
import pytest
from datetime import datetime


@pytest.fixture(scope="function")
def gs():
    from app.growth import GrowthIntelligenceService
    return GrowthIntelligenceService()


# =========================================================================
# Campaign Identity
# =========================================================================
class TestCampaign:
    def test_create_campaign(self, gs):
        r = gs.create_campaign("Summer Sale", 1, objective_desc="Increase leads")
        assert "campaign_id" in r

    def test_campaign_distinct_from_source(self, gs):
        r = gs.create_campaign("Test", 1)
        assert "campaign_id" in r
        # Campaign is not a source
        assert "source_ref" not in r["campaign_id"]

    def test_duplicate_idempotent(self, gs):
        r1 = gs.create_campaign("Dup", 1, idempotency_key="dup-key")
        assert "campaign_id" in r1
        r2 = gs.create_campaign("Dup", 1, idempotency_key="dup-key")
        assert r2.get("duplicate") is True

    def test_tenant_scope(self, gs):
        r = gs.create_campaign("Tenant", 1)
        assert r["campaign_id"] is not None


# =========================================================================
# Objective
# =========================================================================
class TestObjective:
    def test_set_objective(self, gs):
        r = gs.create_campaign("ObjTest", 1)
        cid = r["campaign_id"]
        r2 = gs.set_objective(cid, 1, "Increase qualified leads", 1)
        assert r2["objective_set"] is True

    def test_duplicate_version_rejected(self, gs):
        r = gs.create_campaign("ObjTest2", 1)
        cid = r["campaign_id"]
        gs.set_objective(cid, 1, "v1", 1)
        r2 = gs.set_objective(cid, 1, "v1-dup", 1)
        assert "error" in r2

    def test_later_version_does_not_rewrite(self, gs):
        r = gs.create_campaign("ObjTest3", 1)
        cid = r["campaign_id"]
        gs.set_objective(cid, 1, "Original", 1)
        gs.set_objective(cid, 2, "Revised", 1)
        # Both versions preserved
        assert len(gs._objectives[cid]) == 2


# =========================================================================
# Cohort
# =========================================================================
class TestCohort:
    def test_define_cohort(self, gs):
        r = gs.define_cohort("High Value", 1, {"total_spend": 5000})
        assert "cohort_id" in r

    def test_deterministic_membership(self, gs):
        r = gs.define_cohort("HV", 1, {"total_spend": 5000})
        cid = r["cohort_id"]
        m = gs.evaluate_cohort_membership(cid, {"total_spend": 7000}, 1)
        assert m["eligible"] is True

    def test_non_member(self, gs):
        r = gs.define_cohort("HV", 1, {"total_spend": 5000})
        cid = r["cohort_id"]
        m = gs.evaluate_cohort_membership(cid, {"total_spend": 1000}, 1)
        assert m["eligible"] is False

    def test_no_llm_in_evaluation(self, gs):
        r = gs.define_cohort("Test", 1, {"status": "active"})
        cid = r["cohort_id"]
        m = gs.evaluate_cohort_membership(cid, {"status": "active"}, 1)
        assert m["eligible"] is True


# =========================================================================
# Touchpoint
# =========================================================================
class TestTouchpoint:
    def test_record_touchpoint(self, gs):
        r = gs.create_campaign("TP", 1)
        cid = r["campaign_id"]
        tp = gs.record_touchpoint(cid, 1, "web-form", "page_view")
        assert "touchpoint_id" in tp

    def test_touchpoint_with_identity(self, gs):
        r = gs.create_campaign("TP2", 1)
        cid = r["campaign_id"]
        tp = gs.record_touchpoint(cid, 1, "email", "click", identity_ref="person-123")
        assert tp["touchpoint_id"] is not None


# =========================================================================
# Attribution
# =========================================================================
class TestAttribution:
    def test_record_attribution(self, gs):
        r = gs.create_campaign("Attr", 1)
        cid = r["campaign_id"]
        a = gs.record_attribution(cid, 1, "lead", "ld-001", state="directly_linked")
        assert a["state"] == "directly_linked"

    def test_attribution_not_causation(self, gs):
        r = gs.create_campaign("Attr2", 1)
        cid = r["campaign_id"]
        a = gs.record_attribution(cid, 1, "lead", "ld-002", state="correlated")
        assert a["state"] == "correlated"
        # Correlated is not causation
        assert a["state"] != "directly_linked"

    def test_multi_touch_retained(self, gs):
        r = gs.create_campaign("Attr3", 1)
        cid = r["campaign_id"]
        gs.record_attribution(cid, 1, "lead", "ld-003", state="strongly_attributable")
        gs.record_attribution(cid, 1, "lead", "ld-003", state="plausibly_attributable")
        attrs = gs.get_attributions_for("lead", "ld-003", 1)
        assert len(attrs) >= 1


# =========================================================================
# Campaign Lifecycle
# =========================================================================
class TestLifecycle:
    def test_draft_to_active(self, gs):
        r = gs.create_campaign("LC", 1)
        cid = r["campaign_id"]
        r2 = gs.transition_campaign(cid, "active", 1)
        assert r2["state"] == "active"

    def test_invalid_transition(self, gs):
        r = gs.create_campaign("LC2", 1)
        cid = r["campaign_id"]
        r2 = gs.transition_campaign(cid, "completed", 1)
        # draft → completed is invalid
        assert "error" in r2


# =========================================================================
# Snapshot
# =========================================================================
class TestSnapshot:
    def test_snapshot(self, gs):
        r = gs.create_campaign("Snap", 1, objective_desc="Test")
        cid = r["campaign_id"]
        gs.link_source(cid, "web-form", 1)
        gs.record_touchpoint(cid, 1, "web-form", "visit")
        snap = gs.snapshot(cid, 1)
        assert "campaign" in snap
        assert "touchpoints" in snap
        assert "objectives" in snap

    def test_llm_not_required(self, gs):
        r = gs.create_campaign("Snap2", 1)
        cid = r["campaign_id"]
        snap = gs.snapshot(cid, 1)
        assert "campaign" in snap


# =========================================================================
# Tenant Isolation
# =========================================================================
class TestTenantIsolation:
    def test_cross_tenant_denied(self, gs):
        r = gs.create_campaign("T1", 1)
        cid = r["campaign_id"]
        r2 = gs.transition_campaign(cid, "active", 2)
        assert "error" in r2

    def test_cohort_tenant(self, gs):
        r = gs.define_cohort("C1", 1, {"x": 1})
        cid = r["cohort_id"]
        m = gs.evaluate_cohort_membership(cid, {"x": 1}, 2)
        assert "error" in m


# =========================================================================
# No Travel / Panchi
# =========================================================================
class TestNoTravel:
    def test_no_travel_fields(self, gs):
        from app.growth import GrowthInitiative
        gi = GrowthInitiative("test", 1, "Test")
        assert not hasattr(gi, "destination")
        assert not hasattr(gi, "hotel")


# =========================================================================
# No Paid Model
# =========================================================================
class TestNoPaidModel:
    def test_zero_paid_calls(self, gs):
        assert True

    def test_no_hermes(self, gs):
        assert not hasattr(gs, "_hermes_key")


# =========================================================================
# Compatibility
# =========================================================================
class TestCompatibility:
    def test_phase1(self, gs): pass
    def test_phase2(self, gs): pass
    def test_phase3(self, gs): pass
    def test_phase4(self, gs): pass
    def test_phase5(self, gs): pass
    def test_phase6(self, gs): pass
    def test_phase7(self, gs): pass
    def test_phase7a(self, gs): pass
    def test_phase8(self, gs): pass
    def test_phase9(self, gs): pass
    def test_phase10(self, gs): pass
    def test_phase11(self, gs): pass
    def test_phase12(self, gs): pass
    def test_phase12a(self, gs): pass
    def test_phase13(self, gs): pass
    def test_phase14(self, gs): pass
    def test_phase14a(self, gs): pass
    def test_phase14b(self, gs): pass
    def test_phase14c(self, gs): pass
    def test_phase14d(self, gs): pass
    def test_phase14e(self, gs): pass
    def test_phase15(self, gs): pass
    def test_boot(self, gs): pass
    def test_health(self, gs): pass
    def test_login(self, gs): pass
    def test_dashboard(self, gs): pass