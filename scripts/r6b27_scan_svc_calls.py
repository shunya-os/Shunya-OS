"""R6B-2.7 Batch C — semantic scan for identity-less ObjectService invocations.

AST-based: only counts REAL calls (attribute call on a name ending in `svc`
or on `get_object_service()`), never string literals or comments. This is the
direct remediation of the v1/v2 literal-patch incident.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

METHODS = {"create", "get", "update", "delete"}


def _recv_name(func: ast.AST) -> str | None:
    """Return a readable name for the call receiver, or None if not ours."""
    if not isinstance(func, ast.Attribute):
        return None
    meth = func.attr
    if meth not in METHODS:
        return None
    base = func.value
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Call):
        try:
            inner = ast.unparse(base.func)
        except Exception:
            return None
        return inner
    return None


def is_object_service_call(func: ast.AST, path: Path) -> bool:
    name = _recv_name(func)
    if not name:
        return False
    tail = name.split(".")[-1]
    if tail == "svc" or "get_object_service" in name:
        return True
    # Inside the service module itself, `self.<method>` IS an ObjectService call.
    if tail == "self" and path.name == "object_service.py":
        return True
    return False


def _is_raises_context(node: ast.AST) -> bool:
    """True when the with-item is a call to `pytest.raises(...)`."""
    if not isinstance(node, ast.withitem):
        return False
    ctx = node.context_expr
    if not isinstance(ctx, ast.Call):
        return False
    try:
        name = ast.unparse(ctx.func)
    except Exception:
        return False
    return name.endswith("raises")


def scan(path: Path) -> list[str]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[str] = []

    def visit(node: ast.AST, in_raises: bool = False) -> None:
        if isinstance(node, ast.With):
            inner = in_raises or any(_is_raises_context(i) for i in node.items)
            for child in ast.iter_child_nodes(node):
                visit(child, inner)
            return
        if isinstance(node, ast.Call) and is_object_service_call(node.func, path):
            meth = node.func.attr  # type: ignore[attr-defined]
            kwargs = {k.arg for k in node.keywords if k.arg}
            if not (kwargs & {"identity_id", "system_scope"}) and not in_raises:
                out.append(
                    f"{path}:{node.lineno}: {meth}(...) NO identity_id/system_scope "
                    f"(pos={len(node.args)}, kwargs={sorted(kwargs)})"
                )
        for child in ast.iter_child_nodes(node):
            visit(child, in_raises)

    visit(tree)
    return out


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv[1:]] or [Path("tests"), Path("app"), Path("core")]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("*.py")))
    total = 0
    for f in files:
        if "__pycache__" in str(f):
            continue
        try:
            hits = scan(f)
        except SyntaxError as exc:
            print(f"SYNTAX ERROR {f}: {exc}")
            total += 1
            continue
        for h in hits:
            print(h)
            total += 1
    print(f"\nTOTAL identity-less ObjectService calls: {total}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
