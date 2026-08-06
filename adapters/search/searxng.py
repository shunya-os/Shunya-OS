"""SearXNG search adapter.

STUB — SearXNG is a self-hosted metasearch engine. No Python client is
installed. The real implementation calls its JSON REST API.

Calls: requests.get(url, params={"q": query, "format": "json"})
"""

from __future__ import annotations

from typing import Any

from adapters import SearchAdapter


class SearXNGAdapter(SearchAdapter):
    """Web/metasearch via SearXNG.

    Configure ``base_url`` (e.g. ``http://localhost:8888``) at init time.
    This is a stub — the real implementation issues HTTP GET against
    ``/search?format=json&q=...`` and parses the JSON response.
    """

    def __init__(self, base_url: str = "http://localhost:8888") -> None:
        self.base_url = base_url.rstrip("/")

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search *query* and return up to *limit* results."""
        # Real:
        #   import requests
        #   resp = requests.get(
        #       f"{self.base_url}/search",
        #       params={"q": query, "format": "json", "limit": limit},
        #       timeout=30,
        #   )
        #   resp.raise_for_status()
        #   return [
        #       {"title": r["title"], "url": r["url"],
        #        "snippet": r.get("content", "")}
        #       for r in resp.json()["results"][:limit]
        #   ]
        print(
            f"[stub] SearXNGAdapter.search('{query}', limit={limit}) "
            f"at {self.base_url}"
        )
        return [
            {
                "title": f"[stub] result {i} for '{query}'",
                "url": f"{self.base_url}/stub?q={query}&n={i}",
                "snippet": f"This is a stub search result from SearXNG at {self.base_url}",
            }
            for i in range(min(limit, 3))
        ]