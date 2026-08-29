#!/usr/bin/env python3
"""
SHUNYA Production Smoke Test — verifies a running deployment is healthy.

Usage:
  python3 scripts/smoke_test.py                          # localhost:5001
  python3 scripts/smoke_test.py --url https://shunya.io  # remote
  python3 scripts/smoke_test.py --sha abc1234            # verify specific SHA

Returns exit code 0 if all checks pass, 1 on any failure.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "app/__init__.py",
    "app/auth_routes.py",
    "app/models.py",
    "requirements.txt",
    "pytest.ini",
    "infrastructure/scripts/deploy.sh",
    "scripts/emergency_release.py",
]

REQUIRED_ENDPOINTS = [
    "/health",
    "/auth/login",
    "/api/v1/auth/signup",
]

CHECK_PASS = 0
CHECK_FAIL = 1
total_checks = 0
passed_checks = 0
failed_checks = 0


def check(description, condition, detail=""):
    global total_checks, passed_checks, failed_checks
    total_checks += 1
    if condition:
        passed_checks += 1
        print(f"  ✓ {description}")
    else:
        failed_checks += 1
        print(f"  ✗ {description}" + (f" — {detail}" if detail else ""))


def get_health(base_url, timeout=10):
    """Fetch the /health endpoint and return parsed JSON."""
    url = f"{base_url.rstrip('/')}/health"
    req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def fetch_endpoint(base_url, path, timeout=10):
    """Fetch any endpoint and return (status_code, body_dict or None)."""
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = body
        resp.close()
        return (resp.status, data)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = body
        return (e.code, data)
    except Exception as e:
        return (0, {"error": str(e)})


def verify_release_provenance(expected_sha=None):
    """Check the immutable release provenance file."""
    runtime_root = os.environ.get(
        "RUNTIME_DATA_ROOT", os.path.expanduser("~/shunya_data")
    )
    provenance_path = Path(runtime_root) / "release_provenance.json"
    if not provenance_path.exists():
        check("Release provenance file exists", False, f"not found at {provenance_path}")
        return

    try:
        with open(provenance_path) as f:
            records = json.load(f)
        if not isinstance(records, list):
            check("Release provenance is a list", False, "expected list of records")
            return
        if len(records) == 0:
            check("Release provenance has records", False, "empty list")
            return
        last = records[-1]
        check("Release provenance has git_commit", "git_commit" in last)
        check("Release provenance has release_type", "release_type" in last)
        check("Release provenance has timestamp", "timestamp" in last)
        if expected_sha and last.get("git_commit"):
            check(
                f"Release provenance SHA matches expected ({expected_sha[:8]}...)",
                last["git_commit"] == expected_sha,
                f"provenance has {last['git_commit'][:8] if last['git_commit'] else 'None'}"
            )
    except (json.JSONDecodeError, OSError) as e:
        check("Release provenance is readable", False, str(e))


def run_smoke_tests(base_url, expected_sha=None):
    global total_checks, passed_checks, failed_checks
    total_checks = 0
    passed_checks = 0
    failed_checks = 0

    title = f"SHUNYA Production Smoke Test — {base_url}"
    print("=" * len(title))
    print(title)
    print("=" * len(title))
    print()

    # ── Section 1: Repository integrity ──
    print("[1/5] Repository integrity")
    print("-" * 40)
    for f in REQUIRED_FILES:
        check(f"Required file exists: {f}", (REPO_DIR / f).exists())
    git_dir = REPO_DIR / ".git"
    check("Git repository exists", git_dir.is_dir())
    print()

    # ── Section 2: Health endpoint ──
    print("[2/5] Health endpoint")
    print("-" * 40)
    health = get_health(base_url)
    if "error" in health:
        check("Health endpoint reachable", False, health["error"])
    else:
        check("Health endpoint returns 200", True)
        check("Health status is 'ok'", health.get("status") == "ok", str(health.get("status")))
        check("Health has 'database' field", "database" in health)
        check("Health has 'git_commit' field", "git_commit" in health)
        check("Health has 'release_type' field", "release_type" in health)
        check("Health has 'release_deployed_at' field", "release_deployed_at" in health)
        check("Health has 'uptime_seconds' field", "uptime_seconds" in health)
        db_status = health.get("database", "unknown")
        check("Database connected", db_status == "connected" or db_status is True, str(db_status))
        check("Release type is ci_certified or emergency_manual",
              health.get("release_type", "").lower() in ("ci_certified", "emergency_manual"),
              str(health.get("release_type")))
        running_sha = health.get("git_commit", "")
        if expected_sha and running_sha:
            check(
                f"Running SHA matches expected ({expected_sha[:8]}...)",
                running_sha == expected_sha,
                f"running has {running_sha[:8]}"
            )
    print()

    # ── Section 3: API endpoints ──
    print("[3/5] Key API endpoints")
    print("-" * 40)
    for ep in REQUIRED_ENDPOINTS:
        status, body = fetch_endpoint(base_url, ep)
        # Most endpoints require auth — 401 is acceptable for smoke test
        expected = "reachable" if status in (200, 401) else False
        check(
            f"Endpoint {ep} responds (got HTTP {status})",
            expected,
            str(body)[:100] if not expected else ""
        )
    # Check /health specifically
    status, body = fetch_endpoint(base_url, "/health")
    check("Health endpoint responds", status == 200, f"HTTP {status}")
    print()

    # ── Section 4: Release provenance ──
    print("[4/5] Release provenance")
    print("-" * 40)
    verify_release_provenance(expected_sha)
    print()

    # ── Section 5: Build consistency ──
    print("[5/5] Build consistency")
    print("-" * 40)
    # Check frontend build
    frontend_dist = REPO_DIR / "frontend" / "dist"
    if frontend_dist.is_dir():
        index_html = frontend_dist / "index.html"
        check("Frontend build exists (dist/index.html)", index_html.is_file())
    else:
        check("Frontend dist directory", False, "not built — run: cd frontend && npm run build")
    # Check virtualenv
    venv = REPO_DIR / ".venv"
    if venv.is_dir():
        python_bin = venv / "bin" / "python3"
        check("Virtualenv exists", python_bin.is_file())
        pip_list = venv / "bin" / "pip"
        check("pip available in venv", pip_list.is_file())
    else:
        check("Virtualenv exists", False, "not found — run: python3 -m venv .venv")
    print()

    # ── Summary ──
    print("=" * 40)
    print(f"RESULTS: {passed_checks}/{total_checks} passed, {failed_checks}/{total_checks} failed")
    print("=" * 40)

    return CHECK_PASS if failed_checks == 0 else CHECK_FAIL


def main():
    parser = argparse.ArgumentParser(
        description="SHUNYA Production Smoke Test — verifies deployment health"
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("SHUNYA_HEALTH_URL", "http://127.0.0.1:5001"),
        help="Base URL of the running SHUNYA instance (default: http://127.0.0.1:5001)",
    )
    parser.add_argument(
        "--sha",
        default=None,
        help="Expected git SHA to verify against health endpoint and provenance",
    )
    args = parser.parse_args()

    # If no SHA given, try to detect from HEAD
    if not args.sha:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=REPO_DIR, timeout=10
            )
            if result.returncode == 0:
                args.sha = result.stdout.strip()
                print(f"Using HEAD SHA: {args.sha[:8]}...")
        except Exception:
            pass

    exit_code = run_smoke_tests(args.url, expected_sha=args.sha)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()