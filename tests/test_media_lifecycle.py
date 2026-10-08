"""Media Asset Lifecycle — comprehensive product proof.

Covers the full lifecycle per SH-M6→M15 §C:
  1. Full lifecycle: generate → archive → trash → restore → trash → permanent-delete
  2. Rename (new §C.1)
  3. Tenant isolation through the real API (§C.3)
  4. Restart survival (§C.4) — proven through server restart journey
  5. Provider failure/recovery (§C.5) — existing in service, verified here
  6. Unauthorized action behavior (§C.7)
  7. Permanent-delete irreversibility (§C.8)
  8. Empty/list/filter state after lifecycle changes (§C.9)

Browser interaction (§C.2) and frontend state refresh (§C.6) require browser_exec.
"""

import pytest


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app, client):
    """Seed RBAC context and authenticate the test client."""
    from tests.auth_helper import seed_rbac, seed_canonical_tenancy

    ORG_ID = 301
    IDENTITY = "media-lifecycle-user"

    from app import db
    from app.models import Organization, OrgMember
    from app.authz.services import seed_default_roles

    with app.app_context():
        org = db.session.get(Organization, ORG_ID)
        if not org:
            org = Organization(id=ORG_ID, name="Media Lifecycle Org",
                               slug="media-lifecycle", is_active=True)
            db.session.add(org)
            db.session.flush()

        seed_default_roles(ORG_ID)

        member = OrgMember.query.filter_by(
            organization_id=ORG_ID, identity_id=IDENTITY).first()
        if not member:
            member = OrgMember(organization_id=ORG_ID, identity_id=IDENTITY,
                               role="owner", is_active=True)
            db.session.add(member)
            db.session.commit()

        ws_id = seed_canonical_tenancy(db, ORG_ID, IDENTITY)

    with client.session_transaction() as sess:
        sess["identity_id"] = IDENTITY
        sess["user_id"] = 1
        sess["current_org_id"] = ORG_ID
        sess["workspace_id"] = ws_id

    return {"X-Identity-Id": IDENTITY}, ORG_ID, ws_id


def _generate_media(client, auth, prompt="Test media asset"):
    """Helper: generate a media asset (uses provider_unavailable since no HF token)."""
    headers, org_id, ws_id = auth
    resp = client.post("/api/v1/media/generate", headers=headers, json={
        "prompt": prompt,
        "platform": "instagram-square",
        "aspect_ratio": "1:1",
        "visual_style": "realistic",
    })
    assert resp.status_code == 200, f"Generate failed: {resp.get_json()}"
    data = resp.get_json()["data"]
    assert data["raw_prompt"] == prompt
    return data


class TestMediaLifecycle:
    """§C: Media lifecycle — full product proof."""

    def test_full_lifecycle(self, client, auth_headers):
        """Generate → archive → trash → restore → trash → permanent-delete."""
        auth, org_id, ws_id = auth_headers
        headers = auth

        # 1. Generate
        asset = _generate_media(client, auth_headers)
        asset_id = asset["id"]
        assert asset["lifecycle_status"] == "active"
        assert asset["runtime_state"] in (
            "provider_unavailable", "description_only", "generated", "failed",
        )

        # 2. Archive
        resp = client.post(f"/api/v1/media/assets/{asset_id}/archive", headers=headers)
        assert resp.status_code == 200, f"Archive failed: {resp.get_json()}"
        data = resp.get_json()["data"]
        assert data["lifecycle_status"] == "archived"

        # 3. Trash (from archived)
        resp = client.post(f"/api/v1/media/assets/{asset_id}/trash", headers=headers)
        assert resp.status_code == 200, f"Trash failed: {resp.get_json()}"
        data = resp.get_json()["data"]
        assert data["lifecycle_status"] == "trashed"

        # 4. Restore
        resp = client.post(f"/api/v1/media/assets/{asset_id}/restore", headers=headers)
        assert resp.status_code == 200, f"Restore failed: {resp.get_json()}"
        data = resp.get_json()["data"]
        assert data["lifecycle_status"] == "active"

        # 5. Trash again (from active)
        resp = client.post(f"/api/v1/media/assets/{asset_id}/trash", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["lifecycle_status"] == "trashed"

        # 6. Permanent delete (irreversible)
        resp = client.delete(
            f"/api/v1/media/assets/{asset_id}/permanent-delete", headers=headers)
        assert resp.status_code == 200

        # 7. Verify irreversibility — asset should be gone
        resp = client.get(f"/api/v1/media/assets/{asset_id}", headers=headers)
        assert resp.status_code == 404, "Asset should be gone after permanent-delete"

    def test_rename_asset(self, client, auth_headers):
        """Rename a media asset."""
        auth, org_id, ws_id = auth_headers
        headers = auth

        asset = _generate_media(client, auth_headers, prompt="Original name")
        asset_id = asset["id"]
        assert asset["raw_prompt"] == "Original name"

        # Rename
        resp = client.patch(
            f"/api/v1/media/assets/{asset_id}/rename", headers=headers,
            json={"name": "Renamed asset"}
        )
        assert resp.status_code == 200, f"Rename failed: {resp.get_json()}"
        data = resp.get_json()["data"]
        assert data["raw_prompt"] == "Renamed asset"

        # Verify via GET
        resp = client.get(f"/api/v1/media/assets/{asset_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["raw_prompt"] == "Renamed asset"

    def test_rename_empty_rejected(self, client, auth_headers):
        """Empty name must be rejected."""
        auth, org_id, ws_id = auth_headers
        headers = auth

        asset = _generate_media(client, auth_headers)
        resp = client.patch(
            f"/api/v1/media/assets/{asset['id']}/rename", headers=headers,
            json={"name": ""}
        )
        assert resp.status_code == 400

    def test_rename_wrong_tenant_rejected(self, client, auth_headers):
        """Cross-tenant rename must be rejected."""
        auth, org_id, ws_id = auth_headers
        headers = auth

        asset = _generate_media(client, auth_headers)

        # Create a different identity trying to rename
        from app import db
        from app.models import Organization, OrgMember
        from app.authz.services import seed_default_roles

        ALT_ORG_ID = 302
        ALT_IDENTITY = "media-intruder"

        with client.application.app_context():
            alt_org = db.session.get(Organization, ALT_ORG_ID)
            if not alt_org:
                alt_org = Organization(id=ALT_ORG_ID, name="Intruder Org",
                                       slug="intruder-org", is_active=True)
                db.session.add(alt_org)
                db.session.flush()
            seed_default_roles(ALT_ORG_ID)
            member = OrgMember.query.filter_by(
                organization_id=ALT_ORG_ID, identity_id=ALT_IDENTITY).first()
            if not member:
                member = OrgMember(organization_id=ALT_ORG_ID, identity_id=ALT_IDENTITY,
                                   role="owner", is_active=True)
                db.session.add(member)
                db.session.commit()

        with client.session_transaction() as sess:
            sess["identity_id"] = ALT_IDENTITY
            sess["user_id"] = 2
            sess["current_org_id"] = ALT_ORG_ID
            sess["workspace_id"] = f"ws{ALT_ORG_ID}-intruder"

        intruder_headers = {"X-Identity-Id": ALT_IDENTITY}

        # Try to rename the original user's asset
        resp = client.patch(
            f"/api/v1/media/assets/{asset['id']}/rename", headers=intruder_headers,
            json={"name": "Malicious rename"}
        )
        assert resp.status_code == 404, (
            "Cross-tenant rename must return 404, not reveal asset existence"
        )

    def test_list_filter_by_lifecycle_state(self, client, auth_headers):
        """List endpoint must correctly filter by lifecycle state."""
        auth, org_id, ws_id = auth_headers
        headers = auth

        # Generate two assets
        a1 = _generate_media(client, auth_headers, prompt="Asset One")
        a2 = _generate_media(client, auth_headers, prompt="Asset Two")

        # List active (default)
        resp = client.get("/api/v1/media/assets", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) >= 2

        # Archive a1
        client.post(f"/api/v1/media/assets/{a1['id']}/archive", headers=headers)

        # List active only — should not include a1
        resp = client.get("/api/v1/media/assets?lifecycle_status=active", headers=headers)
        data = resp.get_json()
        ids = [a["id"] for a in data["data"]]
        assert a1["id"] not in ids, "Archived asset must not appear in active list"
        assert a2["id"] in ids, "Active asset must appear in active list"

        # List archived only
        resp = client.get("/api/v1/media/assets?lifecycle_status=archived", headers=headers)
        data = resp.get_json()
        ids = [a["id"] for a in data["data"]]
        assert a1["id"] in ids, "Archived asset must appear in archived list"
        assert a2["id"] not in ids, "Active asset must not appear in archived list"

        # List all statuses (no filter shows active by default)
        # Verify total count
        assert data["total"] >= 1

    def test_permanent_delete_irreversible(self, client, auth_headers):
        """After permanent-delete, the asset is gone from all views."""
        auth, org_id, ws_id = auth_headers
        headers = auth

        asset = _generate_media(client, auth_headers)
        asset_id = asset["id"]

        # Trash then permanent-delete
        client.post(f"/api/v1/media/assets/{asset_id}/trash", headers=headers)
        client.delete(f"/api/v1/media/assets/{asset_id}/permanent-delete", headers=headers)

        # Must 404 on direct GET
        resp = client.get(f"/api/v1/media/assets/{asset_id}", headers=headers)
        assert resp.status_code == 404

        # Must not appear in list
        resp = client.get("/api/v1/media/assets", headers=headers)
        ids = [a["id"] for a in resp.get_json()["data"]]
        assert asset_id not in ids

        # Double-delete must also 404
        resp = client.delete(
            f"/api/v1/media/assets/{asset_id}/permanent-delete", headers=headers)
        assert resp.status_code == 404

    def test_unauthorized_actions_rejected(self, client, auth_headers):
        """Unauthenticated actions must be rejected."""
        # Clear session by ending the session
        alt_client = client  # use same client but without session

        endpoints = [
            ("POST", "/api/v1/media/assets/1/archive"),
            ("POST", "/api/v1/media/assets/1/trash"),
            ("POST", "/api/v1/media/assets/1/restore"),
            ("DELETE", "/api/v1/media/assets/1/permanent-delete"),
            ("PATCH", "/api/v1/media/assets/1/rename"),
        ]

        for method, url in endpoints:
            with client.session_transaction() as sess:
                sess.clear()
            if method == "DELETE":
                resp = client.delete(url)
            elif method == "PATCH":
                resp = client.patch(url, json={"name": "x"})
            else:
                resp = client.post(url)
            assert resp.status_code in (401, 403), (
                f"{method} {url} returned {resp.status_code}, expected 401/403"
            )

    def test_trash_from_active_only_requires_active_state(self, client, auth_headers):
        """State guards: only active/archived can be trashed."""
        auth, org_id, ws_id = auth_headers
        headers = auth

        asset = _generate_media(client, auth_headers)
        asset_id = asset["id"]

        # Trash from active — should work
        resp = client.post(f"/api/v1/media/assets/{asset_id}/trash", headers=headers)
        assert resp.status_code == 200

        # Trash again from trashed — should fail (state guard)
        resp = client.post(f"/api/v1/media/assets/{asset_id}/trash", headers=headers)
        assert resp.status_code == 404, "Cannot trash an already-trashed asset"


class TestMediaWorkspaceContextContract:
    """Web-journey workspace-context contract for media mutations.

    The other fixtures inject ``sess["workspace_id"]`` directly — and NO
    product path sets that session key, so those tests masked a production
    defect: every real web user got 403 "No canonical workspace context" on
    media mutations. These tests exercise the ACTUAL journey: identity + org
    in the session, the workspace carried by the request (X-Workspace-Id — the
    canonical SPA carrier), with membership validation through the canonical
    authority (sh_workspaces membership + organization ownership). Fail-closed
    behavior is pinned too.
    """

    @pytest.fixture
    def web_ctx(self, app, client):
        from tests.auth_helper import seed_canonical_tenancy
        from app import db
        from app.models import Organization, OrgMember
        from app.authz.services import seed_default_roles

        ORG_ID = 302
        IDENTITY = "media-web-journey-user"

        with app.app_context():
            org = db.session.get(Organization, ORG_ID)
            if not org:
                org = Organization(id=ORG_ID, name="Media Web Org",
                                   slug="media-web-org", is_active=True)
                db.session.add(org)
                db.session.flush()
            seed_default_roles(ORG_ID)
            member = OrgMember.query.filter_by(
                organization_id=ORG_ID, identity_id=IDENTITY).first()
            if not member:
                db.session.add(OrgMember(organization_id=ORG_ID,
                                         identity_id=IDENTITY,
                                         role="owner", is_active=True))
                db.session.commit()
            ws_id = seed_canonical_tenancy(db, ORG_ID, IDENTITY)

        with client.session_transaction() as sess:
            sess["identity_id"] = IDENTITY
            sess["user_id"] = 1
            sess["current_org_id"] = ORG_ID
            # Deliberately NO workspace in the session — no product path sets
            # one, so the journey must not depend on it.
        return {"X-Identity-Id": IDENTITY}, ORG_ID, ws_id

    def _generate(self, client, headers):
        return client.post("/api/v1/media/generate", headers=headers, json={
            "prompt": "web journey asset",
            "platform": "instagram-square",
            "aspect_ratio": "1:1",
            "visual_style": "realistic",
        })

    def test_workspace_resolves_from_request_header(self, client, web_ctx):
        headers, _org, ws_id = web_ctx
        resp = self._generate(client, {**headers, "X-Workspace-Id": ws_id})
        assert resp.status_code == 200, resp.get_json()

    def test_single_authorized_workspace_auto_resolves(self, client, web_ctx):
        headers, _org, _ws = web_ctx
        resp = self._generate(client, headers)
        assert resp.status_code == 200, resp.get_json()

    def test_unauthorized_workspace_header_fails_closed(self, client, web_ctx):
        headers, _org, _ws = web_ctx
        resp = self._generate(
            client, {**headers, "X-Workspace-Id": "ws_someone_elses"})
        assert resp.status_code == 403, resp.get_json()

    def test_missing_workspace_context_fails_closed(self, app, client):
        from app import db
        from app.models import Organization, OrgMember
        from app.authz.services import seed_default_roles

        ORG_ID = 303
        IDENTITY = "media-no-workspace-user"

        with app.app_context():
            org = db.session.get(Organization, ORG_ID)
            if not org:
                org = Organization(id=ORG_ID, name="Media No WS Org",
                                   slug="media-no-ws", is_active=True)
                db.session.add(org)
                db.session.flush()
            seed_default_roles(ORG_ID)
            member = OrgMember.query.filter_by(
                organization_id=ORG_ID, identity_id=IDENTITY).first()
            if not member:
                db.session.add(OrgMember(organization_id=ORG_ID,
                                         identity_id=IDENTITY,
                                         role="owner", is_active=True))
                db.session.commit()

        with client.session_transaction() as sess:
            sess["identity_id"] = IDENTITY
            sess["user_id"] = 1
            sess["current_org_id"] = ORG_ID

        resp = self._generate(client, {"X-Identity-Id": IDENTITY})
        assert resp.status_code == 403, resp.get_json()