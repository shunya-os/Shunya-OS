"""
Tests for SHUNYA Universal Planning Runtime — Phase Z8.

Validates: Objective lifecycle, Plan generation, Milestone ordering,
Dependency graph, Checkpoint engine, Inspection chain, Agnosticism.
"""

import pytest


@pytest.fixture(autouse=True)
def _app_context(app):
    """Provide Flask app context for tests that access DB."""
    pass
from app.planning.objective import (
    Objective, ObjectiveStatus, get_store, reset_store,
)
from app.planning.plan import (
    Plan, Milestone, PlanVersion, PlanStatus, PlanEngine, get_engine, reset_engine,
)
from app.planning.dependency import (
    Dependency, DependencyGraph, get_graph, reset_graph,
)
from app.planning.checkpoint import (
    Checkpoint, CheckpointStatus, CheckpointEngine, get_engine as get_cp_engine,
    reset_engine as reset_cp_engine,
)


# ══════════════════════════════════════════════════════════════
# Objective Tests
# ══════════════════════════════════════════════════════════════


class TestObjective:
    def test_create_objective(self):
        o = Objective(objective_id="o1", purpose="Test objective", priority=1)
        assert o.objective_id == "o1"
        assert o.status == ObjectiveStatus.DRAFT

    def test_transition(self):
        o = Objective(objective_id="o1", purpose="Test", status=ObjectiveStatus.DRAFT)
        o.transition_to(ObjectiveStatus.ACTIVE)
        assert o.status == ObjectiveStatus.ACTIVE

    def test_invalid_transition(self):
        o = Objective(objective_id="o1", purpose="Test", status=ObjectiveStatus.COMPLETED)
        with pytest.raises(ValueError, match="Cannot transition"):
            o.transition_to(ObjectiveStatus.ACTIVE)

    def test_full_lifecycle(self):
        o = Objective(objective_id="o1", purpose="Test")
        o.transition_to(ObjectiveStatus.ACTIVE)
        o.transition_to(ObjectiveStatus.COMPLETED)
        assert o.status == ObjectiveStatus.COMPLETED
        assert o.completed_at is not None

    def test_to_dict(self):
        o = Objective(objective_id="o1", purpose="Test", priority=2, owner_actor_id="a1")
        d = o.to_dict()
        assert d["objective_id"] == "o1"
        assert d["priority"] == 2
        assert d["owner_actor_id"] == "a1"


class TestObjectiveStore:
    def setup_method(self):
        reset_store()

    def test_add_and_get(self):
        store = get_store()
        store.add(Objective(objective_id="o1", purpose="Test"))
        assert store.get("o1") is not None
        assert store.count == 1

    def test_get_active(self):
        store = get_store()
        store.add(Objective(objective_id="o1", purpose="T1", status=ObjectiveStatus.ACTIVE))
        store.add(Objective(objective_id="o2", purpose="T2", status=ObjectiveStatus.DRAFT))
        assert len(store.get_active()) == 1

    def test_get_by_owner(self):
        store = get_store()
        store.add(Objective(objective_id="o1", purpose="T1", owner_actor_id="a1"))
        store.add(Objective(objective_id="o2", purpose="T2", owner_actor_id="a2"))
        assert len(store.get_by_owner("a1")) == 1


# ══════════════════════════════════════════════════════════════
# Plan Engine Tests
# ══════════════════════════════════════════════════════════════


class TestPlan:
    def test_create_plan(self):
        engine = PlanEngine()
        milestones = [Milestone(milestone_id="m1", plan_id="p1", label="First", order=1)]
        plan = engine.create_plan("obj1", "Test plan", milestones)
        assert plan.objective_id == "obj1"
        assert plan.status == PlanStatus.DRAFT
        assert len(plan.milestones) == 1

    def test_plan_transition(self):
        engine = PlanEngine()
        plan = engine.create_plan("obj1", "Test", [])
        plan.transition_to(PlanStatus.ACTIVE)
        assert plan.status == PlanStatus.ACTIVE

    def test_milestone_complete(self):
        ms = Milestone(milestone_id="m1", plan_id="p1", label="Test")
        assert not ms.is_completed
        ms.complete()
        assert ms.is_completed
        assert ms.completed_at is not None

    def test_plan_versioning(self):
        engine = PlanEngine()
        v1 = [Milestone(milestone_id="m1", plan_id="p1", label="V1", order=1)]
        plan = engine.create_plan("obj1", "Test", v1)
        assert plan.current_version == 1
        v2 = PlanVersion(version_id="v2", plan_id=plan.plan_id, version_number=2,
                         milestones=[Milestone(milestone_id="m2", plan_id="p1", label="V2", order=1)])
        plan.add_version(v2)
        assert plan.current_version == 2
        assert len(plan.versions) == 2

    def test_plan_to_dict(self):
        engine = PlanEngine()
        plan = engine.create_plan("obj1", "Test", [])
        d = plan.to_dict()
        assert d["objective_id"] == "obj1"
        assert d["version_count"] == 1


# ══════════════════════════════════════════════════════════════
# Dependency Graph Tests
# ══════════════════════════════════════════════════════════════


class TestDependencyGraph:
    def setup_method(self):
        reset_graph()

    def test_add_dependency(self):
        g = get_graph()
        g.add(Dependency(dep_id="d1", source_id="ms1", target_id="ms2", dep_type="finish_to_start"))
        assert g.count == 1

    def test_dependency_types(self):
        g = get_graph()
        for t in ["finish_to_start", "start_to_start", "finish_to_finish", "soft", "hard", "conditional", "cross_domain"]:
            g.add(Dependency(dep_id=f"d_{t}", source_id="s", target_id="t", dep_type=t))
        assert g.count == 7

    def test_dependency_satisfaction(self):
        g = get_graph()
        g.add(Dependency(dep_id="d1", source_id="ms1", target_id="ms2", dep_type="finish_to_start"))
        assert not g.are_all_dependencies_satisfied("ms2")
        g.satisfy("d1")
        assert g.are_all_dependencies_satisfied("ms2")

    def test_no_dependencies(self):
        g = get_graph()
        assert g.are_all_dependencies_satisfied("ms_any")


# ══════════════════════════════════════════════════════════════
# Checkpoint Engine Tests
# ══════════════════════════════════════════════════════════════


class TestCheckpoint:
    def setup_method(self):
        reset_cp_engine()

    def test_create_checkpoint(self):
        cp = Checkpoint(checkpoint_id="cp1", milestone_id="ms1", label="Verify", evidence_required="Sign-off")
        assert cp.status == CheckpointStatus.PENDING

    def test_pass_checkpoint(self):
        cp = Checkpoint(checkpoint_id="cp1", milestone_id="ms1", label="Verify")
        cp.pass_checkpoint(evidence_id="evid_001")
        assert cp.status == CheckpointStatus.PASSED
        assert cp.resolved_at is not None
        assert "evid_001" in cp.evidence_ids

    def test_fail_checkpoint(self):
        cp = Checkpoint(checkpoint_id="cp1", milestone_id="ms1", label="Verify")
        cp.fail_checkpoint("Evidence not provided")
        assert cp.status == CheckpointStatus.FAILED

    def test_all_passed(self):
        engine = get_cp_engine()
        engine.add(Checkpoint(checkpoint_id="cp1", milestone_id="ms1", label="C1"))
        engine.add(Checkpoint(checkpoint_id="cp2", milestone_id="ms1", label="C2"))
        assert not engine.all_passed("ms1")
        engine.get("cp1").pass_checkpoint()
        engine.get("cp2").pass_checkpoint()
        assert engine.all_passed("ms1")

    def test_no_checkpoints(self):
        engine = get_cp_engine()
        assert engine.all_passed("ms_any")


# ══════════════════════════════════════════════════════════════
# Business Agnosticism Tests
# ══════════════════════════════════════════════════════════════


class TestBusinessAgnosticism:
    def test_objective_no_industry(self):
        o = Objective(objective_id="o1", purpose="Test")
        assert not hasattr(o, "project")
        assert not hasattr(o, "department")

    def test_plan_no_industry(self):
        ms = Milestone(milestone_id="m1", plan_id="p1", label="T")
        assert not hasattr(ms, "task_type")
        assert not hasattr(ms, "assignee")

    def test_dependency_no_industry(self):
        d = Dependency(dep_id="d1", source_id="s", target_id="t", dep_type="finish_to_start")
        assert not hasattr(d, "project")
        assert not hasattr(d, "team")


# ══════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════


class TestPlanningIntegration:
    def test_planning_loads_with_app(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            assert c.get('/health').status_code == 200
            # / route may return 200 (frontend built) or 503 (CI runs Python tests first)
            assert c.get('/').status_code in (200, 503)
            r = c.get('/workspace/?inspect_planning=1')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert 'objectives' in data
            assert 'plans' in data
            assert 'dependencies' in data
            assert 'checkpoints' in data

    def test_objectives_loaded_on_startup(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            r = c.get('/workspace/?inspect_planning=1')
            data = r.get_json()
            assert data['objectives']['total'] >= 1
            assert data['plans']['total'] >= 1
            assert data['dependencies']['total'] >= 1
            assert data['checkpoints']['total'] >= 1