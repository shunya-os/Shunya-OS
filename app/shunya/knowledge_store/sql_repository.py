"""SQLAlchemy-backed KnowledgeRepository for production use.

Bridges the KnowledgeObject dataclass (app.shunya.knowledge_store.models)
with the KnowledgeFact SQLAlchemy model (app.shunya.knowledge_store).
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app import db
from app.shunya.knowledge_store import KnowledgeFact
from app.shunya.knowledge_store.models import (
    KnowledgeObject, KnowledgeObjectStatus, SearchQuery, SearchResult,
)
from app.shunya.knowledge_store.repository import KnowledgeRepository


class SqlKnowledgeRepository(KnowledgeRepository):
    """Production KnowledgeRepository backed by PostgreSQL (knowledge_facts table).

    Each KnowledgeObject maps to a KnowledgeFact row with version tracking.
    Thread-safe via database transactions.
    """

    def save(self, obj: KnowledgeObject) -> KnowledgeObject:
        """Save a knowledge object. Creates a new KnowledgeFact row."""
        existing = KnowledgeFact.query.filter_by(
            fact_key=obj.key, domain=obj.namespace
        ).order_by(KnowledgeFact.version.desc()).first()

        version = (existing.version + 1) if existing else 1
        now = datetime.now(timezone.utc)

        if existing and version > 1:
            existing.superseded_at = now

        fact = KnowledgeFact(
            fact_key=obj.key,
            version=version,
            domain=obj.namespace,
            category=obj.type,
            value=json.dumps(obj.payload),
            value_type="json",
            confidence=1.0,
            evidence=obj.metadata.get("evidence", ""),
            source=obj.metadata.get("source", "manual"),
            created_by=obj.created_by,
            created_at=now,
        )
        import hashlib
        fact.checksum = hashlib.sha256(
            f"{obj.namespace}:{obj.key}:{json.dumps(obj.payload)}:v{version}".encode()
        ).hexdigest()
        db.session.add(fact)
        db.session.commit()

        return KnowledgeObject(
            object_id=f"{obj.key}:v{version}",
            type=obj.type,
            namespace=obj.namespace,
            key=obj.key,
            version=version,
            payload=obj.payload,
            metadata=obj.metadata,
            status=KnowledgeObjectStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
            created_by=obj.created_by,
            description=obj.description,
        )

    def get(self, object_id: str, version: Optional[int] = None) -> Optional[KnowledgeObject]:
        """Get a knowledge object by ID (fact_key:version format)."""
        parts = object_id.rsplit(":v", 1)
        fact_key = parts[0]
        ver = int(parts[1]) if len(parts) > 1 and version is None else version

        q = KnowledgeFact.query.filter_by(fact_key=fact_key)
        if ver is not None:
            q = q.filter_by(version=ver)
        else:
            q = q.order_by(KnowledgeFact.version.desc())
        fact = q.first()
        if not fact:
            return None
        return self._fact_to_object(fact)

    def get_by_key(self, namespace: str, key: str, version: Optional[int] = None) -> Optional[KnowledgeObject]:
        """Get a knowledge object by namespace + key."""
        q = KnowledgeFact.query.filter_by(fact_key=key, domain=namespace)
        if version is not None:
            q = q.filter_by(version=version)
        else:
            q = q.order_by(KnowledgeFact.version.desc())
        fact = q.first()
        if not fact:
            return None
        return self._fact_to_object(fact)

    def get_history(self, object_id: str) -> List[KnowledgeObject]:
        """Get all versions of a knowledge object."""
        fact_key = object_id.rsplit(":v", 1)[0]
        facts = KnowledgeFact.query.filter_by(fact_key=fact_key)\
            .order_by(KnowledgeFact.version.asc()).all()
        return [self._fact_to_object(f) for f in facts]

    def search(self, query: SearchQuery) -> SearchResult:
        """Search knowledge objects with namespace filtering and pagination."""
        q = KnowledgeFact.query
        if query.namespace:
            q = q.filter_by(domain=query.namespace)

        # Get latest version for each fact_key
        subq = db.session.query(
            KnowledgeFact.fact_key,
            db.func.max(KnowledgeFact.version).label("max_version")
        ).group_by(KnowledgeFact.fact_key).subquery()

        q = q.join(subq, db.and_(
            KnowledgeFact.fact_key == subq.c.fact_key,
            KnowledgeFact.version == subq.c.max_version,
        ))

        total = q.count()
        facts = q.order_by(KnowledgeFact.created_at.desc())\
            .offset(query.offset).limit(query.limit).all()

        # Filter results through SearchQuery.matches()
        objects = [self._fact_to_object(f) for f in facts]
        filtered = [o for o in objects if query.matches(o)]

        return SearchResult(
            items=filtered[:query.limit],
            total=len(filtered),
            limit=query.limit,
            offset=query.offset,
            has_more=(query.offset + query.limit) < total,
        )

    def delete(self, object_id: str) -> bool:
        """Soft-delete (archive) a knowledge object by superseding all versions."""
        fact_key = object_id.rsplit(":v", 1)[0]
        now = datetime.now(timezone.utc)
        count = KnowledgeFact.query.filter_by(
            fact_key=fact_key, superseded_at=None
        ).update({"superseded_at": now})
        db.session.commit()
        return count > 0

    def count(self, namespace: Optional[str] = None,
              object_type: Optional[str] = None) -> int:
        """Count objects matching criteria."""
        q = KnowledgeFact.query
        if namespace:
            q = q.filter_by(domain=namespace)
        if object_type:
            q = q.filter_by(category=object_type)
        return q.count()

    # ---- Helpers -----------------------------------------------------------

    def _fact_to_object(self, fact: KnowledgeFact) -> KnowledgeObject:
        """Convert a KnowledgeFact SQLAlchemy model to a KnowledgeObject dataclass."""
        try:
            payload = json.loads(fact.value) if fact.value else {}
        except (json.JSONDecodeError, TypeError):
            payload = {"text": fact.value}
        return KnowledgeObject(
            object_id=f"{fact.fact_key}:v{fact.version}",
            type=fact.category or "fact",
            namespace=fact.domain or "default",
            key=fact.fact_key,
            version=fact.version,
            payload=payload,
            metadata={
                "evidence": fact.evidence or "",
                "source": fact.source or "manual",
                "confidence": fact.confidence or 1.0,
            },
            status=KnowledgeObjectStatus.ACTIVE.value if fact.superseded_at is None
                   else KnowledgeObjectStatus.ARCHIVED.value,
            created_at=fact.created_at,
            updated_at=fact.created_at,
            created_by=fact.created_by or "system",
            description=f"{fact.domain}/{fact.category}: {fact.fact_key}",
        )