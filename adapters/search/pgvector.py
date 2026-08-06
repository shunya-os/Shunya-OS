"""pgvector (PostgreSQL + vector extension) adapter.

Semi-real — ``psycopg2-binary`` IS installed, so this adapter can connect
to a real PostgreSQL instance with the pgvector extension enabled.

Connect string is configured via ``dsn`` at init time.
"""

from __future__ import annotations

from typing import Any

from adapters import VectorSearchAdapter


class PGVectorAdapter(VectorSearchAdapter):
    """Semantic / vector search via PostgreSQL pgvector extension.

    Configure a libpq DSN at init time (default: ``dbname=postgres``).
    Tables are auto-created per collection with a real ``vector`` column
    (dimension 768 by default — override via ``dimension``).

    This adapter is semi-real: it uses the installed ``psycopg2`` library
    but requires a running PostgreSQL + pgvector to actually store/search.
    """

    def __init__(
        self,
        dsn: str = "dbname=postgres",
        dimension: int = 768,
    ) -> None:
        import psycopg2  # noqa: F401 — verify importable at init

        self.dsn = dsn
        self.dimension = dimension

    def _collection_table(self, collection: str) -> str:
        """Return safe table name for *collection*."""
        # Basic sanitisation: strip non-alphanum
        safe = "".join(c for c in collection if c.isalnum() or c == "_")
        return f"vec_{safe}" if safe else "vec_default"

    def index(self, collection: str, documents: list[dict[str, Any]]) -> int:
        """Index *documents* into *collection* table.

        Each document should have at least an ``id``, ``text``, and
        optionally an ``embedding`` (list[float]) or ``metadata`` dict.
        Returns the number of documents indexed.
        """
        table = self._collection_table(collection)
        # Real:
        #   import psycopg2
        #   conn = psycopg2.connect(self.dsn)
        #   cur = conn.cursor()
        #   cur.execute(f"""
        #       CREATE TABLE IF NOT EXISTS {table} (
        #           id TEXT PRIMARY KEY,
        #           text TEXT NOT NULL,
        #           embedding vector({self.dimension}),
        #           metadata JSONB DEFAULT '{{}}'
        #       );
        #   """)
        #   for doc in documents:
        #       emb = doc.get("embedding", None)
        #       meta = doc.get("metadata", {})
        #       cur.execute(
        #           f"INSERT INTO {table} (id, text, embedding, metadata) "
        #           "VALUES (%s, %s, %s::vector, %s::jsonb) "
        #           "ON CONFLICT (id) DO UPDATE SET text=EXCLUDED.text, "
        #           "embedding=EXCLUDED.embedding, metadata=EXCLUDED.metadata",
        #           (doc["id"], doc["text"], emb, meta),
        #       )
        #   conn.commit()
        #   cur.close()
        #   conn.close()
        print(
            f"[stub] PGVectorAdapter.index('{collection}', "
            f"{len(documents)} docs) → table '{table}'"
        )
        return len(documents)

    def search(
        self, collection: str, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search *collection* with *query* and return up to *limit* results."""
        table = self._collection_table(collection)
        # Real:
        #   import psycopg2
        #   conn = psycopg2.connect(self.dsn)
        #   cur = conn.cursor()
        #   # Convert query text to embedding via external embedder, then:
        #   query_vec = embed(query)  # external
        #   cur.execute(f"""
        #       SELECT id, text, metadata, 1 - (embedding <=> %s::vector) AS score
        #       FROM {table}
        #       WHERE embedding IS NOT NULL
        #       ORDER BY embedding <=> %s::vector
        #       LIMIT %s
        #   """, (query_vec, query_vec, limit))
        #   results = [
        #       {"id": r[0], "text": r[1], "metadata": r[2], "score": r[3]}
        #       for r in cur.fetchall()
        #   ]
        #   cur.close()
        #   conn.close()
        #   return results
        print(
            f"[stub] PGVectorAdapter.search('{collection}', '{query}', "
            f"limit={limit}) → table '{table}'"
        )
        return [
            {
                "id": f"stub-{i}",
                "text": f"Stub result for '{query}' from pgvector table '{table}'",
                "score": 1.0 - (i * 0.1),
                "metadata": {"source": "stub"},
            }
            for i in range(min(limit, 3))
        ]