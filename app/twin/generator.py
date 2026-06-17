"""Phase 2 — Digital Twin generation pipeline.

Given freeform intel about a counterparty (notes, email excerpts, a LinkedIn
bio, summaries of past calls), produce a structured PersonaProfile. The engine
then role-plays that profile as the twin.

We use Claude's structured-output path so the result is a validated
PersonaProfile — including a plausible *hidden reservation point*, which is what
makes the rehearsal realistic (the twin has a real bottom line to protect).
"""
from __future__ import annotations

from app.core.llm import LLMClient, llm
from app.twin.persona import PersonaProfile

_SYSTEM = """You are an expert negotiation analyst and profiler. Given raw intel \
about a person you'll be negotiating against, infer a realistic negotiation persona.

Be concrete and psychologically grounded. Where the intel is thin, infer the most \
plausible traits for someone in their role and situation — do not leave fields generic.

Critically: infer a believable HIDDEN reservation point (their true bottom line). \
This is the line the twin will protect during rehearsal and never volunteer. Make it \
realistic, not a pushover."""


def generate_persona(
    intel: str,
    *,
    name_hint: str = "",
    role_hint: str = "",
    scenario: str = "",
    client: LLMClient | None = None,
) -> PersonaProfile:
    """Build a PersonaProfile from raw intel text.

    Parameters
    ----------
    intel : the raw notes / documents about the counterparty.
    name_hint / role_hint : optional steer if you already know these.
    scenario : the negotiation context, which shapes objective/BATNA inference.
    """
    client = client or llm
    user = f"""Negotiation scenario:
{scenario or "(not specified — infer a likely business negotiation)"}

Known name: {name_hint or "(infer from intel)"}
Known role: {role_hint or "(infer from intel)"}

Raw intel about the counterparty:
\"\"\"
{intel.strip()}
\"\"\"

Produce the negotiation persona."""

    return client.parse(_SYSTEM, [{"role": "user", "content": user}], PersonaProfile)


def quick_persona_from_role(role: str, scenario: str = "", client: LLMClient | None = None) -> PersonaProfile:
    """Convenience path when you have only a role description, no intel."""
    return generate_persona(
        intel=f"All that is known is the role: {role}.",
        role_hint=role,
        scenario=scenario,
        client=client,
    )
