"""B6: Prove execution engine, automation runtime, and execution log are functional.

Tests the Flask-integrated modules (not the in-memory core.* runtimes):
  - app/execution_engine/ — gate, execute_action(), log_execution()
  - app/execution_log/ — ExecutionLog model, log_execution()
  - app/automation/ — rule CRUD, evaluate_triggers(), AutomationLog

Each test uses the production create_app() factory with SQLite in-memory.
"""

import pytest
from app import db


# =============================================================================
# Helpers
# =============================================================================

def _ensure_tables():
    """Create any tables not yet registered by the app fixture's create_all().

    The conftest app fixture creates all tables at fixture setup time, but
    execution_engine.models.ExecutionLog (table 'execution_logs') is registered
    lazily by the engine module.  Calling create_all() again is safe — it only
    creates tables that don't already exist.
    """
    from app.execution_engine.models import ExecutionLog  # noqa: F401
    from app.execution.models import Outcome  # noqa: F401
    db.create_all()


def _open_gate():
    """Open the execution gate for the test scope."""
    from app.execution_engine.engine import open_execution_gate
    open_execution_gate()


def _close_gate():
    """Close the execution gate after the test scope."""
    from app.execution_engine.engine import close_execution_gate
    close_execution_gate()


# =============================================================================
# 1. Execution Gate
# =============================================================================

class TestExecutionGate:
    """Prove the execution gate lifecycle works."""

    def test_gate_starts_closed(self):
        assert not __import__(
            "app.execution_engine.engine", fromlist=["is_gate_open"]
        ).is_gate_open()

    def test_gate_open_close_lifecycle(self):
        from app.execution_engine.engine import is_gate_open, open_execution_gate, close_execution_gate
        assert not is_gate_open()
        open_execution_gate()
        assert is_gate_open()
        close_execution_gate()
        assert not is_gate_open()

    def test_gate_refcount(self):
        """Multiple open calls keep the gate open until all are closed."""
        from app.execution_engine.engine import is_gate_open, open_execution_gate, close_execution_gate
        open_execution_gate()
        open_execution_gate()
        assert is_gate_open()
        close_execution_gate()
        assert is_gate_open()  # refcount still > 0
        close_execution_gate()
        assert not is_gate_open()  # last close closes it


# =============================================================================
# 2. Execution Engine — execute_action()
# =============================================================================

class TestExecuteAction:
    """Prove the full execution pipeline: gate → evidence → state change → log."""

    def test_execute_action_blocked_without_gate(self, app):
        """Gate enforcement: calling execute_action() without open gate raises."""
        _ensure_tables()
        obj = db.session.get(__import__("app.objects.models", fromlist=["Object"]).Object, 1)
        if not obj:
            from app.objects.models import Object
            obj = Object(type="task", state={"status": "new"}, tenant_id=1)
            db.session.add(obj)
            db.session.commit()

        from app.execution_engine.engine import execute_action
        with pytest.raises(RuntimeError, match="Direct execution forbidden"):
            execute_action(obj, {"type": "update", "payload": {"status": "done"}})

    def test_execute_action_blocked_without_evidence(self, app):
        """Evidence enforcement: no EvidenceRecord → RuntimeError."""
        _ensure_tables()
        from app.execution_engine.engine import open_execution_gate, close_execution_gate, execute_action
        from app.objects.models import Object

        _open_gate()
        try:
            obj = Object(type="task", state={"status": "new"}, tenant_id=1)
            db.session.add(obj)
            db.session.commit()

            with pytest.raises(RuntimeError, match="Execution without evidence forbidden"):
                execute_action(obj, {
                    "type": "update",
                    "payload": {"status": "completed"},
                    "decision_source": "test",
                    "decision_confidence": "high",
                })
        finally:
            _close_gate()

    def test_execute_action_full_pipeline(self, app):
        """Full end-to-end: gate open + evidence record → state mutation + log entry."""
        _ensure_tables()
        from app.execution_engine.engine import open_execution_gate, close_execution_gate, execute_action
        from app.objects.models import Object
        from app.evidence.models_db import EvidenceRecord
        from app.execution_engine.models import ExecutionLog

        _open_gate()
        try:
            # Create an Object
            obj = Object(
                type="task",
                state={"status": "new", "title": "B6 verification task"},
                tenant_id=1,
            )
            db.session.add(obj)
            db.session.commit()

            # Provide evidence (required by execute_action's evidence gate)
            evidence = EvidenceRecord(
                source_type="manual_test",
                source_id=str(obj.id),
                raw_reference={"test": "B6_execution_engine"},
            )
            db.session.add(evidence)
            db.session.commit()

            # Execute the action
            result = execute_action(obj, {
                "type": "update",
                "payload": {"status": "completed", "priority": "high"},
                "decision_source": "b6_verification",
                "decision_confidence": "high",
            })

            # Verify state change
            assert result.state["status"] == "completed"
            assert result.state["priority"] == "high"
            assert result.state["title"] == "B6 verification task"

            # Verify execution log entry was created
            logs = ExecutionLog.query.filter_by(object_id=obj.id).order_by(
                ExecutionLog.id.desc()
            ).all()
            assert len(logs) >= 1, "No execution log entry was created"
            entry = logs[0]
            assert entry.action_type == "update"
            assert entry.state_before == {"status": "new", "title": "B6 verification task"}
            assert entry.state_after == {
                "status": "completed", "title": "B6 verification task", "priority": "high"
            }
            assert entry.payload["status"] == "completed"
            assert entry.payload["priority"] == "high"
        finally:
            _close_gate()

    def test_execute_action_noop_skips_log(self, app):
        """Noop-type actions produce no state change and no log entry."""
        _ensure_tables()
        from app.execution_engine.engine import open_execution_gate, close_execution_gate, execute_action
        from app.objects.models import Object
        from app.evidence.models_db import EvidenceRecord
        from app.execution_engine.models import ExecutionLog

        _open_gate()
        try:
            obj = Object(type="task", state={"status": "new"}, tenant_id=1)
            db.session.add(obj)
            db.session.commit()
            evidence = EvidenceRecord(source_type="test", source_id=str(obj.id))
            db.session.add(evidence)
            db.session.commit()

            obj_id = obj.id
            result = execute_action(obj, {
                "type": "noop",
                "payload": {},
                "decision_source": "test",
                "decision_confidence": "low",
            })

            assert result.state == {"status": "new"}  # unchanged
            logs = ExecutionLog.query.filter_by(object_id=obj_id).all()
            # No log entry for noop actions
            assert len(logs) == 0
        finally:
            _close_gate()


# =============================================================================
# 3. Execution Log — standalone log_execution()
# =============================================================================

class TestExecutionLog:
    """Prove the execution log model and log_execution function work."""

    def test_log_execution_standalone(self, app):
        """Direct call to log_execution() creates a persisted record."""
        _ensure_tables()
        from app.execution_engine.service import log_execution
        from app.execution_engine.models import ExecutionLog

        entry = log_execution(
            object_id=999,
            action_type="test_action",
            payload={"key": "value"},
            state_before={"old": "state"},
            state_after={"new": "state"},
        )

        assert entry.id is not None
        assert entry.object_id == 999
        assert entry.action_type == "test_action"
        assert entry.payload == {"key": "value"}
        assert entry.state_before == {"old": "state"}
        assert entry.state_after == {"new": "state"}

        # Verify it's persisted
        fetched = db.session.get(ExecutionLog, entry.id)
        assert fetched is not None
        assert fetched.action_type == "test_action"

    def test_log_execution_defaults(self, app):
        """log_execution() with minimal args still creates a valid record."""
        _ensure_tables()
        from app.execution_engine.service import log_execution
        from app.execution_engine.models import ExecutionLog

        entry = log_execution(object_id=1, action_type="minimal")
        assert entry.id is not None
        assert entry.payload == {}
        assert entry.state_before == {}
        assert entry.state_after == {}

    def test_act_execution_log_model(self, app):
        """The act_execution_logs model (app/execution_log/models.py) is functional."""
        from app.execution_log.models import ExecutionLog

        entry = ExecutionLog(
            object_id=42,
            event_type="output_generated",
            payload={"title": "Test Output", "summary": "A test output item"},
        )
        db.session.add(entry)
        db.session.flush()

        assert entry.id is not None
        assert entry.object_id == 42
        assert entry.event_type == "output_generated"
        assert entry.payload["title"] == "Test Output"

        # This entry should appear in the /outputs endpoint
        fetched = db.session.get(ExecutionLog, entry.id)
        assert fetched is not None
        assert fetched.event_type == "output_generated"

    def test_act_log_execution_function(self, app):
        """The log_execution() helper in app/execution_log/models.py doesn't return
        the entry (it calls flush() without a return). Verify it still works
        by checking the DB afterward."""
        from app.execution_log.models import ExecutionLog, log_execution as act_log_execution

        act_log_execution(
            object_id=43,
            event_type="document_created",
            payload={"title": "Doc via helper"},
        )

        # Verify the entry was persisted
        entry = ExecutionLog.query.filter_by(object_id=43).first()
        assert entry is not None
        assert entry.event_type == "document_created"
        assert entry.payload["title"] == "Doc via helper"


# =============================================================================
# 4. Automation Runtime
# =============================================================================

class TestAutomation:
    """Prove the automation module (rule CRUD + trigger evaluation + log) works."""

    def test_create_rule(self, app):
        """Create an automation rule and verify it persists."""
        from app.automation.service import create_rule, get_rules

        rule = create_rule(
            identity_id="test_identity",
            name="Test Rule",
            trigger_type="status_changed",
            trigger_config={"entity_type": "Task", "field": "status", "to": "completed"},
            action_type="notify",
            action_config={"notification_type": "automation_fired", "title": "Task completed"},
        )
        assert rule["id"] is not None
        assert rule["name"] == "Test Rule"
        assert rule["trigger_type"] == "status_changed"
        assert rule["is_active"] is True

        # Verify it's queryable
        rules = get_rules(identity_id="test_identity")
        assert len(rules) >= 1
        assert any(r["id"] == rule["id"] for r in rules)

    def test_rule_crud(self, app):
        """Full CRUD lifecycle: create → read → update → toggle → delete."""
        from app.automation.service import (
            create_rule, get_rule, update_rule, toggle_rule, delete_rule,
        )

        rule = create_rule(
            identity_id="crud_test",
            name="CRUD Rule",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="notify",
            action_config={"notification_type": "automation_fired"},
        )
        rule_id = rule["id"]

        # Read
        fetched = get_rule(rule_id)
        assert fetched["name"] == "CRUD Rule"

        # Update
        updated = update_rule(rule_id=rule_id, name="Updated CRUD Rule")
        assert updated["name"] == "Updated CRUD Rule"

        # Toggle off
        toggled = toggle_rule(rule_id=rule_id, is_active=False)
        assert toggled["is_active"] is False

        # Toggle on
        toggled = toggle_rule(rule_id=rule_id, is_active=True)
        assert toggled["is_active"] is True

        # Delete
        deleted = delete_rule(rule_id)
        assert deleted is True
        assert get_rule(rule_id) is None

    def test_evaluate_triggers(self, app):
        """Trigger evaluation engine matches active rules and logs execution."""
        from app.automation.service import (
            create_rule, evaluate_triggers, get_execution_logs,
        )
        from app.automation.models import AutomationLog

        # Create a rule
        rule = create_rule(
            identity_id="eval_test",
            name="Evaluation Test",
            trigger_type="status_changed",
            trigger_config={"entity_type": "Task", "field": "status", "to": "completed"},
            action_type="notify",
            action_config={
                "notification_type": "automation_fired",
                "title": "Task completed: {object_name}",
                "body": "The task {object_name} has been completed.",
            },
        )

        # Evaluate triggers — should match our rule
        results = evaluate_triggers(
            trigger_type="status_changed",
            trigger_object_id="obj_123",
            trigger_summary="Task marked as completed",
            context={
                "object_type": "Task",
                "object_name": "My Task",
                "old_status": "in_progress",
                "new_status": "completed",
            },
        )
        assert len(results) >= 1, "No triggers matched — expected at least 1"
        matched = [r for r in results if r["rule_id"] == rule["id"]]
        assert len(matched) >= 1, f"Expected rule {rule['id']} to match"
        assert matched[0]["status"] == "success"

        # Verify execution log was created
        logs = get_execution_logs(rule_id=rule["id"])
        assert len(logs) >= 1
        assert logs[0]["rule_id"] == rule["id"]
        assert logs[0]["status"] == "success"

    def test_template_create(self, app):
        """Create a rule from a workflow template."""
        from app.automation.service import create_from_template, get_rule

        rule = create_from_template(
            identity_id="template_test",
            template_id="lead_qualified_notify",
        )
        assert rule is not None
        assert rule["name"] == "Lead Qualified → Notify Team"
        assert rule["trigger_type"] == "status_changed"
        assert rule["action_type"] == "notify"

        # Unknown template returns None
        assert create_from_template("t", "nonexistent") is None


# =============================================================================
# 5. HTTP Endpoints
# =============================================================================

class TestOutputsEndpoint:
    """Prove the /api/v1/execution/outputs endpoint is functional."""

    def test_outputs_endpoint_returns_200(self, app, client):
        """The endpoint returns a valid response with no data."""
        resp = client.get("/api/v1/execution/outputs?tenant_id=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]

    def test_outputs_endpoint_with_data(self, app, client):
        """After adding execution log entries, they appear in the output feed."""
        from app.execution_log.models import log_execution

        # Create an output event
        log_execution(
            object_id=100,
            event_type="output_generated",
            payload={
                "title": "B6 Test Output",
                "summary": "Output from B6 execution engine verification",
                "status": "completed",
                "source": "execution",
            },
        )
        db.session.flush()

        resp = client.get("/api/v1/execution/outputs?tenant_id=1")
        assert resp.status_code == 200
        data = resp.get_json()
        items = data["data"]["items"]
        exec_items = [i for i in items if i["type"] == "execution_result"]
        assert len(exec_items) >= 1
        assert any("B6 Test Output" in i["title"] for i in exec_items)

    def test_automation_routes_list(self, app, client):
        """Automation routes require auth, but the blueprint is registered."""
        resp = client.get("/api/v1/automation/rules")
        # Should be 401 (not authenticated) since routes require session auth
        # — proving the blueprint is registered and functional
        assert resp.status_code in (200, 401, 302)
        if resp.status_code == 200:
            data = resp.get_json()
            assert "data" in data or "success" in data


# =============================================================================
# 6. Context Module
# =============================================================================

class TestDecisionContext:
    """Prove the DecisionContext module is functional."""

    def test_decision_context_creation(self):
        from app.execution_engine.context import DecisionContext
        from datetime import datetime, timezone

        ctx = DecisionContext(
            state={"status": "new"},
            intent="test_execution",
            evidence={"source": "b6_test"},
        )
        assert ctx.state == {"status": "new"}
        assert ctx.intent == "test_execution"
        assert ctx.evidence == {"source": "b6_test"}
        assert ctx.has_intent() is True
        assert ctx.has_evidence() is True

    def test_decision_context_defaults(self):
        from app.execution_engine.context import DecisionContext

        ctx = DecisionContext()
        assert ctx.state == {}
        assert ctx.intent is None
        assert ctx.evidence is None
        assert ctx.has_intent() is False
        assert ctx.has_evidence() is False

    def test_decision_context_with_state(self):
        from app.execution_engine.context import DecisionContext

        ctx = DecisionContext(state={"a": 1})
        ctx2 = ctx.with_state({"a": 2, "b": 3})
        assert ctx.state == {"a": 1}  # original unchanged
        assert ctx2.state == {"a": 2, "b": 3}  # new state applied

    def test_decision_context_to_dict(self):
        from app.execution_engine.context import DecisionContext

        ctx = DecisionContext(state={"x": 1}, intent="test")
        d = ctx.to_dict()
        assert d["state"] == {"x": 1}
        assert d["intent"] == "test"
        assert "time" in d


# =============================================================================
# 7. TruthService
# =============================================================================

class TestTruthService:
    """Prove the TruthService module is functional."""

    def test_apply_truth(self, app):
        _ensure_tables()
        from app.execution_engine.truth import TruthService
        from app.objects.models import Object

        obj = Object(type="task", state={"status": "draft"}, tenant_id=1)
        db.session.add(obj)
        db.session.commit()

        TruthService.apply_truth(obj, {"status": "published", "version": 2})
        assert obj.state["status"] == "published"
        assert obj.state["version"] == 2


# =============================================================================
# 8. ExecutionService
# =============================================================================

class TestExecutionService:
    """Prove the ExecutionService (CRUD on Execution model) is functional."""

    def test_create_and_update_execution(self, app):
        _ensure_tables()
        from app.execution_engine.models import Execution
        from app.execution_engine.service import ExecutionService

        exe = ExecutionService.create_execution(object_id=555, decision="test_decision")
        assert exe.id is not None
        assert exe.object_id == 555
        assert exe.decision == "test_decision"
        assert exe.status == "pending"

        ExecutionService.update_status(exe, "completed")
        assert exe.status == "completed"
        fetched = db.session.get(Execution, exe.id)
        assert fetched.status == "completed"