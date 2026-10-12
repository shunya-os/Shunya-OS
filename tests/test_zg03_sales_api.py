"""ZG-03 B1 — Sales lead lifecycle API (detail / edit / status / search / history).

Pins the B1 contract:

* detail, PATCH and status are tenant-scoped — cross-tenant ids 404;
* edits are whitelisted, validated, and audited in the activity log;
* 'won'/'lost' must use their canonical transition routes;
* search (q) is tenant-scoped;
* activities (history) are tenant-scoped.
"""
from tests.test_zg03_leads_tenant_scope import (
    _login,
    _seed_two_orgs_with_leads,
)


def _own_lead(client, code):
    leads = client.get("/api/v1/leads/").get_json()["leads"]
    return [l for l in leads if l["code"] == code][0]


def test_detail_and_cross_tenant_404(app, client):
    org_a, _org_b, lead_b_id = _seed_two_orgs_with_leads(app)

    _login(client, "sid_zg03_a", org_a)
    # cross-tenant read/mutate/history must all fail closed
    assert client.get(f"/api/v1/leads/{lead_b_id}").status_code == 404
    assert client.patch(f"/api/v1/leads/{lead_b_id}",
                        json={"notes": "x"}).status_code == 404
    assert client.post(f"/api/v1/leads/{lead_b_id}/status",
                       json={"status": "contacted"}).status_code == 404
    assert client.get(f"/leads/{lead_b_id}/activities").status_code == 404

    # same-tenant detail works
    own = _own_lead(client, "L-ZG-A-1")
    res = client.get(f"/api/v1/leads/{own['id']}")
    assert res.status_code == 200
    assert res.get_json()["lead"]["code"] == "L-ZG-A-1"


def test_patch_whitelist_validation_and_audit(app, client):
    org_a, _org_b, _lead_b_id = _seed_two_orgs_with_leads(app)
    _login(client, "sid_zg03_a", org_a)
    own = _own_lead(client, "L-ZG-A-1")

    res = client.patch(f"/api/v1/leads/{own['id']}", json={
        "notes": "Updated note", "budget": 250, "status": "won", "ignored": "x",
    })
    assert res.status_code == 200, res.get_json()
    body = res.get_json()
    assert "notes" in body["changed"] and "budget" in body["changed"]
    assert "status" not in body["changed"]   # not whitelisted for edit
    assert "ignored" not in body["changed"]
    assert body["lead"]["notes"] == "Updated note"
    assert body["lead"]["budget"] == 250

    # invalid budget rejected
    res = client.patch(f"/api/v1/leads/{own['id']}", json={"budget": "abc"})
    assert res.status_code == 400

    # audit trail recorded — and attributed to the caller's tenant
    from app import db
    from app.models import ActivityLog
    with app.app_context():
        row = (ActivityLog.query.filter_by(action="updated")
               .order_by(ActivityLog.id.desc()).first())
        assert row is not None
        assert row.tenant_id == org_a, "audit row must carry the tenant (prod NOT NULL)"


def test_status_transition_rules(app, client):
    org_a, _org_b, _lead_b_id = _seed_two_orgs_with_leads(app)
    _login(client, "sid_zg03_a", org_a)
    own = _own_lead(client, "L-ZG-A-1")

    res = client.post(f"/api/v1/leads/{own['id']}/status",
                      json={"status": "contacted"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "contacted"

    # won / lost must go through canonical transition routes
    res = client.post(f"/api/v1/leads/{own['id']}/status",
                      json={"status": "won"})
    assert res.status_code == 400
    assert res.get_json().get("code") == "use_transition_route"

    # unknown status rejected
    assert client.post(f"/api/v1/leads/{own['id']}/status",
                       json={"status": "banana"}).status_code == 400

    # transition audited
    acts = client.get(f"/leads/{own['id']}/activities").get_json()
    assert any(a.get("action") == "status_changed" for a in acts), acts


def test_search_is_scoped(app, client):
    org_a, _org_b, _lead_b_id = _seed_two_orgs_with_leads(app)
    _login(client, "sid_zg03_a", org_a)

    res = client.get("/api/v1/leads/?q=ZG-A")
    codes = [l["code"] for l in res.get_json()["leads"]]
    assert "L-ZG-A-1" in codes
    assert "L-ZG-B-1" not in codes

    # searching for the other tenant's data yields nothing
    res = client.get("/api/v1/leads/?q=B own")
    assert res.get_json()["leads"] == []
