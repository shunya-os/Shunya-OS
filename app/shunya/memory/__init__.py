"""Shunya Memory — 8-class memory architecture.

Memory is not one giant vector database. Each class serves a distinct purpose
with different behavior, retention, and access control.

Classes:
1. WORKING_MEMORY  — Immediate reasoning context (ephemeral)
2. EPISODIC        — What happened in a specific event/interaction
3. SEMANTIC        — Known organizational concepts and facts
4. PROCEDURAL      — How the organization performs work
5. RELATIONSHIP    — History about an entity or relationship
6. DECISION        — Past decisions and their reasoning
7. OUTCOME         — What happened after decisions
8. LEARNING        — Approved organizational learning
"""
import json, logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app import db
from app.models import KnowledgeEntry, Entity, ActivityLog

logger = logging.getLogger("app.shunya.memory")


class MemoryClass(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    RELATIONSHIP = "relationship"
    DECISION = "decision"
    OUTCOME = "outcome"
    LEARNING = "learning"


# Authority hierarchy: which memory classes override which
MEMORY_AUTHORITY = {
    MemoryClass.SEMANTIC: 8,      # Highest — company facts
    MemoryClass.PROCEDURAL: 7,    # How things are done
    MemoryClass.LEARNING: 6,      # Approved patterns
    MemoryClass.DECISION: 5,      # Past decisions
    MemoryClass.OUTCOME: 4,       # What happened
    MemoryClass.RELATIONSHIP: 3,  # Entity history
    MemoryClass.EPISODIC: 2,      # Events
    MemoryClass.WORKING: 1,       # Lowest — ephemeral
}

# Retention (days) per class
MEMORY_RETENTION = {
    MemoryClass.WORKING: 1,       # Ephemeral — 1 day
    MemoryClass.EPISODIC: 90,     # Events — 90 days
    MemoryClass.SEMANTIC: 730,    # Facts — 2 years
    MemoryClass.PROCEDURAL: 730,  # Procedures — 2 years
    MemoryClass.RELATIONSHIP: 365, # Relationships — 1 year
    MemoryClass.DECISION: 730,    # Decisions — 2 years
    MemoryClass.OUTCOME: 365,     # Outcomes — 1 year
    MemoryClass.LEARNING: 730,    # Learning — 2 years
}


class MemoryStore:
    """8-class memory system with provenance, authority, and retention."""

    @staticmethod
    def store(memory_class: MemoryClass, tenant_id: int,
              key: str, content: str,
              user_id: Optional[int] = None,
              entity_id: Optional[int] = None,
              source: str = "ai_observed",
              confidence: float = 0.5,
              metadata: Optional[Dict] = None,
              tags: Optional[List[str]] = None) -> dict:
        """Store a memory with full provenance."""
        metadata = metadata or {}
        tags = tags or []
        
        entry = KnowledgeEntry(
            tenant_id=tenant_id,
            question=f"memory.{memory_class.value}:{key}",
            answer=content[:10000],
            source=f"{source}.{memory_class.value}",
            confidence=min(max(confidence, 0.0), 1.0),
            category=memory_class.value,
            meta_data=json.dumps({
                "memory_class": memory_class.value,
                "authority": MEMORY_AUTHORITY.get(memory_class, 1),
                "retention_days": MEMORY_RETENTION.get(memory_class, 30),
                "user_id": user_id,
                "entity_id": entity_id,
                "key": key,
                "tags": tags,
                "metadata": metadata,
                "stored_at": datetime.utcnow().isoformat(),
            }),
        )
        db.session.add(entry)
        db.session.flush()
        
        # Log storage
        activity = ActivityLog(
            tenant_id=tenant_id,
            user_id=user_id,
            entity_id=entity_id,
            action=f"memory.stored.{memory_class.value}",
            detail=f"Stored: {key} ({memory_class.value})",
        )
        db.session.add(activity)
        db.session.commit()
        
        return {
            "id": entry.id,
            "class": memory_class.value,
            "key": key,
            "confidence": confidence,
        }

    @staticmethod
    def retrieve(memory_class: MemoryClass, tenant_id: int,
                 key: Optional[str] = None,
                 query: Optional[str] = None,
                 entity_id: Optional[int] = None,
                 limit: int = 5) -> List[Dict]:
        """Retrieve memories by class, key, or content query."""
        filters = [
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.category == memory_class.value,
        ]
        
        if key:
            filters.append(KnowledgeEntry.question == f"memory.{memory_class.value}:{key}")
        
        if entity_id:
            filters.append(KnowledgeEntry.meta_data.contains(f'"entity_id": {entity_id}'))
        
        if query:
            filters.append(KnowledgeEntry.answer.ilike(f"%{query}%"))
        
        entries = KnowledgeEntry.query.filter(
            *filters
        ).order_by(
            KnowledgeEntry.confidence.desc(),
            KnowledgeEntry.created_at.desc()
        ).limit(limit).all()
        
        return [MemoryStore._format_entry(e) for e in entries]

    @staticmethod
    def search_all(tenant_id: int, query: str, limit: int = 8) -> Dict[str, List]:
        """Search across ALL memory classes, grouped by class."""
        results = {mc.value: [] for mc in MemoryClass}
        
        entries = KnowledgeEntry.query.filter(
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.question.like("memory.%"),
            KnowledgeEntry.answer.ilike(f"%{query}%"),
        ).order_by(KnowledgeEntry.confidence.desc()).limit(limit * 3).all()
        
        for e in entries:
            mc = e.category or "semantic"
            if mc in results and len(results[mc]) < limit:
                results[mc].append(MemoryStore._format_entry(e))
        
        # Remove empty classes
        return {k: v for k, v in results.items() if v}

    @staticmethod
    def get_context(tenant_id: int, entity_id: Optional[int] = None,
                    query: Optional[str] = None) -> Dict:
        """Get full memory context for AI reasoning — all classes relevant to this entity."""
        context = {}
        
        # Working memory (recent, high-signal)
        working = MemoryStore.retrieve(MemoryClass.WORKING, tenant_id,
                                        entity_id=entity_id, limit=3)
        if working:
            context["working"] = working
        
        # Episodic (recent events)
        episodic = MemoryStore.retrieve(MemoryClass.EPISODIC, tenant_id,
                                         entity_id=entity_id, limit=5)
        if episodic:
            context["episodic"] = episodic
        
        # Semantic (facts about this entity)
        semantic = MemoryStore.retrieve(MemoryClass.SEMANTIC, tenant_id,
                                         entity_id=entity_id, query=query, limit=3)
        if semantic:
            context["semantic"] = semantic
        
        # Relationship (history)
        relationship = MemoryStore.retrieve(MemoryClass.RELATIONSHIP, tenant_id,
                                             entity_id=entity_id, limit=3)
        if relationship:
            context["relationship"] = relationship
        
        # Decision memory (past decisions for this entity)
        decision = MemoryStore.retrieve(MemoryClass.DECISION, tenant_id,
                                         entity_id=entity_id, limit=3)
        if decision:
            context["decision"] = decision
        
        return context

    @staticmethod
    def store_episodic(tenant_id: int, entity_id: int, event: str,
                        detail: str, user_id: Optional[int] = None) -> dict:
        """Convenience: store an episodic memory (something that happened)."""
        return MemoryStore.store(
            MemoryClass.EPISODIC, tenant_id,
            key=f"event:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            content=f"{event}: {detail}",
            user_id=user_id, entity_id=entity_id,
            source="observer",
            confidence=0.9,
            tags=["event", "auto"],
        )

    @staticmethod
    def store_decision(tenant_id: int, entity_id: Optional[int],
                        subject: str, decision: str, reasoning: str,
                        user_id: int, confidence: float = 0.8) -> dict:
        """Convenience: store a decision memory with reasoning."""
        return MemoryStore.store(
            MemoryClass.DECISION, tenant_id,
            key=f"decision:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            content=f"Subject: {subject}\nDecision: {decision}\nReasoning: {reasoning}\nConfidence: {confidence}",
            user_id=user_id, entity_id=entity_id,
            source="reasoning",
            confidence=confidence,
            tags=["decision", "reasoned"],
        )

    @staticmethod
    def store_outcome(tenant_id: int, entity_id: Optional[int],
                       decision_key: str, expected: str, actual: str,
                       learning: Optional[str] = None) -> dict:
        """Convenience: store an outcome with comparison."""
        content = f"Decision: {decision_key}\nExpected: {expected}\nActual: {actual}"
        if learning:
            content += f"\nLearning: {learning}"
        
        return MemoryStore.store(
            MemoryClass.OUTCOME, tenant_id,
            key=f"outcome:{decision_key}",
            content=content,
            entity_id=entity_id,
            source="observer",
            confidence=0.8 if expected == actual else 0.4,
            tags=["outcome", "comparison"],
        )

    @staticmethod
    def store_working(tenant_id: int, user_id: int, context_key: str,
                       content: str, ttl_minutes: int = 60) -> dict:
        """Convenience: store working memory (ephemeral reasoning context).
        
        Working memory auto-expires. This is for temporary reasoning context
        that should not persist permanently.
        """
        return MemoryStore.store(
            MemoryClass.WORKING, tenant_id,
            key=f"working:{user_id}:{context_key}",
            content=content,
            user_id=user_id,
            source="reasoning",
            confidence=0.5,
            metadata={"ttl_minutes": ttl_minutes, "context_key": context_key},
            tags=["working", "ephemeral"],
        )

    @staticmethod
    def get_recent(tenant_id: int, limit: int = 20) -> List[Dict]:
        """Get most recent memories across all classes."""
        entries = KnowledgeEntry.query.filter(
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.question.like("memory.%"),
        ).order_by(KnowledgeEntry.created_at.desc()).limit(limit).all()
        
        return [MemoryStore._format_entry(e) for e in entries]

    @staticmethod
    def get_stats(tenant_id: int) -> Dict:
        """Get memory statistics — count per class."""
        stats = {}
        for mc in MemoryClass:
            count = KnowledgeEntry.query.filter(
                KnowledgeEntry.tenant_id == tenant_id,
                KnowledgeEntry.category == mc.value,
            ).count()
            if count > 0:
                stats[mc.value] = count
        return stats

    @staticmethod
    def _format_entry(entry: KnowledgeEntry) -> Dict:
        """Format a knowledge entry as a memory object."""
        meta = {}
        if entry.meta_data:
            try:
                meta = json.loads(entry.meta_data)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {
            "id": entry.id,
            "class": entry.category or "semantic",
            "key": entry.question.replace("memory.", "", 1) if entry.question.startswith("memory.") else entry.question,
            "content": entry.answer[:500],
            "confidence": entry.confidence,
            "authority": meta.get("authority", 1),
            "tags": meta.get("tags", []),
            "entity_id": meta.get("entity_id"),
            "user_id": meta.get("user_id"),
            "source": entry.source,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }