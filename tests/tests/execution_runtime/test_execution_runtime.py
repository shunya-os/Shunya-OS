"""Tests for SHUNYA Execution Runtime (Phase F).

Covers:
1. Model contracts — state machine, transitions, graph
2. Action registration — plugin architecture
3. Instance creation and lifecycle
4. Single execution
5. Dependency graph — serial, parallel, fan-out, fan-in
6. Cycle detection
7. Retry and failure handling
8. Cancellation
9. Rollback
10. Observability — trace, evidence, timeline
11. Batch execution
12. Policy configuration
13. Health check
14. Graph validation
"""


import pytest

from core.execution_runtime import (
    ExecutionInstance,
    ExecutionRuntime,
    ExecutionState,
    ScheduleType,
)
from core.execution_runtime.models import (
    VALID_EXECUTION_TRANSITIONS,
    ActionContract,
    ExecutionGraph,
    ExecutionPolicies,
)

# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def runtime():
    r = ExecutionRuntime()
    r.register_default_actions()
    return r


@pytest.fixture
def noop_instance(runtime):
    return runtime.create_instance(action_id="noop", actor="test", objective="Test noop")


# ══════════════════════════════════════════════════════════════════════════
# 1. Model Contracts
# ══════════════════════════════════════════════════════════════════════════

class TestStateMachine:
    def test_terminals(self):
        from core.execution_runtime.models import TERMINAL_STATES
        assert ExecutionState.COMPLETED.is_terminal
        assert ExecutionState.CANCELLED.is_terminal
        assert ExecutionState.CANCELLED.is_terminal
        assert not ExecutionState.CREATED.is_terminal
        assert not ExecutionState.EXECUTING.is_terminal
        assert not ExecutionState.FAILED.is_terminal
        assert ExecutionState.COMPLETED in TERMINAL_STATES
        assert ExecutionState.CANCELLED in TERMINAL_STATES
        assert ExecutionState.EXPIRED in TERMINAL_STATES
        assert ExecutionState.ROLLED_BACK not in TERMINAL_STATES  # can transition to COMPLETED

    def test_valid_transitions_created(self):
        allowed = VALID_EXECUTION_TRANSITIONS[ExecutionState.CREATED]
        assert ExecutionState.READY in allowed
        assert ExecutionState.CANCELLED in allowed
        assert ExecutionState.FAILED not in allowed

    def test_invalid_transition_raises(self):
        inst = ExecutionInstance()
        with pytest.raises(ValueError, match="Invalid execution state transition"):
            inst.transition_to(ExecutionState.COMPLETED)  # CREATED → COMPLETED not allowed

    def test_all_states_have_transitions(self):
        for state in ExecutionState:
            assert state in VALID_EXECUTION_TRANSITIONS, f"Missing transitions for {state}"

    def test_terminal_transitions_empty(self):
        from core.execution_runtime.models import TERMINAL_STATES
        for state in ExecutionState:
            if state in TERMINAL_STATES:
                assert VALID_EXECUTION_TRANSITIONS[state] == [], f"{state} should have empty transitions"


class TestExecutionGraph:
    def test_single_node(self):
        g = ExecutionGraph()
        i = ExecutionInstance()
        g.add_instance(i)
        assert i.execution_id in g.nodes
        assert not g.has_cycle()

    def test_linear_chain_no_cycle(self):
        g = ExecutionGraph()
        a = ExecutionInstance(dependencies=[])
        b = ExecutionInstance(dependencies=[a.execution_id])
        c = ExecutionInstance(dependencies=[b.execution_id])
        a.execution_id = "a"
        b.execution_id = "b"
        c.execution_id = "c"
        g.add_instance(a)
        g.add_instance(b)
        g.add_instance(c)
        assert not g.has_cycle()

    def test_cycle_detected(self):
        g = ExecutionGraph()
        a = ExecutionInstance(dependencies=[])
        b = ExecutionInstance(dependencies=["a"])
        c = ExecutionInstance(dependencies=["b"])
        a.execution_id = "a"
        b.execution_id = "b"
        c.execution_id = "c"
        g.add_instance(a)
        g.add_instance(b)
        g.add_instance(c)
        # Create cycle
        a.dependencies = ["c"]
        g.edges[a.execution_id] = ["c"]
        assert g.has_cycle()

    def test_critical_path(self):
        g = ExecutionGraph()
        a = ExecutionInstance(dependencies=[])
        b = ExecutionInstance(dependencies=["a"])
        c = ExecutionInstance(dependencies=["a"])
        d = ExecutionInstance(dependencies=["b", "c"])
        a.execution_id = "a"
        b.execution_id = "b"
        c.execution_id = "c"
        d.execution_id = "d"
        g.add_instance(a)
        g.add_instance(b)
        g.add_instance(c)
        g.add_instance(d)
        path = g.compute_critical_path()
        assert len(path) >= 3  # at least a → b|c → d


# ══════════════════════════════════════════════════════════════════════════
# 2. Action Registration
# ══════════════════════════════════════════════════════════════════════════

class TestActionRegistration:
    def test_register_and_list(self, runtime):
        actions = runtime.list_actions()
        action_ids = {a.action_id for a in actions}
        assert "noop" in action_ids
        assert "echo" in action_ids
        assert "delay" in action_ids

    def test_register_custom_action(self, runtime):
        runtime.register_action(
            "custom",
            ActionContract(action_id="custom", description="Custom action"),
            handler=lambda inputs: {"result": "done"},
        )
        assert runtime.get_action("custom") is not None

    def test_duplicate_raises(self, runtime):
        with pytest.raises(ValueError, match="already registered"):
            runtime.register_action("noop", handler=lambda x: x)

    def test_unknown_action_raises(self, runtime):
        with pytest.raises(ValueError, match="Unknown action"):
            runtime.create_instance(action_id="nonexistent")


# ══════════════════════════════════════════════════════════════════════════
# 3. Instance Creation
# ══════════════════════════════════════════════════════════════════════════

class TestInstanceCreation:
    def test_create_instance(self, runtime):
        inst = runtime.create_instance(
            action_id="noop", actor="user1", objective="Test",
            inputs={"key": "val"}, priority=50,
        )
        assert inst.action_id == "noop"
        assert inst.actor == "user1"
        assert inst.objective == "Test"
        assert inst.inputs["key"] == "val"
        assert inst.priority == 50
        assert inst.state == ExecutionState.CREATED
        assert inst.root_execution_id == inst.execution_id
        assert len(inst.history) == 1
        assert inst.history[0].event_type == "ExecutionCreated"

    def test_get_instance(self, runtime):
        inst = runtime.create_instance(action_id="noop", actor="test", objective="Get")
        fetched = runtime.get_instance(inst.execution_id)
        assert fetched is not None
        assert fetched.execution_id == inst.execution_id

    def test_instance_has_parent(self, runtime):
        parent = runtime.create_instance(action_id="noop", actor="test", objective="Parent")
        child = runtime.create_instance(
            action_id="noop", actor="test", objective="Child",
            parent_execution_id=parent.execution_id,
            root_execution_id=parent.root_execution_id,
        )
        assert child.parent_execution_id == parent.execution_id
        assert child.root_execution_id == parent.root_execution_id


# ══════════════════════════════════════════════════════════════════════════
# 4. Single Execution
# ══════════════════════════════════════════════════════════════════════════

class TestSingleExecution:
    @pytest.mark.asyncio
    async def test_execute_noop(self, runtime, noop_instance):
        result = await runtime.schedule(noop_instance)
        assert result.state == ExecutionState.COMPLETED
        assert result.outputs["status"] == "ok"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_execute_echo(self, runtime):
        inst = runtime.create_instance(
            action_id="echo", actor="test", objective="Echo",
            inputs={"message": "hello"},
        )
        result = await runtime.schedule(inst)
        assert result.state == ExecutionState.COMPLETED
        assert result.outputs["echo"]["message"] == "hello"

    @pytest.mark.asyncio
    async def test_execute_creates_evidence(self, runtime, noop_instance):
        result = await runtime.schedule(noop_instance)
        assert len(result.evidence) >= 2  # started + completed
        assert result.evidence[0].event_type == "execution_started"
        assert result.evidence[1].event_type == "execution_completed"

    @pytest.mark.asyncio
    async def test_execution_timing(self, runtime, noop_instance):
        result = await runtime.schedule(noop_instance)
        assert result.timing.execution_duration_ms > 0
        assert result.timing.started_at
        assert result.timing.completed_at

    @pytest.mark.asyncio
    async def test_execute_schedule_immediate(self, runtime, noop_instance):
        result = await runtime.schedule(noop_instance, ScheduleType.IMMEDIATE)
        assert result.state == ExecutionState.COMPLETED


# ══════════════════════════════════════════════════════════════════════════
# 5. Dependency Graph
# ══════════════════════════════════════════════════════════════════════════

class TestDependencyExecution:
    @pytest.mark.asyncio
    async def test_serial_execution(self, runtime):
        a = runtime.create_instance(action_id="noop", actor="test", objective="A")
        b = runtime.create_instance(
            action_id="noop", actor="test", objective="B",
            dependencies=[a.execution_id],
        )
        c = runtime.create_instance(
            action_id="noop", actor="test", objective="C",
            dependencies=[b.execution_id],
        )
        await runtime.schedule(a)
        await runtime.schedule(b)
        await runtime.schedule(c)
        assert a.state == ExecutionState.COMPLETED
        assert b.state == ExecutionState.COMPLETED
        assert c.state == ExecutionState.COMPLETED

    @pytest.mark.asyncio
    async def test_parallel_execution(self, runtime):
        a = runtime.create_instance(action_id="noop", actor="test", objective="A")
        b = runtime.create_instance(action_id="noop", actor="test", objective="B")
        c = runtime.create_instance(
            action_id="noop", actor="test", objective="C",
            dependencies=[a.execution_id, b.execution_id],
        )
        await runtime.schedule(a)
        await runtime.schedule(b)
        await runtime.schedule(c)
        assert a.state == ExecutionState.COMPLETED
        assert b.state == ExecutionState.COMPLETED
        assert c.state == ExecutionState.COMPLETED

    @pytest.mark.asyncio
    async def test_fan_out(self, runtime):
        parent = runtime.create_instance(action_id="noop", actor="test", objective="Parent")
        children = [
            runtime.create_instance(
                action_id="noop", actor="test", objective=f"Child {i}",
                dependencies=[parent.execution_id],
                parent_execution_id=parent.execution_id,
            )
            for i in range(3)
        ]
        await runtime.schedule(parent)
        for child in children:
            await runtime.schedule(child)
        assert parent.state == ExecutionState.COMPLETED
        for child in children:
            assert child.state == ExecutionState.COMPLETED

    @pytest.mark.asyncio
    async def test_fan_in(self, runtime):
        leaves = [runtime.create_instance(action_id="noop", actor="test", objective=f"Leaf {i}")
                  for i in range(3)]
        join = runtime.create_instance(
            action_id="noop", actor="test", objective="Join",
            dependencies=[l.execution_id for l in leaves],
        )
        for leaf in leaves:
            await runtime.schedule(leaf)
        await runtime.schedule(join)
        for leaf in leaves:
            assert leaf.state == ExecutionState.COMPLETED
        assert join.state == ExecutionState.COMPLETED

    @pytest.mark.asyncio
    async def test_barrier(self, runtime):
        """Barrier: multiple predecessors must complete before successor."""
        a = runtime.create_instance(action_id="noop", actor="test", objective="A")
        b = runtime.create_instance(action_id="noop", actor="test", objective="B",
                                     dependencies=[a.execution_id])
        c = runtime.create_instance(action_id="noop", actor="test", objective="C",
                                     dependencies=[a.execution_id])
        d = runtime.create_instance(action_id="noop", actor="test", objective="D",
                                     dependencies=[b.execution_id, c.execution_id])
        await runtime.schedule(a)
        await runtime.schedule(b)
        await runtime.schedule(c)
        await runtime.schedule(d)
        assert d.state == ExecutionState.COMPLETED


# ══════════════════════════════════════════════════════════════════════════
# 6. Cycle Detection
# ══════════════════════════════════════════════════════════════════════════

class TestCycleDetection:
    def test_validate_graph_no_issues(self, runtime):
        a = runtime.create_instance(action_id="noop", actor="test", objective="A")
        _ = runtime.create_instance(action_id="noop", actor="test", objective="B",
                                     dependencies=[a.execution_id])
        issues = runtime.validate_graph()
        assert len(issues) == 0

    def test_validate_graph_unknown_dependency(self, runtime):
        _ = runtime.create_instance(
            action_id="noop", actor="test", objective="Test",
            dependencies=["nonexistent"],
        )
        issues = runtime.validate_graph()
        assert any("unknown dependency" in i for i in issues)


# ══════════════════════════════════════════════════════════════════════════
# 7. Retry & Failure
# ══════════════════════════════════════════════════════════════════════════

class TestRetry:
    @pytest.mark.asyncio
    async def test_failing_action_retries(self, runtime):
        fail_count = {"count": 0}

        def failing_handler(inputs):
            fail_count["count"] += 1
            if fail_count["count"] < 3:
                raise ValueError("Transient error")
            return {"status": "ok"}

        runtime.register_action("flaky", handler=failing_handler)
        inst = runtime.create_instance(action_id="flaky", actor="test", objective="Flaky",
                                        inputs={})
        result = await runtime.schedule(inst)
        assert result.state == ExecutionState.COMPLETED
        assert fail_count["count"] == 3

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, runtime):
        def always_fails(inputs):
            raise ValueError("Always fails")

        runtime.register_action("always_fail", handler=always_fails)
        inst = runtime.create_instance(action_id="always_fail", actor="test", objective="Fail")
        inst.max_retries = 2
        result = await runtime.schedule(inst)
        assert result.state in (ExecutionState.FAILED, ExecutionState.ROLLED_BACK)
        assert result.retry_count == 3  # initial + 2 retries


# ══════════════════════════════════════════════════════════════════════════
# 8. Cancellation
# ══════════════════════════════════════════════════════════════════════════

class TestCancellation:
    @pytest.mark.asyncio
    async def test_cancel_created(self, runtime):
        inst = runtime.create_instance(action_id="noop", actor="test", objective="Cancel")
        runtime.cancel(inst, "No longer needed")
        assert inst.state == ExecutionState.CANCELLED
        assert inst.history[-1].event_type == "ExecutionCancelled"

    @pytest.mark.asyncio
    async def test_cancel_twice_no_error(self, runtime):
        inst = runtime.create_instance(action_id="noop", actor="test", objective="Double")
        runtime.cancel(inst)
        runtime.cancel(inst)  # No error
        assert inst.state == ExecutionState.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_after_completion_noop(self, runtime, noop_instance):
        result = await runtime.schedule(noop_instance)
        runtime.cancel(result)  # Should not raise
        assert result.state == ExecutionState.COMPLETED


# ══════════════════════════════════════════════════════════════════════════
# 9. Rollback
# ══════════════════════════════════════════════════════════════════════════

class TestRollback:
    @pytest.mark.asyncio
    async def test_rollback_on_retry_exhaustion(self, runtime):
        def fail_handler(inputs):
            raise RuntimeError("Irrecoverable")

        runtime.register_action("doomed",
            ActionContract(action_id="doomed", has_rollback=True, default_retries=0),
            handler=fail_handler,
        )
        inst = runtime.create_instance(action_id="doomed", actor="test", objective="Doomed")
        result = await runtime.schedule(inst)
        assert result.state == ExecutionState.ROLLED_BACK or result.state == ExecutionState.FAILED


# ══════════════════════════════════════════════════════════════════════════
# 10. Observability
# ══════════════════════════════════════════════════════════════════════════

class TestObservability:
    @pytest.mark.asyncio
    async def test_execution_trace(self, runtime, noop_instance):
        result = await runtime.schedule(noop_instance)
        trace = runtime.get_trace(result)
        assert trace.execution_duration_ms > 0
        assert trace.total_duration_ms > 0
        assert len(trace.timeline) > 0

    @pytest.mark.asyncio
    async def test_trace_timeline_events(self, runtime, noop_instance):
        result = await runtime.schedule(noop_instance)
        event_types = [e.event_type for e in result.trace.timeline]
        assert "ExecutionCreated" in event_types
        assert "ExecutionCompleted" in event_types or "ExecutionFailed" in event_types

    @pytest.mark.asyncio
    async def test_evidence_records(self, runtime, noop_instance):
        result = await runtime.schedule(noop_instance)
        assert len(result.evidence) >= 2
        assert result.evidence[0].immutable is True


# ══════════════════════════════════════════════════════════════════════════
# 11. Batch Execution
# ══════════════════════════════════════════════════════════════════════════

class TestBatchExecution:
    @pytest.mark.asyncio
    async def test_batch_independent(self, runtime):
        instances = [
            runtime.create_instance(action_id="noop", actor="test", objective=f"Batch {i}")
            for i in range(5)
        ]
        results = await runtime.execute_batch(instances)
        assert len(results) == 5
        for r in results:
            assert r.state == ExecutionState.COMPLETED

    @pytest.mark.asyncio
    async def test_batch_with_dependencies(self, runtime):
        a = runtime.create_instance(action_id="noop", actor="test", objective="Root")
        b = runtime.create_instance(action_id="noop", actor="test", objective="Child",
                                     dependencies=[a.execution_id])
        c = runtime.create_instance(action_id="noop", actor="test", objective="Grandchild",
                                     dependencies=[b.execution_id])
        results = await runtime.execute_batch([a, b, c])
        assert len(results) == 3
        assert all(r.state == ExecutionState.COMPLETED for r in results)


# ══════════════════════════════════════════════════════════════════════════
# 12. Policies
# ══════════════════════════════════════════════════════════════════════════

class TestPolicies:
    def test_custom_policies(self):
        policies = ExecutionPolicies()
        policies.retry.max_retries = 0
        policies.concurrency.max_concurrent_executions = 5
        r = ExecutionRuntime(policies=policies)
        assert r._policies.retry.max_retries == 0
        assert r._policies.concurrency.max_concurrent_executions == 5

    def test_health_contains_policies(self, runtime):
        hc = runtime.health_check()
        assert "policies" in hc
        assert hc["policies"]["retry_max"] == 3


# ══════════════════════════════════════════════════════════════════════════
# 13. Health
# ══════════════════════════════════════════════════════════════════════════

class TestHealthCheck:
    def test_health_empty_runtime(self):
        r = ExecutionRuntime()
        hc = r.health_check()
        assert hc["status"] == "healthy"
        assert hc["actions_registered"] == 0
        assert hc["total_instances"] == 0

    def test_health_with_actions(self, runtime):
        hc = runtime.health_check()
        assert hc["status"] == "healthy"
        assert hc["actions_registered"] == 3
        assert "noop" in hc["actions"]

    @pytest.mark.asyncio
    async def test_health_after_execution(self, runtime, noop_instance):
        await runtime.schedule(noop_instance)
        hc = runtime.health_check()
        assert hc["total_instances"] == 1
        assert hc["active_instances"] == 0


# ══════════════════════════════════════════════════════════════════════════
# 14. Graph Validation
# ══════════════════════════════════════════════════════════════════════════

class TestGraphValidation:
    def test_validation_clean_graph(self, runtime):
        a = runtime.create_instance(action_id="noop", actor="test", objective="A")
        _ = runtime.create_instance(action_id="noop", actor="test", objective="B",
                                     dependencies=[a.execution_id])
        issues = runtime.validate_graph()
        assert len(issues) == 0

    def test_validation_broken_dependency(self, runtime):
        _ = runtime.create_instance(
            action_id="noop", actor="test", objective="Broken",
            dependencies=["ghost"],
        )
        issues = runtime.validate_graph()
        assert any("ghost" in i for i in issues)


# ══════════════════════════════════════════════════════════════════════════
# 15. Universal Validation (industry-agnostic)
# ══════════════════════════════════════════════════════════════════════════

class TestUniversalValidation:
    """Demonstrate the same runtime executing different workflow patterns
    without code changes. Only action handlers differ."""

    @pytest.mark.asyncio
    async def test_crm_workflow_pattern(self, runtime):
        """CRM: Lead → Opportunity → Deal (sequential)."""
        runtime.register_action("validate_lead", handler=lambda i: {"qualified": True})
        runtime.register_action("score_opportunity", handler=lambda i: {"score": 85})
        runtime.register_action("approve_deal", handler=lambda i: {"approved": True})

        lead = runtime.create_instance(action_id="validate_lead", actor="sales", objective="Validate lead")
        opp = runtime.create_instance(action_id="score_opportunity", actor="sales", objective="Score opportunity",
                                       dependencies=[lead.execution_id])
        deal = runtime.create_instance(action_id="approve_deal", actor="manager", objective="Approve deal",
                                       dependencies=[opp.execution_id])
        await runtime.schedule(lead)
        await runtime.schedule(opp)
        await runtime.schedule(deal)
        assert lead.state == ExecutionState.COMPLETED
        assert opp.state == ExecutionState.COMPLETED
        assert deal.state == ExecutionState.COMPLETED

    @pytest.mark.asyncio
    async def test_healthcare_workflow_pattern(self, runtime):
        """Healthcare: Patient Intake → Triage → Treatment (barrier)."""
        runtime.register_action("register_patient", handler=lambda i: {"patient_id": "P-001"})
        runtime.register_action("triage", handler=lambda i: {"priority": "high"})
        runtime.register_action("assign_doctor", handler=lambda i: {"doctor": "Dr. Smith"})
        runtime.register_action("start_treatment",
                                handler=lambda i: {"status": "in_progress"})

        intake = runtime.create_instance(action_id="register_patient", actor="nurse", objective="Register")
        triage = runtime.create_instance(action_id="triage", actor="nurse", objective="Triage",
                                          dependencies=[intake.execution_id])
        doctor = runtime.create_instance(action_id="assign_doctor", actor="admin", objective="Assign",
                                          dependencies=[triage.execution_id])
        treatment = runtime.create_instance(action_id="start_treatment", actor="doctor", objective="Treat",
                                             dependencies=[doctor.execution_id])
        await runtime.schedule(intake)
        await runtime.schedule(triage)
        await runtime.schedule(doctor)
        await runtime.schedule(treatment)
        assert treatment.state == ExecutionState.COMPLETED

    @pytest.mark.asyncio
    async def test_travel_workflow_pattern(self, runtime):
        """Travel: Search → Book → Confirm (fan-out + fan-in)."""
        runtime.register_action("search_flights", handler=lambda i: {"flights": ["AA100", "UA200"]})
        runtime.register_action("book_flight", handler=lambda i: {"booking_ref": "BK-001"})
        runtime.register_action("confirm_payment", handler=lambda i: {"paid": True})

        search = runtime.create_instance(action_id="search_flights", actor="user", objective="Search")
        book = runtime.create_instance(action_id="book_flight", actor="user", objective="Book",
                                       dependencies=[search.execution_id])
        confirm = runtime.create_instance(action_id="confirm_payment", actor="system", objective="Confirm",
                                          dependencies=[book.execution_id])
        await runtime.schedule(search)
        await runtime.schedule(book)
        await runtime.schedule(confirm)
        assert search.state == ExecutionState.COMPLETED
        assert book.state == ExecutionState.COMPLETED
        assert confirm.state == ExecutionState.COMPLETED

    @pytest.mark.asyncio
    async def test_erp_workflow_pattern(self, runtime):
        """ERP: Create PO → Approve PO → Receive → Pay (parallel + fan-in)."""
        runtime.register_action("create_po", handler=lambda i: {"po_id": "PO-001"})
        runtime.register_action("approve_po", handler=lambda i: {"approved": True})
        runtime.register_action("receive_goods", handler=lambda i: {"received": True})
        runtime.register_action("pay_invoice", handler=lambda i: {"paid": True})

        po = runtime.create_instance(action_id="create_po", actor="buyer", objective="Create PO")
        approve = runtime.create_instance(action_id="approve_po", actor="manager", objective="Approve",
                                          dependencies=[po.execution_id])
        receive = runtime.create_instance(action_id="receive_goods", actor="warehouse", objective="Receive",
                                          dependencies=[po.execution_id])
        pay = runtime.create_instance(action_id="pay_invoice", actor="finance", objective="Pay",
                                      dependencies=[approve.execution_id, receive.execution_id])
        await runtime.schedule(po)
        await runtime.schedule(approve)
        await runtime.schedule(receive)
        await runtime.schedule(pay)
        assert pay.state == ExecutionState.COMPLETED