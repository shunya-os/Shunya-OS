"""
SHUNYA — Mixed Intelligence Router

Constitutional Directive — Open Capability Acceleration

Data source priority (hard mandate):
1. Business Data (PostgreSQL) — Primary source of truth
2. Internal Knowledge (past queries, timeline, relationships) — Contextual enrichment
3. Internet (DuckDuckGo, Brave, SearXNG) — Supporting evidence
4. AI Synthesis (provider chain) — Final output with source labels

Every output SHALL be labeled by data source so users always know
where information comes from.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Source labeling
# ---------------------------------------------------------------------------

class SourceLabel:
    """Identifies the origin of a piece of information."""

    BUSINESS_DATA = "business_data"
    INTERNAL_KNOWLEDGE = "internal_knowledge"
    INTERNET = "internet"
    AI_SYNTHESIS = "ai_synthesis"

    @classmethod
    def label(cls, source: str) -> str:
        labels = {
            cls.BUSINESS_DATA: "Your business data",
            cls.INTERNAL_KNOWLEDGE: "SHUNYA's knowledge",
            cls.INTERNET: "Internet research",
            cls.AI_SYNTHESIS: "AI analysis",
        }
        return labels.get(source, source)


class SourceAttribution:
    """A claim with its source attribution."""

    def __init__(self, text: str, source: str, confidence: str = "high",
                 url: str | None = None):
        self.text = text
        self.source = source
        self.confidence = confidence
        self.url = url

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "source_label": SourceLabel.label(self.source),
            "confidence": self.confidence,
            "url": self.url,
        }


class MixedIntelligenceResponse:
    """Complete response from the Mixed Intelligence Router."""

    def __init__(self, query: str):
        self.query = query
        self.claims: list[SourceAttribution] = []
        self.synthesis: str | None = None
        self.synthesis_model: str | None = None
        self.error: str | None = None

    def add_claim(self, text: str, source: str, confidence: str = "high",
                  url: str | None = None):
        self.claims.append(SourceAttribution(text, source, confidence, url))

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "claims": [c.to_dict() for c in self.claims],
            "synthesis": self.synthesis,
            "synthesis_model": self.synthesis_model,
            "total_sources": len(set(c.source for c in self.claims)),
            "error": self.error,
        }

    @property
    def has_business_data(self) -> bool:
        return any(c.source == "business_data" for c in self.claims)

    @property
    def has_internet_data(self) -> bool:
        return any(c.source == "internet" for c in self.claims)


# ---------------------------------------------------------------------------
# Business Data Retriever
# ---------------------------------------------------------------------------

class BusinessDataRetriever:
    """Query PostgreSQL for business data relevant to the user's question."""

    def __init__(self):
        from app import db
        self.db = db

    def search(self, query: str, identity_id: str | None = None,
               org_id: str | None = None, max_results: int = 10) -> list[SourceAttribution]:
        """Search business objects, invoices, payments, relationships, and more."""
        results = []
        from sqlalchemy import text

        # 1. Founder objects
        try:
            objects = self.db.session.execute(
                text("""SELECT object_id, object_type, name, content, created_at
                        FROM founder_objects
                        WHERE status='active'
                        AND (name ILIKE :q OR content ILIKE :q)
                        ORDER BY created_at DESC LIMIT :limit"""),
                {"q": f"%{query}%", "limit": max_results},
            ).fetchall()
            for obj in objects:
                snippet = (obj.content or "")[:300] if obj.content else obj.name
                results.append(SourceAttribution(
                    text=f"{obj.name}: {snippet}",
                    source="business_data",
                    confidence="high",
                ))
        except Exception as e:
            logger.warning(f"Business object search failed: {e}")

        # 2. Invoices
        try:
            invoices = self.db.session.execute(
                text("""SELECT number, client_name, total_amount, status
                        FROM fin_invoices
                        WHERE client_name ILIKE :q OR number ILIKE :q
                        LIMIT :limit"""),
                {"q": f"%{query}%", "limit": 5},
            ).fetchall()
            for inv in invoices:
                results.append(SourceAttribution(
                    text=f"Invoice #{inv.number} — {inv.client_name}: ${inv.total_amount:,.2f} ({inv.status})",
                    source="business_data",
                    confidence="high",
                ))
        except Exception as e:
            logger.warning(f"Invoice search failed: {e}")

        # 3. Financial summary (revenue, cash flow, totals)
        financial_keywords = ["revenue", "cash flow", "total", "income", "expense",
                              "spent", "paid", "outstanding", "invoice", "sale"]
        if any(kw in query.lower() for kw in financial_keywords):
            try:
                total_invoiced = self.db.session.execute(
                    text("SELECT COALESCE(SUM(total_amount),0) FROM fin_invoices")
                ).scalar() or 0
                total_paid = self.db.session.execute(
                    text("SELECT COALESCE(SUM(amount),0) FROM fin_payments WHERE type='receipt'")
                ).scalar() or 0
                results.append(SourceAttribution(
                    text=f"Total invoiced: ${total_invoiced:,.2f}. Total received: ${total_paid:,.2f}. Outstanding: ${max(0, total_invoiced - total_paid):,.2f}.",
                    source="business_data",
                    confidence="high",
                ))
            except Exception as e:
                logger.warning(f"Financial summary failed: {e}")

        # 4. Count summaries
        count_keywords = ["how many", "count", "number of", "total objects",
                          "list all", "show all"]
        if any(kw in query.lower() for kw in count_keywords):
            try:
                total_objects = self.db.session.execute(
                    text("SELECT COUNT(*) FROM founder_objects WHERE status='active'")
                ).scalar() or 0
                results.append(SourceAttribution(
                    text=f"You have {total_objects} active business objects.",
                    source="business_data",
                    confidence="high",
                ))
            except Exception as e:
                logger.warning(f"Object count failed: {e}")

        return results


# ---------------------------------------------------------------------------
# Internet Retriever
# ---------------------------------------------------------------------------

class InternetRetriever:
    """Search the internet for supporting evidence."""

    def search(self, query: str, max_results: int = 5) -> list[SourceAttribution]:
        """Search via DuckDuckGo → Brave → SearXNG chain."""
        results = []
        try:
            from app.search.provider import resolve_search_provider
            provider = resolve_search_provider()
            web_results = provider.search(query, max_results=max_results)
            for wr in web_results:
                title = wr.get("title", "")
                body = (wr.get("body", "") or "")[:300]
                url = wr.get("url", "")
                if title:
                    text = f"{title}: {body}" if body else title
                    results.append(SourceAttribution(
                        text=text,
                        source="internet",
                        confidence="medium",
                        url=url,
                    ))
        except Exception as e:
            logger.warning(f"Internet search failed: {e}")

        return results


# ---------------------------------------------------------------------------
# AI Synthesizer
# ---------------------------------------------------------------------------

class AISynthesizer:
    """Use the AI provider chain to synthesize a final answer."""

    def synthesize(self, query: str, business_data: list[SourceAttribution],
                   internet_data: list[SourceAttribution],
                   internal_knowledge: list[SourceAttribution] | None = None) -> str | None:
        """Synthesize claims into a coherent answer using the best available AI."""
        from app.ai.provider import get_provider

        provider = get_provider()
        if provider.name == "local":
            # Without a real AI provider, return a template-based summary
            return self._template_summary(query, business_data, internet_data)

        # Build the system prompt
        system_prompt = """You are SHUNYA, an AI operating system for business.

Answer the user's question using the provided data sources. Follow these rules:
1. Business data is the primary source of truth — prefer it over everything.
2. Internet data is supporting evidence — use it when business data is insufficient.
3. If you don't know the answer from the provided data, say so honestly.
4. Always cite which data source you're using.
5. Be concise, direct, and helpful.

Data sources found for this question:
"""

        source_summary = []
        if business_data:
            source_summary.append("--- BUSINESS DATA ---")
            for c in business_data:
                source_summary.append(f"- {c.text}")
        if internet_data:
            source_summary.append("--- INTERNET RESEARCH ---")
            for c in internet_data:
                src = f" (Source: {c.url})" if c.url else ""
                source_summary.append(f"- {c.text}{src}")
        if internal_knowledge:
            source_summary.append("--- INTERNAL KNOWLEDGE ---")
            for c in internal_knowledge:
                source_summary.append(f"- {c.text}")

        user_message = f"Question: {query}\n\n"
        user_message += "\n".join(source_summary) if source_summary else "No specific data found for this query."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            result = provider.complete(messages, temperature=0.3, max_tokens=1024)
            if result.get("finish_reason") != "error":
                return result.get("content")
        except Exception as e:
            logger.warning(f"AI synthesis failed: {e}")

        return self._template_summary(query, business_data, internet_data)

    def _template_summary(self, query: str, business_data: list[SourceAttribution],
                           internet_data: list[SourceAttribution]) -> str:
        """Fallback template-based summary when AI is unavailable."""
        parts = []
        if business_data:
            parts.append("Based on your business data:")
            for c in business_data:
                parts.append(f"  • {c.text}")
        if internet_data:
            parts.append("From internet research:")
            for c in internet_data:
                parts.append(f"  • {c.text}")
        if not business_data and not internet_data:
            parts.append("I don't have enough data to answer that question yet. "
                         "Try adding more business objects or being more specific.")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Mixed Intelligence Router
# ---------------------------------------------------------------------------

class MixedIntelligenceRouter:
    """Route queries to the correct data source and synthesize answers.

    Data source priority:
    1. Business Data (PostgreSQL) — Primary truth
    2. Internal Knowledge — Contextual enrichment
    3. Internet — Supporting evidence
    4. AI Synthesis — Final output with source labels
    """

    def __init__(self):
        self.business = BusinessDataRetriever()
        self.internet = InternetRetriever()
        self.ai = AISynthesizer()

    def answer(self, query: str, identity_id: str | None = None,
               org_id: str | None = None) -> MixedIntelligenceResponse:
        """Answer a question using the full mixed intelligence pipeline."""
        response = MixedIntelligenceResponse(query)

        try:
            # Stage 1: Business data (primary source of truth)
            logger.info(f"MIR Stage 1: Searching business data for '{query}'")
            business_claims = self.business.search(query, identity_id, org_id)
            for c in business_claims:
                response.add_claim(c.text, c.source, c.confidence)

            # Stage 2: Internet research (supporting evidence)
            # Only if business data is thin or question explicitly asks for it
            internet_keywords = ["search", "research", "find", "look up", "google",
                                 "what is", "who is", "latest", "news", "market",
                                 "competitor", "supplier", "price", "review"]
            needs_internet = (len(business_claims) < 3 or
                              any(kw in query.lower() for kw in internet_keywords))

            internet_claims: list[SourceAttribution] = []
            if needs_internet:
                logger.info(f"MIR Stage 2: Searching internet for '{query}'")
                internet_claims = self.internet.search(query)
                for c in internet_claims:
                    response.add_claim(c.text, c.source, c.confidence)

            # Stage 3: AI synthesis
            logger.info(f"MIR Stage 3: Synthesizing answer for '{query}'")
            synthesis = self.ai.synthesize(
                query, business_claims, internet_claims
            )
            if synthesis:
                response.synthesis = synthesis
                response.synthesis_model = "mixed-intelligence"

        except Exception as e:
            logger.error(f"Mixed Intelligence Router failed: {e}")
            response.error = str(e)
            response.synthesis = "I encountered an error processing your question. Please try again."

        return response


# Singleton
_router: MixedIntelligenceRouter | None = None


def get_router() -> MixedIntelligenceRouter:
    global _router
    if _router is None:
        _router = MixedIntelligenceRouter()
    return _router


def reset_router():
    global _router
    _router = None