"""Search Provider Abstraction — Free-First provider chain.

Chain: DuckDuckGo → Brave Search → SearXNG (self-hosted)
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SearchProvider(ABC):
    """Abstract base for internet search providers."""

    name: str = "base"

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[dict]:
        ...


class DuckDuckGoProvider(SearchProvider):
    """Free, no API key required. Region-limited from some servers."""

    name = "duckduckgo"

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return [
                {"title": r.get("title", ""), "body": r.get("body", ""), "url": r.get("href", "")}
                for r in results if r.get("body")
            ]
        except ImportError:
            logger.warning("duckduckgo_search not installed")
            return []
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return []


class BraveSearchProvider(SearchProvider):
    """Brave Search API — free tier available with API key."""

    name = "brave"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        if not self.api_key:
            return []
        try:
            import requests
            resp = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"Accept": "application/json", "Accept-Encoding": "gzip", "X-Subscription-Token": self.api_key},
                params={"q": query, "count": max_results},
                timeout=10,
            )
            data = resp.json()
            results = []
            for r in (data.get("web", {}).get("results", []) or []):
                desc = r.get("description", "") or r.get("snippet", "")
                results.append({"title": r.get("title", ""), "body": desc, "url": r.get("url", "")})
            return results
        except Exception as e:
            logger.warning(f"Brave search failed: {e}")
            return []


class SearXNGProvider(SearchProvider):
    """SearXNG — self-hosted, open-source metasearch engine."""

    name = "searxng"

    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url.rstrip("/")

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            import requests
            resp = requests.get(
                f"{self.base_url}/search",
                params={"q": query, "format": "json", "language": "en", "categories": "general"},
                timeout=10,
            )
            data = resp.json()
            return [
                {"title": r.get("title", ""), "body": r.get("content", ""), "url": r.get("url", "")}
                for r in data.get("results", [])[:max_results]
            ]
        except Exception as e:
            logger.warning(f"SearXNG search failed: {e}")
            return []


def resolve_search_provider() -> SearchProvider:
    """Resolve best available search provider. Free-first order."""
    import os

    chain = [
        DuckDuckGoProvider(),
        BraveSearchProvider(api_key=os.getenv("BRAVE_SEARCH_API_KEY")),
        SearXNGProvider(base_url=os.getenv("SEARXNG_URL", "http://localhost:8888")),
    ]

    for provider in chain:
        test_results = provider.search("test", max_results=1)
        if test_results:
            logger.info(f"Search provider resolved: {provider.name}")
            return provider

    logger.warning("No search provider available — returning DuckDuckGo fallback")
    return chain[0]