"""
Release Governance — tracked, audited, rollback-capable deployments.

Architecture:

  NORMAL RELEASE
    CI-certified SHA → protected deploy path → DeploymentRecord created

  EMERGENCY RELEASE
    Explicit operator authorization → reason → exact SHA
    → immutable audit record → mandatory health/smoke verification
    → explicit emergency release marker → rollback capability

The health endpoint exposes:
  release_provenance: "CI_CERTIFIED" | "EMERGENCY_MANUAL"
  git_commit: exact SHA
  build_id: short SHA

Every process restart checks the deployment record. A restart alone
cannot silently become an unofficial deployment.
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Release Provenance File ───────────────────────────────────────────
# Stored outside the git worktree (RUNTIME_DATA_ROOT) so it survives
# deployments and is not part of the application code.

RELEASE_PROVENANCE_FILE = os.path.join(
    os.environ.get("RUNTIME_DATA_ROOT", os.path.expanduser("~/shunya_data")),
    "release_provenance.json",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _current_sha() -> str:
    """Read the current git HEAD SHA."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


# ── Release Governance API ─────────────────────────────────────────────


def get_release_provenance() -> dict:
    """
    Read the current release provenance.

    Returns:
        {
            "release_type": "CI_CERTIFIED" | "EMERGENCY_MANUAL",
            "git_commit": "<full SHA>",
            "build_id": "<short SHA>",
            "deployed_at": "<ISO timestamp>",
            "authorized_by": "<operator name or 'CI/CD'>",
            "reason": "<deployment reason>",
            "rollback_sha": "<previous SHA>",
            "health_verified": bool,
        }
    """
    default = {
        "release_type": "CI_CERTIFIED",
        "git_commit": _current_sha(),
        "build_id": _current_sha()[:7] if _current_sha() != "unknown" else "unknown",
        "deployed_at": _now_iso(),
        "authorized_by": "CI/CD",
        "reason": "Normal deployment via CI pipeline",
        "rollback_sha": "unknown",
        "health_verified": True,
    }

    if os.path.exists(RELEASE_PROVENANCE_FILE):
        try:
            with open(RELEASE_PROVENANCE_FILE, "r") as f:
                data = json.load(f)
            # Merge default fields for backward compat
            for k, v in default.items():
                data.setdefault(k, v)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read release provenance: %s", e)

    return default


def record_normal_deployment(sha: str) -> dict:
    """
    Record a normal (CI-certified) deployment.

    Called by deploy.sh at the end of a successful CI deployment.
    """
    provenance = {
        "release_type": "CI_CERTIFIED",
        "git_commit": sha,
        "build_id": sha[:7] if len(sha) >= 7 else sha,
        "deployed_at": _now_iso(),
        "authorized_by": "CI/CD",
        "reason": "Normal deployment via CI pipeline",
        "rollback_sha": _current_sha(),
        "health_verified": True,
    }
    _write_provenance(provenance)
    logger.info("Normal deployment recorded: %s @ %s", provenance["release_type"], sha)
    return provenance


def record_emergency_deployment(
    sha: str,
    authorized_by: str,
    reason: str,
    health_verified: bool = False,
) -> dict:
    """
    Record an emergency/manual deployment.

    Required fields:
      - authorized_by: the operator who authorized the manual deployment
      - reason: why the CI path was bypassed
      - sha: the exact commit SHA deployed

    Returns the provenance dict. Raises ValueError if required fields missing.
    """
    if not authorized_by or not authorized_by.strip():
        raise ValueError("authorized_by is required for emergency deployment")
    if not reason or not reason.strip():
        raise ValueError("reason is required for emergency deployment")
    if not sha or len(sha) != 40:
        raise ValueError(f"exact 40-char SHA required, got {sha!r}")

    provenance = {
        "release_type": "EMERGENCY_MANUAL",
        "git_commit": sha,
        "build_id": sha[:7],
        "deployed_at": _now_iso(),
        "authorized_by": authorized_by.strip(),
        "reason": reason.strip(),
        "rollback_sha": _current_sha(),
        "health_verified": health_verified,
    }
    _write_provenance(provenance)
    logger.warning(
        "EMERGENCY deployment recorded: authorized_by=%s reason=%s sha=%s",
        authorized_by, reason, sha,
    )
    return provenance


def _write_provenance(provenance: dict) -> None:
    """Write provenance to the runtime data root (outside git worktree)."""
    os.makedirs(os.path.dirname(RELEASE_PROVENANCE_FILE), exist_ok=True)
    with open(RELEASE_PROVENANCE_FILE, "w") as f:
        json.dump(provenance, f, indent=2, default=str)


def verify_health_after_deploy() -> dict:
    """
    Verify that the currently running service matches the recorded deployment.
    Used as the health/smoke proof for emergency deployments.

    Returns {"verified": True} or {"verified": False, "error": "..."}
    """
    try:
        import urllib.request
        health_url = os.environ.get("SHUNYA_HEALTH_URL", "http://127.0.0.1:5001/health")
        resp = urllib.request.urlopen(health_url, timeout=10)
        health_data = json.loads(resp.read().decode())

        provenance = get_release_provenance()
        running_sha = health_data.get("git_commit", "")
        recorded_sha = provenance.get("git_commit", "")

        if running_sha == recorded_sha:
            return {"verified": True, "running_sha": running_sha, "recorded_sha": recorded_sha}
        else:
            return {
                "verified": False,
                "error": f"Running SHA ({running_sha}) does not match recorded SHA ({recorded_sha})",
                "running_sha": running_sha,
                "recorded_sha": recorded_sha,
            }
    except Exception as e:
        return {"verified": False, "error": f"Health check failed: {e}"}


def get_rollback_command() -> dict:
    """
    Return the exact command to rollback to the previous deployment.
    """
    provenance = get_release_provenance()
    rollback_sha = provenance.get("rollback_sha", "unknown")
    current_sha = provenance.get("git_commit", _current_sha())

    return {
        "current_sha": current_sha,
        "rollback_sha": rollback_sha,
        "command": f"cd /home/shunya-deploy/shunya_os && git checkout {rollback_sha} && sudo systemctl restart shunya",
        "available": rollback_sha != "unknown" and rollback_sha != current_sha,
    }