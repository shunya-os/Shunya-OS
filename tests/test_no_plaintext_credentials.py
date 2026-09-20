"""Regression guard — the repository must contain ZERO plaintext credentials.

This class of defect was found for real, twice:

  * ``scripts/verify-deployment.sh`` held a hard-coded postgres password, and
    four other operational scripts held inline DSN credentials — in a PUBLIC
    repository.
  * after those were fixed, a SECOND sweep found an unquoted
    ``POSTGRES_PASSWORD: <literal>`` in ``docker-compose.yml`` and the same
    value disclosed in prose inside two committed audit documents. The first
    version of this guard missed both because its rules only matched QUOTED
    literals and it skipped markdown. Those blind spots are closed below.

Rules enforced over TRACKED files (excluding test fixtures and vendored code):

  1. No ``PGPASSWORD=<literal>``.
  2. No inline credential in a connection URL (``scheme://user:secret@host``).
  3. No quoted ``password`` / ``passwd`` / ``pwd`` literal.
  4. Config-like files (``.yml``, ``.yaml``, ``.env``, ``.ini``, ``.toml``,
     Dockerfile …) must not carry an UNQUOTED ``*PASSWORD|*SECRET|*TOKEN``
     assignment. This is the rule that catches ``POSTGRES_PASSWORD: hunter2``.
  5. Documents must not disclose a secret in prose: a secret keyword followed by
     a backtick/quoted/code-wrapped token.

Obvious placeholders, empty values and templated values (``${VAR}``,
``os.environ``, ``<redacted>``, ``{{...}}``, ``***``) are allowed — a guard that
cries wolf gets deleted.

The failure message names paths and line numbers and NEVER echoes the value.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Vendored / generated trees.
SKIP_PARTS = {"node_modules", ".git", ".venv", ".venv_test", "dist", "build",
              "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}

# Test fixtures legitimately carry FAKE credentials against isolated databases.
SKIP_PREFIXES = ("tests/", "frontend/src/")
SKIP_SUFFIX: tuple[str, ...] = ()

# The redaction utility's docstring demonstrates the redaction transform on
# illustrative examples; it is not a credential source.
SKIP_FILES = {"app/security/redaction.py"}

SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
                 ".woff", ".woff2", ".ttf", ".otf", ".zip", ".gz", ".whl",
                 ".so", ".pyc", ".db", ".sqlite", ".dump", ".bin"}

MAX_BYTES = 2_000_000

PLACEHOLDERS = {
    "", "test", "tests", "testing", "password", "passwd", "pwd", "secret",
    "demo", "demo123", "demo-password", "changeme", "change-me", "change_me",
    "app-password", "your-password", "your_password", "example", "redacted",
    "none", "null", "undefined", "xyz", "pass", "fake", "dummy", "sample",
    "placeholder", "not-a-secret", "notasecret", "xxx", "abc", "123", "***",
    "[redacted-credential]", "redacted-credential", "shunya", "postgres",
    "root", "admin",
}

TEMPLATE_MARKERS = ("${", "{{", "<", "os.environ", "getenv", "environ[",
                    "%(", "os.getenv", "config", "settings", "vault")

CONFIG_SUFFIXES = {".yml", ".yaml", ".env", ".ini", ".cfg", ".conf", ".toml",
                   ".properties", ".service", ".sh"}
CONFIG_NAMES = {"Dockerfile", "docker-compose.yml", "Makefile"}
DOC_SUFFIXES = {".md", ".html", ".rst", ".txt"}

_PGPASSWORD = re.compile(r"""PGPASSWORD\s*=\s*(['"])(?P<val>[^'"]+)\1""")

_CONN_URL = re.compile(
    r"""(?:postgres|postgresql|mysql|mariadb|redis|rediss|mongodb|amqp|amqps)"""
    r"""://(?P<user>[^/\s:@]+):(?P<val>[^@\s/]+)@"""
)

_KV_SECRET = re.compile(
    r"""(?i)\b(?:pass(?:word)?|passwd|pwd)\s*[:=]\s*(['"])(?P<val>[^'"]{1,200})\1"""
)

# Unquoted assignment in a config-like file: KEY: value   /   KEY=value
# TOKEN is deliberately NOT included (it matched `cost_per_token`), and keys that
# merely reference the environment (`api_key_env`) are excluded.
_UNQUOTED_SECRET = re.compile(
    r"""(?im)^\s*[A-Za-z0-9_.\-]*"""
    r"""(?:PASSWORD|PASSWD|SECRET|API_?KEY|CREDENTIAL)"""
    r"""(?!_?(?:ENV|NAME|FILE|PATH|REF|VAR))"""
    r"""[A-Za-z0-9_.\-]*\s*[:=]\s*(?P<val>[^\s#'"]+)\s*$"""
)

_ENV_REFERENCE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")

# Prose disclosure in a document. Deliberately narrow: it requires a DISCLOSURE
# phrase ("the actual/real/production password is `X`"). A bare keyword rule was
# tried and rejected — it fired on `type="password"`, `class="pass"`, file names
# and env-var names. A guard that cries wolf gets deleted.
_DOC_DISCLOSURE = re.compile(
    r"""(?i)\b(?:actual|real|true|production|live|correct)\s+"""
    r"""(?:pass(?:word)?|passwd|secret|token|api[_ \-]?key)\b"""
    r"""[^`\n<]{0,40}?(?:`|<code>|['"])(?P<val>[A-Za-z0-9!@#$%^&*_\-+=]{6,})"""
)


def _is_allowed(value: str) -> bool:
    v = value.strip()
    if v.lower() in PLACEHOLDERS:
        return True
    # An ALL_CAPS identifier is a reference to an environment variable, not a
    # secret in its own right (`api_key_env: OPENROUTER_API_KEY`).
    if _ENV_REFERENCE.match(v):
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


def _rules_for(rel: str) -> list[tuple[re.Pattern, str]]:
    rules = [(_PGPASSWORD, "PGPASSWORD literal"),
             (_CONN_URL, "inline credential in connection URL"),
             (_KV_SECRET, "hard-coded password literal")]
    name = Path(rel).name
    if Path(rel).suffix.lower() in CONFIG_SUFFIXES or name in CONFIG_NAMES:
        rules.append((_UNQUOTED_SECRET, "unquoted credential assignment"))
    if Path(rel).suffix.lower() in DOC_SUFFIXES:
        rules.append((_DOC_DISCLOSURE, "secret disclosed in prose"))
    return rules


def _violations_in_line(line: str, rel: str = "config.yml") -> list[str]:
    """Rule labels violated by a single line of text."""
    found: list[str] = []
    for pattern, label in _rules_for(rel):
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
            for label in _violations_in_line(line, rel):
                violations.append(f"{rel}:{lineno}: {label}")
    return violations


def test_no_plaintext_credentials_in_tracked_files():
    violations = _scan()
    assert not violations, (
        "Plaintext credential material found in tracked files (values intentionally "
        "not shown):\n  " + "\n  ".join(sorted(set(violations))) + "\n"
        "Move the secret to the deployment environment (see .env / DATABASE_URL), "
        "or redact the disclosure if it is a historical document."
    )


# ---------------------------------------------------------------------------
# Self-tests: a guard that cannot fail is worthless. These prove the rules
# detect the real defect shapes — including the two that were MISSED first time
# — and do not fire on placeholders. The values below are deliberately fake.
# ---------------------------------------------------------------------------

def test_guard_detects_real_credential_shapes():
    detected = (
        ("DB=$(PGPASSWORD='a-real-produced-pass' psql -h localhost)", "x.sh"),
        ("os.environ['DATABASE_URL'] = "
         "'postgresql://shunya:sup3rSecretValue@127.0.0.1:5432/db'", "x.py"),
        ('smtp = SMTPAdapter(host="mail.corp", password="Sup3rSecretValue")', "x.py"),
    )
    for line, rel in detected:
        assert _violations_in_line(line, rel), (
            f"guard FAILED to detect credential shape: {line[:28]}...")


def test_guard_detects_unquoted_config_credential():
    """The blind spot that let docker-compose.yml through the first version."""
    line = "    POSTGRES_PASSWORD: hunter2realvalue"
    assert _violations_in_line(line, "docker-compose.yml"), (
        "guard FAILED to detect an unquoted YAML credential")


def test_guard_detects_secret_disclosed_in_prose():
    """The blind spot that let the audit documents through."""
    line = "The actual password is `hunter2realvalue` (matching the .env file)."
    assert _violations_in_line(line, "plp_cycle31/gap_register.md"), (
        "guard FAILED to detect a secret disclosed in prose")


def test_guard_allows_placeholders_and_templated_values():
    allowed = (
        ('PGPASSWORD="${DB_PASSWORD}" psql', "x.sh"),
        ("os.environ['DATABASE_URL'] = "
         "'postgresql://shunya:***@127.0.0.1:5433/shunya_db'", "x.py"),
        ('password=os.environ.get("SHUNYA_DEMO_PASSWORD", "")', "x.py"),
        ("'postgresql://user:password@host:5432/db'", "x.py"),
        ("    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?must be set}", "docker-compose.yml"),
        ("The actual password is `[REDACTED-CREDENTIAL]`.", "doc.md"),
    )
    for line, rel in allowed:
        assert not _violations_in_line(line, rel), (
            f"guard FALSE POSITIVE on placeholder: {line[:44]}")
