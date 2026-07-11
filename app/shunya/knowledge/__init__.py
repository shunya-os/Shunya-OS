"""Shunya OS — Knowledge Pipeline (Internal Data First → Web Secondary).

Every AI query searches:
1. Internal knowledge base (stored facts from company data)
2. Entity data (structured records — leads, patients, bookings)
3. Activity logs (team actions)
4. AI feedback corrections (learned from past mistakes)
5. Web search (fallback — only if internal has no good answer)

Results are stored back into the knowledge base so the system
gets smarter over time without manual curation.
"""
import json, logging
from typing import Optional
from datetime import datetime
from flask import g
from app import db
from app.models import KnowledgeEntry, Entity, EntityDefinition, ActivityLog, AIFeedback

logger = logging.getLogger("app.knowledge")


class KnowledgePipeline:
    """Searches internal data first, then falls back to web. Stores learnings."""

    @staticmethod
    def search(query: str, tenant_id: int, user_id: Optional[int] = None,
               limit: int = 5, allow_web: bool = True) -> dict:
        """Search all internal sources, then fall back to web if needed.
        
        Returns structured context with source attribution and confidence scores.
        """
        results = []
        sources = []

        # 1. Knowledge base (company-fed facts — highest authority)
        kb = KnowledgeEntry.query.filter(
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.question.ilike(f"%{query}%")
        ).order_by(KnowledgeEntry.use_count.desc()).limit(limit).all()

        for entry in kb:
            results.append({
                "type": "knowledge_base",
                "question": entry.question,
                "answer": entry.answer,
                "confidence": entry.confidence,
                "source": entry.source,
                "source_url": entry.source_url,
                "source_label": "Company Knowledge",
            })
            entry.use_count += 1
            sources.append("internal")

        # 2. Entity data search (structured records)
        defs = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        for d in defs:
            searchable = d.searchable_fields or []
            if not searchable:
                continue
            filters = []
            for field_name in searchable:
                filters.append(Entity.data[field_name].as_string().ilike(f"%{query}%"))
            entities = Entity.query.filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == d.id,
                Entity.is_archived == False,
                db.or_(*filters)
            ).order_by(Entity.created_at.desc()).limit(limit).all()

            for e in entities:
                summary = e.ai_summary or e.display_name
                results.append({
                    "type": "entity",
                    "entity_type": d.label,
                    "entity_code": e.code,
                    "entity_id": e.id,
                    "summary": summary,
                    "data": {k: v for k, v in e.data.items() if k in searchable},
                    "confidence": 0.8,
                    "source_label": f"{d.icon} {d.label}",
                })
                sources.append("internal")

        # 3. Activity log (recent team actions)
        activities = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.detail.ilike(f"%{query}%")
        ).order_by(ActivityLog.created_at.desc()).limit(limit).all()

        for a in activities:
            results.append({
                "type": "activity",
                "action": a.action,
                "detail": a.detail,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "confidence": 0.7,
                "source_label": "Activity Log",
            })
            sources.append("internal")

        # 4. AI feedback corrections (learned from past mistakes)
        corrections = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.correction.isnot(None),
        ).order_by(AIFeedback.created_at.desc()).limit(3).all()

        for c in corrections:
            results.append({
                "type": "correction",
                "original_query": c.query,
                "correction": c.correction,
                "confidence": 0.9,
                "source_label": "AI Learning",
            })
            sources.append("internal")

        has_internal = len(sources) > 0

        # Commit usage count updates
        db.session.commit()

        response = {
            "results": results[:limit],
            "has_internal_data": has_internal,
            "total_internal": len(results),
        }

        # 5. Web search (fallback — only if internal has no good answer)
        if allow_web and (not has_internal or len(results) < 3):
            web_results = KnowledgePipeline.search_web(query, limit=limit - len(results))
            if web_results:
                response["web_results"] = web_results
                response["has_web_results"] = True

                # Store web knowledge for future use
                for wr in web_results[:2]:
                    KnowledgePipeline.store_knowledge(
                        tenant_id=tenant_id,
                        question=query,
                        answer=wr["snippet"],
                        source="web",
                        confidence=0.5,
                        source_url=wr.get("url", ""),
                    )

        return response

    @staticmethod
    def search_web(query: str, limit: int = 3) -> list:
        """Search the web as a secondary source.
        
        Uses web_search tool when available, falls back gracefully.
        """
        results = []
        try:
            # Try web_search tool
            from hermes_tools import web_search
            raw = web_search(query=query, limit=limit)
            web_data = raw.get("data", {}).get("web", [])
            for item in web_data[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", ""),
                    "confidence": 0.4,  # Lower confidence — needs verification
                    "type": "web",
                })
            logger.info("Web search returned %d results for: %s", len(results), query)
        except ImportError:
            logger.warning("web_search tool not available")
        except Exception as e:
            logger.warning("Web search failed: %s", e)

        return results

    @staticmethod
    def search_web_fallback(query: str, limit: int = 3) -> list:
        """Fallback web search using requests + a public API."""
        results = []
        try:
            import requests
            import urllib.parse

            # Try DuckDuckGo instant answer API (no key required)
            encoded = urllib.parse.quote(query)
            resp = requests.get(
                f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1",
                timeout=8,
                headers={"User-Agent": "ShunyaOS/1.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                abstract = data.get("AbstractText", "")
                if abstract:
                    results.append({
                        "title": data.get("Heading", query),
                        "url": data.get("AbstractURL", ""),
                        "snippet": abstract[:500],
                        "confidence": 0.3,
                        "type": "web",
                    })
                # Related topics
                for topic in data.get("RelatedTopics", [])[:limit]:
                    if "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "")[:100],
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", "")[:300],
                            "confidence": 0.3,
                            "type": "web",
                        })
        except Exception as e:
            logger.warning("Web search fallback failed: %s", e)

        return results[:limit]

    @staticmethod
    def search_web_with_serper(query: str, limit: int = 5) -> list:
        """Search the web using Serper.dev API (if configured)."""
        import os
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return KnowledgePipeline.search_web_fallback(query, limit)

        results = []
        try:
            import requests
            resp = requests.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": limit},
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("organic", [])[:limit]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "confidence": 0.5,
                        "type": "web",
                    })
        except Exception as e:
            logger.warning("Serper search failed: %s", e)

        return results or KnowledgePipeline.search_web_fallback(query, limit)

    @staticmethod
    def store_knowledge(tenant_id: int, question: str, answer: str,
                        source: str = "ai_generated", confidence: float = 0.5,
                        source_url: Optional[str] = None) -> KnowledgeEntry:
        """Store a new fact in the knowledge base for future reference."""
        q_normalized = question.lower().strip()

        existing = KnowledgeEntry.query.filter_by(
            tenant_id=tenant_id, question=q_normalized,
        ).first()

        if existing:
            existing.answer = answer
            existing.confidence = max(existing.confidence, confidence)
            existing.use_count += 1
            if source_url:
                existing.source_url = source_url
            db.session.commit()
            return existing

        entry = KnowledgeEntry(
            tenant_id=tenant_id,
            question=q_normalized,
            answer=answer,
            source=source,
            source_url=source_url,
            confidence=confidence,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    @staticmethod
    def get_context_for_ai(query: str, tenant_id: int) -> dict:
        """Build a structured context object with source attribution for LLM consumption."""
        result = KnowledgePipeline.search(query, tenant_id)

        context = {
            "query": query,
            "internal_sources": [],
            "web_sources": [],
            "has_internal_data": result.get("has_internal_data", False),
            "has_web_data": result.get("has_web_results", False),
        }

        for r in result.get("results", []):
            if r["type"] == "knowledge_base":
                context["internal_sources"].append({
                    "type": "knowledge",
                    "label": r["source_label"],
                    "content": f"Q: {r['question']}\nA: {r['answer']}",
                    "confidence": r["confidence"],
                })
            elif r["type"] == "entity":
                context["internal_sources"].append({
                    "type": "entity",
                    "label": r["source_label"],
                    "content": f"[{r['entity_type']}] {r['entity_code']}: {r['summary']}",
                    "confidence": r["confidence"],
                })

        for wr in result.get("web_results", []):
            context["web_sources"].append({
                "type": "web",
                "label": "Web Search",
                "title": wr["title"],
                "url": wr["url"],
                "snippet": wr["snippet"],
                "confidence": wr["confidence"],
            })

        return context