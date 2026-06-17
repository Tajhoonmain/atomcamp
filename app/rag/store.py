"""Phase 3 — vector store over the negotiation knowledge corpus.

Chroma persists to disk and ships its own local embedding model (no API key,
runs offline), which keeps the demo self-contained. The store is a thin facade
so the rest of the system never imports chromadb directly.
"""
from __future__ import annotations

from typing import Iterable

from app.core.config import settings

_COLLECTION = "negotiation_knowledge"


class KnowledgeStore:
    def __init__(self):
        import chromadb  # imported lazily so the app loads without it

        self._client = chromadb.PersistentClient(path=settings.chroma_dir)
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, ids: list[str], texts: list[str], metadatas: list[dict] | None = None) -> None:
        self._col.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas or [{} for _ in ids],
        )

    def query(self, text: str, n: int = 4) -> list[dict]:
        if self.count() == 0:
            return []
        res = self._col.query(query_texts=[text], n_results=min(n, self.count()))
        out: list[dict] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            out.append({"text": doc, "meta": meta or {}, "distance": dist})
        return out

    def count(self) -> int:
        return self._col.count()

    def reset(self) -> None:
        self._client.delete_collection(_COLLECTION)
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION, metadata={"hnsw:space": "cosine"}
        )


def chunk_text(text: str, max_chars: int = 800) -> Iterable[str]:
    """Paragraph-aware chunking. The corpus is short tactic notes, so we keep
    chunks at natural paragraph boundaries and only split if very long."""
    para: list[str] = []
    size = 0
    for line in text.splitlines():
        if not line.strip():
            if para:
                yield "\n".join(para).strip()
                para, size = [], 0
            continue
        para.append(line)
        size += len(line)
        if size >= max_chars:
            yield "\n".join(para).strip()
            para, size = [], 0
    if para:
        yield "\n".join(para).strip()
