"""
ComfyUI Image Adapter — real REST API integration.

Communicates with a running ComfyUI instance to queue txt2img/img2img
workflows, poll for completion, and download the generated images.

Never fabricates output: if ``COMFYUI_URL`` (or the legacy
``COMFYUI_API_URL``) is not configured, an honest ``RuntimeError`` asks the
operator to set it — no Pillow placeholder is produced.
"""

from __future__ import annotations

import logging
import os
import tempfile
import time
from typing import Any

import requests

from adapters import ImageAdapter

logger = logging.getLogger(__name__)

# How long (seconds) to wait for a ComfyUI prompt to finish
_DEFAULT_POLL_TIMEOUT = 300
_DEFAULT_POLL_INTERVAL = 1.0

# Default workflow template — a minimal txt2img payload.
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
    """Image generation and editing via the ComfyUI REST API.

    Parameters
    ----------
    server_url : str | None
        Base URL of the ComfyUI instance. Defaults to the ``COMFYUI_URL``
        (or legacy ``COMFYUI_API_URL``) environment variable. When neither is
        set, calls raise ``RuntimeError``.
    workflow : dict | None
        Custom workflow template. The ``"text"`` field in the CLIPTextEncode
        node will be replaced with the prompt on each call.
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
            server_url
            or os.environ.get("COMFYUI_URL")
            or os.environ.get("COMFYUI_API_URL")
            or ""
        ).rstrip("/")
        self._workflow_template = workflow or dict(_DEFAULT_WORKFLOW)
        self.poll_timeout = poll_timeout
        self.poll_interval = poll_interval

    # ── ImageAdapter ─────────────────────────────────────────────────

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate an image from *prompt*; returns the output image path.

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
        self._require_config()
        try:
            return self._real_generate(prompt, **kwargs)
        except (requests.RequestException, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"ComfyUI at {self.server_url} failed during generation: {exc}"
            ) from exc

    def edit(self, image_path: str, prompt: str, **kwargs: Any) -> str:
        """Edit an image via an img2img workflow; returns the output path."""
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        self._require_config()
        try:
            return self._real_edit(image_path, prompt, **kwargs)
        except (requests.RequestException, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"ComfyUI at {self.server_url} failed during edit: {exc}"
            ) from exc

    # ── Configuration guard ──────────────────────────────────────────

    def _require_config(self) -> None:
        """Raise an honest error when no ComfyUI endpoint is configured."""
        if not self.server_url:
            raise RuntimeError(
                "COMFYUI_URL not configured — set COMFYUI_URL (e.g. "
                "http://127.0.0.1:8188) in .env to enable real image "
                "generation via ComfyUI. No placeholder output is produced."
            )

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