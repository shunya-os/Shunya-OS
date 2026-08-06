"""
ComfyUI Image Adapter — STUB implementation.

ComfyUI is a node-based diffusion workflow engine with a REST API.
This stub documents the endpoints and payload shape for integration.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

from adapters import ImageAdapter


class ComfyUIAdapter(ImageAdapter):
    """Image generation and editing via ComfyUI.

    .. caution:: **STUB** — a running ComfyUI instance is required.
       Set ``COMFYUI_API_URL`` (default ``http://127.0.0.1:8188``) and
       ``COMFYUI_WORKFLOW_DIR`` to activate.
    """

    def __init__(self) -> None:
        self.api_url = os.environ.get("COMFYUI_API_URL", "http://127.0.0.1:8188")
        self.workflow_dir = os.environ.get("COMFYUI_WORKFLOW_DIR", "")
        self._active = False  # Toggle once workflows are loaded

    # ── ImageAdapter ─────────────────────────────────────────────────

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate an image via a ComfyUI workflow.

        Steps (real):
          1. Load or construct a workflow JSON (txt2img, img2img, etc.)
          2. POST to ``{api_url}/prompt`` with ``{"prompt": workflow}``
          3. Poll ``{api_url}/history/{prompt_id}`` until completed
          4. Download output image from ``{api_url}/view?filename=...``

        STUB: Returns a placeholder path.
        """
        out_dir = tempfile.mkdtemp(prefix="shunya_comfyui_")
        stub_path = os.path.join(out_dir, "comfyui_stub.png")

        # Write a minimal valid PNG (not a real image)
        _write_stub_png(stub_path, prompt)

        print(
            f"[ComfyUIAdapter] STUB: generate({prompt!r}) → {stub_path}. "
            f"Connect to a running ComfyUI at {self.api_url} for real generation."
        )
        return stub_path

    def edit(self, image_path: str, prompt: str, **kwargs: Any) -> str:
        """Edit an image via img2img workflow.

        STUB: Returns a placeholder path.
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        out_dir = tempfile.mkdtemp(prefix="shunya_comfyui_edit_")
        stem = os.path.splitext(os.path.basename(image_path))[0]
        stub_path = os.path.join(out_dir, f"{stem}_edited.png")

        _write_stub_png(stub_path, f"edit({prompt})")
        print(
            f"[ComfyUIAdapter] STUB: edit({image_path}, {prompt!r}) → {stub_path}"
        )
        return stub_path


# ── helpers ─────────────────────────────────────────────────────────


def _write_stub_png(path: str, message: str) -> None:
    """Write a stub placeholder PNG with *message* embedded."""
    # Minimal 1×1 blue pixel PNG (valid)
    _1x1_blue_png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    with open(path, "wb") as fh:
        fh.write(_1x1_blue_png)
