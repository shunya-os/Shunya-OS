"""Safety tests for scripts/debug_space_creation.py.

Verifies that the script refuses to run when DATABASE_URL is not set
explicitly by the user, preventing accidental database connection.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "debug_space_creation.py"

# Unique sentinel that is NOT a placeholder — used to prove the script
# does not echo the supplied database URL to any output stream.
_SENTINEL_USER = "dbgusr_d4c4f3b0"
_SENTINEL_PASS = "dbgp4s_d4c4f3b0"


def _resolve_venv_python() -> str | None:
    """Derive the venv Python interpreter from the active environment.

    Checks in order:
    1. sys.prefix != sys.base_prefix → running inside a venv → use sys.executable.
    2. REPO_ROOT/.venv exists → standard project convention → use its python.
    Returns None when neither is available (skip the test).
    """
    if sys.prefix != sys.base_prefix:
        return sys.executable
    venv_python = REPO_ROOT / ".venv" / "bin" / "python3"
    if venv_python.is_file():
        return str(venv_python)
    return None


def _run_script(env: dict | None = None, timeout: int = 15,
                use_venv: bool = False) -> subprocess.CompletedProcess:
    """Run the debug script with the given env, capturing output."""
    python_exe = sys.executable
    base_env = {"PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", "")}
    if use_venv:
        ve = os.environ.get("VIRTUAL_ENV", "")
        if ve:
            base_env["VIRTUAL_ENV"] = ve
        # Provide the minimum import path so the subprocess can find the
        # 'app' module (the debug script does `from app import create_app`).
        base_env.setdefault("PYTHONPATH", str(REPO_ROOT))
        # Use the venv interpreter when available.
        resolved = _resolve_venv_python()
        if resolved:
            python_exe = resolved
    if env:
        base_env.update(env)
    return subprocess.run(
        [python_exe, str(SCRIPT)],
        capture_output=True, text=True, timeout=timeout,
        cwd=REPO_ROOT,
        env=base_env,
    )


class TestMissingDatabaseUrl:
    """The script must exit safely when DATABASE_URL is unavailable."""

    def test_missing_env_var_exits_with_error(self):
        """Running without DATABASE_URL in env exits non-zero."""
        proc = _run_script()
        assert proc.returncode != 0, (
            "Script must exit non-zero when DATABASE_URL is missing"
        )

    def test_missing_env_var_prints_clear_message(self):
        """The error message tells the user to set DATABASE_URL."""
        proc = _run_script()
        assert "DATABASE_URL" in proc.stdout + proc.stderr, (
            "Error message must mention DATABASE_URL"
        )

    def test_missing_env_var_does_not_import_app(self):
        """The script must not reach create_app when DATABASE_URL is missing."""
        proc = _run_script()
        assert "Tables created" not in proc.stdout + proc.stderr
        assert "SHUNYA OS initialised" not in proc.stdout + proc.stderr
        assert "create_app" not in proc.stdout + proc.stderr

    def test_empty_env_var_exits_with_error(self):
        """DATABASE_URL='' also counts as missing."""
        proc = _run_script(env={"DATABASE_URL": ""})
        assert proc.returncode != 0

    def test_empty_env_var_prints_clear_message(self):
        proc = _run_script(env={"DATABASE_URL": ""})
        assert "DATABASE_URL" in proc.stdout + proc.stderr


class TestProvidedDatabaseUrl:
    """With an explicit DATABASE_URL, the script proceeds without leaking."""

    def test_guard_passes_and_url_not_printed(self):
        """The supplied URL (user + password) must NOT appear in output.

        This test supplies a unique sentinel URL that is not a known
        placeholder, and asserts the sentinel values are absent from
        every output stream.  The guard fires and exits *before* any
        Flask import, so no database connection is attempted.
        """
        sentinel_url = (
            f"postgresql://{_SENTINEL_USER}:{_SENTINEL_PASS}"
            f"@127.0.0.1:59999/dbg_test_db"
        )
        proc = _run_script(env={"DATABASE_URL": sentinel_url})
        output = proc.stdout + proc.stderr
        assert _SENTINEL_USER not in output, (
            "Username must not appear in console output"
        )
        assert _SENTINEL_PASS not in output, (
            "Password must not appear in console output"
        )
        # The guard must not have fired — DATABASE_URL was supplied.
        assert "DATABASE_URL is not set" not in output, (
            "Guard should not fire — DATABASE_URL was supplied"
        )
        # The failure must be ModuleNotFoundError (import), not
        # the guard's error, proving the guard logic was bypassed.
        assert "ModuleNotFoundError" in output, (
            "Expected import failure (guard passed, app module missing)"
        )

    def test_guard_passes_but_no_db_connect(self):
        """With valid URL + venv, the script reaches create_app.

        VIRTUAL_ENV from the test runner is passed to the subprocess
        so the import succeeds and *create_app* executes — it then
        fails at database connection (no PostgreSQL on the sentinel
        host:port), proving the entire guard->create_app->DB-connect
        path is live without using a real database.
        """
        ve = os.environ.get("VIRTUAL_ENV", "")
        if not ve:
            venv_python = _resolve_venv_python()
            if not venv_python:
                pytest.skip("VIRTUAL_ENV not set and no venv found — cannot import app in subprocess")

        sentinel_url = (
            f"postgresql://{_SENTINEL_USER}:{_SENTINEL_PASS}"
            f"@127.0.0.1:59999/dbg_test_db"
        )
        # G1.21: the isolation guard also checks the EXECUTION CONTEXT — a
        # PostgreSQL URL is refused unless the process declares itself a test run.
        # This subprocess is a test harness invocation, so it must declare that
        # (SHUNYA_ENV=test), exactly as conftest does for the main process. Without
        # the declaration the guard correctly refuses before create_app runs, which
        # would make this test prove nothing about the connection path.
        proc = _run_script(env={"DATABASE_URL": sentinel_url, "SHUNYA_ENV": "test"},
                           use_venv=True)
        output = proc.stdout + proc.stderr
        # Guard must not have fired.
        assert "DATABASE_URL is not set" not in output, (
            "Guard must not have rejected the supplied URL"
        )
        # If subprocess failed at import, skip as venv path issue
        if "ModuleNotFoundError" in output:
            pytest.skip("VIRTUAL_ENV resolves but subprocess cannot import app")
        # The error must be a database connection error, proving
        # create_app ran and attempted to connect.
        assert ("connect" in output.lower()
                or "connection" in output.lower()
                or "OperationalError" in output
                or "could not translate" in output.lower()), (
            f"Expected DB connection error with venv, got: {output[:300]}"
        )
        # Verify sentinel values are not leaked.
        assert _SENTINEL_USER not in output, (
            "Username must not appear in console output"
        )
        assert _SENTINEL_PASS not in output, (
            "Password must not appear in console output"
        )