"""
SHUNYA — Canonical Knowledge Interface (FDA3).

The canonical governance/retrieval interface for authoritative knowledge.

Knowledge is NOT memory:
- Knowledge = authoritative business facts (versioned, immutable, source-verified)
- Memory = contextual information, observations, preferences, decision history
- Learning weights = model state (not knowledge, not memory)
- Execution evidence = verified outcomes (not knowledge, not memory)

Architecture:
  Canonical KnowledgeInterface (governance + retrieval contract)
  └── KnowledgeStore (app.shunya.knowledge_store) — persistent implementation
  └── KnowledgeIntelligenceRuntime (core.knowledge_intelligence) — in-memory/retrieval

Future FDA7 will integrate document ingestion through this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── Knowledge Type ────────────────────────────────────────────────────

class KnowledgeCategory(str):
    """FDA3 knowledge classification — distinct from memory types."""
    FACT = "fact"                    # Verified business fact
    RULE = "rule"                    # Business rule / policy
    REFERENCE = "reference"          # Reference data (tables, codes)
    DOCUMENT = "document"            # Document-derived knowledge
    RELATIONSHIP = "relationship"    # Relationship metadata
    CONTEXT = "context"              # Situational context augmenting knowledge

    @classmethod
    def values(cls) -> list[str]:
        return [v for k, v in vars(cls).items() if not k.startswith("_") and isinstance(v, str)]


# ── Knowledge Reference ───────────────────────────────────────────────

@dataclass
class KnowledgeReference:
    """A reference to a specific knowledge item for provenance tracking.

    Used by memory to reference knowledge facts, NOT to store them.
    """
    knowledge_id: str = ""
    source: str = ""                 # "knowledge_store", "knowledge_intelligence", etc.
    category: str = KnowledgeCategory.FACT
    retrieved_at: str = field(default_factory=_now_iso)
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "knowledge_id": self.knowledge_id,
            "source": self.source,
            "category": self.category,
            "retrieved_at": self.retrieved_at,
            "confidence": self.confidence,
        }


# ── Canonical Knowledge Interface ─────────────────────────────────────

class KnowledgeInterface(ABC):
    """FDA3 canonical governance/retrieval contract for authoritative knowledge.

    Every knowledge store must implement this interface.

    Consumers must NOT:
    - Bypass this interface to access knowledge storage directly
    - Treat knowledge as memory (contextual)
    - Treat memory as knowledge (authoritative)
    """

    @abstractmethod
    def get(self, knowledge_id: str, tenant_id: Optional[str] = None) -> Optional[dict]:
        """Retrieve a knowledge item by ID.

        Returns None if not found or tenant-mismatched.
        """
        ...

    @abstractmethod
    def search(self, query: str, category: Optional[str] = None,
               tenant_id: Optional[str] = None, limit: int = 20) -> list[dict]:
        """Search for knowledge items matching query.

        Results are tenant-scoped and category-filtered.
        """
        ...

    @abstractmethod
    def get_canonical_interface(self) -> str:
        """Return the canonical interface identifier."""
        return "KnowledgeInterface"

    @abstractmethod
    def health_check(self) -> dict:
        """Return health status of this knowledge store."""
        ...


class KnowledgeGovernance:
    """FDA3 governance rules for knowledge vs memory boundary.

    Machine-enforced rules that prevent:
    - Knowledge being treated as memory
    - Memory being treated as knowledge
    - Direct table access bypassing the interface
    """

    @staticmethod
    def is_valid_knowledge_category(category: str) -> bool:
        return category in KnowledgeCategory.values()

    @staticmethod
    def assert_not_memory_promotion(classification: str, target: str) -> None:
        """Knowledge must not be silently promoted to a different truth level."""
        forbidden = {
            ("observation", "fact"),
            ("memory", "fact"),
            ("inference", "fact"),
        }
        if (classification, target) in forbidden:
            raise ValueError(
                f"Forbidden knowledge promotion: {classification} → {target}. "
                "Knowledge is authoritative truth, not contextual memory."
            )