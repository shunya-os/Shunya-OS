"""Universal Knowledge Intelligence — UCP-04.

The canonical capability for understanding how humans and organizations
acquire, organize, validate, connect, reason about and continuously
evolve knowledge.

Knowledge Intelligence is universal. It does not model a wiki, document
storage, or note taking. Knowledge are Living Knowledge Objects connected
to Reality.

Composes exclusively from frozen SHUNYA runtimes.
No Knowledge Runtime. No Wiki Runtime. No Note Runtime.
"""

from core.knowledge_intelligence.engine import KnowledgeIntelligenceEngine
from core.knowledge_intelligence.models import (
    ConfidenceLevel,
    Contradiction,
    GapSeverity,
    Knowledge,
    KnowledgeGap,
    KnowledgeGraph,
    KnowledgeLink,
    KnowledgeProfile,
    KnowledgeRecommendation,
    KnowledgeRelationship,
    KnowledgeSource,
    KnowledgeType,
    SearchResult,
    SourceType,
)
from core.knowledge_intelligence.runtime import KnowledgeIntelligenceRuntime

__all__ = [
    "KnowledgeIntelligenceRuntime",
    "KnowledgeIntelligenceEngine",
    "Knowledge",
    "KnowledgeProfile",
    "KnowledgeGraph",
    "KnowledgeLink",
    "KnowledgeSource",
    "KnowledgeGap",
    "KnowledgeRecommendation",
    "Contradiction",
    "SearchResult",
    "KnowledgeType",
    "ConfidenceLevel",
    "KnowledgeRelationship",
    "SourceType",
    "GapSeverity",
]