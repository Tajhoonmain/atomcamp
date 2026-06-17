"""Phase 3 — the agentic retriever.

"Agentic" because retrieval isn't a raw similarity lookup on the user's words.
A fast Claude pass first classifies the negotiation *move* in play and rewrites
it into a tactical query, so we retrieve advice about the situation
(e.g. "buyer is using a competing quote as leverage") rather than matching
surface vocabulary. Falls back to the raw text if the rewrite or store is
unavailable, so the engine never hard-depends on RAG.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.llm import LLMClient

_REWRITE_SYSTEM = """You convert a line from a live negotiation into a short search query \
for a library of negotiation tactics and counter-tactics. Identify the underlying move \
or pressure being applied, and phrase the query from the perspective of the person who \
needs advice. Respond with ONLY the query, no preamble. Keep it under 15 words."""


class RAGRetriever:
    def __init__(self, client: LLMClient | None = None):
        # Query rewriting is a cheap, latency-sensitive step → fast model.
        self._client = client or LLMClient(model=settings.fast_model)
        self._store = None

    def _get_store(self):
        if self._store is None:
            try:
                from app.rag.store import KnowledgeStore

                self._store = KnowledgeStore()
            except Exception:
                self._store = False  # mark as unavailable
        return self._store or None

    def rewrite_query(self, utterance: str, *, side: str = "the user") -> str:
        try:
            q = self._client.complete(
                _REWRITE_SYSTEM,
                [{"role": "user", "content": f"Advice is for {side}. Line: {utterance!r}"}],
                max_tokens=40,
                thinking=False,
            )
            return q.strip() or utterance
        except Exception:
            return utterance

    def retrieve(self, utterance: str, *, side: str = "the user", n: int = 4) -> list[dict]:
        store = self._get_store()
        if store is None:
            return []
        query = self.rewrite_query(utterance, side=side)
        return store.query(query, n=n)

    def retrieve_context(self, utterance: str, *, side: str = "the user", n: int = 3) -> str:
        """Return retrieved tactics formatted for injection into a prompt."""
        hits = self.retrieve(utterance, side=side, n=n)
        if not hits:
            return ""
        lines = []
        for h in hits:
            title = h["meta"].get("title", "tactic")
            lines.append(f"- ({title}) {h['text']}")
        return "\n".join(lines)
