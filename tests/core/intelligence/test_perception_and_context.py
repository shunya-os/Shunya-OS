"""Tests for the SHUNYA Perception Engine and Context Assembly Engine.

Covers:
1. Perception Engine — models, pipeline, classification, prioritisation,
   confidence, escalation, health, determinism
2. Context Assembly Engine — models, assembly pipeline, all 5 data store
   queries, relevance scoring, merging, confidence, determinism, health
3. Edge cases — empty payloads, unknown types, threshold boundaries,
   large context sets, error handling
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone, timedelta

import pytest

from core.intelligence.perception import (
    PerceptionEngine,
    IntelligenceEngine as PEIntelligenceEngine,
    EngineInput,
    EngineOutput,
    EscalationResult,
    Observation,
    InputType,
    ObservationStatus,
    PerceptionPriority,
    SourceMetadata,
)
from core.intelligence.context_assembly import (
    ContextAssemblyEngine,
    IntelligenceEngine as CAIntelligenceEngine,
    UnifiedContext,
    ContextAssemblyInput,
    ContextAssemblyOutput,
    MemoryQueryResult,
    KnowledgeQueryResult,
    TimelineQueryResult,
    EvidenceQueryResult,
    RelationshipQueryResult,
    RelevanceScore,
    InMemoryMemoryAdapter,
    InMemoryKnowledgeAdapter,
    InMemoryTimelineAdapter,
    InMemoryEvidenceAdapter,
    InMemoryRelationshipAdapter,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def perception_engine() -> PerceptionEngine:
    return PerceptionEngine()


@pytest.fixture
def context_assembly_engine() -> ContextAssemblyEngine:
    return ContextAssemblyEngine()


@pytest.fixture
def populated_context_assembly_engine() -> ContextAssemblyEngine:
    engine = ContextAssemblyEngine()

    # Populate Memory
    engine.memory_adapter.add_record(
        "obj_001",
        {
            "id": "mem_001",
            "type": "memory",
            "summary": "User prefers dark mode",
            "item_type": "memory",
        },
    )
    engine.memory_adapter.add_record(
        "obj_001",
        {
            "id": "mem_002",
            "type": "memory",
            "summary": "Last interaction was a query about settings",
            "item_type": "memory",
        },
    )

    # Populate Knowledge
    engine.knowledge_adapter.add_fact(
        "obj_001",
        {
            "id": "fact_001",
            "type": "fact",
            "statement": "User has admin role",
            "item_type": "fact",
        },
    )

    # Populate Timeline
    now = datetime.now(timezone.utc)
    engine.timeline_adapter.add_event(
        "obj_001",
        {
            "event_id": "evt_001",
            "type": "event",
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "event_type": "user.login",
            "summary": "User logged in",
        },
    )

    # Populate Evidence
    engine.evidence_adapter.add_evidence(
        "obj_001",
        {
            "evidence_id": "ev_001",
            "type": "evidence",
            "statement": "User authenticated via SSO",
            "item_type": "evidence",
        },
    )

    # Populate Relationships
    engine.relationship_adapter.add_relationship(
        "obj_001",
        {
            "relationship_id": "rel_001",
            "type": "relationship",
            "source_id": "obj_001",
            "target_id": "obj_002",
            "relationship_type": "member_of",
            "label": "Member of Team Alpha",
            "item_type": "relationship",
        },
    )

    return engine


# =========================================================================
# 1. Perception Engine — Models
# =========================================================================


class TestPerceptionModels:
    def test_engine_input_defaults(self):
        inp = EngineInput(input_type="observation", payload={"key": "val"})
        assert inp.input_type == "observation"
        assert inp.payload == {"key": "val"}
        assert inp.context is None
        assert inp.trace_id == ""
        assert inp.confidence_threshold == 0.85

    def test_engine_output_defaults(self):
        out = EngineOutput()
        assert out.output_type == ""
        assert out.payload == {}
        assert out.confidence == 0.0
        assert out.deterministic is True
        assert out.escalation_used is False
        assert out.processing_time_ms == 0.0

    def test_escaltion_result_defaults(self):
        er = EscalationResult()
        assert er.input_type == ""
        assert er.prompt == ""
        assert er.context == {}
        assert er.trace_id == ""

    def test_observation_defaults(self):
        obs = Observation()
        assert obs.input_type == InputType.UNKNOWN.value
        assert obs.payload == {}
        assert obs.priority == PerceptionPriority.NORMAL.value
        assert obs.confidence == 0.0
        assert obs.status == ObservationStatus.CAPTURED.value
        assert obs.classification_rules == []

    def test_observation_to_dict(self):
        obs = Observation(
            observation_id="obs_001",
            input_type=InputType.USER_MESSAGE.value,
            payload={"text": "hello"},
            confidence=0.95,
            trace_id="trace_001",
            status=ObservationStatus.CLASSIFIED.value,
        )
        d = obs.to_dict()
        assert d["observation_id"] == "obs_001"
        assert d["input_type"] == "user_message"
        assert d["payload"] == {"text": "hello"}
        assert d["confidence"] == 0.95
        assert d["trace_id"] == "trace_001"
        assert d["status"] == "classified"
        assert "source_metadata" in d
        assert "classification_rules" in d

    def test_source_metadata_defaults(self):
        sm = SourceMetadata()
        assert sm.source_engine == ""
        assert sm.source_type == ""
        assert sm.source_reliability == 0.5
        assert sm.captured_at == ""
        assert sm.received_at != ""

    def test_input_type_from_string(self):
        assert InputType.from_string("user_message") == InputType.USER_MESSAGE
        assert InputType.from_string("unknown_type") == InputType.UNKNOWN
        assert InputType.from_string("") == InputType.UNKNOWN


# =========================================================================
# 2. Perception Engine — Pipeline
# =========================================================================


class TestPerceptionEngine:
    @pytest.mark.asyncio
    async def test_process_valid_input(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={
                "text": "Hello world",
                "source_reliability": 0.95,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
            trace_id="trace_001",
            confidence_threshold=0.70,
        )
        output = await perception_engine.process(inp)
        assert isinstance(output, EngineOutput)
        assert output.output_type == "observation"
        assert output.deterministic is True
        assert output.escalation_used is False
        assert 0.0 <= output.confidence <= 1.0
        assert output.trace_id == "trace_001"
        assert output.processing_time_ms >= 0.0
        assert "observation_id" in output.payload
        assert output.payload["input_type"] == InputType.USER_MESSAGE.value

    @pytest.mark.asyncio
    async def test_process_classifies_system_event(self, perception_engine):
        inp = EngineInput(
            input_type="system_event",
            payload={"severity": "critical", "message": "Disk full"},
            trace_id="trace_002",
        )
        output = await perception_engine.process(inp)
        assert output.payload["input_type"] == InputType.SYSTEM_ALERT.value
        assert output.payload["priority"] == PerceptionPriority.CRITICAL.value
        # Critical severity gets highest confidence
        assert output.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_process_classifies_sensor_reading(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={"sensor_id": "temp_01", "measurement": 23.5, "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")},
            trace_id="trace_003",
        )
        output = await perception_engine.process(inp)
        assert output.payload["input_type"] == InputType.SENSOR_READING.value
        assert output.payload["priority"] == PerceptionPriority.LOW.value

    @pytest.mark.asyncio
    async def test_process_classifies_timer_trigger(self, perception_engine):
        inp = EngineInput(
            input_type="system_event",
            payload={"trigger_type": "timer", "schedule": "every_5min"},
            trace_id="trace_004",
        )
        output = await perception_engine.process(inp)
        assert output.payload["input_type"] == InputType.TIMER_TRIGGER.value

    @pytest.mark.asyncio
    async def test_process_classifies_user_command(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={"text": "deploy now", "command": "deploy"},
            trace_id="trace_005",
        )
        output = await perception_engine.process(inp)
        assert output.payload["input_type"] == InputType.USER_COMMAND.value
        assert output.payload["priority"] == PerceptionPriority.HIGH.value

    @pytest.mark.asyncio
    async def test_process_classifies_user_query(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={"text": "What is the status?", "is_query": True},
            trace_id="trace_006",
        )
        output = await perception_engine.process(inp)
        assert output.payload["input_type"] == InputType.USER_QUERY.value

    @pytest.mark.asyncio
    async def test_process_unknown_type(self, perception_engine):
        inp = EngineInput(
            input_type="something_weird",
            payload={"data": "test"},
            trace_id="trace_007",
        )
        output = await perception_engine.process(inp)
        # Falls back to UNKNOWN since no heuristic matches
        assert output.payload["input_type"] in (
            InputType.UNKNOWN.value,
            "something_weird",
        )

    @pytest.mark.asyncio
    async def test_process_empty_payload_raises(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={},
            trace_id="trace_008",
        )
        with pytest.raises(ValueError, match="empty"):
            await perception_engine.process(inp)

    @pytest.mark.asyncio
    async def test_process_confidence_above_threshold(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={
                "text": "hello",
                "source_reliability": 0.9,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
            trace_id="trace_009",
            confidence_threshold=0.3,
        )
        output = await perception_engine.process(inp)
        assert output.deterministic is True
        assert output.escalation_used is False

    @pytest.mark.asyncio
    async def test_process_confidence_below_threshold(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={"data": "noisy signal"},
            trace_id="trace_010",
            confidence_threshold=0.99,  # Impossible to reach
        )
        output = await perception_engine.process(inp)
        assert output.deterministic is False
        assert output.escalation_used is True
        assert output.payload.get("metadata", {}).get("escalation_prompt", "") != ""

    @pytest.mark.asyncio
    async def test_determinism(self, perception_engine):
        """Same inputs produce identical outputs (structural determinism)."""
        inp = EngineInput(
            input_type="observation",
            payload={"text": "test message", "timestamp": "2026-01-01T00:00:00Z"},
            trace_id="trace_det_001",
        )
        out1 = await perception_engine.process(inp)
        out2 = await perception_engine.process(inp)
        assert out1.output_type == out2.output_type
        assert out1.payload["input_type"] == out2.payload["input_type"]
        assert out1.payload["priority"] == out2.payload["priority"]
        assert out1.deterministic == out2.deterministic

    def test_escalate_creates_prompt(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={"text": "ambiguous"},
            trace_id="trace_esc_001",
        )
        result = perception_engine.escalate(inp)
        assert isinstance(result, EscalationResult)
        assert result.input_type == "observation"
        assert "Perception Task" in result.prompt
        assert "ambiguous" in result.prompt
        assert result.trace_id == "trace_esc_001"

    def test_get_capabilities(self, perception_engine):
        caps = perception_engine.get_capabilities()
        assert isinstance(caps, list)
        assert "input_validation" in caps
        assert "source_enrichment" in caps
        assert "input_classification" in caps
        assert "priority_assignment" in caps
        assert "confidence_computation" in caps
        assert "observation_creation" in caps
        assert "escalation_bridge" in caps

    def test_health_check(self, perception_engine):
        health = perception_engine.health_check()
        assert health["status"] == "healthy"
        assert health["engine_id"] == "perception_engine_001"
        assert health["engine_type"] == "perception"
        assert health["total_observations"] == 0

    @pytest.mark.asyncio
    async def test_health_after_processing(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={"text": "hello"},
            trace_id="trace_health_001",
        )
        await perception_engine.process(inp)
        health = perception_engine.health_check()
        assert health["total_observations"] == 1

    @pytest.mark.asyncio
    async def test_store_and_retrieve_observation(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={"text": "find me"},
            trace_id="trace_store_001",
        )
        output = await perception_engine.process(inp)
        obs_id = output.payload["observation_id"]

        retrieved = perception_engine.get_observation(obs_id)
        assert retrieved is not None
        assert retrieved.observation_id == obs_id
        assert retrieved.trace_id == "trace_store_001"

        # Query by trace
        by_trace = perception_engine.get_observations_by_trace("trace_store_001")
        assert len(by_trace) == 1
        assert by_trace[0].observation_id == obs_id

        # Query by type
        by_type = perception_engine.get_observations_by_type(
            InputType.USER_MESSAGE
        )
        assert len(by_type) >= 1

        # Query by status
        by_status = perception_engine.get_observations_by_status(
            ObservationStatus.CLASSIFIED
        )
        assert len(by_status) >= 1

    def test_count_observations_empty(self, perception_engine):
        assert perception_engine.count_observations() == 0

    def test_custom_engine_id(self):
        engine = PerceptionEngine(engine_id="perception_custom")
        assert engine.engine_id == "perception_custom"


# =========================================================================
# 3. Context Assembly Engine — Models
# =========================================================================


class TestContextAssemblyModels:
    def test_memory_query_result_defaults(self):
        mqr = MemoryQueryResult()
        assert mqr.records == []
        assert mqr.total_count == 0
        assert mqr.relevancy_scores == []
        assert mqr.query_time_ms == 0.0

    def test_knowledge_query_result_defaults(self):
        kqr = KnowledgeQueryResult()
        assert kqr.facts == []
        assert kqr.total_count == 0

    def test_timeline_query_result_defaults(self):
        tqr = TimelineQueryResult()
        assert tqr.events == []
        assert tqr.total_count == 0
        assert tqr.from_time == ""
        assert tqr.to_time == ""

    def test_evidence_query_result_defaults(self):
        eqr = EvidenceQueryResult()
        assert eqr.evidence == []
        assert eqr.total_count == 0

    def test_relationship_query_result_defaults(self):
        rqr = RelationshipQueryResult()
        assert rqr.relationships == []
        assert rqr.total_count == 0

    def test_relevance_score_defaults(self):
        rs = RelevanceScore()
        assert rs.item_id == ""
        assert rs.score == 0.0
        assert rs.recency == 0.0

    def test_unified_context_defaults(self):
        uc = UnifiedContext()
        assert uc.memory.total_count == 0
        assert uc.knowledge.total_count == 0
        assert uc.timeline.total_count == 0
        assert uc.evidence.total_count == 0
        assert uc.relationships.total_count == 0
        assert uc.total_items == 0
        assert uc.average_relevance == 0.0
        assert uc.context_id == ""

    def test_unified_context_to_dict(self):
        uc = UnifiedContext(
            context_id="ctx_001",
            trace_id="trace_001",
            total_items=5,
            merged_summary="Test summary",
        )
        d = uc.to_dict()
        assert d["context_id"] == "ctx_001"
        assert d["trace_id"] == "trace_001"
        assert d["total_items"] == 5
        assert d["merged_summary"] == "Test summary"
        assert "memory" in d
        assert "knowledge" in d
        assert "timeline" in d
        assert "evidence" in d
        assert "relationships" in d

    def test_context_assembly_input_defaults(self):
        cai = ContextAssemblyInput()
        assert cai.observation == {}
        assert cai.object_ids == []
        assert cai.query_text == ""
        assert cai.max_items_per_store == 50
        assert cai.recency_window_hours == 24
        assert cai.confidence_threshold == 0.75

    def test_context_assembly_output_defaults(self):
        cao = ContextAssemblyOutput()
        assert cao.context.total_items == 0
        assert cao.confidence == 0.0
        assert cao.deterministic is True
        assert cao.escalation_used is False


# =========================================================================
# 4. Context Assembly Engine — Assembly Pipeline
# =========================================================================


class TestContextAssemblyEngine:
    def test_assemble_with_no_data(self, context_assembly_engine):
        inp = ContextAssemblyInput(
            object_ids=["obj_nonexistent"],
            query_text="anything",
            trace_id="trace_empty_001",
        )
        output = context_assembly_engine.assemble(inp)
        assert isinstance(output, ContextAssemblyOutput)
        assert output.context.total_items == 0
        assert output.confidence == 0.0
        # 0.0 confidence < default threshold 0.75, so escalation is triggered
        assert output.deterministic is False
        assert output.escalation_used is True
        assert output.context.merged_summary == "No context data found for the given object IDs."

    def test_assemble_with_populated_data(self, populated_context_assembly_engine):
        inp = ContextAssemblyInput(
            object_ids=["obj_001"],
            query_text="user settings",
            trace_id="trace_pop_001",
        )
        output = populated_context_assembly_engine.assemble(inp)
        ctx = output.context

        assert ctx.total_items == 6  # 2 memories + 1 fact + 1 event + 1 evidence + 1 relationship
        assert ctx.memory.total_count == 2
        assert ctx.knowledge.total_count == 1
        assert ctx.timeline.total_count == 1
        assert ctx.evidence.total_count == 1
        assert ctx.relationships.total_count == 1
        assert 0.0 < ctx.average_relevance <= 1.0
        assert ctx.trace_id == "trace_pop_001"
        assert ctx.context_id != ""

        # Check confidence
        assert 0.0 < output.confidence <= 1.0

        # Check merged summary mentions the data
        assert "memory" in ctx.merged_summary.lower()
        assert "knowledge" in ctx.merged_summary.lower()
        assert "timeline" in ctx.merged_summary.lower()
        assert "evidence" in ctx.merged_summary.lower()
        assert "relationship" in ctx.merged_summary.lower()

    def test_assemble_respects_max_items(self):
        engine = ContextAssemblyEngine()
        # Add many records to memory
        for i in range(100):
            engine.memory_adapter.add_record(
                "obj_001",
                {"id": f"mem_{i:03d}", "type": "memory", "summary": f"Record {i}", "item_type": "memory"},
            )

        inp = ContextAssemblyInput(
            object_ids=["obj_001"],
            max_items_per_store=10,
            trace_id="trace_max_001",
        )
        output = engine.assemble(inp)
        assert output.context.memory.total_count <= 10

    def test_assemble_respects_recency_window(self):
        engine = ContextAssemblyEngine()
        now = datetime.now(timezone.utc)

        # Old event (beyond recency window)
        old_ts = (now - timedelta(hours=48)).isoformat().replace("+00:00", "Z")
        engine.timeline_adapter.add_event(
            "obj_001",
            {"event_id": "evt_old", "timestamp": old_ts, "summary": "Old event"},
        )

        # Recent event (within recency window)
        recent_ts = now.isoformat().replace("+00:00", "Z")
        engine.timeline_adapter.add_event(
            "obj_001",
            {"event_id": "evt_recent", "timestamp": recent_ts, "summary": "Recent event"},
        )

        inp = ContextAssemblyInput(
            object_ids=["obj_001"],
            recency_window_hours=24,  # Only last 24 hours
            trace_id="trace_recency_001",
        )
        output = engine.assemble(inp)
        assert output.context.timeline.total_count == 1
        assert output.context.timeline.events[0]["event_id"] == "evt_recent"

    def test_assemble_multiple_objects(self):
        engine = ContextAssemblyEngine()
        engine.memory_adapter.add_record(
            "obj_001",
            {"id": "mem_a", "type": "memory", "summary": "Object 1 memory", "item_type": "memory"},
        )
        engine.memory_adapter.add_record(
            "obj_002",
            {"id": "mem_b", "type": "memory", "summary": "Object 2 memory", "item_type": "memory"},
        )

        inp = ContextAssemblyInput(
            object_ids=["obj_001", "obj_002"],
            trace_id="trace_multi_001",
        )
        output = engine.assemble(inp)
        assert output.context.total_items == 2

    def test_determinism(self, populated_context_assembly_engine):
        inp = ContextAssemblyInput(
            object_ids=["obj_001"],
            query_text="user",
            trace_id="trace_det_002",
        )
        out1 = populated_context_assembly_engine.assemble(inp)
        out2 = populated_context_assembly_engine.assemble(inp)
        assert out1.context.total_items == out2.context.total_items
        assert out1.context.average_relevance == out2.context.average_relevance
        assert out1.confidence == out2.confidence
        assert out1.deterministic == out2.deterministic

    def test_get_capabilities(self, context_assembly_engine):
        caps = context_assembly_engine.get_capabilities()
        assert isinstance(caps, list)
        assert "memory_query" in caps
        assert "knowledge_query" in caps
        assert "timeline_query" in caps
        assert "evidence_query" in caps
        assert "relationship_query" in caps
        assert "relevance_scoring" in caps
        assert "context_merging" in caps

    def test_health_check(self, context_assembly_engine):
        health = context_assembly_engine.health_check()
        assert health["status"] == "healthy"
        assert health["engine_id"] == "context_assembly_engine_001"
        assert health["engine_type"] == "context_assembly"
        assert health["total_contexts_assembled"] == 0
        assert "adapters" in health

    def test_health_after_assembly(self, populated_context_assembly_engine):
        inp = ContextAssemblyInput(object_ids=["obj_001"], trace_id="trace_health_002")
        populated_context_assembly_engine.assemble(inp)
        health = populated_context_assembly_engine.health_check()
        assert health["total_contexts_assembled"] == 1

    def test_context_retrieval(self, populated_context_assembly_engine):
        inp = ContextAssemblyInput(object_ids=["obj_001"], trace_id="trace_ret_001")
        output = populated_context_assembly_engine.assemble(inp)
        ctx_id = output.context.context_id

        retrieved = populated_context_assembly_engine.get_context(ctx_id)
        assert retrieved is not None
        assert retrieved.context_id == ctx_id

        by_trace = populated_context_assembly_engine.get_contexts_by_trace(
            "trace_ret_001"
        )
        assert len(by_trace) == 1

    def test_confidence_below_threshold(self, context_assembly_engine):
        # Empty assembly should have 0.0 confidence
        inp = ContextAssemblyInput(
            object_ids=["nowhere"],
            confidence_threshold=0.01,  # Above 0.0
            trace_id="trace_lowconf_001",
        )
        output = context_assembly_engine.assemble(inp)
        assert output.escalation_used is True
        assert output.deterministic is False

    def test_confidence_above_threshold(self, populated_context_assembly_engine):
        inp = ContextAssemblyInput(
            object_ids=["obj_001"],
            confidence_threshold=0.01,  # Easily reached
            trace_id="trace_highconf_001",
        )
        output = populated_context_assembly_engine.assemble(inp)
        assert output.escalation_used is False
        assert output.deterministic is True

    def test_custom_engine_id(self):
        engine = ContextAssemblyEngine(engine_id="ca_custom")
        assert engine.engine_id == "ca_custom"

    def test_escalate_creates_prompt(self, context_assembly_engine):
        inp = EngineInput(
            input_type="context_assembly",
            payload={"object_ids": ["obj_001"], "query_text": "test"},
            trace_id="trace_esc_ca_001",
        )
        result = context_assembly_engine.escalate(inp)
        assert isinstance(result, EscalationResult)
        assert "Context Assembly Task" in result.prompt
        assert result.trace_id == "trace_esc_ca_001"


# =========================================================================
# 5. Context Assembly Engine — Process (EngineInput interface)
# =========================================================================


class TestContextAssemblyProcess:
    @pytest.mark.asyncio
    async def test_process_via_engine_input(self, populated_context_assembly_engine):
        inp = EngineInput(
            input_type="context_assembly",
            payload={
                "observation": {"input_type": "user_message", "text": "hello"},
                "object_ids": ["obj_001"],
                "query_text": "user info",
            },
            trace_id="trace_proc_001",
            confidence_threshold=0.01,  # Low threshold so confidence passes
        )
        output = await populated_context_assembly_engine.process(inp)
        assert isinstance(output, EngineOutput)
        assert output.output_type == "assembled_context"
        assert output.deterministic is True
        assert "memory" in output.payload
        assert "knowledge" in output.payload
        assert "timeline" in output.payload
        assert "evidence" in output.payload
        assert "relationships" in output.payload


# =========================================================================
# 6. In-Memory Adapters (unit tests)
# =========================================================================


class TestInMemoryAdapters:
    def test_memory_adapter_add_and_query(self):
        adapter = InMemoryMemoryAdapter()
        adapter.add_record("obj_001", {"id": "mem_1", "text": "test"})
        result = adapter.query(object_ids=["obj_001"], query_text="", max_items=10)
        assert result.total_count == 1
        assert result.records[0]["id"] == "mem_1"

    def test_memory_adapter_no_match(self):
        adapter = InMemoryMemoryAdapter()
        result = adapter.query(object_ids=["nowhere"], query_text="", max_items=10)
        assert result.total_count == 0

    def test_knowledge_adapter_add_and_query(self):
        adapter = InMemoryKnowledgeAdapter()
        adapter.add_fact("obj_001", {"id": "fact_1", "statement": "sky is blue"})
        result = adapter.query(object_ids=["obj_001"], query_text="", max_items=10)
        assert result.total_count == 1

    def test_timeline_adapter_recency_filter(self):
        adapter = InMemoryTimelineAdapter()
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(hours=48)).isoformat().replace("+00:00", "Z")
        recent_ts = now.isoformat().replace("+00:00", "Z")

        adapter.add_event("obj_001", {"event_id": "old", "timestamp": old_ts})
        adapter.add_event("obj_001", {"event_id": "recent", "timestamp": recent_ts})

        result = adapter.query(
            object_ids=["obj_001"], recency_window_hours=24, max_items=10
        )
        assert result.total_count == 1
        assert result.events[0]["event_id"] == "recent"

    def test_evidence_adapter_add_and_query(self):
        adapter = InMemoryEvidenceAdapter()
        adapter.add_evidence("obj_001", {"evidence_id": "ev_1", "statement": "proof"})
        result = adapter.query(object_ids=["obj_001"], query_text="", max_items=10)
        assert result.total_count == 1

    def test_relationship_adapter_add_and_query(self):
        adapter = InMemoryRelationshipAdapter()
        adapter.add_relationship(
            "obj_001",
            {"relationship_id": "rel_1", "source_id": "obj_001", "target_id": "obj_002"},
        )
        result = adapter.query(object_ids=["obj_001"], query_text="", max_items=10)
        assert result.total_count == 1


# =========================================================================
# 7. Edge Cases & Error Handling
# =========================================================================


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_perception_no_trace_id_assigns_one(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload={"text": "hello"},
            # No trace_id
        )
        output = await perception_engine.process(inp)
        assert output.trace_id != ""

    def test_context_assembly_no_trace_id_assigns_one(self, context_assembly_engine):
        inp = ContextAssemblyInput(object_ids=["obj_001"])
        output = context_assembly_engine.assemble(inp)
        assert output.trace_id != ""

    @pytest.mark.asyncio
    async def test_perception_rejects_non_dict_payload(self, perception_engine):
        inp = EngineInput(
            input_type="observation",
            payload="not_a_dict",  # type: ignore
        )
        with pytest.raises(TypeError, match="must be a dict"):
            await perception_engine.process(inp)

    def test_context_assembly_empty_object_ids(self, context_assembly_engine):
        inp = ContextAssemblyInput(object_ids=[])
        output = context_assembly_engine.assemble(inp)
        assert output.context.total_items == 0

    def test_in_memory_adapters_respect_max_items(self):
        adapter = InMemoryMemoryAdapter()
        for i in range(20):
            adapter.add_record("obj_001", {"id": f"mem_{i}", "text": f"record {i}"})
        result = adapter.query(object_ids=["obj_001"], query_text="", max_items=5)
        assert result.total_count == 5

    @pytest.mark.asyncio
    async def test_perception_inherits_engine_interface(self):
        assert issubclass(PerceptionEngine, PEIntelligenceEngine)
        engine = PerceptionEngine()
        assert hasattr(engine, "process")
        assert hasattr(engine, "escalate")
        assert hasattr(engine, "get_capabilities")
        assert hasattr(engine, "health_check")

    def test_context_assembly_inherits_engine_interface(self):
        assert issubclass(ContextAssemblyEngine, CAIntelligenceEngine)
        engine = ContextAssemblyEngine()
        assert hasattr(engine, "process")
        assert hasattr(engine, "escalate")
        assert hasattr(engine, "get_capabilities")
        assert hasattr(engine, "health_check")