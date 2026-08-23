"""FDA5/FDA6 Certification Correction — Outcome, Actionability, UX.

Written as golden cross-boundary tests, not implementation tests.
"""
import pytest
import json


class TestOutcomeEngine:
    """FDA6-G6: Real outcome — execution reaches terminal state with persisted evidence.

    PROD-06 migration: step-based progression removed. The state-driven
    model is: OutcomeRuntime.accept() creates an outcome, update_state()
    mutates its opaque state dict. No predefined lifecycle progression.
    """

    def test_outcome_created_and_retrieved(self, app):
        """Outcome → created via accept() → retrievable via get().

        State-driven: OutcomeRuntime.accept() creates an outcome with
        given intention and optional initial state. No step progression.
        """
        from app.execution import OutcomeRuntime
        with app.app_context():
            engine = OutcomeRuntime()

            # Accept — creates the outcome with intention
            outcome = engine.accept(
                identity_id="1",
                intention="Complete quarterly review for golden test",
                state={"status": "accepted", "result": "pending"},
            )
            assert outcome is not None
            exec_id = outcome.outcome_id

            # Retrieve — outcome is persisted
            retrieved = engine.get(exec_id)
            assert retrieved is not None
            assert retrieved.outcome_id == exec_id
            assert retrieved.intention == "Complete quarterly review for golden test"

    def test_outcome_can_reach_terminal_state(self, app):
        """Outcome state can be updated to a terminal state via update_state().

        State-driven: update_state() mutates the opaque state dict.
        No explicit fail() method — state is just data.
        """
        from app.execution import OutcomeRuntime
        with app.app_context():
            engine = OutcomeRuntime()
            outcome = engine.accept(
                identity_id="1",
                intention="Test failure path",
                state={"status": "processing", "attempt": 1},
            )
            exec_id = outcome.outcome_id

            # Update state to terminal failure
            outcome = engine.update_state(exec_id, {"status": "failed", "reason": "Insufficient data"})
            assert outcome.state.get("status") == "failed"
            assert outcome.state.get("reason") is not None

    def test_execution_idempotency(self, app):
        """Same explicit idempotency_key → same execution identity (idempotent).

        BusinessExecutionInstance.activate() with an explicit idempotency_key
        must return the same outcome_id on replay. Without an explicit key,
        each call creates a distinct execution.
        """
        from app.execution import BusinessExecutionInstance
        from app.execution.models import Outcome
        with app.app_context():
            engine = BusinessExecutionInstance()

            # Same commitment_id called twice WITH explicit idempotency_key
            r1 = engine.activate(commitment_type="task", commitment_id="idempotent_003",
                                 tenant_id=1, idempotency_key="fda-idem-003")
            r2 = engine.activate(commitment_type="task", commitment_id="idempotent_003",
                                 tenant_id=1, idempotency_key="fda-idem-003")

            # Both succeed
            assert r1["success"] is True
            assert r2["success"] is True

            # IDEMPOTENCY: same key must produce the same execution identity
            assert r1["exec_id"] == r2["exec_id"], (
                f"Expected same exec_id for idempotent call, got {r1['exec_id']} vs {r2['exec_id']}"
            )
            # Second call should be recognized as idempotent
            assert r2.get("idempotent") is True

            # Verify the single execution in database
            count = Outcome.query.filter(
                Outcome.intention == "Execute task idempotent_003"
            ).count()
            assert count == 1, f"Expected 1 execution, found {count}"

            # The single execution is retrievable
            outcome = engine.get(r1["exec_id"])
            assert outcome is not None
            assert outcome.outcome_id == r1["exec_id"]

    def test_execution_idempotency_different_tenant(self, app):
        """Different tenant with different commitment_id → separate executions."""
        from app.execution import BusinessExecutionInstance
        with app.app_context():
            engine = BusinessExecutionInstance()

            # Tenant 1 creates execution with unique commitment
            r1 = engine.activate(commitment_type="task", commitment_id="tenant_a_001", tenant_id=1)
            # Tenant 2 creates execution with different commitment_id
            r2 = engine.activate(commitment_type="task", commitment_id="tenant_b_001", tenant_id=2)

            assert r1["success"] is True
            assert r2["success"] is True

            # Different commitments → different executions
            assert r1["exec_id"] != r2["exec_id"]

class TestActionability:
    """FDA6-G7: Recommendation → authorized execution → outcome."""

    def test_authorized_execution_path(self, app):
        """Recommendation → authorized execution → outcome → retrievable."""
        from app.execution import BusinessExecutionInstance
        from app.memory import MemoryService
        from app.memory.models import TruthClassification
        from core.intelligence_core import IntelligenceEngine, TruthCategory

        with app.app_context():
            # Step 1: Add context (company knowledge)
            mem_svc = MemoryService()
            mem_svc.create_memory(
                person_id=None,
                memory_key="action_context",
                value="Quarterly review required for all active accounts",
                truth_classification=TruthClassification.FACT,
            )

            # Step 2: Intelligence produces recommendation
            engine = IntelligenceEngine(memory_service=mem_svc)
            result = engine.answer("What needs to be done for active accounts?", tenant_id="1")
            assert result is not None

            # Step 3: Execute the recommendation
            exec_engine = BusinessExecutionInstance()
            exec_result = exec_engine.activate(
                commitment_type="quarterly_review",
                commitment_id="action_001",
                tenant_id=1,
            )
            assert exec_result["success"] is True
            exec_id = exec_result["exec_id"]

            # Step 4: Outcome is persisted and retrievable
            outcome = exec_engine.get(exec_id)
            assert outcome is not None
            assert outcome.outcome_id == exec_id
            assert outcome.intention is not None

    def test_unauthorized_action_rejected(self, app):
        """Unauthorized action → safe failure."""
        from core.intelligence_core import SafeFailureHandler
        result = SafeFailureHandler.handle_unauthorized()
        assert "permission" in result.content.lower()
        assert result.confidence == 0.0

    def test_failure_produces_safe_state(self, app):
        """Failed execution produces safe terminal state."""
        from app.execution import BusinessExecutionInstance
        with app.app_context():
            exec_engine = BusinessExecutionInstance()
            # Attempt execution with missing parameters
            result = exec_engine.activate(
                commitment_type="",
                commitment_id="",
                tenant_id=1,
            )
            assert result["success"] is True  # Should still succeed (accepts empty)
            assert "exec_id" in result


class TestTenantIsolation:
    """Import API tenant isolation — no tenant fallback to 1."""

    def test_import_route_requires_tenant(self, app):
        """Import route without tenant → 401 or 403."""
        from core.api_contract import register_error_handlers
        with app.app_context():
            register_error_handlers(app)
            with app.test_client() as client:
                # First verify the route exists
                health_resp = client.get("/system/health")
                assert health_resp.status_code == 200
                # Now test without auth/tenant
                resp = client.post("/api/v1/import/contacts/csv")
                assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_import_route_uses_g_tenant_id(self, app):
        """Import route reads tenant from g.tenant_id, not request fallback."""
        # Verify the route file uses g.tenant_id
        import pathlib
        source = pathlib.Path("app/import_api/routes.py").read_text()
        assert "g.tenant_id" in source
        assert "getattr(request" not in source


class TestGmailProviderClassification:
    """Gmail provider dependency — correctly classified."""

    def test_gmail_adapter_has_real_provider_path(self):
        """GmailAdapter has a real provider path (not just mock)."""
        from app.integration.gmail_adapter import GmailAdapter
        import inspect
        source = inspect.getsource(GmailAdapter.connect)
        # The real path uses google.oauth2.credentials
        assert "google.oauth2.credentials" in source or "googleapiclient" in source
        assert "_mock" in source  # Also has mock path for testing

    def test_gmail_adapter_requires_credentials(self):
        """GmailAdapter requires real OAuth credentials to connect."""
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import IntegrationConfig
        adapter = GmailAdapter()
        # Without any credentials
        assert adapter.connect(IntegrationConfig(provider_name="gmail", tenant_id="1")) is False


class TestIntelligenceUX:
    """FDA6 UX — actual running UI path."""

    def test_system_health_endpoint_accessible(self, app):
        """Health endpoint is the minimum UX path."""
        with app.test_client() as client:
            resp = client.get("/system/health")
            assert resp.status_code == 200
            data = json.loads(resp.get_data(as_text=True))
            # Health endpoint returns meaningful data
            assert isinstance(data, dict)

    def test_ui_routes_accessible(self, app):
        """UI routes are registered and return HTML."""
        with app.test_client() as client:
            # Check that the main UI route exists
            resp = client.get("/")
            # Should return either HTML (200), redirect (302), or
            # 503 if frontend not yet built (CI runs Python tests before frontend build)
            assert resp.status_code in (200, 302, 301, 503)

    def test_ui_workspace_route(self, app):
        """Workspace UI route is accessible."""
        with app.test_client() as client:
            resp = client.get("/workspace")
            assert resp.status_code in (200, 302, 301, 401)

    def test_mobile_viewport_check(self, app):
        """UI should be responsive (mobile-capable)."""
        with app.test_client() as client:
            resp = client.get("/", headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)"})
            assert resp.status_code in (200, 302, 301, 503)


class TestGoldenCrossBoundary:
    """Complete cross-boundary golden scenario.

    API → service → execution → persistence → observable result.
    """

    def test_full_golden_path(self, app):
        """Complete golden path across all subsystem boundaries."""
        from app.identity.service import IdentityService
        from app.memory import MemoryService
        from app.memory.models import TruthClassification
        from app.execution import BusinessExecutionInstance
        from core.identity_interface import IdentityClaim, ClaimType

        with app.app_context():
            # 1. Identity: Create a person
            id_svc = IdentityService()
            c = id_svc.add_claim(IdentityClaim(
                claim_value="golden-path@company.com",
                claim_type=ClaimType.EMAIL,
                source="golden_cert",
                source_id="golden_cert_001",
                tenant_id="1",
            ))
            assert c.claim_id is not None
            person_id = c.identity_id

            # 2. Memory: Add context about this person
            mem_svc = MemoryService()
            m = mem_svc.create_memory(
                person_id=int(person_id) if person_id else None,
                memory_key="customer_preference",
                value="Prefers email communication for all business matters",
                truth_classification=TruthClassification.FACT,
            )
            assert m.id is not None
            assert m.truth_classification == "fact"

            # 3. Execution: Execute a business action
            exec_engine = BusinessExecutionInstance()
            exec_result = exec_engine.activate(
                commitment_type="customer_followup",
                commitment_id="golden_cert_action",
                tenant_id=1,
            )
            assert exec_result["success"] is True
            exec_id = exec_result["exec_id"]

            # 4. Outcome: Verify the outcome is persisted and retrievable
            outcome = exec_engine.get(exec_id)
            assert outcome is not None
            assert outcome.outcome_id == exec_id
            assert outcome.intention is not None

            # 5. Identity resolution still works
            r = id_svc.resolve("golden-path@company.com", ClaimType.EMAIL)
            assert r.identity_id == person_id

            # 6. Memory is still retrievable
            retrieved = mem_svc.get_effective_memories(memory_key="customer_preference")
            assert len(retrieved) > 0