# Deployment

The app is a single container that serves the Streamlit dashboard. The only
required secret is `ANTHROPIC_API_KEY`.

## Local container

```bash
docker build -t negotiation-digital-twin .
docker run -p 8080:8080 -e ANTHROPIC_API_KEY=sk-ant-... negotiation-digital-twin
# open http://localhost:8080
```

## Google Cloud Run

```bash
PROJECT=your-gcp-project
gcloud builds submit --tag gcr.io/$PROJECT/ndt
gcloud run deploy ndt \
  --image gcr.io/$PROJECT/ndt \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --set-env-vars ANTHROPIC_API_KEY=sk-ant-...
```

Cloud Run injects `$PORT`; the Dockerfile binds Streamlit to it on `0.0.0.0`.
Use Secret Manager for the API key in production instead of `--set-env-vars`.

## Running the API instead of the dashboard

Override the container command:

```bash
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... \
  negotiation-digital-twin \
  python -m scripts.run_api
```

## Notes

* SQLite (`data/app.db`) and Chroma (`data/chroma/`) are ephemeral on Cloud
  Run's container filesystem — fine for a demo / single session. For
  persistence across instances, mount a volume or swap the DB URL for a managed
  Postgres and Chroma for a hosted vector store.
* The RAG corpus is seeded into the image at build time (`scripts.seed_knowledge`).
