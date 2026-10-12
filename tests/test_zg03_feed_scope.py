"""ZG-03 — celebration & calendar feeds are tenant-scoped.

Both feeds previously queried every tenant's leads (CelebrationEngine /
CalendarService) and were reachable by ANY authenticated session
(``@session_required``). These tests pin the scoped contract:

* a caller only sees celebrations/events whose lead belongs to their
  canonical tenant scope (id + recorded legacy bridge);
* a caller without an authorized organization context is denied (fail
  closed) instead of receiving unfiltered data.
"""
from tests.auth_helper import seed_rbac


def _login(client, identity_id, org_id):
    """Bind the test client session to an identity + org context."""
    from app import db
    from app.auth import TeamMember

    admin = TeamMember.query.filter_by(email="admin@test.com").first()
    if not admin:
        admin = TeamMember(name="Admin", email="admin@test.com",
                           role="admin", is_active=True)
        admin.set_password("test")
        db.session.add(admin)
        db.session.commit()
    with client.session_transaction() as session:
        session["user_id"] = admin.id
        session["identity_id"] = identity_id
        session["current_org_id"] = org_id
        session["_fresh"] = True


def test_celebrations_feed_is_scoped(app, client):
    from app import db
    from app.celebrations import CelebrationEngine
    from app.models import (Lead, clear_lead_tenant_id, set_lead_tenant_id)

    with app.app_context():
        org_a = seed_rbac(db, identity_id="sid_zg03_fa")
        org_b = seed_rbac(db, identity_id="sid_zg03_fb")
        set_lead_tenant_id(org_b)
        lead_b = Lead(code="L-ZG-FB-1", source="test",
                      customer_name="B Celebration")
        lead_b.tenant_id = org_b
        clear_lead_tenant_id()
        db.session.add(lead_b)
        db.session.commit()
        CelebrationEngine().record_celebration(
            celebration_type="manual", title="B-only win",
            message="B celebration", lead_id=lead_b.id)

    _login(client, "sid_zg03_fa", org_a)
    res = client.get("/celebrations")
    assert res.status_code == 200, res.get_json()
    titles = [c.get("title") for c in res.get_json()["celebrations"]]
    assert "B-only win" not in titles  # THE CONTAINMENT

    _login(client, "sid_zg03_fb", org_b)
    res = client.get("/celebrations")
    titles = [c.get("title") for c in res.get_json()["celebrations"]]
    assert "B-only win" in titles      # same-tenant still works


def test_calendar_feed_is_scoped(app, client):
    from app import db
    from app.models import (Lead, clear_lead_tenant_id, set_lead_tenant_id)

    with app.app_context():
        org_a = seed_rbac(db, identity_id="sid_zg03_ca")
        org_b = seed_rbac(db, identity_id="sid_zg03_cb")
        set_lead_tenant_id(org_b)
        lead_b = Lead(code="L-ZG-CB-1", source="test", customer_name="CalGuest",
                      destination="Paris", dates="10-14 Jan 2027")
        lead_b.tenant_id = org_b
        clear_lead_tenant_id()
        db.session.add(lead_b)
        db.session.commit()

    rng = "?start=2027-01-01&end=2027-01-31"

    _login(client, "sid_zg03_ca", org_a)
    res = client.get("/calendar/events" + rng)
    assert res.status_code == 200, res.get_json()
    events = res.get_json()
    assert not [e for e in events if e.get("type") == "lead"]  # no foreign leads
    assert all("CalGuest" not in (e.get("title") or "") for e in events)

    _login(client, "sid_zg03_cb", org_b)
    events = client.get("/calendar/events" + rng).get_json()
    lead_events = [e for e in events if e.get("type") == "lead"]
    assert lead_events, "same-tenant lead events must still render"
    assert any("CalGuest" in (e.get("title") or "") for e in lead_events)


def test_feeds_deny_without_org_context(app, client):
    _login(client, "sid_zg03_fx_none", None)
    assert client.get("/celebrations").status_code == 403
    assert client.get("/calendar/events?start=2027-01-01&end=2027-01-31").status_code == 403
