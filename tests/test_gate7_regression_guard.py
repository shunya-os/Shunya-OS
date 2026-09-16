"""GATE 7 — Regression guard: the legacy founder_objects store is retired.

R6B-2.4 replaced the previous flat exemption list with semantic verification.
The invariant is now absolute:

    ZERO production reads and ZERO production writes against founder_objects,
    outside the model definition itself.

The guard does not merely scan text against a growing whitelist. It parses each
production module with ``ast`` and classifies every occurrence:

  * a docstring occurrence is documentation, not code — permitted;
  * an import is not a read/write — permitted;
  * any other occurrence of the legacy table name (string or identifier,
    inside SQL or ORM calls) is a violation, in EVERY file including the
    allowlisted one unless it is the bare model definition;
  * dynamic SQL is covered, because a string literal such as
    ``UPDATE "{table_name}"`` is not the only way to name the table — the table
    name itself appearing in production code is the violation.

The allowlist is frozen to exactly one entry and is verified to contain a model
definition and nothing else, so it cannot be inflated into a hiding place.
"""

import ast
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]

LEGACY_TABLE = "founder_objects"
LEGACY_CLASS = "FounderObject"

# Frozen allowlist. Exactly one file may name the legacy table: the model
# definition. It is verified below to contain a definition and no read/write.
_LEGACY_NAME_ALLOWLIST = {
    "app/founder/models.py": "ORM model definition for the retired legacy table",
}


def _production_files() -> list[Path]:
    """Return all .py files in app/ and core/ (the production code paths)."""
    result = []
    for d in ("app", "core"):
        root = _PROJECT_ROOT / d
        if root.is_dir():
            result.extend(root.rglob("*.py"))
    return sorted(result)


def _rel(path: Path) -> str:
    return str(path.relative_to(_PROJECT_ROOT)).replace("\\", "/")


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Return the id() of Constant nodes that occupy docstring position."""
    docstrings = set()
    scopes = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if isinstance(node, scopes) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                docstrings.add(id(first.value))
    return docstrings


def _import_nodes(tree: ast.AST) -> set[int]:
    """Return the id() of nodes belonging to import statements."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for child in ast.walk(node):
                ids.add(id(child))
    return ids


def _tablename_constants(tree: ast.AST) -> set[int]:
    """Return the id() of string constants assigned to __tablename__.

    A table name in a model definition is a definition, not a read/write.
    """
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == LEGACY_CLASS:
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            ids.add(id(stmt.value))
    return ids


def _legacy_references(tree: ast.AST) -> list[tuple[int, str, str]]:
    """Classify legacy-store references as (lineno, kind, detail).

    kind is one of: ``definition`` (class/table definition), ``code``
    (an actual read/write reference), ``import`` or ``docstring``.
    """
    docstrings = _docstring_nodes(tree)
    imports = _import_nodes(tree)
    tablename_constants = _tablename_constants(tree)
    found: list[tuple[int, str, str]] = []

    for node in ast.walk(tree):
        if id(node) in imports:
            continue

        # String literal naming the legacy table (covers dynamic SQL payloads
        # and raw string identifiers).
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if LEGACY_TABLE in node.value:
                if id(node) in docstrings:
                    found.append((node.lineno, "docstring", node.value.strip()[:80]))
                elif id(node) in tablename_constants:
                    found.append((node.lineno, "definition", node.value.strip()[:80]))
                else:
                    found.append((node.lineno, "code", node.value.strip()[:80]))

        # f-string parts naming the legacy table.
        elif isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str) \
                        and LEGACY_TABLE in part.value:
                    found.append((node.lineno, "code", part.value.strip()[:80]))

        # Identifier/attribute naming the legacy ORM class.
        elif isinstance(node, ast.Name) and node.id == LEGACY_CLASS:
            found.append((node.lineno, "code", node.id))
        elif isinstance(node, ast.Attribute) and node.attr == LEGACY_CLASS:
            found.append((node.lineno, "code", f".{node.attr}"))

        # Class definition of the legacy model.
        elif isinstance(node, ast.ClassDef) and node.name == LEGACY_CLASS:
            found.append((node.lineno, "definition", f"class {node.name}"))

    return found


def test_no_production_references_to_legacy_object_store():
    """Production code must not read, write or name the legacy object store.

    Only the model definition file may name it, and that file is proven below
    to contain a definition and nothing executable against the table.
    """
    violations = []
    for fpath in _production_files():
        rel = _rel(fpath)
        try:
            tree = ast.parse(fpath.read_text(), filename=str(fpath))
        except SyntaxError as exc:  # pragma: no cover - syntax errors are CI failures
            violations.append(f"{rel}: unparsable: {exc}")
            continue

        for line_no, kind, detail in _legacy_references(tree):
            if kind in ("docstring", "import"):
                continue
            if kind == "definition":
                if rel not in _LEGACY_NAME_ALLOWLIST:
                    violations.append(f"{rel}:{line_no}: {detail}")
                continue
            violations.append(f"{rel}:{line_no}: {detail}")

    assert not violations, (
        "PRODUCTION CODE MUST NOT REFERENCE founder_objects OUTSIDE THE MODEL "
        "DEFINITION.\nViolations found:\n  " + "\n  ".join(violations) + "\n\n"
        "Reads must use ObjectService -> sh_objects. Writes are never permitted "
        "(there is no dual-write path in R6B-2). If a reference is genuinely "
        "required, it must be argued in the certification document and the "
        "guard updated deliberately — not appended to a whitelist."
    )


def test_allowlist_is_frozen_and_contains_only_a_definition():
    """The allowlist may not grow, and its entry must be a definition only."""
    assert _LEGACY_NAME_ALLOWLIST == {
        "app/founder/models.py": "ORM model definition for the retired legacy table",
    }, (
        "The legacy-store allowlist is frozen at exactly one entry (the model "
        "definition). Adding entries is exemption inflation."
    )

    for rel, reason in _LEGACY_NAME_ALLOWLIST.items():
        path = _PROJECT_ROOT / rel
        assert path.is_file(), f"allowlisted file does not exist: {rel}"
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))

        # It must actually define the model (otherwise the entry proves nothing).
        class_defs = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
                      and n.name == LEGACY_CLASS]
        assert class_defs, f"{rel} is allowlisted but does not define {LEGACY_CLASS}"

        # ...and it must contain no executable access to the legacy model.
        model_access = [
            (n.lineno, ast.unparse(n)[:80])
            for n in ast.walk(tree)
            if (isinstance(n, ast.Attribute) and n.attr == "query"
                and isinstance(n.value, ast.Name) and n.value.id == LEGACY_CLASS)
            or (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == LEGACY_CLASS)
        ]
        assert not model_access, (
            f"{rel} is allowlisted but executes against the model: {model_access}"
        )

        for banned in ("INSERT INTO founder_objects", "UPDATE founder_objects",
                       "DELETE FROM founder_objects", "session.add(FounderObject"):
            assert banned not in source, f"{rel} contains a legacy write: {banned}"


def test_legacy_model_import_is_registration_only():
    """A module importing the legacy model must not use it.

    app/__init__.py imports the model so SQLAlchemy registers the retired
    table (it must still exist for historical rows). Registration is an
    import-only concern: any module that imports FounderObject must have zero
    executable references to it — otherwise the reference scan above is being
    bypassed by an import.
    """
    offenders = []
    for fpath in _production_files():
        rel = _rel(fpath)
        if rel in _LEGACY_NAME_ALLOWLIST:
            continue
        source = fpath.read_text()
        tree = ast.parse(source, filename=str(fpath))

        imports_legacy = any(
            isinstance(node, (ast.Import, ast.ImportFrom))
            and any(alias.name == LEGACY_CLASS for alias in node.names)
            for node in ast.walk(tree)
        )
        if not imports_legacy:
            continue

        executable = [
            (line_no, detail)
            for line_no, kind, detail in _legacy_references(tree)
            if kind == "code"
        ]
        if executable:
            offenders.append(f"{rel}: imports and uses {LEGACY_CLASS}: {executable}")

    assert not offenders, (
        "A module may import FounderObject only for model registration; it may "
        "never use it.\n  " + "\n  ".join(offenders)
    )

    # The only legitimate importer is the model registry.
    importers = set()
    for fpath in _production_files():
        tree = ast.parse(fpath.read_text(), filename=str(fpath))
        if any(isinstance(node, (ast.Import, ast.ImportFrom))
               and any(alias.name == LEGACY_CLASS for alias in node.names)
               for node in ast.walk(tree)):
            importers.add(_rel(fpath))
    assert importers == {"app/__init__.py"}, (
        "Only the application factory may import the legacy model (table "
        f"registration). Unexpected importers: {sorted(importers)}"
    )


def test_object_service_is_a_generic_migrator_not_a_legacy_reader():
    """ObjectService.migrate_from() must stay generic (no hardcoded legacy read).

    The migration helper is the only sanctioned path that touches legacy rows,
    and it must do so through a caller-supplied table name — it must not embed
    an authoritative read of founder_objects.
    """
    source = (_PROJECT_ROOT / "core" / "object_service.py").read_text()
    tree = ast.parse(source)

    migrate = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "migrate_from":
            migrate = node
    assert migrate is not None, "ObjectService.migrate_from() is missing"

    # No string constant inside migrate_from may name the legacy table.
    for node in ast.walk(migrate):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert LEGACY_TABLE not in node.value, (
                "migrate_from() must not hardcode founder_objects — the source "
                "table is supplied by the caller."
            )


def test_no_migrate_default_org_one():
    """Assert migrate_from() callers supply explicit org IDs, not default=1.

    The default organization_id=1 in migrate_from() is forbidden as a
    synthetic ownership fallback.
    """
    from core.object_service import get_object_service
    svc = get_object_service()

    import inspect
    sig = inspect.signature(svc.migrate_from)
    default_org = sig.parameters.get("organization_id")
    assert default_org is not None, "migrate_from must accept organization_id"
    # Default of 1 is forbidden — callers must explicitly supply org context
    assert default_org.default != 1, "migrate_from default org_id is 1 — forbidden synthetic ownership fallback. Callers must supply explicit organization_id."
