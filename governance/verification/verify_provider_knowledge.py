"""Verify Provider Knowledge — SearXNG and ComfyUI adapter integration.

Tests (post-remediation — no fabricated output is ever produced):
  1. SearXNGAdapter
     - DB-backed universal search returns structured results (no SEARXNG_URL)
     - a configured-but-unreachable SearXNG instance raises an honest error
  2. ComfyUIAdapter
     - unconfigured (no COMFYUI_URL) raises an honest error — no placeholder
     - a configured-but-unreachable ComfyUI raises an honest error — no PNG
"""

from __future__ import annotations

import os
import sys
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Ensure no config leaks in from the caller's environment for default tests.
for var in ("COMFYUI_URL", "COMFYUI_API_URL", "SEARXNG_URL"):
    os.environ.pop(var, None)

from adapters.search.searxng import SearXNGAdapter  # noqa: E402
from adapters.image.comfyui import ComfyUIAdapter  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════
# SearXNGAdapter tests
# ═══════════════════════════════════════════════════════════════════════


def test_searxng_import() -> dict[str, Any]:
    """SearXNGAdapter is importable and extends SearchAdapter."""
    from adapters import SearchAdapter
    a = SearXNGAdapter()
    assert isinstance(a, SearchAdapter)
    return {"scenario": "SearXNG import & type check", "passed": True}


def test_searxng_configurable_base_url() -> dict[str, Any]:
    """SearXNGAdapter accepts a custom base_url."""
    a = SearXNGAdapter(base_url="http://searxng.local:8888")
    assert a.base_url == "http://searxng.local:8888"
    return {"scenario": "SearXNG configurable base_url", "passed": True}


def test_searxng_db_fallback_structured() -> dict[str, Any]:
    """Without SEARXNG_URL, search falls back to the DB-backed universal
    search and still returns the adapter's result contract (real records)."""
    a = SearXNGAdapter()
    results = a.search("test", limit=5, categories=["web"])
    assert isinstance(results, list)
    for r in results:
        assert "title" in r
        assert "url" in r
        assert "snippet" in r
    assert len(results) <= 5
    return {
        "scenario": "SearXNG DB-backed search (no SEARXNG_URL)",
        "result_count": len(results),
        "passed": True,
    }


def test_searxng_db_fallback_respects_limit() -> dict[str, Any]:
    """DB-backed fallback respects the limit parameter."""
    a = SearXNGAdapter()
    results = a.search("test", limit=2)
    assert len(results) <= 2
    return {
        "scenario": "SearXNG respects limit (DB-backed)",
        "count": len(results),
        "passed": True,
    }


def test_searxng_unreachable_raises() -> dict[str, Any]:
    """A configured-but-unreachable SearXNG must raise an honest error —
    never fall back to fabricated stub results."""
    a = SearXNGAdapter(base_url="http://127.0.0.1:1")  # port 1: connection refused
    try:
        a.search("test", limit=5, categories=["web"])
    except RuntimeError as e:
        assert "SearXNG" in str(e)
        return {"scenario": "SearXNG unreachable → honest RuntimeError", "passed": True}
    raise AssertionError("Unreachable SearXNG must raise RuntimeError, not stub results")


# ═══════════════════════════════════════════════════════════════════════
# ComfyUIAdapter tests
# ═══════════════════════════════════════════════════════════════════════


def test_comfyui_import() -> dict[str, Any]:
    """ComfyUIAdapter is importable and extends ImageAdapter."""
    from adapters import ImageAdapter
    a = ComfyUIAdapter(server_url="http://127.0.0.1:9999")
    assert isinstance(a, ImageAdapter)
    return {"scenario": "ComfyUI import & type check", "passed": True}


def test_comfyui_configurable_url() -> dict[str, Any]:
    """ComfyUIAdapter accepts a custom server_url."""
    a = ComfyUIAdapter(server_url="http://comfyui.local:8188")
    assert a.server_url == "http://comfyui.local:8188"
    return {"scenario": "ComfyUI configurable server_url", "passed": True}


def test_comfyui_unconfigured_raises() -> dict[str, Any]:
    """With no COMFYUI_URL configured, generate() must raise an honest
    RuntimeError telling the operator to set it — no placeholder image."""
    a = ComfyUIAdapter()
    assert a.server_url == "", f"expected unconfigured URL, got {a.server_url!r}"
    try:
        a.generate("A serene mountain landscape at sunset")
    except RuntimeError as e:
        assert "COMFYUI_URL" in str(e)
        return {"scenario": "ComfyUI unconfigured → honest RuntimeError", "passed": True}
    raise AssertionError("Unconfigured ComfyUI must raise RuntimeError, not a stub PNG")


def test_comfyui_unreachable_raises() -> dict[str, Any]:
    """A configured-but-unreachable ComfyUI must raise an honest error —
    never return a Pillow placeholder."""
    a = ComfyUIAdapter(server_url="http://127.0.0.1:1")  # connection refused
    try:
        a.generate("A serene mountain landscape at sunset", width=512, height=512)
    except RuntimeError as e:
        assert str(e).strip()
        return {"scenario": "ComfyUI unreachable → honest RuntimeError", "passed": True}
    raise AssertionError("Unreachable ComfyUI must raise RuntimeError, not a stub PNG")


def test_comfyui_edit_validation() -> dict[str, Any]:
    """edit() validates the source image before making real worklow calls."""
    a = ComfyUIAdapter(server_url="http://127.0.0.1:1")
    try:
        a.edit("/nonexistent/image.png", "Make it sunset style")
    except FileNotFoundError:
        return {"scenario": "ComfyUI edit missing source → FileNotFoundError", "passed": True}
    raise AssertionError("edit() of a missing image must raise FileNotFoundError")


# ═══════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════


def run_all() -> list[dict[str, Any]]:
    tests = [
        # SearXNG
        test_searxng_import,
        test_searxng_configurable_base_url,
        test_searxng_db_fallback_structured,
        test_searxng_db_fallback_respects_limit,
        test_searxng_unreachable_raises,
        # ComfyUI
        test_comfyui_import,
        test_comfyui_configurable_url,
        test_comfyui_unconfigured_raises,
        test_comfyui_unreachable_raises,
        test_comfyui_edit_validation,
    ]

    results = []
    for fn in tests:
        name = fn.__name__
        try:
            r = fn()
            r.setdefault("passed", True)
            r["test_name"] = name
        except Exception as e:
            import traceback
            r = {
                "test_name": name,
                "status": "FAIL",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "passed": False,
            }
        results.append(r)
    return results


if __name__ == "__main__":
    print("=" * 64)
    print("  PROVIDER KNOWLEDGE — SearXNG & ComfyUI Adapter Verification")
    print("=" * 64)
    print()

    results = run_all()
    passed = [r for r in results if r.get("passed")]
    failed = [r for r in results if not r.get("passed")]

    for r in results:
        status = "✅ PASS" if r.get("passed") else "❌ FAIL"
        scenario = r.get("scenario", r.get("test_name", "?"))
        detail = ""
        if "result_count" in r:
            detail = f" ({r['result_count']} results)"
        print(f"  {status} | {scenario}{detail}")

    print()
    print(f"  Total:  {len(results)}")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    print()

    if failed:
        print("  --- FAILURES ---")
        for r in failed:
            print(f"    {r['test_name']}: {r.get('error', 'unknown error')}")
        print()

    exit(0 if len(failed) == 0 else 1)