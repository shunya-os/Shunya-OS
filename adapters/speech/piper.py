"""
Piper TTS Adapter — STUB / partial implementation.

Piper (rhasspy) is a fast neural text-to-speech system that runs locally
via ``piper-tts`` Python package or the ``piper`` CLI.

Install: ``pip install piper-tts``
Models:  Download ``.onnx`` and ``.json`` files from
         https://huggingface.co/rhasspy/piper-voices/tree/main

This adapter prefers the Python API but falls back to CLI if needed.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from adapters import SpeechSynthesisAdapter


class PiperAdapter(SpeechSynthesisAdapter):
    """Text-to-speech via Piper TTS.

    Requires either:
      - ``pip install piper-tts`` (Python API), or
      - ``piper`` CLI binary on PATH.

    Set ``PIPER_MODEL_DIR`` to a directory containing ``*.onnx`` voice
    files (default: ``~/.piper-tts/models/``).
    """

    def __init__(self) -> None:
        self.model_dir = Path(
            os.environ.get("PIPER_MODEL_DIR", os.path.expanduser("~/.piper-tts/models/"))
        )
        self._cli_available = _which("piper") is not None
        self._python_available = _python_pkg_available("piper")
        self._active = self._cli_available or self._python_available

    # ── SpeechSynthesisAdapter ───────────────────────────────────────

    def synthesize(self, text: str, voice: str = "default", **kwargs: Any) -> str:
        """Synthesise speech to a WAV file.

        Parameters (kwargs):
          - speed (float): playback speed multiplier (default ``1.0``)
          - sentence_silence (float): silence between sentences in seconds
            (default ``0.0``)

        Voice files are expected at:
          ``{model_dir}/{voice}.onnx`` and ``{model_dir}/{voice}.json``

        Returns path to the generated WAV file.
        """
        out_dir = tempfile.mkdtemp(prefix="shunya_piper_")
        out_path = os.path.join(out_dir, "speech.wav")

        if not self._active:
            # Stub
            _write_stub_wav(out_path)
            print(
                f"[PiperAdapter] STUB: synthesize({text!r}, voice={voice!r}) → {out_path}. "
                "Install 'piper-tts' or set PIPER_MODEL_DIR for real synthesis."
            )
            return out_path

        model_path = self.model_dir / f"{voice}.onnx"
        config_path = self.model_dir / f"{voice}.json"

        if not model_path.is_file():
            print(
                f"[PiperAdapter] WARNING: Model file not found: {model_path}. "
                f"Using stub output."
            )
            _write_stub_wav(out_path)
            return out_path

        if self._python_available:
            _synthesize_python(text, str(model_path), str(config_path), out_path)
        else:
            _synthesize_cli(text, str(model_path), str(config_path), out_path)

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


def _write_stub_wav(path: str) -> None:
    """Write a minimal valid 44-byte WAV header (silence)."""
    # 16-bit mono 8000 Hz, 1 sample
    import struct
    sample_rate = 8000
    num_samples = 1
    data_size = num_samples * 2  # 16-bit
    with open(path, "wb") as fh:
        fh.write(b"RIFF")
        fh.write(struct.pack("<I", 36 + data_size))
        fh.write(b"WAVE")
        fh.write(b"fmt ")
        fh.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
        fh.write(b"data")
        fh.write(struct.pack("<I", data_size))
        fh.write(struct.pack("<h", 0))  # one silent sample


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
