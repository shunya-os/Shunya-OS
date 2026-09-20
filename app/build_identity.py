"""Immutable build identity — the identity of the LOADED artifact.

Why this module exists
----------------------
``/health`` used to derive ``git_commit`` from ``git rev-parse HEAD`` — mutable
checkout state visible to whatever worker happens to answer. Gunicorn recycles
workers (``--max-requests``), and each recycled worker re-imports the
application. If the checkout moves without a deployment, workers can therefore
report a SHA that no immutable release corresponds to, and the running process
can be a mix of versions.

A certified deployment writes an immutable identity record at deploy time
(``deploy.sh`` step 13). The application reads it and reports:

    backend_release_sha   — the SHA whose code was published by the deploy
    frontend_release_sha  — the immutable frontend release serving that SHA

When the record exists and disagrees with the SHA this process loaded, the
running artifact does NOT correspond to the certified deployment. That is
reported truthfully (``build_identity_matches_running_build = false`` and a
degraded status) rather than being smoothed over.

The record is evidence, never authority: it is read only, and a missing record
is reported as absent rather than invented.
"""
from __future__ import annotations

import json
import os

BUILD_IDENTITY_FILE = os.path.join(
    os.environ.get("RUNTIME_DATA_ROOT", os.path.expanduser("~/shunya_data")),
    "build_identity.json",
)


def build_identity() -> dict | None:
    """Return the deploy-time identity record, or None when absent/invalid."""
    try:
        with open(BUILD_IDENTITY_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def identity_mismatch(running_sha: str, identity: dict | None) -> bool:
    """True when the loaded build does not match the certified deployment.

    A missing record is NOT a mismatch: absence means "no deployment record on
    this host", which is a different condition from "the record disagrees".
    """
    if not identity:
        return False
    recorded = (identity.get("backend_release_sha") or "").strip()
    running = (running_sha or "").strip()
    if not recorded or not running:
        return False
    return recorded != running
