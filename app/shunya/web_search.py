"""Shunya Web Search — with Serper.dev support + graceful fallback."""
import os, json, logging
from typing import List

logger = logging.getLogger("app.shunya.web_search")

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")


def search_web(query: str, limit: int = 5) -> List[dict]:
    """Search the web.
    
    Primary: Serper.dev (Google API, needs SERPER_API_KEY env var)
    Fallback: DuckDuckGo (rate-limited from some servers)
    """
    # Try Serper.dev if configured
    if SERPER_API_KEY:
        return _search_serper(query, limit)
    
    # Fallback to DuckDuckGo
    return _search_duckduckgo(query, limit)


def _search_serper(query: str, limit: int = 5) -> List[dict]:
    """Search using Serper.dev Google API."""
    try:
        import requests
        resp = requests.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": limit},
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("organic", [])[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "google",
                    "type": "web",
                    "confidence": 0.6,
                })
            if results:
                logger.info("Serper returned %d results", len(results))
                return results
    except Exception as e:
        logger.warning("Serper search failed: %s", e)
    return []


def _search_duckduckgo(query: str, limit: int = 5) -> List[dict]:
    """Search using DuckDuckGo (free, may be rate-limited)."""
    try:
        import requests
        # Try the instant answer API
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            abstract = data.get("AbstractText", "")
            if abstract:
                results.append({
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "snippet": abstract[:500],
                    "source": "duckduckgo",
                    "type": "web",
                    "confidence": 0.4,
                })
            for topic in data.get("RelatedTopics", [])[:limit]:
                if "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:150],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")[:300],
                        "source": "duckduckgo",
                        "type": "web",
                        "confidence": 0.4,
                    })
            if results:
                return results[:limit]
    except Exception as e:
        logger.debug("DuckDuckGo failed: %s", e)
    
    return []


def web_search_available() -> bool:
    """Check if web search is configured and working."""
    if SERPER_API_KEY:
        return True
    # DuckDuckGo might work from some servers
    return False


def format_web_unavailable() -> str:
    """Return user-friendly message about web search."""
    return (
        "🌐 **Web search is not yet configured for this server.**\n\n"
        "To enable internet search:\n"
        "1. Get an API key from **serper.dev** (free tier available)\n"
        "2. Set it as `SERPER_API_KEY` in your environment\n"
        "3. The AI will then search the web for any question\n\n"
        "In the meantime, I can still search your **company data** "
        "(knowledge base, entities, past conversations). "
        "Upload documents on the **Ingest** page to teach me!"
    )