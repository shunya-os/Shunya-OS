"""Verify Provider Knowledge — SearXNG and ComfyUI adapter integration.

Tests:
  1. SearXNGAdapter — stub mode (no real SearXNG running)
     - search web, news, images, files
     - returns correct structure and respects limit
  2. ComfyUIAdapter — stub mode (no real ComfyUI running)
     - generate image via Pillow placeholder
     - edit image via Pillow overlay
     - generates valid PNG files
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

os.environ["COMFYUI_API_URL"] = "http://127.0.0.1:8188"  # won't be reachable

from adapters.search.searxng import SearXNGAdapter
from adapters.image.comfyui import ComfyUIAdapter


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


def test_searxng_stub_web_search() -> dict[str, Any]:
    """Stub search returns structured results for web category."""
    a = SearXNGAdapter(base_url="http://127.0.0.1:9999")  # unreachable → stub
    results = a.search("test", limit=5, categories=["web"])
    assert len(results) > 0
    for r in results:
        assert "title" in r
        assert "url" in r
        assert "snippet" in r
    assert len(results) <= 5
    return {
        "scenario": "SearXNG web search (stub)",
        "result_count": len(results),
        "passed": True,
    }


def test_searxng_stub_news_search() -> dict[str, Any]:
    """Stub search returns results for news category."""
    a = SearXNGAdapter(base_url="http://127.0.0.1:9999")
    results = a.search("news", categories=["news"])
    assert len(results) > 0
    return {
        "scenario": "SearXNG news search (stub)",
        "first_title": results[0]["title"],
        "passed": True,
    }


def test_searxng_stub_images_search() -> dict[str, Any]:
    """Stub search returns results for images category."""
    a = SearXNGAdapter(base_url="http://127.0.0.1:9999")
    results = a.search("images", categories=["images"])
    assert len(results) > 0
    return {
        "scenario": "SearXNG images search (stub)",
        "first_title": results[0]["title"],
        "passed": True,
    }


def test_searxng_stub_files_search() -> dict[str, Any]:
    """Stub search returns results for files category."""
    a = SearXNGAdapter(base_url="http://127.0.0.1:9999")
    results = a.search("package", categories=["files"])
    assert len(results) > 0
    return {
        "scenario": "SearXNG files search (stub)",
        "first_title": results[0]["title"],
        "passed": True,
    }


def test_searxng_stub_respects_limit() -> dict[str, Any]:
    """Stub search respects the limit parameter."""
    a = SearXNGAdapter(base_url="http://127.0.0.1:9999")
    results = a.search("test", limit=2)
    assert len(results) <= 2
    return {
        "scenario": "SearXNG respects limit (stub)",
        "count": len(results),
        "passed": True,
    }


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


def test_comfyui_default_url() -> dict[str, Any]:
    """ComfyUIAdapter defaults to http://127.0.0.1:8188."""
    a = ComfyUIAdapter()
    assert a.server_url == "http://127.0.0.1:8188"
    return {"scenario": "ComfyUI default URL", "passed": True}


def test_comfyui_stub_generate() -> dict[str, Any]:
    """Stub generate creates a valid PNG file."""
    a = ComfyUIAdapter(server_url="http://127.0.0.1:9999")
    path = a.generate("A serene mountain landscape at sunset", width=512, height=512)
    assert os.path.isfile(path), f"File not found: {path}"
    assert path.endswith(".png"), f"Not a PNG: {path}"
    size = os.path.getsize(path)
    assert size > 500, f"PNG too small ({size} bytes)"
    return {
        "scenario": "ComfyUI stub generate (Pillow)",
        "path": path,
        "size_bytes": size,
        "passed": True,
    }


def test_comfyui_stub_edit() -> dict[str, Any]:
    """Stub edit opens a source image, overlays text, and saves a new PNG."""
    # First, create a stub image to edit
    a = ComfyUIAdapter(server_url="http://127.0.0.1:9999")
    source_path = a.generate("Source image for editing", width=256, height=256)
    assert os.path.isfile(source_path)

    edit_path = a.edit(source_path, "Make it sunset style", denoise=0.8)
    assert os.path.isfile(edit_path), f"Edited file not found: {edit_path}"
    assert edit_path != source_path, "Edited path should differ from source"
    size = os.path.getsize(edit_path)
    assert size > 500, f"Edited PNG too small ({size} bytes)"
    return {
        "scenario": "ComfyUI stub edit (Pillow)",
        "source": source_path,
        "edited": edit_path,
        "size_bytes": size,
        "passed": True,
    }


def test_comfyui_stub_generate_with_args() -> dict[str, Any]:
    """Stub generate accepts and applies kwargs (seed, steps, dimensions)."""
    a = ComfyUIAdapter(server_url="http://127.0.0.1:9999")
    path = a.generate(
        "Test image",
        width=200,
        height=300,
        seed=12345,
        steps=30,
        negative_prompt="bad quality, blurry",
    )
    assert os.path.isfile(path)
    from PIL import Image
    with Image.open(path) as img:
        assert img.size == (200, 300), f"Expected 200x300, got {img.size}"
    return {
        "scenario": "ComfyUI stub generate with kwargs",
        "path": path,
        "dimensions": "200x300",
        "passed": True,
    }


# ═══════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════


def run_all() -> list[dict[str, Any]]:
    tests = [
        # SearXNG
        test_searxng_import,
        test_searxng_configurable_base_url,
        test_searxng_stub_web_search,
        test_searxng_stub_news_search,
        test_searxng_stub_images_search,
        test_searxng_stub_files_search,
        test_searxng_stub_respects_limit,
        # ComfyUI
        test_comfyui_import,
        test_comfyui_configurable_url,
        test_comfyui_default_url,
        test_comfyui_stub_generate,
        test_comfyui_stub_edit,
        test_comfyui_stub_generate_with_args,
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
        elif "first_title" in r:
            detail = f" [{r['first_title'][:50]}]"
        elif "size_bytes" in r:
            detail = f" ({r['size_bytes']} bytes)"
        elif "dimensions" in r:
            detail = f" ({r['dimensions']})"
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
            tb = r.get("traceback")
            if tb:
                for line in tb.splitlines()[-5:]:
                    print(f"      {line}")
        print()

    exit(0 if len(failed) == 0 else 1)