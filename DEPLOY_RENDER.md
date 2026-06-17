# Deploying to Render — full stack (React frontend + FastAPI backend)

> **Why your site currently shows Streamlit:** the previous version of this guide
> deployed the Docker image, whose `CMD` runs `streamlit run ui/streamlit_app.py`.
> Render therefore served the Streamlit UI, not the React app in `web/`. This guide
> deploys the **React frontend** as a static site and the **FastAPI backend** as a
> separate service, using the `render.yaml` Blueprint in the repo root.

## What deploys

| Service | Render type | Serves | URL (example) |
|---|---|---|---|
| `ndt-web` | Static Site | the React app (`web/dist`) — the updated UI | `https://ndt-web.onrender.com` |
| `ndt-api` | Web Service (Python) | the FastAPI backend | `https://ndt-api.onrender.com` |

Judge Mode (the scripted demo) works on `ndt-web` **with no backend and no key** — so you always have a live, impressive URL. Live mode (real coach/twin/prediction) uses `ndt-api`.

---

## 0. Rotate the leaked key first
The OpenAI key pasted earlier is compromised. Revoke it at
<https://platform.openai.com/api-keys> and create a new one. The new key goes
**only** into Render's dashboard (Step 3), never into the repo.

> **Provider note:** the backend currently runs on **Anthropic Claude**, so it reads
> `ANTHROPIC_API_KEY`. To run it on your **OpenAI** key, first do the provider swap in
> `app/core/llm.py` (see `docs/ANTIGRAVITY_BLUEPRINT.md` → Phase 2), then use
> `OPENAI_API_KEY` as the secret name below.

---

## 1. Get the updated code onto GitHub

These changes live in your local project. Commit and push them to
`github.com/Tajhoonmain/atomcamp` from your authenticated machine
(this environment has no GitHub credentials, so it cannot push for you):

```bash
cd C:\Projects\negotiation-digital-twin     # or wherever your clone is
git add render.yaml DEPLOY_RENDER.md web/src/api.ts web/.env.example .gitignore app/api/server.py
git commit -m "Render full-stack: static React site + FastAPI API, CORS, env-toggled features"
git push origin main
```

Confirm `web/node_modules`, `web/dist`, and any `.env` are **not** staged
(`git status` should not list them — `.gitignore` now excludes them).

---

## 2. Apply the Blueprint on Render

1. Render dashboard → **New +** → **Blueprint**.
2. Connect `Tajhoonmain/atomcamp`. Render reads `render.yaml` and proposes
   **two** services (`ndt-web`, `ndt-api`). Approve.

---

## 3. Set secrets / env (one time, in the dashboard)

**ndt-api** (Environment tab):
- `ANTHROPIC_API_KEY` = your rotated key  *(or `OPENAI_API_KEY` after the swap)*
- `CORS_ORIGINS` = your frontend URL, e.g. `https://ndt-web.onrender.com`

**ndt-web** (Environment tab):
- `VITE_API_BASE_URL` = your backend URL, e.g. `https://ndt-api.onrender.com`
  *(static-site env vars are baked at build time — after setting it, trigger a
  redeploy of `ndt-web` so the build picks it up.)*

Nothing secret is in the repo or the image — Render injects these at runtime.

---

## 4. Verify

- `https://ndt-api.onrender.com/health` → `{"status":"ok"}` (boots without a key).
- `https://ndt-web.onrender.com` → the animated landing page → **Launch Demo** →
  the command-center dashboard (Judge Mode, scripted — always works).
- Live mode: with `VITE_API_BASE_URL` set and a valid key on `ndt-api`, the live
  endpoints (`/sessions`, `/turn`, …) drive real twin/coach/prediction.

---

## Notes & gotchas
- **Free Python instances cold-start** (~30–60s first hit). For judging, bump
  `ndt-api` off free or hit `/health` to warm it; Judge Mode doesn't need the API.
- `ENABLE_RAG=0` by default (RAG pulls a ~79 MB embedder + needs the seeded corpus).
  Leave it off unless you've seeded `data/chroma` into the image/instance.
- The old Docker/Streamlit path still works if you ever want the Streamlit UI —
  it's just not what `render.yaml` deploys.
