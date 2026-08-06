"""
Flux Image Adapter — STUB implementation.

Flux (by Black Forest Labs / Stability AI) is a text-to-image model
available via Replicate, Fal.ai, and local inference.
This stub documents the API surface for a remote provider call.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

from adapters import ImageAdapter


class FluxAdapter(ImageAdapter):
    """Image generation via Flux (Replicate / Fal.ai / local).

    .. caution:: **STUB** — requires an API key or local model.
       Set ``FLUX_API_KEY`` and ``FLUX_ENDPOINT`` environment variables
       to activate.

    Endpoints (one of):
      - Replicate: ``https://api.replicate.com/v1/predictions``
      - Fal.ai:    ``https://fal.run/fal-ai/flux``
      - Local:     ComfyUI workflow with Flux checkpoint
    """

    def __init__(self) -> None:
        self.api_key = os.environ.get("FLUX_API_KEY", "")
        self.endpoint = os.environ.get(
            "FLUX_ENDPOINT", "https://api.replicate.com/v1/predictions"
        )
        self._active = bool(self.api_key)

    # ── ImageAdapter ─────────────────────────────────────────────────

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate from text prompt.

        Parameters (kwargs):
          - aspect_ratio (str): e.g. ``"16:9"``, ``"1:1"`` (default ``"1:1"``)
          - num_outputs (int): images to generate (default ``1``)
          - num_inference_steps (int): (default ``28``)
          - guidance_scale (float): (default ``3.5``)
          - seed (int | None): (default ``None``)

        STUB: Returns a placeholder path.
        """
        if self._active:
            raise NotImplementedError(
                "FluxAdapter.generate: API key is set but the HTTP integration "
                f"is not yet implemented. Endpoint: {self.endpoint}"
            )

        out_dir = tempfile.mkdtemp(prefix="shunya_flux_")
        stub_path = os.path.join(out_dir, "flux_stub.png")
        _write_stub_png(stub_path, prompt)
        print(
            f"[FluxAdapter] STUB: generate({prompt!r}) → {stub_path}. "
            "Set FLUX_API_KEY and FLUX_ENDPOINT for real generation."
        )
        return stub_path

    def edit(self, image_path: str, prompt: str, **kwargs: Any) -> str:
        """Edit an image via Flux img2img / inpainting.

        Parameters (kwargs):
          - strength (float): influence of the input image (default ``0.8``)
          - guidance_scale (float): (default ``7.5``)

        STUB: Returns a placeholder path.
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        out_dir = tempfile.mkdtemp(prefix="shunya_flux_edit_")
        stem = os.path.splitext(os.path.basename(image_path))[0]
        stub_path = os.path.join(out_dir, f"{stem}_flux_edited.png")
        _write_stub_png(stub_path, f"edit({prompt})")
        print(
            f"[FluxAdapter] STUB: edit({image_path}, {prompt!r}) → {stub_path}"
        )
        return stub_path


# ── helpers ─────────────────────────────────────────────────────────


def _write_stub_png(path: str, _message: str) -> None:
    """Write a minimal valid 1×1 PNG placeholder."""
    _1x1_green_png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    with open(path, "wb") as fh:
        fh.write(_1x1_green_png)
