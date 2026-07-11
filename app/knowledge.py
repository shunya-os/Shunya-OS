"""Shunya OS — Knowledge Pipeline (Internal Data First → Web Secondary).

Every AI query searches:
1. Internal knowledge base (stored facts)
2. Entity data (structured records)
3. Past AI conversations (Honcho memory)
4. Activity logs (team actions)
5. Web (fallback — only if internal has no answer)
"""
import json, logging, hashlib
from typing import Optional
from datetime import datetime
from flask import g
from app import db
from app.models import KnowledgeEntry, Entity, EntityDefinition, ActivityLog, AIFeedback

logger = logging.getLogger("app.knowledge")


class KnowledgePipeline:
    """Searches internal data first, then falls back to web."""

    @staticmethod
    def search(query: str, tenant_id: int, user_id: Optional[int] = None, limit: int = 5) -> dict:
        """Search all internal sources for an answer. Returns context + confidence."""
        results = []
        sources = []

        # 1. Knowledge base (exact + semantic via ILIKE)
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
            })
            entry.use_count += 1
            sources.append("internal")

        # 2. Entity data search
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
                })
                sources.append("internal")

        # 3. Activity log (recent actions related to query)
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
            })
            sources.append("internal")

        has_internal = len(sources) > 0

        db.session.commit()

        return {
            "results": results[:limit],
            "has_internal_data": has_internal,
            "total_internal": len(results),
            "should_search_web": not has_internal,
        }

    @staticmethod
    def store_knowledge(tenant_id: int, question: str, answer: str,
                        source: str = "ai_generated", confidence: float = 0.5,
                        source_url: Optional[str] = None) -> KnowledgeEntry:
        """Store a new fact in the knowledge base for future reference."""
        # Normalize the question
        q_normalized = question.lower().strip()

        existing = KnowledgeEntry.query.filter_by(
            tenant_id=tenant_id,
            question=q_normalized,
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
    def get_context_for_ai(query: str, tenant_id: int) -> str:
        """Build a text context string from all internal sources for LLM consumption."""
        result = KnowledgePipeline.search(query, tenant_id)
        if not result["results"]:
            return ""

        parts = ["### Internal Company Data\n"]
        for r in result["results"]:
            if r["type"] == "knowledge_base":
                parts.append(f"Q: {r['question']}\nA: {r['answer']} (confidence: {r['confidence']})")
            elif r["type"] == "entity":
                parts.append(f"[{r['entity_type']}] {r['entity_code']}: {r['summary']}")
                if r.get("data"):
                    parts.append(f"  Details: {json.dumps(r['data'], indent=2)}")
            elif r["type"] == "activity":
                parts.append(f"[Activity] {r['action']}: {r['detail']}")
            elif r["type"] == "correction":
                parts.append(f"[Correction] Query: '{r['original_query']}' → {r['correction']}")

        return "\n\n".join(parts)