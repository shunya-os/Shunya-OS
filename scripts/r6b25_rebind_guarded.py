"""R6B-2.5 — rebind the guarded DDL facade into every Alembic revision.

Idempotent: files already carrying ``guarded_op`` are left untouched.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path("/home/shunya-deploy/shunya_os/migrations/versions")
IMPORT_LINE = "    from migrations.guarded import guarded_op\n"
BIND_LINE = "    op = guarded_op(op)\n"

FUNC_RE = re.compile(r"^def (?:upgrade|downgrade)\(\)(\s*->\s*[^:]+)?:\s*$")


def docstring_end(lines, start):
    """Return index just past a leading docstring, else ``start``."""
    i = start
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i >= len(lines):
        return start
    stripped = lines[i].strip()
    for quote in ('"""', "'''"):
        if stripped.startswith(quote):
            # single-line docstring?
            if stripped.endswith(quote) and len(stripped) > len(quote):
                return i + 1
            j = i + 1
            while j < len(lines):
                if quote in lines[j]:
                    return j + 1
                j += 1
            return i + 1
    return start


def process(path):
    text = path.read_text()
    if "guarded_op(" in text:
        return False
    lines = text.splitlines(keepends=True)
    out = []
    idx = 0
    changed = False
    while idx < len(lines):
        line = lines[idx]
        out.append(line)
        if FUNC_RE.match(line.strip()) and line.startswith("def "):
            insert_at = docstring_end(lines, idx + 1)
            # emit any docstring lines that belong to this function first
            out.extend(lines[idx + 1:insert_at])
            out.append(IMPORT_LINE)
            out.append(BIND_LINE)
            idx = insert_at
            changed = True
            continue
        idx += 1
    if changed:
        path.write_text("".join(out))
    return changed


def main():
    touched = []
    for path in sorted(ROOT.glob("*.py")):
        if process(path):
            touched.append(path.name)
    print(f"rebound {len(touched)} revisions:")
    for name in touched:
        print("  ", name)


if __name__ == "__main__":
    main()
