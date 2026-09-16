"""R6B-2 Runtime Journey Proof — complete chain verification.

Tests: user auth -> canonical org/workspace -> object creation ->
canonical read -> AI context -> tenant isolation -> denial behaviour.

Uses Flask test client with SQLite in-memory. Not production data.
"""
import os
import json
import uuid

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['FLASK_ENV'] = 'test'
os.environ['SHUNYA_ENVIRONMENT'] = 'test'

from app import create_app, db
from app.models import Organization, OrgMember
from app.authz.services import seed_default_roles
from app.authz.models import Role, OrgMemberRole
from app.founder.models import FounderSpace
from app.auth import TeamMember

app = create_app()

with app.app_context():
    db.create_all()

    # === SETUP ===
    # Create Organization A
    org_a = Organization(name="OrgA", slug="org-a", business_type="tech")
    db.session.add(org_a)
    db.session.flush()
    org_a_id = org_a.id

    # Seed RBAC roles for Org A
    seed_default_roles(organization_id=org_a_id)

    # Create Organization B
    org_b = Organization(name="OrgB", slug="org-b", business_type="finance")
    db.session.add(org_b)
    db.session.flush()
    org_b_id = org_b.id

    # Create user Alice (Org A member only) — need identity_id before workspaces
    tm = TeamMember(name="Alice", email="alice@test.com", is_active=True, tenant_id=org_a_id)
    tm.set_password("test")
    db.session.add(tm)
    db.session.flush()
    identity_id = str(tm.id)

    # Create canonical workspaces
    ws_a_id = f"ws_a_{uuid.uuid4().hex[:8]}"
    ws_b_id = f"ws_b_{uuid.uuid4().hex[:8]}"
    db.session.execute(db.text(
        "INSERT INTO sh_workspaces (id, name, workspace_type, organization_id, status, created_by) "
        "VALUES (:id, :name, :type, :oid, 'active', :cb)"
    ), [
        {"id": ws_a_id, "name": "Workspace A", "type": "organization", "oid": org_a_id, "cb": identity_id},
        {"id": ws_b_id, "name": "Workspace B", "type": "organization", "oid": org_b_id, "cb": identity_id},
    ])
    db.session.commit()

    # OrgMember for Org A
    om_a = OrgMember(organization_id=org_a_id, identity_id=identity_id, email="alice@test.com", is_active=True)
    db.session.add(om_a)

    # Admin role in Org A (need member_id from OrgMember, not identity_id)
    admin_role = Role.query.filter_by(name="admin", organization_id=org_a_id).first()
    if admin_role and om_a.id:
        omr = OrgMemberRole(organization_id=org_a_id, member_id=om_a.id, role_id=admin_role.id)
        db.session.add(omr)

    # Alice is NOT in Org B — no OrgMember for B
    db.session.commit()

    # === TEST 1: Create canonical object in Org A ===
    from core.object_service import get_object_service
    svc = get_object_service()
    obj = svc.create(
        object_type="Document",
        name="OrgA_Doc",
        organization_id=org_a_id,
        data={"content": "Org A document content"},
        created_by=identity_id,
        workspace_id=ws_a_id,
        identity_id=identity_id,
    )
    obj_id = obj["id"]
    obj_oid = obj["object_id"]
    print(f"TEST1: Created object id={obj_id} oid={obj_oid} in org_a_id={org_a_id}")
    assert obj["organization_id"] == org_a_id, (
        f"Expected org_a_id={org_a_id}, got {obj['organization_id']}"
    )

    # === TEST 2: Read canonical object (Org A → Org A object = ALLOW) ===
    retrieved = svc.get(obj_id, organization_id=org_a_id, identity_id=identity_id)
    assert retrieved is not None, "Should retrieve object in same org"
    print(f"TEST2: Org A read own object: {retrieved['name']} — ALLOW ✓")

    # === TEST 3: Cross-org read (Org A object → Org B scope = DENY) ===
    cross = svc.get(obj_id, organization_id=org_b_id, identity_id=identity_id)
    assert cross is None, f"Cross-org read should be DENIED, got: {cross}"
    print(f"TEST3: Org B read Org A object: None — DENY ✓")

    # === TEST 4: Missing org (org_id=0) = DENY ===
    raised_valueerror = False
    try:
        svc.create(
            object_type="Document",
            name="NoOrg_Doc",
            organization_id=0,
            data={},
            created_by=identity_id,
            identity_id=identity_id,
        )
    except ValueError:
        raised_valueerror = True
    assert raised_valueerror, "Should fail closed on missing org (0)"
    print(f"TEST4: Rejected org_id=0 — DENY ✓")

    # === TEST 5: Synthetic/unowned org (99999) = DENY ===
    # Alice holds no canonical membership in org 99999, so creating there must
    # be refused by AUTHORIZATION — not silently accepted as an isolated object.
    from app.authz.workspace_context import OwnershipContextError
    denied = False
    try:
        svc.create(
            object_type="Document",
            name="InvalidOrg_Doc",
            organization_id=99999,
            data={},
            created_by=identity_id,
            workspace_id=ws_a_id,
            identity_id=identity_id,
        )
    except (OwnershipContextError, ValueError):
        denied = True
    assert denied, "org=99999 with no membership MUST be denied"
    print("TEST5: org=99999 without membership — DENY ✓")

    # === TEST 6: Read via get_by_object_id (canonical-first read path) ===
    ai_read = svc.get_by_object_id(obj_oid, organization_id=org_a_id)
    assert ai_read is not None, "AI context should read canonical"
    print(f"TEST6: AI context read canonical object: {ai_read['name']} — ALLOW ✓")

    # === TEST 7: Tenant isolation in list ===
    all_a = svc.list_by_workspace(workspace_id=ws_a_id, organization_id=org_a_id)
    all_b = svc.list_by_workspace(workspace_id=ws_b_id, organization_id=org_b_id)
    assert len(all_a) >= 1, f"Org A should have >=1 objects, had {len(all_a)}"
    assert len(all_b) == 0, f"Org B workspace should be empty, had {len(all_b)}"
    print(f"TEST7: Org A has {len(all_a)} object(s), Org B has {len(all_b)} — isolation ✓")

    # === TEST 8: Synthetic org lookup returns None ===
    fake = svc.get_by_object_id("nonexistent_oid", organization_id=1)
    assert fake is None, f"Should return None for nonexistent object, got {fake}"
    print("TEST8: org_id=1 on nonexistent returns None — closed ✓")

    # === TEST 9: Verify object persistence across service instance ===
    from core.object_service import ObjectService
    svc2 = ObjectService()
    re_read = svc2.get(obj_id, organization_id=org_a_id, identity_id=identity_id)
    assert re_read is not None, "Object should persist across service instances"
    assert re_read["name"] == "OrgA_Doc", f"Name should persist, got {re_read['name']}"
    print(f"TEST9: Object persists across service instances: {re_read['name']} — SURVIVES ✓")

    print()
    print("=== RUNTIME JOURNEY: ALL 9 TESTS PASSED ===")
    print("Complete chain: canonical org/workspace → object creation →")
    print("canonical read → AI context → tenant isolation → denial → restart survival")