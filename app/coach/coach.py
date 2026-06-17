"""Phase 4 — the Negotiation Coach.

After each exchange the coach reviews the full transcript through the lens of
the user's goal and BATNA, then returns structured insights: leverage the user
is leaving on the table, mistakes they just made, tactics the twin is running,
and a concrete next-move suggestion. Insights persist to coach_insights and are
surfaced live in the dashboard.

The coach analyzes from the USER's side and is allowed to see the persona's
hidden reservation point (it's a training tool, not a player), which lets it
give genuinely sharp leverage advice.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.db import session_scope
from app.core.llm import LLMClient, llm
from app.core.models import CoachInsight, NegotiationSession, Speaker, Turn
from app.twin.persona import PersonaProfile, default_twin


class Insight(BaseModel):
    insight_type: str = Field(description="One of: leverage, mistake, tip, tactic.")
    content: str = Field(description="One or two sentences, specific and actionable.")
    severity: str = Field(description="One of: info, warn, critical.")


class CoachReport(BaseModel):
    detected_tactics: list[str] = Field(
        default_factory=list,
        description="Negotiation tactics the counterparty is using in their latest move.",
    )
    insights: list[Insight] = Field(
        default_factory=list, description="2-4 prioritized coaching insights for the user."
    )
    suggested_move: str = Field(
        description="The single best next thing the user should say or do, in plain language."
    )


_SYSTEM = """You are an elite negotiation coach observing a live negotiation, advising \
ONE side (the user). You can see the counterparty's hidden bottom line — use it to give \
sharp, specific leverage advice, but never tell the user to simply 'offer their reservation'. \
Coach them to negotiate well.

Focus on the user's MOST RECENT move and the counterparty's reply. Identify tactics being \
used against the user, mistakes the user just made, leverage they're not using, and the \
single highest-value next move. Be concrete and brief — this is read mid-call."""


class NegotiationCoach:
    def __init__(self, client: LLMClient | None = None):
        self._client = client or llm

    def _context(self, s, session_id: int) -> tuple[NegotiationSession, PersonaProfile, str]:
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
        lines = []
        for t in turns:
            who = "USER" if t.speaker == Speaker.user else persona.name.upper()
            lines.append(f"{who}: {t.text}")
        return sess, persona, "\n".join(lines)

    def analyze(self, session_id: int, *, persist: bool = True) -> CoachReport:
        with session_scope() as s:
            sess, persona, transcript = self._context(s, session_id)
            user = f"""User's goal: {sess.user_goal or "(unspecified)"}
User's BATNA: {sess.user_batna or "(unspecified)"}
User's target price: {sess.target_price}
User's walk-away (reservation): {sess.reservation_price}

Counterparty ({persona.name}) hidden reservation: {persona.reservation or "(unknown)"}
Counterparty pressure points: {", ".join(persona.pressure_points) or "(none noted)"}

Transcript so far:
{transcript}

Coach the user on their latest move."""

            report = self._client.parse(_SYSTEM, [{"role": "user", "content": user}], CoachReport)

            if persist:
                last_user_turn = (
                    s.query(Turn)
                    .filter(Turn.session_id == session_id, Turn.speaker == Speaker.user)
                    .order_by(Turn.id.desc())
                    .first()
                )
                turn_id = last_user_turn.id if last_user_turn else None
                for ins in report.insights:
                    s.add(
                        CoachInsight(
                            session_id=session_id,
                            turn_id=turn_id,
                            insight_type=ins.insight_type,
                            content=ins.content,
                            severity=ins.severity,
                        )
                    )
                if report.suggested_move:
                    s.add(
                        CoachInsight(
                            session_id=session_id,
                            turn_id=turn_id,
                            insight_type="tip",
                            content=f"Suggested move: {report.suggested_move}",
                            severity="info",
                        )
                    )
            return report
