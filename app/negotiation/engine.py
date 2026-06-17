"""The negotiation engine — Phase 1 core.

Responsibilities:
  * Create / load a negotiation session and its twin persona.
  * Build the twin's system prompt from the persona + scenario.
  * Drive a turn: take the user's utterance, stream the twin's in-character
    reply, and persist both turns.

Extension points (filled in later phases) are marked with `# HOOK:` comments so
the later agents (RAG, coach, predictor) slot in without restructuring.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator

from app.core.db import init_db, session_scope
from app.core.llm import llm
from app.core.models import (
    NegotiationSession,
    Persona,
    Speaker,
    SessionStatus,
    Turn,
)
from app.twin.persona import PersonaProfile, default_twin


@dataclass
class TurnResult:
    user_text: str
    twin_text: str
    session_id: int
    coach: object | None = None        # CoachReport | None
    prediction: object | None = None   # OutcomePrediction | None


def _twin_system_prompt(persona: PersonaProfile, session_row: NegotiationSession,
                        retrieved_context: str = "") -> str:
    """Compose the twin's character + situation into a system prompt.

    The persona's `reservation` is included but explicitly fenced as private —
    the twin must protect it, never volunteer it. This is what makes the twin a
    realistic adversary rather than a pushover.
    """
    rag_block = ""
    if retrieved_context:
        rag_block = (
            "\n\nRelevant negotiation tactics you may draw on:\n"
            f"{retrieved_context}\n"
        )

    return f"""You are role-playing a counterparty in a live negotiation. Stay fully in character. \
You are NOT an AI assistant — you are this person, negotiating for your own interests.

# Who you are
Name: {persona.name}
Role: {persona.role}
Objective: {persona.objective}
Your BATNA (walk-away alternative): {persona.batna}
Personality: {persona.personality}
Communication style: {persona.communication_style}
Tactics you favor: {", ".join(persona.tactics) or "none specified"}
Pressure points you feel: {", ".join(persona.pressure_points) or "none specified"}

# PRIVATE — never reveal directly
Your true reservation point: {persona.reservation or "unspecified"}
Protect this. Concede toward it only under real pressure, and never announce it.

# The situation
{session_row.scenario or "A business negotiation."}

The other side's stated goal (as you understand it): {session_row.user_goal or "unknown"}
{rag_block}
# How to behave
- Speak naturally, the way this person would on a call. 1–4 sentences per turn, conversational.
- Negotiate hard but realistically. Use your tactics. React to leverage the other side applies.
- Don't break character, don't narrate, don't explain your strategy. Just respond as {persona.name}.
"""


class NegotiationEngine:
    def __init__(
        self,
        *,
        enable_rag: bool = False,
        enable_coach: bool = False,
        enable_prediction: bool = False,
    ):
        init_db()
        self.enable_rag = enable_rag
        self.enable_coach = enable_coach
        self.enable_prediction = enable_prediction
        self._rag_obj = None
        self._coach_obj = None
        self._predictor_obj = None

    # Lazy accessors — heavy modules (chromadb) are only imported if used, so
    # the engine loads fine in environments without the optional deps.
    def _rag(self):
        if self._rag_obj is None:
            from app.rag.agent import RAGRetriever

            self._rag_obj = RAGRetriever()
        return self._rag_obj

    def _coach(self):
        if self._coach_obj is None:
            from app.coach.coach import NegotiationCoach

            self._coach_obj = NegotiationCoach()
        return self._coach_obj

    def _predictor(self):
        if self._predictor_obj is None:
            from app.prediction.engine import PredictionEngine

            self._predictor_obj = PredictionEngine()
        return self._predictor_obj

    # ------------------------------------------------------------------ #
    # Session setup                                                       #
    # ------------------------------------------------------------------ #
    def create_session(
        self,
        title: str,
        scenario: str,
        *,
        persona: PersonaProfile | None = None,
        user_goal: str = "",
        user_batna: str = "",
        target_price: float | None = None,
        reservation_price: float | None = None,
    ) -> int:
        persona = persona or default_twin()
        with session_scope() as s:
            p = Persona(name=persona.name, role=persona.role, profile=persona.to_dict())
            s.add(p)
            s.flush()  # assign p.id
            sess = NegotiationSession(
                title=title,
                scenario=scenario,
                user_goal=user_goal,
                user_batna=user_batna,
                target_price=target_price,
                reservation_price=reservation_price,
                persona_id=p.id,
            )
            s.add(sess)
            s.flush()
            return sess.id

    # ------------------------------------------------------------------ #
    # Conversation history                                                #
    # ------------------------------------------------------------------ #
    def _history_as_messages(self, s, session_id: int) -> list[dict]:
        """Turns -> Claude messages. The twin is the 'assistant'; the user is
        the 'user'. Coach/system turns are excluded from the twin's view."""
        turns = (
            s.query(Turn)
            .filter(Turn.session_id == session_id, Turn.speaker.in_([Speaker.user, Speaker.twin]))
            .order_by(Turn.id)
            .all()
        )
        msgs: list[dict] = []
        for t in turns:
            role = "assistant" if t.speaker == Speaker.twin else "user"
            msgs.append({"role": role, "content": t.text})
        return msgs

    def _load_persona(self, s, session_row: NegotiationSession) -> PersonaProfile:
        if session_row.persona and session_row.persona.profile:
            return PersonaProfile.from_dict(session_row.persona.profile)
        return default_twin()

    # ------------------------------------------------------------------ #
    # The turn                                                            #
    # ------------------------------------------------------------------ #
    def respond_stream(
        self,
        session_id: int,
        user_text: str,
        *,
        on_delta: Callable[[str], None] | None = None,
    ) -> TurnResult:
        """Record the user's turn, stream the twin's reply, persist it.

        ``on_delta`` is called with each text chunk as it streams (for live UI /
        TTS). Returns the full result once complete, including coach/prediction
        output if those agents are enabled.
        """
        # Phase 3: agentic RAG runs before the DB scope (it needs no session row)
        # and feeds tactics into the twin's prompt.
        retrieved_context = ""
        if self.enable_rag:
            try:
                retrieved_context = self._rag().retrieve_context(
                    user_text, side="the counterparty / seller"
                )
            except Exception:
                retrieved_context = ""

        with session_scope() as s:
            session_row = s.get(NegotiationSession, session_id)
            if session_row is None:
                raise ValueError(f"No session {session_id}")
            persona = self._load_persona(s, session_row)

            # 1. persist user turn
            s.add(Turn(session_id=session_id, speaker=Speaker.user, text=user_text))
            s.flush()

            system = _twin_system_prompt(persona, session_row, retrieved_context)
            messages = self._history_as_messages(s, session_id)

            # 2. stream twin reply
            chunks: list[str] = []
            for delta in llm.stream(system, messages, max_tokens=600):
                chunks.append(delta)
                if on_delta:
                    on_delta(delta)
            twin_text = "".join(chunks).strip()

            # 3. persist twin turn
            s.add(Turn(session_id=session_id, speaker=Speaker.twin, text=twin_text))

        # 4. Post-turn analysis (Phase 4/5). Runs after the turn commits so the
        #    coach/predictor see the latest turns. They open their own DB scopes.
        coach_report = None
        prediction = None
        if self.enable_coach:
            try:
                coach_report = self._coach().analyze(session_id)
            except Exception:
                coach_report = None
        if self.enable_prediction:
            try:
                prediction = self._predictor().predict(session_id)
            except Exception:
                prediction = None

        return TurnResult(
            user_text=user_text,
            twin_text=twin_text,
            session_id=session_id,
            coach=coach_report,
            prediction=prediction,
        )

    def end_session(self, session_id: int) -> None:
        with session_scope() as s:
            sess = s.get(NegotiationSession, session_id)
            if sess:
                sess.status = SessionStatus.ended

    def transcript(self, session_id: int) -> list[dict]:
        with session_scope() as s:
            turns = (
                s.query(Turn)
                .filter(Turn.session_id == session_id)
                .order_by(Turn.id)
                .all()
            )
            return [
                {"speaker": t.speaker.value, "text": t.text, "at": t.created_at.isoformat()}
                for t in turns
            ]
