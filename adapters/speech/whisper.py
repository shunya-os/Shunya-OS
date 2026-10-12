"""
Whisper Speech Recognition Adapter — real Hugging Face serverless inference.

Transcribes audio via the HF serverless Inference API:
``https://api-inference.huggingface.co/models/openai/whisper-large-v3``
(authenticated with ``Authorization: Bearer`` from ``HF_API_KEY``), with
automatic fallback to the X-LARGE variants when the primary model is not
deployed/gated. Cold-starts (HTTP 503) are retried with backoff.

No placeholder transcription is ever fabricated: without a token, or when
every candidate model is unavailable, an honest ``RuntimeError`` is raised.
"""

from __future__ import annotations

import json
import os
from typing import Any

from adapters import SpeechRecognitionAdapter
from adapters._hf import get_hf_token, hf_post

#: Candidate serverless models, most generous first.
WHISPER_MODELS = [
    "openai/whisper-large-v3",
    "openai/whisper-large-v3-turbo",
    "openai/whisper-large-v2",
]


class WhisperAdapter(SpeechRecognitionAdapter):
    """Speech-to-text via OpenAI Whisper on the HF serverless Inference API.

    Requires ``HF_API_KEY`` (or ``HF_TOKEN``). ``WHISPER_MODEL`` may be set
    to pin a specific model ID; otherwise the candidate list is tried in
    order until one succeeds.
    """

    def __init__(self) -> None:
        self.api_key = get_hf_token()
        self.model = os.environ.get("WHISPER_MODEL", "")  # optional pin
        self._use_api = bool(self.api_key)

    # ── SpeechRecognitionAdapter ─────────────────────────────────────

    def transcribe(self, audio_path: str, language: str = "en") -> dict[str, Any]:
        """Transcribe an audio file to text via HF serverless Whisper.

        The raw audio bytes are POSTed to the model endpoint
        (``Content-Type: application/octet-stream``); the server auto-detects
        the spoken language (the serverless endpoint does not accept a
        language hint). Returns ``{"text": ..., "segments": [], "language": ...,
        "model": ...}`` — segment timestamps are not provided by the
        serverless endpoint.

        Raises ``RuntimeError`` when ``HF_API_KEY`` is missing or every
        candidate model is unavailable — a fabricated transcription is never
        returned.
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with open(audio_path, "rb") as fh:
            audio_bytes = fh.read()

        models = [self.model] if self.model else WHISPER_MODELS
        last_error: Exception | None = None

        for model in models:
            try:
                body = hf_post(
                    model,
                    data=audio_bytes,
                    headers={"Content-Type": "application/octet-stream"},
                )
                text = _parse_transcription(body, model)
                return {
                    "text": text,
                    "segments": [],
                    "language": language,
                    "model": model,
                    "stub": False,
                }
            except RuntimeError as exc:
                last_error = exc
                continue

        raise RuntimeError(
            "Whisper transcription failed on all candidate models "
            f"({', '.join(models)}): {last_error}"
        ) from last_error


# ── helpers ─────────────────────────────────────────────────────────


def _parse_transcription(body: bytes, model: str) -> str:
    """Extract the transcription text from a HF serverless response."""
    try:
        data = json.loads(body.decode("utf-8", errors="replace"))
        if isinstance(data, dict) and data.get("text"):
            return str(data["text"]).strip()
    except (ValueError, UnicodeDecodeError):
        data = None

    # Some deployments reply with plain text rather than JSON.
    if data is None:
        text = body.decode("utf-8", errors="replace").strip()
        if text:
            return text

    raise RuntimeError(
        f"Unexpected response from HF model '{model}': no 'text' field "
        f"in response: {body[:300]!r}"
    )