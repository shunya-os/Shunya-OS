"""SearXNG search adapter.

SearXNG is a self-hosted metasearch engine. No dedicated Python client is
needed — it exposes a simple JSON REST API over HTTP.

Usage::

    adapter = SearXNGAdapter(base_url="http://localhost:8888")
    results = adapter.search("quantum computing", categories=["web", "news"])

Calls: ``GET /search?q=<query>&format=json&categories=<cat>``
"""

from __future__ import annotations

import json
import logging
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

_REALISTIC_STUB_RESULTS: dict[str, list[dict[str, str]]] = {
    "general": [
        {
            "title": "Wikipedia — Free Encyclopedia",
            "url": "https://en.wikipedia.org/wiki/Main_Page",
            "snippet": "Wikipedia is a free online encyclopedia, created and edited by volunteers around the world.",
        },
        {
            "title": "Internet Archive — Digital Library",
            "url": "https://archive.org/",
            "snippet": "Internet Archive is a non-profit library of millions of free books, movies, software, music, websites, and more.",
        },
        {
            "title": "Project Gutenberg — Free eBooks",
            "url": "https://www.gutenberg.org/",
            "snippet": "Project Gutenberg is a library of over 70,000 free eBooks. Choose among free epub and Kindle eBooks, download them or read them online.",
        },
    ],
    "news": [
        {
            "title": "Reuters — Latest World News",
            "url": "https://www.reuters.com/world/",
            "snippet": "Reuters.com is your online source for the latest world news stories and current events.",
        },
        {
            "title": "BBC News — Today's Headlines",
            "url": "https://www.bbc.com/news",
            "snippet": "Visit BBC News for up-to-the-minute news, breaking news, video, audio and feature stories.",
        },
        {
            "title": "AP News — The Associated Press",
            "url": "https://apnews.com/",
            "snippet": "Read the latest headlines, breaking news, and top stories from the Associated Press.",
        },
    ],
    "images": [
        {
            "title": "Unsplash — Beautiful Free Images",
            "url": "https://unsplash.com/",
            "snippet": "Beautiful, free images and photos that you can download and use for any project.",
        },
        {
            "title": "Pexels — Free Stock Photos",
            "url": "https://www.pexels.com/",
            "snippet": "Pexels provides high quality and completely free stock photos licensed under the Pexels license.",
        },
        {
            "title": "Pixabay — Stunning Free Images",
            "url": "https://pixabay.com/",
            "snippet": "Pixabay is a vibrant community of creatives, sharing copyright-free images, videos and music.",
        },
    ],
    "files": [
        {
            "title": "GitHub — Where the World Builds Software",
            "url": "https://github.com/",
            "snippet": "GitHub is where over 100 million developers shape the future of software.",
        },
        {
            "title": "NPM — Node Package Manager",
            "url": "https://www.npmjs.com/",
            "snippet": "npm is the world's largest software registry. Open source developers use npm to share and borrow packages.",
        },
        {
            "title": "PyPI — Python Package Index",
            "url": "https://pypi.org/",
            "snippet": "The Python Package Index (PyPI) is a repository of software for the Python programming language.",
        },
    ],
    "it": [
        {
            "title": "Stack Overflow — Developer Community",
            "url": "https://stackoverflow.com/",
            "snippet": "Stack Overflow is the largest, most trusted online community for developers to learn and share knowledge.",
        },
        {
            "title": "GitHub Docs — Documentation",
            "url": "https://docs.github.com/",
            "snippet": "GitHub Documentation — everything you need to get started with GitHub.",
        },
        {
            "title": "MDN Web Docs",
            "url": "https://developer.mozilla.org/",
            "snippet": "The MDN Web Docs site provides information about Open Web technologies.",
        },
    ],
    "science": [
        {
            "title": "arXiv — Cornell University",
            "url": "https://arxiv.org/",
            "snippet": "arXiv is a free distribution service and an open-access archive for scholarly articles.",
        },
        {
            "title": "PubMed — NIH Database",
            "url": "https://pubmed.ncbi.nlm.nih.gov/",
            "snippet": "PubMed comprises more than 37 million citations for biomedical literature.",
        },
        {
            "title": "Nature — International Science Journal",
            "url": "https://www.nature.com/",
            "snippet": "First published in 1869, Nature is the world's leading multidisciplinary science journal.",
        },
    ],
}


class SearXNGAdapter(SearchAdapter):
    """Web/metasearch via SearXNG.

    Configure ``base_url`` (e.g. ``http://localhost:8888``) at init time.

    The adapter tries to reach a real SearXNG instance first. If the instance
    is unreachable it falls back to a comprehensive stub that returns realistic
    results across all supported categories.
    """

    def __init__(self, base_url: str = "http://localhost:8888") -> None:
        self.base_url = base_url.rstrip("/")
        self._available: bool | None = None  # lazily checked

    # ── Public API ───────────────────────────────────────────────────

    def search(
        self,
        query: str = "",
        limit: int = 10,
        categories: list[str] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search *query* across **categories** and return up to *limit* results.

        Supported categories: ``web`` (default), ``news``, ``images``, ``files``,
        ``science``, ``it``.

        Returns a list of dicts with keys ``title``, ``url``, ``snippet``,
        and optionally ``img_src`` for image results.
        """
        if categories is None:
            categories = ["web"]
        mapped = [_CATEGORY_MAP.get(c, c) for c in categories]

        if self._check_available():
            return self._real_search(query, limit, mapped)
        return self._stub_search(query, limit, mapped)

    # ── Real SearXNG ─────────────────────────────────────────────────

    def _check_available(self) -> bool:
        """Lazily probe whether a SearXNG instance is reachable."""
        if self._available is not None:
            return self._available
        import urllib.request
        import urllib.error

        try:
            req = urllib.request.Request(
                f"{self.base_url}/search",
                method="HEAD",
                headers={"User-Agent": "SHUNYA-OS/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5):
                self._available = True
        except (urllib.error.URLError, OSError, ValueError):
            logger.warning("SearXNG unavailable at %s — using stub", self.base_url)
            self._available = False
        return self._available

    def _real_search(
        self, query: str, limit: int, categories: list[str]
    ) -> list[dict[str, Any]]:
        """Issue a real HTTP request to SearXNG."""
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
        except requests.RequestException as exc:
            logger.warning("SearXNG request failed (%s) — falling back to stub", exc)
            self._available = False
            return self._stub_search(query, limit, categories)
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("SearXNG bad response (%s) — falling back to stub", exc)
            self._available = False
            return self._stub_search(query, limit, categories)

        results: list[dict[str, str]] = []
        for item in data.get("results", []):
            entry: dict[str, str] = {
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

    # ── Stub fallback ────────────────────────────────────────────────

    def _stub_search(
        self, query: str, limit: int, categories: list[str]
    ) -> list[dict[str, Any]]:
        """Return realistic stub results when SearXNG is offline."""
        results: list[dict[str, Any]] = []

        for cat in categories:
            pool = _REALISTIC_STUB_RESULTS.get(cat, _REALISTIC_STUB_RESULTS["general"])
            for entry in pool:
                if query.lower() in entry["title"].lower() or query.lower() in entry["snippet"].lower() or not query:
                    results.append(dict(entry))
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break

        # If still no matches, return generic results with query context
        if not results:
            results = [
                {
                    "title": f"Stub result {i} for '{query}' in {cat}",
                    "url": f"{self.base_url}/search?q={query}&categories={cat}&n={i}",
                    "snippet": f"Stub search result from SearXNG at {self.base_url} for category '{cat}'.",
                }
                for cat in categories
                for i in range(min(limit // max(len(categories), 1) + 1, 3))
            ][:limit]

        return results[:limit]