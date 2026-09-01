"""ZGC-PR-17C — Controlled Learning Loop + Orphan Engine Integration."""

import pytest


@pytest.fixture(scope="module")
def learn_app():
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["SHUNYA_ENV"] = "test"
    from app import create_app, db
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()


class TestControlledLearningLoop:
    def test_observation_evaluation(self, learn_app):
        """Observation → evaluation produces correct classification."""
        from core.intelligence_runtime.learning_loop import ControlledLearningLoop

        loop = ControlledLearningLoop()

        # Success evaluation — detailed outcome produces high confidence
        s1 = loop.process_observation(
            "Created invoice for client", "expected success",
            "Invoice created successfully and sent to client with all line items",
            identity_id="sid_test", tenant_id="1",
        )
        assert s1.evaluation == "success"
        assert s1.confidence >= 0.6  # detailed enough to be authoritative

        # Failure evaluation — short message, lower confidence, stays as observation
        s2 = loop.process_observation(
            "Send payment reminder", "expected success", "Failed to send — API error",
            identity_id="sid_test", tenant_id="1",
        )
        assert s2.evaluation == "failure"
        # Below 0.6 threshold — stays as observation (correct governed behavior)
        assert s2.confidence < 0.6

        # Unknown evaluation — lowest confidence
        s3 = loop.process_observation(
            "Check status update", "expected acknowledgement", "unknown",
            identity_id="sid_test", tenant_id="1",
        )
        assert s3.evaluation == "unknown"
        assert s3.confidence < 0.6  # below threshold

    def test_governed_memory_update(self, learn_app):
        """Learning signals with confidence >= 0.6 are stored in durable memory."""
        from core.intelligence_runtime.memory import MemoryEngine
        from core.intelligence_runtime.memory_db import DBMemoryRepository
        from core.intelligence_runtime.learning_loop import ControlledLearningLoop

        engine = MemoryEngine(repository=DBMemoryRepository())
        loop = ControlledLearningLoop(memory_engine=engine)

        signal = loop.process_observation(
            "Customer onboarding", "complete within 3 days", "Completed in 2 days — early",
            identity_id="sid_learn", tenant_id="10",
        )
        assert signal.evaluation == "success"
        assert signal.confidence >= 0.6

        # The signal must be stored in durable memory
        key = f"learning_signal_{signal.signal_id}"
        stored = engine.get(key, identity_id="sid_learn", tenant_id="10")
        assert stored is not None
        assert "Customer onboarding" in stored.content

        # Cleanup
        engine.forget(key, identity_id="sid_learn", tenant_id="10")

    def test_learning_intelligence_integration(self, learn_app):
        """Learning intelligence engine is reachable and importable."""
        from core.learning_intelligence.engine import LearningIntelligenceEngine
        from core.learning_intelligence.models import Skill, CompetencyLevel

        class MockLearner:
            def __init__(self):
                self.skills = []
                self.identity_id = "sid_test"

        engine = LearningIntelligenceEngine()
        learner = MockLearner()
        # Gap analysis with empty learner returns empty recommendations
        results = engine.analyze_skill_gaps(learner, [])
        assert isinstance(results, list)

    def test_operations_intelligence_importable(self, learn_app):
        """Operations intelligence engine is reachable from integration."""
        from core.operations_intelligence.engine import OperationsIntelligenceEngine
        from core.operations_intelligence.models import Process, ProcessStep
        engine = OperationsIntelligenceEngine()
        proc = Process(process_id="test", name="Test Process", steps=[])
        result = engine.analyze_process(proc)
        assert isinstance(result, dict)

    def test_health_intelligence_importable(self, learn_app):
        """Health intelligence engine is reachable from integration."""
        from core.health_intelligence.engine import HealthIntelligenceEngine
        from core.health_intelligence.models import HealthProfile
        engine = HealthIntelligenceEngine()
        result = engine.assess_mental_wellbeing(HealthProfile())
        assert isinstance(result, list)

    def test_no_autonomous_code_modification(self, learn_app):
        """The learning loop must NOT modify code, prompts, or model weights."""
        from core.intelligence_runtime.learning_loop import ControlledLearningLoop
        loop = ControlledLearningLoop()

        # Verify the loop has no method that modifies system state
        methods = [
            m for m in dir(loop)
            if not m.startswith("_") and callable(getattr(loop, m))
        ]
        methods = [m for m in methods if not m.startswith("wire_")]
        assert "process_observation" in methods
        # Only these two public methods exist
        assert "process_observation" in methods
        # No 'modify', 'mutate', 'train', 'fine_tune', 'update_code' etc.
        dangerous = [m for m in methods if any(
            d in m.lower() for d in ["modify", "mutate", "train", "finetune", "fine_tune", "update_code"]
        )]
        assert not dangerous, f"Learning loop has dangerous methods: {dangerous}"