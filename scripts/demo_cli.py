"""Phase 1 demo: a live, streaming negotiation against the digital twin.

Run from the repo root:

    python -m scripts.demo_cli

Text mode by default. With the voice extras installed and NDT_VOICE_ENABLED=true,
the twin's replies are spoken aloud (typed input is still used unless you wire a
mic — kept simple here so the core loop is the focus).
"""
from __future__ import annotations

import sys

from app.negotiation.engine import NegotiationEngine
from app.twin.persona import default_twin
from app.voice.tts import get_tts

BANNER = r"""
  Negotiation Digital Twin  ·  Phase 1
  Win the conversation before it happens.
"""


def main() -> None:
    print(BANNER)
    twin = default_twin()
    engine = NegotiationEngine()
    tts = get_tts()

    scenario = (
        "Annual enterprise SaaS renewal call. The customer (you) currently pays "
        "$120k/yr and wants a meaningful discount plus added seats. The vendor "
        "wants to renew at list price."
    )
    session_id = engine.create_session(
        title="SaaS renewal — vs Dana Whitlock",
        scenario=scenario,
        persona=twin,
        user_goal="Cut price by 25% and add 20 seats at no extra cost.",
        user_batna="A competitor quoted 20% less but migration would cost 6 weeks.",
        target_price=90_000,
        reservation_price=105_000,
    )

    print(f"Scenario: {scenario}\n")
    print(f"You're negotiating against {twin.name} — {twin.role}.")
    print("Type your opening line. Commands: /end to finish, /quit to abort.\n")

    while True:
        try:
            user_text = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        if user_text == "/quit":
            print("Aborted.")
            return
        if user_text == "/end":
            break

        print(f"{twin.name}> ", end="", flush=True)
        result = engine.respond_stream(
            session_id,
            user_text,
            on_delta=lambda d: (sys.stdout.write(d), sys.stdout.flush()),
        )
        print("\n")
        if tts:
            tts.speak(result.twin_text)

    engine.end_session(session_id)
    print("\n--- Transcript saved. Session", session_id, "---")
    for turn in engine.transcript(session_id):
        if turn["speaker"] in ("user", "twin"):
            who = "You" if turn["speaker"] == "user" else twin.name
            print(f"  {who}: {turn['text']}")


if __name__ == "__main__":
    main()
