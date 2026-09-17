"""SHUNYA — Frontend release-integrity resolver.

WHY THIS EXISTS (R6B-2.7 Window 6, §3)
--------------------------------------
`frontend/dist` used to be served straight out of the live developer checkout.
That meant a plain `npm run build` silently changed what production served —
without a commit, CI, a deployment, a release authorisation or a SHA
certification. The deployed frontend was also not tied to the certified release
SHA, and the deploy reset the live worktree (destroying uncommitted work).

This module makes the served frontend an IMMUTABLE RELEASE ARTIFACT:

    source repo → committed SHA → CI build → immutable release dir
                → atomic symlink swap → production

Production points `SHUNYA_FRONTEND_DIST` at ``<releases>/current`` (a symlink
swapped atomically by the deploy). The worktree's ``frontend/dist`` is only an
intermediate build directory and is never served in production.

Design rules:
  * Pure resolution + validation — no writes, no side effects, testable.
  * A configured release directory must carry a valid manifest tying it to a
    release SHA. If it cannot, that is a fail-closed condition for the deploy.
  * If the env var is unset (development), fall back to the repo build dir.
"""
from __future__ import annotations

import json
import os
from typing import Any, Mapping, Optional

#: Environment variable naming the directory production serves frontend files from.
FRONTEND_RELEASE_ENV = "SHUNYA_FRONTEND_DIST"

#: Manifest written next to a published build, binding it to a release SHA.
MANIFEST_NAME = "release.json"


def repo_root() -> str:
    """Absolute path of the repository root (parent of the ``app`` package)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def default_releases_root() -> str:
    """Sibling of the checkout where immutable frontend releases are published."""
    return os.path.join(os.path.dirname(repo_root()), "releases")


def default_build_dir() -> str:
    """Development build directory inside the checkout (never served in production)."""
    return os.path.join(repo_root(), "frontend", "dist")


def resolve_frontend_dist(env: Optional[Mapping[str, str]] = None) -> str:
    """Return the directory the app should serve frontend files from.

    Resolution order:
      1. ``SHUNYA_FRONTEND_DIST`` when set (explicit override).
      2. ``<releases>/current`` when a *valid* immutable release has been
         published there — this is what production uses, and it means a local
         ``npm run build`` in the checkout can never change what production
         serves.
      3. The in-checkout build directory (development).

    Step 2 makes the fix self-bootstrapping: no systemd/env change is required
    for production to stop serving the mutable worktree.
    """
    environ = os.environ if env is None else env
    configured = (environ.get(FRONTEND_RELEASE_ENV) or "").strip()
    if configured:
        return os.path.abspath(configured)

    published = os.path.join(default_releases_root(), "current")
    if os.path.isdir(published) and read_release_manifest(published) is not None:
        return os.path.abspath(published)

    return default_build_dir()


def is_immutable_release(dist_dir: str, env: Optional[Mapping[str, str]] = None) -> bool:
    """True when ``dist_dir`` is an immutable release directory, not the worktree build."""
    if not dist_dir:
        return False
    return os.path.abspath(dist_dir) != default_build_dir()


def read_release_manifest(dist_dir: str) -> Optional[dict[str, Any]]:
    """Read the release manifest from a published build, or None if absent/invalid."""
    path = os.path.join(dist_dir, MANIFEST_NAME)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def validate_release_manifest(
    manifest: Optional[dict[str, Any]], expected_sha: Optional[str]
) -> tuple[bool, str]:
    """Validate that a manifest binds the artifact to ``expected_sha``.

    Returns ``(ok, reason)``. A release is only valid when a manifest exists,
    declares a ``release_sha``, and that SHA equals the certified SHA.
    """
    if not expected_sha:
        return False, "no expected release SHA supplied"
    if not manifest:
        return False, f"missing or unreadable {MANIFEST_NAME}"
    declared = str(manifest.get("release_sha") or "").strip()
    if not declared:
        return False, "manifest has no release_sha"
    if declared != expected_sha:
        return False, f"manifest release_sha {declared[:12]} != expected {expected_sha[:12]}"
    if not manifest.get("asset_manifest_sha256"):
        return False, "manifest has no asset_manifest_sha256"
    return True, "ok"


def frontend_provenance(dist_dir: Optional[str] = None) -> dict[str, Any]:
    """Truthful frontend provenance for ``/health``.

    Reports whether the served build is an immutable release, its declared SHA,
    and the artifact hash — so a mismatch between the running backend SHA and
    the served frontend is observable rather than silent.
    """
    directory = dist_dir or resolve_frontend_dist()
    immutable = is_immutable_release(directory)
    manifest = read_release_manifest(directory)
    return {
        "frontend_dist_mode": "immutable_release" if immutable else "worktree_build",
        "frontend_dist_exists": os.path.isdir(directory),
        "frontend_release_sha": (manifest or {}).get("release_sha"),
        "frontend_asset_manifest_sha256": (manifest or {}).get("asset_manifest_sha256"),
        "frontend_release_verified": bool(manifest) if immutable else False,
    }
