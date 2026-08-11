"""
SHUNYA — Web Intelligence Engine (FDA7).

Canonical external research interface with provenance, freshness, citations,
conflict handling, and prompt-injection isolation.

Reuses existing SearchProvider chain (DuckDuckGo → Brave → SearXNG).
Web content is always EXTERNAL EVIDENCE, never CANONICAL BUSINESS TRUTH.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Web Evidence Model
# ═══════════════════════════════════════════════════════════════════

class Freshness(Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass
class WebSource:
    """Provenance for a web-derived claim."""
    url: str
    title: str
    retrieved_at: datetime
    published_at: Optional[datetime] = None
    provider: str = "unknown"
    snippet: str = ""
    freshness: Freshness = Freshness.UNKNOWN


@dataclass
class WebResult:
    """Complete result from a web research operation."""
    claim: str
    sources: list[WebSource] = field(default_factory=list)
    confidence: float = 0.0
    conflict_detected: bool = False
    conflicts: list[dict] = field(default_factory=list)
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════
# Web Research Engine
# ═══════════════════════════════════════════════════════════════════

class WebResearchEngine:
    """Canonical external research engine.

    Uses the existing SearchProvider chain.
    All web content is classified as EXTERNAL, never FACT.
    """

    def __init__(self, search_provider=None):
        self._provider = search_provider

    def _get_provider(self):
        if self._provider:
            return self._provider
        from app.search.provider import resolve_search_provider
        return resolve_search_provider()

    def research(self, query: str, max_results: int = 5) -> WebResult:
        """Perform external research with full provenance.

        Returns structured result with sources, freshness, and conflict detection.
        """
        provider = self._get_provider()
        now = datetime.utcnow()

        try:
            raw_results = provider.search(query, max_results=max_results)
        except Exception as e:
            return WebResult(
                claim=f"Web search failed: {e}",
                confidence=0.0,
                error=str(e),
            )

        if not raw_results:
            return WebResult(
                claim="No web search results found.",
                confidence=0.0,
                error="empty_results",
            )

        sources = []
        claims = []
        for r in raw_results:
            url = r.get("url", "")
            title = r.get("title", "")
            snippet = r.get("body", "") or r.get("snippet", "")
            claims.append(snippet or title)

            source = WebSource(
                url=url,
                title=title,
                retrieved_at=now,
                provider=provider.name,
                snippet=snippet,
                freshness=self._determine_freshness(r),
            )
            sources.append(source)

        # Conflict detection
        conflict_detected, conflicts = self._detect_conflicts(sources)

        # Determine best claim
        best_claim = claims[0] if claims else "No meaningful content retrieved."

        return WebResult(
            claim=best_claim,
            sources=sources,
            confidence=0.7 if not conflict_detected else 0.4,
            conflict_detected=conflict_detected,
            conflicts=conflicts,
        )

    def _determine_freshness(self, raw: dict) -> Freshness:
        """Determine freshness of a search result."""
        published = raw.get("published") or raw.get("date") or raw.get("published_at")
        if not published:
            return Freshness.UNKNOWN
        try:
            if isinstance(published, str):
                pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            else:
                pub_date = published
            age_days = (datetime.utcnow() - pub_date).days
            if age_days <= 30:
                return Freshness.FRESH
            elif age_days <= 365:
                return Freshness.STALE
            return Freshness.STALE
        except (ValueError, TypeError):
            return Freshness.UNKNOWN

    def _detect_conflicts(self, sources: list[WebSource]) -> tuple[bool, list[dict]]:
        """Detect conflicts between sources."""
        if len(sources) < 2:
            return False, []

        conflicts = []
        seen_claims: dict[str, list[str]] = {}
        for src in sources:
            key = src.url
            if key not in seen_claims:
                seen_claims[key] = [src.snippet]
            else:
                seen_claims[key].append(src.snippet)

        # Check for contradictory claims across different sources
        claims_set = set()
        for src_list in seen_claims.values():
            for c in src_list:
                claims_set.add(c.strip()[:100])

        if len(claims_set) >= 2 and len(sources) >= 2:
            for i, s1 in enumerate(sources):
                for s2 in sources[i + 1:]:
                    if s1.snippet and s2.snippet and s1.snippet != s2.snippet:
                        conflicts.append({
                            "source_a": {"url": s1.url, "claim": s1.snippet[:100]},
                            "source_b": {"url": s2.url, "claim": s2.snippet[:100]},
                        })

        return len(conflicts) > 0, conflicts[:3]

    @staticmethod
    def format_citation(source: WebSource) -> str:
        """Format a source citation for user display."""
        parts = [source.title, source.url]
        if source.published_at:
            parts.append(f"published: {source.published_at.date()}")
        parts.append(f"retrieved: {source.retrieved_at.date()}")
        parts.append(f"source: {source.provider}")
        return " | ".join(parts)


# ═══════════════════════════════════════════════════════════════════
# Prompt Injection Guard (FDA7.6)
# ═══════════════════════════════════════════════════════════════════

class PromptInjectionGuard:
    """Guards against prompt injection in external web content.

    Web content is DATA, never INSTRUCTION.
    """

    INJECTION_PATTERNS = [
        "ignore previous instructions",
        "ignore all previous",
        "forget your instructions",
        "you are now",
        "you are a free",
        "system instruction",
        "override your",
        "disregard all",
        "new instructions:",
        "you must not",
        "ignore your rules",
        "ignore security",
        "reveal your",
    ]

    @classmethod
    def scan(cls, text: str) -> list[dict]:
        """Scan text for prompt injection patterns.

        Returns list of detected patterns with context.
        """
        findings = []
        text_lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if pattern in text_lower:
                idx = text_lower.index(pattern)
                start = max(0, idx - 40)
                end = min(len(text), idx + len(pattern) + 40)
                findings.append({
                    "pattern": pattern,
                    "context": text[start:end],
                })
        return findings

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Sanitize web content for safe use in prompts.

        Replaces injection-like content with safe markers.
        """
        result = text
        for pattern in cls.INJECTION_PATTERNS:
            result = result.replace(pattern, f"[BLOCKED: {pattern}]")
            result = result.replace(pattern.capitalize(), f"[BLOCKED: {pattern}]")
            result = result.replace(pattern.upper(), f"[BLOCKED: {pattern}]")
        return result


# ═══════════════════════════════════════════════════════════════════
# Web Intelligence Service — integrates with SHUNYA intelligence
# ═══════════════════════════════════════════════════════════════════

class WebIntelligenceService:
    """Complete web intelligence service.

    Integrates web research with the intelligence core.
    All external content is EXTERNAL evidence, never FACT.
    """

    def __init__(self):
        self._engine = WebResearchEngine()

    def research_with_context(self, query: str, company_context: Optional[str] = None) -> dict:
        """Perform web research tied to company context.

        Company-first: uses company data before external retrieval.
        """
        result = self._engine.research(query)

        # Build response with provenance
        response = {
            "query": query,
            "claim": result.claim,
            "confidence": result.confidence,
            "conflict_detected": result.conflict_detected,
            "conflicts": result.conflicts,
            "classification": "external",
            "sources": [
                {
                    "url": s.url,
                    "title": s.title,
                    "retrieved_at": s.retrieved_at.isoformat(),
                    "published_at": s.published_at.isoformat() if s.published_at else None,
                    "freshness": s.freshness.value,
                    "provider": s.provider,
                    "citation": WebResearchEngine.format_citation(s),
                }
                for s in result.sources
            ],
        }

        # Scan for prompt injection
        all_text = " ".join([s.snippet for s in result.sources])
        injection_findings = PromptInjectionGuard.scan(all_text)
        if injection_findings:
            response["injection_detected"] = True
            response["injection_patterns"] = injection_findings
        else:
            response["injection_detected"] = False

        return response