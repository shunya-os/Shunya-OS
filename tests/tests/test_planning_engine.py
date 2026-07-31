"""
Tests for the SHUNYA Planning Engine.

Covers plan creation, dependency graph validation (acyclic check, cycle
detection), topological sort, resource conflict detection, risk classification,
the IntelligenceEngine interface, and edge cases.
"""

from __future__ import annotations

import pytest

from core.intelligence.planning import (
    EngineInput,
    EngineOutput,
    Plan,
    PlanningEngine,
    PlanStep,
    PlanStepStatus,
    Resource,
    Risk,
    RiskCategory,
    RiskSeverity,
    get_planning_engine,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def engine() -> PlanningEngine:
    return PlanningEngine()


@pytest.fixture
def linear_plan(engine: PlanningEngine) -> Plan:
    """A plan with simple linear dependencies: A -> B -> C."""
    steps = [
        PlanStep(step_id="step-a", order=1, action="Step A", actor="alice"),
        PlanStep(
            step_id="step-b",
            order=2,
            action="Step B",
            actor="bob",
            depends_on=("step-a",),
        ),
        PlanStep(
            step_id="step-c",
            order=3,
            action="Step C",
            actor="carol",
            depends_on=("step-b",),
        ),
    ]
    return engine.create_plan("Linear test plan", steps)


@pytest.fixture
def diamond_plan(engine: PlanningEngine) -> Plan:
    """A plan with diamond dependencies: A -> (B, C) -> D."""
    steps = [
        PlanStep(step_id="start", order=1, action="Start", actor="alice"),
        PlanStep(
            step_id="branch-b",
            order=2,
            action="Branch B",
            actor="bob",
            depends_on=("start",),
        ),
        PlanStep(
            step_id="branch-c",
            order=2,
            action="Branch C",
            actor="carol",
            depends_on=("start",),
        ),
        PlanStep(
            step_id="merge-d",
            order=3,
            action="Merge D",
            actor="dave",
            depends_on=("branch-b", "branch-c"),
        ),
    ]
    return engine.create_plan("Diamond test plan", steps)


@pytest.fixture
def plan_with_resources(engine: PlanningEngine) -> Plan:
    """A plan where two parallel steps compete for the same resource."""
    db = Resource(name="database", resource_type="tool", quantity=1)
    steps = [
        PlanStep(
            step_id="s1",
            order=1,
            action="Query data",
            actor="alice",
            resources=(db,),
        ),
        PlanStep(
            step_id="s2",
            order=2,
            action="Write data",
            actor="bob",
            resources=(db,),
        ),
    ]
    return engine.create_plan("Resource test", steps)


# ══════════════════════════════════════════════════════════════════════════════
# Plan Creation Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestPlanCreation:
    def test_create_minimal_plan(self, engine: PlanningEngine) -> None:
        """A plan with a single step can be created."""
        step = PlanStep(step_id="s1", order=1, action="Do something", actor="me")
        plan = engine.create_plan("Test", [step])
        assert plan.objective == "Test"
        assert len(plan.steps) == 1
        assert plan.plan_id is not None

    def test_create_plan_empty_objective_rejected(
        self, engine: PlanningEngine
    ) -> None:
        with pytest.raises(ValueError, match="non-empty objective"):
            engine.create_plan("", [])

    def test_create_plan_no_steps_rejected(
        self, engine: PlanningEngine
    ) -> None:
        with pytest.raises(ValueError, match="at least one step"):
            engine.create_plan("Test", [])

    def test_plan_auto_assigns_orders(
        self, engine: PlanningEngine
    ) -> None:
        """Steps without explicit orders get auto-assigned."""
        steps = [
            PlanStep(step_id="a", order=1, action="First", actor="x"),
            PlanStep(step_id="b", order=0, action="Second", actor="y"),
            PlanStep(step_id="c", order=0, action="Third", actor="z"),
        ]
        plan = engine.create_plan("Auto-order", steps)
        orders = {s.step_id: s.order for s in plan.steps}
        assert orders["a"] == 1
        assert orders["b"] == 2
        assert orders["c"] == 3

    def test_plan_auto_derives_dependencies(
        self, engine: PlanningEngine
    ) -> None:
        """Dependency map is auto-derived from steps' depends_on."""
        steps = [
            PlanStep(step_id="a", order=1, action="A", actor="x"),
            PlanStep(
                step_id="b", order=2, action="B", actor="y", depends_on=("a",)
            ),
        ]
        plan = engine.create_plan("Deps", steps)
        assert plan.dependencies["b"] == ["a"]

    def test_plan_stores_and_retrieves(
        self, engine: PlanningEngine
    ) -> None:
        """Plans are retrievable by ID after creation."""
        step = PlanStep(step_id="s1", order=1, action="Go", actor="me")
        plan = engine.create_plan("Retrieve test", [step])
        fetched = engine.get_plan(plan.plan_id)
        assert fetched is not None
        assert fetched.objective == "Retrieve test"
        assert fetched.plan_id == plan.plan_id

    def test_plan_nonexistent_id(self, engine: PlanningEngine) -> None:
        """Fetching a nonexistent plan returns None."""
        assert engine.get_plan("nonexistent") is None


# ══════════════════════════════════════════════════════════════════════════════
# Dependency Graph Validation Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestDependencyValidation:
    def test_acyclic_linear_plan(
        self, engine: PlanningEngine, linear_plan: Plan
    ) -> None:
        """Linear chain is correctly identified as acyclic."""
        result = engine.validate_dependencies(linear_plan)
        assert result["acyclic"] is True
        assert len(result["sorted_step_ids"]) == 3

    def test_acyclic_diamond_plan(
        self, engine: PlanningEngine, diamond_plan: Plan
    ) -> None:
        """Diamond-shaped graph is correctly identified as acyclic."""
        result = engine.validate_dependencies(diamond_plan)
        assert result["acyclic"] is True
        assert len(result["sorted_step_ids"]) == 4
        # 'start' must be first
        assert result["sorted_step_ids"][0] == "start"
        # 'merge-d' must be last
        assert result["sorted_step_ids"][-1] == "merge-d"

    def test_cycle_detected(self, engine: PlanningEngine) -> None:
        """A cycle in dependencies is detected."""
        steps = [
            PlanStep(
                step_id="a",
                order=1,
                action="A",
                actor="x",
                depends_on=("c",),
            ),
            PlanStep(
                step_id="b",
                order=2,
                action="B",
                actor="y",
                depends_on=("a",),
            ),
            PlanStep(
                step_id="c",
                order=3,
                action="C",
                actor="z",
                depends_on=("b",),
            ),
        ]
        plan = engine.create_plan("Cyclic plan", steps)
        result = engine.validate_dependencies(plan)
        assert result["acyclic"] is False
        assert len(result["cycle_path"]) > 0

    def test_self_dependency_detected(self, engine: PlanningEngine) -> None:
        """A step depending on itself is flagged."""
        steps = [
            PlanStep(
                step_id="a",
                order=1,
                action="A",
                actor="x",
                depends_on=("a",),  # self-dependency
            ),
        ]
        plan = engine.create_plan("Self-dep plan", steps)
        result = engine.validate_dependencies(plan)
        assert "a" in result["self_dependencies"]

    def test_no_orphan_steps_in_connected_graph(
        self, engine: PlanningEngine, linear_plan: Plan
    ) -> None:
        """A fully connected graph has no orphans."""
        result = engine.validate_dependencies(linear_plan)
        assert len(result["orphan_steps"]) <= 1  # leaf has no dependents

    def test_complex_dag_is_acyclic(
        self, engine: PlanningEngine
    ) -> None:
        """A complex DAG with multiple branches is acyclic."""
        steps = [
            PlanStep(step_id="a", order=1, action="A", actor="x"),
            PlanStep(
                step_id="b", order=2, action="B", actor="y", depends_on=("a",)
            ),
            PlanStep(
                step_id="c", order=2, action="C", actor="z", depends_on=("a",)
            ),
            PlanStep(
                step_id="d", order=3, action="D", actor="w", depends_on=("b",)
            ),
            PlanStep(
                step_id="e",
                order=3,
                action="E",
                actor="v",
                depends_on=("b", "c"),
            ),
            PlanStep(
                step_id="f",
                order=4,
                action="F",
                actor="u",
                depends_on=("d", "e"),
            ),
        ]
        plan = engine.create_plan("Complex DAG", steps)
        result = engine.validate_dependencies(plan)
        assert result["acyclic"] is True
        assert len(result["sorted_step_ids"]) == 6


# ══════════════════════════════════════════════════════════════════════════════
# Topological Sort Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestTopologicalSort:
    def test_topological_sort_linear(
        self, engine: PlanningEngine, linear_plan: Plan
    ) -> None:
        sorted_ids = engine.topological_sort(linear_plan)
        assert sorted_ids == ["step-a", "step-b", "step-c"]

    def test_topological_sort_diamond(
        self, engine: PlanningEngine, diamond_plan: Plan
    ) -> None:
        sorted_ids = engine.topological_sort(diamond_plan)
        assert sorted_ids[0] == "start"
        assert sorted_ids[-1] == "merge-d"
        # branch-b and branch-c can appear in any order
        assert sorted_ids.index("branch-b") < sorted_ids.index("merge-d")
        assert sorted_ids.index("branch-c") < sorted_ids.index("merge-d")

    def test_topological_sort_cyclic_returns_empty(
        self, engine: PlanningEngine
    ) -> None:
        steps = [
            PlanStep(
                step_id="a",
                order=1,
                action="A",
                actor="x",
                depends_on=("b",),
            ),
            PlanStep(
                step_id="b",
                order=2,
                action="B",
                actor="y",
                depends_on=("a",),
            ),
        ]
        plan = engine.create_plan("Cycle", steps)
        sorted_ids = engine.topological_sort(plan)
        assert sorted_ids == []


# ══════════════════════════════════════════════════════════════════════════════
# Resource Conflict Detection Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestResourceConflictDetection:
    def test_parallel_conflict_detected(
        self, engine: PlanningEngine
    ) -> None:
        """Parallel steps sharing a resource create a conflict."""
        db = Resource(name="database", resource_type="tool", quantity=1)
        steps = [
            PlanStep(
                step_id="s1",
                order=1,
                action="Query",
                actor="a",
                resources=(db,),
            ),
            PlanStep(
                step_id="s2",
                order=2,
                action="Write",
                actor="b",
                resources=(db,),
            ),
        ]
        plan = engine.create_plan("Conflict test", steps)
        conflicts = engine.detect_resource_conflicts(plan)
        assert len(conflicts) >= 1
        assert conflicts[0]["resource"] == "database"

    def test_sequential_same_resource_no_conflict(
        self, engine: PlanningEngine
    ) -> None:
        """Sequential steps using the same resource have no conflict."""
        db = Resource(name="database", resource_type="tool", quantity=1)
        steps = [
            PlanStep(
                step_id="s1",
                order=1,
                action="Query",
                actor="a",
                resources=(db,),
            ),
            PlanStep(
                step_id="s2",
                order=2,
                action="Write",
                actor="b",
                depends_on=("s1",),
                resources=(db,),
            ),
        ]
        plan = engine.create_plan("Sequential resource", steps)
        conflicts = engine.detect_resource_conflicts(plan)
        # S2 depends on S1, so no conflict
        assert conflicts == [] or all(
            c["steps"] != ["s1", "s2"] for c in conflicts
        )

    def test_no_resources_no_conflict(
        self, engine: PlanningEngine, linear_plan: Plan
    ) -> None:
        """A plan with no resources has no conflicts."""
        conflicts = engine.detect_resource_conflicts(linear_plan)
        assert conflicts == []

    def test_multiple_resources_partial_conflict(
        self, engine: PlanningEngine
    ) -> None:
        """Multiple resources might create multiple conflicts."""
        db = Resource(name="db", resource_type="tool", quantity=1)
        cache = Resource(name="cache", resource_type="tool", quantity=1)
        steps = [
            PlanStep(
                step_id="s1",
                order=1,
                action="Read",
                actor="a",
                resources=(db, cache),
            ),
            PlanStep(
                step_id="s2",
                order=2,
                action="Write",
                actor="b",
                resources=(db,),
            ),
        ]
        plan = engine.create_plan("Multi-resource", steps)
        conflicts = engine.detect_resource_conflicts(plan)
        assert len(conflicts) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Risk Classification Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestRiskClassification:
    def test_classify_risks(self, engine: PlanningEngine) -> None:
        """Risks are correctly classified by category and severity."""
        tech_risk = Risk(
            description="Server may go down",
            severity=RiskSeverity.HIGH,
            category=RiskCategory.TECHNICAL,
            probability=0.3,
            impact=0.9,
            mitigation="Use auto-scaling",
            contingency="Failover to backup",
            owner="infra-team",
        )
        schedule_risk = Risk(
            description="Deadline may slip",
            severity=RiskSeverity.MEDIUM,
            category=RiskCategory.SCHEDULE,
            probability=0.5,
            impact=0.5,
            mitigation="Add buffer time",
        )
        step = PlanStep(
            step_id="s1",
            order=1,
            action="Build",
            actor="team",
            risks=(tech_risk, schedule_risk),
        )
        plan = engine.create_plan("Risky plan", [step])
        classifications = engine.classify_risks(plan)
        assert len(classifications) == 2

        categories = {c["category"] for c in classifications}
        assert "technical" in categories
        assert "schedule" in categories

        severities = {c["severity"] for c in classifications}
        assert "high" in severities
        assert "medium" in severities

    def test_risk_score_computation(self) -> None:
        """Risk.risk_score correctly computes probability * impact."""
        risk = Risk(
            description="Test",
            severity=RiskSeverity.MEDIUM,
            category=RiskCategory.TECHNICAL,
            probability=0.5,
            impact=0.8,
        )
        assert risk.risk_score == 0.4

    def test_no_risks_no_classifications(
        self, engine: PlanningEngine, linear_plan: Plan
    ) -> None:
        """A plan with no risks has empty classifications."""
        classifications = engine.classify_risks(linear_plan)
        assert classifications == []


# ══════════════════════════════════════════════════════════════════════════════
# Engine Interface Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEngineInterface:
    def test_process_with_explicit_steps(
        self, engine: PlanningEngine
    ) -> None:
        """process() with explicit steps works."""
        step = PlanStep(step_id="s1", order=1, action="Do it", actor="me")
        inp = EngineInput(
            input_type="objective",
            payload={
                "objective": "Test process",
                "plan_steps": [step],
            },
            trace_id="trace-proc-01",
        )
        output = engine.process(inp)
        assert output.output_type == "plan.generated"
        assert output.deterministic is True
        assert output.escalation_used is False
        assert output.confidence > 0.0

    def test_process_with_step_dicts(
        self, engine: PlanningEngine
    ) -> None:
        """process() with dict steps works."""
        inp = EngineInput(
            input_type="objective",
            payload={
                "objective": "Dict steps test",
                "steps": [
                    {
                        "action": "Analyse",
                        "actor": "alice",
                        "depends_on": [],
                    },
                    {
                        "action": "Build",
                        "actor": "bob",
                        "depends_on": [0],
                    },
                ],
            },
            trace_id="trace-proc-02",
        )
        output = engine.process(inp)
        assert len(output.payload["steps"]) == 2
        assert output.deterministic is True

    def test_process_ai_escalation(self, engine: PlanningEngine) -> None:
        """process() escalates when no steps are provided."""
        inp = EngineInput(
            input_type="objective",
            payload={"objective": "Generate a plan from scratch"},
            trace_id="trace-proc-03",
        )
        output = engine.process(inp)
        # Should have used AI escalation since no steps provided
        assert output.escalation_used is True
        assert output.deterministic is False
        assert len(output.payload["steps"]) >= 1

    def test_process_raises_on_empty_objective(
        self, engine: PlanningEngine
    ) -> None:
        """process() raises ValueError for empty objective."""
        with pytest.raises(ValueError, match="non-empty objective"):
            engine.process(
                EngineInput(
                    input_type="objective",
                    payload={"objective": ""},
                )
            )

    def test_get_capabilities(self, engine: PlanningEngine) -> None:
        """Engine exposes all planning capabilities."""
        caps = engine.get_capabilities()
        assert len(caps) == 5
        assert "planning.generate" in caps
        assert "planning.validate_dependencies" in caps
        assert "planning.topological_sort" in caps
        assert "planning.resource_conflict_detection" in caps
        assert "planning.risk_classification" in caps

    def test_health_check(self, engine: PlanningEngine) -> None:
        """Health check returns engine identity and status."""
        health = engine.health_check()
        assert health["engine_id"] == "planning_engine"
        assert health["engine_type"] == "planning"
        assert health["status"] == "healthy"
        assert health["plans_count"] == 0

    def test_health_check_with_plans(
        self, engine: PlanningEngine, linear_plan: Plan
    ) -> None:
        """Health check reflects created plans."""
        health = engine.health_check()
        assert health["plans_count"] >= 1

    def test_escalate_method(self, engine: PlanningEngine) -> None:
        """escalate() returns structured result with AI-generated steps."""
        result = engine.escalate(
            EngineInput(
                input_type="objective",
                payload={"objective": "Test escalation"},
            )
        )
        assert result.confidence > 0.0
        assert len(result.result.get("steps", [])) >= 1

    def test_validation_in_process_output(
        self, engine: PlanningEngine
    ) -> None:
        """process() output includes validation results."""
        step = PlanStep(step_id="s1", order=1, action="Go", actor="me")
        inp = EngineInput(
            input_type="objective",
            payload={"objective": "Validation check", "plan_steps": [step]},
        )
        output = engine.process(inp)
        assert "acyclic" in output.payload
        assert output.payload["acyclic"] is True
        assert "sorted_step_ids" in output.payload
        assert "resource_conflicts" in output.payload


# ══════════════════════════════════════════════════════════════════════════════
# Model Validation Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestModelValidation:
    def test_plan_step_empty_action_rejected(self) -> None:
        with pytest.raises(ValueError, match="must have an action"):
            PlanStep(step_id="s1", order=1, action="", actor="x")

    def test_plan_step_negative_order_rejected(self) -> None:
        with pytest.raises(ValueError, match="order must be non-negative"):
            PlanStep(step_id="s1", order=-1, action="A", actor="x")

    def test_resource_zero_quantity_rejected(self) -> None:
        with pytest.raises(ValueError, match="quantity must be positive"):
            Resource(name="r", resource_type="t", quantity=0)

    def test_risk_out_of_range_probability(self) -> None:
        with pytest.raises(ValueError, match="probability must be in"):
            Risk(
                description="bad",
                severity=RiskSeverity.MEDIUM,
                category=RiskCategory.TECHNICAL,
                probability=1.5,
            )

    def test_risk_out_of_range_impact(self) -> None:
        with pytest.raises(ValueError, match="impact must be in"):
            Risk(
                description="bad",
                severity=RiskSeverity.MEDIUM,
                category=RiskCategory.TECHNICAL,
                impact=-0.1,
            )

    def test_plan_missing_step_in_dependency(self) -> None:
        """Plan creation fails if a dependency references a missing step."""
        with pytest.raises(ValueError, match="does not exist in plan steps"):
            Plan(
                objective="Bad deps",
                steps=(
                    PlanStep(step_id="a", order=1, action="A", actor="x"),
                ),
                dependencies={"a": ["nonexistent"]},
            )

    def test_risk_severity_default(self) -> None:
        """Risk defaults to MEDIUM severity and OPERATIONAL category."""
        risk = Risk(description="Test risk")
        assert risk.severity == RiskSeverity.MEDIUM
        assert risk.category == RiskCategory.OPERATIONAL
        assert risk.probability == 0.5
        assert risk.impact == 0.5


# ══════════════════════════════════════════════════════════════════════════════
# Singleton Accessor
# ══════════════════════════════════════════════════════════════════════════════


class TestSingleton:
    def test_get_planning_engine(self) -> None:
        """Singleton accessor returns same instance."""
        e1 = get_planning_engine()
        e2 = get_planning_engine()
        assert e1 is e2

    def test_import_from_init(self) -> None:
        """Engine is importable from core.intelligence.planning."""
        from core.intelligence.planning import (
            PlanningEngine as ImportedEngine,
        )

        assert ImportedEngine is PlanningEngine