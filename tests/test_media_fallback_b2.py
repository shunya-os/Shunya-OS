"""ZG-03 B2 — Image fallback chain and route-shadow resolution tests.

All network calls are monkeypatched; nothing hits production or paid APIs.
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
        from app.objects.legacy_models import Workspace, ShWorkspaceMembership, ShunyaObject  # noqa: F401
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture
def auth(app, client):
    """Seed RBAC context and authenticate the test client (same as lifecycle tests)."""
    from tests.auth_helper import seed_rbac, seed_canonical_tenancy
    from app import db
    from app.models import Organization, OrgMember
    from app.authz.services import seed_default_roles

    ORG_ID = 302
    IDENTITY = "b2-media-user"

    with app.app_context():
        org = db.session.get(Organization, ORG_ID)
        if not org:
            org = Organization(id=ORG_ID, name="B2 Media Org", slug="b2-media", is_active=True)
            db.session.add(org)
            db.session.flush()
        seed_default_roles(ORG_ID)
        member = OrgMember.query.filter_by(organization_id=ORG_ID, identity_id=IDENTITY).first()
        if not member:
            member = OrgMember(organization_id=ORG_ID, identity_id=IDENTITY, role="owner", is_active=True)
            db.session.add(member)
            db.session.commit()
        ws_id = seed_canonical_tenancy(db, ORG_ID, IDENTITY)

    with client.session_transaction() as sess:
        sess["identity_id"] = IDENTITY
        sess["user_id"] = 1
        sess["current_org_id"] = ORG_ID
        sess["workspace_id"] = ws_id
    return {"X-Identity-Id": IDENTITY}, ORG_ID, ws_id


@pytest.fixture
def offline_images(monkeypatch):
    """Force HF dead + Pollinations alive with deterministic bytes; avoid disk IO."""
    from app.media import service as ms
    from app.content_studio.image_providers import get_registry, init_providers, GenerationResult

    PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 256

    def _dead_hf(prompt, aspect_ratio="1:1"):
        raise RuntimeError("simulated HF 402 no credits")

    monkeypatch.setattr(ms, "_generate_hf_image", _dead_hf)
    monkeypatch.setattr(ms, "_get_hf_token", lambda: "fake-token")
    monkeypatch.setattr(ms, "_fetch_pollinations_bytes",
                        lambda prompt, width=1024, height=1024: PNG)
    monkeypatch.setattr(ms, "_save_image_file",
                        lambda raw, identity: f"/api/v1/media/uploads/{identity}/b2test.png")

    # Pin the image-provider REGISTRY generator to deterministic bytes too
    # (the registry holds the function reference at registration time, so the
    # module-level monkeypatch above would not affect it).
    try:
        reg = get_registry()
        if not reg.get_available_tiers():
            reg = init_providers()

        def _fake_pollinations(prompt, config, **kw):
            return GenerationResult(
                success=True, image_bytes=PNG,
                provider="pollinations", model="pollinations", tier="economy",
            )
        reg._generators["pollinations"] = _fake_pollinations
    except Exception:
        pass  # registry not initialized in this app context is fine for unit tests
    return PNG


@pytest.fixture
def dead_everything(monkeypatch):
    """Both providers fail → truthful degradation."""
    from app.media import service as ms

    def _dead_hf(prompt, aspect_ratio="1:1"):
        raise RuntimeError("simulated HF 402 no credits")

    def _dead_pollinations(prompt, width=1024, height=1024):
        raise RuntimeError("simulated pollinations outage")

    monkeypatch.setattr(ms, "_generate_hf_image", _dead_hf)
    monkeypatch.setattr(ms, "_get_hf_token", lambda: "fake-token")
    monkeypatch.setattr(ms, "_fetch_pollinations_bytes", _dead_pollinations)
    return None


class TestImageFallbackChain:
    """HF dead → Pollinations fallback must produce a real image."""

    def test_generate_media_uses_pollinations(self, app, auth, offline_images):
        from app.media.service import generate_media
        _auth, org_id, ws_id = auth
        result = generate_media(
            raw_prompt="a sunrise over the ocean",
            identity_id="b2-media-user",
            organization_id=org_id,
            workspace_id=ws_id,
            aspect_ratio="1:1",
            visual_style="realistic",
        )
        assert result["runtime_state"] == "generated", result.get("failure_reason")
        assert result["result_kind"] == "generated_image"
        assert result["asset_url"] is not None
        assert "pollinations" in (result["provider"] or ""), result.get("provider")
        # New truthful flag: an actual image exists
        assert result["image_generated"] is True

    def test_generate_media_all_dead_is_truthful(self, app, auth, dead_everything):
        from app.media.service import generate_media
        _auth, org_id, ws_id = auth
        result = generate_media(
            raw_prompt="a sunrise over the ocean",
            identity_id="b2-media-user",
            organization_id=org_id,
            workspace_id=ws_id,
            aspect_ratio="1:1",
            visual_style="realistic",
        )
        assert result["runtime_state"] == "description_only", result
        assert result["result_kind"] == "visual_concept"
        assert result["asset_url"] is None
        assert result["image_generated"] is False
        assert "pollinations" in (result.get("failure_reason") or "")
        assert "huggingface" in (result.get("failure_reason") or "")

    def test_fallback_chain_unit(self, monkeypatch):
        """_generate_image_with_fallback returns (bytes, provider, []) when HF dead."""
        from app.media import service as ms

        def _dead_hf(prompt, aspect_ratio="1:1"):
            raise RuntimeError("412 simulated")

        def _ok_poll(prompt, width=1024, height=1024):
            return b"\xff\xd8" + b"\x00" * 64  # JPEG magic

        monkeypatch.setattr(ms, "_generate_hf_image", _dead_hf)
        monkeypatch.setattr(ms, "_get_hf_token", lambda: "tok")
        monkeypatch.setattr(ms, "_fetch_pollinations_bytes", _ok_poll)
        image_bytes, provider, errors = ms._generate_image_with_fallback("test", "1:1")
        assert image_bytes is not None
        assert provider == "pollinations/pollinations"
        assert errors == []


class TestRouteShadowResolution:
    """/api/v1/content/image/generate must reach the IMAGE handler; text stays text."""

    def test_image_generate_route_reachable(self, client, auth, offline_images):
        headers, _org, _ws = auth
        resp = client.post("/api/v1/content/image/generate", headers=headers, json={
            "prompt": "sunrise illustration",
            "tier": "economy",
            "provider": "pollinations",
        })
        body = resp.get_json()
        assert resp.status_code == 200, body
        assert body["success"] is True
        assert body["image_generated"] is True
        assert body["image_url"] is not None
        assert body["provider"] == "pollinations"
        # The image handler must NOT echo text-generation fields
        assert "output_language" not in body

    def test_text_generate_still_text(self, client, auth, offline_images):
        headers, _org, _ws = auth
        resp = client.post("/api/v1/content/generate", headers=headers, json={
            "prompt": "Write a short blog post",
            "content_type": "blog_post",
            "tone": "professional",
            "word_count": 30,
        })
        body = resp.get_json()
        # Text handler response (conftest pins SHUNYA_AI_PROVIDERS=local so this
        # deterministically succeeds with canned content; the point is the ROUTE)
        assert "output_language" in body
        assert body.get("image_url") is None

    def test_providers_alias_still_available(self, client, auth, offline_images):
        headers, _org, _ws = auth
        resp = client.get("/api/v1/content/providers", headers=headers)
        body = resp.get_json()
        assert resp.status_code == 200, body
        assert body["success"] is True
        names = {p["name"] for t in body["tiers"] for p in t["providers"]}
        assert "huggingface" in names
        assert "pollinations" in names
        assert "dummy" not in names  # never advertised in production listing

    def test_image_providers_new_path(self, client, auth, offline_images):
        headers, _org, _ws = auth
        resp = client.get("/api/v1/content/image/providers", headers=headers)
        body = resp.get_json()
        assert resp.status_code == 200, body
        assert body["success"] is True
        assert len(body["tiers"]) >= 1

    def test_capabilities_endpoint(self, client, auth):
        headers, _org, _ws = auth
        resp = client.get("/api/v1/capabilities/summary", headers=headers)
        body = resp.get_json()
        assert resp.status_code == 200, body
        assert body["success"] is True
        rows = {r["capability"]: r for r in body["capabilities"]}
        assert rows["image_generation"]["status"] == "AVAILABLE"  # pollinations ready
        assert rows["video_generation"]["status"] == "UNAVAILABLE"

    def test_capabilities_execute_unknown(self, client, auth):
        headers, _org, _ws = auth
        resp = client.post("/api/v1/capabilities/execute", headers=headers, json={
            "capability": "time_travel",
        })
        assert resp.status_code == 400
        assert resp.get_json()["error_class"] == "BAD_REQUEST"