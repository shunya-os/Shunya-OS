"""
SHUNYA — Reflection Engine Tests

Tests for the Reflection Engine covering:
- Outcome comparison
- Anomaly detection (threshold-based)
- Success score computation
- Improvement signal generation
- Engine interface compliance
- Full reflection cycle
"""
import pytest

from core.intelligence.models import EngineInput
from core.intelligence.reflection import (
    DEFAULT_ANOMALY_THRESHOLDS,
    DEFAULT_REFLECTION_WEIGHTS,
    Anomaly,
    AnomalySeverity,
    ImprovementSignal,
    ImprovementSignalCategory,
    OutcomeComparison,
    ReflectionEngine,
    ReflectionRecord,
)

# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def engine() -> ReflectionEngine:
    """Create a fresh ReflectionEngine for each test."""
    return ReflectionEngine()


@pytest.fixture
def sample_expected() -> dict:
    """Sample expected outcome for a decision."""
    return {
        "cost": 50000,
        "timing": "on_time",
        "quality": "high",
        "efficiency": 0.85,
    }


@pytest.fixture
def sample_actual() -> dict:
    """Sample actual outcome with slight deviations."""
    return {
        "cost": 52000,
        "timing": "on_time",
        "quality": "medium",
        "efficiency": 0.75,
    }


# ── Outcome Comparison ──────────────────────────────────────────────────────────


class TestOutcomeComparison:
    """Test outcome comparison logic."""

    def test_exact_match(self, engine: ReflectionEngine):
        """Test that exact matches produce no deviation."""
        comparisons = engine.compare_outcomes(
            {"cost": 100, "status": "done"},
            {"cost": 100, "status": "done"},
        )
        assert len(comparisons) == 2
        for c in comparisons:
            assert c.within_tolerance
            assert c.deviation_pct == 0.0

    def test_numeric_deviation(self, engine: ReflectionEngine):
        """Test that numeric deviations are computed correctly."""
        comparisons = engine.compare_outcomes(
            {"cost": 1000},
            {"cost": 1100},
        )
        assert len(comparisons) == 1
        c = comparisons[0]
        assert c.deviation == 100.0
        assert c.deviation_pct == 0.1  # 10% deviation
        assert not c.within_tolerance

    def test_non_numeric_mismatch(self, engine: ReflectionEngine):
        """Test that non-numeric mismatches are flagged."""
        comparisons = engine.compare_outcomes(
            {"status": "success"},
            {"status": "failure"},
        )
        c = comparisons[0]
        assert not c.within_tolerance
        assert c.deviation == 1.0

    def test_custom_tolerances(self, engine: ReflectionEngine):
        """Test that custom tolerances are respected."""
        comparisons = engine.compare_outcomes(
            {"cost": 1000},
            {"cost": 1050},
            tolerances={"cost": 100.0},  # Allow up to 100 deviation
        )
        assert comparisons[0].within_tolerance
        assert comparisons[0].tolerance == 100.0

    def test_missing_keys(self, engine: ReflectionEngine):
        """Test that missing keys in actual are flagged."""
        comparisons = engine.compare_outcomes(
            {"cost": 100, "status": "done"},
            {"cost": 100},  # 'status' missing
        )
        assert len(comparisons) == 2
        status_comp = next(c for c in comparisons if c.dimension == "status")
        assert not status_comp.within_tolerance

    def test_unexpected_keys(self, engine: ReflectionEngine):
        """Test that unexpected keys in actual are flagged."""
        comparisons = engine.compare_outcomes(
            {"cost": 100},
            {"cost": 100, "extra": "unexpected"},
        )
        assert len(comparisons) == 2
        extra_comp = next(c for c in comparisons if c.dimension == "extra")
        assert not extra_comp.within_tolerance

    def test_zero_expected_value(self, engine: ReflectionEngine):
        """Test comparison when expected value is zero."""
        comparisons = engine.compare_outcomes(
            {"cost": 0},
            {"cost": 50},
        )
        c = comparisons[0]
        # When expected is 0, deviation_pct = deviation (absolute)
        assert c.deviation_pct == 50.0
        assert not c.within_tolerance


# ── Anomaly Detection ────────────────────────────────────────────────────────────


class TestAnomalyDetection:
    """Test anomaly detection logic."""

    def test_no_anomalies_when_within_tolerance(self, engine: ReflectionEngine):
        """Test that no anomalies are detected when all within tolerance."""
        comparisons = [
            OutcomeComparison(
                dimension="cost",
                expected=100, actual=100,
                deviation=0, deviation_pct=0.0,
                within_tolerance=True, tolerance=0,
            ),
        ]
        anomalies = engine.detect_anomalies(comparisons)
        assert len(anomalies) == 0

    def test_info_anomaly(self, engine: ReflectionEngine):
        """Test detection of info-level anomaly."""
        comparisons = [
            OutcomeComparison(
                dimension="cost",
                expected=100, actual=105,
                deviation=5, deviation_pct=0.05,
                within_tolerance=False, tolerance=0,
            ),
        ]
        anomalies = engine.detect_anomalies(comparisons)
        # 5% deviation is below info threshold (10%) for default thresholds
        assert len(anomalies) == 1
        assert anomalies[0].severity == AnomalySeverity.INFO

    def test_warning_anomaly(self, engine: ReflectionEngine):
        """Test detection of warning-level anomaly."""
        comparisons = [
            OutcomeComparison(
                dimension="cost",
                expected=100, actual=130,
                deviation=30, deviation_pct=0.30,
                within_tolerance=False, tolerance=0,
            ),
        ]
        anomalies = engine.detect_anomalies(comparisons)
        assert len(anomalies) == 1
        assert anomalies[0].severity == AnomalySeverity.WARNING

    def test_error_anomaly(self, engine: ReflectionEngine):
        """Test detection of error-level anomaly."""
        comparisons = [
            OutcomeComparison(
                dimension="cost",
                expected=100, actual=160,
                deviation=60, deviation_pct=0.60,
                within_tolerance=False, tolerance=0,
            ),
        ]
        anomalies = engine.detect_anomalies(comparisons)
        assert len(anomalies) == 1
        assert anomalies[0].severity == AnomalySeverity.ERROR

    def test_critical_anomaly(self, engine: ReflectionEngine):
        """Test detection of critical-level anomaly."""
        comparisons = [
            OutcomeComparison(
                dimension="cost",
                expected=100, actual=200,
                deviation=100, deviation_pct=1.0,
                within_tolerance=False, tolerance=0,
            ),
        ]
        anomalies = engine.detect_anomalies(comparisons)
        assert len(anomalies) == 1
        assert anomalies[0].severity == AnomalySeverity.CRITICAL

    def test_anomalies_sorted_by_severity(self, engine: ReflectionEngine):
        """Test that anomalies are sorted by severity (most severe first)."""
        comparisons = [
            OutcomeComparison(
                dimension="small", expected=100, actual=105,
                deviation=5, deviation_pct=0.05,
                within_tolerance=False, tolerance=0,
            ),
            OutcomeComparison(
                dimension="big", expected=100, actual=200,
                deviation=100, deviation_pct=1.0,
                within_tolerance=False, tolerance=0,
            ),
        ]
        anomalies = engine.detect_anomalies(comparisons)
        assert len(anomalies) == 2
        # Most severe first
        assert anomalies[0].severity == AnomalySeverity.CRITICAL
        assert anomalies[1].severity == AnomalySeverity.INFO

    def test_custom_thresholds(self, engine: ReflectionEngine):
        """Test that custom anomaly thresholds work."""
        engine.set_anomaly_thresholds({
            "info": 0.01,
            "warning": 0.05,
            "error": 0.10,
            "critical": 0.20,
        })
        comparisons = [
            OutcomeComparison(
                dimension="cost",
                expected=100, actual=103,
                deviation=3, deviation_pct=0.03,
                within_tolerance=False, tolerance=0,
            ),
        ]
        anomalies = engine.detect_anomalies(comparisons)
        # 3% deviation exceeds info (1%) and warning (5%)... wait, 3% < 5% so it's info
        assert len(anomalies) == 1
        assert anomalies[0].severity == AnomalySeverity.INFO


# ── Success Score ────────────────────────────────────────────────────────────────


class TestSuccessScore:
    """Test success score computation."""

    def test_perfect_score(self, engine: ReflectionEngine):
        """Test that perfect matches yield 1.0 score."""
        comparisons = [
            OutcomeComparison(
                dimension="cost", expected=100, actual=100,
                deviation=0, deviation_pct=0.0,
                within_tolerance=True, tolerance=0,
            ),
            OutcomeComparison(
                dimension="timing", expected="on_time", actual="on_time",
                deviation=0, deviation_pct=0.0,
                within_tolerance=True, tolerance=0,
            ),
        ]
        components = engine.compute_success_score(comparisons)
        assert components.overall_score == 1.0

    def test_partial_score(self, engine: ReflectionEngine):
        """Test that partial matches yield intermediate scores."""
        comparisons = [
            OutcomeComparison(
                dimension="quality", expected="high", actual="high",
                deviation=0, deviation_pct=0.0,
                within_tolerance=True, tolerance=0,
            ),
            OutcomeComparison(
                dimension="accuracy", expected=1.0, actual=0.5,
                deviation=0.5, deviation_pct=0.5,
                within_tolerance=False, tolerance=0,
            ),
        ]
        components = engine.compute_success_score(comparisons)
        # quality=1.0 (weight=0.20), accuracy=0.5 (weight=0.30)
        # Overall = (1.0*0.20 + 0.5*0.30) / 0.50 = 0.35 / 0.50 = 0.70
        assert components.overall_score == pytest.approx(0.70, rel=0.01)

    def test_custom_weights(self, engine: ReflectionEngine):
        """Test that custom weights affect the score."""
        comparisons = [
            OutcomeComparison(
                dimension="cost", expected=100, actual=100,
                deviation=0, deviation_pct=0.0,
                within_tolerance=True, tolerance=0,
            ),
            OutcomeComparison(
                dimension="quality", expected="high", actual="low",
                deviation=1, deviation_pct=1.0,
                within_tolerance=False, tolerance=0,
            ),
        ]
        # Weight cost at 0.9, quality at 0.1
        components = engine.compute_success_score(
            comparisons, weights={"cost": 0.9, "quality": 0.1}
        )
        # cost=1.0*0.9 + quality=0.0*0.1 = 0.9
        assert components.overall_score == pytest.approx(0.9, rel=0.01)

    def test_empty_comparisons(self, engine: ReflectionEngine):
        """Test that empty comparisons yield 0.0 score."""
        components = engine.compute_success_score([])
        assert components.overall_score == 0.0
        assert components.dimension_scores == {}

    def test_dimension_not_in_weights(self, engine: ReflectionEngine):
        """Test that dimensions not in weights are excluded."""
        comparisons = [
            OutcomeComparison(
                dimension="unknown_metric", expected=100, actual=200,
                deviation=100, deviation_pct=1.0,
                within_tolerance=False, tolerance=0,
            ),
        ]
        components = engine.compute_success_score(comparisons)
        # 'unknown_metric' is not in default weights, so excluded
        assert components.overall_score == 0.0
        assert components.dimension_scores == {}


# ── Improvement Signals ──────────────────────────────────────────────────────────


class TestImprovementSignals:
    """Test improvement signal generation."""

    def test_signals_from_anomalies(self, engine: ReflectionEngine):
        """Test that anomaly-based signals are generated."""
        reflection = ReflectionRecord(
            subject_id="decision_1",
            subject_type="decision",
            anomalies=[
                Anomaly(
                    anomaly_id="a1", field="cost",
                    expected_value=100, actual_value=200,
                    deviation=1.0, severity=AnomalySeverity.ERROR,
                    description="Cost doubled",
                ),
            ],
        )
        signals = engine.generate_improvement_signals(reflection)
        assert len(signals) == 1
        assert signals[0].category == ImprovementSignalCategory.OTHER
        assert signals[0].priority == 7  # ERROR = 7

    def test_info_anomalies_do_not_generate_signals(self, engine: ReflectionEngine):
        """Test that info-level anomalies don't generate signals."""
        reflection = ReflectionRecord(
            subject_id="decision_1", subject_type="decision",
            anomalies=[
                Anomaly(
                    anomaly_id="a1", field="cost",
                    expected_value=100, actual_value=102,
                    deviation=0.02, severity=AnomalySeverity.INFO,
                    description="Minor deviation",
                ),
            ],
        )
        signals = engine.generate_improvement_signals(reflection)
        assert len(signals) == 0

    def test_signal_category_inference(self, engine: ReflectionEngine):
        """Test that signal categories are inferred from field names."""
        reflection = ReflectionRecord(
            subject_id="decision_1", subject_type="decision",
            anomalies=[
                Anomaly(
                    anomaly_id="a1", field="cost",
                    expected_value=100, actual_value=200,
                    deviation=1.0, severity=AnomalySeverity.ERROR,
                    description="Cost issue",
                ),
                Anomaly(
                    anomaly_id="a2", field="timing",
                    expected_value="on_time", actual_value="late",
                    deviation=1.0, severity=AnomalySeverity.ERROR,
                    description="Timing issue",
                ),
                Anomaly(
                    anomaly_id="a3", field="knowledge_gap",
                    expected_value="known", actual_value="unknown",
                    deviation=1.0, severity=AnomalySeverity.WARNING,
                    description="Knowledge issue",
                ),
                Anomaly(
                    anomaly_id="a4", field="process_step",
                    expected_value="complete", actual_value="incomplete",
                    deviation=1.0, severity=AnomalySeverity.WARNING,
                    description="Process issue",
                ),
            ],
        )
        signals = engine.generate_improvement_signals(reflection)
        categories = {s.category for s in signals}
        assert ImprovementSignalCategory.OTHER in categories
        assert ImprovementSignalCategory.TIMING in categories
        assert ImprovementSignalCategory.KNOWLEDGE in categories
        assert ImprovementSignalCategory.PROCESS in categories


# ── Full Reflection Cycle ────────────────────────────────────────────────────────


class TestFullReflection:
    """Test the complete reflection cycle."""

    @pytest.mark.asyncio
    async def test_full_reflection(
        self,
        engine: ReflectionEngine,
        sample_expected: dict,
        sample_actual: dict,
    ):
        """Test the full reflect process()."""
        result = await engine.process(EngineInput(
            input_type="reflect",
            payload={
                "subject_id": "decision_abc_123",
                "subject_type": "decision",
                "subject_label": "Vendor payment approval",
                "expected_outcome": sample_expected,
                "actual_outcome": sample_actual,
            },
        ))

        assert result.payload["reflection_id"]
        assert result.payload["subject_id"] == "decision_abc_123"
        assert 0 < result.payload["success_score"] < 1.0
        assert len(result.payload["comparisons"]) == 4
        assert len(result.payload["anomalies"]) > 0
        assert len(result.payload["signals"]) > 0
        assert result.deterministic
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_reflection_missing_subject_id(self, engine: ReflectionEngine):
        """Test that reflection without subject_id fails."""
        result = await engine.process(EngineInput(
            input_type="reflect",
            payload={
                "expected_outcome": {"cost": 100},
                "actual_outcome": {"cost": 110},
            },
        ))
        assert "error" in result.payload

    @pytest.mark.asyncio
    async def test_reflection_missing_expected(self, engine: ReflectionEngine):
        """Test that reflection without expected_outcome fails."""
        result = await engine.process(EngineInput(
            input_type="reflect",
            payload={"subject_id": "test"},
        ))
        assert "error" in result.payload

    @pytest.mark.asyncio
    async def test_compare_outcomes_handler(
        self,
        engine: ReflectionEngine,
        sample_expected: dict,
        sample_actual: dict,
    ):
        """Test the compare_outcomes input handler."""
        result = await engine.process(EngineInput(
            input_type="compare_outcomes",
            payload={
                "expected_outcome": sample_expected,
                "actual_outcome": sample_actual,
            },
        ))
        assert result.payload["total_dimensions"] == 4
        assert "comparisons" in result.payload

    @pytest.mark.asyncio
    async def test_detect_anomalies_handler(self, engine: ReflectionEngine):
        """Test the detect_anomalies input handler."""
        comparisons = engine.compare_outcomes(
            {"cost": 1000}, {"cost": 2000}
        )
        result = await engine.process(EngineInput(
            input_type="detect_anomalies",
            payload={
                "comparisons": [vars(c) for c in comparisons],
            },
        ))
        assert result.payload["total_anomalies"] == 1
        assert result.payload["has_critical"]

    @pytest.mark.asyncio
    async def test_compute_success_score_handler(self, engine: ReflectionEngine):
        """Test the compute_success_score input handler."""
        comparisons = engine.compare_outcomes(
            {"cost": 100, "timing": "on_time"},
            {"cost": 100, "timing": "on_time"},
        )
        result = await engine.process(EngineInput(
            input_type="compute_success_score",
            payload={
                "comparisons": [vars(c) for c in comparisons],
            },
        ))
        assert result.payload["overall_score"] == 1.0

    @pytest.mark.asyncio
    async def test_generate_signals_handler(self, engine: ReflectionEngine):
        """Test the generate_signals input handler."""
        result = await engine.process(EngineInput(
            input_type="generate_signals",
            payload={
                "subject_id": "test_decision",
                "subject_type": "decision",
                "anomalies": [
                    {
                        "field": "cost",
                        "expected_value": 100,
                        "actual_value": 200,
                        "deviation": 1.0,
                        "severity": "error",
                    },
                ],
            },
        ))
        assert result.payload["total_signals"] > 0


# ── Engine Interface ────────────────────────────────────────────────────────────


class TestEngineInterface:
    """Test the ReflectionEngine's IntelligenceEngine interface compliance."""

    def test_get_capabilities(self, engine: ReflectionEngine):
        """Test that capabilities are returned."""
        caps = engine.get_capabilities()
        assert isinstance(caps, list)
        assert len(caps) > 0
        assert "reflect" in caps
        assert "compare_outcomes" in caps
        assert "detect_anomalies" in caps

    def test_health_check(self, engine: ReflectionEngine):
        """Test health check returns valid status."""
        health = engine.health_check()
        assert health["engine_id"] == "reflection_engine"
        assert health["engine_type"] == "reflection"
        assert health["status"] in ("active", "degraded", "offline")
        assert "total_reflections" in health
        assert "dimension_weights" in health
        assert "anomaly_thresholds" in health

    def test_escalate(self, engine: ReflectionEngine):
        """Test that escalation produces a valid result."""
        result = engine.escalate(EngineInput(
            input_type="reflect",
            payload={
                "subject_id": "decision_1",
                "subject_label": "Test",
                "expected_outcome": {"cost": 100},
                "actual_outcome": {"cost": 120},
            },
        ))
        assert result.input_type == "reflect"
        assert result.prompt
        assert "Test" in result.prompt
        assert "cost" in result.prompt

    @pytest.mark.asyncio
    async def test_unknown_input_type(self, engine: ReflectionEngine):
        """Test that unknown input types return an error."""
        result = await engine.process(EngineInput(
            input_type="nonexistent",
            payload={},
        ))
        assert "error" in result.payload

    @pytest.mark.asyncio
    async def test_importable(self):
        """Test that the engine is importable from the expected path."""
        from core.intelligence.reflection import ReflectionEngine
        assert ReflectionEngine is not None


# ── Configuration ────────────────────────────────────────────────────────────────


class TestConfiguration:
    """Test engine configuration."""

    def test_set_dimension_weights(self, engine: ReflectionEngine):
        """Test that dimension weights can be updated."""
        engine.set_dimension_weights({"accuracy": 1.0})
        assert engine._dimension_weights == {"accuracy": 1.0}

    def test_set_dimension_weights_empty(self, engine: ReflectionEngine):
        """Test that empty weights raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.set_dimension_weights({})

    def test_set_dimension_weights_invalid(self, engine: ReflectionEngine):
        """Test that invalid weights raise ValueError."""
        with pytest.raises(ValueError, match="must be in"):
            engine.set_dimension_weights({"x": 1.5})

    def test_set_anomaly_thresholds(self, engine: ReflectionEngine):
        """Test that anomaly thresholds can be updated."""
        engine.set_anomaly_thresholds({
            "info": 0.05, "warning": 0.15,
            "error": 0.30, "critical": 0.50,
        })
        assert engine._anomaly_thresholds["info"] == 0.05
        assert engine._anomaly_thresholds["critical"] == 0.50

    def test_set_anomaly_thresholds_missing_keys(self, engine: ReflectionEngine):
        """Test that missing keys raise ValueError."""
        with pytest.raises(ValueError, match="must include all"):
            engine.set_anomaly_thresholds({"info": 0.1})


# ── Reflection Retrieval ────────────────────────────────────────────────────────


class TestReflectionRetrieval:
    """Test reflection record retrieval and listing."""

    @pytest.mark.asyncio
    async def test_get_reflection(self, engine: ReflectionEngine):
        """Test retrieving a reflection by ID."""
        result = await engine.process(EngineInput(
            input_type="reflect",
            payload={
                "subject_id": "decision_1",
                "subject_type": "decision",
                "expected_outcome": {"cost": 100},
                "actual_outcome": {"cost": 105},
            },
        ))
        rid = result.payload["reflection_id"]

        reflection = engine.get_reflection(rid)
        assert reflection is not None
        assert reflection.subject_id == "decision_1"

    def test_get_nonexistent_reflection(self, engine: ReflectionEngine):
        """Test that getting a nonexistent reflection returns None."""
        assert engine.get_reflection("nonexistent") is None

    @pytest.mark.asyncio
    async def test_list_reflections(self, engine: ReflectionEngine):
        """Test listing reflections with filters."""
        # Create two reflections
        await engine.process(EngineInput(
            input_type="reflect",
            payload={
                "subject_id": "decision_a", "subject_type": "decision",
                "expected_outcome": {"cost": 100},
                "actual_outcome": {"cost": 100},
            },
        ))
        await engine.process(EngineInput(
            input_type="reflect",
            payload={
                "subject_id": "decision_b", "subject_type": "plan",
                "expected_outcome": {"cost": 200},
                "actual_outcome": {"cost": 300},
            },
        ))

        reflections = engine.list_reflections()
        assert len(reflections) == 2

        reflections = engine.list_reflections(subject_type="decision")
        assert len(reflections) == 1

        reflections = engine.list_reflections(has_anomalies=True)
        assert len(reflections) == 1  # decision_b has anomaly

        reflections = engine.list_reflections(has_anomalies=False)
        assert len(reflections) == 1  # decision_a has no anomaly

    def test_reflection_count(self, engine: ReflectionEngine):
        """Test total reflection count."""
        assert engine.get_reflection_count() == 0
        engine._reflections["r1"] = ReflectionRecord(
            subject_id="test", subject_type="decision"
        )
        assert engine.get_reflection_count() == 1


# ── Model Tests ─────────────────────────────────────────────────────────────────


class TestModels:
    """Test the reflection model classes."""

    def test_reflection_record_auto_id(self):
        """Test that reflection records auto-generate IDs."""
        record = ReflectionRecord(subject_id="test", subject_type="decision")
        assert record.reflection_id
        assert record.timestamp

    def test_has_anomalies_property(self):
        """Test the has_anomalies property."""
        record = ReflectionRecord(subject_id="test", subject_type="decision")
        assert not record.has_anomalies
        record.anomalies.append(Anomaly(
            field="cost", deviation=0.5, severity=AnomalySeverity.ERROR
        ))
        assert record.has_anomalies

    def test_has_improvement_signals_property(self):
        """Test the has_improvement_signals property."""
        record = ReflectionRecord(subject_id="test", subject_type="decision")
        assert not record.has_improvement_signals
        record.improvement_signals.append(ImprovementSignal(
            category=ImprovementSignalCategory.PROCESS,
            description="Test",
            priority=5,
        ))
        assert record.has_improvement_signals

    def test_default_weights_sum_to_one(self):
        """Test that default weights sum to 1.0."""
        total = sum(DEFAULT_REFLECTION_WEIGHTS.values())
        assert total == pytest.approx(1.0, rel=0.01)

    def test_default_thresholds_have_all_levels(self):
        """Test that default thresholds include all severity levels."""
        assert "info" in DEFAULT_ANOMALY_THRESHOLDS
        assert "warning" in DEFAULT_ANOMALY_THRESHOLDS
        assert "error" in DEFAULT_ANOMALY_THRESHOLDS
        assert "critical" in DEFAULT_ANOMALY_THRESHOLDS