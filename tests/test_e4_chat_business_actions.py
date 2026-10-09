"""E4 — the chat executes real business actions, confirmed and scoped.

A create-request in the chat must NOT silently write. Without an explicit
confirmation word in the SAME message, the reply is a truthful preview and
nothing is created. With it, the registered tool handler runs for real:
canonical store (rel_relationships for customers, suppliers for suppliers),
an Outcome is recorded, a canonical event is emitted, and the reply reports
exactly what happened — including truthful duplicates.
"""

import pytest


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


def _run_chat(message, org_id=7, identity_id="sid_e4_test"):
    from core.intelligence_runtime.integration import ask, ensure_runtime
    ensure_runtime()
    return ask(
        query=message,
        session_id="e4_test_session",
        identity_id=identity_id,
        tenant_id=str(org_id),
    )


class TestPlannerDetection:
    def test_detects_customer_create_with_confirmation(self):
        from core.intelligence_runtime.planner import ActionPlanner
        from core.intelligence_runtime.types import ActionType
        step = ActionPlanner().detect_business_action(
            "confirmed: create customer E4 Orion Foods")
        assert step is not None
        assert step.action == ActionType.CREATE_CUSTOMER
        assert step.parameters["name"] == "E4 Orion Foods"
        assert step.parameters["confirmed"] is True

    def test_detects_customer_create_without_confirmation(self):
        from core.intelligence_runtime.planner import ActionPlanner
        from core.intelligence_runtime.types import ActionType
        step = ActionPlanner().detect_business_action(
            "create a customer named E4 Blue Dunes")
        assert step is not None
        assert step.action == ActionType.CREATE_CUSTOMER
        assert step.parameters["name"] == "E4 Blue Dunes"
        assert step.parameters["confirmed"] is False

    def test_confirmation_word_trimmed_from_name(self):
        from core.intelligence_runtime.planner import ActionPlanner
        step = ActionPlanner().detect_business_action("create customer E4 Horizon, confirm")
        assert step is not None
        assert step.parameters["name"] == "E4 Horizon"

    def test_plain_question_is_not_a_business_action(self):
        from core.intelligence_runtime.planner import ActionPlanner
        assert ActionPlanner().detect_business_action(
            "how many customers do I have right now?") is None

    def test_supplier_detection(self):
        from core.intelligence_runtime.planner import ActionPlanner
        from core.intelligence_runtime.types import ActionType
        step = ActionPlanner().detect_business_action("add supplier E4 Saffron Traders")
        assert step is not None
        assert step.action == ActionType.CREATE_SUPPLIER
        assert step.parameters["name"] == "E4 Saffron Traders"


class TestChatExecutionGate:
    def test_unconfirmed_create_writes_nothing(self, app):
        from app.relationship.models import CanonicalRelationship
        res = _run_chat("create customer E4 Ghost Ventures")
        assert "Nothing has been created yet" in res["content"]
        assert CanonicalRelationship.query.filter_by(
            display_name="E4 Ghost Ventures").first() is None

    def test_confirmed_create_writes_canonical_relationship(self, app):
        from app.relationship.models import CanonicalRelationship
        res = _run_chat("confirmed: create customer E4 Sunrise Travels")
        assert "Created customer" in res["content"]
        rel = CanonicalRelationship.query.filter_by(
            display_name="E4 Sunrise Travels").first()
        assert rel is not None
        assert rel.relationship_type == "customer"
        assert rel.organization_id == 7

    def test_confirmed_create_records_outcome(self, app):
        """The outcome id REPORTED in the reply must exist in the ledger."""
        import re
        from app.execution.models import Outcome
        res = _run_chat("confirmed: create customer E4 Ledger Proof")
        assert "Created customer" in res["content"]
        m = re.search(r"outcome ([0-9A-Fa-f]+)", res["content"])
        assert m, res["content"]
        oid = m.group(1)
        assert Outcome.query.filter_by(outcome_id=oid).first() is not None

    def test_duplicate_refused_truthfully(self, app):
        from app.relationship.models import CanonicalRelationship
        _run_chat("confirmed: create customer E4 Same Name Co")
        res = _run_chat("confirmed: create customer E4 Same Name Co")
        assert "already exists" in res["content"]
        assert CanonicalRelationship.query.filter_by(
            display_name="E4 Same Name Co").count() == 1

    def test_confirmed_supplier_create(self, app):
        from app.models import Supplier
        res = _run_chat("confirm: add supplier E4 Fallback Supply")
        assert "Created supplier" in res["content"]
        s = Supplier.query.filter_by(tenant_id=7, name="E4 Fallback Supply").first()
        assert s is not None
