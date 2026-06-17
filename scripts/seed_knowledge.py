"""Ingest the negotiation knowledge corpus into Chroma for the RAG system.

    python -m scripts.seed_knowledge
"""
from __future__ import annotations

from app.rag.ingest import ingest_directory


def main() -> None:
    print("Ingesting negotiation knowledge corpus...")
    n = ingest_directory()
    print(f"Done. {n} chunks ingested.")


if __name__ == "__main__":
    main()
