#!/usr/bin/env python3
"""Verification test for Document Provider Adapters (LibreOffice & ONLYOFFICE).

Tests: create, edit, convert, export, import for all supported formats.
Run: PYTHONPATH=/path/to/shunya_os python3 verify_provider_document.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent  # governance/.. → shunya_os root

sys.path.insert(0, str(PROJECT))

# -----------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------

from adapters import LibreOfficeAdapter, OnlyOfficeAdapter

# ── colours ────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str, detail: str = "") -> None:
    print(f"  {GREEN}✓{RESET} {msg}{detail}")


def fail(msg: str, detail: str = "") -> None:
    print(f"  {RED}✗{RESET} {msg}{detail}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET} {msg}")


# ── helpers ────────────────────────────────────────────────────────────
PASSED = 0
FAILED = 0


def check(condition: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        ok(label, detail)
    else:
        FAILED += 1
        fail(label, detail)


# ── tests ──────────────────────────────────────────────────────────────
def test_create(adapter, name: str) -> dict[str, str]:
    """Create documents in all supported formats."""
    print(f"\n{BOLD}{name}: create_document{RESET}")
    paths: dict[str, str] = {}
    for fmt in ("odt", "docx", "pdf", "txt", "html"):
        try:
            p = adapter.create_document("TestDoc", "Hello, world!", fmt)
            paths[fmt] = p
            check(os.path.isfile(p) and os.path.getsize(p) > 0, f"{fmt}", f"  → {p}")
        except Exception as e:
            FAILED += 1
            fail(f"{fmt}", f"  ERROR: {e}")
    return paths


def test_extract(adapter, name: str, paths: dict[str, str]) -> None:
    """Extract text from all formats."""
    print(f"\n{BOLD}{name}: extract_text{RESET}")
    for fmt, p in paths.items():
        try:
            text = adapter.extract_text(p)
            has_hello = "Hello" in text or "TestDoc" in text
            check(has_hello, f"{fmt}", f"  extracted {len(text)} chars")
        except Exception as e:
            FAILED += 1
            fail(f"{fmt}", f"  ERROR: {e}")


def test_convert(adapter, name: str, paths: dict[str, str]) -> None:
    """Convert between formats."""
    print(f"\n{BOLD}{name}: convert{RESET}")
    pairs = [
        ("odt", "docx"),
        ("odt", "pdf"),
        ("odt", "txt"),
        ("docx", "odt"),
        ("docx", "pdf"),
        ("docx", "txt"),
    ]
    for src_fmt, tgt_fmt in pairs:
        src = paths.get(src_fmt)
        if not src:
            continue
        try:
            result = adapter.convert(src, tgt_fmt)
            check(
                os.path.isfile(result) and os.path.getsize(result) > 0,
                f"{src_fmt} → {tgt_fmt}",
                f"  → {result}",
            )
        except Exception as e:
            FAILED += 1
            fail(f"{src_fmt} → {tgt_fmt}", f"  ERROR: {e}")


def test_edit(adapter, name: str, paths: dict[str, str]) -> None:
    """Edit a DOCX document."""
    print(f"\n{BOLD}{name}: edit_document{RESET}")
    docx_path = paths.get("docx")
    if not docx_path:
        warn("No DOCX to edit, skipping")
        return
    try:
        edited = adapter.edit_document(docx_path, new_content="Edited content here.")
        text = adapter.extract_text(edited)
        check(
            "Edited content" in text,
            "replace content",
            f"  → {text[:80]}",
        )
    except Exception as e:
        FAILED += 1
        fail("replace content", f"  ERROR: {e}")


def test_import_from_fs(adapter, name: str) -> None:
    """Import (extract_text) an externally-created file."""
    print(f"\n{BOLD}{name}: import (extract from external file){RESET}")
    t = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
    t.write("Imported content\nSecond line")
    t.close()
    try:
        text = adapter.extract_text(t.name)
        check("Imported content" in text, "TXT import", f"  → {text[:60]}")
    except Exception as e:
        FAILED += 1
        fail("TXT import", f"  ERROR: {e}")
    finally:
        os.unlink(t.name)


# ── main ───────────────────────────────────────────────────────────────
def main() -> int:
    global PASSED, FAILED

    print(f"{BOLD}Document Provider Adapter Verification{RESET}")
    print(f"{'=' * 50}")

    # ── LibreOfficeAdapter ─────────────────────────────────────────────
    try:
        lo = LibreOfficeAdapter()
        check(True, "instantiation")
    except Exception as e:
        FAILED += 1
        fail("instantiation", f"  {e}")
        return 1

    lo_paths = test_create(lo, "LibreOfficeAdapter")
    test_extract(lo, "LibreOfficeAdapter", lo_paths)
    test_convert(lo, "LibreOfficeAdapter", lo_paths)
    test_edit(lo, "LibreOfficeAdapter", lo_paths)
    test_import_from_fs(lo, "LibreOfficeAdapter")

    # ── OnlyOfficeAdapter ──────────────────────────────────────────────
    try:
        oo = OnlyOfficeAdapter()
        check(True, "instantiation")
    except Exception as e:
        FAILED += 1
        fail("instantiation", f"  {e}")
        return 1

    oo_paths = test_create(oo, "OnlyOfficeAdapter")
    test_extract(oo, "OnlyOfficeAdapter", oo_paths)
    test_convert(oo, "OnlyOfficeAdapter", oo_paths)
    test_edit(oo, "OnlyOfficeAdapter", oo_paths)
    test_import_from_fs(oo, "OnlyOfficeAdapter")

    # ── summary ────────────────────────────────────────────────────────
    total = PASSED + FAILED
    print(f"\n{'=' * 50}")
    print(f"{BOLD}Results:{RESET}  {GREEN}{PASSED} passed{RESET}  {RED}{FAILED} failed{RESET}  {total} total")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())