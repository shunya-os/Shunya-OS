"""SHUNYA Deployment Diagnostic Service.

Provides machine-readable release evidence so production failures
are diagnosable without SSH archaeology.
"""
import os
import subprocess
import json
import time
from datetime import datetime, timezone
from flask import Blueprint, jsonify

deploy_bp = Blueprint("deploy_diagnostics", __name__, url_prefix="/api/v1/deploy")


def _run(cmd, timeout=10):
    """Run a shell command and return stdout/stderr."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=os.path.dirname(os.path.dirname(__file__)))
        return {"exit_code": r.returncode, "stdout": r.stdout[:2000], "stderr": r.stderr[:1000]}
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": f"timeout ({timeout}s)"}
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}


@deploy_bp.route("/status", methods=["GET"])
def deployment_status():
    """Return machine-readable deployment diagnostic evidence."""
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Git info
    head = _run("git rev-parse HEAD")
    origin = _run("git rev-parse origin/master")
    branch = _run("git branch --show-current")
    status = _run("git status --porcelain")
    log = _run("git log --oneline -5 HEAD")
    
    # Health check
    health = {"status": "unreachable"}
    try:
        import requests
        r = requests.get("http://127.0.0.1:5001/health", timeout=5)
        health = r.json() if r.status_code == 200 else {"status": f"HTTP {r.status_code}"}
    except Exception as e:
        health = {"status": f"error: {str(e)}"}
    
    # Service status
    service = _run("systemctl status shunya 2>&1 | head -10" if os.system("which systemctl >/dev/null 2>&1") == 0 else "ps aux | grep gunicorn | grep -v grep | head -5")
    
    # Dependencies
    pip_list = _run("pip list --format=columns 2>/dev/null | head -20")
    
    # Migration
    migration = _run("alembic current 2>/dev/null" if os.path.exists(os.path.join(repo_dir, "alembic.ini")) else "echo 'no alembic.ini'")
    
    # .env check
    env_present = os.path.exists(os.path.join(repo_dir, ".env"))
    
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git": {
            "head": head.get("stdout", "").strip(),
            "origin_master": origin.get("stdout", "").strip(),
            "branch": branch.get("stdout", "").strip(),
            "origin_parity": "MATCH" if head.get("stdout", "").strip() == origin.get("stdout", "").strip() else "MISMATCH",
            "dirty": bool(status.get("stdout", "").strip()),
            "recent_commits": log.get("stdout", "").strip(),
        },
        "production": {
            "health": health,
            "service": service.get("stdout", "")[:500],
            "deployed_sha": health.get("git_commit", ""),
            "build_id": health.get("build_id", ""),
        },
        "environment": {
            "env_file_present": env_present,
            "python": _run("python3 --version").get("stdout", "").strip(),
            "dependencies": pip_list.get("stdout", ""),
        },
        "migration": {
            "current": migration.get("stdout", "").strip(),
        },
    }
    
    return jsonify(result)


@deploy_bp.route("/health", methods=["GET"])
def health():
    """Health check for the diagnostic endpoint."""
    return jsonify({
        "status": "ok",
        "service": "deploy-diagnostics",
    })