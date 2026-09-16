"""R6B-2.5 — chain intent audit.

Guards the same defect class found with act_execution_logs: a revision adds a
column/index to a table that does not exist yet at that point in the chain,
so the guarded facade correctly skips it and the declared artifact is silently
lost unless the revision that later materialises the table declares it.

Read-only: inspects an already-built certification schema plus the revision
files. Writes nothing.

Usage:
    .venv/bin/python scripts/r6b25_chain_intent_audit.py <database>
"""
from __future__ import annotations

import ast
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path("/home/shunya-deploy/shunya_os")
VERS = REPO / "migrations" / "versions"
PSQL = "/usr/lib/postgresql/16/bin/psql"


def psql(db, sql):
    out = subprocess.run(
        [PSQL, "-d", db, "-tAc", sql],
        capture_output=True, text=True,
        env={"PGHOST": "127.0.0.1", "PGPORT": "5433",
             "PGUSER": "shunya-deploy", "PATH": "/usr/bin:/bin"},
    )
    return [ln for ln in out.stdout.splitlines() if ln]


def revision_order():
    """Return [(revision, path)] in chain order."""
    meta = {}
    for path in VERS.glob("*.py"):
        text = path.read_text()
        rev = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', text, re.M)
        down = re.search(r'^down_revision\s*=\s*(.+)$', text, re.M)
        if not rev:
            continue
        down_val = None
        if down:
            raw = down.group(1).strip()
            try:
                down_val = ast.literal_eval(raw)
            except Exception:
                down_val = None
        meta[rev.group(1)] = (path, down_val)

    # walk from the roots
    children = {}
    roots = []
    for rev, (path, down) in meta.items():
        if isinstance(down, str) and down in meta:
            children.setdefault(down, []).append(rev)
        else:
            roots.append(rev)

    ordered, seen = [], set()

    def walk(node):
        if node in seen:
            return
        seen.add(node)
        ordered.append(node)
        for child in sorted(children.get(node, [])):
            walk(child)

    for root in sorted(roots):
        walk(root)
    for rev in sorted(meta):
        walk(rev)
    return [(rev, meta[rev][0]) for rev in ordered]


def add_column_intents(path):
    """[(table, column)] from op.add_column calls in upgrade()."""
    tree = ast.parse(path.read_text())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not isinstance(fn, ast.Attribute) or fn.attr != "add_column":
            continue
        if len(node.args) < 2:
            continue
        tbl = node.args[0]
        col = node.args[1]
        if not (isinstance(tbl, ast.Constant) and isinstance(tbl.value, str)):
            continue
        name = None
        if isinstance(col, ast.Call):
            for kw in col.keywords:
                if kw.arg == "name":
                    name = kw.value.value
            if name is None:
                for a in col.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        name = a.value
                        break
        if name:
            out.append((tbl.value, name))
    return out


def create_index_intents(path):
    tree = ast.parse(path.read_text())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not isinstance(fn, ast.Attribute) or fn.attr != "create_index":
            continue
        if len(node.args) < 3:
            continue
        idx, tbl = node.args[0], node.args[1]
        if isinstance(idx, ast.Constant) and isinstance(tbl, ast.Constant):
            out.append((idx.value, tbl.value))
    return out


def main():
    db = sys.argv[1] if len(sys.argv) > 1 else "shunya_r6b25_cert"

    final_tables = set(psql(db, "SELECT table_name FROM information_schema.tables "
                                "WHERE table_schema='public'"))
    final_cols = set()
    for row in psql(db, "SELECT table_name||'.'||column_name FROM information_schema.columns "
                        "WHERE table_schema='public'"):
        final_cols.add(row)
    final_idx = set(psql(db, "SELECT indexname FROM pg_indexes WHERE schemaname='public'"))

    print(f"final schema: {len(final_tables)} tables, {len(final_cols)} columns, "
          f"{len(final_idx)} indexes")

    missing_cols, missing_idx = [], []
    for rev, path in revision_order():
        for tbl, col in add_column_intents(path):
            if tbl in final_tables and f"{tbl}.{col}" not in final_cols:
                missing_cols.append((rev, tbl, col))
        for idx, tbl in create_index_intents(path):
            if tbl in final_tables and idx not in final_idx:
                missing_idx.append((rev, tbl, idx))

    print("\n=== declared add_column artifacts absent from the final schema ===")
    if missing_cols:
        for rev, tbl, col in missing_cols:
            print(f"  {rev}: {tbl}.{col}")
    else:
        print("  none")

    print("\n=== declared create_index artifacts absent from the final schema ===")
    if missing_idx:
        for rev, tbl, idx in missing_idx:
            print(f"  {rev}: index {idx} on {tbl}")
    else:
        print("  none")

    ok = not missing_cols and not missing_idx
    print(f"\nCHAIN_INTENT_AUDIT={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())