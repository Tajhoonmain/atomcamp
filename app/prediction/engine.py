"""Phase 5 — Outcome Prediction Engine.

After each turn, estimate where the deal stands: probability of reaching
agreement, the most likely final outcome in plain terms, and the factors
pushing the probability up or down. Each estimate is stored as a Prediction
row so the dashboard can plot a probability curve across the negotiation and
the replay engine can flag the turns that moved it most.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.db import session_scope
from app.core.llm import LLMClient, llm
from app.core.models import NegotiationSession, Prediction, Speaker, Turn
from app.twin.persona import PersonaProfile, default_twin


class Driver(BaseModel):
    factor: str = Field(description="A specific factor affecting the outcome.")
    direction: str = Field(description="'up' if it favors a deal for the user, 'down' if not.")
    weight: float = Field(description="Relative importance, 0..1.")


class OutcomePrediction(BaseModel):
    deal_probability: float = Field(
        description="Probability (0..1) that the two sides reach an agreement."
    )
    user_favorability: float = Field(
        description="If a deal happens, how favorable to the user (0=worst case, 1=user's target)."
    )
    predicted_outcome: str = Field(
        description="One or two sentences describing the most likely final agreement or impasse."
    )
    drivers: list[Driver] = Field(default_factory=list, description="3-5 factors driving this.")


_SYSTEM = """You are a negotiation analyst estimating the likely outcome of a live \
negotiation from the USER's perspective. Read the transcript and the known positions, then \
produce a calibrated probability the sides reach a deal, how favorable that deal is likely \
to be for the user, and the key drivers. Be calibrated, not optimistic — account for the \
counterparty's hidden bottom line and leverage."""


class PredictionEngine:
    def __init__(self, client: LLMClient | None = None):
        self._client = client or llm

    def predict(self, session_id: int, *, persist: bool = True) -> OutcomePrediction:
        with session_scope() as s:
            sess = s.get(NegotiationSession, session_id)
            if sess is None:
                raise ValueError(f"No session {session_id}")
            persona = (
                PersonaProfile.from_dict(sess.persona.profile)
                if sess.persona and sess.persona.profile
                else default_twin()
            )
            turns = (
                s.query(Turn)
                .filter(
                    Turn.session_id == session_id,
                    Turn.speaker.in_([Speaker.user, Speaker.twin]),
                )
                .order_by(Turn.id)
                .all()
            )
            transcript = "\n".join(
                f"{'USER' if t.speaker == Speaker.user else persona.name.upper()}: {t.text}"
                for t in turns
            )
            user = f"""User goal: {sess.user_goal or "(unspecified)"}
User target price: {sess.target_price}   walk-away: {sess.reservation_price}
User BATNA: {sess.user_batna or "(unspecified)"}
Counterparty ({persona.name}) BATNA: {persona.batna}
Counterparty hidden reservation: {persona.reservation or "(unknown)"}

Transcript:
{transcript or "(no turns yet)"}

Estimate the outcome."""

            pred = self._client.parse(_SYSTEM, [{"role": "user", "content": user}], OutcomePrediction)

            if persist:
                last_turn = turns[-1] if turns else None
                s.add(
                    Prediction(
                        session_id=session_id,
                        turn_id=last_turn.id if last_turn else None,
                        deal_probability=pred.deal_probability,
                        predicted_outcome=pred.predicted_outcome,
                        drivers={
                            "user_favorability": pred.user_favorability,
                            "drivers": [d.model_dump() for d in pred.drivers],
                        },
                    )
                )
            return pred
