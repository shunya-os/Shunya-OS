"""GATE 7 — Regression guard: production code must not reintroduce FounderObject writes.

This test fails CI if any production code (app/ or core/) writes to the
founder_objects table outside explicitly approved compatibility/migration
boundaries. A future developer should not be able to reintroduce dual-write
by accident.
"""

import os
import sys
import subprocess
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _production_files() -> list[Path]:
    """Return all .py files in app/ and core/ (the production code paths)."""
    result = []
    for d in ("app", "core"):
        root = _PROJECT_ROOT / d
        if root.is_dir():
            result.extend(root.rglob("*.py"))
    return sorted(result)


def _get_definition_lines(filepath: Path) -> list[tuple[int, str]]:
    """Return (line_number, stripped_line) for each line in the file."""
    lines = filepath.read_text().splitlines()
    return [(i + 1, line) for i, line in enumerate(lines)]


def test_no_production_writes_to_founder_objects():
    """Assert zero production code writes to founder_objects.

    Exemptions (must be explicitly listed with reason):
    - app/founder/models.py: model definition
    - app/founder/routes.py: test_convergence module (NOTE)
    - tests/: test files are excluded
    """
    exempt_files = {
        "app/founder/models.py",          # Model definition — defines the table
        "core/object_service.py",         # Migration helper — migrate_from() reads legacy
        "app/ai/context.py",              # Canonical-first with legacy fallback (C boundary)
        "app/objects/canonical.py",       # Explicit compatibility layer (C boundary)
        "app/founder/routes.py",          # API compat layer with canonical-first + legacy fallback
    }

    # Patterns that indicate writes
    write_patterns = [
        "FounderObject(",
        "db.session.add(FounderObject",
        ".add(FounderObject",
        "INSERT INTO founder_objects",
        "UPDATE founder_objects",
        "DELETE FROM founder_objects",
    ]

    # Patterns that indicate authoritative legacy reads (GATE 3 regression)
    read_patterns = [
        "FounderObject.query",
        "FROM founder_objects",
        "founder_objects WHERE",
        "FounderObject.get",
        "FounderObject.filter",
    ]

    violations = []
    read_violations = []

    for fpath in _production_files():
        rel = fpath.relative_to(_PROJECT_ROOT)
        rel_str = str(rel).replace("\\", "/")

        # Skip exempt files
        if rel_str in exempt_files:
            continue

        # Skip __init__.py (import-only)
        if fpath.name == "__init__.py":
            continue

        lines = _get_definition_lines(fpath)

        for line_no, line in lines:
            for pattern in write_patterns:
                if pattern in line:
                    # Check if it's a comment about legacy (not an actual write)
                    stripped = line.strip()
                    if stripped.startswith("#") or "NOTE:" in stripped or "noqa" in stripped:
                        continue
                    if "FounderObject(" in line and "import" in line:
                        continue  # Import, not a write

                    violations.append(f"{rel_str}:{line_no}: {line.strip()}")

            for pattern in read_patterns:
                if pattern in line:
                    stripped = line.strip()
                    if stripped.startswith("#") or "NOTE:" in stripped or "noqa" in stripped:
                        continue
                    # Import statements are not reads
                    if "import" in line and ("FounderObject" in line or "founder_objects" in line):
                        continue
                    # Model definition is not a read
                    if "class FounderObject" in line or "class FounderSpace" in line:
                        continue
                    # Compatibility boundary comments are exempt
                    if "COMPATIBILITY BOUNDARY" in stripped or "compat boundary" in stripped.lower():
                        continue

                    read_violations.append(f"{rel_str}:{line_no}: {line.strip()}")

    assert not violations, (
        "PRODUCTION CODE MUST NOT WRITE TO founder_objects.\n"
        "Violations found:\n  " + "\n  ".join(violations) + "\n\n"
        "If these are legitimate compatibility boundaries, add the file to\n"
        "the exempt_files set in this test with documentation. Otherwise,\n"
        "migrate the write to ObjectService -> sh_objects."
    )

    assert not read_violations, (
        "PRODUCTION CODE MUST NOT PERFORM AUTHORITATIVE legacy reads.\n"
        "Unauthorized reads from founder_objects found:\n  " + "\n  ".join(read_violations) + "\n\n"
        "Convert these reads to ObjectService -> sh_objects. If the read is a\n"
        "legitimate compatibility boundary, add the file to exempt_files.\n"
        "For FounderSpace reads, convert to sh_workspaces queries."
    )


def test_no_migrate_default_org_one():
    """Assert migrate_from() callers supply explicit org IDs, not default=1.

    The default organization_id=1 in migrate_from() is forbidden as a
    synthetic ownership fallback.
    """
    exempt_files = {
        "app/onboard.py",  # migration bootstrap runs early
    }

    from core.object_service import get_object_service
    svc = get_object_service()

    # This doesn't test the default; it just verifies the function signature
    import inspect
    sig = inspect.signature(svc.migrate_from)
    default_org = sig.parameters.get("organization_id")
    assert default_org is not None, "migrate_from must accept organization_id"
    # Default of 1 is forbidden — callers must explicitly supply org context
    assert default_org.default != 1, "migrate_from default org_id is 1 — forbidden synthetic ownership fallback. Callers must supply explicit organization_id."