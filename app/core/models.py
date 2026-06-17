"""ORM models — the database schema.

The data model is intentionally narrow: a Session (one negotiation) has many
Turns, and each Turn can spawn CoachInsights and Predictions. The Twin's
character lives in a Persona row. JSON columns hold the flexible, model-shaped
payloads (persona profiles, detected tactics, prediction drivers) so we don't
need a migration every time an agent's output evolves.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Speaker(str, enum.Enum):
    user = "user"
    twin = "twin"
    coach = "coach"
    system = "system"


class SessionStatus(str, enum.Enum):
    active = "active"
    ended = "ended"


class Persona(Base):
    """A digital twin of a counterparty."""

    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(200), default="")
    # Full PersonaProfile (goals, BATNA, personality, tactics, tells, style).
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    source_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    sessions: Mapped[list["NegotiationSession"]] = relationship(back_populates="persona")


class NegotiationSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    scenario: Mapped[str] = mapped_column(Text, default="")
    # Your side of the table.
    user_goal: Mapped[str] = mapped_column(Text, default="")
    user_batna: Mapped[str] = mapped_column(Text, default="")
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    reservation_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    persona_id: Mapped[int | None] = mapped_column(ForeignKey("personas.id"), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    persona: Mapped["Persona | None"] = relationship(back_populates="sessions")
    turns: Mapped[list["Turn"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Turn.id"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Prediction.id"
    )


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    speaker: Mapped[Speaker] = mapped_column(Enum(Speaker))
    text: Mapped[str] = mapped_column(Text)
    audio_path: Mapped[str | None] = mapped_column(String(400), nullable=True)
    # sentiment, detected tactics, etc.
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    session: Mapped["NegotiationSession"] = relationship(back_populates="turns")
    insights: Mapped[list["CoachInsight"]] = relationship(
        back_populates="turn", cascade="all, delete-orphan"
    )


class CoachInsight(Base):
    __tablename__ = "coach_insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    turn_id: Mapped[int | None] = mapped_column(ForeignKey("turns.id"), nullable=True)
    insight_type: Mapped[str] = mapped_column(String(60))   # leverage | mistake | tip | tactic
    content: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="info")  # info | warn | critical
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    turn: Mapped["Turn | None"] = relationship(back_populates="insights")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    turn_id: Mapped[int | None] = mapped_column(ForeignKey("turns.id"), nullable=True)
    deal_probability: Mapped[float] = mapped_column(Float)   # 0..1
    predicted_outcome: Mapped[str] = mapped_column(Text, default="")
    drivers: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    session: Mapped["NegotiationSession"] = relationship(back_populates="predictions")


class Document(Base):
    """Registry of ingested RAG documents (chunks live in Chroma)."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    source: Mapped[str] = mapped_column(String(500), default="")
    n_chunks: Mapped[int] = mapped_column(Integer, default=0)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
