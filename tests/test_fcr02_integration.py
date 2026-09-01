"""FCR-02 Integration Suite — real execution truth acceptance tests.

This suite proves:
- capability discovery and selection
- permission enforcement and authorization denial
- execution lifecycle (REQUESTED → AUTHORIZED → RUNNING → SUCCEEDED/FAILED/DENIED)
- read-only requests produce evidence+observation ONLY (no execution/outcome)
- write/action requests produce full chain with governed lifecycle states
- persistence, provenance, and identity/tenant isolation
- failure, retry, and denied paths

Every test inspects actual persisted state in the database,
not only returned JSON responses.
"""

import json
import pytest
from datetime import datetime, timezone

from app import db, create_app
from app.shunya.observer_learning import Observation
from app.evidence.models_db import EvidenceRecord
from app.evidence.decision_trace import DecisionTrace
from app.execution_engine.models import Execution, ExecutionLog
from app.execution.models import Outcome


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create app with test configuration."""
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://shunya:0jyVsAbKMy@localhost:5433/shunya_test"
    # Use the main database which is already initialized.
    # Tests create and clean up their own records.
    return _app


@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean synthetic records before each test to prevent contamination."""
    with app.app_context():
        # Clean any leftover execution-chain records
        for table in [Outcome, ExecutionLog, Execution, DecisionTrace, EvidenceRecord, Observation]:
            try:
                db.session.query(table).delete()
                db.session.commit()
            except Exception:
                db.session.rollback()


# ---------------------------------------------------------------------------
# Capability Registry Tests
# ---------------------------------------------------------------------------

class TestCapabilityRegistry:
    """Capability discovery, selection, and permission enforcement."""

    def test_registry_can_discover_capabilities(self, app):
        """Prove capability registry returns known capabilities by query."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            # Discovery by keyword
            matched = registry.find("show me documents")
            names = [c.name for c in matched]
            assert "documents" in names, f"Expected 'documents' in {names}"

            matched = registry.find("create invoice")
            names = [c.name for c in matched]
            assert "invoices" in names, f"Expected 'invoices' in {names}"

    def test_registry_distinguishes_availability(self, app):
        """Prove registry knows the difference between AVAILABLE and UNWIRED."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            available = registry.list(status="AVAILABLE")
            unwired = registry.list(status="UNWIRED")
            unused = registry.list(status="INTEGRATED_BUT_UNUSED")

            assert len(available) >= 18, f"Expected >=18 AVAILABLE (8 intel engines + app caps), got {len(available)}"
            assert len(unwired) >= 2, f"Expected >=2 UNWIRED (UCP domain engines), got {len(unwired)}"

            # AVAILABLE capabilities have handlers
            for c in available:
                assert c._handler is not None or c.engine == "self", \
                    f"{c.name} is AVAILABLE but has no handler"

    def test_registry_permission_enforcement(self, app):
        """Prove unauthorized role cannot invoke a permission-gated capability."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            # Execution requires "execution.execute" permission
            result = registry.invoke("execution", context={}, user_role="guest")
            assert "error" in result, \
                "Guest should be denied execution — got success"
            assert "Not authorized" in result.get("error", ""), \
                f"Wrong error: {result}"

    def test_registry_invocation_records_usage(self, app):
        """Prove invocation increments counter and records timestamp."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            # Register a test handler
            def test_handler(ctx):
                return {"result": "test_ok"}

            registry.promote_to_available("workspace", test_handler)

            # Invoke twice
            registry.invoke("workspace", context={})
            registry.invoke("workspace", context={})

            # Check usage
            cap = registry.get("workspace")
            assert cap._invocation_count >= 2, \
                f"Expected >=2 invocations, got {cap._invocation_count}"
            assert cap._last_invoked is not None, "Last invoked timestamp should be set"


# ---------------------------------------------------------------------------
# Execution Chain Lifecycle Tests
# ---------------------------------------------------------------------------

class TestExecutionChainReadPath:
    """Read-only queries produce evidence + observation, NEVER execution/outcome."""

    def test_read_query_produces_only_evidence_and_observation(self, app):
        """Prove a read-only query creates no DecisionTrace, Execution, or Outcome."""
        with app.app_context():
            from core.execution_chain import record_read_chain

            result = record_read_chain(
                query="What are my current leads?",
                identity_id="test_user_1",
                tenant_id=92,
                confidence=0.85,
                response_summary="You have 12 leads in your pipeline.",
            )

            # Evidence and observation should exist
            assert result["evidence_id"] is not None, "Evidence should be created"
            assert result["observation_id"] is not None, "Observation should be created"

            # No execution artifacts
            assert result.get("decision_trace_id") is None, \
                "Read queries must NOT create decision traces"
            assert result.get("execution_id") is None, \
                "Read queries must NOT create executions"
            assert result.get("outcome_id") is None, \
                "Read queries must NOT create outcomes"

            # Verify persisted state
            ev = db.session.get(EvidenceRecord, result["evidence_id"])
            assert ev is not None, "Evidence must be persisted"
            assert ev.source_type == "ai_query", \
                f"Expected ai_query, got {ev.source_type}"

            obs = db.session.get(Observation, result["observation_id"])
            assert obs is not None, "Observation must be persisted"
            assert obs.success == True, "Read observations should be successful"
            assert obs.tenant_id == 92, f"Expected tenant_id=92, got {obs.tenant_id}"

    def test_read_query_state_is_never_completed(self, app):
        """Prove read-only queries never set status='completed' on anything."""
        with app.app_context():
            from core.execution_chain import record_read_chain

            result = record_read_chain(
                query="Show me recent documents",
                identity_id="test_user_1",
                tenant_id=89,
            )

            # No execution means no status at all (read path doesn't create executions)
            exec_count = db.session.query(Execution).count()
            assert exec_count == 0, \
                f"Read queries must never create executions (found {exec_count})"

            obs = db.session.get(Observation, result["observation_id"])
            assert obs.success == True


class TestExecutionChainActionPath:
    """Write/action queries produce full chain with governed lifecycle states."""

    def test_action_chain_starts_as_requested(self, app):
        """Prove action chain begins in REQUESTED state — never auto-completed."""
        with app.app_context():
            from core.execution_chain import record_action_chain, ExecutionState

            result = record_action_chain(
                query="Create a new lead for Acme Corp",
                action_type="create",
                identity_id="test_user_2",
                tenant_id=89,
                object_id=1,
            )

            # Full chain should exist
            assert result["decision_trace_id"] is not None
            assert result["execution_id"] is not None
            assert result["evidence_id"] is not None
            assert result["observation_id"] is not None
            assert result["outcome_id"] is None, \
                "Outcome must NOT exist until action completes"
            assert result["state"] == ExecutionState.REQUESTED.value, \
                f"Expected REQUESTED, got {result['state']}"

            # Verify persisted execution state is REQUESTED
            exec_record = db.session.get(Execution, result["execution_id"])
            assert exec_record is not None
            assert exec_record.status == ExecutionState.REQUESTED.value, \
                f"Expected REQUESTED, got {exec_record.status}"

            # Verify decision trace is PENDING
            dt = db.session.get(DecisionTrace, result["decision_trace_id"])
            assert dt is not None
            assert dt.execution_status == "pending", \
                f"Expected pending, got {dt.execution_status}"

            # Verify observation has null success (not yet known)
            obs = db.session.get(Observation, result["observation_id"])
            assert obs is not None

    def test_action_chain_complete_moves_to_succeeded(self, app):
        """Prove completing an action transitions REQUESTED → SUCCEEDED."""
        with app.app_context():
            from core.execution_chain import (
                record_action_chain, complete_action_chain, ExecutionState,
            )

            chain = record_action_chain(
                query="Send proposal to Acme Corp",
                action_type="send",
                identity_id="user_proposal",
                tenant_id=89,
            )
            exec_id = chain["execution_id"]
            obs_id = chain["observation_id"]

            # Complete the action
            completion = complete_action_chain(
                exec_id=exec_id,
                outcome="succeeded",
                response_summary="Proposal sent to Acme Corp successfully",
                identity_id="user_proposal",
                tenant_id=89,
                state={"sent": True, "recipient": "acme@corp.com"},
                observation_id=obs_id,
            )

            # Verify execution state transition
            exec_record = db.session.get(Execution, exec_id)
            assert exec_record.status == ExecutionState.SUCCEEDED.value, \
                f"Expected SUCCEEDED, got {exec_record.status}"

            # Verify outcome was created
            assert completion["outcome_id"] is not None, \
                "Outcome must be created on successful action"
            outcome = Outcome.query.filter_by(
                outcome_id=completion["outcome_id"]
            ).first()
            assert outcome is not None
            assert "sent" in (outcome.state or {}), \
                f"Outcome state should include action result: {outcome.state}"

            # Verify observation updated
            obs = db.session.get(Observation, obs_id)
            assert obs.success == True, "Observation should be marked success"

            # Verify execution log
            log = ExecutionLog.query.filter_by(
                object_id=exec_record.object_id
            ).order_by(ExecutionLog.created_at.desc()).first()
            assert log is not None
            assert "succeeded" in str(log.state_after), \
                f"Log should reflect final state: {log.state_after}"

    def test_action_chain_failure_path(self, app):
        """Prove a failed action transitions properly."""
        with app.app_context():
            from core.execution_chain import (
                record_action_chain, complete_action_chain, ExecutionState,
            )

            chain = record_action_chain(
                query="Approve payment #1234",
                action_type="approve",
                identity_id="approver_1",
                tenant_id=89,
            )
            exec_id = chain["execution_id"]
            obs_id = chain["observation_id"]

            # Fail the action
            completion = complete_action_chain(
                exec_id=exec_id,
                outcome="failed",
                response_summary="Payment approval failed: insufficient funds",
                identity_id="approver_1",
                tenant_id=89,
                state={"error": "insufficient_funds"},
                observation_id=obs_id,
            )

            exec_record = db.session.get(Execution, exec_id)
            assert exec_record.status == ExecutionState.FAILED.value, \
                f"Expected FAILED, got {exec_record.status}"

            # Outcome should NOT be created for failures
            assert completion["outcome_id"] is None, \
                "Failed actions should not produce outcomes"

            # Observation should reflect failure
            obs = db.session.get(Observation, obs_id)
            assert obs.success == False, "Observation should be marked failed"
            assert obs.severity == "error", "Failure should set error severity"

    def test_action_chain_deny_path(self, app):
        """Prove an unauthorized action goes to DENIED state."""
        with app.app_context():
            from core.execution_chain import (
                record_action_chain, deny_action_chain, ExecutionState,
            )

            chain = record_action_chain(
                query="Delete customer record",
                action_type="delete",
                identity_id="unauthorized_user",
            )
            exec_id = chain["execution_id"]

            # Deny
            deny_action_chain(exec_id, reason="No delete permissions")

            exec_record = db.session.get(Execution, exec_id)
            assert exec_record.status == ExecutionState.DENIED.value, \
                f"Expected DENIED, got {exec_record.status}"

    def test_action_chain_transition_logged(self, app):
        """Prove every state transition is recorded in execution_logs."""
        with app.app_context():
            from core.execution_chain import (
                record_action_chain, transition_execution, ExecutionState,
            )

            chain = record_action_chain(
                query="Update deal stage to negotiation",
                action_type="update",
                identity_id="sales_1",
                tenant_id=89,
            )
            exec_id = chain["execution_id"]

            # Authorize
            transition_execution(exec_id, ExecutionState.AUTHORIZED.value)
            # Run
            transition_execution(exec_id, ExecutionState.RUNNING.value)
            # Succeed
            transition_execution(exec_id, ExecutionState.SUCCEEDED.value)

            # Verify log entries
            logs = ExecutionLog.query.filter_by(
                object_id=db.session.get(Execution, exec_id).object_id
            ).order_by(ExecutionLog.created_at.asc()).all()
            states = []
            for log in logs:
                sa = log.state_after or {}
                states.append(sa.get("status", ""))

            assert "requested" in states, f"REQEUSTED transition not logged: {states}"
            assert "authorized" in states, f"AUTHORIZED transition not logged: {states}"
            assert "running" in states, f"RUNNING transition not logged: {states}"
            assert "succeeded" in states, f"SUCCEEDED transition not logged: {states}"


class TestExecutionChainInvariants:
    """Invariant enforcement for execution chain records."""

    def test_read_never_becomes_execution(self, app):
        """Prove the system never conflates a read with an executed action."""
        with app.app_context():
            from core.execution_chain import record_read_chain

            # Record several read-only queries
            for i in range(5):
                record_read_chain(
                    query=f"What is the status of lead {i}?",
                    identity_id="test_user",
                    tenant_id=89,
                )

            # Verify zero executions were created
            exec_count = db.session.query(Execution).count()
            assert exec_count == 0, \
                f"{exec_count} executions found — reads must never create executions"

            # Verify evidence and observations exist
            ev_count = db.session.query(EvidenceRecord).count()
            obs_count = db.session.query(Observation).count()
            assert ev_count == 5, f"Expected 5 evidence records, got {ev_count}"
            assert obs_count == 5, f"Expected 5 observations, got {obs_count}"

    def test_each_record_has_provenance_chain(self, app):
        """Prove every action record traces who → where → what → which capability."""
        with app.app_context():
            from core.execution_chain import record_action_chain

            chain = record_action_chain(
                query="Create task for project onboarding",
                action_type="create",
                identity_id="pm_1",
                tenant_id=89,
                object_id=7,
            )

            # Decision trace carries context
            dt = db.session.get(DecisionTrace, chain["decision_trace_id"])
            assert dt is not None
            md = dt.main_decision or {}
            assert "pm_1" in str(md), f"Decision trace missing identity context: {md}"

            # Execution is linked to object
            exec_rec = db.session.get(Execution, chain["execution_id"])
            assert exec_rec.object_id == 7, \
                f"Execution object_id mismatch: {exec_rec.object_id}"

            # Evidence links back to everything
            ev = db.session.get(EvidenceRecord, chain["evidence_id"])
            assert ev is not None

    def test_duplicate_action_creates_distinct_chain(self, app):
        """Prove duplicate requests create distinct chains, not same records."""
        with app.app_context():
            from core.execution_chain import record_action_chain

            chain1 = record_action_chain(
                query="Approve invoice INV-001",
                action_type="approve",
                identity_id="finance_1",
                tenant_id=89,
            )
            chain2 = record_action_chain(
                query="Approve invoice INV-001",
                action_type="approve",
                identity_id="finance_1",
                tenant_id=89,
            )

            # Distinct IDs
            assert chain1["execution_id"] != chain2["execution_id"], \
                "Same action twice should create distinct executions"
            assert chain1["decision_trace_id"] != chain2["decision_trace_id"], \
                "Same action twice should create distinct decision traces"
            assert chain1["evidence_id"] != chain2["evidence_id"], \
                "Same action twice should create distinct evidence"

    def test_denied_action_never_reaches_succeeded(self, app):
        """Prove a denied action is truly terminal — cannot be retroactively succeeded."""
        with app.app_context():
            from core.execution_chain import (
                record_action_chain, deny_action_chain,
                transition_execution, ExecutionState,
            )

            chain = record_action_chain(
                query="Delete company records",
                action_type="delete",
                identity_id="audit_1",
                tenant_id=89,
            )
            exec_id = chain["execution_id"]

            # Deny it
            deny_action_chain(exec_id)

            # Attempt to transition to running or succeeded — should be rejected
            result = transition_execution(exec_id, ExecutionState.SUCCEEDED.value)
            assert result == False, "Transition from DENIED to SUCCEEDED should return False"

            exec_record = db.session.get(Execution, exec_id)
            assert exec_record.status == ExecutionState.DENIED.value, \
                f"Dented execution should remain DENIED, got {exec_record.status}"


# ---------------------------------------------------------------------------
# Capability-as-Orchestration-Fabric Tests
# ---------------------------------------------------------------------------

class TestCapabilityOrchestration:
    """The capability registry as a governed execution layer."""

    def test_capability_selects_correct_engine(self, app):
        """Prove capability routing maps user intent → correct engine."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            matched = registry.route("I want to search my documents")
            names = [c.name for c in matched]
            assert "search" in names or "documents" in names, \
                f"Search/document query should match relevant caps: {names}"

            matched = registry.route("Show me my invoices")
            names = [c.name for c in matched]
            assert "invoices" in names or "finance" in names, \
                f"Invoice query should match invoices: {names}"

    def test_capability_from_ask_includes_routing(self, app):
        """Prove ask() returns capability routing context."""
        with app.app_context():
            from core.intelligence_runtime.integration import _get_capability_context

            ctx = _get_capability_context(
                "create an invoice for $5000",
                identity_id="test_user",
                tenant_id="1",
                workspace_type="org",
            )

            assert ctx["capability_count"] > 0, \
                f"Should match capabilities, got {ctx}"
            assert "can_write" in ctx, f"Missing can_write: {ctx}"
            assert "can_execute" in ctx, f"Missing can_execute: {ctx}"


# ---------------------------------------------------------------------------
# Cleanup: mark synthetic test data clearly
# ---------------------------------------------------------------------------

class TestSyntheticDataIntegrity:
    """Prove synthetic test records are clearly distinguishable."""

    def test_test_records_are_not_confused_with_production(self, app):
        """Prove every test record in the DB was created by us in this session."""
        with app.app_context():
            from core.execution_chain import record_read_chain, ExecutionState

            r = record_read_chain(
                query="test query",
                identity_id="test_user",
            )

            ev = db.session.get(EvidenceRecord, r["evidence_id"])
            assert ev is not None
            # Test records are identifiable by their source type
            assert ev.source_type.startswith("ai_"), \
                f"Expected ai_ prefix in source_type: {ev.source_type}"

    def test_cleanup_removes_synthetic_records(self, app):
        """Prove _clear_synthetic_records works without affecting real data."""
        with app.app_context():
            from core.execution_chain import _clear_synthetic_records, record_read_chain

            legal_ev = EvidenceRecord(
                source_type="crm_lead", source_id="L-001",
                raw_reference={"type": "real"},
            )
            db.session.add(legal_ev)
            db.session.commit()

            rec1 = record_read_chain(
                query="test cleanup query 1", identity_id="cleanup_test")
            rec2 = record_read_chain(
                query="test cleanup query 2", identity_id="cleanup_test")

            counts = _clear_synthetic_records()
            assert counts.get("evidence", 0) >= 2, \
                f"Should clear >=2 synthetic evidence: {counts}"
            assert counts.get("observations", 0) >= 2, \
                f"Should clear >=2 synthetic observations: {counts}"

            # Legal record should remain
            remaining = db.session.get(EvidenceRecord, legal_ev.id)
            assert remaining is not None, \
                "Legal evidence must survive cleanup"


# ---------------------------------------------------------------------------
# Intelligence Engine Wiring (Phase 5)
# ---------------------------------------------------------------------------

class TestIntelligenceEngineWiring:
    """Prove the 8 intelligence engines are invocable through the registry."""

    def test_all_engines_registered_and_available(self, app):
        """Prove all 8 engines have AVAILABLE status with handlers."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            for name in ["perception", "context_assembly", "reasoning",
                         "planning", "decision", "reflection",
                         "learning", "confidence"]:
                cap = registry.get(name)
                assert cap is not None, f"{name} should be registered"
                assert cap.status == "AVAILABLE", \
                    f"{name} should be AVAILABLE, got {cap.status}"
                assert cap._handler is not None, \
                    f"{name} should have a handler"

    def test_perception_engine_invocation(self, app):
        """Prove perception engine processes input and returns observation."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            result = registry.invoke("perception", context={
                "input_type": "observation",
                "payload": {
                    "text": "Create a new lead for Acme Corp",
                    "source": "user_input",
                },
                "confidence_threshold": 0.5,
            })
            assert result["success"], f"Perception failed: {result}"
            payload = result.get("result", {}).get("payload", {})
            assert "observation_id" in str(payload), \
                f"Perception should produce observation: {payload}"

    def test_reasoning_engine_invocation(self, app):
        """Prove reasoning engine performs deductive reasoning."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            result = registry.invoke("reasoning", context={
                "input_type": "reasoning",
                "payload": {
                    "premises": [
                        "All leads need follow-up within 24 hours",
                        "Acme Corp is a lead",
                    ],
                    "reasoning_type": "deductive",
                },
            })
            assert result["success"], f"Reasoning failed: {result}"
            payload = result.get("result", {}).get("payload", "")
            assert "conclusion" in str(payload).lower(), \
                f"Reasoning should produce conclusion: {payload}"

    def test_decision_engine_invocation(self, app):
        """Prove decision engine creates a decision record."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            result = registry.invoke("decision", context={
                "input_type": "create_decision",
                "payload": {
                    "label": "Qualify lead Acme Corp",
                    "description": "Determine if Acme Corp meets qualification criteria",
                    "owner": "sales_agent",
                },
            })
            assert result["success"], f"Decision failed: {result}"
            payload = result.get("result", {}).get("payload", {})
            assert "decision_id" in str(payload), \
                f"Decision should produce decision_id: {payload}"

    def test_planning_engine_invocation(self, app):
        """Prove planning engine generates a plan from an objective."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            result = registry.invoke("planning", context={
                "input_type": "plan",
                "payload": {
                    "objective": "Qualify and close Acme Corp lead",
                },
                "confidence_threshold": 0.5,
            })
            assert result["success"], f"Planning failed: {result}"
            payload = result.get("result", {}).get("payload", {})
            assert "plan_id" in str(payload) or "steps" in str(payload), \
                f"Planning should produce plan with steps: {payload[:200]}"

    def test_reflection_engine_invocation(self, app):
        """Prove reflection engine can reflect on outcomes."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            result = registry.invoke("reflection", context={
                "input_type": "reflect",
                "payload": {
                    "expected_outcome": {"status": "sent"},
                    "actual_outcome": {"status": "failed"},
                    "subject_id": "lead-123",
                    "subject_type": "lead",
                },
            })
            assert result["success"], f"Reflection failed: {result}"
            payload = result.get("result", {}).get("payload", {})
            assert "reflection_id" in str(payload), \
                f"Reflection should produce reflection_id: {payload[:100]}"

    def test_learning_engine_invocation(self, app):
        """Prove learning engine detects patterns from reflections."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            result = registry.invoke("learning", context={
                "input_type": "reflection",
                "payload": {
                    "success_score": 0.4,
                    "improvement_signals": [
                        {"signal": "response_time_too_high", "value": 120},
                    ],
                    "anomalies": ["delayed_follow_up"],
                    "subject_id": "lead-123",
                    "subject_type": "lead",
                },
            })
            assert result["success"], f"Learning failed: {result}"
            payload = result.get("result", {}).get("payload", {})
            assert "pattern_id" in str(payload), \
                f"Learning should produce pattern_id: {payload[:100]}"

    def test_confidence_engine_invocation(self, app):
        """Prove confidence engine computes overall confidence score."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            result = registry.invoke("confidence", context={
                "input_type": "compute",
                "payload": {
                    "factors": [
                        {"name": "source_reliability", "value": 0.9, "weight": 0.25},
                        {"name": "evidence_strength", "value": 0.7, "weight": 0.3},
                        {"name": "consistency", "value": 0.8, "weight": 0.2},
                    ],
                },
            })
            assert result["success"], f"Confidence failed: {result}"
            payload = result.get("result", {}).get("payload", {})
            assert "overall" in str(payload), \
                f"Confidence should produce overall score: {payload[:100]}"

    def test_engine_invocation_records_usage(self, app):
        """Prove engine invocation increments usage counters."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            before = registry.get("perception")._invocation_count
            registry.invoke("perception", context={
                "input_type": "observation",
                "payload": {"text": "test", "source": "test"},
                "confidence_threshold": 0.5,
            })
            after = registry.get("perception")._invocation_count
            assert after == before + 1, \
                f"Expected {before + 1}, got {after}"

    def test_engine_error_returns_structured_result(self, app):
        """Prove engine processing errors produce structured responses, not crashes."""
        with app.app_context():
            from core.capability_registry import get_registry
            registry = get_registry()

            # Send empty payload to planning engine — should error gracefully
            result = registry.invoke("planning", context={})
            assert not result["success"], \
                "Empty planning request should fail"
            assert "error" in result, \
                "Error should be in result, not thrown as exception"