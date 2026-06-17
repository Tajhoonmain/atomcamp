# Negotiation Digital Twin — Antigravity Implementation Blueprint

> Execution spec for Antigravity. The frontend (React/Vite in `web/`, brand + animations
> complete) is the source of truth for UX. This document defines the **OpenAI-based backend**,
> integration, deployment, secret automation, and Judge Mode needed to make every UI surface real.
>
> **Model-ID caveat:** model names below (e.g. `gpt-4o`, `gpt-4o-realtime-preview`,
> `text-embedding-3-large`) reflect a Jan-2026 knowledge cutoff. Antigravity MUST confirm the
> current GA model IDs from the OpenAI docs before pinning them in code. Treat the IDs as
> placeholders behind a single `settings.MODELS` map.

---

## 0. Repository ground truth (what already exists)

```
negotiation-digital-twin/
├── app/                    # Python backend (currently Anthropic — to be re-pointed to OpenAI)
│   ├── core/   config.py, llm.py, db.py, models.py
│   ├── twin/   persona.py (PersonaProfile schema), generator.py
│   ├── rag/    store.py (Chroma), ingest.py, agent.py (query rewrite)
│   ├── coach/  coach.py
│   ├── prediction/ engine.py
│   ├── replay/ engine.py
│   ├── negotiation/ engine.py   # turn orchestration (the spine)
│   └── api/    server.py        # FastAPI surface
├── ui/                     # legacy Streamlit dashboard (secondary)
├── web/                    # PRIMARY frontend: Vite+React+TS+Tailwind+Framer Motion
│   └── src/ App.tsx, demo.ts (scripted Judge-Mode data), components/*
└── data/  knowledge corpus + chroma/ + app.db
```

The data contracts already exist in `web/src/demo.ts` (Turn, Insight, persona, probabilitySeries,
leverage, persuasion, graph, replaySteps, outcome) and in `app/twin/persona.py` (`PersonaProfile`).
**These are the canonical schemas — the backend must emit exactly these shapes** so the frontend
binds with zero rework. This is the single most important integration constraint.

---

## PHASE 1 — Codebase analysis methodology + audit checklist

Antigravity runs this top-to-bottom before writing code.

**Step-by-step methodology**
1. **Inventory the frontend.** Parse `web/src`. Enumerate views from `App.tsx` (`landing | loading | demo`) and every component in `web/src/components`.
2. **Map components → data needs.** For each component, list the props/state it reads from `demo.ts`. That list IS the backend's output contract.
3. **Diff live vs scripted.** Anything sourced from `demo.ts` is currently *mocked*. Flag each as "needs live endpoint."
4. **Inventory the backend.** Parse `app/`. For each module, classify: real-and-wired / real-but-Anthropic / stub / missing.
5. **Trace the seam.** `app/api/server.py` is the only HTTP surface. Confirm which `demo.ts` fields have a matching endpoint and which don't.
6. **Catalog external services.** OpenAI Chat, Embeddings, Realtime; vector store; object storage for uploads; DB.

**Audit checklist (mark each: ✅ wired / 🟡 partial / 🔴 missing)**

| # | Item | Where to look | Expected finding |
|---|---|---|---|
| 1 | Frontend routes/views | `web/src/App.tsx` | landing → loading → demo (state-based, no router) |
| 2 | Component inventory | `web/src/components/*` | Hero, Landing, Dashboard, Replay, KnowledgeGraph, widgets, ParticleField, Logo |
| 3 | Data contract source | `web/src/demo.ts` | 🟡 all dashboard data is scripted, not live |
| 4 | LLM provider | `app/core/llm.py` | 🔴 Anthropic — must swap to OpenAI client |
| 5 | Embeddings | `app/rag/store.py` | 🟡 Chroma local model — swap to OpenAI embeddings |
| 6 | Twin generation | `app/twin/generator.py` | 🟡 structured-output call; re-point to OpenAI `response_format` |
| 7 | Coach / Prediction / Replay | `app/{coach,prediction,replay}` | 🟡 implemented, Anthropic-bound, not exposed to `web/` |
| 8 | Voice | `app/voice/*` | 🔴 STT/TTS adapters only; no Realtime; no browser audio |
| 9 | API ↔ frontend wiring | `app/api/server.py` ↔ `web/` | 🔴 frontend never calls the API (uses `demo.ts`) |
| 10 | Secret handling | `.env`, `config.py` | 🔴 must move to Secret Manager; never in image/git/frontend |
| 11 | Realtime token minting | — | 🔴 missing `/realtime/session` ephemeral-token endpoint |
| 12 | Upload ingestion (PDF/email/etc.) | `app/rag/ingest.py` | 🟡 dir ingest only; no upload endpoint or parsers |

Output of Phase 1 = this table filled in + a "live-ification" task list keyed to `demo.ts` fields.

---

## PHASE 2 — Backend architecture (OpenAI-centered)

**Service boundaries** (one FastAPI app, modular services — keep the monolith for hackathon speed; boundaries are logical):

| Service | Responsibility | OpenAI surface |
|---|---|---|
| `llm` | Single OpenAI client; chat, structured output, streaming | Chat Completions / Responses |
| `embeddings` | Embed chunks + queries | `text-embedding-3-large` |
| `rag` | Ingest → chunk → embed → retrieve → assemble | embeddings + vector store |
| `twin` | Build `PersonaProfile` from RAG context | Chat structured output |
| `negotiation` | Turn loop: twin reply (stream), persist | Chat streaming |
| `coach` | Per-turn structured insights | Chat structured output |
| `prediction` | Explainable scoring (Phase 6) | Chat structured output |
| `replay` | Timeline + review + what-if | Chat |
| `voice` | Mint Realtime ephemeral tokens; relay events | Realtime API |
| `secrets/health` | Key detection + startup validation + readiness report | all of the above |

**Folder structure (extends existing `app/`)**
```
app/
  core/        config.py (OpenAI settings + MODELS map), llm.py (OpenAI), db.py, models.py, security.py (secret loader+validator)
  embeddings/  client.py
  rag/         ingest.py, parsers/ (pdf,email,docx,txt,profile), chunk.py, store.py, retriever.py
  twin/        persona.py, generator.py
  negotiation/ engine.py
  coach/ prediction/ replay/   (as today, re-pointed to OpenAI)
  voice/       realtime.py (token minting + event schema)
  api/         server.py (routers), schemas.py (Pydantic = demo.ts shapes), deps.py
  health/      readiness.py (the deployment readiness report)
```

**API contracts** (JSON shapes mirror `web/src/demo.ts`):
- `POST /sessions` → `{session_id, persona: PersonaProfile}`
- `POST /sessions/{id}/turn` (SSE stream) → twin tokens; final `{twin, coach: CoachReport, prediction: OutcomePrediction}`
- `GET /sessions/{id}/timeline` → `Turn[]` enriched with prob + insights
- `GET /sessions/{id}/review` → `ReplayReview`
- `POST /sessions/{id}/whatif` → `{alternative_line, twin_response, deal_probability, predicted_outcome}`
- `POST /twin/generate` (multipart: files + notes) → `PersonaProfile`
- `POST /realtime/session` → `{client_secret, expires_at, model, voice}` (ephemeral; see Phase 5)
- `GET /health/readiness` → readiness report (see Secret Automation)

**Data flow (per turn)**
```
browser → POST /turn (text)
  → rag.retrieve(text)               (embed query → vector search → top-k tactics)
  → negotiation: build twin prompt (persona + retrieved + history) → OpenAI stream → SSE to browser
  → on complete: coach.analyze() + prediction.score()  (parallel, structured)
  → persist Turn + Prediction + Insights → return final payload
```

**Component responsibilities:** `llm` is the ONLY module importing the OpenAI SDK. Everything else depends on `llm`/`embeddings` interfaces, so a provider swap is one file.

---

## PHASE 3 — Agentic RAG implementation

**Pipeline:** `ingest → parse → chunk → embed → store → (query) rewrite → retrieve → rerank → assemble → generate`.

1. **Ingestion** (`POST /twin/generate` multipart, or `/rag/ingest`): accept PDF, DOCX, EML/text email, plain notes, pasted LinkedIn-style profile text.
2. **Parsing** (`rag/parsers/`): PDF → `pypdf`/`pdfplumber`; DOCX → `python-docx`; email → `email` stdlib (strip headers/signatures); profile/notes → passthrough. Normalize to `{source, kind, text}`.
3. **Chunking:** ~800-token chunks, ~120 overlap, split on paragraph/section boundaries; attach metadata `{source, kind, doc_id, position}`.
4. **Embeddings:** batch through `text-embedding-3-large` (3072-d) or `-small` for cost. Store vectors + metadata.
5. **Retrieval:** **agentic** — a cheap chat call rewrites the user's line/the twin task into a tactical query ("buyer cites competing quote" → "counter a competitor BATNA anchor"), embed, top-k (k=6) cosine, then a lightweight LLM rerank to top-3.
6. **Memory:** two tiers — (a) **session memory** = conversation turns in DB; (b) **profile memory** = the persisted `PersonaProfile` + its source chunks. Optionally summarize long sessions to stay within context.
7. **Context assembly:** system prompt = persona + fenced private reservation + retrieved tactics + recent turns (windowed). Deterministic ordering for prompt caching.
8. **Response generation:** streamed chat for the twin; structured (`response_format: json_schema`, strict) for coach/prediction/twin-generation.

**Vector store:** keep **Chroma** for the hackathon (already integrated; zero external dep) but swap its embedder to OpenAI. Production upgrade path: pgvector or a managed store behind the same `retriever` interface.

---

## PHASE 4 — Digital Twin engine

**Inputs:** uploaded docs (PDF/contract/email/notes/profile text) + optional scenario + known name/role.

**Processing stages:**
1. Ingest + RAG over the uploaded corpus (Phase 3).
2. Retrieve the most identity-revealing chunks (role, past behavior, stated goals).
3. Single structured OpenAI call (`response_format` = `PersonaProfile` JSON schema, strict) that infers, with citations back to chunk ids where possible:
   - **Personality profile**, **negotiation style**
   - **Incentives** (what they're rewarded for), **constraints** (budget, approvals, timeline)
   - **Risks**, **likely objections**
   - **BATNA assumptions**, **leverage opportunities** (with strength 0..1)
   - **Hidden reservation point** (fenced private; the twin protects it — this is what makes rehearsal adversarial)
4. Validation pass: schema-validate; if fields are thin, a second targeted call fills gaps.

**Outputs:** a `PersonaProfile` (extends the existing schema with `incentives[]`, `constraints[]`, `risks[]`, `objections[]`, `leverage[]{label,strength}` so it feeds the dashboard's Leverage panel directly).

**Storage:** `personas` row (JSON profile) + `documents` registry + chunk vectors in Chroma. Twin is reusable across sessions; version on regeneration.

---

## PHASE 5 — Voice system (OpenAI Realtime API)

**Two agents, two sessions:**
- **Counterparty voice agent** = the twin, speaking in character (Realtime model + a chosen voice), persona injected as session instructions.
- **Coach voice agent** = whispered, lower-frequency analysis; either a second Realtime session or text coach piped to TTS. Recommend: coach runs as **text** off the transcript (cheaper, no audio collision) and only speaks on demand.

**Session flow:**
1. Browser asks backend `POST /realtime/session`. Backend mints an **ephemeral client token** via OpenAI `/v1/realtime/sessions` using the *server-side* key, returns the short-lived `client_secret`. **The real key never reaches the browser.**
2. Browser opens a **WebRTC** connection directly to OpenAI with the ephemeral token; mic audio streams up, twin audio streams down.
3. Backend optionally subscribes to the event stream (or receives transcript deltas via a data channel relay) for real-time coach/prediction.

**Event flow:** `session.update` (instructions/voice/VAD) → `input_audio_buffer.*` → `response.audio.delta` (playback) → `response.audio_transcript.delta` (live captions) → `conversation.item.created`. **Interruptions:** enable server VAD; on user speech, send `response.cancel` and truncate playback — barge-in works out of the box.

**Audio architecture:** WebRTC browser↔OpenAI for low latency; backend stays on the control plane (token minting + transcript tap). **Latency:** keep the audio path peer-to-peer (don't proxy audio through your backend); use server VAD; pre-warm the session on "Launch Demo"; target <800ms turn latency.

---

## PHASE 6 — Outcome prediction (explainable, not black-box)

Score each turn into **named, defended sub-metrics**, then a transparent aggregate.

| Metric | Definition | Source |
|---|---|---|
| Confidence | model's certainty in its own read | structured field + self-report |
| Persuasion | rapport + anchoring control + information edge | sub-gauges (already in `persuasion`) |
| Momentum | direction of the last N turns | delta of probability series |
| Risk | chance of impasse / value left on table | structured field |
| Success probability | calibrated P(deal) | weighted aggregate |

**Explainability rules:** every score ships with (a) a one-line **rationale**, (b) 3–5 **drivers** `{factor, direction(up/down), weight}` (already modeled in `prediction/engine.py`), and (c) the **turn(s)** that moved it. The UI shows the number *and* the drivers — never a bare percentage. Use `response_format` json_schema so drivers are always present. Calibrate the prompt to be conservative (account for the hidden reservation).

---

## PHASE 7 — Frontend integration map

Replace `demo.ts` reads with API calls behind a `useDemoData` / `useLiveSession` hook so Judge Mode (scripted) and Live mode (API) share one interface.

| UI component | Backend service | Endpoint | Data source |
|---|---|---|---|
| Hero / Landing | — | — | static |
| Launch splash | health | `GET /health/readiness` | startup checks |
| Digital Twin panel | twin | `POST /twin/generate` or session persona | `PersonaProfile` |
| Live Transcript | negotiation | `POST /sessions/{id}/turn` (SSE) | streamed twin tokens |
| Coach panel | coach | (returned with `/turn`) | `CoachReport` |
| Active Agents / Retrieval feed | rag + orchestrator | server events on `/turn` | agent states + retrieved chunks |
| Outcome Prediction (counter+spark) | prediction | (returned with `/turn`) | `OutcomePrediction` series |
| Persuasion gauges | prediction | (returned with `/turn`) | `persuasion[]` |
| Leverage bars | twin | session persona | `leverage[]` |
| Knowledge Graph | twin/rag | `GET /sessions/{id}/graph` | entities + relations |
| Replay timeline | replay | `GET /sessions/{id}/timeline` | `Turn[]`+prob+insights |
| What-if simulator | replay | `POST /sessions/{id}/whatif` | `WhatIfResult` |
| Voice mode | voice | `POST /realtime/session` | ephemeral token → WebRTC |

---

## PHASE 8 — Deployment plan

**Two services on Cloud Run:** `api` (FastAPI, OpenAI) and `web` (static React build, Nginx). `web` calls `api` via a configured base URL.

- **Env vars (api):** `OPENAI_API_KEY` (from Secret Manager — see below), `MODELS_*`, `CHROMA_DIR` (or pgvector URL), `CORS_ORIGINS`.
- **Env vars (web):** `VITE_API_BASE_URL` (baked at build time; non-secret).
- **Secrets management:** GCP **Secret Manager** + Cloud Run `--set-secrets`. Never in image, git, or frontend (see Secret Automation section).
- **Build:** `web`: `npm ci && npm run build` → static; `api`: pip install into `python:3.11-slim`. Cloud Build or `gcloud run deploy --source`.
- **Production config:** `api` min-instances 1 (avoid cold starts during judging), concurrency tuned for streaming, 1 vCPU / 1–2 GiB. Chroma on a mounted volume or swap to managed store for multi-instance.
- **Monitoring:** Cloud Run metrics + uptime check on `/health/readiness`; alert on 5xx and latency.
- **Logging:** structured JSON logs to Cloud Logging; **never log prompts containing secrets or full PII**; log request ids + token usage.

---

## PHASE 9 — Judge Mode (wow in <15s)

- **One-click "Launch Demo"** (already in `web/`). Loads the **scripted dataset** (`demo.ts`) — **no API key, no backend required** for the canned path. This is the reliability guarantee: the demo cannot fail on stage.
- **Behind a toggle, "Live mode"** swaps the same hook to real endpoints (needs the rotated key in Secret Manager).
- Judge Mode preloads: persona (Dana Whitlock), auto-playing streamed transcript, live coach insights, animated 78% outcome, persuasion gauges, knowledge graph, replay + what-if — all already built.
- **Pre-warm** the Realtime session and `api` instance when "Launch Demo" is pressed so Live mode (if used) is instant.
- 15-second beat: splash (2s) → command center populates (3s) → transcript streams + probability climbs (10s).

---

## DELIVERABLES

### 1. Architecture blueprint — see Phases 2–6 above.

### 2. Engineering roadmap (ordered)
1. Re-point `core/llm.py` + `rag/store.py` to OpenAI (client + embeddings). **Smallest change, unblocks everything.**
2. Define `api/schemas.py` to exactly match `demo.ts`.
3. Wire `/sessions` + `/turn` (SSE) + coach + prediction; test against the React app via `VITE_API_BASE_URL`.
4. Twin generation upload pipeline (Phase 3/4).
5. Replay/what-if + knowledge-graph endpoints.
6. Realtime voice (Phase 5).
7. Secret automation + readiness report (below).
8. Deploy (Phase 8).

### 3. Integration roadmap — Phase 7 table; build the `useLiveSession` hook first, migrate components one row at a time, keep Judge Mode on `demo.ts` throughout.

### 4. Deployment roadmap — Phase 8 + Secret Automation. Order: Secret Manager → readiness gate → `api` deploy → `web` deploy → smoke test → pre-warm.

### 5. Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Leaked API key (already occurred) | High | High | Revoke + rotate; Secret Manager only; never in chat/git/image |
| Realtime latency/complexity on stage | Med | High | Keep Judge Mode fully scripted; Live voice is opt-in, pre-warmed |
| Cold starts during judging | Med | Med | min-instances=1; pre-warm on Launch |
| Model-ID drift vs cutoff | Med | Med | `MODELS` map; verify IDs from docs before pinning |
| Chroma multi-instance state | Med | Low | single instance for demo, or pgvector |
| OpenAI rate limits mid-demo | Low | High | scripted fallback; cache; retries w/ backoff |
| PII in uploaded docs | Med | Med | don't log content; ephemeral storage; delete after session |

### 6. Priority matrix

| | High impact | Lower impact |
|---|---|---|
| **Low effort** | OpenAI swap (llm+embeddings); schemas match demo.ts; Secret Manager + readiness gate | logging polish |
| **High effort** | Realtime voice; twin upload pipeline | knowledge-graph live endpoint |

**Do first (high-impact/low-effort):** OpenAI swap, contract alignment, secret automation. **Do last / optional for demo:** live voice (scripted demo already wows).

---

## AUTOMATED SECRET CONFIGURATION (workflow design)

**Principle:** one-time secure entry → automated thereafter. Key lives ONLY in GCP Secret Manager.

**1. Detect** (`app/core/security.py` at startup): read `OPENAI_API_KEY` from env (injected by Cloud Run from Secret Manager). If absent → fail fast with remediation, do not start serving.

**2. Provision (one-time, operator runs locally — never via chat):**
```bash
# rotate first! then:
printf '%s' "$NEW_KEY" | gcloud secrets create openai-api-key --data-file=- \
  || printf '%s' "$NEW_KEY" | gcloud secrets versions add openai-api-key --data-file=-
```
Never in source, `.env` committed, Docker image, or frontend. `.dockerignore` excludes `.env`; `.gitignore` excludes `.env`.

**3. Startup validation** (`health/readiness.py`, runs once on boot, cached):
- key present? → models list ping (connectivity)
- embeddings: embed `"ping"` → expect vector
- chat: 1-token completion → expect 200
- realtime (if `VOICE_ENABLED`): mint an ephemeral session → expect token

**4. Inject at deploy:**
```bash
gcloud run deploy ndt-api --source . --region us-central1 --allow-unauthenticated \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest \
  --min-instances=1
```
Cloud Run mounts the secret as the env var at runtime; the image stays clean.

**5. Readiness report** — `GET /health/readiness` returns and logs:
```
Secret configured:     YES/NO
OpenAI connectivity:   PASS/FAIL
Embeddings:            PASS/FAIL
Chat completions:      PASS/FAIL
Realtime:              PASS/FAIL/SKIPPED
```
A `scripts/preflight.sh` calls this and **exits non-zero** if any check fails.

**6. On failure:** deployment gate (`preflight.sh`) stops, prints the failing check, the likely cause (bad key / no billing / region / model access), and the exact fix (rotate key, enable billing, request model access, set `--set-secrets`). No partial deploys.
