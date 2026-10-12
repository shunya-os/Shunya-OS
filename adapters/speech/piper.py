"""
Piper TTS Adapter — real speech synthesis.

Preferred path: local Piper inference (``piper-tts`` Python API or the
``piper`` CLI with ``.onnx``/``.json`` voice files). When no local engine is
installed, falls back to the HF serverless Inference API with
``rhasspy/piper-voices`` (Bearer token from ``HF_API_KEY``), retrying once
on cold start.

A fake/silence WAV is never written: missing voice files, a missing token,
or an unavailable service all raise an honest ``RuntimeError``.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from adapters import SpeechSynthesisAdapter
from adapters._hf import hf_post

#: HF serverless model ID attempted when no local piper engine exists.
PIPER_HF_MODEL = "rhasspy/piper-voices"


class PiperAdapter(SpeechSynthesisAdapter):
    """Text-to-speech via Piper (local engine or HF serverless)."""

    def __init__(self) -> None:
        self.model_dir = Path(
            os.environ.get("PIPER_MODEL_DIR", os.path.expanduser("~/.piper-tts/models/"))
        )
        self._cli_available = _which("piper") is not None
        self._python_available = _python_pkg_available("piper")
        self._active = self._cli_available or self._python_available

    # ── SpeechSynthesisAdapter ───────────────────────────────────────

    def synthesize(self, text: str, voice: str = "default", **kwargs: Any) -> str:
        """Synthesise speech to a real WAV file and return its path.

        Voice files are expected at ``{model_dir}/{voice}.onnx`` and
        ``{model_dir}/{voice}.json`` for local synthesis; otherwise the HF
        serverless endpoint is attempted. Raises an honest ``RuntimeError``
        when nothing is available — no stub audio is ever produced.
        """
        if not text.strip():
            raise ValueError("PiperTTS: empty text — nothing to synthesise")

        out_dir = tempfile.mkdtemp(prefix="shunya_piper_")
        out_path = os.path.join(out_dir, "speech.wav")

        model_path = self.model_dir / f"{voice}.onnx"
        config_path = self.model_dir / f"{voice}.json"

        if self._python_available or self._cli_available:
            if not model_path.is_file():
                raise RuntimeError(
                    f"Piper voice model not found: {model_path}. Download the "
                    f"'{voice}' voice files (.onnx + .json) into "
                    f"{self.model_dir} or set PIPER_MODEL_DIR. "
                    f"No audio was fabricated."
                )
            if not config_path.is_file():
                raise RuntimeError(
                    f"Piper voice config not found: {config_path}. The voice "
                    f"'{voice}' needs both .onnx and .json files. "
                    f"No audio was fabricated."
                )

            if self._python_available:
                _synthesize_python(text, str(model_path), str(config_path), out_path)
            else:
                _synthesize_cli(text, str(model_path), str(config_path), out_path)
            return out_path

        # No local engine — attempt HF serverless piper (real call, honest error)
        return self._synthesize_hf(text, voice, out_path)

    # ── HF serverless path ───────────────────────────────────────────

    def _synthesize_hf(self, text: str, voice: str, out_path: str) -> str:
        """Synthesise via the HF serverless Inference API (retry once)."""
        payload = {"inputs": text, "voice": voice}
        try:
            audio_bytes = hf_post(PIPER_HF_MODEL, json_body=payload)
        except RuntimeError as exc:
            try:
                audio_bytes = hf_post(
                    PIPER_HF_MODEL,
                    json_body={"inputs": text, "parameters": {"voice": voice}},
                )
            except RuntimeError:
                raise RuntimeError(
                    "Piper TTS is currently unavailable: "
                    f"{PIPER_HF_MODEL} is not deployed on the HF serverless "
                    f"Inference API ({exc}). Install 'piper-tts' with voice files, "
                    f"or use the Kokoro adapter. No audio was fabricated."
                ) from exc

        with open(out_path, "wb") as fh:
            fh.write(audio_bytes)
        return out_path


# ── helpers ─────────────────────────────────────────────────────────


def _synthesize_python(text: str, model_path: str, config_path: str, out_path: str) -> None:
    """Use the ``piper`` Python API."""
    try:
        import piper
        import soundfile as sf
        import numpy as np
    except ImportError:
        raise RuntimeError("piper Python package not installed.")

    with open(config_path, "r") as fh:
        voice_config = json.load(fh)

    voice = piper.Voice(model_path, config=voice_config, use_cuda=False)
    synthesizer = piper.PiperVoice(voice)
    audio = synthesizer.synthesize(text)
    sf.write(out_path, np.array(audio, dtype=np.float32), voice.config.sample_rate)


def _synthesize_cli(text: str, model_path: str, config_path: str, out_path: str) -> None:
    """Use the ``piper`` CLI tool."""
    cmd = [
        "piper",
        "--model", model_path,
        "--config", config_path,
        "--output-file", out_path,
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            capture_output=True,
            check=True,
            timeout=120,
        )
    except FileNotFoundError:
        raise RuntimeError("piper CLI not found on PATH.")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"piper CLI failed: {exc.stderr.decode()}") from exc


def _which(binary: str) -> str | None:
    """Shim for ``shutil.which``."""
    import shutil
    return shutil.which(binary)


def _python_pkg_available(pkg: str) -> bool:
    """Return True if *pkg* is importable."""
    try:
        __import__(pkg)
        return True
    except ImportError:
        return False