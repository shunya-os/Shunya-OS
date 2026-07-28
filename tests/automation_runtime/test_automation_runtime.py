"""Tests for Automation & Event Runtime."""

import pytest

from core.automation_runtime import (
    AutomationRuntime,
    Event,
    EventPriority,
    RuleCondition,
    RuleOperator,
    WorkflowStatus,
)


@pytest.fixture
def runtime():
    return AutomationRuntime()


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish(self, runtime):
        event = Event(topic="order.created", payload={"order_id": 123})
        result = await runtime.publish(event)
        assert result.event_id
        assert result.topic == "order.created"

    @pytest.mark.asyncio
    async def test_idempotency(self, runtime):
        event1 = Event(topic="t", idempotency_key="key1", payload={"x": 1})
        event2 = Event(topic="t", idempotency_key="key1", payload={"x": 2})
        await runtime.publish(event1)
        await runtime.publish(event2)
        stats = runtime.get_stats()
        assert stats.total_events == 2
        traces = runtime.get_traces()
        dup = [t for t in traces if t.operation == "publish_duplicate"]
        assert len(dup) == 1

    @pytest.mark.asyncio
    async def test_subscribe_and_notify(self, runtime):
        received = []
        async def handler(event):
            received.append(event)
        runtime.subscribe("test.topic", handler)
        await runtime.publish(Event(topic="test.topic", payload={"data": 1}))
        assert len(received) == 1
        assert received[0].topic == "test.topic"

    def test_unsubscribe(self, runtime):
        sub = runtime.subscribe("t", lambda e: None)
        assert runtime.unsubscribe(sub.sub_id) is True
        assert runtime.unsubscribe("nonexistent") is False


class TestEventSchema:
    def test_register_schema(self, runtime):
        s = runtime.register_schema("order.created", {"type": "object"})
        assert s.event_type == "order.created"
        assert s.version == 1

    def test_get_schema(self, runtime):
        runtime.register_schema("user.updated", {})
        assert runtime.get_schema("user.updated") is not None


class TestTriggerEngine:
    def test_register_trigger(self, runtime):
        t = runtime.register_trigger("High order", "order.created",
                                      "payload.value > 1000", "alert")
        assert t.name == "High order"
        assert t.status.value == "active"

    def test_pause_resume(self, runtime):
        t = runtime.register_trigger("T", "t", "", "a")
        assert runtime.pause_trigger(t.trigger_id)
        assert t.status.value == "paused"
        assert runtime.resume_trigger(t.trigger_id)
        assert t.status.value == "active"

    @pytest.mark.asyncio
    async def test_trigger_fires(self, runtime):
        runtime.register_trigger("Match", "events", "priority == 'high'", "alert")
        event = Event(topic="events", priority=EventPriority.HIGH, payload={"v": 1})
        await runtime.publish(event)
        traces = runtime.get_traces()
        assert any(t.operation == "trigger_fired" for t in traces)

    @pytest.mark.asyncio
    async def test_trigger_approval(self, runtime):
        runtime.register_trigger("Approve", "app", "", "act", requires_approval=True)
        await runtime.publish(Event(topic="app", payload={"x": 1}))
        wfs = [w for w in runtime._workflows.values()
               if w.status == WorkflowStatus.WAITING_APPROVAL]
        assert len(wfs) >= 1


class TestRuleEngine:
    def test_add_rule(self, runtime):
        r = runtime.add_rule("High", "order.created",
                             [RuleCondition(field="payload.v", operator=RuleOperator.GREATER_THAN, value=100)],
                             "finance")
        assert r.name == "High"

    @pytest.mark.asyncio
    async def test_rule_matches(self, runtime):
        runtime.add_rule("Match", "test.e",
                         [RuleCondition(field="payload.score", operator=RuleOperator.GREATER_THAN, value=50)],
                         "alert")
        await runtime.publish(Event(event_type="test.e", payload={"score": 80}))
        traces = runtime.get_traces()
        assert any(t.operation == "rule_matched" for t in traces)

    @pytest.mark.asyncio
    async def test_rule_no_match(self, runtime):
        runtime.add_rule("NoMatch", "test.e",
                         [RuleCondition(field="payload.score", operator=RuleOperator.LESS_THAN, value=10)],
                         "alert")
        await runtime.publish(Event(event_type="test.e", payload={"score": 80}))
        traces = runtime.get_traces()
        assert not any(t.operation == "rule_matched" for t in traces)


class TestWorkflow:
    def test_create(self, runtime):
        steps = [{"name": "A", "action": "act1"}, {"name": "B", "action": "act2", "depends_on": ["A"]}]
        wf = runtime.create_workflow("W", steps)
        assert len(wf.steps) == 2

    def test_advance(self, runtime):
        wf = runtime.create_workflow("W", [{"name": "A", "action": "a"}])
        result = runtime.advance_workflow(wf.workflow_id)
        assert result.status == WorkflowStatus.COMPLETED

    def test_advance_with_approval(self, runtime):
        wf = runtime.create_workflow("W", [{"name": "A", "action": "a", "requires_approval": True}])
        result = runtime.advance_workflow(wf.workflow_id)
        assert result.status == WorkflowStatus.WAITING_APPROVAL

    def test_approve_step(self, runtime):
        wf = runtime.create_workflow("W", [{"name": "A", "action": "a", "requires_approval": True}])
        runtime.advance_workflow(wf.workflow_id)
        assert runtime.approve_step(wf.workflow_id, "A") is True
        assert wf.status == WorkflowStatus.COMPLETED


class TestEventSourcing:
    @pytest.mark.asyncio
    async def test_get_events(self, runtime):
        await runtime.publish(Event(topic="t1", payload={"a": 1}))
        await runtime.publish(Event(topic="t2", payload={"b": 2}))
        events = runtime.get_events(topic="t1")
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_replay(self, runtime):
        await runtime.publish(Event(topic="r", payload={"x": 1}))
        for r in runtime._events:
            r.processed = False
        count = runtime.replay_events(topic="r")
        assert count >= 1


class TestDeadLetter:
    def test_dead_letter(self, runtime):
        dlq = runtime.dead_letter(Event(topic="f", payload={}), "err", 3)
        assert dlq.error == "err"
        assert dlq.retry_count == 3

    def test_get_dead_letter(self, runtime):
        runtime.dead_letter(Event(topic="t", payload={}), "e1")
        runtime.dead_letter(Event(topic="t", payload={}), "e2")
        assert len(runtime.get_dead_letter()) == 2

    @pytest.mark.asyncio
    async def test_retry_dlq(self, runtime):
        dlq = runtime.dead_letter(Event(topic="r", payload={"ok": True}), "err")
        assert await runtime.retry_dead_letter(dlq.dlq_id) is True
        assert len(runtime.get_dead_letter()) == 0


class TestSchedule:
    def test_add_and_list(self, runtime):
        runtime.add_schedule("Daily", "0 9 * * *", "report")
        runtime.add_schedule("Hourly", "0 * * * *", "check")
        assert len(runtime.list_schedules()) == 2


class TestObservability:
    @pytest.mark.asyncio
    async def test_stats(self, runtime):
        await runtime.publish(Event(topic="t", payload={}))
        await runtime.publish(Event(topic="t", payload={}))
        stats = runtime.get_stats()
        assert stats.total_events == 2

    def test_health(self, runtime):
        hc = runtime.health_check()
        assert hc["status"] == "healthy"
        assert hc["runtime"] == "automation_runtime"