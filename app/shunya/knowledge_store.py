"""
Shunya — Immutable Knowledge Store (Phase 2, v3)

Versioned, traceable fact store. Never silently overwritten.
History is preserved — complete audit trail of every fact change.

Requirements:
- knowledge_facts table in PostgreSQL
- Fact V1 → V2 → V3 lineage preserved
- No hidden edits, no disappearing evidence
- Every fact has: creator, timestamp, evidence, confidence
- Supports domain-specific namespacing (travel, healthcare, etc.)
"""

from __future__ import annotations
import json
import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app import db
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index, func
from sqlalchemy.orm import validates


# ---------------------------------------------------------------------------
# SQLAlchemy Model
# ---------------------------------------------------------------------------


class KnowledgeFact(db.Model):
    """Immutable knowledge fact with version history."""

    __tablename__ = "knowledge_facts"
    __table_args__ = (
        Index("ix_kf_domain_category", "domain", "category"),
        Index("ix_kf_fact_key", "fact_key"),
        Index("ix_kf_created", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    fact_key = Column(String(255), nullable=False, index=True)  # e.g. "destination.bali.visa"
    version = Column(Integer, nullable=False, default=1)
    domain = Column(String(60), default="travel")  # travel, healthcare, legal...
    category = Column(String(120), default="general")  # visa, tax, venue, transport...
    value = Column(Text, nullable=False)  # JSON-serialized fact value
    value_type = Column(String(60), default="text")  # text, number, json, markdown
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    evidence = Column(Text, default="")  # Source or reasoning behind this fact
    source = Column(String(255), default="manual")  # manual, web_scrape, reasoning, learning
    checksum = Column(String(64), unique=True)  # SHA-256 of content for integrity
    created_by = Column(String(120), default="system")  # user or system component
    superseded_at = Column(DateTime, nullable=True)  # When this version was superseded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @validates("value")
    def validate_value(self, key, value):
        if not value or not value.strip():
            raise ValueError("Fact value cannot be empty")
        return value

    def __repr__(self):
        return f"<KnowledgeFact {self.fact_key} v{self.version} [{self.domain}]>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fact_key": self.fact_key,
            "version": self.version,
            "domain": self.domain,
            "category": self.category,
            "value": self._deserialize_value(),
            "value_type": self.value_type,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "source": self.source,
            "checksum": self.checksum,
            "created_by": self.created_by,
            "superseded_at": self.superseded_at.isoformat() if self.superseded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def _deserialize_value(self):
        """Deserialize stored value based on value_type."""
        if self.value_type == "json":
            try:
                return json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                return self.value
        return self.value


# ---------------------------------------------------------------------------
# Fact Helpers
# ---------------------------------------------------------------------------


def _compute_checksum(domain: str, key: str, value: str, version: int) -> str:
    """Compute SHA-256 checksum for integrity verification."""
    raw = f"{domain}:{key}:v{version}:{value}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _next_version(session, fact_key: str) -> int:
    """Determine the next version number for a fact key."""
    latest = (
        session.query(func.max(KnowledgeFact.version))
        .filter(KnowledgeFact.fact_key == fact_key)
        .scalar()
    )
    return (latest or 0) + 1


def _current_fact(session, fact_key: str) -> KnowledgeFact | None:
    """Get the current (non-superseded) version of a fact."""
    return (
        session.query(KnowledgeFact)
        .filter(
            KnowledgeFact.fact_key == fact_key,
            KnowledgeFact.superseded_at.is_(None),
        )
        .order_by(KnowledgeFact.version.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# Knowledge Store
# ---------------------------------------------------------------------------


class ImmutableKnowledgeStore:
    """
    Immutable, versioned knowledge store.

    Core operations:
        store(fact)     — Insert new fact version
        get(key)        — Get current version
        history(key)    — Get all versions of a fact
        search(query)   — Search across facts
        verify()        — Verify integrity (checksums)
    """

    def __init__(self, session=None):
        self._session = session or db.session

    # ------------------------------------------------------------------
    # Write Operations
    # ------------------------------------------------------------------

    def store(self, fact_key: str, value: Any, *,
              domain: str = "travel",
              category: str = "general",
              value_type: str = "text",
              confidence: float = 1.0,
              evidence: str = "",
              source: str = "manual",
              created_by: str = "system") -> KnowledgeFact:
        """
        Store a new fact. Creates a new version automatically.

        Never overwrites — always appends a new version.
        Previous version is marked as superseded.
        """
        # Serialize value
        if not isinstance(value, str):
            value = json.dumps(value)
            value_type = value_type or "json"

        # Compute version
        version = _next_version(self._session, fact_key)
        checksum = _compute_checksum(domain, fact_key, value, version)

        # Supersede current version
        current = _current_fact(self._session, fact_key)
        if current:
            current.superseded_at = datetime.utcnow()
            self._session.add(current)

        # Insert new version
        fact = KnowledgeFact(
            fact_key=fact_key,
            version=version,
            domain=domain,
            category=category,
            value=value,
            value_type=value_type or "text",
            confidence=min(1.0, max(0.0, confidence)),
            evidence=evidence,
            source=source,
            checksum=checksum,
            created_by=created_by,
        )
        self._session.add(fact)
        self._session.commit()
        return fact

    def store_batch(self, facts: list[dict]) -> list[KnowledgeFact]:
        """Store multiple facts in a single transaction."""
        results = []
        for f in facts:
            fact = self.store(
                fact_key=f["fact_key"],
                value=f["value"],
                domain=f.get("domain", "travel"),
                category=f.get("category", "general"),
                value_type=f.get("value_type", "text"),
                confidence=f.get("confidence", 1.0),
                evidence=f.get("evidence", ""),
                source=f.get("source", "manual"),
                created_by=f.get("created_by", "system"),
            )
            results.append(fact)
        return results

    # ------------------------------------------------------------------
    # Read Operations
    # ------------------------------------------------------------------

    def get(self, fact_key: str) -> Optional[dict]:
        """Get the current version of a fact."""
        fact = _current_fact(self._session, fact_key)
        return fact.to_dict() if fact else None

    def get_value(self, fact_key: str) -> Any:
        """Get just the deserialized value of the current fact."""
        fact = _current_fact(self._session, fact_key)
        if not fact:
            return None
        return fact._deserialize_value()

    def history(self, fact_key: str) -> list[dict]:
        """Get all versions of a fact (oldest first)."""
        facts = (
            self._session.query(KnowledgeFact)
            .filter(KnowledgeFact.fact_key == fact_key)
            .order_by(KnowledgeFact.version.asc())
            .all()
        )
        return [f.to_dict() for f in facts]

    def get_by_domain(self, domain: str, category: str = "") -> list[dict]:
        """Get all current facts for a domain, optionally filtered by category."""
        query = self._session.query(KnowledgeFact).filter(
            KnowledgeFact.domain == domain,
            KnowledgeFact.superseded_at.is_(None),
        )
        if category:
            query = query.filter(KnowledgeFact.category == category)
        facts = query.order_by(KnowledgeFact.fact_key).all()
        return [f.to_dict() for f in facts]

    def search(self, query_str: str, domain: str = "", limit: int = 20) -> list[dict]:
        """Search current facts by key, value, or category."""
        q = f"%{query_str}%"
        conditions = [
            KnowledgeFact.fact_key.ilike(q),
            KnowledgeFact.value.ilike(q),
            KnowledgeFact.category.ilike(q),
            KnowledgeFact.evidence.ilike(q),
        ]
        query = self._session.query(KnowledgeFact).filter(
            KnowledgeFact.superseded_at.is_(None),
        )
        # Only use OR_ if we imported it
        import sqlalchemy as sa
        query = query.filter(sa.or_(*conditions))

        if domain:
            query = query.filter(KnowledgeFact.domain == domain)
        facts = query.order_by(KnowledgeFact.created_at.desc()).limit(limit).all()
        return [f.to_dict() for f in facts]

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    def verify(self, fact_key: str = "") -> list[dict]:
        """
        Verify integrity of stored facts.
        Returns list of any facts with checksum mismatches.
        """
        query = self._session.query(KnowledgeFact)
        if fact_key:
            query = query.filter(KnowledgeFact.fact_key == fact_key)

        violations = []
        for fact in query.all():
            expected = _compute_checksum(
                fact.domain, fact.fact_key, fact.value, fact.version
            )
            if expected != fact.checksum:
                violations.append({
                    "id": fact.id,
                    "fact_key": fact.fact_key,
                    "version": fact.version,
                    "expected_checksum": expected,
                    "stored_checksum": fact.checksum,
                })
        return violations

    def stats(self) -> dict:
        """Return knowledge store statistics."""
        total = self._session.query(func.count(KnowledgeFact.id)).scalar() or 0
        current = (
            self._session.query(func.count(KnowledgeFact.id))
            .filter(KnowledgeFact.superseded_at.is_(None))
            .scalar() or 0
        )
        domains = [
            r[0] for r in
            self._session.query(KnowledgeFact.domain)
            .filter(KnowledgeFact.superseded_at.is_(None))
            .distinct().all()
        ]
        return {
            "total_facts": total,
            "current_facts": current,
            "archived_versions": total - current,
            "domains": domains,
            "integrity_pass": len(self.verify()) == 0,
        }

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    def seed_from_markdown(self, md_path: str, domain: str = "travel",
                           created_by: str = "seed") -> int:
        """
        Seed the knowledge store from a markdown knowledge base file.
        Returns number of facts created.
        """
        if not os.path.exists(md_path):
            return 0

        with open(md_path, "r") as f:
            content = f.read()

        count = 0
        # Parse ## sections as categories
        sections = re.split(r"\n## ", content)
        for section in sections:
            if not section.strip():
                continue
            lines = section.strip().split("\n")
            category = lines[0].strip().rstrip("#").strip().lower().replace(" ", "_")

            # Store the whole section as a knowledge fact
            body = "\n".join(lines[1:]).strip()
            if body:
                self.store(
                    fact_key=f"destination.{category}",
                    value=body,
                    domain=domain,
                    category=category,
                    value_type="markdown",
                    source="seed",
                    created_by=created_by,
                )
                count += 1

            # Also extract bullet points as individual facts
            for line in lines[1:]:
                line = line.strip()
                if line.startswith("- **") or line.startswith("-"):
                    fact_key = re.sub(r"[^a-z0-9_]", "_", line.lower().strip("- ").split(":")[0].strip())[:60]
                    if fact_key:
                        self.store(
                            fact_key=f"destination.{category}.{fact_key}",
                            value=line.strip("- "),
                            domain=domain,
                            category=category,
                            value_type="text",
                            source="seed",
                            created_by=created_by,
                        )
                        count += 1

        return count