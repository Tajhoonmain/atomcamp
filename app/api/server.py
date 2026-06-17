"""Phase 8 — FastAPI surface.

Exposes the whole system over HTTP so the dashboard, a voice frontend, or an
external integration can drive negotiations. The engine is constructed once
with all agents enabled.

Run:  python -m scripts.run_api      (or: uvicorn app.api.server:app --reload)
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.negotiation.engine import NegotiationEngine
from app.twin.generator import generate_persona
from app.twin.persona import PersonaProfile, default_twin

app = FastAPI(title="Negotiation Digital Twin API", version="0.1.0")

# Full-featured engine: RAG-augmented twin + live coach + prediction per turn.
engine = NegotiationEngine(enable_rag=True, enable_coach=True, enable_prediction=True)


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #
class CreateSessionRequest(BaseModel):
    title: str
    scenario: str
    user_goal: str = ""
    user_batna: str = ""
    target_price: float | None = None
    reservation_price: float | None = None
    persona: PersonaProfile | None = None
    # If persona is omitted but intel is given, generate one.
    persona_intel: str | None = None


class TurnRequest(BaseModel):
    text: str


class WhatIfRequest(BaseModel):
    up_to_turn_index: int
    alternative_line: str


class GeneratePersonaRequest(BaseModel):
    intel: str
    name_hint: str = ""
    role_hint: str = ""
    scenario: str = ""


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/personas/generate")
def gen_persona(req: GeneratePersonaRequest) -> PersonaProfile:
    return generate_persona(
        req.intel, name_hint=req.name_hint, role_hint=req.role_hint, scenario=req.scenario
    )


@app.post("/sessions")
def create_session(req: CreateSessionRequest) -> dict:
    persona = req.persona
    if persona is None and req.persona_intel:
        persona = generate_persona(req.persona_intel, scenario=req.scenario)
    persona = persona or default_twin()
    sid = engine.create_session(
        title=req.title,
        scenario=req.scenario,
        persona=persona,
        user_goal=req.user_goal,
        user_batna=req.user_batna,
        target_price=req.target_price,
        reservation_price=req.reservation_price,
    )
    return {"session_id": sid, "persona": persona.to_dict()}


@app.post("/sessions/{session_id}/turn")
def take_turn(session_id: int, req: TurnRequest) -> dict:
    try:
        result = engine.respond_stream(session_id, req.text)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {
        "twin": result.twin_text,
        "coach": result.coach.model_dump() if result.coach else None,
        "prediction": result.prediction.model_dump() if result.prediction else None,
    }


@app.get("/sessions/{session_id}/transcript")
def transcript(session_id: int) -> list[dict]:
    return engine.transcript(session_id)


@app.get("/sessions/{session_id}/timeline")
def timeline(session_id: int) -> list[dict]:
    from app.replay.engine import ReplayEngine

    return ReplayEngine().timeline(session_id)


@app.get("/sessions/{session_id}/review")
def review(session_id: int) -> dict:
    from app.replay.engine import ReplayEngine

    return ReplayEngine().review(session_id).model_dump()


@app.post("/sessions/{session_id}/whatif")
def what_if(session_id: int, req: WhatIfRequest) -> dict:
    from app.replay.engine import ReplayEngine

    res = ReplayEngine().what_if(session_id, req.up_to_turn_index, req.alternative_line)
    return res.__dict__


@app.post("/sessions/{session_id}/end")
def end_session(session_id: int) -> dict:
    engine.end_session(session_id)
    return {"status": "ended", "session_id": session_id}
