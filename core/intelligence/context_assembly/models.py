"""SHUNYA Context Assembly Engine — Data Models.

Defines the core data structures for the Context Assembly Engine: context
queries, results, the unified Context object, relevance scoring, and
recency-filtered data bundles.

All models follow the canonical contracts defined in:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §3 (Engine Contract)
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §6 (Context Assembly Engine)
    - docs/canon/07_ai_canon.md §6-7 (Memory & Knowledge Engines)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ── Timestamp helper ───────────────────────────────────────────────────────────


def _now_iso() -> str:
    """Return the current UTC timestamp as ISO-8601 with 'Z' suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── Relevance Score ────────────────────────────────────────────────────────────


@dataclass
class RelevanceScore:
    """A scored relevance assessment for a single context item.

    Each context item retrieved from a data store (Memory, Knowledge, Timeline,
    Evidence, Relationships) is scored for relevance to the input query.

    Attributes:
        item_id: The identifier of the item being scored.
        item_type: The type of item (e.g., 'memory', 'knowledge', 'event').
        score: Relevance score [0, 1], where 1 is most relevant.
        reasoning: Brief explanation of why this score was assigned.
        recency: Recency factor [0, 1], where 1 is most recent.
    """

    item_id: str = ""
    """The identifier of the item being scored."""

    item_type: str = ""
    """The type of item (e.g., 'memory', 'knowledge', 'event', 'evidence')."""

    score: float = 0.0
    """Relevance score on [0, 1], where 1.0 is most relevant."""

    reasoning: str = ""
    """Brief explanation of why this score was assigned."""

    recency: float = 0.0
    """Recency factor on [0, 1], where 1.0 is most recent."""


# ── Data Store Results ─────────────────────────────────────────────────────────


@dataclass
class MemoryQueryResult:
    """Result of querying the Memory Engine for related records.

    Attributes:
        records: List of memory records matching the query.
        total_count: Total number of matching records (before pagination).
        relevancy_scores: Per-record relevance scores.
        query_time_ms: Time taken to execute the query, in milliseconds.
    """

    records: list[dict[str, Any]] = field(default_factory=list)
    """List of memory records matching the query."""

    total_count: int = 0
    """Total number of matching records (before pagination)."""

    relevancy_scores: list[RelevanceScore] = field(default_factory=list)
    """Per-record relevance scores, same order as ``records``."""

    query_time_ms: float = 0.0
    """Time taken to execute the query, in milliseconds."""


@dataclass
class KnowledgeQueryResult:
    """Result of querying the Knowledge Engine for facts.

    Attributes:
        facts: List of knowledge facts matching the query.
        total_count: Total number of matching facts (before pagination).
        relevancy_scores: Per-fact relevance scores.
        query_time_ms: Time taken to execute the query, in milliseconds.
    """

    facts: list[dict[str, Any]] = field(default_factory=list)
    """List of knowledge facts matching the query."""

    total_count: int = 0
    """Total number of matching facts (before pagination)."""

    relevancy_scores: list[RelevanceScore] = field(default_factory=list)
    """Per-fact relevance scores, same order as ``facts``."""

    query_time_ms: float = 0.0
    """Time taken to execute the query, in milliseconds."""


@dataclass
class TimelineQueryResult:
    """Result of querying the Timeline Engine for recent events.

    Attributes:
        events: List of timeline events matching the query.
        total_count: Total number of matching events (before pagination).
        from_time: ISO-8601 start of the query window.
        to_time: ISO-8601 end of the query window.
        query_time_ms: Time taken to execute the query, in milliseconds.
    """

    events: list[dict[str, Any]] = field(default_factory=list)
    """List of timeline events matching the query."""

    total_count: int = 0
    """Total number of matching events (before pagination)."""

    from_time: str = ""
    """ISO-8601 start of the query window."""

    to_time: str = ""
    """ISO-8601 end of the query window."""

    query_time_ms: float = 0.0
    """Time taken to execute the query, in milliseconds."""


@dataclass
class EvidenceQueryResult:
    """Result of querying the Evidence Engine for supporting data.

    Attributes:
        evidence: List of evidence records matching the query.
        total_count: Total number of matching records (before pagination).
        relevancy_scores: Per-record relevance scores.
        query_time_ms: Time taken to execute the query, in milliseconds.
    """

    evidence: list[dict[str, Any]] = field(default_factory=list)
    """List of evidence records matching the query."""

    total_count: int = 0
    """Total number of matching records (before pagination)."""

    relevancy_scores: list[RelevanceScore] = field(default_factory=list)
    """Per-record relevance scores, same order as ``evidence``."""

    query_time_ms: float = 0.0
    """Time taken to execute the query, in milliseconds."""


@dataclass
class RelationshipQueryResult:
    """Result of querying the Relationship Engine for graph context.

    Attributes:
        relationships: List of relationship records matching the query.
        total_count: Total number of matching relationships (before pagination).
        relevancy_scores: Per-relationship relevance scores.
        query_time_ms: Time taken to execute the query, in milliseconds.
    """

    relationships: list[dict[str, Any]] = field(default_factory=list)
    """List of relationship records matching the query."""

    total_count: int = 0
    """Total number of matching relationships (before pagination)."""

    relevancy_scores: list[RelevanceScore] = field(default_factory=list)
    """Per-relationship relevance scores, same order as ``relationships``."""

    query_time_ms: float = 0.0
    """Time taken to execute the query, in milliseconds."""


# ── Unified Context ────────────────────────────────────────────────────────────


@dataclass
class UnifiedContext:
    """The unified context object assembled by the Context Assembly Engine.

    A single Context object that merges results from all five data stores:
    Memory, Knowledge, Timeline, Evidence, and Relationships. Each store's
    results are independently accessible, and the merged context provides
    a consolidated view for downstream reasoning.

    Attributes:
        memory: Query results from the Memory Engine.
        knowledge: Query results from the Knowledge Engine.
        timeline: Query results from the Timeline Engine.
        evidence: Query results from the Evidence Engine.
        relationships: Query results from the Relationship Engine.
        merged_summary: A human-readable summary of the assembled context.
        total_items: Total number of individual items across all stores.
        average_relevance: Average relevance score across all scored items.
        assembly_time_ms: Time taken to assemble the full context, in ms.
        context_id: Unique identifier for this context assembly.
        trace_id: Correlation ID linking this context to the original input.
        created_at: ISO-8601 timestamp of when the context was assembled.
    """

    memory: MemoryQueryResult = field(default_factory=MemoryQueryResult)
    """Query results from the Memory Engine."""

    knowledge: KnowledgeQueryResult = field(default_factory=KnowledgeQueryResult)
    """Query results from the Knowledge Engine."""

    timeline: TimelineQueryResult = field(default_factory=TimelineQueryResult)
    """Query results from the Timeline Engine."""

    evidence: EvidenceQueryResult = field(default_factory=EvidenceQueryResult)
    """Query results from the Evidence Engine."""

    relationships: RelationshipQueryResult = field(
        default_factory=RelationshipQueryResult
    )
    """Query results from the Relationship Engine."""

    merged_summary: str = ""
    """A human-readable summary of the assembled context."""

    total_items: int = 0
    """Total number of individual items across all stores."""

    average_relevance: float = 0.0
    """Average relevance score across all scored items [0, 1]."""

    assembly_time_ms: float = 0.0
    """Time taken to assemble the full context, in milliseconds."""

    context_id: str = ""
    """Unique identifier for this context assembly."""

    trace_id: str = ""
    """Correlation ID linking this context to the original input."""

    created_at: str = field(default_factory=_now_iso)
    """ISO-8601 timestamp of when the context was assembled."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the unified context to a plain dictionary.

        Returns:
            A JSON-serializable dict representation.
        """
        return {
            "context_id": self.context_id,
            "trace_id": self.trace_id,
            "created_at": self.created_at,
            "total_items": self.total_items,
            "average_relevance": self.average_relevance,
            "assembly_time_ms": self.assembly_time_ms,
            "merged_summary": self.merged_summary,
            "memory": {
                "total_count": self.memory.total_count,
                "records": list(self.memory.records),
                "query_time_ms": self.memory.query_time_ms,
            },
            "knowledge": {
                "total_count": self.knowledge.total_count,
                "facts": list(self.knowledge.facts),
                "query_time_ms": self.knowledge.query_time_ms,
            },
            "timeline": {
                "total_count": self.timeline.total_count,
                "events": list(self.timeline.events),
                "from_time": self.timeline.from_time,
                "to_time": self.timeline.to_time,
                "query_time_ms": self.timeline.query_time_ms,
            },
            "evidence": {
                "total_count": self.evidence.total_count,
                "evidence": list(self.evidence.evidence),
                "query_time_ms": self.evidence.query_time_ms,
            },
            "relationships": {
                "total_count": self.relationships.total_count,
                "relationships": list(self.relationships.relationships),
                "query_time_ms": self.relationships.query_time_ms,
            },
        }


# ── Context Assembly Input/Output ──────────────────────────────────────────────


@dataclass
class ContextAssemblyInput:
    """Input to the Context Assembly Engine.

    Contains the observation and related references needed to query all
    data stores for relevant context.

    Attributes:
        observation: The observation dict produced by the Perception Engine.
        object_ids: List of object IDs whose context should be assembled.
        query_text: Optional free-text query to guide context retrieval.
        trace_id: Correlation ID for tracing through the pipeline.
        max_items_per_store: Maximum items to retrieve per data store.
        recency_window_hours: How far back (in hours) to query for recent
            events. Defaults to 24 hours.
        confidence_threshold: Minimum confidence before escalation.
    """

    observation: dict[str, Any] = field(default_factory=dict)
    """The observation dict produced by the Perception Engine."""

    object_ids: list[str] = field(default_factory=list)
    """List of object IDs whose context should be assembled."""

    query_text: str = ""
    """Optional free-text query to guide context retrieval."""

    trace_id: str = ""
    """Correlation ID for tracing through the pipeline."""

    max_items_per_store: int = 50
    """Maximum items to retrieve per data store. Defaults to 50."""

    recency_window_hours: int = 24
    """How far back (in hours) to query for recent events. Defaults to 24."""

    confidence_threshold: float = 0.75
    """Minimum confidence before escalation triggers.

    Defaults to 0.75 per the Intelligence Runtime Canon (Context Assembly
    can tolerate some uncertainty).
    """


@dataclass
class ContextAssemblyOutput:
    """Output from the Context Assembly Engine.

    Wraps the assembled UnifiedContext along with the standard engine
    output envelope (confidence, determinism, timing).

    Attributes:
        context: The assembled UnifiedContext.
        confidence: Computed confidence score for the assembled context [0, 1].
        confidence_factors: Breakdown of confidence computation.
        deterministic: True if computed locally without AI.
        trace_id: Correlation ID matching the input.
        escalation_used: True if an AI provider was invoked.
        processing_time_ms: Wall-clock processing time in milliseconds.
    """

    context: UnifiedContext = field(default_factory=UnifiedContext)
    """The assembled UnifiedContext."""

    confidence: float = 0.0
    """Computed confidence score for the assembled context [0, 1]."""

    confidence_factors: dict[str, float] = field(default_factory=dict)
    """Breakdown of confidence computation."""

    deterministic: bool = True
    """True if computed locally without AI assistance."""

    trace_id: str = ""
    """Correlation ID matching the input."""

    escalation_used: bool = False
    """True if an AI provider was invoked during assembly."""

    processing_time_ms: float = 0.0
    """Wall-clock processing time in milliseconds."""