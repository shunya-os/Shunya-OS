"""R6B-2.7 Batch E — AST inventory of ObjectService READ-surface callers.

Reports every invocation of the non-CRUD query surface:
  get_by_object_id, get_by_type, list_by_workspace, list_by_creator,
  search, count_by_type

Only REAL calls whose receiver is provably an ObjectService are reported:
  * `svc.<m>(...)`            where svc is a local name
  * `get_object_service().<m>(...)`
  * `self.<m>(...)` inside core/object_service.py

Also reports whether the call already carries `identity_id`, which is the
authorization context Batch E must add.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

READ_METHODS = {
    "get_by_object_id", "get_by_type", "list_by_workspace",
    "list_by_creator", "search", "count_by_type",
}


def _receiver_ok(node: ast.AST, path: Path) -> bool:
    if not isinstance(node, ast.Attribute) or node.attr not in READ_METHODS:
        return False
    base = node.value
    if isinstance(base, ast.Name):
        if base.id == "svc":
            return True
        if base.id == "self" and path.name == "object_service.py":
            return True
        # any local bound from get_object_service()
        return False
    if isinstance(base, ast.Call):
        try:
            return "get_object_service" in ast.unparse(base.func)
        except Exception:
            return False
    return False


def scan(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [f"SYNTAX ERROR {path}: {exc}"]
    out = []
    # names bound from get_object_service() in this module
    svc_names = {"svc"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            try:
                src = ast.unparse(node.value.func)
            except Exception:
                continue
            if "get_object_service" in src:
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        svc_names.add(t.id)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not isinstance(f, ast.Attribute) or f.attr not in READ_METHODS:
            continue
        base = f.value
        ok = False
        if isinstance(base, ast.Name) and base.id in svc_names:
            ok = True
        if isinstance(base, ast.Name) and base.id == "self" and path.name == "object_service.py":
            ok = True
        if isinstance(base, ast.Call):
            try:
                ok = "get_object_service" in ast.unparse(base.func)
            except Exception:
                ok = False
        if not ok:
            continue
        kwargs = {k.arg for k in node.keywords if k.arg}
        out.append(
            f"{path}:{node.lineno}: {f.attr}(...) "
            f"{'HAS identity_id' if 'identity_id' in kwargs else 'NO identity_id'}"
        )
    return out


def main(argv):
    roots = [Path(a) for a in argv[1:]] or [Path("app"), Path("core")]
    files = []
    for r in roots:
        files.extend(sorted(r.rglob("*.py")) if r.is_dir() else [r])
    total = with_id = 0
    for f in files:
        if "__pycache__" in str(f):
            continue
        for line in scan(f):
            print(line)
            total += 1
            if "HAS identity_id" in line:
                with_id += 1
    print(f"\nTOTAL read-surface calls: {total}  (with identity_id: {with_id}, "
          f"without: {total - with_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
