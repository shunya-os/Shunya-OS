"""Pytest tests for UBME 2B.5 — Event Bus, Actions, Dashboards, Templates."""

import json
import os
import pytest

# ── Event Bus Tests ────────────────────────────────────────────────


class TestEventBus:
    def test_basic_subscribe_and_emit(self):
        from app.ubme.events import EventType, EventBus
        bus = EventBus()
        events = []
        bus.subscribe(EventType.OBJECT_CREATED, lambda e: events.append(e))
        bus.emit(EventType.OBJECT_CREATED, module_key="test", object_type="widget", instance_id="123")
        assert len(events) == 1
        assert events[0]["type"] == "object.created"
        assert events[0]["module_key"] == "test"

    def test_wildcard_subscriber(self):
        from app.ubme.events import EventType, EventBus
        bus = EventBus()
        all_events = []
        bus.subscribe_all(lambda e: all_events.append(e))
        bus.emit(EventType.OBJECT_CREATED, key="v1")
        bus.emit(EventType.OBJECT_UPDATED, key="v2")
        assert len(all_events) == 2

    def test_subscribe_only_specific_type(self):
        from app.ubme.events import EventType, EventBus
        bus = EventBus()
        created = []
        bus.subscribe(EventType.OBJECT_CREATED, lambda e: created.append(e))
        bus.emit(EventType.OBJECT_UPDATED, key="v1")
        assert len(created) == 0
        bus.emit(EventType.OBJECT_CREATED, key="v2")
        assert len(created) == 1

    def test_unsubscribe(self):
        from app.ubme.events import EventType, EventBus
        bus = EventBus()
        events = []
        def handler(e): events.append(e)
        bus.subscribe(EventType.OBJECT_CREATED, handler)
        bus.emit(EventType.OBJECT_CREATED, key="1")
        assert len(events) == 1
        bus.unsubscribe(EventType.OBJECT_CREATED, handler)
        bus.emit(EventType.OBJECT_CREATED, key="2")
        assert len(events) == 1  # no new event

    def test_singleton(self):
        from app.ubme.events import get_bus, reset_bus
        reset_bus()
        b1 = get_bus()
        b2 = get_bus()
        assert b1 is b2
        reset_bus()
        b3 = get_bus()
        assert b3 is not b1

    def test_handler_exception_does_not_crash_bus(self):
        from app.ubme.events import EventType, EventBus
        bus = EventBus()
        def failing(e): raise ValueError("oops")
        ok = []
        bus.subscribe(EventType.OBJECT_CREATED, failing)
        bus.subscribe(EventType.OBJECT_CREATED, lambda e: ok.append(e))
        bus.emit(EventType.OBJECT_CREATED, key="test")
        assert len(ok) == 1  # second handler still ran

    def test_clear_removes_all_subscribers(self):
        from app.ubme.events import EventType, EventBus
        bus = EventBus()
        events = []
        bus.subscribe(EventType.OBJECT_CREATED, lambda e: events.append(e))
        bus.clear()
        bus.emit(EventType.OBJECT_CREATED, key="test")
        assert len(events) == 0


# ── ActionDef & DashboardCard Model Tests ─────────────────────────


class TestActionModel:
    def test_actiondef_creation(self):
        from app.ubme.models import ActionDef
        a = ActionDef(key="confirm", label="Confirm", icon="✅", requires_confirmation=True)
        assert a.key == "confirm"
        assert a.label == "Confirm"
        assert a.requires_confirmation is True

    def test_actiondef_serialization(self):
        from app.ubme.models import ActionDef
        a = ActionDef(key="send", label="Send", icon="📧", endpoint="/send", method="POST")
        d = a.to_dict()
        assert d["key"] == "send"
        assert d["endpoint"] == "/send"
        a2 = ActionDef.from_dict(d)
        assert a2.key == "send"

    def test_dashboardcard_creation(self):
        from app.ubme.models import DashboardCard
        c = DashboardCard(key="count_active", label="Active", card_type="count", object_type="booking", filter_criteria="status == 'confirmed'")
        assert c.card_type == "count"
        assert c.filter_criteria == "status == 'confirmed'"

    def test_dashboardcard_serialization(self):
        from app.ubme.models import DashboardCard
        c = DashboardCard(key="revenue", label="Revenue", card_type="sum", object_type="payment", field="amount")
        d = c.to_dict()
        assert d["card_type"] == "sum"
        c2 = DashboardCard.from_dict(d)
        assert c2.field == "amount"


# ── ObjectTypeDef with Actions Tests ──────────────────────────────


class TestObjectTypeWithActions:
    def test_object_type_with_actions(self):
        from app.ubme.models import ObjectTypeDef, FieldDef, FieldType, ActionDef
        ot = ObjectTypeDef(
            key="task", name="Task",
            fields=[FieldDef(key="name", label="Name", field_type=FieldType.TEXT)],
            actions=[ActionDef(key="complete", label="Complete", icon="✅")]
        )
        d = ot.to_dict()
        assert len(d["actions"]) == 1
        assert d["actions"][0]["key"] == "complete"
        ot2 = ObjectTypeDef.from_dict(d)
        assert len(ot2.actions) == 1

    def test_module_with_dashboard_cards(self):
        from app.ubme.models import ModuleDef, DashboardCard
        cards = [
            DashboardCard(key="c1", label="Card 1", card_type="count", object_type="widget"),
            DashboardCard(key="c2", label="Card 2", card_type="sum", object_type="widget", field="price"),
        ]
        mod = ModuleDef(key="test", name="Test", dashboard_cards=cards)
        d = mod.to_dict()
        assert len(d["dashboard_cards"]) == 2
        mod2 = ModuleDef.from_dict(d)
        assert len(mod2.dashboard_cards) == 2
        assert mod2.dashboard_cards[0].key == "c1"


# ── Engine Event Integration Tests ────────────────────────────────


class TestEngineEvents:
    def test_create_emits_event(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.events import get_bus, reset_bus
        from app.ubme.models import ModuleDef, ObjectTypeDef, FieldDef, FieldType
        reset_bus()
        ubme_engine.reset()
        module = ModuleDef(key="test", name="Test", object_types=[
            ObjectTypeDef(key="widget", name="Widget", fields=[
                FieldDef(key="name", label="Name", field_type=FieldType.TEXT),
            ])
        ])
        ubme_engine.register_module(module)
        events = []
        get_bus().subscribe_all(lambda e: events.append(e))
        inst = ubme_engine.create_instance("test", "widget", {"name": "A"})
        assert inst is not None
        assert any(e["type"] == "object.created" for e in events)
        reset_bus()

    def test_update_emits_event(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.events import get_bus, reset_bus
        from app.ubme.models import ModuleDef, ObjectTypeDef, FieldDef, FieldType
        reset_bus()
        ubme_engine.reset()
        module = ModuleDef(key="test", name="Test", object_types=[
            ObjectTypeDef(key="widget", name="Widget", fields=[
                FieldDef(key="name", label="Name", field_type=FieldType.TEXT),
            ])
        ])
        ubme_engine.register_module(module)
        inst = ubme_engine.create_instance("test", "widget", {"name": "A"})
        events = []
        get_bus().subscribe_all(lambda e: events.append(e))
        ubme_engine.update_instance("test", "widget", inst["id"], {"name": "B"})
        assert any(e["type"] == "object.updated" for e in events)
        reset_bus()

    def test_delete_emits_event(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.events import get_bus, reset_bus
        from app.ubme.models import ModuleDef, ObjectTypeDef, FieldDef, FieldType
        reset_bus()
        ubme_engine.reset()
        module = ModuleDef(key="test", name="Test", object_types=[
            ObjectTypeDef(key="widget", name="Widget", fields=[
                FieldDef(key="name", label="Name", field_type=FieldType.TEXT),
            ])
        ])
        ubme_engine.register_module(module)
        inst = ubme_engine.create_instance("test", "widget", {"name": "A"})
        events = []
        get_bus().subscribe_all(lambda e: events.append(e))
        ubme_engine.delete_instance("test", "widget", inst["id"])
        assert any(e["type"] == "object.deleted" for e in events)
        reset_bus()


# ── Dashboard Resolution Tests ────────────────────────────────────


class TestDashboardResolution:
    def test_count_card(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.models import ModuleDef, ObjectTypeDef, FieldDef, FieldType, DashboardCard
        from app.ubme.routes import _resolve_dashboard_card
        ubme_engine.reset()
        module = ModuleDef(key="test", name="Test", object_types=[
            ObjectTypeDef(key="task", name="Task", fields=[
                FieldDef(key="name", label="Name", field_type=FieldType.TEXT),
                FieldDef(key="status", label="Status", field_type=FieldType.SELECT, options=["open", "closed"]),
            ])
        ])
        ubme_engine.register_module(module)
        ubme_engine.create_instance("test", "task", {"name": "A", "status": "open"})
        ubme_engine.create_instance("test", "task", {"name": "B", "status": "closed"})
        ubme_engine.create_instance("test", "task", {"name": "C", "status": "open"})
        card = DashboardCard(key="open_tasks", label="Open Tasks", card_type="count", object_type="task", filter_criteria="status == 'open'")
        result = _resolve_dashboard_card(card, "test")
        assert result["value"] == 2

    def test_sum_card(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.models import ModuleDef, ObjectTypeDef, FieldDef, FieldType, DashboardCard
        from app.ubme.routes import _resolve_dashboard_card
        ubme_engine.reset()
        module = ModuleDef(key="test", name="Test", object_types=[
            ObjectTypeDef(key="invoice", name="Invoice", fields=[
                FieldDef(key="amount", label="Amount", field_type=FieldType.CURRENCY),
            ])
        ])
        ubme_engine.register_module(module)
        ubme_engine.create_instance("test", "invoice", {"amount": 100.50})
        ubme_engine.create_instance("test", "invoice", {"amount": 249.50})
        card = DashboardCard(key="total", label="Total", card_type="sum", object_type="invoice", field="amount")
        result = _resolve_dashboard_card(card, "test")
        assert result["value"] == 350.0

    def test_recent_card(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.models import ModuleDef, ObjectTypeDef, FieldDef, FieldType, DashboardCard
        from app.ubme.routes import _resolve_dashboard_card
        ubme_engine.reset()
        module = ModuleDef(key="test", name="Test", object_types=[
            ObjectTypeDef(key="lead", name="Lead", fields=[
                FieldDef(key="name", label="Name", field_type=FieldType.TEXT),
            ])
        ])
        ubme_engine.register_module(module)
        n1 = ubme_engine.create_instance("test", "lead", {"name": "Alpha"})["name"]
        n2 = ubme_engine.create_instance("test", "lead", {"name": "Beta"})["name"]
        card = DashboardCard(key="recent", label="Recent Leads", card_type="recent", object_type="lead")
        result = _resolve_dashboard_card(card, "test")
        assert len(result["value"]) == 2
        assert result["value"][0]["name"] == "Beta"  # most recent first

    def test_alert_card(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.models import ModuleDef, ObjectTypeDef, FieldDef, FieldType, DashboardCard
        from app.ubme.routes import _resolve_dashboard_card
        ubme_engine.reset()
        module = ModuleDef(key="test", name="Test", object_types=[
            ObjectTypeDef(key="task", name="Task", fields=[
                FieldDef(key="status", label="Status", field_type=FieldType.SELECT, options=["active", "overdue"]),
            ])
        ])
        ubme_engine.register_module(module)
        ubme_engine.create_instance("test", "task", {"status": "overdue"})
        ubme_engine.create_instance("test", "task", {"status": "active"})
        card = DashboardCard(key="alerts", label="Overdue Tasks", card_type="alert", object_type="task", filter_criteria="status == 'overdue'")
        result = _resolve_dashboard_card(card, "test")
        assert result["value"] == 1


# ── Template Loading Tests ─────────────────────────────────────────


class TestTemplates:
    def test_travel_template_loads(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.routes import _load_builtin_templates
        ubme_engine.reset()
        _load_builtin_templates()
        templates = ubme_engine.list_templates()
        template_ids = [t.id for t in templates]
        assert "travel" in template_ids
        assert "medical" in template_ids

    def test_travel_template_has_actions(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.routes import _load_builtin_templates
        ubme_engine.reset()
        _load_builtin_templates()
        template = next(t for t in ubme_engine.list_templates() if t.id == "travel")
        mod = template.module
        total_actions = sum(len(ot.actions or []) for ot in (mod.object_types or []))
        assert total_actions >= 15
        assert len(mod.dashboard_cards or []) >= 3

    def test_medical_template_has_actions_and_dashboard(self):
        from app.ubme import engine as ubme_engine
        from app.ubme.routes import _load_builtin_templates
        ubme_engine.reset()
        _load_builtin_templates()
        template = next(t for t in ubme_engine.list_templates() if t.id == "medical")
        mod = template.module
        total_actions = sum(len(ot.actions or []) for ot in (mod.object_types or []))
        assert total_actions >= 15
        assert len(mod.dashboard_cards or []) >= 3


# ── Blueprint Route Registration Tests ────────────────────────────


class TestBlueprint:
    def test_ubme_blueprint_registered(self):
        from app import create_app
        app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        rules = [r.rule for r in app.url_map.iter_rules() if "ubme" in r.rule]
        assert any("actions" in r for r in rules), "No actions route"
        assert any("dashboard" in r for r in rules), "No dashboard route"
        # Verify new routes exist
        assert "/api/ubme/actions/<object_type>" in rules
        assert "/api/ubme/dashboard/<module_key>" in rules