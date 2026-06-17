"""Phase 1 smoke test — validates the engine, DB, and persona wiring without
hitting the Claude API. Stubs the LLM stream so it runs offline / keyless.

    python -m scripts.smoke_test
"""
from __future__ import annotations

import app.core.llm as llm_mod
from app.negotiation.engine import NegotiationEngine
from app.twin.persona import PersonaProfile, default_twin


def _fake_stream(self, system, messages, *, max_tokens=2000, thinking=True):
    # Echo a deterministic, in-character-ish reply built from history length.
    n = len([m for m in messages if m["role"] == "user"])
    for piece in [f"[twin reply #{n}] ", "List price it is. ", "What term are you thinking?"]:
        yield piece


def main() -> None:
    # Patch the streaming method so no API call is made.
    llm_mod.LLMClient.stream = _fake_stream  # type: ignore[method-assign]

    engine = NegotiationEngine()
    persona = default_twin()
    assert isinstance(persona, PersonaProfile)

    sid = engine.create_session(
        title="smoke",
        scenario="Renewal call.",
        persona=persona,
        user_goal="25% discount",
    )
    print("created session", sid)

    r1 = engine.respond_stream(sid, "We need a 25% cut to renew.")
    print("turn1 twin:", r1.twin_text)
    r2 = engine.respond_stream(sid, "A competitor quoted us 20% less.")
    print("turn2 twin:", r2.twin_text)

    engine.end_session(sid)
    tx = engine.transcript(sid)
    speakers = [t["speaker"] for t in tx]

    assert speakers == ["user", "twin", "user", "twin"], speakers
    assert r1.twin_text and r2.twin_text
    assert "#1" in r1.twin_text and "#2" in r2.twin_text  # history grew correctly
    print(f"transcript has {len(tx)} turns:", speakers)
    print("\nPHASE 1 SMOKE TEST PASSED [OK]")


if __name__ == "__main__":
    main()
