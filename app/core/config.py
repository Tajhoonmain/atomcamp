"""Central configuration, loaded from environment / .env.

Everything that varies between machines or deployments lives here so the rest
of the code never reads os.environ directly.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = two levels up from this file (app/core/config.py -> repo root).
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NDT_",
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Claude ---
    # ANTHROPIC_API_KEY is read by the SDK directly (no NDT_ prefix), so we
    # alias it explicitly rather than relying on the env_prefix.
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    model: str = "claude-opus-4-8"          # primary reasoning model
    fast_model: str = "claude-haiku-4-5"     # cheap/fast path (coach quick-checks)
    effort: str = "high"                     # low | medium | high | xhigh | max

    # --- Storage ---
    db_url: str = f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"
    chroma_dir: str = str(DATA_DIR / "chroma")

    # --- Voice (optional) ---
    voice_enabled: bool = False
    tts_backend: str = "offline"   # offline | none
    stt_backend: str = "whisper"   # whisper | none
    whisper_model: str = "base.en"

    @property
    def audio_dir(self) -> Path:
        d = DATA_DIR / "audio"
        d.mkdir(parents=True, exist_ok=True)
        return d


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
