"""R6B-2.7 Window 5 — Content Studio lifecycle route certification.

Covers `POST /api/v1/content/history/<id>/lifecycle` end-to-end through the
real HTTP route:

  ACTIVE   → archive → ARCHIVED   | trash → TRASHED
  ARCHIVED → restore → ACTIVE     | trash → TRASHED
  TRASHED  → recover → ACTIVE     | permanent_delete → removed

Regression guard: the original implementation used `setattr` lambdas whose
return value is always `None`, so EVERY action (including archive) returned
400 "Invalid transition". These tests assert the real transition succeeds —
they fail against that implementation.

Also asserts:
  * truthful, distinguishable failures (409 for state conflicts, not 400),
  * no existence disclosure across identities (404, never 403),
  * permanent delete requires the TRASHED state and truly removes the row,
  * a repeated permanent delete returns a truthful 404 (not a fake success).
"""
import pytest


OWNER = "sid_cs_lifecycle_owner"
OTHER = "sid_cs_lifecycle_other"


def _login(client, identity_id=OWNER):
    with client.session_transaction() as sess:
        sess["identity_id"] = identity_id
        sess["user_id"] = 1
        sess["current_org_id"] = 1


def _mk_item(app, identity_id=OWNER, **kw):
    from app import db
    from app.integration.models import ContentGeneration
    cg = ContentGeneration(
        identity_id=identity_id,
        content_type=kw.get("content_type", "blog_post"),
        prompt=kw.get("prompt", "test prompt"),
        generated_content=kw.get("generated_content", "test body"),
        status=kw.get("status", "active"),
        is_deleted=kw.get("is_deleted", False),
    )
    db.session.add(cg)
    db.session.commit()
    return cg.id


def _act(client, item_id, action):
    return client.post(f"/api/v1/content/history/{item_id}/lifecycle",
                       json={"action": action})


def _state(app, item_id):
    from app import db
    from app.integration.models import ContentGeneration
    row = db.session.get(ContentGeneration, item_id)
    if row is None:
        return None
    if row.is_deleted:
        return "trashed"
    return "archived" if row.status == "archived" else "active"


# ── Happy path ────────────────────────────────────────────────────────────

class TestTransitionsSucceed:
    def test_archive_active(self, app, client):
        _login(client)
        iid = _mk_item(app)
        r = _act(client, iid, "archive")
        assert r.status_code == 200, r.get_json()
        assert r.get_json()["state"] == "archived"
        assert _state(app, iid) == "archived"

    def test_restore_archived(self, app, client):
        _login(client)
        iid = _mk_item(app, status="archived")
        r = _act(client, iid, "restore")
        assert r.status_code == 200, r.get_json()
        assert r.get_json()["state"] == "active"
        assert _state(app, iid) == "active"

    def test_trash_active(self, app, client):
        _login(client)
        iid = _mk_item(app)
        r = _act(client, iid, "trash")
        assert r.status_code == 200, r.get_json()
        assert r.get_json()["state"] == "trashed"
        assert _state(app, iid) == "trashed"

    def test_trash_archived(self, app, client):
        _login(client)
        iid = _mk_item(app, status="archived")
        r = _act(client, iid, "trash")
        assert r.status_code == 200, r.get_json()
        assert _state(app, iid) == "trashed"

    def test_recover_trashed(self, app, client):
        _login(client)
        iid = _mk_item(app, is_deleted=True)
        r = _act(client, iid, "recover")
        assert r.status_code == 200, r.get_json()
        assert r.get_json()["state"] == "active"
        assert _state(app, iid) == "active"

    def test_full_round_trip(self, app, client):
        _login(client)
        iid = _mk_item(app)
        assert _act(client, iid, "archive").status_code == 200
        assert _state(app, iid) == "archived"
        assert _act(client, iid, "restore").status_code == 200
        assert _state(app, iid) == "active"
        assert _act(client, iid, "trash").status_code == 200
        assert _state(app, iid) == "trashed"
        assert _act(client, iid, "recover").status_code == 200
        assert _state(app, iid) == "active"


# ── Invalid transitions are truthful 409 conflicts ────────────────────────

class TestInvalidTransitions:
    @pytest.mark.parametrize("state,action", [
        ("archived", "archive"),
        ("active", "restore"),
        ("trashed", "restore"),
        ("trashed", "archive"),
        ("active", "recover"),
        ("archived", "recover"),
    ])
    def test_conflict(self, app, client, state, action):
        _login(client)
        iid = _mk_item(app,
                       status="archived" if state == "archived" else "active",
                       is_deleted=(state == "trashed"))
        r = _act(client, iid, action)
        assert r.status_code == 409, (state, action, r.get_json())
        body = r.get_json()
        assert body["success"] is False
        assert body["state"] == state
        # The action must NOT have changed the row.
        assert _state(app, iid) == state

    def test_unknown_action_400(self, app, client):
        _login(client)
        iid = _mk_item(app)
        r = _act(client, iid, "explode")
        assert r.status_code == 400
        assert r.get_json()["success"] is False

    def test_permanent_delete_requires_trashed(self, app, client):
        _login(client)
        active = _mk_item(app)
        archived = _mk_item(app, status="archived")
        for iid in (active, archived):
            r = _act(client, iid, "permanent_delete")
            assert r.status_code == 409, r.get_json()
            assert _state(app, iid) is not None  # NOT deleted


# ── Permanent delete ──────────────────────────────────────────────────────

class TestPermanentDelete:
    def test_removes_row(self, app, client):
        _login(client)
        iid = _mk_item(app, is_deleted=True)
        r = _act(client, iid, "permanent_delete")
        assert r.status_code == 200, r.get_json()
        assert r.get_json()["state"] == "deleted"
        assert _state(app, iid) is None

    def test_repeat_is_truthful_404(self, app, client):
        """A second permanent delete reports not-found, not a fake success."""
        _login(client)
        iid = _mk_item(app, is_deleted=True)
        assert _act(client, iid, "permanent_delete").status_code == 200
        r = _act(client, iid, "permanent_delete")
        assert r.status_code == 404
        assert r.get_json()["success"] is False


# ── Authorization ─────────────────────────────────────────────────────────

class TestAuthorization:
    def test_requires_auth(self, app, client):
        iid = _mk_item(app)
        r = client.post(f"/api/v1/content/history/{iid}/lifecycle",
                        json={"action": "archive"})
        assert r.status_code == 401

    def test_wrong_identity_no_existence_disclosure(self, app, client):
        """Another identity gets 404, never 403 — no existence leak."""
        iid = _mk_item(app, identity_id=OWNER)
        _login(client, OTHER)
        for action in ("archive", "trash", "recover", "permanent_delete"):
            r = _act(client, iid, action)
            assert r.status_code == 404, (action, r.get_json())
        # And the row is untouched.
        assert _state(app, iid) == "active"

    def test_wrong_identity_cannot_hard_delete(self, app, client):
        iid = _mk_item(app, identity_id=OWNER, is_deleted=True)
        _login(client, OTHER)
        assert _act(client, iid, "permanent_delete").status_code == 404
        assert _state(app, iid) == "trashed"  # still present


# ── History truthfulness ──────────────────────────────────────────────────

class TestHistoryTruthfulness:
    def test_history_reports_own_items_only(self, app, client):
        mine = _mk_item(app, identity_id=OWNER)
        theirs = _mk_item(app, identity_id=OTHER)
        _login(client, OWNER)
        r = client.get("/api/v1/content/history")
        assert r.status_code == 200
        ids = {i["id"] for i in r.get_json()["data"]}
        assert mine in ids
        assert theirs not in ids

    def test_history_schema_includes_lifecycle_fields(self, app, client):
        iid = _mk_item(app, identity_id=OWNER)
        _login(client, OWNER)
        r = client.get("/api/v1/content/history")
        assert r.status_code == 200
        row = next(i for i in r.get_json()["data"] if i["id"] == iid)
        assert row["status"] == "active"
        assert row["is_deleted"] is False

    def test_history_never_masks_storage_error(self, app, client, monkeypatch):
        """A storage failure must be a truthful 500, not an empty 200."""
        from app.integration.models import ContentGeneration

        class _BoomQuery:
            def filter_by(self, *a, **kw):
                raise RuntimeError("storage unavailable")

        _login(client, OWNER)
        monkeypatch.setattr(ContentGeneration, "query", _BoomQuery())
        r = client.get("/api/v1/content/history")
        assert r.status_code == 500
        assert r.get_json()["success"] is False
