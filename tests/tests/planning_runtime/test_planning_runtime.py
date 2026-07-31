"""Tests for Planning & Reasoning Runtime."""

import pytest

from core.planning_runtime import (
    ConstraintCategory,
    ConstraintType,
    PlanningRuntime,
    PlanStatus,
    TaskType,
)


@pytest.fixture
def runtime():
    return PlanningRuntime()


class TestGoalDecomposition:
    def test_create_goal(self, runtime):
        g = runtime.create_goal("Sign contract", "Get customer signature", priority=10)
        assert g.label == "Sign contract"
        assert g.priority == 10

    def test_decompose(self, runtime):
        parent = runtime.create_goal("Deliver project")
        runtime.decompose_goal(parent.goal_id, ["Design", "Implement", "Test"])
        children = runtime.get_sub_goals(parent.goal_id)
        assert len(children) == 3

    def test_hierarchical_goals(self, runtime):
        top = runtime.create_goal("Top")
        mid = runtime.create_goal("Mid", parent_goal_id=top.goal_id)
        bot = runtime.create_goal("Bot", parent_goal_id=mid.goal_id)
        assert top.sub_goals == [mid.goal_id]
        assert mid.sub_goals == [bot.goal_id]


class TestTaskNetwork:
    def test_create_primitive(self, runtime):
        t = runtime.create_task("Send email", TaskType.PRIMITIVE, action_id="email.send",
                                estimated_cost=5.0, estimated_duration_sec=10)
        assert t.task_type == TaskType.PRIMITIVE
        assert t.action_id == "email.send"

    def test_create_compound(self, runtime):
        parent = runtime.create_task("Process order", TaskType.COMPOUND)
        runtime.decompose_task(parent.task_id, ["Validate", "Ship", "Invoice"])
        children = runtime.get_sub_tasks(parent.task_id)
        assert len(children) == 3

    def test_dependencies(self, runtime):
        a = runtime.create_task("A")
        b = runtime.create_task("B", dependencies=[a.task_id])
        assert b.dependencies == [a.task_id]


class TestPlanCreation:
    def test_create_plan(self, runtime):
        g = runtime.create_goal("Test")
        t = runtime.create_task("Do work")
        plan = runtime.create_plan("My Plan", g.goal_id, [t.task_id])
        assert plan.label == "My Plan"
        assert plan.status == PlanStatus.DRAFT
        assert len(plan.tasks) == 1

    def test_plan_total_cost(self, runtime):
        g = runtime.create_goal("Cost test")
        t1 = runtime.create_task("Task 1", estimated_cost=100)
        t2 = runtime.create_task("Task 2", estimated_cost=200)
        plan = runtime.create_plan("Cost Plan", g.goal_id, [t1.task_id, t2.task_id])
        runtime._update_plan_totals(plan)
        assert plan.total_cost == 300

    def test_missing_goal_raises(self, runtime):
        with pytest.raises(ValueError, match="Goal not found"):
            runtime.create_plan("Bad", "nonexistent")


class TestMultiStepReasoning:
    def test_reason_steps(self, runtime):
        g = runtime.create_goal("Reason test")
        a = runtime.create_task("Step A", estimated_cost=10, estimated_risk=0.1)
        b = runtime.create_task("Step B", dependencies=[a.task_id], estimated_cost=20)
        plan = runtime.create_plan("Reason Plan", g.goal_id, [a.task_id, b.task_id])
        steps = runtime.reason(plan.plan_id)
        assert len(steps) == 2
        assert steps[0]["task"] == "Step A"
        assert steps[1]["depends_on"] == ["Step A"]


class TestAlternatives:
    def test_generate_alternatives(self, runtime):
        g = runtime.create_goal("Alt test")
        tasks = [runtime.create_task(f"T{i}", estimated_cost=i*10) for i in range(3)]
        plan = runtime.create_plan("Alt Plan", g.goal_id, [t.task_id for t in tasks])
        alts = runtime.generate_alternatives(plan.plan_id, count=2)
        assert len(alts) == 2
        assert all(a.plan_id == plan.plan_id for a in alts)
        assert alts[0].label == "Variant 1"

    def test_get_alternatives(self, runtime):
        g = runtime.create_goal("GA")
        t = runtime.create_task("T")
        plan = runtime.create_plan("P", g.goal_id, [t.task_id])
        runtime.generate_alternatives(plan.plan_id, count=1)
        found = runtime.get_alternatives(plan.plan_id)
        assert len(found) == 1


class TestCostRiskEstimation:
    def test_estimate_plan(self, runtime):
        g = runtime.create_goal("Estimate")
        t = runtime.create_task("Task", estimated_cost=50, estimated_risk=0.2,
                                estimated_duration_sec=100)
        plan = runtime.create_plan("E Plan", g.goal_id, [t.task_id])
        est = runtime.estimate_plan(plan.plan_id)
        assert est["total_cost"] == 50
        assert est["total_risk"] == 0.2
        assert est["total_duration_sec"] == 100


class TestPlanValidation:
    def test_validate_valid_plan(self, runtime):
        g = runtime.create_goal("Validate good")
        t = runtime.create_task("Good task")
        plan = runtime.create_plan("Good", g.goal_id, [t.task_id])
        result = runtime.validate_plan(plan.plan_id)
        assert result["valid"] is True

    def test_validate_cycle_detected(self, runtime):
        g = runtime.create_goal("Cycle")
        a = runtime.create_task("A")
        b = runtime.create_task("B", dependencies=[a.task_id])
        a.dependencies.append(b.task_id)  # Create cycle
        plan = runtime.create_plan("Cycle Plan", g.goal_id, [a.task_id, b.task_id])
        result = runtime.validate_plan(plan.plan_id)
        assert result["valid"] is False
        assert any("cycle" in i.lower() for i in result["issues"])

    def test_validate_missing_dependency(self, runtime):
        g = runtime.create_goal("Missing dep")
        t = runtime.create_task("T", dependencies=["ghost"])
        plan = runtime.create_plan("Missing Dep", g.goal_id, [t.task_id])
        result = runtime.validate_plan(plan.plan_id)
        assert result["valid"] is False


class TestPlanRepair:
    def test_repair_plan(self, runtime):
        g = runtime.create_goal("Repair goal")
        t = runtime.create_task("Failing task")
        plan = runtime.create_plan("Original", g.goal_id, [t.task_id])
        repaired = runtime.repair_plan(plan.plan_id, t.task_id, "Replacement task")
        assert repaired is not None
        assert repaired.status == PlanStatus.REPAIRED
        assert repaired.version == 2
        assert len(repaired.tasks) == 1
        assert repaired.tasks[0].label == "Replacement task"

    def test_replan(self, runtime):
        g = runtime.create_goal("Replan goal")
        t = runtime.create_task("Old task")
        plan = runtime.create_plan("Old", g.goal_id, [t.task_id])
        new_plan = runtime.re_plan(plan.plan_id, "New approach")
        assert new_plan is not None
        assert new_plan.parent_plan_id == plan.plan_id
        assert new_plan.status == PlanStatus.DRAFT


class TestConstraints:
    def test_add_plan_constraint(self, runtime):
        g = runtime.create_goal("C goal")
        plan = runtime.create_plan("C Plan", g.goal_id)
        c = runtime.add_constraint(plan.plan_id,
                                    category=ConstraintCategory.BUDGET,
                                    constraint_type=ConstraintType.HARD,
                                    description="cost < 500")
        assert c is not None
        assert c.category == ConstraintCategory.BUDGET

    def test_add_task_constraint(self, runtime):
        t = runtime.create_task("T constrained")
        g = runtime.create_goal("C goal")
        plan = runtime.create_plan("C Plan", g.goal_id, [t.task_id])
        c = runtime.add_constraint(plan.plan_id, task_id=t.task_id,
                                    description="requires admin")
        assert c is not None
        assert c.description == "requires admin"

    def test_check_constraints(self, runtime):
        g = runtime.create_goal("Check goal")
        t = runtime.create_task("T")
        plan = runtime.create_plan("Check", g.goal_id, [t.task_id])
        runtime.add_constraint(plan.plan_id, description="cost < 1000")
        results = runtime.check_constraints(plan.plan_id)
        assert len(results) == 1
        assert results[0]["satisfied"] is True


class TestResourcePlanning:
    def test_allocate_resources(self, runtime):
        from core.planning_runtime.models import Resource
        g = runtime.create_goal("Resource goal")
        plan = runtime.create_plan("R Plan", g.goal_id)
        resources = [
            Resource(name="Engineer", quantity=2),
            Resource(name="Budget", quantity=5000),
        ]
        allocated = runtime.allocate_resources(plan.plan_id, resources)
        assert len(allocated) == 2
        assert len(plan.constraints) == 2


class TestTemporalPlanning:
    def test_compute_timeline_serial(self, runtime):
        g = runtime.create_goal("Timeline")
        a = runtime.create_task("Step A", estimated_duration_sec=10)
        b = runtime.create_task("Step B", dependencies=[a.task_id], estimated_duration_sec=20)
        plan = runtime.create_plan("T Plan", g.goal_id, [a.task_id, b.task_id])
        timeline = runtime.compute_timeline(plan.plan_id)
        assert len(timeline) == 2
        assert timeline[0]["task"] == "Step A"
        assert timeline[1]["start_sec"] >= timeline[0]["end_sec"]

    def test_compute_timeline_parallel(self, runtime):
        g = runtime.create_goal("Parallel")
        a = runtime.create_task("Root", estimated_duration_sec=5)
        b = runtime.create_task("B1", dependencies=[a.task_id], estimated_duration_sec=10)
        c = runtime.create_task("B2", dependencies=[a.task_id], estimated_duration_sec=15)
        plan = runtime.create_plan("P Plan", g.goal_id, [a.task_id, b.task_id, c.task_id])
        timeline = runtime.compute_timeline(plan.plan_id)
        assert len(timeline) == 3
        # B1 and B2 should start at roughly the same time (parallel after Root)
        b1 = next(t for t in timeline if t["task"] == "B1")
        b2 = next(t for t in timeline if t["task"] == "B2")
        assert abs(b1["start_sec"] - b2["start_sec"]) < 1


class TestApproval:
    def test_approve_plan(self, runtime):
        g = runtime.create_goal("Approval")
        plan = runtime.create_plan("A Plan", g.goal_id)
        runtime.approve_plan(plan.plan_id)
        assert plan.status == PlanStatus.APPROVED

    def test_approve_task(self, runtime):
        g = runtime.create_goal("Task approval")
        t = runtime.create_task("Needs approval", requires_approval=True)
        plan = runtime.create_plan("T Plan", g.goal_id, [t.task_id])
        approved = runtime.approve_task(plan.plan_id, t.task_id)
        assert approved is not None
        assert approved.approved is True


class TestObservability:
    def test_provenance(self, runtime):
        g = runtime.create_goal("Provenance")
        plan = runtime.create_plan("P Plan", g.goal_id)
        runtime.approve_plan(plan.plan_id)
        provenance = runtime.get_provenance(plan.plan_id)
        assert len(provenance) >= 1

    def test_stats(self, runtime):
        g = runtime.create_goal("Stats")
        runtime.create_plan("Plan 1", g.goal_id)
        runtime.create_plan("Plan 2", g.goal_id)
        stats = runtime.get_stats()
        assert stats.total_plans == 2

    def test_health(self, runtime):
        hc = runtime.health_check()
        assert hc["status"] == "healthy"
        assert hc["runtime"] == "planning_runtime"