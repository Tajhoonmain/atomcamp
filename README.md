# Negotiation Digital Twin

> Win the conversation before it happens.

Train against an AI mirror of the person across the table — rehearse live, with a
coach reading leverage in real time and an engine predicting the outcome — so the
real negotiation is just a formality.

## Status

| Phase | Capability | State |
|---|---|---|
| 1 | Core voice negotiation experience | ✅ built + tested |
| 2 | Digital Twin generation pipeline | 🔜 |
| 3 | Agentic RAG system | 🔜 |
| 4 | Negotiation Coach | 🔜 |
| 5 | Outcome Prediction Engine | 🔜 |
| 6 | Replay Engine | 🔜 |
| 7 | Dashboard UI | 🔜 |
| 8 | Deployment | 🔜 |

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

copy .env.example .env          # then add your ANTHROPIC_API_KEY
```

Run the Phase 1 negotiation demo (streams the twin's replies in your terminal):

```bash
python -m scripts.demo_cli
```

No API key handy? Verify the plumbing offline:

```bash
python -m scripts.smoke_test
```

## Voice (optional)

The app runs in text mode by default. For spoken replies and local speech-to-text:

```bash
pip install -r requirements-voice.txt
# set NDT_VOICE_ENABLED=true in .env
```

STT uses local Whisper (no key); TTS uses your OS voices. Both degrade silently
to text if unavailable.

## Architecture

A modular Python backend (`app/`) split by capability, a FastAPI surface, and a
Streamlit dashboard. Local-first: SQLite + Chroma, so the only hard requirement
is `ANTHROPIC_API_KEY`. Every Claude-backed agent (twin, coach, predictor,
persona generator, RAG retriever) shares one thin client in `app/core/llm.py`
and runs on `claude-opus-4-8` with adaptive thinking.

```
app/
  core/         config, Claude client, DB engine, ORM schema
  twin/         persona schema + generation pipeline
  rag/          Chroma store, ingest, agentic retriever
  coach/        real-time coaching
  prediction/   outcome engine
  replay/       session replay + what-if
  negotiation/  the turn-orchestration engine (the spine)
  api/          FastAPI app
ui/             Streamlit dashboard
scripts/        demo_cli, smoke_test, seed_knowledge, run_api
data/           knowledge corpus + chroma/ + app.db (gitignored)
```

See `scripts/smoke_test.py` for how the pieces connect.
