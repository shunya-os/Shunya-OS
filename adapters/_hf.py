"""Shared Hugging Face Inference API helper for the adapters package.

Same token semantics as the canonical app helper (``app.media.service.
_get_hf_token``): the token is read from ``HF_API_KEY`` with ``HF_TOKEN``
as fallback. All model calls hit the serverless Inference API
(``https://api-inference.huggingface.co/models/<model>``) with
``Authorization: Bearer <token>``. HTTP 503 (model cold start) and
transient network errors are retried with backoff so callers get real
model output — nothing here ever fabricates a response.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

HF_INFERENCE_URL = "https://api-inference.huggingface.co/models"

# HTTP status meaning "model is loading / cold start" — worth retrying.
_COLD_START_STATUS = 503

# Other statuses that mean "this model will not serve us" — no retry.
_INVALID_MODEL_STATUSES = (400, 401, 402, 403, 404, 422)


def get_hf_token() -> str:
    """Resolve the Hugging Face API token (HF_API_KEY, then HF_TOKEN)."""
    return (os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN") or "").strip()


def require_hf_token() -> str:
    """Return the HF token or raise an honest error — never fake output."""
    token = get_hf_token()
    if not token:
        raise RuntimeError("HF_API_KEY not configured")
    return token


def hf_post(
    model: str,
    *,
    data: Optional[bytes] = None,
    json_body: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
    retries: int = 3,
    backoff: float = 6.0,
    timeout: float = 180.0,
) -> bytes:
    """POST to an HF serverless Inference API endpoint.

    Returns the raw response body (image bytes, audio bytes, or JSON text).
    HTTP 503 (model cold start) and transient network errors are retried up
    to ``retries`` times with ``backoff`` seconds between attempts. Any other
    HTTP error (model not deployed, gated, etc.) raises immediately.

    Raises ``RuntimeError`` with a clear message on failure — the caller
    never receives a fabricated response.
    """
    import requests

    token = require_hf_token()
    url = f"{HF_INFERENCE_URL}/{model}"
    hdrs = {"Authorization": f"Bearer {token}"}
    if headers:
        hdrs.update(headers)

    last_error: Optional[Exception] = None
    for attempt in range(retries):
        try:
            resp = requests.post(
                url, data=data, json=json_body, headers=hdrs, timeout=timeout
            )
            if resp.status_code == _COLD_START_STATUS:
                last_error = RuntimeError(
                    f"model {model} is cold-starting (HTTP 503) — "
                    f"attempt {attempt + 1}/{retries}"
                )
                if attempt < retries - 1:
                    time.sleep(backoff)
                continue
            if resp.status_code in _INVALID_MODEL_STATUSES:
                raise RuntimeError(
                    f"Hugging Face rejected model '{model}' (HTTP {resp.status_code}): "
                    f"{resp.text[:300]}. The model may be gated, private, or not "
                    f"deployed on the serverless Inference API."
                )
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(backoff)

    raise RuntimeError(
        f"Hugging Face Inference API call to '{model}' failed after {retries} "
        f"attempts: {last_error}"
    ) from last_error