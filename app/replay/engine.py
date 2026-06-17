"""Phase 6 — Replay & What-If Engine.

Three capabilities over a (usually completed) session:

  * timeline()      — turns joined with probability snapshots + coach insights,
                      ready for the dashboard's replay view.
  * review()        — a graded post-mortem: overall grade, biggest mistakes,
                      turning points, and a better line for key user turns.
  * what_if()       — replay from a chosen turn with a different user line and
                      see the twin's likely response + a re-scored prediction,
                      WITHOUT mutating the stored session.
"""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.core.db import session_scope
from app.core.llm import LLMClient, llm
from app.core.models import CoachInsight, NegotiationSession, Prediction, Speaker, Turn
from app.negotiation.engine import _twin_system_prompt
from app.twin.persona import PersonaProfile, default_twin


class Alternative(BaseModel):
    turn_index: int = Field(description="Index (0-based) of the user turn this refers to.")
    original: str = Field(description="What the user actually said.")
    better_line: str = Field(description="A stronger thing they could have said.")
    why: str = Field(description="Why the alternative is stronger.")


class ReplayReview(BaseModel):
    overall_grade: str = Field(description="Letter grade A-F for the user's performance.")
    summary: str = Field(description="2-3 sentence assessment of how the user negotiated.")
    biggest_mistakes: list[str] = Field(default_factory=list)
    turning_points: list[str] = Field(
        default_factory=list, description="Moments that shifted the negotiation."
    )
    alternatives: list[Alternative] = Field(
        default_factory=list, description="Better lines for 2-3 key user turns."
    )


@dataclass
class WhatIfResult:
    alternative_line: str
    twin_response: str
    deal_probability: float
    predicted_outcome: str


_REVIEW_SYSTEM = """You are a master negotiation coach delivering a candid post-mortem of a \
completed negotiation, assessing the USER's performance. Grade fairly, identify the biggest \
mistakes and turning points, and for 2-3 pivotal user turns give a concretely better line. \
Reference what actually happened. Be direct and useful, not flattering."""


class ReplayEngine:
    def __init__(self, client: LLMClient | None = None):
        self._client = client or llm

    # ------------------------------------------------------------------ #
    def timeline(self, session_id: int) -> list[dict]:
        """Turn-by-turn timeline with attached prediction + insights."""
        with session_scope() as s:
            turns = (
                s.query(Turn).filter(Turn.session_id == session_id).order_by(Turn.id).all()
            )
            preds = {
                p.turn_id: p
                for p in s.query(Prediction).filter(Prediction.session_id == session_id).all()
            }
            insights: dict[int, list] = {}
            for ins in (
                s.query(CoachInsight).filter(CoachInsight.session_id == session_id).all()
            ):
                insights.setdefault(ins.turn_id, []).append(
                    {"type": ins.insight_type, "content": ins.content, "severity": ins.severity}
                )
            out = []
            for t in turns:
                p = preds.get(t.id)
                out.append(
                    {
                        "turn_id": t.id,
                        "speaker": t.speaker.value,
                        "text": t.text,
                        "deal_probability": p.deal_probability if p else None,
                        "predicted_outcome": p.predicted_outcome if p else None,
                        "insights": insights.get(t.id, []),
                    }
                )
            return out

    # ------------------------------------------------------------------ #
    def review(self, session_id: int) -> ReplayReview:
        with session_scope() as s:
            sess, persona, transcript = self._load(s, session_id)
            user = f"""User goal: {sess.user_goal}
User target: {sess.target_price}   walk-away: {sess.reservation_price}
Counterparty: {persona.name} — {persona.role}

Full transcript:
{transcript}

Deliver the post-mortem."""
            return self._client.parse(_REVIEW_SYSTEM, [{"role": "user", "content": user}], ReplayReview)

    # ------------------------------------------------------------------ #
    def what_if(self, session_id: int, up_to_turn_index: int, alternative_line: str) -> WhatIfResult:
        """Replay: at the user turn with index ``up_to_turn_index``, substitute
        ``alternative_line`` and see how the twin would respond. Read-only."""
        from app.prediction.engine import OutcomePrediction  # local import (lazy)

        with session_scope() as s:
            sess, persona, _ = self._load(s, session_id)

            convo_turns = (
                s.query(Turn)
                .filter(
                    Turn.session_id == session_id,
                    Turn.speaker.in_([Speaker.user, Speaker.twin]),
                )
                .order_by(Turn.id)
                .all()
            )
            # Rebuild history up to (but not including) the chosen user turn,
            # then append the alternative line as the user's move.
            messages: list[dict] = []
            user_seen = -1
            for t in convo_turns:
                if t.speaker == Speaker.user:
                    user_seen += 1
                    if user_seen == up_to_turn_index:
                        break
                role = "assistant" if t.speaker == Speaker.twin else "user"
                messages.append({"role": role, "content": t.text})
            messages.append({"role": "user", "content": alternative_line})

            system = _twin_system_prompt(persona, sess)
            twin_response = self._client.complete(system, messages, max_tokens=600)

        # Score the hypothetical exchange with a fresh prediction (no persistence).
        pred = self._client.parse(
            _WHATIF_PRED_SYSTEM,
            [
                {
                    "role": "user",
                    "content": (
                        f"User goal: {sess.user_goal}\n"
                        f"User said: {alternative_line!r}\n"
                        f"Counterparty ({persona.name}) replied: {twin_response!r}\n"
                        f"Counterparty hidden reservation: {persona.reservation}\n"
                        "Estimate the resulting outcome."
                    ),
                }
            ],
            OutcomePrediction,
        )
        return WhatIfResult(
            alternative_line=alternative_line,
            twin_response=twin_response,
            deal_probability=pred.deal_probability,
            predicted_outcome=pred.predicted_outcome,
        )

    # ------------------------------------------------------------------ #
    def _load(self, s, session_id: int) -> tuple[NegotiationSession, PersonaProfile, str]:
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
            .filter(Turn.session_id == session_id, Turn.speaker.in_([Speaker.user, Speaker.twin]))
            .order_by(Turn.id)
            .all()
        )
        transcript = "\n".join(
            f"{'USER' if t.speaker == Speaker.user else persona.name.upper()}: {t.text}"
            for t in turns
        )
        return sess, persona, transcript


_WHATIF_PRED_SYSTEM = """You are a negotiation analyst. Given a single hypothetical exchange, \
estimate the deal probability and likely outcome from the user's perspective. Be calibrated."""
