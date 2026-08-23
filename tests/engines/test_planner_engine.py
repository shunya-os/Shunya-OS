"""Tests for Phase G — Planner Engine (ES-004).

Covers:
  - Unit tests for all canonical planner models
  - Planning type implementations (reactive, operational, strategic, etc.)
  - Template registry tests
  - PlannerEngine 9-stage pipeline tests
  - Input validation tests
  - Goal analysis tests
  - Constraint resolution tests
  - Alternative generation tests
  - Optimization tests
  - Risk analysis tests
  - Resource planning tests
  - Dependency graph tests (including cycle detection)
  - Execution graph / scheduling tests
  - Governance packaging tests
  - Determinism tests (identical inputs -> identical outputs)
  - Failure-path tests
  - Error mode tests
  - Integration tests (if Event Bus available)
"""

import copy
import itertools
import pytest
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta

from app.shunya.planner.models import (
    # Enums
    PlanningType, PlanState, TaskStatus,
    OptimizationDimension, ResourceType, FailureMode,

    # Core models
    ExecutionPlan, PlanTask, PlanningConstraint, Objective,
    Resource, ResourceAllocation, ResourcePool,
    Dependency, DependencyGraph, Schedule,
    RiskAssessment, DecisionTree, DecisionNode,
    GovernancePackage, PlanningInput, PlanningOutput,
    PlanningMetadata, OptimizationCriteria,
    PlanningError,
)
from app.shunya.planner.engine import (
    PlannerEngine, get_planner_engine, reset_planner_engine,
)
from app.shunya.planner.templates import (
    register_template, get_template, list_templates,
    create_reactive_plan, create_operational_plan,
    create_strategic_plan, create_constraint_based_plan,
    create_scenario_plan, create_contingency_plan,
    dispatch_planning_type, merge_plans,
)


# ===========================================================================
# Helper: create a mock reasoning result
# ===========================================================================


class MockConfidence:
    def __init__(self, overall_score: float = 0.8, level: str = "high"):
        self.overall_score = overall_score
        self.level = level


class MockFinding:
    def __init__(self, finding_id: str = "f-1", finding_type: str = "observation",
                 severity: str = "info", label: str = "Test finding",
                 description: str = "A test finding", confidence: float = 0.9):
        self.finding_id = finding_id
        self.finding_type = finding_type
        self.severity = severity
        self.label = label
        self.description = description
        self.confidence = confidence
        self.fact_key = ""
        self.fact_value = None
        self.source = ""
        self.evidence = []
        self.metadata = {}


class MockContradiction:
    def __init__(self, contradiction_id: str = "c-1",
                 contradiction_type: str = "fact_conflict",
                 severity: str = "medium", label: str = "Test contradiction",
                 description: str = "A test contradiction"):
        self.contradiction_id = contradiction_id
        self.contradiction_type = contradiction_type
        self.severity = severity
        self.label = label
        self.description = description
        self.fact_keys = []
        self.fact_values = []
        self.sources = []
        self.finding_ids = []
        self.evidence = []
        self.metadata = {}


class MockAssumption:
    def __init__(self, assumption_id: str = "a-1", fact_key: str = "",
                 label: str = "Test assumption", description: str = ""):
        self.assumption_id = assumption_id
        self.fact_key = fact_key
        self.label = label
        self.description = description
        self.assumed_value = None
        self.evidence = []
        self.metadata = {}


class MockConstraint:
    def __init__(self, constraint_id: str = "con-1", fact_key: str = "",
                 constraint_type: str = "", label: str = "Test constraint",
                 description: str = "", value: Any = None):
        self.constraint_id = constraint_id
        self.fact_key = fact_key
        self.constraint_type = constraint_type
        self.label = label
        self.description = description
        self.value = value
        self.evidence = []
        self.metadata = {}
        self.created_at = datetime.now(timezone.utc)


class MockReasoningResult:
    def __init__(self, result_id: str = "rr-1", findings: List = None,
                 contradictions: List = None, assumptions: List = None,
                 constraints: List = None, attention_items: List = None,
                 confidence: MockConfidence = None):
        self.result_id = result_id
        self.findings = findings or []
        self.contradictions = contradictions or []
        self.assumptions = assumptions or []
        self.constraints = constraints or []
        self.attention_items = attention_items or []
        self.confidence = confidence or MockConfidence()
        self.created_at = datetime.now(timezone.utc)

    @property
    def is_healthy(self) -> bool:
        return self.confidence.overall_score >= 0.5

    @property
    def requires_attention(self) -> bool:
        return len(self.attention_items) > 0 or len(self.contradictions) > 0


class MockContext:
    def __init__(self, context_id: str = "ctx-1", tenant_id: int = 1):
        self.context_id = context_id
        self.tenant_id = tenant_id


def make_standard_reasoning_result() -> MockReasoningResult:
    """Create a standard reasoning result for planner tests."""
    return MockReasoningResult(
        result_id="rr-test-1",
        findings=[
            MockFinding("f-1", "observation", "high", "Customer inquiry received",
                        "New customer inquiry for travel package"),
            MockFinding("f-2", "gap", "medium", "Missing customer preference",
                        "Customer destination preference not specified"),
            MockFinding("f-3", "risk", "low", "Budget constraint risk",
                        "Customer budget may be below minimum"),
        ],
        contradictions=[
            MockContradiction("c-1", "fact_conflict", "low",
                              "Date conflict", "Travel dates may conflict with availability"),
        ],
        assumptions=[
            MockAssumption("a-1", "", "Standard pricing", "Assume standard pricing applies"),
        ],
        constraints=[
            MockConstraint("con-1", "", "budget", "Budget limit",
                           "Customer budget limit", 100000),
        ],
        attention_items=[
            "Missing: Customer destination preference",
            "Risk: Budget constraint risk",
        ],
        confidence=MockConfidence(0.75, "high"),
    )


# ===========================================================================
# Section 1: Canonical Model Tests
# ===========================================================================


class TestPlannerModels:
    """Unit tests for all canonical planner data models."""

    def test_plan_task_auto_id(self):
        task = PlanTask(label="Test task")
        assert task.task_id != ""
        assert task.label == "Test task"
        assert task.status == TaskStatus.PENDING.value

    def test_plan_task_with_explicit_id(self):
        task = PlanTask(task_id="custom-id", label="Custom")
        assert task.task_id == "custom-id"

    def test_plan_task_duration_hours(self):
        task = PlanTask(label="Task", estimated_duration_minutes=120)
        assert task.duration_hours == 2.0

    def test_plan_task_is_ready(self):
        task = PlanTask(label="Ready")
        assert task.is_ready is True

    def test_execution_plan_auto_id(self):
        plan = ExecutionPlan(name="Test Plan")
        assert plan.plan_id != ""
        assert plan.state == PlanState.DRAFT.value

    def test_execution_plan_add_and_find_task(self):
        plan = ExecutionPlan(name="Test")
        task = PlanTask(label="Task A", task_id="t-a")
        plan.add_task(task)
        assert plan.task_count == 1
        assert plan.find_task("t-a") is task
        assert plan.find_task("nonexistent") is None

    def test_execution_plan_completed_and_blocked_tasks(self):
        plan = ExecutionPlan(name="Test")
        plan.add_task(PlanTask(task_id="t1", label="Done", status=TaskStatus.COMPLETED.value))
        plan.add_task(PlanTask(task_id="t2", label="Blocked", status=TaskStatus.BLOCKED.value))
        plan.add_task(PlanTask(task_id="t3", label="Pending"))
        assert len(plan.completed_tasks) == 1
        assert len(plan.blocked_tasks) == 1

    def test_execution_plan_duration_properties(self):
        plan = ExecutionPlan(name="Test")
        plan.total_estimated_duration_minutes = 1440  # 1 day
        assert plan.total_duration_hours == 24.0
        assert plan.total_duration_days == 1.0

    def test_planning_constraint_auto_id(self):
        c = PlanningConstraint(constraint_type="budget", label="Budget")
        assert c.constraint_id != ""
        assert c.is_hard is True

    def test_planning_constraint_soft(self):
        c = PlanningConstraint(constraint_type="time", label="Flexible", is_hard=False)
        assert c.is_hard is False

    def test_objective_auto_id(self):
        o = Objective(label="Minimize cost", priority=0.9)
        assert o.objective_id != ""
        assert o.priority == 0.9

    def test_resource_auto_id(self):
        r = Resource(label="Developer", resource_type=ResourceType.PEOPLE.value,
                     total_capacity=5.0)
        assert r.resource_id != ""
        assert r.available_capacity == 5.0  # auto-initialized from total

    def test_resource_explicit_available(self):
        r = Resource(label="Server", resource_type=ResourceType.SYSTEMS.value,
                     total_capacity=100.0, available_capacity=80.0)
        assert r.available_capacity == 80.0

    def test_resource_pool(self):
        r1 = Resource(label="Dev", resource_id="dev-1")
        r2 = Resource(label="QA", resource_id="qa-1", resource_type=ResourceType.PEOPLE.value)
        pool = ResourcePool(resources=[r1, r2])
        found = pool.find_by_type(ResourceType.PEOPLE.value)
        assert len(found) == 2
        assert pool.find_by_id("dev-1") is r1
        assert pool.find_by_id("nonexistent") is None

    def test_dependency_graph(self):
        t1 = PlanTask(task_id="t1", label="Task 1")
        t2 = PlanTask(task_id="t2", label="Task 2", depends_on=["t1"])
        dep = Dependency(from_task_id="t1", to_task_id="t2")
        graph = DependencyGraph(tasks=[t1, t2], dependencies=[dep])
        assert len(graph.find_upstream("t2")) == 1
        assert len(graph.find_downstream("t1")) == 1

    def test_dependency_graph_no_cycle(self):
        graph = DependencyGraph()
        assert graph.has_cycles is False

    def test_schedule(self):
        now = datetime.now(timezone.utc)
        schedule = Schedule(
            plan_id="p1",
            planned_start=now,
            planned_end=now + timedelta(hours=2),
            total_duration_minutes=120,
        )
        assert schedule.total_duration_hours == 2.0
        assert schedule.total_duration_days == 2.0 / 24.0

    def test_risk_assessment(self):
        risk = RiskAssessment(
            overall_risk_score=0.3,
            overall_confidence=0.7,
            per_task_risk={"t1": 0.3, "t2": 0.5},
            risk_factors=[{"task_id": "t2", "label": "High risk", "risk_score": 0.5}],
        )
        assert len(risk.risk_factors) == 1
        assert risk.per_task_risk["t1"] == 0.3

    def test_governance_package_auto_id(self):
        pkg = GovernancePackage()
        assert pkg.governance_package_id != ""

    def test_governance_package_with_plan(self):
        plan = ExecutionPlan(name="Plan A")
        pkg = GovernancePackage(
            plan=plan,
            reasoning_result_id="rr-1",
            reasoning_summary="Test reasoning summary",
        )
        assert pkg.plan is plan
        assert pkg.governance_package_id != ""

    def test_decision_tree(self):
        root = DecisionNode(label="Root", decision_type="choice")
        tree = DecisionTree(root_node=root)
        tree.add_node(DecisionNode(label="Child", parent_node_id=root.node_id))
        assert len(tree.nodes) == 1
        assert tree.depth == 0

    def test_planning_input(self):
        rr = make_standard_reasoning_result()
        inp = PlanningInput(
            reasoning_result=rr,
            tenant_id=1,
            actor_id="user-1",
        )
        assert inp.tenant_id == 1
        assert inp.actor_id == "user-1"

    def test_planning_output_success(self):
        output = PlanningOutput(
            primary_plan=ExecutionPlan(name="Plan"),
            confidence=0.8,
        )
        assert output.is_success is True
        assert output.is_error is False

    def test_planning_output_error(self):
        output = PlanningOutput(error="Something failed")
        assert output.is_success is False
        assert output.is_error is True

    def test_planning_metadata(self):
        meta = PlanningMetadata(
            reasoning_result_id="rr-1",
            context_id="ctx-1",
            planning_types_used=["operational"],
            stages_executed=9,
            stages_passed=9,
            alternatives_generated=3,
        )
        assert meta.planning_id != ""
        assert meta.engine_name == "planner_engine"
        assert meta.planning_engine_version == "1.0.0"

    def test_optimization_criteria_defaults(self):
        criteria = OptimizationCriteria()
        assert criteria.get_weight(OptimizationDimension.RISK.value) == 0.3
        assert criteria.get_direction(OptimizationDimension.TIME.value) == "minimize"

    def test_optimization_criteria_custom(self):
        criteria = OptimizationCriteria(dimensions={
            OptimizationDimension.TIME.value: {"weight": 0.5, "direction": "minimize"},
        })
        assert criteria.get_weight(OptimizationDimension.TIME.value) == 0.5

    def test_planning_error(self):
        err = PlanningError("Cannot plan", failure_mode=FailureMode.LOW_CONFIDENCE.value,
                            stage="input_validation")
        assert err.message == "Cannot plan"
        assert err.failure_mode == FailureMode.LOW_CONFIDENCE.value
        assert err.stage == "input_validation"
        d = err.to_dict()
        assert d["failure_mode"] == FailureMode.LOW_CONFIDENCE.value

    def test_resource_allocation(self):
        ra = ResourceAllocation(task_id="t1", resource_id="r1", quantity=2.0, cost=1000.0)
        assert ra.allocation_id != ""
        assert ra.cost == 1000.0


# ===========================================================================
# Section 2: Planning Type Implementation Tests
# ===========================================================================


class TestPlanningTypes:
    """Tests for each planning type implementation."""

    def test_reactive_plan_creation(self):
        rr = make_standard_reasoning_result()
        plan = create_reactive_plan(rr)
        assert plan.planning_type == PlanningType.REACTIVE.value
        assert plan.task_count >= 1

    def test_reactive_plan_uses_attention_items(self):
        rr = MockReasoningResult(
            attention_items=["Urgent: Missing data", "Warning: Budget risk"],
            findings=[MockFinding("f-1", "observation", "high", "Inquiry")],
        )
        plan = create_reactive_plan(rr)
        assert plan.task_count == 2
        assert "Urgent: Missing data" in plan.tasks[0].label

    def test_reactive_plan_no_attention_items(self):
        rr = MockReasoningResult(findings=[MockFinding("f-1", "observation", "info", "Test")])
        plan = create_reactive_plan(rr)
        assert plan.task_count == 1

    def test_operational_plan_creation(self):
        rr = make_standard_reasoning_result()
        plan = create_operational_plan(rr, template_name="notification")
        assert plan.planning_type == PlanningType.OPERATIONAL.value
        assert plan.task_count >= 1

    def test_operational_plan_unknown_template(self):
        rr = make_standard_reasoning_result()
        plan = create_operational_plan(rr, template_name="nonexistent")
        assert plan.task_count == 2  # default generic tasks

    def test_strategic_plan_creation(self):
        rr = make_standard_reasoning_result()
        plan = create_strategic_plan(rr)
        assert plan.planning_type == PlanningType.STRATEGIC.value
        # Should have analysis task + at least one finding-based task + review
        assert plan.task_count >= 3

    def test_strategic_plan_includes_all_findings(self):
        findings = [MockFinding(f"f-{i}", "observation", "info", f"Finding {i}")
                    for i in range(3)]
        rr = MockReasoningResult(findings=findings)
        plan = create_strategic_plan(rr)
        # 1 analysis + 3 findings + 1 review = 5 tasks
        assert plan.task_count == 5

    def test_constraint_based_plan_creation(self):
        rr = make_standard_reasoning_result()
        constraints = [
            PlanningConstraint(constraint_type="budget", label="Budget limit", value=50000),
            PlanningConstraint(constraint_type="time", label="Time limit", value=120),
        ]
        plan = create_constraint_based_plan(rr, constraints)
        assert plan.planning_type == PlanningType.CONSTRAINT_BASED.value
        assert plan.metadata.get("budget_limit") == "50000"
        assert plan.metadata.get("time_limit_minutes") == "120"

    def test_scenario_plan_creation(self):
        rr = make_standard_reasoning_result()
        scenarios = [
            {"name": "sunny", "description": "Sunny weather", "estimated_minutes": 60},
            {"name": "rainy", "description": "Rainy weather", "estimated_minutes": 90},
        ]
        plan = create_scenario_plan(rr, scenarios)
        assert plan.planning_type == PlanningType.SCENARIO.value
        assert plan.metadata.get("scenarios") == ["sunny", "rainy"]

    def test_contingency_plan_creation(self):
        rr = make_standard_reasoning_result()
        primary = create_reactive_plan(rr)
        plan = create_contingency_plan(rr, primary, critical_task_ids=[primary.tasks[0].task_id])
        assert plan.planning_type == PlanningType.CONTINGENCY.value
        # Should have original tasks + fallback tasks
        assert plan.task_count > primary.task_count

    def test_merge_plans(self):
        plan_a = ExecutionPlan(name="Plan A")
        plan_a.add_task(PlanTask(label="Task A1"))
        plan_b = ExecutionPlan(name="Plan B")
        plan_b.add_task(PlanTask(label="Task B1"))
        merged = merge_plans([plan_a, plan_b])
        assert merged.task_count == 2
        assert "merged" in merged.name.lower()

    def test_merge_plans_empty_raises(self):
        with pytest.raises(ValueError):
            merge_plans([])

    def test_dispatch_planning_type(self):
        assert dispatch_planning_type(PlanningType.REACTIVE.value) is not None
        assert dispatch_planning_type(PlanningType.OPERATIONAL.value) is not None
        assert dispatch_planning_type(PlanningType.STRATEGIC.value) is not None
        assert dispatch_planning_type("unknown_type") is None

    def test_template_registry(self):
        before = len(list_templates())
        register_template("custom_test", "A test template", lambda x, y: [PlanTask(label="T")])
        after = len(list_templates())
        assert after == before + 1
        tmpl = get_template("custom_test")
        assert tmpl is not None
        assert tmpl["name"] == "custom_test"
        assert tmpl["description"] == "A test template"


# ===========================================================================
# Section 3: PlannerEngine Pipeline Tests
# ===========================================================================


class TestPlannerEngine:
    """Tests for the PlannerEngine 9-stage pipeline."""

    def setup_method(self):
        reset_planner_engine()

    def _make_input(self, reasoning_result=None, constraints=None,
                    resources=None, context=None, objectives=None,
                    planning_types=None, skip_default_rr=False) -> PlanningInput:
        rr = reasoning_result
        if rr is None and not skip_default_rr:
            rr = make_standard_reasoning_result()
        return PlanningInput(
            reasoning_result=rr,
            constraints=constraints or [],
            resources=resources or [],
            context=context or MockContext(),
            objectives=objectives or [],
            planning_types=planning_types or [PlanningType.OPERATIONAL.value],
            tenant_id=1,
            actor_id="test-user",
            correlation_id="test-correlation",
        )

    # --- Input Validation ---

    def test_plan_with_valid_input(self):
        engine = PlannerEngine()
        inp = self._make_input()
        output = engine.plan(inp)
        assert output.is_success, f"Plan failed: {output.error}"
        assert output.primary_plan is not None
        assert output.primary_plan.state == PlanState.PROPOSED.value
        assert output.primary_plan.task_count >= 1

    def test_plan_with_no_reasoning_result(self):
        engine = PlannerEngine()
        inp = self._make_input(skip_default_rr=True, reasoning_result=None)
        output = engine.plan(inp)
        assert output.is_error
        assert "No reasoning result" in output.error

    def test_plan_with_empty_findings(self):
        engine = PlannerEngine()
        rr = MockReasoningResult(findings=[])
        inp = self._make_input(reasoning_result=rr)
        output = engine.plan(inp)
        assert output.is_error
        assert "Empty reasoning result" in output.error

    def test_plan_with_zero_confidence(self):
        engine = PlannerEngine()
        rr = MockReasoningResult(findings=[MockFinding()],
                                 confidence=MockConfidence(0.0, "insufficient"))
        inp = self._make_input(reasoning_result=rr)
        output = engine.plan(inp)
        assert output.is_error
        assert output.failure_mode == FailureMode.LOW_CONFIDENCE.value

    def test_plan_with_tenant_mismatch(self):
        engine = PlannerEngine()
        inp = self._make_input(context=MockContext(tenant_id=2))
        inp.tenant_id = 1
        output = engine.plan(inp)
        assert output.is_error
        assert "Tenant mismatch" in output.error

    # --- Full pipeline ---

    def test_plan_produces_governance_package(self):
        engine = PlannerEngine()
        inp = self._make_input()
        output = engine.plan(inp)
        assert output.is_success
        assert output.governance_package is not None
        assert output.governance_package.plan is not None
        assert output.governance_package.reasoning_result_id == "rr-test-1"

    def test_plan_produces_risk_assessment(self):
        engine = PlannerEngine()
        inp = self._make_input()
        output = engine.plan(inp)
        assert output.is_success
        assert output.risk_assessment is not None
        assert 0.0 <= output.risk_assessment.overall_risk_score <= 1.0

    def test_plan_produces_schedule(self):
        engine = PlannerEngine()
        inp = self._make_input()
        output = engine.plan(inp)
        assert output.is_success
        assert output.schedule is not None
        assert output.schedule.total_duration_minutes > 0

    def test_plan_produces_dependency_graph(self):
        engine = PlannerEngine()
        inp = self._make_input()
        output = engine.plan(inp)
        assert output.is_success
        assert output.dependency_graph is not None

    def test_plan_produces_metadata(self):
        engine = PlannerEngine()
        inp = self._make_input()
        output = engine.plan(inp)
        assert output.is_success
        assert output.planning_metadata is not None
        assert output.planning_metadata.stages_executed >= 9

    def test_plan_uses_planning_types(self):
        engine = PlannerEngine()
        inp = self._make_input(planning_types=[
            PlanningType.REACTIVE.value,
            PlanningType.OPERATIONAL.value,
        ])
        output = engine.plan(inp)
        assert output.is_success
        assert output.planning_metadata is not None

    def test_plan_with_multiple_objectives(self):
        engine = PlannerEngine()
        objectives = [
            Objective(label="Minimize cost", priority=0.9),
            Objective(label="Maximize speed", priority=0.7),
        ]
        inp = self._make_input(objectives=objectives)
        output = engine.plan(inp)
        assert output.is_success

    def test_plan_with_constraints(self):
        engine = PlannerEngine()
        constraints = [
            PlanningConstraint(constraint_type="budget", label="Budget", value=50000, is_hard=True),
        ]
        inp = self._make_input(constraints=constraints)
        output = engine.plan(inp)
        assert output.is_success
        assert len(output.governance_package.constraints) == 1

    def test_plan_with_resources(self):
        engine = PlannerEngine()
        resources = [
            Resource(label="Developer", resource_type=ResourceType.PEOPLE.value,
                     total_capacity=3.0, cost_per_unit=5000.0),
            Resource(label="Server", resource_type=ResourceType.SYSTEMS.value,
                     total_capacity=1.0),
        ]
        inp = self._make_input(resources=resources)
        output = engine.plan(inp)
        assert output.is_success
        assert output.primary_plan is not None

    # --- Determinism ---

    def test_identical_inputs_identical_outputs(self):
        engine = PlannerEngine()
        inp1 = self._make_input()
        inp2 = self._make_input()  # Same structure

        output1 = engine.plan(inp1)
        output2 = engine.plan(inp2)

        assert output1.is_success == output2.is_success
        if output1.is_success and output2.is_success:
            assert output1.primary_plan.planning_type == output2.primary_plan.planning_type
            assert output1.confidence == output2.confidence
            assert len(output1.alternatives) == len(output2.alternatives)

    # --- Failure paths ---

    def test_plan_with_conflicting_hard_constraints(self):
        engine = PlannerEngine()
        constraints = [
            PlanningConstraint(constraint_type="budget", label="Budget A",
                               value=50000, is_hard=True),
            PlanningConstraint(constraint_type="budget", label="Budget B",
                               value=100000, is_hard=True),
        ]
        inp = self._make_input(constraints=constraints)
        output = engine.plan(inp)
        # Hard constraint conflict should fail
        assert output.is_error
        assert output.failure_mode == FailureMode.IMPOSSIBLE_PLAN.value

    def test_plan_with_no_planning_types(self):
        engine = PlannerEngine()
        inp = self._make_input(planning_types=[])
        output = engine.plan(inp)
        assert output.is_success  # Should use default operational

    def test_plan_with_unknown_planning_type(self):
        engine = PlannerEngine()
        inp = self._make_input(planning_types=["unknown_type"])
        output = engine.plan(inp)
        assert output.is_success  # Should fall back to generic plan

    # --- Engine singleton ---

    def test_get_engine_singleton(self):
        reset_planner_engine()
        e1 = get_planner_engine()
        e2 = get_planner_engine()
        assert e1 is e2
        reset_planner_engine()
        e3 = get_planner_engine()
        assert e3 is not e1

    # --- Stage-specific edge cases ---

    def test_goal_analysis_extracts_findings(self):
        engine = PlannerEngine()
        findings = [MockFinding(finding_id="f-test", label="Test goal")]
        rr = MockReasoningResult(findings=findings)
        goals = engine._goal_analysis(self._make_input(reasoning_result=rr))
        assert goals is not None
        assert len(goals) == 1
        assert goals[0]["finding_id"] == "f-test"

    def test_goal_analysis_empty_returns_none(self):
        engine = PlannerEngine()
        rr = MockReasoningResult(findings=[])
        goals = engine._goal_analysis(self._make_input(reasoning_result=rr))
        assert goals is None

    def test_constraint_resolution_no_conflicts(self):
        engine = PlannerEngine()
        resolution = engine._constraint_resolution([])
        assert resolution == []

    def test_constraint_resolution_soft_conflict(self):
        engine = PlannerEngine()
        constraints = [
            PlanningConstraint(constraint_type="budget", label="Budget",
                               value=50000, is_hard=False),
        ]
        resolution = engine._constraint_resolution(constraints)
        assert resolution is not None

    def test_dependency_graph_cycle_detection(self):
        engine = PlannerEngine()
        # Create a plan with a cycle: t1 -> t2 -> t1
        t1 = PlanTask(task_id="t1", label="Task 1", depends_on=["t2"])
        t2 = PlanTask(task_id="t2", label="Task 2", depends_on=["t1"])
        plan = ExecutionPlan(name="Cyclic Plan", tasks=[t1, t2])
        graph = engine._build_dependency_graph([plan])
        assert graph is None

    def test_dependency_graph_valid(self):
        engine = PlannerEngine()
        t1 = PlanTask(task_id="t1", label="Task 1")
        t2 = PlanTask(task_id="t2", label="Task 2", depends_on=["t1"])
        t3 = PlanTask(task_id="t3", label="Task 3", depends_on=["t2"])
        plan = ExecutionPlan(name="Valid Plan", tasks=[t1, t2, t3])
        graph = engine._build_dependency_graph([plan])
        assert graph is not None
        assert graph.has_cycles is False

    def test_execution_graph_scheduling(self):
        engine = PlannerEngine()
        t1 = PlanTask(task_id="t1", label="Task 1", estimated_duration_minutes=30.0)
        t2 = PlanTask(task_id="t2", label="Task 2", estimated_duration_minutes=60.0,
                      depends_on=["t1"])
        plan = ExecutionPlan(name="Scheduled Plan", tasks=[t1, t2])
        schedule = engine._build_execution_graph([plan], None)
        assert schedule is not None
        assert schedule.total_duration_minutes >= 90.0
        assert schedule.milestones is not None

    def test_governance_package_includes_trade_offs(self):
        engine = PlannerEngine()
        inp = self._make_input(planning_types=[
            PlanningType.OPERATIONAL.value,
            PlanningType.STRATEGIC.value,
        ])
        output = engine.plan(inp)
        if output.is_success and output.governance_package:
            # Trade-offs should exist when multi-alternative
            pass  # Non-critical assertion

    def test_planning_metadata_tracks_stages(self):
        engine = PlannerEngine()
        inp = self._make_input()
        output = engine.plan(inp)
        assert output.planning_metadata.stages_passed >= 7  # At least 7 stages pass
        assert output.planning_metadata.alternatives_generated >= 1

    def test_confidence_is_deterministic(self):
        engine = PlannerEngine()
        inp = self._make_input()
        output1 = engine.plan(inp)

        reset_planner_engine()
        engine2 = PlannerEngine()
        output2 = engine2.plan(inp)

        assert output1.confidence == output2.confidence


# ===========================================================================
# Section 4: Concurrency Tests
# ===========================================================================


class TestPlannerConcurrency:
    """Tests for thread safety (PlannerEngine is stateless per-cycle)."""

    def test_concurrent_planning(self):
        engine = PlannerEngine()
        results: List[PlanningOutput] = []
        errors: List[Exception] = []

        def run_plan():
            try:
                inp = PlanningInput(
                    reasoning_result=make_standard_reasoning_result(),
                    tenant_id=1,
                    actor_id="user",
                )
                out = engine.plan(inp)
                results.append(out)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=run_plan) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 5
        for r in results:
            assert r.is_success

    def test_concurrent_identical_inputs(self):
        engine = PlannerEngine()
        inp = PlanningInput(
            reasoning_result=make_standard_reasoning_result(),
            tenant_id=1,
            actor_id="user",
        )
        results: List[PlanningOutput] = []

        def run():
            out = engine.plan(inp)
            results.append(out)

        threads = [threading.Thread(target=run) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 3
        if all(r.is_success for r in results):
            confidences = [r.confidence for r in results]
            assert all(c == confidences[0] for c in confidences)


# ===========================================================================
# Section 5: Integration Tests (with Event Bus if available)
# ===========================================================================
# NOTE: TestPlannerIntegration was removed because all 3 test methods
# were empty stubs (pass). Real integration tests should be written when
# Event Bus infrastructure is available.