"""
Whisper Speech Recognition Adapter — STUB implementation.

Whisper (OpenAI) is available via:
  - ``openai-whisper`` Python package (local inference)
  - OpenAI API (``whisper-1`` model)
  - ``faster-whisper`` (CTranslate2 backend)

This stub documents the integration points.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

from adapters import SpeechRecognitionAdapter


class WhisperAdapter(SpeechRecognitionAdapter):
    """Speech-to-text via OpenAI Whisper.

    .. caution:: **STUB** — install dependencies to activate.
       Local: ``pip install openai-whisper`` (or ``faster-whisper``)
       API:   Set ``OPENAI_API_KEY`` (uses ``whisper-1`` at 20¢/hour).
    """

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("WHISPER_MODEL", "base")
        self._use_api = bool(self.api_key)

    # ── SpeechRecognitionAdapter ─────────────────────────────────────

    def transcribe(self, audio_path: str, language: str = "en") -> dict[str, Any]:
        """Transcribe an audio file to text.

        Local (``openai-whisper``):
            >>> import whisper
            >>> model = whisper.load_model(self.model)
            >>> result = model.transcribe(audio_path, language=language)
            >>> return {"text": result["text"], "segments": result["segments"],
            ...         "language": result.get("language", language)}

        API (``openai``):
            >>> import openai
            >>> with open(audio_path, "rb") as fh:
            ...     resp = openai.Audio.transcribe("whisper-1", fh,
            ...             language=language)
            >>> return {"text": resp.text, "language": language}

        STUB: Returns a placeholder result.
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if self._use_api:
            raise NotImplementedError(
                "WhisperAdapter.transcribe: OPENAI_API_KEY is set but the HTTP "
                "integration is not yet implemented."
            )

        stub_result = {
            "text": f"[Whisper STUB — transcribed from {audio_path}]",
            "segments": [
                {"start": 0.0, "end": 1.0, "text": f"[Whisper STUB — transcription of {audio_path}]"}
            ],
            "language": language,
            "stub": True,
        }

        print(
            f"[WhisperAdapter] STUB: transcribe({audio_path}, lang={language!r}). "
            f"Install 'openai-whisper' or set OPENAI_API_KEY for real transcription."
        )
        return stub_result
