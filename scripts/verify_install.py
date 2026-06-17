"""Full-stack verification — imports every module and exercises the parts that
don't need an API key (DB, RAG ingest + retrieval). Run after installing deps:

    python -m scripts.verify_install
"""
from __future__ import annotations


def check(label: str, fn) -> bool:
    try:
        fn()
        print(f"  [OK]   {label}")
        return True
    except Exception as e:
        print(f"  [FAIL] {label}: {type(e).__name__}: {e}")
        return False


def main() -> None:
    print("Imports:")
    ok = True

    def _imports():
        import app.core.config  # noqa
        import app.core.llm  # noqa
        import app.core.db  # noqa
        import app.core.models  # noqa
        import app.twin.persona  # noqa
        import app.twin.generator  # noqa
        import app.voice.stt  # noqa
        import app.voice.tts  # noqa
        import app.negotiation.engine  # noqa
        import app.coach.coach  # noqa
        import app.prediction.engine  # noqa
        import app.replay.engine  # noqa
        import app.rag.store  # noqa
        import app.rag.ingest  # noqa
        import app.rag.agent  # noqa
        import app.api.server  # noqa

    ok &= check("all app modules import", _imports)

    print("\nDatabase:")
    def _db():
        from app.core.db import init_db
        init_db()
    ok &= check("init_db creates schema", _db)

    print("\nRAG (local embeddings, no API key):")
    def _rag():
        from app.rag.ingest import ingest_directory
        from app.rag.store import KnowledgeStore
        ingest_directory()
        store = KnowledgeStore()
        assert store.count() > 0, "no chunks ingested"
        hits = store.query("how do I respond to a competitor's lower quote?", n=2)
        assert hits, "no retrieval hits"
        print(f"         retrieved top tactic: {hits[0]['text'][:70]}...")
    ok &= check("ingest + semantic retrieval", _rag)

    print("\nResult:", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")


if __name__ == "__main__":
    main()
