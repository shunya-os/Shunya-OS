"""
Tests for SHUNYA Orchestration Runtime — Phase Z9.

Validates: Cycle execution, Signal propagation, Trigger evaluation,
Action execution, Execution queue ordering, Synchronization, Inspection.
"""

import pytest
from app.orchestration.signal import (
    RuntimeSignal, Trigger, TriggerEvent, ActionType, OrchestrationAction,
    SignalBus, get_bus, reset_bus,
)
from app.orchestration.cycle import OrchestratorEngine, get_engine, reset_engine
from app.orchestration.queue import ExecutionQueue, get_queue, reset_queue
from app.orchestration.sync import SynchronizationPoint, SyncManager, get_manager, reset_manager


# ══════════════════════════════════════════════════════════════
# Signal Tests
# ══════════════════════════════════════════════════════════════


class TestSignal:
    def test_create_signal(self):
        s = RuntimeSignal(signal_id="s1", source_runtime="decision", trigger_event=TriggerEvent.DECISION_APPROVED)
        assert s.source_runtime == "decision"
        assert s.trigger_event == TriggerEvent.DECISION_APPROVED

    def test_signal_bus(self):
        bus = SignalBus()
        bus.publish("test", TriggerEvent.DECISION_APPROVED, {"id": "d1"})
        assert bus.count == 1
        signals = bus.get_signals()
        assert signals[0].payload["id"] == "d1"

    def test_signal_to_dict(self):
        s = RuntimeSignal(signal_id="s1", source_runtime="execution", trigger_event=TriggerEvent.EXECUTION_COMPLETED)
        d = s.to_dict()
        assert d["signal_id"] == "s1"
        assert d["trigger_event"] == "execution_completed"


# ══════════════════════════════════════════════════════════════
# Trigger Tests
# ══════════════════════════════════════════════════════════════


class TestTrigger:
    def test_trigger_matches_event(self):
        t = Trigger(trigger_id="t1", trigger_event=TriggerEvent.CHECKPOINT_FAILED, action_type=ActionType.ESCALATE)
        s = RuntimeSignal(signal_id="s1", source_runtime="planning", trigger_event=TriggerEvent.CHECKPOINT_FAILED)
        result = t.evaluate(s)
        assert result == ActionType.ESCALATE

    def test_trigger_does_not_match(self):
        t = Trigger(trigger_id="t1", trigger_event=TriggerEvent.CHECKPOINT_FAILED, action_type=ActionType.ESCALATE)
        s = RuntimeSignal(signal_id="s1", source_runtime="planning", trigger_event=TriggerEvent.EXECUTION_COMPLETED)
        result = t.evaluate(s)
        assert result is None

    def test_trigger_with_condition(self):
        def condition(signal, state):
            return signal.payload.get("severity") == "high"

        t = Trigger(trigger_id="t1", trigger_event=TriggerEvent.HEALTH_DECLINED,
                     action_type=ActionType.NOTIFY, condition_fn=condition)
        s1 = RuntimeSignal(signal_id="s1", source_runtime="cortex", trigger_event=TriggerEvent.HEALTH_DECLINED,
                           payload={"severity": "low"})
        assert t.evaluate(s1) is None
        s2 = RuntimeSignal(signal_id="s2", source_runtime="cortex", trigger_event=TriggerEvent.HEALTH_DECLINED,
                           payload={"severity": "high"})
        assert t.evaluate(s2) == ActionType.NOTIFY


# ══════════════════════════════════════════════════════════════
# Orchestration Cycle Tests
# ══════════════════════════════════════════════════════════════


class TestOrchestrationCycle:
    def setup_method(self):
        reset_engine()
        reset_bus()

    def test_cycle_execution(self):
        engine = get_engine()
        bus = get_bus()
        engine.register_trigger(Trigger(trigger_id="t1", trigger_event=TriggerEvent.DECISION_APPROVED, action_type=ActionType.NOTIFY))
        bus.publish("decision", TriggerEvent.DECISION_APPROVED, {"id": "d1"})
        cycle = engine.execute_cycle(bus)
        assert cycle.status == "completed"
        assert cycle.signals_processed == 1
        assert cycle.actions_produced >= 1

    def test_cycle_no_signals(self):
        engine = get_engine()
        bus = get_bus()
        cycle = engine.execute_cycle(bus)
        assert cycle.signals_processed == 0
        assert cycle.actions_produced == 0

    def test_multiple_cycles(self):
        engine = get_engine()
        bus = get_bus()
        engine.execute_cycle(bus)
        engine.execute_cycle(bus)
        assert engine.cycle_count == 2

    def test_cycle_to_dict(self):
        engine = get_engine()
        bus = get_bus()
        cycle = engine.execute_cycle(bus)
        d = cycle.to_dict()
        assert "cycle_id" in d
        assert "duration_ms" in d


# ══════════════════════════════════════════════════════════════
# Execution Queue Tests
# ══════════════════════════════════════════════════════════════


class TestExecutionQueue:
    def setup_method(self):
        reset_queue()

    def test_enqueue_dequeue(self):
        q = get_queue()
        a = OrchestrationAction(action_id="a1", trigger_id="t1", action_type=ActionType.NOTIFY, signal_id="s1")
        q.enqueue(a)
        assert q.pending_count == 1
        dequeued = q.dequeue()
        assert dequeued is not None
        assert dequeued.action_id == "a1"
        assert q.pending_count == 0

    def test_priority_ordering(self):
        q = get_queue()
        q.enqueue(OrchestrationAction(action_id="a1", trigger_id="t1", action_type=ActionType.NOTIFY, signal_id="s1"))
        q.enqueue(OrchestrationAction(action_id="a2", trigger_id="t2", action_type=ActionType.ESCALATE, signal_id="s2"))
        q.enqueue(OrchestrationAction(action_id="a3", trigger_id="t3", action_type=ActionType.START, signal_id="s3"))

        first = q.dequeue()
        assert first.action_id == "a2"  # ESCALATE has highest priority
        second = q.dequeue()
        assert second.action_type == ActionType.START
        third = q.dequeue()
        assert third.action_type == ActionType.NOTIFY

    def test_complete(self):
        q = get_queue()
        a = OrchestrationAction(action_id="a1", trigger_id="t1", action_type=ActionType.NOTIFY, signal_id="s1")
        q.enqueue(a)
        q.dequeue()
        q.complete(a)
        assert q.completed_count == 1
        assert a.is_executed

    def test_cancel(self):
        q = get_queue()
        q.enqueue(OrchestrationAction(action_id="a1", trigger_id="t1", action_type=ActionType.NOTIFY, signal_id="s1"))
        assert q.cancel("a1")
        assert q.cancelled_count == 1
        assert q.pending_count == 0

    def test_empty_dequeue(self):
        q = get_queue()
        assert q.dequeue() is None


# ══════════════════════════════════════════════════════════════
# Synchronization Tests
# ══════════════════════════════════════════════════════════════


class TestSynchronization:
    def setup_method(self):
        reset_manager()

    def test_create_sync(self):
        sm = get_manager()
        sp = sm.create_sync(["planning", "execution"])
        assert sp.status == "pending"
        assert sm.count == 1

    def test_complete_sync(self):
        sm = get_manager()
        sp = sm.create_sync(["planning", "temporal"])
        sm.complete_sync(sp.sync_id)
        assert sp.status == "completed"
        assert sp.completed_at is not None

    def test_get_pending(self):
        sm = get_manager()
        sm.create_sync(["planning"])
        sm.create_sync(["execution"])
        sp3 = sm.create_sync(["temporal"])
        sm.complete_sync(sp3.sync_id)
        assert len(sm.get_pending()) == 2


# ══════════════════════════════════════════════════════════════
# Business Agnosticism Tests
# ══════════════════════════════════════════════════════════════


class TestBusinessAgnosticism:
    def test_signal_no_industry(self):
        s = RuntimeSignal(signal_id="s1", source_runtime="decision", trigger_event=TriggerEvent.DECISION_APPROVED)
        assert not hasattr(s, "industry")

    def test_trigger_no_industry(self):
        t = Trigger(trigger_id="t1", trigger_event=TriggerEvent.DECISION_APPROVED, action_type=ActionType.NOTIFY)
        assert not hasattr(t, "project")

    def test_sync_no_industry(self):
        sp = SynchronizationPoint(sync_id="s1", runtimes=["planning"])
        assert not hasattr(sp, "team")


# ══════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════


class TestOrchestrationIntegration:
    def test_orch_loads_with_app(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            assert c.get('/').status_code == 200
            assert c.get('/workspace/').status_code == 200
            r = c.get('/workspace/?inspect_orch=1')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert 'orchestrator' in data
            assert 'signals' in data
            assert 'queue' in data
            assert 'synchronization' in data

    def test_orchestrator_cycle_executed_on_startup(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            r = c.get('/workspace/?inspect_orch=1')
            data = r.get_json()
            assert data['orchestrator']['cycles'] >= 1
            assert data['signals']['total'] >= 1
            assert 'recent_cycles' in data['orchestrator']