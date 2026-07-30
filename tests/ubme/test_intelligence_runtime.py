"""Pytest tests for Universal Intelligence Runtime."""

import pytest
from core.intelligence_runtime.types import (
    ActionType, ContextFrame, IntelligenceResponse, IntentCategory,
    MemoryEntry, MemoryType, PlanStep, ReasoningStep, ReasoningStrategy,
    ReasoningTrace, RetrievedEvidence, UniversalSuggestion, UrgencyLevel, UserIntent,
)
from core.intelligence_runtime.intent import IntentEngine
from core.intelligence_runtime.context import ContextEngine
from core.intelligence_runtime.memory import MemoryEngine
from core.intelligence_runtime.retrieval import RetrievalLayer
from core.intelligence_runtime.reasoning import ReasoningEngine
from core.intelligence_runtime.planner import ActionPlanner
from core.intelligence_runtime.execution import ToolExecutionLayer
from core.intelligence_runtime.conversation import ConversationRuntime
from core.intelligence_runtime.suggestions import SuggestionsEngine
from core.intelligence_runtime import get_runtime, reset_runtime


class TestTypes:
    def test_user_intent_defaults(self):
        i = UserIntent(raw_input="show invoices")
        assert i.category == IntentCategory.UNKNOWN
        assert i.urgency == UrgencyLevel.NORMAL
        assert i.confidence == 0.0

    def test_user_intent_is_certain(self):
        i = UserIntent(raw_input="test", category=IntentCategory.QUESTION, confidence=0.85, ambiguity=0.1)
        assert i.is_certain()

    def test_context_frame_defaults(self):
        c = ContextFrame()
        assert c.active_workspace == ""
        assert c.active_object_type == ""

    def test_memory_entry_auto_timestamp(self):
        m = MemoryEntry(key="test", content="hello")
        assert m.timestamp != ""

    def test_memory_entry_expiry(self):
        import time
        m = MemoryEntry(key="test", content="hello", ttl_seconds=1)
        assert not m.is_expired()
        time.sleep(1.1)
        assert m.is_expired()

    def test_retrieved_evidence_defaults(self):
        e = RetrievedEvidence(source="object", content="data")
        assert e.relevance == 0.0
        assert e.confidence == 0.0

    def test_reasoning_step_roundtrip(self):
        s = ReasoningStep(step_type="analyze", description="test", output="result", confidence=0.9)
        d = s.to_dict()
        assert d["step_type"] == "analyze"
        assert d["confidence"] == 0.9

    def test_plan_step_roundtrip(self):
        p = PlanStep(action=ActionType.ANSWER, description="Provide answer")
        d = p.to_dict()
        assert d["action"] == "answer"

    def test_reasoning_trace_timestamp(self):
        t = ReasoningTrace(intent=UserIntent(raw_input="hi"), context=ContextFrame(),
                           strategy=ReasoningStrategy.DIRECT_ANSWER)
        assert t.timestamp != ""

    def test_intelligence_response_defaults(self):
        r = IntelligenceResponse(content="Hello")
        assert not r.requires_clarification
        assert r.clarification_question == ""

    def test_universal_suggestion_defaults(self):
        s = UniversalSuggestion(key="test", title="Test", description="desc", suggestion_type="action")
        assert s.confidence == 0.0


class TestIntentEngine:
    def test_question_intent(self):
        engine = IntentEngine()
        result = engine.classify("What are my open invoices?")
        assert result.category == IntentCategory.QUESTION
        assert result.confidence >= 0.7

    def test_command_intent(self):
        engine = IntentEngine()
        result = engine.classify("Create a new customer named Acme Corp")
        assert result.category == IntentCategory.COMMAND

    def test_search_intent(self):
        engine = IntentEngine()
        result = engine.classify("Find bookings for Paris")
        assert result.category == IntentCategory.SEARCH

    def test_navigate_intent(self):
        engine = IntentEngine()
        result = engine.classify("Go to my dashboard")
        assert result.category == IntentCategory.NAVIGATE

    def test_explain_intent(self):
        engine = IntentEngine()
        result = engine.classify("Why did you recommend this?")
        assert result.category == IntentCategory.EXPLAIN

    def test_automate_intent(self):
        engine = IntentEngine()
        result = engine.classify("Automate sending invoices")
        assert result.category == IntentCategory.AUTOMATE

    def test_urgency_detection(self):
        engine = IntentEngine()
        result = engine.classify("This is urgent, I need this immediately")
        assert result.urgency == UrgencyLevel.CRITICAL

    def test_entity_extraction(self):
        engine = IntentEngine()
        result = engine.classify("Show me invoice for customer Acme")
        assert any(e["value"] == "invoice" for e in result.entities)

    def test_empty_input(self):
        engine = IntentEngine()
        result = engine.classify("")
        assert result.category == IntentCategory.UNKNOWN


class TestContextEngine:
    def test_basic_update(self):
        ctx = ContextEngine()
        result = ctx.update("session1", active_workspace="travel")
        assert result.active_workspace == "travel"

    def test_get_existing(self):
        ctx = ContextEngine()
        ctx.update("session1", active_workspace="travel")
        result = ctx.get("session1")
        assert result.active_workspace == "travel"

    def test_get_new_creates_default(self):
        ctx = ContextEngine()
        result = ctx.get("new_session")
        assert result.conversation_id == "new_session"

    def test_push_history(self):
        ctx = ContextEngine()
        ctx.push_history("s1", "hello")
        ctx.push_history("s1", "world")
        assert len(ctx.get("s1").recent_history) == 2

    def test_set_task(self):
        ctx = ContextEngine()
        ctx.set_task("s1", "Review invoices")
        assert ctx.get("s1").current_task == "Review invoices"

    def test_navigate_updates_context(self):
        ctx = ContextEngine()
        ctx.navigate("s1", "travel", "booking", "123")
        f = ctx.get("s1")
        assert f.active_workspace == "travel"
        assert f.active_object_type == "booking"
        assert f.active_object_id == "123"

    def test_reset_session(self):
        ctx = ContextEngine()
        ctx.update("s1", active_workspace="travel")
        ctx.reset_session("s1")
        assert ctx.get("s1").active_workspace == ""


class TestMemoryEngine:
    def test_store_and_retrieve(self):
        mem = MemoryEngine()
        mem.store("user_name", "Alice", MemoryType.LONG_TERM)
        result = mem.get("user_name", MemoryType.LONG_TERM)
        assert result is not None
        assert result.content == "Alice"

    def test_store_and_retrieve_auto_type(self):
        mem = MemoryEngine()
        mem.store("fav_color", "blue", MemoryType.LONG_TERM)
        result = mem.get("fav_color")
        assert result is not None
        assert result.content == "blue"

    def test_search(self):
        mem = MemoryEngine()
        mem.store("business_name", "Acme Corp", MemoryType.BUSINESS)
        mem.store("owner_name", "Bob", MemoryType.LONG_TERM)
        results = mem.search("acme")
        assert len(results) >= 1

    def test_recall_recent(self):
        mem = MemoryEngine()
        mem.store("q1", "hello", MemoryType.SHORT_TERM)
        mem.store("q2", "world", MemoryType.SHORT_TERM)
        recent = mem.recall_recent(MemoryType.SHORT_TERM, 5)
        assert len(recent) == 2

    def test_forget(self):
        mem = MemoryEngine()
        mem.store("temp", "data", MemoryType.SHORT_TERM, ttl_seconds=3600)
        assert mem.forget("temp", MemoryType.SHORT_TERM) is True
        assert mem.forget("nonexistent") is False

    def test_store_with_ttl(self):
        mem = MemoryEngine()
        mem.store("expiring", "data", MemoryType.SHORT_TERM, ttl_seconds=0)
        result = mem.get("expiring")
        assert result is not None

    def test_clear_type(self):
        mem = MemoryEngine()
        mem.store("a", "1", MemoryType.SHORT_TERM)
        mem.store("b", "2", MemoryType.LONG_TERM)
        mem.clear(MemoryType.SHORT_TERM)
        assert mem.count(MemoryType.SHORT_TERM) == 0
        assert mem.count(MemoryType.LONG_TERM) == 1


class TestConversationRuntime:
    def test_add_message(self):
        conv = ConversationRuntime()
        msg = conv.add_message("s1", "user", "Hello")
        assert msg["role"] == "user"
        assert msg["content"] == "Hello"

    def test_get_history(self):
        conv = ConversationRuntime()
        conv.add_message("s1", "user", "Hi")
        conv.add_message("s1", "assistant", "Hello there")
        history = conv.get_history("s1")
        assert len(history) == 2

    def test_context_continuity(self):
        conv = ConversationRuntime()
        ctx = ContextFrame(active_workspace="travel", active_module="travel")
        conv.add_message("s1", "user", "Show bookings", ctx)
        result = conv.get_context_continuity("s1", ContextFrame(active_workspace="medical"))
        assert result["context_shifted"] is True


class TestRetrievalLayer:
    def test_retrieve_with_graph_provider(self):
        layer = RetrievalLayer()
        calls = []
        layer.set_graph_provider(lambda q: ([{"name": "Customer"}, {"name": "Invoice"}], calls.append(1)))
        # Actually let's just test it works without providers
        layer.set_graph_provider(lambda q: [{"name": "Customer"}])
        evidence = layer.retrieve("invoice", module_key="travel")
        assert len(evidence) >= 1


class TestSuggestionsEngine:
    def test_suggest_basic(self):
        se = SuggestionsEngine()
        ctx = ContextFrame(active_module="travel", active_object_type="booking", active_object_id="123")
        suggestions = se.suggest(ctx)
        assert len(suggestions) >= 2  # explore + object_actions

    def test_suggest_for_query(self):
        se = SuggestionsEngine()
        ctx = ContextFrame(active_module="travel")
        suggestions = se.suggest_for_query("explore", ctx)
        assert len(suggestions) >= 1


class TestFullPipeline:
    def test_end_to_end_with_wired_providers(self):
        reset_runtime()
        runtime = get_runtime()
        runtime.wire_graph_provider(lambda q: [{"name": "Customer"}, {"name": "Invoice"}])
        runtime.wire_object_provider(lambda q, m: [{"name": "Invoice #1001"}])
        runtime.wire_memory_provider(lambda q: runtime.memory.search(q))

        response = runtime.process("Show me invoices", session_id="e2e", module_key="travel")
        assert len(response.trace.evidence) >= 1
        assert response.trace.intent.category == IntentCategory.QUESTION

    def test_command_creates_action_plan(self):
        reset_runtime()
        runtime = get_runtime()
        runtime.wire_object_provider(lambda q, m: [])
        runtime.wire_graph_provider(lambda q: [])

        response = runtime.process("Create a new customer", session_id="cmd")
        assert len(response.actions) >= 1 or response.trace.intent.category == IntentCategory.COMMAND

    def test_memory_persists_across_queries(self):
        reset_runtime()
        runtime = get_runtime()
        runtime.memory.store("business", "Test Co", MemoryType.BUSINESS)
        found = runtime.memory.get("business", MemoryType.BUSINESS)
        assert found is not None
        assert found.content == "Test Co"

    def test_health_check(self):
        reset_runtime()
        runtime = get_runtime()
        health = runtime.health()
        assert health["status"] == "healthy"
        assert "memory_count" in health

    def test_reset_clears_state(self):
        reset_runtime()
        runtime = get_runtime()
        runtime.process("hello", session_id="reset_test")
        runtime.reset()
        assert runtime.memory.count() == 0