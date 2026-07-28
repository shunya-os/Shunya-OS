"""Tests for Milestone 7 — Automation.

Covers:
- Rule CRUD (create, read, update, delete, toggle)
- Trigger evaluation engine (entity_created, status_changed)
- Action execution (notify, create_object)
- Execution logging
- Workflow template creation
- API endpoints
- Regression tests for M1–M6
"""
from __future__ import annotations

from app.automation.service import (
    create_from_template,
    create_rule,
    delete_rule,
    evaluate_triggers,
    get_execution_logs,
    get_rule,
    get_rules,
    get_workflow_templates,
    toggle_rule,
    update_rule,
)
from app.automation.models import WORKFLOW_TEMPLATES


def _make_identity(app):
    from app.adapters.os_adapter import sign_in
    result = sign_in(email="m7@shunyaos.com", name="M7 Test")
    assert result["success"]
    return result["identity_id"]


# ===========================================================================
# 1. Rule CRUD
# ===========================================================================

class TestRuleCRUD:
    """Automation rule creation, retrieval, update, deletion."""

    def test_create_rule(self, app):
        identity_id = _make_identity(app)
        result = create_rule(
            identity_id=identity_id,
            name="Test Rule",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="notify",
            action_config={"notification_type": "automation_fired", "title": "Lead created"},
        )
        assert result["name"] == "Test Rule"
        assert result["trigger_type"] == "entity_created"
        assert result["is_active"] is True
        assert result["id"] > 0

    def test_get_rules(self, app):
        identity_id = _make_identity(app)
        create_rule(identity_id=identity_id, name="R1", trigger_type="entity_created",
                     trigger_config={}, action_type="notify", action_config={})
        create_rule(identity_id=identity_id, name="R2", trigger_type="status_changed",
                     trigger_config={}, action_type="notify", action_config={})
        rules = get_rules(identity_id=identity_id)
        assert len(rules) == 2

    def test_get_rules_excludes_inactive(self, app):
        identity_id = _make_identity(app)
        r = create_rule(identity_id=identity_id, name="Active", trigger_type="entity_created",
                         trigger_config={}, action_type="notify", action_config={})
        toggle_rule(rule_id=r["id"], is_active=False)
        rules = get_rules(identity_id=identity_id)
        assert len(rules) == 0
        rules_all = get_rules(identity_id=identity_id, include_inactive=True)
        assert len(rules_all) == 1

    def test_get_rule(self, app):
        identity_id = _make_identity(app)
        created = create_rule(identity_id=identity_id, name="Get Me", trigger_type="entity_created",
                              trigger_config={}, action_type="notify", action_config={})
        fetched = get_rule(rule_id=created["id"])
        assert fetched is not None
        assert fetched["name"] == "Get Me"

    def test_get_rule_not_found(self, app):
        assert get_rule(rule_id=99999) is None

    def test_update_rule(self, app):
        identity_id = _make_identity(app)
        r = create_rule(identity_id=identity_id, name="Original", trigger_type="entity_created",
                         trigger_config={}, action_type="notify", action_config={})
        updated = update_rule(rule_id=r["id"], name="Updated Name", description="New desc")
        assert updated["name"] == "Updated Name"
        assert updated["description"] == "New desc"

    def test_toggle_rule(self, app):
        identity_id = _make_identity(app)
        r = create_rule(identity_id=identity_id, name="Togglable", trigger_type="entity_created",
                         trigger_config={}, action_type="notify", action_config={})
        assert r["is_active"] is True
        toggled = toggle_rule(rule_id=r["id"], is_active=False)
        assert toggled["is_active"] is False
        toggled_back = toggle_rule(rule_id=r["id"], is_active=True)
        assert toggled_back["is_active"] is True

    def test_delete_rule(self, app):
        identity_id = _make_identity(app)
        r = create_rule(identity_id=identity_id, name="Delete Me", trigger_type="entity_created",
                         trigger_config={}, action_type="notify", action_config={})
        assert delete_rule(rule_id=r["id"]) is True
        assert get_rule(rule_id=r["id"]) is None

    def test_delete_nonexistent(self, app):
        assert delete_rule(rule_id=99999) is False


# ===========================================================================
# 2. Trigger Evaluation Engine
# ===========================================================================

class TestTriggerEngine:
    """Trigger evaluation and action execution."""

    def test_evaluate_entity_created_trigger(self, app):
        identity_id = _make_identity(app)
        create_rule(
            identity_id=identity_id,
            name="Lead Created",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="notify",
            action_config={"notification_type": "automation_fired", "title": "Lead created: {object_name}"},
        )
        results = evaluate_triggers(
            trigger_type="entity_created",
            trigger_object_id="lead_001",
            trigger_summary="New lead created",
            context={"object_type": "Lead", "object_name": "Acme Corp"},
        )
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert "notification" in results[0].get("action_summary", "").lower()

    def test_evaluate_entity_type_mismatch(self, app):
        identity_id = _make_identity(app)
        create_rule(
            identity_id=identity_id,
            name="Lead Only",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="notify",
            action_config={},
        )
        # Trigger with wrong entity type
        results = evaluate_triggers(
            trigger_type="entity_created",
            trigger_object_id="task_001",
            trigger_summary="Task created",
            context={"object_type": "Task", "object_name": "Some Task"},
        )
        assert len(results) == 0

    def test_evaluate_status_changed_match(self, app):
        identity_id = _make_identity(app)
        create_rule(
            identity_id=identity_id,
            name="Lead Qualified",
            trigger_type="status_changed",
            trigger_config={"entity_type": "Lead", "to": "qualified"},
            action_type="notify",
            action_config={"notification_type": "automation_fired", "title": "Lead qualified"},
        )
        results = evaluate_triggers(
            trigger_type="status_changed",
            trigger_object_id="lead_002",
            trigger_summary="Lead status changed",
            context={"object_type": "Lead", "old_status": "new", "new_status": "qualified"},
        )
        assert len(results) == 1

    def test_evaluate_status_changed_no_match(self, app):
        identity_id = _make_identity(app)
        create_rule(
            identity_id=identity_id,
            name="Only Qualified",
            trigger_type="status_changed",
            trigger_config={"entity_type": "Lead", "to": "qualified"},
            action_type="notify",
            action_config={},
        )
        results = evaluate_triggers(
            trigger_type="status_changed",
            trigger_object_id="lead_003",
            trigger_summary="Lead cancelled",
            context={"object_type": "Lead", "old_status": "new", "new_status": "cancelled"},
        )
        assert len(results) == 0

    def test_create_object_action(self, app):
        from app.founder.models import FounderSpace
        from app import db
        identity_id = _make_identity(app)
        # Need a space for object creation
        space = FounderSpace(space_id="m7_spc", name="M7 Space", identity_id=identity_id)
        db.session.add(space)
        db.session.commit()

        create_rule(
            identity_id=identity_id,
            name="Create Task on Lead",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="create_object",
            action_config={"object_type": "Task", "name": "Follow-up: {object_name}"},
        )
        results = evaluate_triggers(
            trigger_type="entity_created",
            trigger_object_id="lead_004",
            trigger_summary="Lead created",
            context={"object_type": "Lead", "object_name": "Test Corp"},
        )
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert "created" in results[0].get("action_summary", "").lower()

    def test_inactive_rule_not_evaluated(self, app):
        identity_id = _make_identity(app)
        r = create_rule(
            identity_id=identity_id,
            name="Inactive Rule",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="notify",
            action_config={},
        )
        toggle_rule(rule_id=r["id"], is_active=False)
        results = evaluate_triggers(
            trigger_type="entity_created",
            trigger_object_id="lead_005",
            trigger_summary="Lead created",
            context={"object_type": "Lead"},
        )
        assert len(results) == 0


# ===========================================================================
# 3. Execution Logging
# ===========================================================================

class TestExecutionLogs:
    """Automation execution history."""

    def test_execution_logged(self, app):
        identity_id = _make_identity(app)
        create_rule(
            identity_id=identity_id,
            name="Logged Rule",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="notify",
            action_config={"notification_type": "automation_fired", "title": "Test"},
        )
        evaluate_triggers(
            trigger_type="entity_created",
            trigger_object_id="lead_log",
            trigger_summary="Test lead",
            context={"object_type": "Lead", "object_name": "Log Corp"},
        )
        logs = get_execution_logs(identity_id=identity_id)
        assert len(logs) >= 1
        assert logs[0]["status"] == "success"

    def test_execution_log_includes_details(self, app):
        identity_id = _make_identity(app)
        create_rule(
            identity_id=identity_id,
            name="Detail Rule",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="notify",
            action_config={},
        )
        evaluate_triggers(
            trigger_type="entity_created",
            trigger_object_id="lead_detail",
            trigger_summary="Detailed test",
            context={"object_type": "Lead", "object_name": "Detail Corp"},
        )
        logs = get_execution_logs(identity_id=identity_id)
        assert len(logs) >= 1
        assert logs[0]["trigger_summary"] == "Detailed test"

    def test_execution_log_failures(self, app):
        identity_id = _make_identity(app)
        create_rule(
            identity_id=identity_id,
            name="Failing Rule",
            trigger_type="entity_created",
            trigger_config={"entity_type": "Lead"},
            action_type="create_object",
            action_config={"object_type": "Task", "name": "Test"},
        )
        # No space exists, so create_object will fail
        results = evaluate_triggers(
            trigger_type="entity_created",
            trigger_object_id="lead_fail",
            trigger_summary="Failing test",
            context={"object_type": "Lead", "object_name": "Fail Corp"},
        )
        # Should be logged as failure
        logs = get_execution_logs(identity_id=identity_id)
        failed = [l for l in logs if l["status"] == "failed"]
        assert len(failed) >= 1


# ===========================================================================
# 4. Workflow Templates
# ===========================================================================

class TestWorkflowTemplates:
    """Workflow template management."""

    def test_templates_available(self, app):
        templates = get_workflow_templates()
        assert len(templates) >= 3

    def test_templates_have_required_fields(self, app):
        templates = get_workflow_templates()
        for t in templates:
            assert t.get("id")
            assert t.get("name")
            assert t.get("trigger_type")
            assert t.get("action_type")
            assert t.get("trigger_config_template") is not None
            assert t.get("action_config_template") is not None

    def test_create_from_template(self, app):
        identity_id = _make_identity(app)
        result = create_from_template(identity_id=identity_id, template_id="lead_qualified_notify")
        assert result is not None
        assert result["trigger_type"] == "status_changed"
        assert result["action_type"] == "notify"

    def test_create_from_invalid_template(self, app):
        identity_id = _make_identity(app)
        result = create_from_template(identity_id=identity_id, template_id="nonexistent")
        assert result is None

    def test_create_from_template_with_overrides(self, app):
        identity_id = _make_identity(app)
        result = create_from_template(
            identity_id=identity_id,
            template_id="lead_qualified_notify",
            overrides={
                "action_config": {
                    "title": "Custom: {object_name} qualified",
                }
            },
        )
        assert result is not None
        import json
        action_cfg = json.loads(result["action_config"])
        assert action_cfg.get("title") == "Custom: {object_name} qualified"


# ===========================================================================
# 5. API Endpoints
# ===========================================================================

class TestAutomationAPI:
    """Automation API endpoints."""

    def _login(self, app, client, identity_id):
        with client.session_transaction() as sess:
            sess["identity_id"] = identity_id
            sess["user_id"] = identity_id

    def test_create_rule_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.post("/api/v1/automation/rules", json={
                "name": "API Rule",
                "trigger_type": "entity_created",
                "trigger_config": {"entity_type": "Lead"},
                "action_type": "notify",
                "action_config": {"notification_type": "automation_fired", "title": "Test"},
            })
            data = resp.get_json()
            assert data["success"]
            assert data["data"]["name"] == "API Rule"

    def test_list_rules_api(self, app):
        identity_id = _make_identity(app)
        create_rule(identity_id=identity_id, name="API List", trigger_type="entity_created",
                     trigger_config={}, action_type="notify", action_config={})
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.get("/api/v1/automation/rules")
            data = resp.get_json()
            assert data["success"]
            assert len(data["data"]) >= 1

    def test_get_rule_api(self, app):
        identity_id = _make_identity(app)
        r = create_rule(identity_id=identity_id, name="API Get", trigger_type="entity_created",
                         trigger_config={}, action_type="notify", action_config={})
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.get(f"/api/v1/automation/rules/{r['id']}")
            assert resp.get_json()["success"]

    def test_toggle_rule_api(self, app):
        identity_id = _make_identity(app)
        r = create_rule(identity_id=identity_id, name="API Toggle", trigger_type="entity_created",
                         trigger_config={}, action_type="notify", action_config={})
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.post(f"/api/v1/automation/rules/{r['id']}/toggle", json={"is_active": False})
            assert resp.get_json()["success"]
            assert resp.get_json()["data"]["is_active"] is False

    def test_delete_rule_api(self, app):
        identity_id = _make_identity(app)
        r = create_rule(identity_id=identity_id, name="API Delete", trigger_type="entity_created",
                         trigger_config={}, action_type="notify", action_config={})
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.delete(f"/api/v1/automation/rules/{r['id']}")
            assert resp.get_json()["success"] is True

    def test_trigger_api(self, app):
        identity_id = _make_identity(app)
        create_rule(identity_id=identity_id, name="API Trigger", trigger_type="entity_created",
                     trigger_config={"entity_type": "Lead"},
                     action_type="notify", action_config={"notification_type": "automation_fired", "title": "T"})
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.post("/api/v1/automation/trigger", json={
                "trigger_type": "entity_created",
                "trigger_object_id": "api_lead",
                "trigger_summary": "API trigger",
                "context": {"object_type": "Lead", "object_name": "API Corp"},
            })
            data = resp.get_json()
            assert data["success"]
            assert data["data"]["matched"] >= 1

    def test_templates_api(self, app):
        with app.test_client() as client:
            resp = client.get("/api/v1/automation/templates")
            data = resp.get_json()
            assert data["success"]
            assert len(data["data"]) >= 3

    def test_create_from_template_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.post("/api/v1/automation/templates/lead_qualified_notify/create")
            data = resp.get_json()
            assert data["success"]

    def test_api_requires_auth(self, app):
        with app.test_client() as client:
            resp = client.get("/api/v1/automation/rules")
            assert resp.status_code == 401

    def test_logs_api(self, app):
        identity_id = _make_identity(app)
        create_rule(identity_id=identity_id, name="Log API", trigger_type="entity_created",
                     trigger_config={"entity_type": "Lead"},
                     action_type="notify", action_config={})
        evaluate_triggers(trigger_type="entity_created", trigger_object_id="log_api",
                          trigger_summary="Log test", context={"object_type": "Lead", "object_name": "L"})
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.get("/api/v1/automation/logs")
            data = resp.get_json()
            assert data["success"]


# ===========================================================================
# 6. Regression — Milestones 1–6
# ===========================================================================

class TestMilestoneRegression:
    """All prior milestones still pass."""

    def test_m1_signin(self, app):
        from app.adapters.os_adapter import sign_in
        result = sign_in(email="m7-reg@test.com", name="M7 Reg")
        assert result["success"]

    def test_m2_executive_home(self, app):
        from app.adapters.os_adapter import get_executive_home
        identity_id = _make_identity(app)
        result = get_executive_home(identity_id=identity_id)
        assert result["success"]

    def test_m3_insights(self, app):
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        result = build_insights(identity_id=identity_id)
        assert "summary" in result

    def test_m4_workspace(self, app):
        from app.founder.workspace_intelligence import build_workspace_summary
        from app.founder.models import FounderObject, FounderSpace
        from app import db
        identity_id = _make_identity(app)
        space = FounderSpace(space_id="m7r_spc", name="M7R", identity_id=identity_id)
        db.session.add(space)
        db.session.flush()
        obj = FounderObject(object_id="m7r_obj", space_id="m7r_spc", name="M7Reg",
                            object_type="Document", created_by=identity_id)
        db.session.add(obj)
        db.session.commit()
        result = build_workspace_summary("m7r_obj")
        assert result["name"] == "M7Reg"

    def test_m5_ai_copilot(self, app):
        from app.ai.copilot import copilot_health
        health = copilot_health()
        assert "provider" in health

    def test_m6_notifications(self, app):
        from app.integration.service import create_notification, get_notifications
        identity_id = _make_identity(app)
        create_notification(identity_id=identity_id, notification_type="test", title="M7 Reg")
        notifs = get_notifications(identity_id=identity_id)
        assert len(notifs) >= 1

    def test_m6_integrations(self, app):
        from app.integration.service import save_connection, get_connections
        identity_id = _make_identity(app)
        save_connection(identity_id=identity_id, provider="gmail", access_token="reg")
        conns = get_connections(identity_id=identity_id)
        assert len(conns) >= 1