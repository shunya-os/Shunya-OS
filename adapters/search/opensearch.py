"""OpenSearch vector search adapter.

STUB — the ``opensearch-py`` package is not installed. To use:
    pip install opensearch-py

Calls: opensearchpy.OpenSearch client (index, search with k-NN)
"""

from __future__ import annotations

import time
from typing import Any

from adapters import VectorSearchAdapter


class OpenSearchAdapter(VectorSearchAdapter):
    """Semantic / vector search via OpenSearch k-NN plugin.

    Configure host, port, and optional auth at init time.
    This is a stub — the real implementation uses ``opensearchpy.OpenSearch``
    with ``knn`` index mappings and ``knn: true`` in search bodies.
    """

    def __init__(
        self,
        hosts: list[str] | None = None,
        http_auth: tuple[str, str] | None = None,
        use_ssl: bool = True,
    ) -> None:
        self.hosts = hosts or ["https://localhost:9200"]
        self.http_auth = http_auth
        self.use_ssl = use_ssl

    def index(self, collection: str, documents: list[dict[str, Any]]) -> int:
        """Index *documents* into *collection* (an OpenSearch index).

        Returns the number of documents indexed.
        """
        # Real:
        #   from opensearchpy import OpenSearch
        #   client = OpenSearch(self.hosts, http_auth=self.http_auth,
        #                       use_ssl=self.use_ssl)
        #   mappings = {
        #       "settings": {"index": {"knn": True}},
        #       "mappings": {
        #           "properties": {
        #               "embedding": {"type": "knn_vector", "dimension": 768},
        #               "text": {"type": "text"},
        #               "metadata": {"type": "object"},
        #           }
        #       },
        #   }
        #   if not client.indices.exists(collection):
        #       client.indices.create(collection, body=mappings)
        #   for doc in documents:
        #       client.index(index=collection, body=doc, refresh=True)
        #   return len(documents)
        print(
            f"[stub] OpenSearchAdapter.index('{collection}', "
            f"{len(documents)} docs)"
        )
        return len(documents)

    def search(
        self, collection: str, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search *collection* for *query* and return up to *limit* hits."""
        # Real:
        #   from opensearchpy import OpenSearch
        #   client = OpenSearch(self.hosts, http_auth=self.http_auth,
        #                       use_ssl=self.use_ssl)
        #   body = {
        #       "size": limit,
        #       "query": {
        #           "knn": {
        #               "embedding": {
        #                   "vector": embed(query),  # external embedder
        #                   "k": limit,
        #               }
        #           }
        #       },
        #   }
        #   resp = client.search(index=collection, body=body)
        #   return [h["_source"] for h in resp["hits"]["hits"]]
        print(
            f"[stub] OpenSearchAdapter.search('{collection}', '{query}', "
            f"limit={limit})"
        )
        return [
            {
                "id": f"stub-{i}",
                "text": f"Stub result for '{query}' from OpenSearch index '{collection}'",
                "score": 1.0 - (i * 0.1),
                "metadata": {"source": "stub"},
            }
            for i in range(min(limit, 3))
        ]