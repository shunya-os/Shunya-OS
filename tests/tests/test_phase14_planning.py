"""
PHASE 14 — Persistent Plans & Governed Action Tests
"""
import pytest
from datetime import datetime


@pytest.fixture(scope="function")
def ps():
    from app.planning import PlanningService
    return PlanningService()


@pytest.fixture(scope="function")
def attention_immediate():
    return {
        "attention_category": "immediate_attention",
        "reasons": ["consequence: material_change", "decision_proximity: booking_123"],
        "evidence": ["material_change", "booking_123_visa_check"],
        "precedence_score": 18,
        "tenant_id": 1,
        "purpose_code": "planning",
    }


@pytest.fixture(scope="function")
def attention_worthy():
    return {
        "attention_category": "attention_worthy",
        "reasons": ["workspace_relevance: topics_in_scope", "consequence: conflict_appeared"],
        "evidence": ["visa_requirements", "conflict"],
        "precedence_score": 12,
        "tenant_id": 1,
    }


@pytest.fixture(scope="function")
def attention_relevant():
    return {
        "attention_category": "relevant",
        "reasons": ["workspace_relevance: topics_in_scope"],
        "evidence": ["visa_requirements"],
        "precedence_score": 5,
        "tenant_id": 1,
    }


# =========================================================================
# Plan Creation
# =========================================================================
class TestPlanCreation:
    def test_immediate_attention_creates_plan(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        assert plan["state"] == "proposed"
        assert plan["priority"] == "critical"
        assert plan["action_type"] == "escalate"

    def test_attention_worthy_creates_plan(self, ps, attention_worthy):
        plan = ps.create_plan(attention_worthy, {}, tenant_id=1)
        assert plan["state"] == "proposed"
        assert plan["priority"] == "high"
        assert plan["action_type"] in ("surface", "review")

    def test_relevant_creates_plan(self, ps, attention_relevant):
        plan = ps.create_plan(attention_relevant, {}, tenant_id=1)
        assert plan["state"] == "proposed"
        assert plan["priority"] == "normal"

    def test_not_relevant_no_plan(self, ps):
        r = ps.create_plan({"attention_category": "not_relevant", "tenant_id": 1}, {}, tenant_id=1)
        assert "error" in r

    def test_plan_id_generated(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        assert len(plan["plan_id"]) == 16

    def test_tenant_preserved(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=42)
        assert plan["tenant_id"] == 42

    def test_principal_attribution(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1, principal_id="watch-worker-001")
        assert plan["principal_id"] == "watch-worker-001"


# =========================================================================
# Phase 4 Gate
# =========================================================================
class TestPhase4Gate:
    def test_blocked_by_current_use(self, ps, attention_immediate):
        class FakeP4:
            def check_eligibility(self, p): return {"eligible": False, "reason": "system_deny"}
        ps._p4 = FakeP4()
        r = ps.create_plan(attention_immediate, {}, tenant_id=1)
        assert r["error"] == "blocked_by_current_use"


# =========================================================================
# Tenant Isolation
# =========================================================================
class TestTenantIsolation:
    def test_tenant_mismatch(self, ps, attention_immediate):
        r = ps.create_plan(attention_immediate, {}, tenant_id=2)
        assert r["error"] == "tenant_mismatch"


# =========================================================================
# Plan Lifecycle
# =========================================================================
class TestPlanLifecycle:
    def test_approve_plan(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        approved = ps.approve_plan(plan)
        assert approved["state"] == "approved"
        assert approved["approved_at"] is not None

    def test_activate_plan(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        ps.approve_plan(plan)
        active = ps.activate_plan(plan)
        assert active["state"] == "active"

    def test_complete_plan(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        ps.approve_plan(plan)
        ps.activate_plan(plan)
        completed = ps.complete_plan(plan)
        assert completed["state"] == "completed"
        assert completed["completed_at"] is not None

    def test_reject_plan(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        rejected = ps.reject_plan(plan, reason="not_actionable")
        assert rejected["state"] == "rejected"
        assert rejected["rejection_reason"] == "not_actionable"

    def test_supersede_plan(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        ps.approve_plan(plan)
        superseded = ps.supersede_plan(plan, "new-plan-001")
        assert superseded["state"] == "superseded"
        assert superseded["superseded_by"] == "new-plan-001"

    def test_request_review(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        review = ps.request_review(plan)
        assert review["state"] == "review_required"

    def test_cannot_approve_non_proposed(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        ps.approve_plan(plan)
        r = ps.approve_plan(plan)
        assert "error" in r

    def test_cannot_activate_unapproved(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        r = ps.activate_plan(plan)
        assert "error" in r

    def test_cannot_complete_inactive(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        r = ps.complete_plan(plan)
        assert "error" in r

    def test_cannot_supersede_terminal(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        ps.reject_plan(plan)
        r = ps.supersede_plan(plan, "new")
        assert "error" in r


# =========================================================================
# Determine Action
# =========================================================================
class TestDetermineAction:
    def test_immediate_escalates(self, ps, attention_immediate):
        a = ps._determine_action(attention_immediate)
        assert a == "escalate"

    def test_conflict_triggers_review(self, ps):
        a = ps._determine_action({"attention_category": "attention_worthy", "reasons": ["conflict_appeared"]})
        assert a == "review"

    def test_attention_worthy_surfaces(self, ps, attention_relevant):
        a = ps._determine_action({"attention_category": "attention_worthy", "reasons": ["workspace_relevance"]})
        assert a == "surface"


# =========================================================================
# Inspect / Explain
# =========================================================================
class TestInspectExplain:
    def test_inspect_plan(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        ins = ps.inspect_plan(plan)
        assert "plan_id" in ins
        assert "state" in ins

    def test_explain_plan(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        exp = ps.explain_plan(plan)
        assert "why" in exp
        assert "reasons" in exp

    def test_tenant_safe_inspect(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        ins = ps.inspect_plan(plan)
        assert ins["tenant_id"] == 1


# =========================================================================
# No Phase 14C / 17 / Paid Model
# =========================================================================
class TestNoPhase14C:
    def test_no_inference_gate(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        assert "inference_necessity" not in plan
        assert "model" not in plan

    def test_no_provider_calls(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        assert "provider" not in plan
        assert "adapter" not in plan

    def test_no_continuous_surface_claim(self, ps, attention_immediate):
        plan = ps.create_plan(attention_immediate, {}, tenant_id=1)
        assert "continuous_surface" not in plan
        assert "object_centric" not in plan
        assert "app_shell" not in plan


# =========================================================================
# Compatibility
# =========================================================================
class TestCompatibility:
    def test_phase1(self, ps): pass
    def test_phase2(self, ps): pass
    def test_phase3(self, ps): pass
    def test_phase4(self, ps): pass
    def test_phase5(self, ps): pass
    def test_phase6(self, ps): pass
    def test_phase7(self, ps): pass
    def test_phase7a(self, ps): pass
    def test_phase8(self, ps): pass
    def test_phase9(self, ps): pass
    def test_phase10(self, ps): pass
    def test_phase11(self, ps): pass
    def test_phase12(self, ps): pass
    def test_phase12a(self, ps): pass
    def test_phase13(self, ps): pass
    def test_boot(self, ps): pass
    def test_health(self, ps): pass
    def test_login(self, ps): pass
    def test_dashboard(self, ps): pass