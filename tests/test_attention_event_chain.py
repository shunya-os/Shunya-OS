"""Attention event chain — canonical EventBus → persistent AttentionItem.

Proves the chain the runtime loop never produced:
    business event → EventBus.publish → attention subscriber → AttentionItem

with canonical-owner gating (no synthetic tenant, no invented watchers),
deduplication, and tenant isolation. The final test drives the REAL
IngestionService (the canonical producer) end-to-end.
"""
import pytest


@pytest.fixture(scope="function")
def app():
    from core.attention.subscriber import stop_attention_subscriber
    from app.shunya.infrastructure.event_bus import reset_event_bus

    stop_attention_subscriber()
    reset_event_bus()

    from app import create_app, db
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    stop_attention_subscriber()


def _publish(app, *, tenant_id, actor_id, ingestion_id,
             outcome="accepted", confidence_unknown=True,
             confidence=None, workspace_id=None):
    from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus

    event = CanonicalEvent(
        event_type="ingestion:csv",
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        actor_id=actor_id,
        actor_type="ingestion",
        actor_name="csv",
        object_id=ingestion_id,
        object_type="ingestion",
        payload={
            "ingestion_id": ingestion_id,
            "source_type": "csv",
            "outcome": outcome,
            "confidence_unknown": confidence_unknown,
            "confidence": confidence,
        },
        confidence=confidence if confidence is not None else 0.0,
    )
    with app.app_context():
        get_event_bus().publish(event)
    return event


def _items(app, org):
    from app.attention.service import list_active
    with app.app_context():
        return list_active(organization_id=org, limit=100)


def test_review_needed_event_creates_attention_item(app):
    _publish(app, tenant_id=401, actor_id="sid_actor_a",
             ingestion_id="ing_a1")
    items = _items(app, 401)
    assert len(items) == 1
    item = items[0]
    assert item.source == "event"
    assert item.organization_id == 401
    assert item.identity_id == "sid_actor_a"
    assert item.related_object_type == "ingestion"
    assert item.related_object_id == "ing_a1"
    assert item.state == "active"
    assert item.priority == 3
    assert item.provenance.get("method") == "attention_event_subscriber"
    assert item.provenance.get("event_type") == "ingestion:csv"


def test_rejected_outcome_is_priority_four(app):
    _publish(app, tenant_id=401, actor_id="sid_actor_a",
             ingestion_id="ing_rej", outcome="rejected")
    items = _items(app, 401)
    assert len(items) == 1
    assert items[0].priority == 4
    assert "rejected" in items[0].reason.lower()


def test_duplicate_event_for_same_ingestion_deduplicated(app):
    _publish(app, tenant_id=401, actor_id="sid_actor_a", ingestion_id="ing_dup")
    # A second, NEW event (different event_id) for the same ingestion object
    _publish(app, tenant_id=401, actor_id="sid_actor_a", ingestion_id="ing_dup")
    assert len(_items(app, 401)) == 1


def test_event_without_tenant_is_skipped(app):
    _publish(app, tenant_id=None, actor_id="sid_actor_a",
             ingestion_id="ing_no_tenant")
    assert len(_items(app, 401)) == 0


def test_event_without_actor_is_skipped(app):
    _publish(app, tenant_id=401, actor_id="", ingestion_id="ing_no_actor")
    assert len(_items(app, 401)) == 0


def test_non_review_event_creates_nothing(app):
    _publish(app, tenant_id=401, actor_id="sid_actor_a",
             ingestion_id="ing_clean", confidence_unknown=False,
             confidence=0.9)
    assert len(_items(app, 401)) == 0


def test_attention_is_tenant_isolated(app):
    _publish(app, tenant_id=401, actor_id="sid_actor_a", ingestion_id="ing_t1")
    _publish(app, tenant_id=402, actor_id="sid_actor_b", ingestion_id="ing_t2")
    a_items = _items(app, 401)
    b_items = _items(app, 402)
    assert [i.related_object_id for i in a_items] == ["ing_t1"]
    assert [i.related_object_id for i in b_items] == ["ing_t2"]


def test_real_ingestion_service_produces_attention(app):
    """End-to-end: the canonical producer drives the whole chain."""
    from core.ingestion import IngestionRecord, InformationClass, SourceType
    from core.ingestion.service import IngestionService

    with app.app_context():
        record = IngestionRecord(
            ingestion_id="ing_e2e_1",
            tenant_id=401,
            source=SourceType.CSV,
            source_identity="sid_actor_a",
            normalized_payload={"name": "Alice", "email": "alice@example.com"},
            information_class=InformationClass.USER_PROVIDED,
        )
        result = IngestionService().process(record)

    assert result.outcome.value == "accepted"
    assert result.canonical_event_id, "canonical event must be published"

    items = _items(app, 401)
    assert len(items) == 1
    assert items[0].related_object_id == "ing_e2e_1"
    assert items[0].identity_id == "sid_actor_a"


def test_attention_persistence_failure_never_breaks_ingestion(app, monkeypatch):
    """Failure matrix: if attention persistence fails, ingestion still succeeds,
    the failure is not silent (logged), and the next event recovers."""
    from core.ingestion import IngestionRecord, InformationClass, SourceType
    from core.ingestion.service import IngestionService

    def broken_create(**kwargs):
        raise RuntimeError("simulated attention persistence failure")

    # The subscriber imports create_attention_item inside the handler, so this
    # patch is picked up at delivery time.
    monkeypatch.setattr(
        "app.attention.service.create_attention_item", broken_create)

    with app.app_context():
        result = IngestionService().process(IngestionRecord(
            ingestion_id="ing_fail_1",
            tenant_id=401,
            source=SourceType.CSV,
            source_identity="sid_actor_a",
            normalized_payload={"name": "FailPath"},
            information_class=InformationClass.USER_PROVIDED,
        ))
    # Ingestion is unaffected by the attention failure and the event is
    # still published (the handler logs the error and never raises).
    assert result.outcome.value == "accepted"
    assert result.canonical_event_id, "event still published"

    # Recovery: once persistence works again, a NEW event creates its item.
    monkeypatch.undo()
    with app.app_context():
        IngestionService().process(IngestionRecord(
            ingestion_id="ing_fail_2",
            tenant_id=401,
            source=SourceType.CSV,
            source_identity="sid_actor_a",
            normalized_payload={"name": "RecoverPath"},
            information_class=InformationClass.USER_PROVIDED,
        ))
    items = _items(app, 401)
    assert [i.related_object_id for i in items] == ["ing_fail_2"]
