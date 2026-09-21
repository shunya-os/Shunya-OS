"""GJ-16b — EMOTIONAL CONTEXT TENANT BOUNDARY (proof, not narration).

The pre-existing `test_auth_boundary_wrong_tenant` asserted only that
NON-EXISTENT items return 404 while its docstring claimed "cross-tenant access
via header injection is not possible". That claim was never demonstrated.

This module demonstrates it, against a REAL item owned by a REAL other tenant:

  POSITIVE  the owning tenant can read its own item
  NEGATIVE  a caller with no membership cannot reach it by asserting
            X-Tenant-Id / X-Identity-Id, and the row is left UNCHANGED
  NEGATIVE  a cross-tenant WRITE (correct) is denied
  ANON      no session and no headers is denied

Why this matters: the route resolves
``tenant_id = g.current_org_id or request.headers.get("X-Tenant-Id")``, so if the
request-level guard ever stopped setting or denying the org context, a
client-chosen tenant would silently become authority. These tests pin the
boundary at the interface, where it can actually be attacked.
"""
from __future__ import annotations

import pytest

from app import db

VICTIM_ORG = 77001
OTHER_ORG = 77002
SECRET_CONTEXT = "CONFIDENTIAL victim frustration about a named employee"


@pytest.fixture
def seeded(app):
    """Victim org with an item, plus a second org with its own member."""
    with app.app_context():
        from app.auth import TeamMember
        from app.human_context.emotional import EmotionalContextService
        from app.models import OrgMember, Organization

        for oid, name in ((VICTIM_ORG, "Victim Org"), (OTHER_ORG, "Other Org")):
            db.session.add(Organization(id=oid, name=name, slug=f"org-{oid}", is_active=True))
        db.session.flush()

        victim = TeamMember(name="Victim", email="victim@t.com", role="owner", is_active=True)
        victim.set_password("x")
        victim.verified = True
        db.session.add(victim)
        db.session.flush()
        db.session.add(OrgMember(organization_id=VICTIM_ORG, identity_id=str(victim.id),
                                 name="Victim", email="victim@t.com", role="owner"))

        other = TeamMember(name="Other", email="other@t.com", role="owner", is_active=True)
        other.set_password("x")
        other.verified = True
        db.session.add(other)
        db.session.flush()
        db.session.add(OrgMember(organization_id=OTHER_ORG, identity_id=str(other.id),
                                 name="Other", email="other@t.com", role="owner"))
        db.session.commit()

        svc = EmotionalContextService()
        created = svc.record(
            expression_type="frustration",
            person_id=1,
            tenant_id=VICTIM_ORG,
            context=SECRET_CONTEXT,
            provenance="direct_observation",
            created_by=str(victim.id),
        )
        return {
            "item_id": created["item_id"],
            "victim_identity": str(victim.id),
            "other_identity": str(other.id),
        }


def _row(item_id):
    from app.human_context.emotional import EmotionalContextItem
    return db.session.get(EmotionalContextItem, item_id)


def test_positive_owner_can_read_own_item(app, seeded):
    """POSITIVE: with the owner's session the item is visible and intact."""
    with app.app_context():
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["identity_id"] = seeded["victim_identity"]
            sess["user_id"] = seeded["victim_identity"]
            sess["current_org_id"] = VICTIM_ORG

        resp = client.get("/api/v1/emotional/?person_id=1&limit=100",
                          headers={"X-Include-Sensitive": "true"})
        assert resp.status_code == 200, resp.get_json()
        ids = [i["id"] for i in (resp.get_json().get("items") or [])]
        assert seeded["item_id"] in ids, "owner must see their own tenant's context"


def test_negative_forged_tenant_header_cannot_read(app, seeded):
    """NEGATIVE: asserting another tenant via headers grants nothing."""
    with app.app_context():
        client = app.test_client()
        resp = client.get("/api/v1/emotional/?person_id=1&limit=100",
                          headers={
                              "X-Identity-Id": "attacker-999",
                              "X-Tenant-Id": str(VICTIM_ORG),
                              "X-Include-Sensitive": "true",
                          })
        assert resp.status_code in (401, 403), (
            f"forged tenant header must be denied, got {resp.status_code}: {resp.get_json()}"
        )
        body = resp.get_json() or {}
        assert SECRET_CONTEXT not in str(body), "response leaked another tenant's context"


def test_negative_cross_tenant_write_denied_and_row_unchanged(app, seeded):
    """NEGATIVE: a cross-tenant correction is denied and mutates nothing."""
    with app.app_context():
        before = _row(seeded["item_id"])
        assert before.status == "active"
        assert before.context == SECRET_CONTEXT

        client = app.test_client()
        resp = client.patch(
            f"/api/v1/emotional/{seeded['item_id']}/correct",
            json={"new_expression_type": "excitement", "new_context": "ATTACKER REWRITE"},
            headers={"X-Identity-Id": "attacker-999", "X-Tenant-Id": str(VICTIM_ORG)},
        )
        assert resp.status_code in (401, 403, 404), resp.get_json()

        after = _row(seeded["item_id"])
        assert after.status == "active", "denied write must not change the row"
        assert after.context == SECRET_CONTEXT, "denied write must not rewrite context"


def test_negative_expire_cross_tenant_denied(app, seeded):
    """NEGATIVE: another tenant cannot expire the item."""
    with app.app_context():
        client = app.test_client()
        resp = client.delete(
            f"/api/v1/emotional/{seeded['item_id']}",
            headers={"X-Identity-Id": "attacker-999", "X-Tenant-Id": str(VICTIM_ORG)},
        )
        assert resp.status_code in (401, 403, 404), resp.get_json()
        assert _row(seeded["item_id"]).status == "active"


def test_anonymous_is_denied(app, seeded):
    """ANON: no session and no headers must not reach emotional context."""
    with app.app_context():
        client = app.test_client()
        resp = client.get("/api/v1/emotional/?person_id=1")
        assert resp.status_code >= 400, resp.get_json()
        assert SECRET_CONTEXT not in str(resp.get_json() or {})
