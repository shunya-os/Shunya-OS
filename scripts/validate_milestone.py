#!/usr/bin/env python3
"""
SHUNYA Milestone Closure Validator — Part of the Execution Integrity system.

Validates as much as can be mechanically verified for a given milestone.
FAILS CLOSED: unknown status ≠ PASS.

Usage:
    python scripts/validate_milestone.py G1.1-R1
    python scripts/validate_milestone.py --all       # Validate all tracked milestones
    python scripts/validate_milestone.py --ci         # CI-friendly output (exit codes)
"""

import json
import os
import re
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MILESTONE_TRACKER = REPO_ROOT / "governance" / "milestone_tracker.yaml"
EXECUTION_INTEGRITY = REPO_ROOT / "governance" / "execution_integrity.yaml"
REQUIRED_EVIDENCE_DIR = REPO_ROOT / "governance" / "verification" / "milestones"


def eprint(*args: Any, **kwargs: Any) -> None:
    print(*args, file=sys.stderr, **kwargs)


def sh(cmd: str, check: bool = False) -> str:
    """Run a shell command, return stdout, don't raise on non-zero by default."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=REPO_ROOT)
        if check and r.returncode != 0:
            eprint(f"  WARN: command failed (rc={r.returncode}): {cmd}")
            eprint(f"  stderr: {r.stderr[:500]}")
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return f"TIMEOUT"
    except Exception as e:
        return f"ERROR({e})"


def check_git_state() -> dict:
    """Check working tree, HEAD, remote."""
    result = {}
    head = sh("git rev-parse HEAD")
    result["local_head"] = head if head else "UNKNOWN"

    # Check remote — use current branch's upstream
    current_branch = sh("git rev-parse --abbrev-ref HEAD")
    if current_branch and current_branch != "HEAD":
        remote = sh(f"git rev-parse origin/{current_branch} 2>/dev/null")
    else:
        remote = sh("git rev-parse origin/main 2>/dev/null || git rev-parse origin/master 2>/dev/null")
    result["remote_head"] = remote if remote else "UNKNOWN"

    dirty = sh("git status --porcelain")
    result["working_tree_dirty"] = bool(dirty)
    result["dirty_files"] = dirty.split("\n") if dirty else []

    # HEAD == remote?
    if head and remote and head == remote:
        result["head_matches_remote"] = True
    else:
        result["head_matches_remote"] = False

    return result


def check_db_migrations() -> dict:
    """Check alembic migration state."""
    result = {}
    try:
        result["alembic_head"] = sh("cd /home/shunya-deploy/shunya_os && python3 -c \"from alembic.config import Config; from alembic.script import ScriptDirectory; cfg = Config('alembic.ini'); script = ScriptDirectory.from_config(cfg); print(script.get_heads()[0])\"")
    except Exception as e:
        result["alembic_head"] = f"ERROR({e})"
    return result


def check_files_exist(paths: list) -> dict:
    """Verify required files exist."""
    result = {}
    for p in paths:
        result[p] = Path(REPO_ROOT / p).exists()
    return result


def load_milestone_tracker() -> dict:
    """Load the milestone tracker YAML."""
    if MILESTONE_TRACKER.exists():
        try:
            with open(MILESTONE_TRACKER) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            return {"error": str(e)}
    return {}


def validate_execution_principle() -> dict:
    """Check that the final execution principle is encoded in the constitution."""
    constitution_path = REPO_ROOT / "docs/governance" / "SHUNYA_EXECUTION_INTEGRITY_CONSTITUTION.md"
    if not constitution_path.exists():
        return {"status": "FAIL", "detail": "Constitution file not found"}
    content = constitution_path.read_text()
    checks = {}
    checks["rule_0_present"] = "## Rule 0" in content
    checks["build_prove_challenge_fix_close"] = "BUILD IT. PROVE IT. CHALLENGE IT. FIX IT. THEN CLOSE IT." in content
    checks["never_build_test_declare"] = "Build it → test it → declare it done." in content
    all_pass = all(checks.values())
    return {
        "status": "PASS" if all_pass else "FAIL",
        "detail": "Checks: " + ", ".join(f"{k}: {'✓' if v else '✗'}" for k, v in checks.items())
    }


def validate_milestone(milestone_id: str, ci_mode: bool = False) -> dict:
    """
    Validate a single milestone against all mechanical gates.
    Returns dict of check name → {status, detail}.
    """
    results = {}

    # --- Final Execution Principle ---
    principle = validate_execution_principle()
    results["final_execution_principle"] = principle
    milestone_file = REQUIRED_EVIDENCE_DIR / f"{milestone_id}_evidence.yaml"
    results["evidence_file_exists"] = {
        "status": "PASS" if milestone_file.exists() else "FAIL",
        "detail": f"Evidence file at {milestone_file}" if milestone_file.exists() else f"Missing: {milestone_file}"
    }

    # --- Validation config exists ---
    results["execution_integrity_config"] = {
        "status": "PASS" if EXECUTION_INTEGRITY.exists() else "FAIL",
        "detail": "execution_integrity.yaml " + ("found" if EXECUTION_INTEGRITY.exists() else "missing")
    }

    # --- Tracked status ---
    tracker = load_milestone_tracker()
    milestone_data = tracker.get("milestones", {}).get(milestone_id, {})
    status = milestone_data.get("status", "UNVERIFIED")
    valid_statuses = tracker.get("valid_statuses", ["PASS", "FAIL", "BLOCKED", "UNVERIFIED"])

    results["tracker_status"] = {
        "status": status if status in valid_statuses else "INVALID",
        "detail": f"Status: {status} (valid: {status in valid_statuses})"
    }

    # --- Git state ---
    git = check_git_state()
    results["working_tree_clean"] = {
        "status": "PASS" if not git["working_tree_dirty"] else "FAIL",
        "detail": f"Dirty files: {git['dirty_files'][:10]}" if git["working_tree_dirty"] else "Clean working tree"
    }
    results["head_matches_remote"] = {
        "status": "PASS" if git["head_matches_remote"] else "FAIL",
        "detail": f"HEAD: {git['local_head'][:12]} | Remote: {git['remote_head'][:12]}"
    }

    # --- Committed ---
    # Check if there are any uncommitted changes
    results["all_changes_committed"] = {
        "status": "PASS" if not git["working_tree_dirty"] else "FAIL",
        "detail": "All changes committed" if not git["working_tree_dirty"] else f"{len(git['dirty_files'])} uncommitted file(s)"
    }

    # --- Migrations ---
    mig = check_db_migrations()
    results["migration_head_determined"] = {
        "status": "PASS" if "ERROR" not in str(mig.get("alembic_head", "")) else "FAIL",
        "detail": f"Alembic head: {mig.get('alembic_head', 'UNKNOWN')}"
    }

    # --- Verify constitution and governance files exist ---
    required_files = [
        "docs/governance/SHUNYA_EXECUTION_INTEGRITY_CONSTITUTION.md",
        "docs/governance/KNOWN_EXECUTION_FAILURE_PATTERNS.md",
        "governance/execution_integrity.yaml",
        "governance/milestone_tracker.yaml",
        "scripts/validate_milestone.py",
    ]
    file_checks = check_files_exist(required_files)
    all_files_exist = all(file_checks.values())
    results["required_governance_files"] = {
        "status": "PASS" if all_files_exist else "FAIL",
        "detail": ", ".join(f"{k}: {'✓' if v else '✗'}" for k, v in file_checks.items())
    }

    # --- Blocker check from tracker ---
    blockers = milestone_data.get("blockers", [])
    results["unresolved_blockers"] = {
        "status": "PASS" if not blockers else "BLOCKED",
        "detail": f"{len(blockers)} unresolved blockers: {blockers[:5]}" if blockers else "No unresolved blockers"
    }

    # --- Prohibited legacy consumers (if milestone-specific pattern file exists) ---
    pattern_file = REQUIRED_EVIDENCE_DIR / f"{milestone_id}_consumers.txt"
    results["legacy_consumer_check"] = {
        "status": "PASS" if pattern_file.exists() else "UNVERIFIED",
        "detail": "Consumer audit file " + ("present" if pattern_file.exists() else "not found (UNVERIFIED — manual check)")
    }

    # --- Overall ---
    statuses = [v["status"] for v in results.values()]
    if all(s == "PASS" for s in statuses):
        overall = "PASS"
    elif any(s == "FAIL" for s in statuses):
        overall = "FAIL"
    elif any(s == "BLOCKED" for s in statuses):
        overall = "BLOCKED"
    else:
        overall = "UNVERIFIED"

    return {
        "milestone": milestone_id,
        "overall_status": overall,
        "checks": results,
    }


def ci_format(result: dict) -> None:
    """CI-friendly output."""
    print(f"MILESTONE: {result['milestone']}")
    print(f"OVERALL: {result['overall_status']}")
    for check, data in sorted(result["checks"].items()):
        print(f"  [{data['status']:10s}] {check}: {data['detail'][:120]}")
    if result["overall_status"] != "PASS":
        sys.exit(1)


def human_format(result: dict) -> None:
    """Human-readable output."""
    print(f"\n{'='*60}")
    print(f"  Milestone: {result['milestone']}")
    print(f"  Overall:   {result['overall_status']}")
    print(f"{'='*60}")
    for check, data in sorted(result["checks"].items()):
        status = data["status"]
        marker = {"PASS": "✓", "FAIL": "✗", "BLOCKED": "⊘", "UNVERIFIED": "?"}.get(status, "?")
        print(f"  {marker} [{status:10s}] {check}")
        print(f"    {data['detail'][:120]}")
    if result["overall_status"] == "PASS":
        print(f"\n{'='*60}")
        print(f"  ✅ MILESTONE {result['milestone']}: VALIDATED PASS")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"  ❌ MILESTONE {result['milestone']}: {result['overall_status']}")
        print(f"{'='*60}")
        if result["overall_status"] == "FAIL":
            fails = [k for k, v in result["checks"].items() if v["status"] == "FAIL"]
            print(f"  Failed checks: {fails}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    ci_mode = "--ci" in flags
    validate_all = "--all" in flags

    if validate_all:
        tracker = load_milestone_tracker()
        milestones = list(tracker.get("milestones", {}).keys())
        if not milestones:
            eprint("No milestones found in tracker")
            sys.exit(1)
        results = [validate_milestone(m, ci_mode) for m in milestones]
        if ci_mode:
            for r in results:
                ci_format(r)
        else:
            for r in results:
                human_format(r)
        # If any failed, exit 1
        if any(r["overall_status"] != "PASS" for r in results):
            sys.exit(1)
        return

    if not args:
        eprint("Error: milestone ID required")
        eprint(__doc__)
        sys.exit(1)
    milestone_id = args[0].strip()
    if not milestone_id:
        eprint("Milestone ID required")
        sys.exit(1)

    result = validate_milestone(milestone_id, ci_mode)

    if ci_mode:
        ci_format(result)
    else:
        human_format(result)


if __name__ == "__main__":
    main()