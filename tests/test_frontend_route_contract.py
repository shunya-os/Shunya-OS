"""Frontend ⇄ backend route contract guard.

A green backend suite cannot see a UI that calls an endpoint which does not
exist. This happened for real: `commitment-workspace.tsx` posted the user's
resolution note to `/api/v1/commitments/<id>/resolve`, a route that has never
existed, behind a `.catch(() => {})` — so a typed note was silently discarded
while the UI reported success.

The check compares SEGMENT SHAPES, so it needs no knowledge of ids:
  frontend `/api/v1/commitments/${id}/resolve` -> ["api","v1","*","resolve"]
A path matches a rule only if the segment counts are equal and every static
segment agrees; wildcard segments (``${...}`` in the frontend, ``<...>`` in a
Flask rule) match anything. This is precise: it flags the missing
`/commitments/*/resolve` even though rules like `/attention/<id>/resolve` and
`/customer/commitments/<id>/resolve` exist.

Files that are archived and never imported by the app are listed in
NOT_REACHABLE: they cannot run in the browser, so a stale path there is dead code
rather than broken product behaviour. The list is explicit so that a NEW file
cannot silently join it.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app import create_app

FRONTEND_SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"

# Archived / never-imported components. Verified individually: each is either
# declared archived in its own index, or referenced by no other module.
NOT_REACHABLE = {
    "components/living-workspace/living-workspace.tsx",
}

PATH_RE = re.compile(r"""['"`](/api/v1/[A-Za-z0-9_./:${}\-]*)['"`]""")


def _shape(path: str) -> list[str] | None:
    """Segment shape of a frontend path, or None if it is not a real path."""
    path = path.split("?")[0].rstrip("/")
    if not path.startswith("/api/"):
        return None
    segs = []
    for seg in path.split("/")[1:]:
        # A segment is a wildcard when it contains a template expression.
        if "${" in seg or "{" in seg:
            segs.append("*")
        elif seg:
            segs.append(seg)
    return segs or None


def _rule_shape(rule: str) -> list[str]:
    segs = []
    for seg in rule.split("/")[1:]:
        segs.append("*" if (seg.startswith("<") and seg.endswith(">")) else seg)
    return [s for s in segs if s]


def _strip_comments(text: str) -> str:
    """Remove comments so PROSE about a removed path is not read as a call.

    Without this, documenting "the previous `/api/v1/x` does not exist" would
    itself fail the guard.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)//.*$", "", text)


def _frontend_paths():
    for file in sorted(FRONTEND_SRC.rglob("*")):
        if file.suffix not in {".ts", ".tsx"} or not file.is_file():
            continue
        rel = str(file.relative_to(FRONTEND_SRC))
        if ".test." in rel or "/__tests__/" in rel:
            continue
        text = _strip_comments(file.read_text(encoding="utf-8", errors="ignore"))
        for raw in PATH_RE.findall(text):
            shape = _shape(raw)
            if shape:
                yield rel, raw, shape


def _matches(fe: tuple[str, ...], rule: tuple[str, ...]) -> bool:
    """True when a frontend path can address a rule.

    A frontend wildcard (``${...}``) matches ANY rule segment — including a
    static one, because ``/api/v1/pdf/${objectType}/${id}`` legitimately
    addresses ``/api/v1/pdf/invoice/<int:invoice_id>``. A STATIC frontend
    segment must agree with a static rule segment.
    """
    if len(fe) != len(rule):
        return False
    for a, b in zip(fe, rule):
        if a == "*" or b == "*":
            continue
        if a != b:
            return False
    return True


def _is_prefix(fe: tuple[str, ...], rule: tuple[str, ...]) -> bool:
    """True when the frontend path is a BASE constant that rules extend.

    `const BASE = '/api/v1/integration'` followed by ``${BASE}/configs`` is
    legitimate: the literal alone has no rule, but rules live beneath it.
    """
    if len(fe) >= len(rule):
        return False
    for a, b in zip(fe, rule):
        if a != "*" and b != "*" and a != b:
            return False
    return True


@pytest.fixture(scope="module")
def rule_shapes():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    return [tuple(_rule_shape(str(r))) for r in app.url_map.iter_rules()]


def test_every_reachable_frontend_api_path_exists(rule_shapes):
    """Each call a reachable component can make must hit a real route."""
    missing: list[str] = []
    checked = 0
    for rel, raw, shape in _frontend_paths():
        if rel in NOT_REACHABLE:
            continue
        checked += 1
        fe = tuple(shape)
        if not any(
            _matches(fe, rule) or _is_prefix(fe, rule) for rule in rule_shapes
        ):
            missing.append(f"{rel}: {raw}")
    assert checked > 50, f"expected to scan the frontend, only saw {checked} paths"
    assert not missing, "frontend calls endpoints that do not exist:\n  " + "\n  ".join(
        sorted(set(missing))
    )


def test_archived_files_are_really_not_referenced():
    """Keep the allowlist honest: an archived file must not be imported as a module."""
    for rel in NOT_REACHABLE:
        stem = Path(rel).stem
        # Match an IMPORT of the module itself (`.../living-workspace'`), not a
        # sibling in the same directory (`.../living-workspace/living-store`).
        import_re = re.compile(rf"""/{re.escape(stem)}['"]""")
        referencing = []
        for file in FRONTEND_SRC.rglob("*.tsx"):
            if str(file.relative_to(FRONTEND_SRC)) == rel:
                continue
            text = file.read_text(encoding="utf-8", errors="ignore")
            if import_re.search(text):
                referencing.append(str(file.relative_to(FRONTEND_SRC)))
        assert not referencing, f"{rel} is in NOT_REACHABLE but is imported by {referencing}"
