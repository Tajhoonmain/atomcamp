"""Text-to-speech adapter.

Offline OS voices via pyttsx3 when available; otherwise a no-op that the
caller treats as "text only". The twin's reply is always returned as text too,
so nothing breaks when TTS is off.
"""
from __future__ import annotations

from app.core.config import settings


class OfflineTTS:
    def __init__(self):
        import pyttsx3  # optional dep

        self._engine = pyttsx3.init()

    def speak(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()


def get_tts():
    """Return a TTS engine with a .speak(str) method, or None if disabled."""
    if not settings.voice_enabled or settings.tts_backend != "offline":
        return None
    try:
        return OfflineTTS()
    except Exception:  # pragma: no cover - optional dep / no audio device
        return None
