"""SHUNYA Automation & Event Runtime — Orchestrator."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.automation_runtime.models import (
    AutomationStats,
    AutomationTrace,
    DeadLetterEvent,
    Event,
    EventRecord,
    EventSchema,
    Rule,
    RuleCondition,
    RuleOperator,
    ScheduledAutomation,
    Subscription,
    Trigger,
    TriggerStatus,
    TriggerType,
    Workflow,
    WorkflowStatus,
    WorkflowStep,
    _now_iso,
)

logger = logging.getLogger(__name__)


class AutomationRuntime:
    """Event-driven automation engine. Continuously reacts to changes."""

    def __init__(self):
        self._schemas: dict[str, EventSchema] = {}
        self._events: list[EventRecord] = []
        self._subscriptions: dict[str, Subscription] = {}
        self._triggers: dict[str, Trigger] = {}
        self._rules: dict[str, Rule] = {}
        self._workflows: dict[str, Workflow] = {}
        self._schedules: dict[str, ScheduledAutomation] = {}
        self._dead_letter: list[DeadLetterEvent] = []
        self._idempotency: set[str] = set()
        self._traces: list[AutomationTrace] = []
        self._topic_subscribers: dict[str, list[str]] = {}

    # ── Event Schema Registry ─────────────────────────────────────────

    def register_schema(self, event_type: str, schema: dict[str, Any],
                        description: str = "") -> EventSchema:
        version = 1
        for s in self._schemas.values():
            if s.event_type == event_type:
                version = max(version, s.version + 1)
        es = EventSchema(event_type=event_type, version=version,
                         schema=schema, description=description)
        self._schemas[es.schema_id] = es
        return es

    def get_schema(self, event_type: str) -> EventSchema | None:
        for s in self._schemas.values():
            if s.event_type == event_type:
                return s
        return None

    # ── Event Bus ─────────────────────────────────────────────────────

    async def publish(self, event: Event) -> Event:
        """Publish an event to the bus. Returns the event with generated ID."""
        record = EventRecord(event=event)
        self._events.append(record)

        # Idempotency check
        if event.idempotency_key and event.idempotency_key in self._idempotency:
            self._record_trace("publish_duplicate", event_id=event.event_id)
            return event
        if event.idempotency_key:
            self._idempotency.add(event.idempotency_key)

        record.provenance.append(f"Published at {_now_iso()}")

        # Check triggers
        self._evaluate_triggers(event, record)

        # Check rules
        self._evaluate_rules(event, record)

        # Notify subscribers
        await self._notify_subscribers(event)

        self._record_trace("publish", event_id=event.event_id,
                           details={"topic": event.topic, "type": event.event_type})
        return event

    def subscribe(self, topic: str, handler: Any,
                  filter_expression: str = "",
                  max_retries: int = 3) -> Subscription:
        sub = Subscription(topic=topic, handler=handler,
                          filter_expression=filter_expression,
                          max_retries=max_retries)
        self._subscriptions[sub.sub_id] = sub
        self._topic_subscribers.setdefault(topic, []).append(sub.sub_id)
        return sub

    def unsubscribe(self, sub_id: str) -> bool:
        sub = self._subscriptions.pop(sub_id, None)
        if sub:
            subs = self._topic_subscribers.get(sub.topic, [])
            if sub_id in subs:
                subs.remove(sub_id)
            return True
        return False

    async def _notify_subscribers(self, event: Event) -> None:
        """Notify subscribers matching the event topic."""
        sub_ids = self._topic_subscribers.get(event.topic, [])
        for sub_id in sub_ids:
            sub = self._subscriptions.get(sub_id)
            if not sub:
                continue
            # Filter check
            if sub.filter_expression and not self._evaluate_simple_expression(event, sub.filter_expression):
                    continue
            try:
                result = sub.handler(event)
                if asyncio.iscoroutine(result):
                    await asyncio.wait_for(result, timeout=sub.timeout_ms / 1000)
            except (ValueError, TypeError, RuntimeError) as exc:
                logger.warning("Subscriber %s failed: %s", sub_id, exc)

    # ── Trigger Engine ────────────────────────────────────────────────

    def register_trigger(self, name: str, topic: str, condition: str,
                         action: str, trigger_type: TriggerType = TriggerType.EVENT,
                         requires_approval: bool = False) -> Trigger:
        trigger = Trigger(name=name, topic=topic, condition=condition,
                         action=action, trigger_type=trigger_type,
                         requires_approval=requires_approval)
        self._triggers[trigger.trigger_id] = trigger
        return trigger

    def pause_trigger(self, trigger_id: str) -> bool:
        t = self._triggers.get(trigger_id)
        if t:
            t.status = TriggerStatus.PAUSED
            return True
        return False

    def resume_trigger(self, trigger_id: str) -> bool:
        t = self._triggers.get(trigger_id)
        if t:
            t.status = TriggerStatus.ACTIVE
            return True
        return False

    def _evaluate_triggers(self, event: Event, record: EventRecord) -> None:
        for trigger in self._triggers.values():
            if trigger.status != TriggerStatus.ACTIVE:
                continue
            if trigger.topic and trigger.topic != event.topic:
                continue
            if trigger.condition and not self._evaluate_simple_expression(event, trigger.condition):
                    continue
            # Trigger fires
            record.provenance.append(f"Triggered: {trigger.name}")
            self._record_trace("trigger_fired", event_id=event.event_id,
                               trigger_id=trigger.trigger_id)

            if trigger.requires_approval:
                # Create workflow awaiting approval
                self._create_approval_workflow(f"Approval: {trigger.name}", event, trigger)
            else:
                # Execute action directly (simulated)
                pass

    def _evaluate_simple_expression(self, event: Event, expression: str) -> bool:
        """Evaluate a simple expression like 'priority == \"high\"' or 'payload.value > 100'."""
        try:
            # Handle priority comparisons
            if "priority" in expression:
                expr = expression.replace("priority", f"'{event.priority.value}'")
                return bool(eval(expr))
            # Handle payload field access
            for key, val in event.payload.items():
                if isinstance(val, str):
                    expr = expression.replace(f"payload.{key}", f"'{val}'")
                else:
                    expr = expression.replace(f"payload.{key}", str(val))
                if expr != expression:
                    return bool(eval(expr))
            # Simple keyword match
            if expression.startswith("event."):
                fields = expression[6:].split("==")
                if len(fields) == 2:
                    field = fields[0].strip()
                    val = fields[1].strip().strip("'\"")
                    if field == "event_type":
                        return event.event_type == val
                    elif field == "topic":
                        return event.topic == val
                    elif field == "source":
                        return event.source == val
            return True
        except (ValueError, TypeError, RuntimeError, NameError):
            logger.debug("Expression evaluation failed: %s", expression)
            return False

    # ── Rule Engine ───────────────────────────────────────────────────

    def add_rule(self, name: str, event_type: str,
                 conditions: list[RuleCondition],
                 action: str) -> Rule:
        rule = Rule(name=name, event_type=event_type,
                   conditions=conditions, action=action)
        self._rules[rule.rule_id] = rule
        return rule

    def _evaluate_rules(self, event: Event, record: EventRecord) -> None:
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if rule.event_type and rule.event_type != event.event_type:
                continue

            matched = True
            for cond in rule.conditions:
                if not self._evaluate_condition(event, cond):
                    matched = False
                    break

            if matched:
                record.provenance.append(f"Rule matched: {rule.name}")
                self._record_trace("rule_matched", event_id=event.event_id,
                                   details={"rule": rule.name})

    @staticmethod
    def _evaluate_condition(event: Event, condition: RuleCondition) -> bool:
        """Evaluate a single rule condition against an event."""
        # Extract value from event
        if condition.field == "event_type":
            actual: Any = event.event_type
        elif condition.field == "topic":
            actual = event.topic
        elif condition.field == "source":
            actual = event.source
        elif condition.field == "priority":
            actual = event.priority.value
        elif condition.field.startswith("payload."):
            key = condition.field[8:]
            actual = event.payload.get(key)
        else:
            actual = None

        if condition.operator == RuleOperator.EQUALS:
            return actual == condition.value
        elif condition.operator == RuleOperator.NOT_EQUALS:
            return actual != condition.value
        elif condition.operator in (RuleOperator.GREATER_THAN, RuleOperator.LESS_THAN):
            try:
                a = float(actual) if actual is not None else 0.0
                b = float(condition.value) if condition.value is not None else 0.0
                if condition.operator == RuleOperator.GREATER_THAN:
                    return a > b
                else:
                    return a < b
            except (ValueError, TypeError):
                return False
        elif condition.operator == RuleOperator.CONTAINS:
            return condition.value in str(actual)
        elif condition.operator == RuleOperator.IN:
            return actual in (condition.value or [])
        return False

    # ── Workflow Orchestration ────────────────────────────────────────

    def create_workflow(self, name: str, steps: list[dict[str, Any]]) -> Workflow:
        workflow_steps = []
        for i, s in enumerate(steps):
            step = WorkflowStep(
                name=s.get("name", f"Step {i+1}"),
                action=s.get("action", ""),
                depends_on=s.get("depends_on", []),
                requires_approval=s.get("requires_approval", False),
                timeout_ms=s.get("timeout_ms", 60000),
                max_retries=s.get("max_retries", 3),
            )
            workflow_steps.append(step)
        wf = Workflow(name=name, steps=workflow_steps)
        self._workflows[wf.workflow_id] = wf
        self._record_trace("create_workflow", workflow_id=wf.workflow_id)
        return wf

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def advance_workflow(self, workflow_id: str) -> Workflow | None:
        """Advance a workflow to the next step whose dependencies are met."""
        wf = self._workflows.get(workflow_id)
        if not wf or wf.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED):
            return wf

        wf.status = WorkflowStatus.RUNNING
        for i, step in enumerate(wf.steps):
            if step.status != "pending":
                continue
            # Check dependencies
            deps_met = all(
                any(s.name == dep and s.status == "completed" for s in wf.steps)
                for dep in step.depends_on
            )
            if not deps_met:
                continue
            if step.requires_approval:
                wf.status = WorkflowStatus.WAITING_APPROVAL
                step.status = "waiting_approval"
                wf.current_step = i
                return wf
            step.status = "completed"
            wf.current_step = i
            self._record_trace("advance_workflow", workflow_id=workflow_id,
                               details={"step": step.name})

        # Check if all steps completed
        if all(s.status == "completed" for s in wf.steps):
            wf.status = WorkflowStatus.COMPLETED
        return wf

    def approve_step(self, workflow_id: str, step_name: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return False
        for step in wf.steps:
            if step.name == step_name:
                step.approved = True
                step.status = "completed"
                wf.status = WorkflowStatus.RUNNING
                self.advance_workflow(workflow_id)
                return True
        return False

    def _create_approval_workflow(self, name: str, event: Event, trigger: Trigger) -> Workflow:
        step = WorkflowStep(name="approval", action=trigger.action,
                           requires_approval=True)
        wf = Workflow(name=name, trigger_event_id=event.event_id, steps=[step],
                      status=WorkflowStatus.WAITING_APPROVAL)
        self._workflows[wf.workflow_id] = wf
        return wf

    # ── Scheduled Automations ─────────────────────────────────────────

    def add_schedule(self, name: str, cron: str, action: str) -> ScheduledAutomation:
        sa = ScheduledAutomation(name=name, cron=cron, action=action)
        self._schedules[sa.schedule_id] = sa
        return sa

    def list_schedules(self) -> list[ScheduledAutomation]:
        return list(self._schedules.values())

    # ── Event Sourcing & Replay ───────────────────────────────────────

    def get_events(self, topic: str | None = None,
                   event_type: str | None = None,
                   limit: int = 100) -> list[EventRecord]:
        results = self._events
        if topic:
            results = [r for r in results if r.event.topic == topic]
        if event_type:
            results = [r for r in results if r.event.event_type == event_type]
        return results[-limit:]

    def replay_events(self, topic: str | None = None,
                      event_type: str | None = None) -> int:
        """Re-trigger processing for historical events."""
        count = 0
        for record in self._events:
            if record.processed:
                continue
            if topic and record.event.topic != topic:
                continue
            if event_type and record.event.event_type != event_type:
                continue
            self._evaluate_triggers(record.event, record)
            self._evaluate_rules(record.event, record)
            record.processed = True
            count += 1
        return count

    # ── Dead-Letter Queue ─────────────────────────────────────────────

    def dead_letter(self, event: Event, error: str, retry_count: int = 0) -> DeadLetterEvent:
        dlq = DeadLetterEvent(event=event, error=error, retry_count=retry_count)
        self._dead_letter.append(dlq)
        self._record_trace("dead_letter", event_id=event.event_id,
                           details={"error": error})
        return dlq

    def get_dead_letter(self, limit: int = 100) -> list[DeadLetterEvent]:
        return self._dead_letter[-limit:]

    async def retry_dead_letter(self, dlq_id: str) -> bool:
        for dlq in self._dead_letter:
            if dlq.dlq_id == dlq_id:
                await self.publish(dlq.event)
                self._dead_letter.remove(dlq)
                return True
        return False

    # ── Observability ─────────────────────────────────────────────────

    def get_stats(self) -> AutomationStats:
        by_topic: dict[str, int] = {}
        for r in self._events:
            by_topic[r.event.topic] = by_topic.get(r.event.topic, 0) + 1
        return AutomationStats(
            total_events=len(self._events),
            total_triggers=len(self._triggers),
            total_workflows=len(self._workflows),
            total_rules=len(self._rules),
            events_by_topic=by_topic,
            dead_letter_count=len(self._dead_letter),
        )

    def get_traces(self, limit: int = 100) -> list[AutomationTrace]:
        return self._traces[-limit:]

    def health_check(self) -> dict[str, Any]:
        stats = self.get_stats()
        return {
            "status": "healthy",
            "runtime": "automation_runtime",
            "total_events": stats.total_events,
            "total_triggers": stats.total_triggers,
            "total_workflows": stats.total_workflows,
            "total_rules": stats.total_rules,
            "dead_letter_count": stats.dead_letter_count,
            "events_by_topic": stats.events_by_topic,
        }

    def _record_trace(self, operation: str, event_id: str = "",
                      trigger_id: str = "", workflow_id: str = "",
                      details: dict | None = None) -> None:
        self._traces.append(AutomationTrace(
            operation=operation, event_id=event_id, trigger_id=trigger_id,
            workflow_id=workflow_id, details=details or {},
        ))