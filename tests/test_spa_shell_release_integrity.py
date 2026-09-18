"""The SPA shell must be served from the SAME directory as the assets.

Release-integrity gap: assets were served from the immutable published release
(``resolve_frontend_dist()``), but the shell HTML was read from the mutable
in-checkout ``frontend/dist`` for `/`, `/auth/*` and `/workspace/*`. A local
``npm run build`` would therefore change the served shell to reference asset
hashes that are absent from the published release — broken production with a
green health endpoint.

These tests pin the resolution behaviour: the shell follows the resolved
frontend directory, with the in-checkout build kept only as a fallback.
"""
import os

import pytest

MARKER = "SHUNYA_RELEASE_SHELL_MARKER"


@pytest.fixture
def release_dir(tmp_path):
    """A stand-in immutable release directory containing a marked shell."""
    dist = tmp_path / "releases" / "current"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text(
        f"<!doctype html><html><body>{MARKER}<script crossorigin src=\"/assets/x.js\"></script></body></html>",
        encoding="utf-8",
    )
    return str(dist)


def test_spa_shell_is_served_from_the_resolved_frontend_dir(app, release_dir, monkeypatch):
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", release_dir)
    resp = app.test_client().get("/")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:200]
    body = resp.get_data(as_text=True)
    assert MARKER in body, "shell was not served from the resolved frontend directory"
    # and the crossorigin attribute is still stripped as before
    assert "crossorigin " not in body


def test_auth_shell_also_uses_the_resolved_dir(app, release_dir, monkeypatch):
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", release_dir)
    resp = app.test_client().get("/auth/login")
    assert resp.status_code == 200
    assert MARKER in resp.get_data(as_text=True)


def test_resolution_order_prefers_the_release_and_keeps_the_worktree_fallback(
        app, release_dir, monkeypatch):
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", release_dir)
    from app.routes import _spa_shell_dirs, _FRONTEND_DIST
    dirs = _spa_shell_dirs()
    assert os.path.abspath(dirs[0]) == os.path.abspath(release_dir)
    # the in-checkout build is still available as a development fallback
    assert any(os.path.abspath(d) == os.path.abspath(_FRONTEND_DIST) for d in dirs)


def test_resolution_never_raises_when_nothing_is_published(app, monkeypatch, tmp_path):
    """A missing/!invalid release must degrade to the worktree, not crash."""
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", str(tmp_path / "does-not-exist"))
    from app.routes import _spa_shell_dirs
    dirs = _spa_shell_dirs()
    assert dirs, "expected at least the in-checkout fallback"
    assert all(isinstance(d, str) and d for d in dirs)
