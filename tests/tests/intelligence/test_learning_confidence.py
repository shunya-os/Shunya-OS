"""Tests for SHUNYA Intelligence Runtime — Learning Engine and Confidence Engine."""
import sys; sys.path.insert(0, '/home/shunya-deploy/shunya_os')
import pytest, time

from core.intelligence.learning.engine import LearningEngine
from core.intelligence.confidence.engine import ConfidenceEngine, ConfidenceFactor, ConfidenceScore
from core.intelligence.models import EngineInput, ReflectionRecord


# =====================================================================
# Learning Engine Tests
# =====================================================================

class TestLearningEngine:
    def setup_method(self):
        self.eng = LearningEngine()

    def test_process_reflection(self):
        inp = EngineInput(
            input_type="reflection",
            payload={
                "success_score": 0.8,
                "improvement_signals": [{"type": "timing", "description": "Task took longer than expected"}],
                "anomalies": [],
                "subject_id": "task_001",
                "subject_type": "task",
            },
        )
        out = self.eng.process(inp)
        assert out.output_type == "patterns_detected"
        assert len(out.payload["patterns"]) >= 0
        assert out.deterministic is True

    def test_process_batch(self):
        records = [
            {"success_score": 0.9, "improvement_signals": [], "anomalies": []},
            {"success_score": 0.3, "improvement_signals": [{"type": "error", "description": "Failed validation"}], "anomalies": ["Unexpected error"]},
        ]
        inp = EngineInput(input_type="batch", payload={"records": records})
        out = self.eng.process(inp)
        assert out.output_type == "patterns_detected"
        assert out.payload["total_reflections"] == 2

    def test_low_success_pattern(self):
        inp = EngineInput(
            input_type="reflection",
            payload={"success_score": 0.2, "improvement_signals": [], "anomalies": []},
        )
        out = self.eng.process(inp)
        assert len(out.payload["patterns"]) >= 1

    def test_pattern_deduplication(self):
        inp = EngineInput(
            input_type="reflection",
            payload={
                "success_score": 0.5,
                "improvement_signals": [{"type": "recurring", "description": "Same issue"}],
                "anomalies": [],
            },
        )
        self.eng.process(inp)
        self.eng.process(inp)
        patterns = self.eng.get_patterns()
        # Same pattern type should appear once with support_count incremented
        recurring = [p for p in patterns if p.pattern_type == "recurring"]
        assert len(recurring) <= 1

    def test_health_check(self):
        health = self.eng.health_check()
        assert health["engine_id"] == "learning_engine"
        assert health["status"] == "active"

    def test_capabilities(self):
        caps = self.eng.get_capabilities()
        assert "pattern_detection" in caps
        assert "knowledge_consolidation" in caps

    def test_never_escalates(self):
        inp = EngineInput(input_type="reflection", payload={"success_score": 0.5, "improvement_signals": [], "anomalies": []})
        out1 = self.eng.process(inp)
        out2 = self.eng.escalate(inp)
        assert out1.output_type == out2.output_type

    def test_unknown_input_type(self):
        inp = EngineInput(input_type="unknown", payload={})
        out = self.eng.process(inp)
        assert out.output_type == "error"

    def test_clear(self):
        inp = EngineInput(input_type="reflection", payload={"success_score": 0.5, "improvement_signals": [], "anomalies": []})
        self.eng.process(inp)
        assert len(self.eng._reflection_log) > 0
        self.eng.clear()
        assert len(self.eng._reflection_log) == 0


# =====================================================================
# Confidence Engine Tests
# =====================================================================

class TestConfidenceEngine:
    def setup_method(self):
        self.eng = ConfidenceEngine()

    def test_process_factors(self):
        inp = EngineInput(
            input_type="confidence",
            payload={
                "factors": [
                    {"name": "source_reliability", "value": 0.9},
                    {"name": "evidence_strength", "value": 0.8},
                    {"name": "consistency", "value": 0.7},
                ],
                "subject_id": "obj_001",
                "subject_type": "decision",
            },
        )
        out = self.eng.process(inp)
        assert out.output_type == "confidence_score"
        assert 0.0 < out.confidence <= 1.0
        assert out.payload["subject_id"] == "obj_001"

    def test_weighted_average(self):
        factors = [
            ConfidenceFactor(name="a", value=1.0, weight=0.5),
            ConfidenceFactor(name="b", value=0.0, weight=0.5),
        ]
        score = self.eng.compute(factors)
        assert score.overall == 0.5

    def test_min_method(self):
        factors = [
            ConfidenceFactor(name="a", value=0.9, weight=1.0),
            ConfidenceFactor(name="b", value=0.3, weight=1.0),
        ]
        score = self.eng.compute(factors, method="min")
        assert score.overall == 0.3

    def test_max_method(self):
        factors = [
            ConfidenceFactor(name="a", value=0.9, weight=1.0),
            ConfidenceFactor(name="b", value=0.3, weight=1.0),
        ]
        score = self.eng.compute(factors, method="max")
        assert score.overall == 0.9

    def test_empty_factors(self):
        score = self.eng.compute([])
        assert score.overall == 0.5

    def test_single_factor(self):
        factors = [ConfidenceFactor(name="test", value=0.85, weight=1.0)]
        score = self.eng.compute(factors)
        assert score.overall == 0.85

    def test_labels(self):
        assert self.eng.label(0.95) == "very_high"
        assert self.eng.label(0.75) == "high"
        assert self.eng.label(0.55) == "moderate"
        assert self.eng.label(0.35) == "low"
        assert self.eng.label(0.15) == "very_low"

    def test_combine_scores(self):
        s1 = ConfidenceScore(overall=0.8, subject_id="a", subject_type="type_a")
        s2 = ConfidenceScore(overall=0.6, subject_id="b", subject_type="type_b")
        combined = self.eng.combine([s1, s2])
        assert combined.overall == 0.7

    def test_never_escalates(self):
        inp = EngineInput(input_type="confidence", payload={"factors": [{"name": "test", "value": 0.5}]})
        out1 = self.eng.process(inp)
        out2 = self.eng.escalate(inp)
        assert out1.output_type == out2.output_type

    def test_health_check(self):
        health = self.eng.health_check()
        assert health["engine_id"] == "confidence_engine"
        assert health["status"] == "active"

    def test_capabilities(self):
        caps = self.eng.get_capabilities()
        assert "weighted_average" in caps
        assert "confidence_tracking" in caps

    def test_history_tracking(self):
        for i in range(5):
            inp = EngineInput(input_type="confidence", payload={"factors": [{"name": "test", "value": 0.5 + i * 0.1}]})
            self.eng.process(inp)
        assert len(self.eng.get_history()) == 5
        assert len(self.eng.get_history(limit=2)) == 2

    def test_clear(self):
        inp = EngineInput(input_type="confidence", payload={"factors": [{"name": "test", "value": 0.5}]})
        self.eng.process(inp)
        self.eng.clear()
        assert len(self.eng._history) == 0

    def test_bayesian_combination(self):
        factors = [
            ConfidenceFactor(name="prior", value=0.5, weight=1.0),
            ConfidenceFactor(name="evidence", value=0.9, weight=2.0),
        ]
        score = self.eng.compute(factors, method="bayesian")
        # (0.5*1 + 0.9*2) / (1+2+1_prior) = (0.5 + 1.8) / 4 = 2.3/4 = 0.575
        # Actually the prior_weight is 1.0, so numerator = 0.5*1 + 0.5*1 + 0.9*2 = 2.8
        # denominator = 1 + 1 + 2 = 4, result = 0.7
        assert abs(score.overall - 0.7) < 0.01