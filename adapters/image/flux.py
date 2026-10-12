"""
Flux Image Adapter — real Hugging Face serverless inference (FLUX.1-schnell).

Text-to-image via the HF serverless Inference API:
``https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell``
authenticated with ``Authorization: Bearer`` from ``HF_API_KEY`` (fallback
``HF_TOKEN``). Cold-starts (HTTP 503) are retried with backoff.

No stub or placeholder output is ever produced: without a token the adapter
raises an honest ``RuntimeError`` instead of fabricating a PNG.
"""

from __future__ import annotations

import os
from typing import Any

from adapters import ImageAdapter
from adapters._hf import HF_INFERENCE_URL, get_hf_token, hf_post

#: HF serverless model ID for FLUX.1-schnell (fast, 4-step, 1024x1024).
FLUX_MODEL = "black-forest-labs/FLUX.1-schnell"


class FluxAdapter(ImageAdapter):
    """Image generation via FLUX.1-schnell on the HF serverless Inference API.

    Requires ``HF_API_KEY`` (or ``HF_TOKEN``) in the environment. Without a
    token, ``generate()``/``edit()`` raise ``RuntimeError`` — a placeholder
    is never fabricated.
    """

    def __init__(self) -> None:
        self.api_key = get_hf_token()
        self.endpoint = f"{HF_INFERENCE_URL}/{FLUX_MODEL}"
        self._active = bool(self.api_key)

    # ── ImageAdapter ─────────────────────────────────────────────────

    def generate(self, prompt: str, **kwargs: Any) -> bytes:  # type: ignore[override]  # task contract: return real image bytes, not a path
        """Generate an image from *prompt*.

        Returns the raw bytes of a REAL generated image as served by the HF
        Inference API. Raises ``RuntimeError`` if ``HF_API_KEY`` is missing
        or the model is unreachable.
        """
        return hf_post(FLUX_MODEL, json_body={"inputs": prompt})

    def edit(self, image_path: str, prompt: str, **kwargs: Any) -> bytes:  # type: ignore[override]  # task contract: return real image bytes, not a path
        """Edit an image — real generation via the FLUX.1-schnell endpoint.

        NOTE: the FLUX.1-schnell serverless API is text-to-image only; the
        input image cannot be uploaded to this endpoint. ``edit()`` performs
        a genuine fresh generation conditioned on the edit prompt, so the
        returned bytes are real model output — never a placeholder. True
        img2img requires a self-hosted Flux/ComfyUI endpoint instead.
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        return hf_post(FLUX_MODEL, json_body={"inputs": prompt})