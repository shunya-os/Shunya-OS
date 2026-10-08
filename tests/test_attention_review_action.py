"""Attention review action — the M9 human-action contract.

POST /api/v1/attention/<id>/confirm-review persists the human decision
canonically (provenance.review_decision), emits the canonical decision event,
and resolves the item — with full tenant enforcement (404/403/409 truth).
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
        from app.models import Organization, OrgMember
        from app.authz.services import seed_default_roles

        for org_id, ident in ((401, "sid_reviewer_a"), (402, "sid_outsider_b")):
            org = Organization(id=org_id, name=f"Review Org {org_id}",
                               slug=f"review-org-{org_id}", is_active=True)
            db.session.add(org)
            db.session.flush()
            seed_default_roles(org_id)
            db.session.add(OrgMember(organization_id=org_id,
                                     identity_id=ident, role="owner",
                                     is_active=True))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()
    stop_attention_subscriber()


def _make_review_item(app, ingestion_id="ing_rev_1", outcome="rejected"):
    from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus
    from app.attention.models import AttentionItem, AttentionSource

    event = CanonicalEvent(
        event_type="ingestion:csv",
        tenant_id=401,
        actor_id="sid_reviewer_a",
        actor_type="ingestion",
        object_id=ingestion_id,
        object_type="ingestion",
        payload={"ingestion_id": ingestion_id, "source_type": "csv",
                 "outcome": outcome, "confidence_unknown": False},
    )
    with app.app_context():
        get_event_bus().publish(event)
        item = AttentionItem.query.filter_by(
            organization_id=401, source=AttentionSource.EVENT.value,
            related_object_id=ingestion_id).first()
        assert item is not None
        return item.id


def _session(client, ident, org_id):
    with client.session_transaction() as sess:
        sess["identity_id"] = ident
        sess["user_id"] = ident
        sess["current_org_id"] = org_id


def test_confirm_review_persists_decision_and_resolves(app):
    item_id = _make_review_item(app)
    client = app.test_client()
    _session(client, "sid_reviewer_a", 401)

    resp = client.post(f"/api/v1/attention/{item_id}/confirm-review",
                       json={"note": "checked against source"})
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()["data"]
    assert data["state"] == "resolved"
    decision = data["provenance"]["review_decision"]
    assert decision["decision"] == "confirmed"
    assert decision["decided_by"] == "sid_reviewer_a"
    assert decision["note"] == "checked against source"
    assert decision["source_event_id"]

    # Active list no longer contains it; the item remains auditable.
    resp = client.get("/api/v1/attention/")
    active_ids = [i["id"] for i in resp.get_json()["data"]]
    assert item_id not in active_ids
    resp = client.get(f"/api/v1/attention/{item_id}")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["state"] == "resolved"
    assert resp.get_json()["data"]["provenance"]["review_decision"]["decision"] == "confirmed"


def test_confirm_review_anonymous_refused(app):
    item_id = _make_review_item(app)
    client = app.test_client()
    resp = client.post(f"/api/v1/attention/{item_id}/confirm-review", json={})
    assert resp.status_code in (401, 403), resp.status_code


def test_confirm_review_wrong_tenant_refused_with_detail(app):
    item_id = _make_review_item(app)
    client = app.test_client()
    _session(client, "sid_outsider_b", 402)
    resp = client.post(f"/api/v1/attention/{item_id}/confirm-review", json={})
    assert resp.status_code == 403, resp.status_code
    assert "different organization" in resp.get_json()["detail"]


def test_confirm_review_already_resolved_conflict(app):
    item_id = _make_review_item(app)
    client = app.test_client()
    _session(client, "sid_reviewer_a", 401)
    ok = client.post(f"/api/v1/attention/{item_id}/confirm-review", json={})
    assert ok.status_code == 200
    again = client.post(f"/api/v1/attention/{item_id}/confirm-review", json={})
    assert again.status_code == 409, again.status_code
    assert "active" in again.get_json()["detail"]


def test_confirm_review_non_event_item_conflict(app):
    from app.attention.service import create_attention_item
    with app.app_context():
        item = create_attention_item(identity_id="sid_reviewer_a",
                                     organization_id=401,
                                     source="intention.engine",
                                     reason="engine item")
        item_id = item.id
    client = app.test_client()
    _session(client, "sid_reviewer_a", 401)
    resp = client.post(f"/api/v1/attention/{item_id}/confirm-review", json={})
    assert resp.status_code == 409, resp.status_code
    assert "not a reviewable" in resp.get_json()["detail"]
