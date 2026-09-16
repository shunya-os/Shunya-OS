"""R6B-2.5 — fix the guarded binding inserted by r6b25_rebind_guarded.py.

The first insertion used ``op = guarded_op(op)``, which raises
``UnboundLocalError`` because the assignment makes ``op`` local to the
function. ``guarded_op()`` with no argument wraps Alembic's own proxy, so the
correct binding references no local name at all.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path("/home/shunya-deploy/shunya_os/migrations/versions")
OLD = "    op = guarded_op(op)\n"
NEW = "    op = guarded_op()\n"


def main():
    fixed = []
    for path in sorted(ROOT.glob("*.py")):
        text = path.read_text()
        if OLD in text:
            path.write_text(text.replace(OLD, NEW))
            fixed.append(path.name)
    print(f"fixed binding in {len(fixed)} revisions")
    for name in fixed:
        print("  ", name)


if __name__ == "__main__":
    main()
