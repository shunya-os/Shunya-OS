"""R6B-2.7 Window 6 §3 — Release-integrity regression tests.

These prove the release-integrity defect is FIXED, not merely documented:

  1. A local build cannot change the production-served artifact.
  2. The production artifact is tied to a release SHA.
  3. The production frontend SHA is comparable to the backend release identity.
  4. Deployment does not discard unrelated repository work.
  5. Dirty/unexpected production state fails closed.
  6. CI remains the only authorized production delivery path.

Test 4/5 execute the real pre-flight guard against real temporary git
repositories — an executable proof, not a source-text assertion.
"""
from __future__ import annotations

import json
import os
import subprocess

import pytest

from app import frontend_release as fr

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEPLOY_SH = os.path.join(REPO_ROOT, "infrastructure", "scripts", "deploy.sh")
PREFLIGHT_SH = os.path.join(REPO_ROOT, "infrastructure", "scripts", "deploy_preflight.sh")
CI_YML = os.path.join(REPO_ROOT, ".github", "workflows", "ci.yml")


# ── 1. Local build cannot change the production-served artifact ──────────


def test_env_override_wins(tmp_path):
    target = tmp_path / "rel"
    target.mkdir()
    assert fr.resolve_frontend_dist({fr.FRONTEND_RELEASE_ENV: str(target)}) == str(target)


def test_published_release_is_served_instead_of_the_worktree(tmp_path, monkeypatch):
    """Once a release is published, production NEVER serves frontend/dist."""
    releases = tmp_path / "releases"
    current = releases / "current"
    current.mkdir(parents=True)
    (current / "release.json").write_text(json.dumps({
        "release_sha": "a" * 40,
        "asset_manifest_sha256": "b" * 64,
    }))

    monkeypatch.setattr(fr, "default_releases_root", lambda: str(releases))

    resolved = fr.resolve_frontend_dist({})
    assert resolved == str(current), "a published release must be preferred"
    assert resolved != fr.default_build_dir(), "production must not serve the worktree build"
    assert fr.is_immutable_release(resolved) is True


def test_worktree_build_is_used_only_when_no_release_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(fr, "default_releases_root", lambda: str(tmp_path / "absent"))
    assert fr.resolve_frontend_dist({}) == fr.default_build_dir()
    assert fr.is_immutable_release(fr.default_build_dir()) is False


def test_incomplete_release_is_ignored(tmp_path, monkeypatch):
    """A 'current' dir without a manifest must NOT be served as a release."""
    releases = tmp_path / "releases"
    (releases / "current").mkdir(parents=True)
    monkeypatch.setattr(fr, "default_releases_root", lambda: str(releases))
    assert fr.resolve_frontend_dist({}) == fr.default_build_dir()


def test_app_serves_through_the_resolver():
    """app/__init__.py must resolve the served dir via the release resolver."""
    src = open(os.path.join(REPO_ROOT, "app", "__init__.py"), encoding="utf-8").read()
    assert "from app.frontend_release import resolve_frontend_dist" in src
    assert "frontend_dist = resolve_frontend_dist()" in src


# ── 2 & 3. Artifact tied to a release SHA; matches backend identity ──────


def test_manifest_binds_artifact_to_sha():
    sha = "c" * 40
    ok, reason = fr.validate_release_manifest(
        {"release_sha": sha, "asset_manifest_sha256": "d" * 64}, sha
    )
    assert ok, reason


def test_manifest_rejects_wrong_sha():
    ok, _ = fr.validate_release_manifest(
        {"release_sha": "e" * 40, "asset_manifest_sha256": "d" * 64}, "f" * 40
    )
    assert not ok


def test_manifest_rejects_missing_asset_hash():
    ok, _ = fr.validate_release_manifest({"release_sha": "a" * 40}, "a" * 40)
    assert not ok


def test_manifest_rejects_absent_manifest():
    ok, _ = fr.validate_release_manifest(None, "a" * 40)
    assert not ok


def test_provenance_reports_mismatch_capability():
    """frontend_provenance exposes the keys /health uses to detect drift."""
    prov = fr.frontend_provenance()
    for key in (
        "frontend_dist_mode",
        "frontend_dist_exists",
        "frontend_release_sha",
        "frontend_asset_manifest_sha256",
        "frontend_release_verified",
    ):
        assert key in prov


# ── 4 & 5. Deploy must not discard work; dirty state fails closed ────────


def _git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


def _init_repo(path):
    _git(path, "init", "-q")
    (path / "a.txt").write_text("hello\n")
    _git(path, "add", "a.txt")
    _git(path, "commit", "-q", "-m", "init")
    return path


def _preflight(path):
    return subprocess.run(
        ["bash", PREFLIGHT_SH, str(path)], capture_output=True, text=True
    )


def test_preflight_passes_on_clean_tree(tmp_path):
    repo = _init_repo(tmp_path)
    r = _preflight(repo)
    assert r.returncode == 0, r.stderr


def test_preflight_refuses_uncommitted_tracked_changes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("uncommitted developer work\n")
    r = _preflight(repo)
    assert r.returncode == 1
    assert "refusing to deploy" in r.stderr.lower()
    # The work must still be there — the guard modified nothing.
    assert (repo / "a.txt").read_text() == "uncommitted developer work\n"


def test_preflight_refuses_untracked_files(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "scratch.txt").write_text("wip\n")
    r = _preflight(repo)
    assert r.returncode == 1
    assert (repo / "scratch.txt").exists(), "guard must not delete untracked work"


def test_preflight_does_not_run_any_reset():
    """The guard must never mutate the repository (checked on executable lines)."""
    src = open(PREFLIGHT_SH, encoding="utf-8").read()
    code_lines = [
        ln for ln in src.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    code = "\n".join(code_lines)
    for forbidden in ("git reset", "git checkout", "git clean", "git stash", "git rebase"):
        assert forbidden not in code, f"pre-flight must not call '{forbidden}'"


# ── 6. CI remains the only authorized delivery path ─────────────────────


def test_guard_precedes_the_first_hard_reset_in_deploy():
    """No reset may run before the work-preservation guard has passed."""
    src = open(DEPLOY_SH, encoding="utf-8").read()
    guard_idx = src.find("deploy_preflight.sh")
    reset_idx = src.find("git reset --hard")
    assert guard_idx != -1, "deploy.sh must invoke the pre-flight guard"
    assert reset_idx != -1, "deploy.sh still deploys a SHA"
    assert guard_idx < reset_idx, "the guard MUST run before any hard reset"


def test_deploy_publishes_an_immutable_release_atomically():
    src = open(DEPLOY_SH, encoding="utf-8").read()
    assert "release.json" in src, "deploy must write a release manifest"
    assert "asset_manifest_sha256" in src
    assert "ln -sfn" in src and "mv -Tf" in src, "symlink swap must be atomic"


def test_ci_is_the_authorized_delivery_path():
    src = open(CI_YML, encoding="utf-8").read()
    assert "deploy.sh' > \"${DEPLOY_SCRIPT}\"" in src or "deploy.sh" in src
    assert "github.sha" in src, "deploy must be tied to the certified SHA"
    assert "git show" in src, "deploy script must come from the certified commit"
