"""Safety tests for scripts/test_server.py.

Exercises the REAL guards through subprocess execution (no mocks, no
monkeypatching of the guard logic).  Each test builds an explicit environment
and asserts both the process outcome and the filesystem side effects.

Covered:
- refuses without explicit opt-in (SHUNYA_TEST_SERVER_ALLOWED)
- refuses an inherited production-like DATABASE_URL
- refuses unsafe TEST_DB_PATH values (outside /tmp, bad basename, relative)
- never deletes an unrelated pre-existing file
- removes only its own stale DB at the validated path, and creates a fresh one
- test-only routes are confined to the __main__ entry point
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER = REPO_ROOT / "scripts" / "test_server.py"

_IMPORT_SNIPPET = (
    "import importlib.util, sys;"
    "spec = importlib.util.spec_from_file_location('ts_under_test', sys.argv[1]);"
    "mod = importlib.util.module_from_spec(spec);"
    "spec.loader.exec_module(mod);"
    "print('IMPORT_OK')"
)


def _venv_python() -> str | None:
    if sys.prefix != sys.base_prefix:
        return sys.executable
    vp = REPO_ROOT / ".venv" / "bin" / "python3"
    return str(vp) if vp.is_file() else None


def _run_import(env_extra: dict, timeout: int = 120) -> subprocess.CompletedProcess:
    py = _venv_python()
    if not py:
        pytest.skip("No venv python available to import the test server")
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": str(REPO_ROOT),
    }
    env.update(env_extra)
    return subprocess.run(
        [py, "-c", _IMPORT_SNIPPET, str(SERVER)],
        capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT, env=env,
    )


def _unique_path() -> Path:
    return Path(f"/tmp/shunya_test_server_safety_{uuid.uuid4().hex[:10]}.sqlite")


@pytest.fixture()
def cleanup_paths():
    created: list[Path] = []
    yield created
    for p in created:
        for cand in (p, Path(str(p) + "-wal"), Path(str(p) + "-shm")):
            try:
                if cand.exists():
                    cand.unlink()
            except OSError:
                pass


def test_refuses_without_opt_in(cleanup_paths):
    db = _unique_path()
    cleanup_paths.append(db)
    proc = _run_import({"TEST_DB_PATH": str(db)})
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "SHUNYA_TEST_SERVER_ALLOWED" in out
    assert not db.exists(), "No DB may be created when the opt-in is missing"


def test_refuses_inherited_database_url(cleanup_paths):
    db = _unique_path()
    cleanup_paths.append(db)
    proc = _run_import({
        "SHUNYA_TEST_SERVER_ALLOWED": "true",
        "TEST_DB_PATH": str(db),
        # Deliberately non-SQLite and non-local-pattern; no real credentials.
        "DATABASE_URL": "postgresql://someuser@127.0.0.1:59999/prodlike",
    })
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "DATABASE_URL" in out
    assert not db.exists()


def test_refuses_path_outside_tmp(cleanup_paths):
    db = REPO_ROOT / f"shunya_test_server_{uuid.uuid4().hex[:8]}.sqlite"
    cleanup_paths.append(db)
    proc = _run_import({
        "SHUNYA_TEST_SERVER_ALLOWED": "true",
        "TEST_DB_PATH": str(db),
    })
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "TEST_DB_PATH" in out
    assert not db.exists()


def test_refuses_unrelated_basename_and_preserves_file(cleanup_paths):
    db = Path(f"/tmp/precious_unrelated_{uuid.uuid4().hex[:8]}.sqlite")
    cleanup_paths.append(db)
    db.write_bytes(b"PRECIOUS USER DATA - must not be deleted")
    proc = _run_import({
        "SHUNYA_TEST_SERVER_ALLOWED": "true",
        "TEST_DB_PATH": str(db),
    })
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "TEST_DB_PATH" in out
    assert db.read_bytes() == b"PRECIOUS USER DATA - must not be deleted"


def test_refuses_relative_path(cleanup_paths):
    proc = _run_import({
        "SHUNYA_TEST_SERVER_ALLOWED": "true",
        "TEST_DB_PATH": "shunya_test_server_relative.sqlite",
    })
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "absolute" in out.lower()


def test_removes_only_owned_stale_db_and_creates_fresh(cleanup_paths):
    db = _unique_path()
    cleanup_paths.append(db)
    db.write_bytes(b"stale content from a previous test-server run")
    proc = _run_import({
        "SHUNYA_TEST_SERVER_ALLOWED": "true",
        "TEST_DB_PATH": str(db),
    }, timeout=180)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"import failed: {out[-800:]}"
    assert "Removing stale test DB" in out
    assert "IMPORT_OK" in out
    assert db.exists()
    # A real SQLite database replaced the stale bytes.
    assert db.read_bytes()[:16] == b"SQLite format 3\x00"


def test_test_routes_confined_to_main():
    src = SERVER.read_text(encoding="utf-8")
    total = src.count('@app.route("/__test__')
    main_idx = src.find('if __name__ == "__main__":')
    assert main_idx > 0
    before = src[:main_idx].count('@app.route("/__test__')
    after = src[main_idx:].count('@app.route("/__test__')
    assert total >= 4
    assert before == 0, "Test-only routes must not be registered at import time"
    assert after == total


def test_refuses_symlinked_database_path(cleanup_paths, tmp_path):
    target = tmp_path / "real_target.sqlite"
    target.write_bytes(b"TARGET DATA - must survive")
    link = _unique_path()
    link.symlink_to(target)
    cleanup_paths.append(link)
    proc = _run_import({
        "SHUNYA_TEST_SERVER_ALLOWED": "true",
        "TEST_DB_PATH": str(link),
    })
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "symlink" in out.lower()
    assert target.read_bytes() == b"TARGET DATA - must survive"


def test_refuses_symlinked_sidecar_before_deleting_anything(cleanup_paths, tmp_path):
    main = _unique_path()
    cleanup_paths.append(main)
    main.write_bytes(b"MAIN DB SENTINEL - must survive when a sidecar is ambiguous")
    precious = tmp_path / "precious_target"
    precious.write_bytes(b"PRECIOUS - must survive")
    wal = Path(str(main) + "-wal")
    wal.symlink_to(precious)
    proc = _run_import({
        "SHUNYA_TEST_SERVER_ALLOWED": "true",
        "TEST_DB_PATH": str(main),
    })
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "symlink" in out.lower()
    # Validation happens before any unlink: the main DB must still exist.
    assert main.exists(), "main DB must not be deleted when cleanup is refused"
    assert main.read_bytes() == b"MAIN DB SENTINEL - must survive when a sidecar is ambiguous"
    assert precious.read_bytes() == b"PRECIOUS - must survive"


def test_refuses_concurrent_instance_holding_lock(cleanup_paths):
    import fcntl
    db = _unique_path()
    cleanup_paths.append(db)
    lock_path = Path(str(db) + ".lock")
    cleanup_paths.append(lock_path)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        proc = _run_import({
            "SHUNYA_TEST_SERVER_ALLOWED": "true",
            "TEST_DB_PATH": str(db),
        })
        out = proc.stdout + proc.stderr
        assert proc.returncode != 0
        assert "already holds" in out or "Another test-server instance" in out
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)