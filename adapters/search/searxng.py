"""SearXNG search adapter — real results, never fabricated.

SearXNG is a self-hosted metasearch engine with a simple JSON REST API.

Behavior:
  * When ``SEARXNG_URL`` is configured (env or ``base_url`` arg), a real
    ``GET {SEARXNG_URL}/search?q=<query>&format=json`` request is issued and
    parsed. If the instance is unreachable, an honest error is raised.
  * When no SearXNG instance is configured, the canonical DB-backed
    universal search (``app.search.universal_search.search_canonical_objects``)
    is used — real records, never placeholder results.

Usage::

    adapter = SearXNGAdapter()  # reads SEARXNG_URL from env
    results = adapter.search("quantum computing", categories=["web", "news"])
"""

from __future__ import annotations

import logging
import os
from typing import Any

from adapters import SearchAdapter

logger = logging.getLogger(__name__)

_CATEGORY_MAP = {
    "web": "general",
    "news": "news",
    "images": "images",
    "files": "files",
    "general": "general",
    "science": "science",
    "it": "it",
}


class SearXNGAdapter(SearchAdapter):
    """Web/metasearch via SearXNG, falling back to DB-backed universal search.

    ``SEARXNG_URL`` (e.g. ``http://localhost:8888``) enables the real SearXNG
    JSON API. Without it, search is served by the canonical universal search
    over the SHUNYA object store — real data, no stubs.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url or os.environ.get("SEARXNG_URL") or ""
        ).rstrip("/")

    # ── Public API ───────────────────────────────────────────────────

    def search(
        self,
        query: str = "",
        limit: int = 10,
        categories: list[str] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search *query* and return up to *limit* real results.

        Supported categories (SearXNG): ``web``, ``news``, ``images``,
        ``files``, ``science``, ``it``.

        Returns a list of dicts with keys ``title``, ``url``, ``snippet``,
        and optionally ``img_src`` for image results.
        """
        if categories is None:
            categories = ["web"]
        mapped = [_CATEGORY_MAP.get(c, c) for c in categories]

        if self.base_url:
            return self._searxng_search(query, limit, mapped)
        return self._db_universal_search(query, limit)

    # ── Real SearXNG ─────────────────────────────────────────────────

    def _searxng_search(
        self, query: str, limit: int, categories: list[str]
    ) -> list[dict[str, Any]]:
        """Issue a real HTTP request to the SearXNG JSON API."""
        import requests

        params: dict[str, Any] = {
            "q": query,
            "format": "json",
            "categories": ",".join(categories),
        }
        try:
            resp = requests.get(
                f"{self.base_url}/search",
                params=params,
                timeout=30,
                headers={"User-Agent": "SHUNYA-OS/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(
                f"SearXNG request to {self.base_url}/search failed: {exc}"
            ) from exc

        results: list[dict[str, Any]] = []
        for item in data.get("results", []):
            entry: dict[str, Any] = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            if "img_src" in item:
                entry["img_src"] = item["img_src"]
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    # ── DB-backed fallback (real data, no stub) ─────────────────────

    def _db_universal_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search the canonical SHUNYA object store — real records only."""
        try:
            from app.search.universal_search import search_canonical_objects

            result = search_canonical_objects(query, limit=limit)
        except Exception as exc:
            raise RuntimeError(
                "SEARXNG_URL is not configured and the DB-backed universal "
                f"search is unavailable: {exc}. Set SEARXNG_URL in .env to "
                "enable real web search. No stub results are returned."
            ) from exc

        results: list[dict[str, Any]] = []
        for item in result.get("results", []):
            results.append(
                {
                    "title": item.get("name") or item.get("title") or "",
                    "url": item.get("url")
                    or item.get("api_path")
                    or f"/workspace/{item.get('type', '')}/{item.get('id', '')}",
                    "snippet": item.get("summary") or item.get("description") or "",
                }
            )
            if len(results) >= limit:
                break
        return results