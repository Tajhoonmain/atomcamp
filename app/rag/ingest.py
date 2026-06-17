"""Phase 3 — corpus ingestion.

Reads .md/.txt files from a directory, chunks them, embeds into Chroma, and
registers each file in the documents table.
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import ROOT
from app.core.db import init_db, session_scope
from app.core.models import Document
from app.rag.store import KnowledgeStore, chunk_text

DEFAULT_CORPUS = ROOT / "data" / "knowledge"


def ingest_directory(path: str | Path | None = None) -> int:
    """Ingest every .md/.txt under ``path``. Returns total chunks added."""
    init_db()
    corpus = Path(path or DEFAULT_CORPUS)
    if not corpus.exists():
        raise FileNotFoundError(f"Knowledge corpus not found: {corpus}")

    store = KnowledgeStore()
    total = 0
    files = sorted([*corpus.glob("**/*.md"), *corpus.glob("**/*.txt")])
    for fp in files:
        text = fp.read_text(encoding="utf-8")
        chunks = [c for c in chunk_text(text) if c]
        ids = [f"{fp.stem}-{i}" for i in range(len(chunks))]
        metas = [{"source": fp.name, "title": fp.stem} for _ in chunks]
        if chunks:
            store.add(ids, chunks, metas)
            total += len(chunks)
        with session_scope() as s:
            s.add(Document(title=fp.stem, source=fp.name, n_chunks=len(chunks)))
        print(f"  ingested {fp.name}: {len(chunks)} chunks")

    print(f"Total chunks in store: {store.count()}")
    return total


if __name__ == "__main__":
    ingest_directory()
