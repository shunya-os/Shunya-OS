"""SHUNYA Context Assembly Engine — In-Memory Implementation.

The ContextAssemblyEngine queries all five Universal Runtime data stores
(Memory, Knowledge, Timeline, Evidence, Relationships) and merges the
results into a single, unified Context object for downstream reasoning.

**Processing Pipeline:**

    Input + Observation ──► Context Assembly Engine
                               │
                               ├── 1. Query Memory for related records
                               ├── 2. Query Knowledge for facts
                               ├── 3. Query Timeline for recent events
                               ├── 4. Query Evidence for supporting data
                               ├── 5. Query Relationships for graph context
                               ├── 6. Score relevance for each item
                               ├── 7. Apply recency filtering
                               ├── 8. Merge into unified Context
                               └── 9. Return Context → Reasoning Engine

**Deterministic Work** (always local):
    - All data store queries (Memory, Knowledge, Timeline, Evidence, Relationship)
    - Context merging and deduplication
    - Relevance scoring
    - Recency filtering

**AI-Assisted Work** (via escalation):
    - Summarization of large context sets
    - Relevance ranking of unstructured data

**Data Store Adapters:**
    The engine uses adapter objects for each data store. By default, it uses
    in-memory stores that can be pre-populated. Production deployments should
    substitute these with adapters backed by persistent stores. The adapter
    interface is defined as a simple protocol — any object with the right
    method signature works.

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §3 (Engine Contract)
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §6 (Context Assembly Engine)
    - docs/canon/07_ai_canon.md §6-7 (Memory & Knowledge Engines)
"""

from __future__ import annotations

import logging
import time
from typing import Any

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
    _now_iso,
)
from core.intelligence.perception.models import (
    EngineInput,
    EngineOutput,
    EscalationResult,
)

logger = logging.getLogger(__name__)


# ── Intelligence Engine interface ──────────────────────────────────────────────


class IntelligenceEngine:
    """Abstract interface that every Intelligence Engine implements.

    All eight engines (Perception, Context Assembly, Reasoning, Planning,
    Decision, Reflection, Learning, Confidence) conform to this contract.

    Subclasses override ``process()``, ``escalate()``, ``get_capabilities()``,
    and ``health_check()``.
    """

    engine_id: str = ""
    """Unique identifier for this engine instance."""

    engine_type: str = ""
    """Canonical engine type string."""

    async def process(self, input_data: EngineInput) -> EngineOutput:
        """Process an input and return an output.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    def escalate(self, input_data: EngineInput) -> EscalationResult:
        """Bridge to external AI inference.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    def get_capabilities(self) -> list[str]:
        """Return a list of capability strings.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Subclasses must implement this method.
        """
        raise NotImplementedError


# ── Data Store Adapter Protocols ───────────────────────────────────────────────

# These are the adapter interfaces for the five data stores. Each adapter is
# a callable that takes a query context and returns a typed result.
# By default, the engine uses InMemoryStoreAdapters that are pre-populated
# with test/stub data. Production deployments should substitute real adapters.


class MemoryStoreAdapter:
    """Adapter for querying the Memory Engine.

    Override ``query()`` to substitute a real Memory Engine backing store.
    """

    def query(
        self,
        object_ids: list[str],
        query_text: str,
        max_items: int,
    ) -> MemoryQueryResult:
        """Query Memory for records related to the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            query_text: Optional free-text query.
            max_items: Maximum records to return.

        Returns:
            A ``MemoryQueryResult`` with matching records.
        """
        raise NotImplementedError


class KnowledgeStoreAdapter:
    """Adapter for querying the Knowledge Engine.

    Override ``query()`` to substitute a real Knowledge Engine backing store.
    """

    def query(
        self,
        object_ids: list[str],
        query_text: str,
        max_items: int,
    ) -> KnowledgeQueryResult:
        """Query Knowledge for facts related to the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            query_text: Optional free-text query.
            max_items: Maximum facts to return.

        Returns:
            A ``KnowledgeQueryResult`` with matching facts.
        """
        raise NotImplementedError


class TimelineStoreAdapter:
    """Adapter for querying the Timeline Engine.

    Override ``query()`` to substitute a real Timeline Engine backing store.
    """

    def query(
        self,
        object_ids: list[str],
        recency_window_hours: int,
        max_items: int,
    ) -> TimelineQueryResult:
        """Query Timeline for recent events related to the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            recency_window_hours: How far back in hours to query.
            max_items: Maximum events to return.

        Returns:
            A ``TimelineQueryResult`` with matching events.
        """
        raise NotImplementedError


class EvidenceStoreAdapter:
    """Adapter for querying the Evidence Engine.

    Override ``query()`` to substitute a real Evidence Engine backing store.
    """

    def query(
        self,
        object_ids: list[str],
        query_text: str,
        max_items: int,
    ) -> EvidenceQueryResult:
        """Query Evidence for supporting data related to the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            query_text: Optional free-text query.
            max_items: Maximum evidence records to return.

        Returns:
            An ``EvidenceQueryResult`` with matching evidence records.
        """
        raise NotImplementedError


class RelationshipStoreAdapter:
    """Adapter for querying the Relationship Engine.

    Override ``query()`` to substitute a real Relationship Engine backing store.
    """

    def query(
        self,
        object_ids: list[str],
        query_text: str,
        max_items: int,
    ) -> RelationshipQueryResult:
        """Query Relationships for graph context related to the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            query_text: Optional free-text query.
            max_items: Maximum relationships to return.

        Returns:
            A ``RelationshipQueryResult`` with matching relationships.
        """
        raise NotImplementedError


# ── In-Memory Store Adapters ───────────────────────────────────────────────────


class InMemoryMemoryAdapter(MemoryStoreAdapter):
    """Default in-memory Memory Engine adapter.

    Stores records in a dict and indexes by object_id. Suitable for
    prototyping and testing.
    """

    def __init__(self) -> None:
        self._records: dict[str, list[dict[str, Any]]] = {}

    def add_record(
        self, object_id: str, record: dict[str, Any]
    ) -> None:
        """Add a memory record for an object.

        Args:
            object_id: The object ID to associate with.
            record: The memory record data.
        """
        self._records.setdefault(object_id, []).append(record)

    def query(
        self,
        object_ids: list[str],
        query_text: str,
        max_items: int,
    ) -> MemoryQueryResult:
        """Query in-memory store for records matching the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            query_text: Optional free-text query (not used in simple impl).
            max_items: Maximum records to return.

        Returns:
            A ``MemoryQueryResult`` with matching records.
        """
        start = time.monotonic()
        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        for oid in object_ids:
            for rec in self._records.get(oid, []):
                rid = rec.get("id", id(rec))
                if rid not in seen:
                    seen.add(rid)
                    results.append(rec)
                    if len(results) >= max_items:
                        break
            if len(results) >= max_items:
                break

        total = len(results)
        elapsed = (time.monotonic() - start) * 1000.0

        return MemoryQueryResult(
            records=results,
            total_count=total,
            query_time_ms=round(elapsed, 3),
        )


class InMemoryKnowledgeAdapter(KnowledgeStoreAdapter):
    """Default in-memory Knowledge Engine adapter.

    Stores facts in a dict and indexes by object_id. Suitable for
    prototyping and testing.
    """

    def __init__(self) -> None:
        self._facts: dict[str, list[dict[str, Any]]] = {}

    def add_fact(self, object_id: str, fact: dict[str, Any]) -> None:
        """Add a knowledge fact for an object.

        Args:
            object_id: The object ID to associate with.
            fact: The fact data.
        """
        self._facts.setdefault(object_id, []).append(fact)

    def query(
        self,
        object_ids: list[str],
        query_text: str,
        max_items: int,
    ) -> KnowledgeQueryResult:
        """Query in-memory store for facts matching the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            query_text: Optional free-text query (not used in simple impl).
            max_items: Maximum facts to return.

        Returns:
            A ``KnowledgeQueryResult`` with matching facts.
        """
        start = time.monotonic()
        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        for oid in object_ids:
            for fact in self._facts.get(oid, []):
                fid = fact.get("id", id(fact))
                if fid not in seen:
                    seen.add(fid)
                    results.append(fact)
                    if len(results) >= max_items:
                        break
            if len(results) >= max_items:
                break

        total = len(results)
        elapsed = (time.monotonic() - start) * 1000.0

        return KnowledgeQueryResult(
            facts=results,
            total_count=total,
            query_time_ms=round(elapsed, 3),
        )


class InMemoryTimelineAdapter(TimelineStoreAdapter):
    """Default in-memory Timeline Engine adapter.

    Stores events in a list and indexes by object_id. Suitable for
    prototyping and testing.
    """

    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}

    def add_event(self, object_id: str, event: dict[str, Any]) -> None:
        """Add a timeline event for an object.

        Args:
            object_id: The object ID to associate with.
            event: The event data (should include 'timestamp').
        """
        self._events.setdefault(object_id, []).append(event)

    def query(
        self,
        object_ids: list[str],
        recency_window_hours: int,
        max_items: int,
    ) -> TimelineQueryResult:
        """Query in-memory store for events matching the given object IDs.

        Filters by recency window.

        Args:
            object_ids: Object IDs to search for.
            recency_window_hours: How far back in hours to query.
            max_items: Maximum events to return.

        Returns:
            A ``TimelineQueryResult`` with matching events.
        """
        start = time.monotonic()
        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(hours=recency_window_hours)

        for oid in object_ids:
            for ev in self._events.get(oid, []):
                eid = ev.get("event_id", ev.get("id", id(ev)))
                if eid in seen:
                    continue

                # Check recency
                ts = ev.get("timestamp", "")
                try:
                    event_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if event_time < cutoff:
                        continue
                except (ValueError, TypeError):
                    # If no valid timestamp, include it
                    pass

                seen.add(eid)
                results.append(ev)
                if len(results) >= max_items:
                    break
            if len(results) >= max_items:
                break

        total = len(results)
        elapsed = (time.monotonic() - start) * 1000.0

        now = _now_iso()
        return TimelineQueryResult(
            events=results,
            total_count=total,
            from_time=cutoff.isoformat().replace("+00:00", "Z"),
            to_time=now,
            query_time_ms=round(elapsed, 3),
        )


class InMemoryEvidenceAdapter(EvidenceStoreAdapter):
    """Default in-memory Evidence Engine adapter.

    Stores evidence records in a dict and indexes by object_id. Suitable
    for prototyping and testing.
    """

    def __init__(self) -> None:
        self._evidence: dict[str, list[dict[str, Any]]] = {}

    def add_evidence(self, object_id: str, evidence: dict[str, Any]) -> None:
        """Add an evidence record for an object.

        Args:
            object_id: The object ID to associate with.
            evidence: The evidence record data.
        """
        self._evidence.setdefault(object_id, []).append(evidence)

    def query(
        self,
        object_ids: list[str],
        query_text: str,
        max_items: int,
    ) -> EvidenceQueryResult:
        """Query in-memory store for evidence matching the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            query_text: Optional free-text query (not used in simple impl).
            max_items: Maximum evidence records to return.

        Returns:
            An ``EvidenceQueryResult`` with matching records.
        """
        start = time.monotonic()
        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        for oid in object_ids:
            for ev in self._evidence.get(oid, []):
                eid = ev.get("evidence_id", ev.get("id", id(ev)))
                if eid in seen:
                    continue
                seen.add(eid)
                results.append(ev)
                if len(results) >= max_items:
                    break
            if len(results) >= max_items:
                break

        total = len(results)
        elapsed = (time.monotonic() - start) * 1000.0

        return EvidenceQueryResult(
            evidence=results,
            total_count=total,
            query_time_ms=round(elapsed, 3),
        )


class InMemoryRelationshipAdapter(RelationshipStoreAdapter):
    """Default in-memory Relationship Engine adapter.

    Stores relationships in a dict and indexes by source/target object IDs.
    Suitable for prototyping and testing.
    """

    def __init__(self) -> None:
        self._relationships: dict[str, list[dict[str, Any]]] = {}

    def add_relationship(
        self, object_id: str, relationship: dict[str, Any]
    ) -> None:
        """Add a relationship record involving an object.

        Args:
            object_id: The object ID that is involved in this relationship.
            relationship: The relationship record data.
        """
        self._relationships.setdefault(object_id, []).append(relationship)

    def query(
        self,
        object_ids: list[str],
        query_text: str,
        max_items: int,
    ) -> RelationshipQueryResult:
        """Query in-memory store for relationships involving the given object IDs.

        Args:
            object_ids: Object IDs to search for.
            query_text: Optional free-text query (not used in simple impl).
            max_items: Maximum relationships to return.

        Returns:
            A ``RelationshipQueryResult`` with matching records.
        """
        start = time.monotonic()
        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        for oid in object_ids:
            for rel in self._relationships.get(oid, []):
                rid = rel.get("relationship_id", rel.get("id", id(rel)))
                if rid in seen:
                    continue
                seen.add(rid)
                results.append(rel)
                if len(results) >= max_items:
                    break
            if len(results) >= max_items:
                break

        total = len(results)
        elapsed = (time.monotonic() - start) * 1000.0

        return RelationshipQueryResult(
            relationships=results,
            total_count=total,
            query_time_ms=round(elapsed, 3),
        )


# ── Relevance Scoring ──────────────────────────────────────────────────────────


def _compute_relevance_score(
    item: dict[str, Any],
    query_text: str,
    object_ids: list[str],
) -> RelevanceScore:
    """Compute a deterministic relevance score for a single context item.

    Relevance is computed from:
    - Direct object ID match (boost: 0.4)
    - Text overlap with query text (boost: 0.3)
    - Item type weight (boost: 0.2)
    - Recency (boost: 0.1, set externally)

    Args:
        item: The context item to score.
        query_text: The free-text query to match against.
        object_ids: Object IDs that the query is about.

    Returns:
        A ``RelevanceScore`` with the computed score and reasoning.
    """
    score = 0.0
    reasoning_parts: list[str] = []

    # 1. Direct object ID match (weight 0.4)
    item_id = item.get("object_id", item.get("source_id", item.get("target_id", "")))
    if item_id in object_ids:
        score += 0.4
        reasoning_parts.append("direct_object_match")

    # 2. Text overlap with query text (weight 0.3)
    if query_text:
        query_lower = query_text.lower()
        match_fields = ["statement", "label", "description", "name", "summary", "text"]
        text_score = 0.0
        for field in match_fields:
            field_value = item.get(field, "")
            if isinstance(field_value, str) and query_lower in field_value.lower():
                text_score = max(text_score, 0.3)
        score += text_score
        if text_score > 0:
            reasoning_parts.append("text_overlap")

    # 3. Item type weight (weight 0.2)
    item_type = item.get("item_type", item.get("type", "unknown"))
    type_weights: dict[str, float] = {
        "observation": 0.20,
        "memory": 0.18,
        "fact": 0.16,
        "evidence": 0.14,
        "event": 0.12,
        "relationship": 0.10,
    }
    score += type_weights.get(item_type, 0.10)
    reasoning_parts.append(f"type_weight:{item_type}")

    # Clamp
    score = max(0.0, min(1.0, score))

    return RelevanceScore(
        item_id=item.get("id", item.get("object_id", item.get("event_id", ""))),
        item_type=item_type,
        score=round(score, 4),
        reasoning=", ".join(reasoning_parts),
        recency=0.0,  # Set externally by the caller
    )


def _compute_context_confidence(
    memory_result: MemoryQueryResult,
    knowledge_result: KnowledgeQueryResult,
    timeline_result: TimelineQueryResult,
    evidence_result: EvidenceQueryResult,
    relationship_result: RelationshipQueryResult,
) -> tuple[float, dict[str, float]]:
    """Compute the overall confidence score for the assembled context.

    Confidence is computed from the completeness and quality of each
    data store query result. Each store contributes a factor based on
    whether it returned data and its average relevance score.

    Args:
        memory_result: Result from the Memory Engine query.
        knowledge_result: Result from the Knowledge Engine query.
        timeline_result: Result from the Timeline Engine query.
        evidence_result: Result from the Evidence Engine query.
        relationship_result: Result from the Relationship Engine query.

    Returns:
        A tuple of (confidence, confidence_factors dict).
    """
    # Store weights — each contributes equally
    W_MEMORY = 0.20
    W_KNOWLEDGE = 0.20
    W_TIMELINE = 0.20
    W_EVIDENCE = 0.20
    W_RELATIONSHIP = 0.20

    def _store_factor(result: Any) -> float:
        """Compute a factor for a store based on its result."""
        total = result.total_count
        if total == 0:
            return 0.0
        # Base factor from having data
        factor = 0.7
        # Boost from relevance scores
        if hasattr(result, "relevancy_scores") and result.relevancy_scores:
            avg_relevance = sum(
                rs.score for rs in result.relevancy_scores
            ) / len(result.relevancy_scores)
            factor += 0.3 * avg_relevance
        return min(1.0, factor)

    memory_factor = _store_factor(memory_result)
    knowledge_factor = _store_factor(knowledge_result)
    timeline_factor = _store_factor(timeline_result)
    evidence_factor = _store_factor(evidence_result)
    relationship_factor = _store_factor(relationship_result)

    confidence = (
        W_MEMORY * memory_factor
        + W_KNOWLEDGE * knowledge_factor
        + W_TIMELINE * timeline_factor
        + W_EVIDENCE * evidence_factor
        + W_RELATIONSHIP * relationship_factor
    )
    confidence = max(0.0, min(1.0, confidence))

    factors: dict[str, float] = {
        "memory_factor": memory_factor,
        "knowledge_factor": knowledge_factor,
        "timeline_factor": timeline_factor,
        "evidence_factor": evidence_factor,
        "relationship_factor": relationship_factor,
        "memory_weight": W_MEMORY,
        "knowledge_weight": W_KNOWLEDGE,
        "timeline_weight": W_TIMELINE,
        "evidence_weight": W_EVIDENCE,
        "relationship_weight": W_RELATIONSHIP,
    }

    return round(confidence, 6), factors


# ── Context Assembly Engine ────────────────────────────────────────────────────


class ContextAssemblyEngine(IntelligenceEngine):
    """In-memory Context Assembly Engine — assembles unified context from stores.

    The ContextAssemblyEngine is the second engine in the Intelligence Runtime
    pipeline. It takes an observation from the Perception Engine and assembles
    the complete context needed for downstream reasoning.

    **Pipeline:**

    1. **Query Memory** — Retrieve related records from the Memory Engine
    2. **Query Knowledge** — Retrieve structured facts from the Knowledge Engine
    3. **Query Timeline** — Retrieve recent events from the Timeline Engine
    4. **Query Evidence** — Retrieve supporting data from the Evidence Engine
    5. **Query Relationships** — Retrieve graph context from the Relationship Engine
    6. **Score relevance** — Compute relevance scores for each item
    7. **Merge** — Combine all results into a unified Context object
    8. **Return** — Deliver the Context to the Reasoning Engine

    **Data Store Adapters:**
    By default, the engine uses ``InMemory*Adapter`` classes that store data
    in dicts. Production deployments should inject real adapters via the
    constructor.

    Usage::
        >>> import asyncio
        >>> engine = ContextAssemblyEngine()
        >>> input_data = ContextAssemblyInput(
        ...     object_ids=["obj_001"],
        ...     query_text="What happened recently?",
        ...     trace_id="trace_001",
        ... )
        >>> output = engine.assemble(input_data)
        >>> output.context.total_items >= 0
        True
        >>> output.deterministic
        True
    """

    engine_id: str = "context_assembly_engine_001"
    """Unique identifier for this engine instance."""

    engine_type: str = "context_assembly"
    """Canonical engine type."""

    # ── Constructor ──────────────────────────────────────────────────────────

    def __init__(
        self,
        engine_id: str | None = None,
        memory_adapter: MemoryStoreAdapter | None = None,
        knowledge_adapter: KnowledgeStoreAdapter | None = None,
        timeline_adapter: TimelineStoreAdapter | None = None,
        evidence_adapter: EvidenceStoreAdapter | None = None,
        relationship_adapter: RelationshipStoreAdapter | None = None,
    ) -> None:
        """Initialise the Context Assembly Engine.

        Args:
            engine_id: Optional override for the engine ID.
            memory_adapter: Custom Memory Engine adapter. Defaults to
                ``InMemoryMemoryAdapter``.
            knowledge_adapter: Custom Knowledge Engine adapter. Defaults to
                ``InMemoryKnowledgeAdapter``.
            timeline_adapter: Custom Timeline Engine adapter. Defaults to
                ``InMemoryTimelineAdapter``.
            evidence_adapter: Custom Evidence Engine adapter. Defaults to
                ``InMemoryEvidenceAdapter``.
            relationship_adapter: Custom Relationship Engine adapter. Defaults to
                ``InMemoryRelationshipAdapter``.
        """
        if engine_id:
            self.engine_id = engine_id

        self._memory = memory_adapter or InMemoryMemoryAdapter()
        self._knowledge = knowledge_adapter or InMemoryKnowledgeAdapter()
        self._timeline = timeline_adapter or InMemoryTimelineAdapter()
        self._evidence = evidence_adapter or InMemoryEvidenceAdapter()
        self._relationships = relationship_adapter or InMemoryRelationshipAdapter()

        # Context store: context_id -> UnifiedContext
        self._contexts: dict[str, UnifiedContext] = {}

        # Index by trace_id
        self._contexts_by_trace: dict[str, list[str]] = {}

        logger.info(
            "ContextAssemblyEngine initialised [engine_id=%s]",
            self.engine_id,
        )

    # ── Public API ───────────────────────────────────────────────────────────

    async def process(self, input_data: EngineInput) -> EngineOutput:
        """Process an input through the full context assembly pipeline.

        Accepts a standard ``EngineInput`` and converts it to the
        ``ContextAssemblyInput`` format before assembling.

        Args:
            input_data: The canonical engine input envelope. The ``payload``
                should contain ``observation``, ``object_ids``, and optionally
                ``query_text``.

        Returns:
            An ``EngineOutput`` with the assembled context as its payload.
        """
        start_time = time.monotonic()
        trace_id = input_data.trace_id or _now_iso()

        payload = input_data.payload
        observation = payload.get("observation", {})
        object_ids = payload.get("object_ids", [])
        query_text = payload.get("query_text", "")

        assembly_input = ContextAssemblyInput(
            observation=observation,
            object_ids=object_ids,
            query_text=query_text,
            trace_id=trace_id,
            confidence_threshold=input_data.confidence_threshold,
        )

        assembly_output = self.assemble(assembly_input)

        processing_time = (time.monotonic() - start_time) * 1000.0

        return EngineOutput(
            output_type="assembled_context",
            payload=assembly_output.context.to_dict(),
            confidence=assembly_output.confidence,
            confidence_factors=assembly_output.confidence_factors,
            deterministic=assembly_output.deterministic,
            trace_id=trace_id,
            escalation_used=assembly_output.escalation_used,
            processing_time_ms=round(processing_time, 3),
        )

    def assemble(self, input_data: ContextAssemblyInput) -> ContextAssemblyOutput:
        """Assemble context from all five data stores.

        This is the primary entry point. It queries each store in parallel
        (sequentially in this in-memory impl), scores relevance, applies
        recency filtering, and merges into a unified context.

        Args:
            input_data: The context assembly input with observation, object IDs,
                query text, and filtering parameters.

        Returns:
            A ``ContextAssemblyOutput`` with the assembled context.
        """
        start_time = time.monotonic()
        trace_id = input_data.trace_id or _now_iso()
        object_ids = input_data.object_ids or []
        query_text = input_data.query_text
        max_items = input_data.max_items_per_store
        recency_window = input_data.recency_window_hours

        logger.debug(
            "ContextAssemblyEngine assembling context [trace_id=%s, objects=%d]",
            trace_id,
            len(object_ids),
        )

        # ── Step 1: Query Memory ──────────────────────────────────────────
        memory_result = self._memory.query(
            object_ids=object_ids,
            query_text=query_text,
            max_items=max_items,
        )

        # ── Step 2: Query Knowledge ───────────────────────────────────────
        knowledge_result = self._knowledge.query(
            object_ids=object_ids,
            query_text=query_text,
            max_items=max_items,
        )

        # ── Step 3: Query Timeline ────────────────────────────────────────
        timeline_result = self._timeline.query(
            object_ids=object_ids,
            recency_window_hours=recency_window,
            max_items=max_items,
        )

        # ── Step 4: Query Evidence ────────────────────────────────────────
        evidence_result = self._evidence.query(
            object_ids=object_ids,
            query_text=query_text,
            max_items=max_items,
        )

        # ── Step 5: Query Relationships ───────────────────────────────────
        relationship_result = self._relationships.query(
            object_ids=object_ids,
            query_text=query_text,
            max_items=max_items,
        )

        # ── Step 6: Score relevance ───────────────────────────────────────
        memory_result.relevancy_scores = [
            _compute_relevance_score(rec, query_text, object_ids)
            for rec in memory_result.records
        ]
        knowledge_result.relevancy_scores = [
            _compute_relevance_score(fact, query_text, object_ids)
            for fact in knowledge_result.facts
        ]
        evidence_result.relevancy_scores = [
            _compute_relevance_score(ev, query_text, object_ids)
            for ev in evidence_result.evidence
        ]
        relationship_result.relevancy_scores = [
            _compute_relevance_score(rel, query_text, object_ids)
            for rel in relationship_result.relationships
        ]

        # ── Step 7: Compute confidence ────────────────────────────────────
        confidence, confidence_factors = _compute_context_confidence(
            memory_result=memory_result,
            knowledge_result=knowledge_result,
            timeline_result=timeline_result,
            evidence_result=evidence_result,
            relationship_result=relationship_result,
        )

        # ── Step 8: Merge into unified context ────────────────────────────
        total_items = (
            memory_result.total_count
            + knowledge_result.total_count
            + timeline_result.total_count
            + evidence_result.total_count
            + relationship_result.total_count
        )

        # Compute average relevance across all scored items
        all_scores = (
            memory_result.relevancy_scores
            + knowledge_result.relevancy_scores
            + evidence_result.relevancy_scores
            + relationship_result.relevancy_scores
        )
        avg_relevance = (
            round(sum(rs.score for rs in all_scores) / len(all_scores), 4)
            if all_scores
            else 0.0
        )

        # Build summary
        summary_parts: list[str] = []
        if memory_result.total_count > 0:
            summary_parts.append(
                f"{memory_result.total_count} memory record(s)"
            )
        if knowledge_result.total_count > 0:
            summary_parts.append(
                f"{knowledge_result.total_count} knowledge fact(s)"
            )
        if timeline_result.total_count > 0:
            summary_parts.append(
                f"{timeline_result.total_count} timeline event(s)"
            )
        if evidence_result.total_count > 0:
            summary_parts.append(
                f"{evidence_result.total_count} evidence record(s)"
            )
        if relationship_result.total_count > 0:
            summary_parts.append(
                f"{relationship_result.total_count} relationship(s)"
            )

        merged_summary = (
            f"Assembled context with {', '.join(summary_parts)}."
            if summary_parts
            else "No context data found for the given object IDs."
        )

        # Check threshold and escalate if needed
        escalation_used = False
        deterministic = True
        threshold = input_data.confidence_threshold
        if confidence < threshold:
            logger.info(
                "Context confidence %.4f below threshold %.4f "
                "[trace_id=%s]",
                confidence,
                threshold,
                trace_id,
            )
            escalation_used = True
            # We mark as non-deterministic but don't actually call an AI
            # provider — the escalation policy layer handles that.
            deterministic = False

        # Build the unified context
        assembly_time = (time.monotonic() - start_time) * 1000.0

        context = UnifiedContext(
            memory=memory_result,
            knowledge=knowledge_result,
            timeline=timeline_result,
            evidence=evidence_result,
            relationships=relationship_result,
            merged_summary=merged_summary,
            total_items=total_items,
            average_relevance=avg_relevance,
            assembly_time_ms=round(assembly_time, 3),
            context_id=_now_iso(),
            trace_id=trace_id,
        )

        # Store the context
        self._contexts[context.context_id] = context
        self._contexts_by_trace.setdefault(trace_id, []).append(context.context_id)

        output = ContextAssemblyOutput(
            context=context,
            confidence=confidence,
            confidence_factors=confidence_factors,
            deterministic=deterministic,
            trace_id=trace_id,
            escalation_used=escalation_used,
            processing_time_ms=round(assembly_time, 3),
        )

        logger.info(
            "Context %s assembled (items=%d, conf=%.4f, det=%s, time=%.1fms) "
            "[trace_id=%s]",
            context.context_id,
            total_items,
            confidence,
            deterministic,
            assembly_time,
            trace_id,
        )

        return output

    def escalate(self, input_data: EngineInput) -> EscalationResult:
        """Bridge to external AI inference for context assembly.

        Called when the assembled context confidence is below threshold.
        Packages the context query into a prompt suitable for an LLM or
        other AI provider.

        Args:
            input_data: The input that fell below the confidence threshold.

        Returns:
            An ``EscalationResult`` with the packaged prompt and context.
        """
        trace_id = input_data.trace_id or _now_iso()
        payload = input_data.payload

        prompt_parts: list[str] = [
            "## Context Assembly Task",
            "",
            "The following context could not be assembled with sufficient confidence.",
            "Please analyse the available data and determine:",
            "1. The most relevant context items for the given query",
            "2. Relationships between the identified objects",
            "3. A summary of the current state of affairs",
            "",
            f"### Object IDs: {payload.get('object_ids', [])}",
            f"### Query: {payload.get('query_text', 'N/A')}",
            f"### Observation: {payload.get('observation', {})}",
        ]

        prompt = "\n".join(prompt_parts)

        context: dict[str, Any] = {
            "escalation_reason": "context_confidence_below_threshold",
            "engine_id": self.engine_id,
        }

        return EscalationResult(
            input_type="context_assembly",
            prompt=prompt,
            context=context,
            trace_id=trace_id,
        )

    def get_capabilities(self) -> list[str]:
        """Return a list of capability strings for this engine.

        Returns:
            A list of capability identifiers.
        """
        return [
            "memory_query",
            "knowledge_query",
            "timeline_query",
            "evidence_query",
            "relationship_query",
            "relevance_scoring",
            "recency_filtering",
            "context_merging",
            "context_summarization",
            "escalation_bridge",
        ]

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Returns:
            A dict with status, engine_id, engine_type, and store stats.
        """
        return {
            "status": "healthy",
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "total_contexts_assembled": len(self._contexts),
            "adapters": {
                "memory": type(self._memory).__name__,
                "knowledge": type(self._knowledge).__name__,
                "timeline": type(self._timeline).__name__,
                "evidence": type(self._evidence).__name__,
                "relationships": type(self._relationships).__name__,
            },
        }

    # ── Context Query Methods ───────────────────────────────────────────────

    def get_context(self, context_id: str) -> UnifiedContext | None:
        """Retrieve a single context by ID.

        Args:
            context_id: The unique context identifier.

        Returns:
            The ``UnifiedContext`` if found, or None.
        """
        return self._contexts.get(context_id)

    def get_contexts_by_trace(self, trace_id: str) -> list[UnifiedContext]:
        """Retrieve all contexts for a given trace ID.

        Args:
            trace_id: The correlation trace ID.

        Returns:
            List of ``UnifiedContext`` objects, in assembly order.
        """
        ids = self._contexts_by_trace.get(trace_id, [])
        return [self._contexts[cid] for cid in ids if cid in self._contexts]

    # ── Adapter Accessors ───────────────────────────────────────────────────

    @property
    def memory_adapter(self) -> MemoryStoreAdapter:
        """Return the current Memory Engine adapter."""
        return self._memory

    @property
    def knowledge_adapter(self) -> KnowledgeStoreAdapter:
        """Return the current Knowledge Engine adapter."""
        return self._knowledge

    @property
    def timeline_adapter(self) -> TimelineStoreAdapter:
        """Return the current Timeline Engine adapter."""
        return self._timeline

    @property
    def evidence_adapter(self) -> EvidenceStoreAdapter:
        """Return the current Evidence Engine adapter."""
        return self._evidence

    @property
    def relationship_adapter(self) -> RelationshipStoreAdapter:
        """Return the current Relationship Engine adapter."""
        return self._relationships