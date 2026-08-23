"""
Tests for SHUNYA Autonomous Organization Runtime — Phase Z7.

Validates: Actor model, Responsibility graph, Delegation,
Capacity computation, Escalation, Coordination sessions,
Inspection chain, Business agnosticism.
"""

import pytest


@pytest.fixture(autouse=True)
def _app_context(app):
    """Provide Flask app context for tests that access DB."""
    pass
from app.organization.actor import (
    Actor, ActorCapability, CapacityStatus, get_store, reset_store,
)
from app.organization.responsibility import (
    Responsibility, Delegation, DelegationStatus, ResponsibilityGraph,
    get_graph, reset_graph,
)
from app.organization.escalation import (
    EscalationRule, EscalationEvent, EscalationEngine, get_engine, reset_engine,
)
from app.organization.coordination import (
    CoordinationSession, SessionStatus, get_store as get_coord_store,
    reset_store as reset_coord_store,
)


# ══════════════════════════════════════════════════════════════
# Actor Model Tests
# ══════════════════════════════════════════════════════════════


class TestActor:
    def test_actor_creation(self):
        a = Actor(actor_id="a1", name="Sarah", actor_type="human")
        assert a.actor_id == "a1"
        assert a.actor_type == "human"
        assert a.capacity_status == CapacityStatus.IDLE

    def test_actor_type_flexibility(self):
        for t in ["human", "ai_agent", "team", "department", "vendor", "api", "robot"]:
            a = Actor(actor_id=f"a_{t}", name=f"Test {t}", actor_type=t)
            assert a.actor_type == t

    def test_capacity_ratio(self):
        a = Actor(actor_id="a1", name="T", actor_type="human", max_concurrent_responsibilities=5, current_responsibilities=2)
        assert a.capacity_ratio == 0.4
        assert a.can_accept_responsibility

    def test_capacity_full(self):
        a = Actor(actor_id="a1", name="T", actor_type="human", max_concurrent_responsibilities=3, current_responsibilities=3)
        assert a.capacity_ratio == 1.0
        assert not a.can_accept_responsibility
        assert a.capacity_status == CapacityStatus.OVERLOADED

    def test_assign_release_responsibility(self):
        a = Actor(actor_id="a1", name="T", actor_type="human", max_concurrent_responsibilities=2)
        a.assign_responsibility()
        assert a.current_responsibilities == 1
        assert a.capacity_status == CapacityStatus.AVAILABLE
        a.assign_responsibility()
        assert a.current_responsibilities == 2
        assert a.capacity_status == CapacityStatus.OVERLOADED
        a.release_responsibility()
        assert a.current_responsibilities == 1

    def test_to_dict(self):
        a = Actor(actor_id="a1", name="Sarah", actor_type="human",
                  capabilities=[ActorCapability("c1", "Legal")])
        d = a.to_dict()
        assert d["actor_id"] == "a1"
        assert d["capabilities"] == ["Legal"]


class TestActorStore:
    def setup_method(self):
        reset_store()

    def test_add_and_get(self):
        store = get_store()
        store.add(Actor(actor_id="a1", name="T", actor_type="human"))
        assert store.get("a1") is not None
        assert store.count == 1

    def test_get_by_type(self):
        store = get_store()
        store.add(Actor(actor_id="a1", name="T", actor_type="human"))
        store.add(Actor(actor_id="a2", name="T", actor_type="ai_agent"))
        assert len(store.get_by_type("human")) == 1
        assert len(store.get_by_type("ai_agent")) == 1

    def test_get_available(self):
        store = get_store()
        store.add(Actor(actor_id="a1", name="T", actor_type="human", max_concurrent_responsibilities=2, current_responsibilities=0))
        store.add(Actor(actor_id="a2", name="T", actor_type="vendor", max_concurrent_responsibilities=1, current_responsibilities=1))
        assert len(store.get_available()) == 1


# ══════════════════════════════════════════════════════════════
# Responsibility Graph Tests
# ══════════════════════════════════════════════════════════════


class TestResponsibilityGraph:
    def setup_method(self):
        reset_graph()
        reset_store()

    def test_add_responsibility(self):
        graph = get_graph()
        resp = Responsibility(responsibility_id="r1", decision_id="d1", actor_id="a1", role="responsible")
        graph.add_responsibility(resp)
        assert graph.count == 1

    def test_resolve_chain(self):
        from app.organization.actor import get_store as get_actor_store
        store = get_actor_store()
        store.add(Actor(actor_id="a1", name="Sarah", actor_type="human"))
        store.add(Actor(actor_id="a2", name="Marcus", actor_type="human"))

        graph = get_graph()
        graph.add_responsibility(Responsibility(responsibility_id="r1", decision_id="d1", actor_id="a1", role="responsible"))
        graph.add_responsibility(Responsibility(responsibility_id="r2", decision_id="d1", actor_id="a2", role="supporting"))

        chain = graph.resolve_chain("d1")
        assert len(chain["responsible"]) == 1
        assert chain["responsible"][0]["actor_name"] == "Sarah"
        assert len(chain["supporting"]) == 1

    def test_delegation(self):
        graph = get_graph()
        d = Delegation(delegation_id="del1", decision_id="d1", delegator_id="a1", delegate_id="a2",
                       reason="Need legal review", authority_granted="Full authority")
        graph.add_delegation(d)
        assert graph.get_delegation("del1") is d
        assert len(graph.get_delegations_for_decision("d1")) == 1


# ══════════════════════════════════════════════════════════════
# Escalation Engine Tests
# ══════════════════════════════════════════════════════════════


class TestEscalation:
    def setup_method(self):
        reset_engine()
        reset_store()

    def test_add_rule(self):
        esc = get_engine()
        esc.add_rule(EscalationRule(rule_id="r1", name="Test", rule_type="time_based", condition_description="Test"))
        assert esc.count == 1

    def test_capacity_escalation(self):
        from app.organization.actor import get_store as get_actor_store
        store = get_actor_store()
        store.add(Actor(actor_id="a1", name="T", actor_type="human", max_concurrent_responsibilities=1, current_responsibilities=1))

        esc = get_engine()
        esc.add_rule(EscalationRule(rule_id="r1", name="Cap Esc", rule_type="capacity_based",
                                    condition_description="Escalate if overloaded",
                                    max_capacity_ratio=0.8))

        d = Delegation(delegation_id="del1", decision_id="d1", delegator_id="owner", delegate_id="a1")
        events = esc.evaluate_delegation(d)
        assert len(events) >= 1
        assert events[0].rule_id == "r1"


# ══════════════════════════════════════════════════════════════
# Coordination Session Tests
# ══════════════════════════════════════════════════════════════


class TestCoordination:
    def setup_method(self):
        reset_coord_store()

    def test_create_session(self):
        store = get_coord_store()
        s = CoordinationSession(session_id="s1", decision_id="d1", objective="Complete legal review")
        store.add(s)
        assert store.count == 1
        assert s.status == SessionStatus.ACTIVE

    def test_add_participant(self):
        s = CoordinationSession(session_id="s1", decision_id="d1", objective="Review")
        s.add_participant("a1")
        s.add_participant("a2")
        assert len(s.participant_ids) == 2

    def test_blocker(self):
        s = CoordinationSession(session_id="s1", decision_id="d1", objective="Review")
        s.add_blocker("Waiting for legal input")
        assert s.status == SessionStatus.BLOCKED
        s.resolve_blocker("Waiting for legal input")
        assert s.status == SessionStatus.ACTIVE

    def test_complete(self):
        s = CoordinationSession(session_id="s1", decision_id="d1", objective="Review")
        s.complete("Successfully completed")
        assert s.status == SessionStatus.COMPLETED
        assert s.completed_at is not None


# ══════════════════════════════════════════════════════════════
# Business Agnosticism Tests
# ══════════════════════════════════════════════════════════════


class TestBusinessAgnosticism:
    def test_actor_no_industry(self):
        a = Actor(actor_id="a1", name="T", actor_type="human")
        assert not hasattr(a, "employee_id")
        assert not hasattr(a, "department")
        assert not hasattr(a, "role")

    def test_responsibility_no_industry(self):
        r = Responsibility(responsibility_id="r1", decision_id="d1", actor_id="a1", role="responsible")
        assert not hasattr(r, "project")
        assert not hasattr(r, "task")

    def test_escalation_no_industry(self):
        rule = EscalationRule(rule_id="r1", name="T", rule_type="time_based", condition_description="T")
        assert not hasattr(rule, "team")
        assert not hasattr(rule, "region")


# ══════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════


class TestOrganizationIntegration:
    def test_org_loads_with_app(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            assert c.get('/health').status_code == 200
            # / route may return 200 (frontend built) or 503 (CI runs Python tests first)
            assert c.get('/').status_code in (200, 503)

            r = c.get('/workspace/?inspect_org=1')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert 'actors' in data
            assert 'responsibilities' in data
            assert 'delegations' in data
            assert 'escalations' in data
            assert 'coordination' in data

    def test_actors_loaded_on_startup(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            r = c.get('/workspace/?inspect_org=1')
            data = r.get_json()
            assert data['actors']['total'] >= 3