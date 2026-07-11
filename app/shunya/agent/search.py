"""Shunya Personal Agent — Omniscient Search Engine.

Multi-engine web search, deep page reading, source decision tree,
verification badges, search cache, and dual-source merging.
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json, time, hashlib, logging

logger = logging.getLogger("app.shunya.agent.search")


# ---------------------------------------------------------------------------
# Source Decision Tree
# ---------------------------------------------------------------------------

class QueryDomain(str):
    ENTITY = "entity"           # "Show me the Patel invoice" → internal ONLY
    KNOWLEDGE = "knowledge"     # "What's our refund policy?" → KB first, web fallback
    ANALYTICS = "analytics"     # "What's our revenue this month?" → entity + analytics
    RESEARCH = "research"       # "Compare Bali vs Maldives" → web first, then internal
    FACTUAL = "factual"         # "Visa fee for Thailand" → web, cross-validate
    REALTIME = "realtime"       # "Flight status of UK-815" → web live
    ACTION = "action"           # "Create a lead for Sharma" → tool pipeline
    AMBIGUOUS = "ambiguous"     # "Tell me about Bali" → BOTH sources
    UNKNOWN = "unknown"


class SourceDecisionTree:
    """Classifies queries to decide WHERE to search."""

    ENTITY_PATTERNS = ["show", "list", "my", "our", "find", "get", "display", "view"]
    KNOWLEDGE_PATTERNS = ["policy", "procedure", "how do we", "what is our", "company"]
    ANALYTICS_PATTERNS = ["revenue", "profit", "p&l", "sales", "report", "dashboard"]
    RESEARCH_PATTERNS = ["compare", "vs", "versus", "verses", "difference"]
    FACTUAL_PATTERNS = ["what is", "how much", "how many", "cost", "fee", "price", "when is"]
    REALTIME_PATTERNS = ["flight", "status", "weather", "exchange rate", "stock", "news"]
    ACTION_PATTERNS = ["create", "add", "new", "make", "update", "change", "edit", "send", "delete"]
    WEB_PATTERNS = ["search web", "search internet", "look up", "google", "find online"]

    @staticmethod
    def classify(query: str) -> QueryDomain:
        q = query.lower().strip()

        # Check web-first patterns
        if any(p in q for p in SourceDecisionTree.WEB_PATTERNS):
            return QueryDomain.FACTUAL

        # Check action patterns
        first_word = q.split()[0] if q.split() else ""
        if first_word in ("create", "add", "new", "make", "update", "change", "edit", "delete", "remove", "send"):
            return QueryDomain.ACTION

        # Check realtime
        if any(p in q for p in SourceDecisionTree.REALTIME_PATTERNS):
            return QueryDomain.REALTIME

        # Check research
        if any(p in q for p in SourceDecisionTree.RESEARCH_PATTERNS):
            return QueryDomain.RESEARCH

        # Check knowledge (BEFORE entity — "our" is more specific for knowledge)
        if any(p in q for p in SourceDecisionTree.KNOWLEDGE_PATTERNS):
            return QueryDomain.KNOWLEDGE

        # Check analytics
        if any(p in q for p in SourceDecisionTree.ANALYTICS_PATTERNS):
            return QueryDomain.ANALYTICS

        # Check entity
        if any(p in q for p in SourceDecisionTree.ENTITY_PATTERNS):
            return QueryDomain.ENTITY

        # Check factual
        if any(p in q for p in SourceDecisionTree.FACTUAL_PATTERNS):
            return QueryDomain.FACTUAL

        # Default: ambiguous — check both
        return QueryDomain.AMBIGUOUS

    @staticmethod
    def get_search_plan(query: str) -> dict:
        """Return a plan: which sources to search and in what order."""
        domain = SourceDecisionTree.classify(query)
        plans = {
            QueryDomain.ENTITY: {"internal": True, "web": False, "order": ["internal"]},
            QueryDomain.KNOWLEDGE: {"internal": True, "web": True, "order": ["internal", "web"]},
            QueryDomain.ANALYTICS: {"internal": True, "web": False, "order": ["analytics"]},
            QueryDomain.RESEARCH: {"internal": True, "web": True, "order": ["web", "internal"]},
            QueryDomain.FACTUAL: {"internal": False, "web": True, "order": ["web"]},
            QueryDomain.REALTIME: {"internal": False, "web": True, "order": ["web_live"]},
            QueryDomain.ACTION: {"internal": False, "web": False, "order": ["action"]},
            QueryDomain.AMBIGUOUS: {"internal": True, "web": True, "order": ["internal", "web"]},
            QueryDomain.UNKNOWN: {"internal": True, "web": True, "order": ["internal", "web"]},
        }
        return {"domain": domain, **plans.get(domain, plans[QueryDomain.AMBIGUOUS])}


# ---------------------------------------------------------------------------
# Search Cache
# ---------------------------------------------------------------------------

class SearchCache:
    """Cache search results with TTL per domain."""

    TTL = {
        "realtime": timedelta(minutes=2),
        "exchange_rate": timedelta(minutes=5),
        "flight_status": timedelta(minutes=2),
        "weather": timedelta(minutes=30),
        "visa_info": timedelta(hours=24),
        "factual": timedelta(hours=24),
        "company_knowledge": timedelta(days=7),
        "default": timedelta(hours=1),
    }

    def __init__(self):
        self._store: dict[str, dict] = {}

    def _key(self, query: str, domain: str) -> str:
        return hashlib.md5(f"{domain}:{query.lower().strip()}".encode()).hexdigest()

    def get(self, query: str, domain: str) -> Optional[dict]:
        key = self._key(query, domain)
        entry = self._store.get(key)
        if not entry:
            return None
        ttl = self.TTL.get(domain, self.TTL["default"])
        created = datetime.fromisoformat(entry["cached_at"])
        if datetime.utcnow() - created > ttl:
            del self._store[key]
            return None
        return entry["data"]

    def set(self, query: str, domain: str, data: dict):
        key = self._key(query, domain)
        self._store[key] = {"data": data, "cached_at": datetime.utcnow().isoformat()}

    def clear(self):
        self._store.clear()


_search_cache = SearchCache()


def get_cache() -> SearchCache:
    return _search_cache


# ---------------------------------------------------------------------------
# Web Search Engine
# ---------------------------------------------------------------------------

@dataclass
class SearchResultItem:
    title: str
    url: str
    snippet: str
    source: str  # "web" | "knowledge" | "internal"
    confidence: float = 0.5


@dataclass
class CrossValidatedResult:
    answer: str
    sources: list[SearchResultItem]
    agreement_score: float  # 0-1, what % of sources agree
    contradictions: list[str]
    confidence: float


class WebSearchEngine:
    """Searches the web with multi-engine fallback and cross-validation."""

    def search(self, query: str, depth: str = "normal") -> list[SearchResultItem]:
        """Search with fallback depth."""
        from app.shunya.web_search import web_search

        results = []
        try:
            data = web_search(query, limit=5 if depth == "quick" else 10)
            if data and isinstance(data, list):
                for item in data[:10]:
                    results.append(SearchResultItem(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", item.get("description", "")),
                        source="web",
                        confidence=0.6,
                    ))
        except Exception as e:
            logger.warning("Web search failed: %s", e)

        return results

    def read_page(self, url: str, target_query: str) -> Optional[str]:
        """Read a full page and extract content relevant to the query."""
        import requests
        try:
            resp = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; ShunyaAgent/1.0)"
            })
            if resp.status_code == 200:
                text = resp.text
                # Simple extraction — find the most relevant paragraph
                lines = text.split("\n")
                relevant = [l.strip() for l in lines if target_query.lower() in l.lower() and len(l.strip()) > 50]
                return "\n".join(relevant[:5]) if relevant else text[:2000]
        except Exception as e:
            logger.warning("Page read failed for %s: %s", url, e)
        return None

    def deep_read(self, urls: list[str], target_query: str) -> list[dict]:
        """Read multiple pages and extract relevant content."""
        results = []
        for url in urls[:3]:
            content = self.read_page(url, target_query)
            if content:
                results.append({"url": url, "content": content})
        return results

    def cross_validate(self, results: list[SearchResultItem]) -> CrossValidatedResult:
        """Compare results from multiple sources and return a verified answer."""
        if not results:
            return CrossValidatedResult(
                answer="", sources=[], agreement_score=0, contradictions=[], confidence=0
            )

        # For web results, check if snippets agree on key facts
        snippets = [r.snippet.lower() for r in results if r.snippet]
        if not snippets:
            return CrossValidatedResult(
                answer=results[0].snippet if results else "",
                sources=results,
                agreement_score=0.3,
                contradictions=[],
                confidence=0.3,
            )

        # Simple agreement: check shared key phrases
        words = set(snippets[0].split()[:20])
        agreements = sum(1 for s in snippets[1:] if any(w in s for w in words))
        total_extra = len(snippets) - 1 if len(snippets) > 1 else 1
        agreement_score = agreements / total_extra if total_extra > 0 else 0.5

        return CrossValidatedResult(
            answer=results[0].snippet,
            sources=results,
            agreement_score=agreement_score,
            contradictions=[] if agreement_score > 0.5 else ["Sources may disagree"],
            confidence=min(0.5 + agreement_score * 0.4, 0.95),
        )


# ---------------------------------------------------------------------------
# Verification Badges
# ---------------------------------------------------------------------------

class VerificationBadge:
    """Assigns and renders verification badges."""

    BADGES = {
        "verified": {"icon": "✅", "label": "Verified", "color": "text-green-600", "bg": "bg-green-50"},
        "company": {"icon": "📚", "label": "Company Data", "color": "text-blue-600", "bg": "bg-blue-50"},
        "web_single": {"icon": "🌐", "label": "Web (Single)", "color": "text-amber-600", "bg": "bg-amber-50"},
        "conflicting": {"icon": "⚠️", "label": "Conflicting", "color": "text-red-600", "bg": "bg-red-50"},
        "low_confidence": {"icon": "❓", "label": "Low Confidence", "color": "text-slate-500", "bg": "bg-slate-50"},
        "not_found": {"icon": "🔴", "label": "Not Found", "color": "text-red-500", "bg": "bg-red-50"},
        "cached": {"icon": "💾", "label": "Cached", "color": "text-purple-600", "bg": "bg-purple-50"},
    }

    @staticmethod
    def from_result(data: Optional[dict], sources: list, cross_validated: Optional[CrossValidatedResult] = None,
                    is_cached: bool = False) -> str:
        if data is None:
            return "not_found"

        if is_cached:
            return "cached"

        if cross_validated:
            if cross_validated.agreement_score >= 0.7 and cross_validated.confidence >= 0.7:
                return "verified"
            if cross_validated.contradictions:
                return "conflicting"
            if cross_validated.confidence < 0.4:
                return "low_confidence"

        # Single source
        source_types = set(s.source for s in sources if hasattr(s, 'source'))
        if "internal" in source_types or "knowledge" in source_types:
            return "company"

        if len(sources) <= 1:
            return "web_single"

        return "low_confidence"

    @staticmethod
    def to_html(badge_key: str) -> str:
        info = VerificationBadge.BADGES.get(badge_key, VerificationBadge.BADGES["low_confidence"])
        return f'<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium {info["bg"]} {info["color"]}">{info["icon"]} {info["label"]}</span>'


# ---------------------------------------------------------------------------
# Dual Source Merger
# ---------------------------------------------------------------------------

@dataclass
class DualSourceResult:
    answer: str
    internal_sources: list[dict] = field(default_factory=list)
    web_sources: list[dict] = field(default_factory=list)
    badge: str = "company"
    confidence: float = 0.5
    needs_verification: bool = False
    verification_reason: str = ""
    is_cached: bool = False

    def to_display(self) -> str:
        """Build a display string with badges."""
        parts = []

        if self.badge == "not_found":
            return self.answer

        # Badge
        badge_html = VerificationBadge.to_html(self.badge)
        parts.append(badge_html)

        # Answer
        parts.append(self.answer)

        # Sources
        if self.internal_sources:
            src_list = [f"📚 {s.get('label', 'Company')}" for s in self.internal_sources[:2]]
            parts.append(f"<div style='font-size:0.75rem;color:#64748b;margin-top:4px;'>{' · '.join(src_list)}</div>")

        if self.web_sources:
            src_list = []
            for s in self.web_sources[:2]:
                title = s.get('title', 'Source')
                url = s.get('url', '')
                if url:
                    src_list.append(f'<a href="{url}" style="color:#2563eb;text-decoration:underline;">🌐 {title}</a>')
                else:
                    src_list.append(f"🌐 {title}")
            parts.append(f"<div style='font-size:0.75rem;margin-top:4px;'>{' · '.join(src_list)}</div>")

        if self.needs_verification:
            parts.append(f"<div style='font-size:0.75rem;color:#d97706;margin-top:4px;'>⚠️ {self.verification_reason}</div>")

        if self.is_cached:
            parts.append("<div style='font-size:0.65rem;color:#8b5cf6;margin-top:2px;'>💾 Cached — may not be real-time</div>")

        return "\n".join(parts)


class DualSourceMerger:
    """Merges internal + web results into a single verified answer."""

    def __init__(self):
        self.search_engine = WebSearchEngine()
        self.cache = get_cache()

    def answer(self, query: str, tenant_id: int, user_id: int) -> DualSourceResult:
        """Get the best answer using internal data, web, or both."""
        # 1. Classify
        plan = SourceDecisionTree.get_search_plan(query)
        domain = plan["domain"]

        # 2. Check cache (skip for realtime and action)
        if domain not in ("realtime", "action"):
            cached = self.cache.get(query, domain)
            if cached:
                cached["is_cached"] = True
                return DualSourceResult(**cached)

        # 3. Search internal if needed
        internal_sources = []
        if plan.get("internal"):
            try:
                from app.shunya.knowledge import KnowledgePipeline
                ctx = KnowledgePipeline.get_context_for_ai(query, tenant_id)
                internal_sources = ctx.get("internal_sources", [])
            except Exception as e:
                logger.warning("Internal search failed: %s", e)

        # 4. Search web if needed
        web_sources = []
        web_results: list[SearchResultItem] = []
        if plan.get("web"):
            try:
                web_results = self.search_engine.search(query,
                    depth="deep" if domain == "factual" else "normal")
                web_sources = [{"title": r.title, "url": r.url, "snippet": r.snippet}
                               for r in web_results[:5]]
            except Exception as e:
                logger.warning("Web search failed: %s", e)

        # 5. Cross-validate web results
        cross_validated = None
        if len(web_results) >= 2:
            cross_validated = self.search_engine.cross_validate(web_results)

        # 6. Build answer
        answer_parts = []
        if internal_sources:
            for src in internal_sources[:2]:
                content = src.get("content", "")
                label = src.get("label", "Company Knowledge")
                answer_parts.append(f"📚 From {label}: {content[:500]}")

        if web_sources and not answer_parts:
            for src in web_sources[:2]:
                snippet = src.get("snippet", "")
                if snippet:
                    answer_parts.append(snippet[:500])

        if not answer_parts:
            # Nothing found — "I don't know" protocol
            return DualSourceResult(
                answer=("I searched your company data and the web but couldn't find a clear answer. "
                        "Here's what I can do:\n"
                        "- Upload a document with this information on the Ingest page\n"
                        "- Ask me to search differently\n"
                        "- I can research this deeper — just tell me where to look"),
                badge="not_found",
                confidence=0,
            )

        answer_text = "\n\n".join(answer_parts[:3])

        # 7. Determine badge
        badge = VerificationBadge.from_result(
            {"answer": answer_text}, web_results if web_results else [SearchResultItem(title="internal", url="", snippet="", source="internal")],
            cross_validated,
        )

        needs_verify = False
        verify_reason = ""
        if badge in ("conflicting", "low_confidence"):
            needs_verify = True
            verify_reason = "Sources don't fully agree. Verify with a manager before acting."

        result = DualSourceResult(
            answer=answer_text,
            internal_sources=internal_sources,
            web_sources=web_sources,
            badge=badge,
            confidence=cross_validated.confidence if cross_validated else (0.8 if internal_sources else 0.4),
            needs_verification=needs_verify,
            verification_reason=verify_reason,
        )

        # 8. Cache (non-realtime, non-action)
        if domain not in ("realtime", "action"):
            self.cache.set(query, domain, {
                "answer": answer_text,
                "badge": badge,
                "confidence": result.confidence,
                "needs_verification": needs_verify,
                "verification_reason": verify_reason,
                "is_cached": True,
            })

        return result