"""SHUNYA Context Assembly Engine.

The Context Assembly Engine queries all five Universal Runtime data stores
(Memory, Knowledge, Timeline, Evidence, Relationships) and merges the
results into a single, unified Context object for downstream reasoning.

Exports:
    ContextAssemblyEngine: The main engine class.
    IntelligenceEngine: Abstract base class for all engines.
    UnifiedContext: The assembled context object.
    ContextAssemblyInput: Input to the assembly process.
    ContextAssemblyOutput: Output from the assembly process.
    MemoryQueryResult: Result of querying the Memory Engine.
    KnowledgeQueryResult: Result of querying the Knowledge Engine.
    TimelineQueryResult: Result of querying the Timeline Engine.
    EvidenceQueryResult: Result of querying the Evidence Engine.
    RelationshipQueryResult: Result of querying the Relationship Engine.
    RelevanceScore: A scored relevance assessment.
    MemoryStoreAdapter: Adapter for the Memory Engine.
    KnowledgeStoreAdapter: Adapter for the Knowledge Engine.
    TimelineStoreAdapter: Adapter for the Timeline Engine.
    EvidenceStoreAdapter: Adapter for the Evidence Engine.
    RelationshipStoreAdapter: Adapter for the Relationship Engine.
"""

from __future__ import annotations

from core.intelligence.context_assembly.engine import (
    ContextAssemblyEngine,
    EvidenceStoreAdapter,
    InMemoryEvidenceAdapter,
    InMemoryKnowledgeAdapter,
    InMemoryMemoryAdapter,
    InMemoryRelationshipAdapter,
    InMemoryTimelineAdapter,
    IntelligenceEngine,
    KnowledgeStoreAdapter,
    MemoryStoreAdapter,
    RelationshipStoreAdapter,
    TimelineStoreAdapter,
)
from core.intelligence.context_assembly.models import (
    ContextAssemblyInput,
    ContextAssemblyOutput,
    EvidenceQueryResult,
    KnowledgeQueryResult,
    MemoryQueryResult,
    RelationshipQueryResult,
    RelevanceScore,
    TimelineQueryResult,
    UnifiedContext,
)

__all__ = [
    "ContextAssemblyEngine",
    "ContextAssemblyInput",
    "ContextAssemblyOutput",
    "EvidenceQueryResult",
    "EvidenceStoreAdapter",
    "InMemoryEvidenceAdapter",
    "InMemoryKnowledgeAdapter",
    "InMemoryMemoryAdapter",
    "InMemoryRelationshipAdapter",
    "InMemoryTimelineAdapter",
    "IntelligenceEngine",
    "KnowledgeQueryResult",
    "KnowledgeStoreAdapter",
    "MemoryQueryResult",
    "MemoryStoreAdapter",
    "RelationshipQueryResult",
    "RelationshipStoreAdapter",
    "RelevanceScore",
    "TimelineQueryResult",
    "TimelineStoreAdapter",
    "UnifiedContext",
]