"""Tests for Milestone 8 — Executive Intelligence.

Covers:
- Reasoning trace creation, retrieval, correction
- Learning feedback loop
- Anomaly detection
- Confidence scoring
- API endpoints
- Regression tests for M1–M7
"""
from __future__ import annotations


def _make_identity(app):
    from app.adapters.os_adapter import sign_in
    result = sign_in(email="m8@shunyaos.com", name="M8 Test")
    assert result["success"]
    return result["identity_id"]

def _seed_m8_data(app, identity_id):
    from app import db
    from app.founder.models import FounderConversation, FounderMessage, FounderObject, FounderSpace
    space = FounderSpace(space_id="m8_spc", name="M8 Space", identity_id=identity_id)
    db.session.add(space)
    db.session.flush()
    obj = FounderObject(object_id="m8_obj", space_id="m8_spc", name="M8 Object",
                        object_type="Document", content="Test data for M8.", created_by=identity_id)
    db.session.add(obj)
    db.session.flush()
    conv = FounderConversation(conv_id="m8_conv", object_id="m8_obj", title="M8 Conv", identity_id=identity_id)
    db.session.add(conv)
    db.session.flush()
    db.session.add(FounderMessage(conv_id="m8_conv", role="human", content="Test question"))
    db.session.add(FounderMessage(conv_id="m8_conv", role="assistant", content="Test answer"))
    db.session.commit()


# ===========================================================================
# 1. Reasoning Traces
# ===========================================================================

class TestReasoningTraces:
    """Reasoning trace creation, retrieval, correction."""

    def test_create_trace(self, app):
        identity_id = _make_identity(app)
        _seed_m8_data(app, identity_id)
        from app.intelligence.service import create_reasoning_trace
        trace = create_reasoning_trace(
            identity_id=identity_id,
            reasoning_type="analysis",
            query="What is the status of M8 Object?",
            ai_response="M8 Object is a Document with active conversation.",
            context_summary="Test context",
            object_id="m8_obj",
            reasoning_chain=[{"step": "identity_resolution", "data": {"id": identity_id}}],
            sources=[{"type": "object", "id": "m8_obj", "field": "name"}],
            confidence_score=0.85,
            execution_time_ms=120,
        )
        assert trace.trace_id is not None
        assert trace.reasoning_type == "analysis"
        assert trace.confidence_score == 0.85

    def test_get_traces(self, app):
        identity_id = _make_identity(app)
        _seed_m8_data(app, identity_id)
        from app.intelligence.service import create_reasoning_trace, get_traces
        create_reasoning_trace(identity_id=identity_id, reasoning_type="analysis",
                                query="Q1", ai_response="A1")
        create_reasoning_trace(identity_id=identity_id, reasoning_type="summary",
                                query="Q2", ai_response="A2")
        traces = get_traces(identity_id=identity_id)
        assert len(traces) >= 2

    def test_get_trace_by_id(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import create_reasoning_trace, get_trace
        t = create_reasoning_trace(identity_id=identity_id, reasoning_type="test",
                                    query="Q", ai_response="A")
        fetched = get_trace(trace_id=t.trace_id)
        assert fetched is not None
        assert fetched["query_text"] == "Q"

    def test_trace_filter_by_object(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import create_reasoning_trace, get_traces
        create_reasoning_trace(identity_id=identity_id, reasoning_type="test",
                                query="Q", ai_response="A", object_id="obj_a")
        create_reasoning_trace(identity_id=identity_id, reasoning_type="test",
                                query="Q2", ai_response="A2", object_id="obj_b")
        traces_a = get_traces(identity_id=identity_id, object_id="obj_a")
        assert len(traces_a) == 1

    def test_correct_trace(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import (
            correct_trace,
            create_reasoning_trace,
            get_trace,
        )
        t = create_reasoning_trace(identity_id=identity_id, reasoning_type="test",
                                    query="Q", ai_response="Wrong answer")
        result = correct_trace(trace_id=t.trace_id, corrected_response="Corrected answer")
        assert result is True
        updated = get_trace(trace_id=t.trace_id)
        assert updated["is_corrected"] is True
        assert updated["corrected_response"] == "Corrected answer"

    def test_correct_nonexistent_trace(self, app):
        from app.intelligence.service import correct_trace
        assert correct_trace(trace_id="nonexistent", corrected_response="X") is False

    def test_trace_not_found(self, app):
        from app.intelligence.service import get_trace
        assert get_trace(trace_id="nonexistent") is None


# ===========================================================================
# 2. Learning Feedback
# ===========================================================================

class TestLearningFeedback:
    """Learning event recording and history."""

    def test_record_learning(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import get_learning_history, record_learning
        record_learning(
            identity_id=identity_id,
            learning_type="correction",
            trigger_summary="Corrected status assessment",
            before_state={"status": "wrong"},
            after_state={"status": "correct"},
            outcome="positive",
        )
        history = get_learning_history(identity_id=identity_id)
        assert len(history) >= 1
        assert history[0]["learning_type"] == "correction"

    def test_learning_summary(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import get_learning_summary, record_learning
        record_learning(identity_id=identity_id, learning_type="validation",
                        trigger_summary="Validated prediction", outcome="positive")
        summary = get_learning_summary(identity_id=identity_id)
        assert summary["total_learnings"] >= 1
        assert "corrections_received" in summary


# ===========================================================================
# 3. Anomaly Detection
# ===========================================================================

class TestAnomalyDetection:
    """Anomaly detection rules."""

    def test_detect_no_anomalies_empty(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import detect_anomalies
        result = detect_anomalies(identity_id=identity_id)
        assert isinstance(result, list)

    def test_detect_anomalies_with_data(self, app):
        identity_id = _make_identity(app)
        from app import db
        from datetime import datetime, timedelta
        from app.founder.models import FounderConversation, FounderMessage, FounderObject, FounderSpace

        # Create stale data
        old = datetime.utcnow() - timedelta(days=30)
        space = FounderSpace(space_id="m8a_spc", name="M8A", identity_id=identity_id)
        db.session.add(space)
        db.session.flush()
        obj = FounderObject(object_id="m8a_obj", space_id="m8a_spc", name="Stale Object",
                            object_type="Document", created_by=identity_id,
                            created_at=old, updated_at=old)
        db.session.add(obj)
        db.session.flush()
        conv = FounderConversation(conv_id="m8a_conv", object_id="m8a_obj", title="Stale Conv",
                                   identity_id=identity_id)
        db.session.add(conv)
        db.session.flush()
        db.session.add(FounderMessage(conv_id="m8a_conv", role="human", content="Old message"))
        db.session.commit()

        from app.intelligence.service import detect_anomalies
        result = detect_anomalies(identity_id=identity_id)
        assert len(result) >= 1
        types = [a["anomaly_type"] for a in result]
        assert "status_stall" in types

    def test_get_anomalies(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import get_anomalies
        result = get_anomalies(identity_id=identity_id)
        assert isinstance(result, list)

    def test_resolve_anomaly(self, app):
        from app.intelligence.service import create_reasoning_trace
        identity_id = _make_identity(app)
        from app import db
        from app.intelligence.models import AnomalyRecord
        anomaly = AnomalyRecord(identity_id=identity_id, anomaly_type="status_stall",
                                 severity="info", title="Test", description="Test")
        db.session.add(anomaly)
        db.session.commit()
        from app.intelligence.service import resolve_anomaly
        assert resolve_anomaly(anomaly_id=anomaly.id) is True
        assert resolve_anomaly(anomaly_id=99999) is False


# ===========================================================================
# 4. Confidence Scoring
# ===========================================================================

class TestConfidenceScoring:
    """Deterministic confidence scoring."""

    def test_high_confidence(self, app):
        from app.intelligence.service import compute_confidence
        result = compute_confidence({
            "object_name": "Test", "object_type": "Document",
            "object_content": "Content", "has_owner": True,
            "relationship_count": 5, "message_count": 10,
            "days_since_update": 0,
        })
        assert result["score"] >= 0.7
        assert result["label"] == "high"

    def test_low_confidence(self, app):
        from app.intelligence.service import compute_confidence
        result = compute_confidence({
            "object_name": "Test", "object_type": "",
            "object_content": "", "has_owner": False,
            "relationship_count": 0, "message_count": 0,
            "days_since_update": 100,
        })
        assert result["score"] < 0.4
        assert result["label"] == "low"

    def test_confidence_score_range(self, app):
        from app.intelligence.service import compute_confidence
        result = compute_confidence({})
        assert 0 <= result["score"] <= 1


# ===========================================================================
# 5. API Endpoints
# ===========================================================================

class TestIntelligenceAPI:
    """M8 API endpoints."""

    def _login(self, app, client, identity_id):
        with client.session_transaction() as sess:
            sess["identity_id"] = identity_id
            sess["user_id"] = identity_id

    def test_traces_api(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import create_reasoning_trace
        create_reasoning_trace(identity_id=identity_id, reasoning_type="test",
                                query="API test", ai_response="API response")
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.get("/api/v1/intelligence/traces")
            assert resp.get_json()["success"]

    def test_trace_detail_api(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import create_reasoning_trace
        t = create_reasoning_trace(identity_id=identity_id, reasoning_type="test",
                                    query="Detail", ai_response="Detail response")
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.get(f"/api/v1/intelligence/traces/{t.trace_id}")
            assert resp.get_json()["success"]

    def test_correct_trace_api(self, app):
        identity_id = _make_identity(app)
        from app.intelligence.service import create_reasoning_trace
        t = create_reasoning_trace(identity_id=identity_id, reasoning_type="test",
                                    query="Q", ai_response="Wrong")
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.post(f"/api/v1/intelligence/traces/{t.trace_id}/correct",
                               json={"corrected_response": "Right"})
            assert resp.get_json()["success"] is True

    def test_learning_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.get("/api/v1/intelligence/learning")
            assert resp.get_json()["success"]

    def test_learning_summary_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.get("/api/v1/intelligence/learning/summary")
            assert resp.get_json()["success"]

    def test_anomalies_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.get("/api/v1/intelligence/anomalies")
            assert resp.get_json()["success"]

    def test_detect_anomalies_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.post("/api/v1/intelligence/anomalies/detect")
            assert resp.get_json()["success"]

    def test_confidence_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            self._login(app, client, identity_id)
            resp = client.post("/api/v1/intelligence/confidence",
                               json={"object_name": "Test", "message_count": 5})
            assert resp.get_json()["success"]

    def test_api_requires_auth(self, app):
        with app.test_client() as client:
            resp = client.get("/api/v1/intelligence/traces")
            assert resp.status_code == 401


# ===========================================================================
# 6. Regression
# ===========================================================================

class TestMilestoneRegression:
    """All prior milestones still pass."""

    def test_m1_signin(self, app):
        from app.adapters.os_adapter import sign_in
        result = sign_in(email="m8-reg@test.com", name="M8 Reg")
        assert result["success"]

    def test_m2_executive_home(self, app):
        from app.adapters.os_adapter import get_executive_home
        identity_id = _make_identity(app)
        result = get_executive_home(identity_id=identity_id)
        assert result["success"]

    def test_m3_insights(self, app):
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        _seed_m8_data(app, identity_id)
        result = build_insights(identity_id=identity_id)
        assert "summary" in result

    def test_m4_workspace(self, app):
        from app.founder.workspace_intelligence import build_workspace_summary
        identity_id = _make_identity(app)
        _seed_m8_data(app, identity_id)
        result = build_workspace_summary("m8_obj")
        assert result["name"] == "M8 Object"

    def test_m5_ai_copilot(self, app):
        from app.ai.copilot import copilot_health
        health = copilot_health()
        assert "provider" in health

    def test_m6_notifications(self, app):
        from app.integration.service import create_notification, get_notifications
        identity_id = _make_identity(app)
        create_notification(identity_id=identity_id, notification_type="test", title="M8 Reg")
        notifs = get_notifications(identity_id=identity_id)
        assert len(notifs) >= 1

    def test_m7_automation(self, app):
        from app.automation.service import create_rule, get_rules
        identity_id = _make_identity(app)
        create_rule(identity_id=identity_id, name="M7 Reg", trigger_type="entity_created",
                     trigger_config={}, action_type="notify", action_config={})
        rules = get_rules(identity_id=identity_id)
        assert len(rules) >= 1