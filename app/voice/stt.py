"""Speech-to-text adapter.

The whole voice layer is optional. If faster-whisper isn't installed (or
voice is disabled), ``transcribe`` simply isn't available and callers fall
back to typed text. This keeps the core experience runnable with no audio deps.
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import settings


class STTUnavailable(RuntimeError):
    pass


class WhisperSTT:
    """Local Whisper via faster-whisper — no API key, runs offline."""

    def __init__(self, model_name: str | None = None):
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:  # pragma: no cover - optional dep
            raise STTUnavailable(
                "faster-whisper not installed. `pip install -r requirements-voice.txt`"
            ) from e
        self._model = WhisperModel(model_name or settings.whisper_model, compute_type="int8")

    def transcribe(self, audio_path: str | Path) -> str:
        segments, _ = self._model.transcribe(str(audio_path))
        return " ".join(seg.text.strip() for seg in segments).strip()


def get_stt() -> WhisperSTT | None:
    """Return an STT engine, or None if voice/STT is disabled or unavailable."""
    if not settings.voice_enabled or settings.stt_backend != "whisper":
        return None
    try:
        return WhisperSTT()
    except STTUnavailable:
        return None
