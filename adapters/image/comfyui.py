"""
ComfyUI Image Adapter — Full implementation with Pillow stub fallback.

ComfyUI is a node-based diffusion workflow engine with a REST API.
This adapter communicates with a running ComfyUI instance to queue
prompts, poll for completion, and download generated images.

When ComfyUI is unreachable, it falls back to Pillow-generated placeholder
images so the caller never receives a hard failure.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from adapters import ImageAdapter

logger = logging.getLogger(__name__)

# How long (seconds) to wait for a ComfyUI prompt to finish
_DEFAULT_POLL_TIMEOUT = 300
_DEFAULT_POLL_INTERVAL = 1.0

# Default workflow template — a minimal txt2img payload.
# The real workflow ID is returned by the queue prompt endpoint.
_DEFAULT_WORKFLOW: dict[str, Any] = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 42,
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0],
        },
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"},
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "prompt placeholder", "clip": ["4", 1]},
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "", "clip": ["4", 1]},
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": "shunya_comfyui", "images": ["8", 0]},
    },
}


class ComfyUIAdapter(ImageAdapter):
    """Image generation and editing via ComfyUI REST API.

    Parameters
    ----------
    server_url : str
        Base URL of the ComfyUI instance (default ``http://127.0.0.1:8188``).
    workflow : dict | None
        Custom workflow template. The ``"text"`` field in the CLIPTextEncode
        node (class_type ``"CLIPTextEncode"``) will be replaced with the
        prompt on each call. If ``None``, a default txt2img workflow is used.
    poll_timeout : int
        Max seconds to wait for a generation to complete.
    poll_interval : float
        Seconds between status polls.
    """

    def __init__(
        self,
        server_url: str | None = None,
        workflow: dict[str, Any] | None = None,
        poll_timeout: int = _DEFAULT_POLL_TIMEOUT,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
    ) -> None:
        self.server_url = (
            (server_url or os.environ.get("COMFYUI_API_URL", "http://127.0.0.1:8188"))
            .rstrip("/")
        )
        self._workflow_template = workflow or dict(_DEFAULT_WORKFLOW)
        self.poll_timeout = poll_timeout
        self.poll_interval = poll_interval
        self._available: bool | None = None  # lazily checked

    # ── ImageAdapter ─────────────────────────────────────────────────

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate an image from *prompt*.

        kwargs
        ------
        negative_prompt : str
            Negative prompt text.
        width : int
            Output width (default 1024).
        height : int
            Output height (default 1024).
        seed : int
            Random seed (default 42).
        steps : int
            Sampling steps (default 20).
        """
        if self._check_available():
            return self._real_generate(prompt, **kwargs)
        return self._stub_generate(prompt, **kwargs)

    def edit(self, image_path: str, prompt: str, **kwargs: Any) -> str:
        """Edit an image via img2img workflow.

        kwargs
        ------
        denoise : float
            How much to transform the input (default 0.7).
        negative_prompt : str
            Negative prompt text.
        seed : int
            Random seed.
        steps : int
            Sampling steps.
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        if self._check_available():
            return self._real_edit(image_path, prompt, **kwargs)
        return self._stub_edit(image_path, prompt, **kwargs)

    # ── Availability check ───────────────────────────────────────────

    def _check_available(self) -> bool:
        """Lazily probe whether ComfyUI is reachable via its ``/queue`` or ``/system_stats`` endpoint."""
        if self._available is not None:
            return self._available

        try:
            req = urllib.request.Request(
                f"{self.server_url}/system_stats",
                method="GET",
                headers={"User-Agent": "SHUNYA-OS/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5):
                self._available = True
        except (urllib.error.URLError, OSError, ValueError):
            logger.warning("ComfyUI unavailable at %s — using Pillow stub", self.server_url)
            self._available = False
        return self._available

    # ── Real ComfyUI generation ──────────────────────────────────────

    def _real_generate(self, prompt: str, **kwargs: Any) -> str:
        """Queue a prompt on ComfyUI and return the output image path."""
        import requests

        workflow = self._build_workflow(prompt, is_edit=False, **kwargs)
        prompt_id = self._queue_prompt(requests, workflow)
        output = self._poll_for_output(requests, prompt_id)
        return self._download_image(requests, output)

    def _real_edit(self, image_path: str, prompt: str, **kwargs: Any) -> str:
        """Upload an image to ComfyUI, queue an img2img prompt, download result."""
        import requests

        # Upload the image first
        image_name = os.path.basename(image_path)
        with open(image_path, "rb") as fh:
            resp = requests.post(
                f"{self.server_url}/upload/image",
                files={"image": (image_name, fh, "image/png")},
                timeout=60,
            )
            resp.raise_for_status()

        workflow = self._build_workflow(prompt, is_edit=True, image_name=image_name, **kwargs)
        prompt_id = self._queue_prompt(requests, workflow)
        output = self._poll_for_output(requests, prompt_id)
        return self._download_image(requests, output)

    # ── Workflow helpers ─────────────────────────────────────────────

    def _build_workflow(
        self,
        prompt: str,
        is_edit: bool = False,
        image_name: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Deep-copy the template and inject prompt parameters."""
        import copy

        workflow = copy.deepcopy(self._workflow_template)

        # Inject prompt into all CLIPTextEncode nodes
        negative = kwargs.get("negative_prompt", "")
        seed = kwargs.get("seed", 42)
        steps = kwargs.get("steps", 20)
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        denoise = kwargs.get("denoise", 0.7)

        for node_id, node in workflow.items():
            if node.get("class_type") == "CLIPTextEncode":
                if not node["inputs"].get("text") or node["inputs"]["text"] == "prompt placeholder":
                    node["inputs"]["text"] = prompt
                elif negative and node["inputs"]["text"] == "":
                    node["inputs"]["text"] = negative

            if node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = seed
                node["inputs"]["steps"] = steps
                node["inputs"]["denoise"] = denoise if is_edit else 1.0

            if node.get("class_type") == "EmptyLatentImage":
                node["inputs"]["width"] = width
                node["inputs"]["height"] = height

            # Img2img: replace EmptyLatentImage with LoadImage
            if is_edit and node.get("class_type") == "EmptyLatentImage":
                node["class_type"] = "LoadImage"
                node["inputs"] = {"image": image_name}

        return workflow

    def _queue_prompt(self, requests_module: Any, workflow: dict[str, Any]) -> str:
        """POST workflow to ComfyUI and return the prompt_id."""
        resp = requests_module.post(
            f"{self.server_url}/prompt",
            json={"prompt": workflow},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        prompt_id: str = data["prompt_id"]
        return prompt_id

    def _poll_for_output(self, requests_module: Any, prompt_id: str) -> dict[str, Any]:
        """Poll ``/history/{prompt_id}`` until generation completes."""
        deadline = time.time() + self.poll_timeout
        while time.time() < deadline:
            resp = requests_module.get(
                f"{self.server_url}/history/{prompt_id}",
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    history = data[prompt_id]
                    if "outputs" in history:
                        return history["outputs"]
            time.sleep(self.poll_interval)

        raise TimeoutError(
            f"ComfyUI prompt {prompt_id} did not finish within {self.poll_timeout}s"
        )

    def _download_image(self, requests_module: Any, outputs: dict[str, Any]) -> str:
        """Download the first output image from a completed prompt."""
        # Find the first image in outputs
        for _node_id, node_out in outputs.items():
            for img in node_out.get("images", []):
                filename = img["filename"]
                subfolder = img.get("subfolder", "")
                resp = requests_module.get(
                    f"{self.server_url}/view",
                    params={"filename": filename, "subfolder": subfolder, "type": "output"},
                    timeout=30,
                )
                resp.raise_for_status()

                out_dir = tempfile.mkdtemp(prefix="shunya_comfyui_")
                dest = os.path.join(out_dir, filename)
                with open(dest, "wb") as fh:
                    fh.write(resp.content)
                return dest

        raise RuntimeError("ComfyUI returned no output images")

    # ── Stub (Pillow) fallback ───────────────────────────────────────

    def _stub_generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a Pillow placeholder image with prompt text rendered on it."""
        from PIL import Image, ImageDraw, ImageFont

        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        seed = kwargs.get("seed", 42)

        img = Image.new("RGB", (width, height), color=(30, 30, 40))
        draw = ImageDraw.Draw(img)

        # Draw a subtle gradient-like overlay
        for y in range(height):
            r = int(30 + (y / height) * 40)
            g = int(30 + (y / height) * 20)
            b = int(40 + (y / height) * 60)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Draw a decorative border
        draw.rectangle([10, 10, width - 10, height - 10], outline=(100, 120, 200), width=2)

        # Draw prompt text (centered, wrapped)
        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
            )
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
            )
        except (IOError, OSError):
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Title
        title = "ComfyUI — STUB Mode"
        bbox = draw.textbbox((0, 0), title, font=font_large)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, 40), title, fill=(200, 220, 255), font=font_large)

        # Prompt text (wrapped)
        max_w = width - 80
        words = prompt.split()
        lines: list[str] = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            tb = draw.textbbox((0, 0), test, font=font_small)
            if (tb[2] - tb[0]) > max_w:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)

        y_pos = 120
        for line in lines:
            draw.text((40, y_pos), line, fill=(220, 220, 240), font=font_small)
            y_pos += 28

        # Info footer
        footer = f"seed={seed}  {width}×{height}  [ComfyUI offline — Pillow stub]"
        fb = draw.textbbox((0, 0), footer, font=font_small)
        draw.text(
            ((width - (fb[2] - fb[0])) // 2, height - 60),
            footer,
            fill=(150, 160, 180),
            font=font_small,
        )

        out_dir = tempfile.mkdtemp(prefix="shunya_comfyui_")
        stub_path = os.path.join(out_dir, "comfyui_stub.png")
        img.save(stub_path, "PNG")

        logger.info(
            "ComfyUIAdapter STUB: generate(%r) → %s (%dx%d)",
            prompt, stub_path, width, height,
        )
        return stub_path

    def _stub_edit(self, image_path: str, prompt: str, **kwargs: Any) -> str:
        """Edit a placeholder via Pillow — overlay prompt text on the source image."""
        from PIL import Image, ImageDraw, ImageFont

        denoise = kwargs.get("denoise", 0.7)

        try:
            img = Image.open(image_path).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Cannot open image {image_path}: {exc}") from exc

        w, h = img.size
        draw = ImageDraw.Draw(img)

        # Semi-transparent overlay effect (simulated with dark stripe)
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([0, h - 80, w, h], fill=(0, 0, 0, 160))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
            )
        except (IOError, OSError):
            font = ImageFont.load_default()

        # Edit badge
        badge = f"EDIT: {prompt[:60]}…" if len(prompt) > 60 else f"EDIT: {prompt}"
        draw.text((20, h - 60), badge, fill=(255, 220, 100), font=font)

        info = f"denoise={denoise}  source={os.path.basename(image_path)}  [Pillow stub]"
        draw.text((20, h - 32), info, fill=(180, 180, 200), font=font)

        out_dir = tempfile.mkdtemp(prefix="shunya_comfyui_edit_")
        stem = os.path.splitext(os.path.basename(image_path))[0]
        stub_path = os.path.join(out_dir, f"{stem}_edited.png")
        img.save(stub_path, "PNG")

        logger.info(
            "ComfyUIAdapter STUB: edit(%s, %r) → %s",
            image_path, prompt, stub_path,
        )
        return stub_path