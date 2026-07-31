
"""Tests for Perception Engine and Context Assembly Engine."""
import pytest, asyncio
from core.intelligence.perception import PerceptionEngine, PerceptionPriority
from core.intelligence.context_assembly import ContextAssemblyEngine
from core.intelligence.models import EngineInput

class TestPerceptionEngine:
    def setup_method(self):
        self.eng = PerceptionEngine()
    def _run(self, inp):
        return asyncio.run(self.eng.process(inp))

    def test_process_observation(self):
        out = self._run(EngineInput(input_type="observation", payload={"text": "test"}, trace_id="t1"))
        assert out.output_type == "observation"
        assert out.deterministic is True

    def test_process_unknown(self):
        out = self._run(EngineInput(input_type="unknown", payload={"text": "test"}))
        assert out is not None

    def test_escalate(self):
        r = self.eng.escalate(EngineInput(input_type="query", payload={"text": "what?"}))
        assert r is not None

    def test_capabilities(self):
        assert len(self.eng.get_capabilities()) > 0

    def test_health(self):
        h = self.eng.health_check()
        assert "status" in h

    def test_priority(self):
        assert PerceptionPriority.CRITICAL.value == "critical"
        assert PerceptionPriority.LOW.value == "low"

class TestContextAssemblyEngine:
    def setup_method(self):
        self.eng = ContextAssemblyEngine()
    def _run(self, inp):
        return asyncio.run(self.eng.process(inp))

    def test_process(self):
        out = self._run(EngineInput(input_type="context_query", payload={"subject_id": "test"}, trace_id="t1"))
        assert out is not None

    def test_escalate(self):
        r = self.eng.escalate(EngineInput(input_type="query", payload={"text": "test"}))
        assert r is not None

    def test_capabilities(self):
        assert len(self.eng.get_capabilities()) > 0

    def test_health(self):
        h = self.eng.health_check()
        assert "status" in h
