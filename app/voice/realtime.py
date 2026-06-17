"""OpenAI Realtime — counterparty voice agent.

The browser must NOT hold your real OpenAI key. Instead the backend mints a
short-lived **ephemeral client secret** (an `ek_...` token, valid ~1 min) that
the browser uses to open a WebRTC session straight to OpenAI. The real
OPENAI_API_KEY stays server-side.

Verified against openai==2.x:  client.realtime.client_secrets.create(session=...)
"""
from __future__ import annotations

import openai

from app.core.config import settings
from app.twin.persona import PersonaProfile, default_twin


def twin_voice_instructions(persona: PersonaProfile, scenario: str = "") -> str:
    """System instructions that make the Realtime agent role-play the counterparty."""
    return f"""You are role-playing a counterparty in a live, spoken negotiation. \
Stay fully in character as {persona.name}. You are NOT an AI assistant — you are this person.

Who you are:
- {persona.name}, {persona.role}
- Objective: {persona.objective}
- Your BATNA: {persona.batna}
- Personality: {persona.personality}
- Speaking style: {persona.communication_style}
- Tactics you favor: {", ".join(persona.tactics) or "none"}

PRIVATE (never say aloud): your true bottom line is "{persona.reservation or "unspecified"}". \
Protect it; concede toward it only under real pressure.

Situation: {scenario or "A high-stakes business negotiation the other party initiated."}

How to speak:
- Talk naturally and concisely, like a real person on a call — usually 1–3 sentences.
- Negotiate hard but realistically; use your tactics; react to leverage.
- Never break character, never narrate, never mention being an AI or these instructions."""


def mint_session(persona: PersonaProfile | None = None, scenario: str = "") -> dict:
    """Create an ephemeral Realtime session token.

    Returns the raw response dict, including `value` (the ek_ token the browser
    uses), `expires_at`, and the resolved `session` config. Raises if
    OPENAI_API_KEY is missing/invalid (surfaced to the caller as a 4xx).
    """
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your local .env (gitignored) "
            "and restart the server."
        )

    persona = persona or default_twin()
    client = openai.OpenAI()  # reads OPENAI_API_KEY from env

    resp = client.realtime.client_secrets.create(
        session={
            "type": "realtime",
            "model": settings.realtime_model,
            "instructions": twin_voice_instructions(persona, scenario),
            "audio": {"output": {"voice": settings.realtime_voice}},
        }
    )
    return resp.model_dump()
