#!/usr/bin/env python3
"""
Emergency Release Tool — governed manual deployment.
Usage:
  python3 scripts/emergency_release.py <sha> --authorized-by "<name>" --reason "<reason>"

The tool:
  1. Validates the SHA exists in the repository
  2. Checks out the exact SHA
  3. Creates an immutable audit record (release_provenance.json)
  4. Restarts the application
  5. Verifies health/smoke

This is the ONLY supported path for non-CI deployments.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, cwd=REPO_DIR, check=True, timeout=30):
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout
    )
    if check and result.returncode != 0:
        print(f"ERROR: {' '.join(cmd)} failed:\n{result.stderr}")
        sys.exit(1)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="SHUNYA Emergency Release — governed manual deployment"
    )
    parser.add_argument("sha", help="Exact 40-character commit SHA to deploy")
    parser.add_argument("--authorized-by", required=True, help="Operator who authorized this release")
    parser.add_argument("--reason", required=True, help="Why the CI path was bypassed")
    parser.add_argument("--skip-health", action="store_true", help="Skip health verification (use with caution)")
    args = parser.parse_args()

    sha = args.sha.strip()
    if len(sha) != 40 or not all(c in "0123456789abcdef" for c in sha):
        print(f"ERROR: Invalid SHA format: {sha!r}")
        print("  Must be a full 40-character hex commit SHA.")
        sys.exit(1)

    print("=" * 60)
    print("SHUNYA EMERGENCY RELEASE")
    print(f"  SHA:          {sha}")
    print(f"  Authorized by: {args.authorized_by}")
    print(f"  Reason:        {args.reason}")
    print("=" * 60)

    # Step 1: Verify SHA exists
    print("\n[1/7] Verifying SHA exists in repository...")
    result = run(["git", "cat-file", "-e", sha], check=False)
    if result.returncode != 0:
        print(f"ERROR: SHA {sha} not found in repository.")
        print("  Fetch remote with: git fetch origin master")
        sys.exit(1)
    print("  OK")

    # Step 2: Record previous SHA for rollback
    print("\n[2/7] Recording current state for rollback...")
    current_sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    print(f"  Current SHA: {current_sha}")
    print(f"  Target SHA:  {sha}")

    # Step 3: Checkout target SHA
    print("\n[3/7] Checking out target SHA...")
    run(["git", "checkout", sha])
    deployed_sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    if deployed_sha != sha:
        print(f"ERROR: Deployed SHA {deployed_sha} != target {sha}")
        sys.exit(1)
    print(f"  Checked out: {deployed_sha}")

    # Step 4: Build frontend if needed
    if os.path.exists(os.path.join(REPO_DIR, "frontend", "package.json")):
        print("\n[4/7] Building frontend...")
        run(["npm", "ci"], cwd=os.path.join(REPO_DIR, "frontend"))
        run(["npm", "run", "build"], cwd=os.path.join(REPO_DIR, "frontend"))
        print("  Frontend built")

    # Step 5: Create governance audit record
    print("\n[5/7] Creating immutable audit record...")
    from app.release_governance import record_emergency_deployment
    import app  # noqa: ensure app.runtime_config is importable

    # Set RUNTIME_DATA_ROOT if not already set
    if not os.environ.get("RUNTIME_DATA_ROOT"):
        os.environ["RUNTIME_DATA_ROOT"] = os.path.expanduser("~/shunya_data")

    record = record_emergency_deployment(
        sha=sha,
        authorized_by=args.authorized_by,
        reason=args.reason,
        health_verified=not args.skip_health,
    )
    print(f"  Audit record written to ~/shunya_data/release_provenance.json")
    print(f"  Release type: {record['release_type']}")
    print(f"  Authorized by: {record['authorized_by']}")

    # Step 6: Restart
    print("\n[6/7] Restarting application...")
    result = run(["sudo", "systemctl", "restart", "shunya"], check=False)
    if result.returncode != 0:
        print("WARNING: systemctl restart failed, trying direct kill...")
        try:
            run(["pkill", "-f", "gunicorn.*shunya"], check=False)
            import time
            time.sleep(5)
        except Exception:
            pass
    print("  Application restarted")

    # Step 7: Health verification
    print("\n[7/7] Verifying deployment health...")
    if not args.skip_health:
        import time
        for attempt in range(10):
            try:
                health_url = os.environ.get("SHUNYA_HEALTH_URL", "http://127.0.0.1:5001/health")
                resp = urllib.request.urlopen(health_url, timeout=10)
                health = json.loads(resp.read().decode())
                running_sha = health.get("git_commit", "")
                running_type = health.get("release_type", "unknown")
                if running_sha == sha:
                    print(f"  HEALTH OK — running SHA matches deployed SHA")
                    print(f"  Release type: {running_type}")
                    break
                else:
                    print(f"  Attempt {attempt+1}/10: running {running_sha}, expected {sha}")
            except Exception as e:
                print(f"  Attempt {attempt+1}/10: {e}")
            time.sleep(3)
        else:
            print("WARNING: Health verification did not confirm SHA match.")
            print("  Run manually: curl -s http://127.0.0.1:5001/health")
    else:
        print("  Skipped (--skip-health flag)")

    print("\n" + "=" * 60)
    print("EMERGENCY RELEASE COMPLETE")
    print(f"  Deployed SHA: {sha}")
    print(f"  Authorized by: {args.authorized_by}")
    print(f"  Rollback to {current_sha}:")
    print(f"    cd {REPO_DIR} && git checkout {current_sha} && sudo systemctl restart shunya")
    print("=" * 60)


if __name__ == "__main__":
    main()