"""ZG-03 — legacy leads API tenant containment (REG-RC-001).

The reproduction that opened this fix: a certification session (org 278)
listed every tenant's leads through ``GET /api/v1/leads/`` and could reach
any lead by id through the CRM module. These tests pin the containment
contract:

* reads are scoped to the caller's organization — the canonical id PLUS the
  recorded legacy bridge (``organizations.legacy_tenant_id``) — never "all
  leads";
* writes bind the canonical organization id server-side (never the body);
* a caller without an organization context is denied before any data path;
* cross-tenant lead ids fail closed on the CRM mutation surface.
"""
import pytest

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


def _seed_two_orgs_with_leads(app):
    """Org A (with legacy bridge 990) + org B, each owning leads."""
    from app import db
    from app.models import (Lead, Organization, clear_lead_tenant_id,
                            set_lead_tenant_id)

    with app.app_context():
        org_a = seed_rbac(db, identity_id="sid_zg03_a")
        org_b = seed_rbac(db, identity_id="sid_zg03_b")
        org = db.session.get(Organization, org_a)
        org.legacy_tenant_id = 990

        # Construct leads with an explicit tenant context per lead (the
        # Lead-Entity bridge requires it even under SQLite, where the entity
        # itself is skipped).
        set_lead_tenant_id(org_a)
        lead_a = Lead(code="L-ZG-A-1", source="test", customer_name="A own")
        lead_a.tenant_id = org_a
        set_lead_tenant_id(990)
        lead_leg = Lead(code="L-ZG-LEG-1", source="test", customer_name="A legacy")
        lead_leg.tenant_id = 990
        set_lead_tenant_id(org_b)
        lead_b = Lead(code="L-ZG-B-1", source="test", customer_name="B own")
        lead_b.tenant_id = org_b
        clear_lead_tenant_id()

        db.session.add_all([lead_a, lead_leg, lead_b])
        db.session.commit()
        return org_a, org_b, lead_b.id


def test_list_is_scoped_to_caller_tenant(app, client):
    org_a, org_b, _lead_b_id = _seed_two_orgs_with_leads(app)

    _login(client, "sid_zg03_a", org_a)
    res = client.get("/api/v1/leads/")
    assert res.status_code == 200
    codes = {l["code"] for l in res.get_json()["leads"]}
    assert "L-ZG-A-1" in codes       # canonical org id readable
    assert "L-ZG-LEG-1" in codes     # legacy bridge readable (founder data)
    assert "L-ZG-B-1" not in codes   # THE CONTAINMENT: other tenant hidden

    _login(client, "sid_zg03_b", org_b)
    res = client.get("/api/v1/leads/")
    assert res.status_code == 200
    codes = {l["code"] for l in res.get_json()["leads"]}
    assert codes == {"L-ZG-B-1"}     # b sees only its own


def test_create_binds_canonical_org_and_requires_context(app, client):
    from app import db
    from app.models import Lead

    with app.app_context():
        org_a = seed_rbac(db, identity_id="sid_zg03_c")

    _login(client, "sid_zg03_c", org_a)
    res = client.post("/api/v1/leads/", json={
        "customer_name": "ZG03 Lead", "source": "test", "budget": 100})
    assert res.status_code == 200
    body = res.get_json()
    assert "id" in body

    with app.app_context():
        lead = db.session.get(Lead, body["id"])
        assert lead is not None
        assert lead.tenant_id == org_a  # canonical write id, never the body


def test_no_org_context_is_denied(app, client):
    _login(client, "sid_zg03_no_org", None)
    assert client.get("/api/v1/leads/").status_code in (401, 403)
    assert client.post("/api/v1/leads/", json={}).status_code in (401, 403)


def test_crm_surface_fails_closed_on_cross_tenant_lead(app, client):
    org_a, org_b, lead_b_id = _seed_two_orgs_with_leads(app)

    _login(client, "sid_zg03_a", org_a)
    # Mutation + read by id must fail closed for a foreign tenant's lead.
    assert client.post(f"/api/v1/crm/leads/{lead_b_id}/qualify").status_code == 404
    assert client.get(f"/api/v1/crm/leads/{lead_b_id}/sla").status_code == 404
    assert client.post(f"/api/v1/crm/leads/{lead_b_id}/lost",
                       json={"reason": "x"}).status_code == 404

    # And the same-tenant path still works: A sees its own two leads.
    res = client.get("/api/v1/crm/leads")
    assert res.status_code == 200
    assert res.get_json()["total"] == 2
