"""Regression guard — the repository must contain ZERO plaintext credentials.

This class of defect was found for real: ``scripts/verify-deployment.sh`` held a
hard-coded postgres password in a PUBLIC repository, and ``scripts/seed_demo_m4.py``
held a literal demo password. A string of bytes in a git object graph cannot be
un-published, so the only durable defence is to stop the next one from landing.

Rules enforced over TRACKED files only (``git ls-files``):

  1. No ``PGPASSWORD=<literal>`` — credentials must come from the environment.
  2. No inline credential in a connection URL (``scheme://user:secret@host``).
  3. No ``password`` / ``passwd`` / ``pwd`` assigned a non-placeholder literal.

Obvious placeholders, empty values and any templated value (``${VAR}``,
``os.environ``, ``getenv``, ``<redacted>``, ``{{...}}``) are allowed — the guard
targets *real*material, and a guard that cries wolf gets deleted.

The failure message names paths and line numbers and NEVER echoes the value.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories that are vendored / generated rather than authored source.
SKIP_PARTS = {"node_modules", ".git", ".venv", ".venv_test", "dist", "build",
              "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}

# Test fixtures legitimately carry FAKE credentials against isolated databases;
# documentation quotes placeholders. The defect class this guard targets is a
# real credential in OPERATIONAL code, so those two trees are out of scope.
SKIP_PREFIXES = ("tests/", "frontend/src/", "artifacts/")
SKIP_SUFFIX = (".md",)

# The redaction utility's docstring demonstrates the redaction transform on
# illustrative examples; it is not a credential source.
SKIP_FILES = {"app/security/redaction.py"}

# Files that are not authored text.
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
                 ".woff", ".woff2", ".ttf", ".otf", ".zip", ".gz", ".whl",
                 ".so", ".pyc", ".db", ".sqlite", ".dump", ".bin"}

MAX_BYTES = 2_000_000

# Values that are plainly not material. Compared case-insensitively.
PLACEHOLDERS = {
    "", "test", "tests", "testing", "password", "passwd", "pwd", "secret",
    "demo", "demo123", "demo-password", "changeme", "change-me", "change_me",
    "app-password", "your-password", "your_password", "example", "redacted",
    "none", "null", "undefined", "xyz", "pass", "fake", "dummy", "sample",
    "placeholder", "not-a-secret", "notasecret", "xxx", "abc", "123", "***",
}

TEMPLATE_MARKERS = ("${", "{{", "<", "os.environ", "getenv", "environ[",
                    "%(", "os.getenv", "config", "settings", "vault")

_PGPASSWORD = re.compile(r"""PGPASSWORD\s*=\s*(['"])(?P<val>[^'"]+)\1""")

_CONN_URL = re.compile(
    r"""(?:postgres|postgresql|mysql|mariadb|redis|rediss|mongodb|amqp|amqps)"""
    r"""://(?P<user>[^/\s:@]+):(?P<val>[^@\s/]+)@"""
)

_KV_SECRET = re.compile(
    r"""(?i)\b(?:pass(?:word)?|passwd|pwd)\s*[:=]\s*(['"])(?P<val>[^'"]{1,200})\1"""
)


def _is_allowed(value: str) -> bool:
    v = value.strip()
    if v.lower() in PLACEHOLDERS:
        return True
    low = v.lower()
    return any(marker in low for marker in TEMPLATE_MARKERS)


def _tracked_files() -> list[tuple[str, Path]]:
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    files = []
    for rel in filter(None, out.split("\0")):
        if (rel in SKIP_FILES or rel.startswith(SKIP_PREFIXES)
                or rel.endswith(SKIP_SUFFIX)):
            continue
        p = REPO_ROOT / rel
        if any(part in SKIP_PARTS for part in Path(rel).parts):
            continue
        if p.suffix.lower() in SKIP_SUFFIXES:
            continue
        files.append((rel, p))
    return files


def _violations_in_line(line: str) -> list[str]:
    """Rule labels violated by a single line of text."""
    found: list[str] = []
    for pattern, label in ((_PGPASSWORD, "PGPASSWORD literal"),
                           (_CONN_URL, "inline credential in connection URL"),
                           (_KV_SECRET, "hard-coded password literal")):
        for m in pattern.finditer(line):
            val = m.groupdict().get("val") or ""
            if _is_allowed(val):
                continue
            found.append(label)
    return found


def _scan() -> list[str]:
    violations: list[str] = []
    for rel, path in _tracked_files():
        try:
            if not path.is_file() or path.stat().st_size > MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for label in _violations_in_line(line):
                violations.append(f"{rel}:{lineno}: {label}")
    return violations


def test_no_plaintext_credentials_in_tracked_files():
    violations = _scan()
    assert not violations, (
        "Plaintext credential material found in tracked files (values intentionally "
        "not shown):\n  " + "\n  ".join(sorted(set(violations))) + "\n"
        "Move the secret to the deployment environment (see .env / DATABASE_URL) "
        "and read it at run time."
    )


# ---------------------------------------------------------------------------
# Self-tests: a guard that cannot fail is worthless. These prove the rules
# actually detect the defect class AND do not fire on placeholders.
# Synthetic values below are deliberately fake.
# ---------------------------------------------------------------------------

def test_guard_detects_real_credential_shapes():
    detected = (
        "DB_SCHEMA=$(PGPASSWORD='a-real-produced-pass' psql -h localhost)",
        "os.environ['DATABASE_URL'] = "
        "'postgresql://shunya:sup3rSecretValue@127.0.0.1:5432/db'",
        'smtp = SMTPAdapter(host="mail.corp", password="Sup3rSecretValue")',
    )
    for line in detected:
        assert _violations_in_line(line), (
            f"guard FAILED to detect credential shape: {line[:28]}...")


def test_guard_allows_placeholders_and_templated_values():
    allowed = (
        'PGPASSWORD="${DB_PASSWORD}" psql',
        "os.environ['DATABASE_URL'] = "
        "'postgresql://shunya:***@127.0.0.1:5433/shunya_db'",
        'password=os.environ.get("SHUNYA_DEMO_PASSWORD", "")',
        "'postgresql://user:password@host:5432/db'",
    )
    for line in allowed:
        assert not _violations_in_line(line), (
            f"guard FALSE POSITIVE on placeholder: {line[:40]}")
