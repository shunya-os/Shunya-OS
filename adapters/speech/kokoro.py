"""
Kokoro TTS Adapter — real speech synthesis.

Primary path: Kokoro-82M on the HF serverless Inference API
(``https://api-inference.huggingface.co/models/hexgrad/Kokoro-82M``) with
``Authorization: Bearer`` from ``HF_API_KEY``. If ``KOKORO_API_URL`` is set
(a self-hosted Kokoro FastAPI server), the documented REST contract is used
instead: ``POST {api_url}/v1/audio/speech`` with JSON
``{"model": "kokoro", "input": text, "voice": voice}``.

The synthesized audio is written to a real WAV file and its path returned.
No placeholder/silence audio is ever fabricated: missing credentials or an
unreachable service raise an honest ``RuntimeError``.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

from adapters import SpeechSynthesisAdapter
from adapters._hf import hf_post

#: HF serverless model ID for Kokoro-82M (open-weight TTS).
KOKORO_MODEL = "hexgrad/Kokoro-82M"


class KokoroAdapter(SpeechSynthesisAdapter):
    """Text-to-speech via Kokoro (HF serverless or self-hosted FastAPI).

    Requires ``HF_API_KEY`` (or ``HF_TOKEN``) unless ``KOKORO_API_URL`` is
    set. Returns the path of a genuinely synthesized WAV file.
    """

    # Known voices — from the Kokoro model card
    KNOWN_VOICES: dict[str, str] = {
        "af_heart": "American Female — Heart",
        "af_bella": "American Female — Bella",
        "af_nicole": "American Female — Nicole",
        "af_aoede": "American Female — Aoede",
        "af_kore": "American Female — Kore",
        "af_sarah": "American Female — Sarah",
        "af_nova": "American Female — Nova",
        "af_sky": "American Female — Sky",
        "am_adam": "American Male — Adam",
        "am_echo": "American Male — Echo",
        "am_eric": "American Male — Eric",
        "am_fenrir": "American Male — Fenrir",
        "am_liam": "American Male — Liam",
        "am_murmur": "American Male — Murmur",
        "am_puck": "American Male — Puck",
        "bf_emma": "British Female — Emma",
        "bf_isabella": "British Female — Isabella",
        "bm_george": "British Male — George",
        "bm_lewis": "British Male — Lewis",
        "ff_siwis": "French Female — Siwis",
        "fm_blue": "French Male — Blue",
        "jf_nezumi": "Japanese Female — Nezumi",
        "jf_tebukuro": "Japanese Female — Tebukuro",
        "jm_kumo": "Japanese Male — Kumo",
        "zf_xiaobei": "Chinese Female — Xiaobei",
        "zf_xiaoyi": "Chinese Female — Xiaoyi",
        "zf_xiaoman": "Chinese Female — Xiaoman",
        "zf_xiaoqiu": "Chinese Female — Xiaoqiu",
        "zf_xiaoyun": "Chinese Female — Xiaoyun",
        "zf_xiaolian": "Chinese Female — Xiaolian",
    }

    def __init__(self) -> None:
        self.api_url = os.environ.get("KOKORO_API_URL", "").rstrip("/")
        self._active = bool(self.api_url)

    # ── SpeechSynthesisAdapter ───────────────────────────────────────

    def synthesize(self, text: str, voice: str = "af_heart", **kwargs: Any) -> str:
        """Synthesise speech via Kokoro and return the path of the WAV file.

        Parameters (kwargs):
          - format (str): output extension — ``"wav"`` (default) or ``"mp3"``
            (chosen by the audio MIME served; the extension is a hint only).

        If ``KOKORO_API_URL`` is set the self-hosted REST API is used; else
        the HF serverless endpoint. Raises ``RuntimeError`` with an honest
        message when credentials are missing or synthesis fails — a fake WAV
        is never written.
        """
        if not text.strip():
            raise ValueError("KokoroTTS: empty text — nothing to synthesise")

        if voice not in self.KNOWN_VOICES:
            print(
                f"[KokoroAdapter] WARNING: Unknown voice {voice!r}. "
                f"Known voices: {list(self.KNOWN_VOICES)[:5]}... "
                f"Using anyway."
            )

        fmt = str(kwargs.get("format", "wav")).lstrip(".")
        if fmt not in ("wav", "mp3"):
            fmt = "wav"

        if self._active:
            audio_bytes = self._synthesize_selfhosted(text, voice)
        else:
            audio_bytes = self._synthesize_hf(text, voice)

        out_dir = tempfile.mkdtemp(prefix="shunya_kokoro_")
        out_path = os.path.join(out_dir, f"speech.{fmt}")
        with open(out_path, "wb") as fh:
            fh.write(audio_bytes)
        return out_path

    # ── Real synthesis paths ──────────────────────────────────────────

    def _synthesize_hf(self, text: str, voice: str) -> bytes:
        """Synthesise via HF serverless Kokoro-82M (audio bytes returned).

        Tries the canonical payload shape first; retries once with the
        alternate ``parameters`` shape on failure.
        """
        payload = {"inputs": text, "voice": voice}
        try:
            return hf_post(KOKORO_MODEL, json_body=payload)
        except RuntimeError:
            # Retry once with the alternate parameter shape.
            return hf_post(
                KOKORO_MODEL, json_body={"inputs": text, "parameters": {"voice": voice}}
            )

    def _synthesize_selfhosted(self, text: str, voice: str) -> bytes:
        """Synthesise via a self-hosted Kokoro FastAPI server."""
        import requests

        url = f"{self.api_url}/v1/audio/speech"
        payload = {"model": "kokoro", "input": text, "voice": voice}
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Kokoro self-hosted server at {self.api_url} failed: {exc}"
            ) from exc