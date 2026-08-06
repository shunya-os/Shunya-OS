"""
Kokoro TTS Adapter — STUB implementation.

Kokoro (https://github.com/remsky/Kokoro-FastAPI) is a fast,
open-weight TTS model.  It is typically self-hosted as a FastAPI
service or run via the ``kokoro`` Python package.

This stub documents the integration points for a Kokoro FastAPI
server or direct model usage.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

from adapters import SpeechSynthesisAdapter


class KokoroAdapter(SpeechSynthesisAdapter):
    """Text-to-speech via Kokoro.

    .. caution:: **STUB** — requires Kokoro server or Python package.
       Self-hosted server: set ``KOKORO_API_URL`` (default
       ``http://127.0.0.1:8880``).

    Kokoro supports multiple voices (American/British English,
    Japanese, Chinese, French, Korean, etc).
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
        self.api_url = os.environ.get("KOKORO_API_URL", "http://127.0.0.1:8880")
        self._active = bool(os.environ.get("KOKORO_API_URL"))

    # ── SpeechSynthesisAdapter ───────────────────────────────────────

    def synthesize(self, text: str, voice: str = "af_heart", **kwargs: Any) -> str:
        """Synthesise speech via Kokoro.

        Parameters (kwargs):
          - speed (float): playback speed (default ``1.0``)
          - format (str): output format — ``"wav"`` (default) or ``"mp3"``

        Voices: see ``KNOWN_VOICES``.  The default ``af_heart`` is an
        American female voice.

        REST API (real):
          POST ``{api_url}/v1/audio/speech`` with JSON:
          ``{"model": "kokoro", "input": text, "voice": voice}``

        STUB: Returns a placeholder WAV.
        """
        if voice not in self.KNOWN_VOICES:
            print(
                f"[KokoroAdapter] WARNING: Unknown voice {voice!r}. "
                f"Known voices: {list(self.KNOWN_VOICES)[:5]}... "
                f"Using anyway."
            )

        if self._active:
            raise NotImplementedError(
                "KokoroAdapter.synthesize: KOKORO_API_URL is set but the HTTP "
                f"integration is not yet implemented. Server: {self.api_url}"
            )

        out_dir = tempfile.mkdtemp(prefix="shunya_kokoro_")
        out_path = os.path.join(out_dir, "speech.wav")
        _write_stub_wav(out_path)

        print(
            f"[KokoroAdapter] STUB: synthesize({text!r}, voice={voice!r}) → {out_path}. "
            "Set KOKORO_API_URL to connect to a running Kokoro FastAPI server."
        )
        return out_path


# ── helpers ─────────────────────────────────────────────────────────


def _write_stub_wav(path: str) -> None:
    """Write a minimal valid WAV header (44 bytes, 1 sample silence)."""
    import struct
    sample_rate = 8000
    num_samples = 1
    data_size = num_samples * 2
    with open(path, "wb") as fh:
        fh.write(b"RIFF")
        fh.write(struct.pack("<I", 36 + data_size))
        fh.write(b"WAVE")
        fh.write(b"fmt ")
        fh.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
        fh.write(b"data")
        fh.write(struct.pack("<I", data_size))
        fh.write(struct.pack("<h", 0))
