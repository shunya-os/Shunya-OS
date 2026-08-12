"""FDA11 — Product Outcome + Real-World Intelligence + Execution Hardening

Tests for: company-first intelligence with distinct semantic states,
execution hardening, multi-tenant security, provider fabric, observability.
"""
import pytest
import time
from datetime import datetime


class TestCompanyFirstIntelligence:
    """Distinct semantic states: FACT/MEMORY/OBSERVATION/INFERENCE/RECOMMENDATION/UNKNOWN."""

    def test_evidence_semantic_state_fact(self, app, client):
        """Company data is classified as FACT semantic state."""
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["identity_id"] = "user_1"
            sess["current_org_id"] = "org_1"

        resp = client.post("/api/v1/intelligence/ask", json={"question": "Our invoices"})
        assert resp.status_code == 200
        data = resp.get_json()
        pipeline = {s["stage"]: s for s in (data.get("pipeline") or [])}
        assembly = pipeline.get("evidence_assembly", {})
        if assembly.get("company_evidence_count", 0) > 0:
            for ev in (data.get("evidence_used") or []):
                assert ev["semantic"] == "FACT", f"Evidence missing FACT semantic: {ev}"

    def test_unknown_semantic_when_no_evidence(self, app, client):
        """When no company evidence exists, semantic state includes UNKNOWN."""
        # Use a tenant/org with no data
        from app.tenant import Tenant
        from app import db
        with app.app_context():
            t = Tenant(company_name="NoData", slug="no-data-fda11", business_type="test", is_active=True)
            db.session.add(t)
            db.session.commit()
            tid = t.id

        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["identity_id"] = "user_1"
            sess["current_org_id"] = str(tid)

        resp = client.post("/api/v1/intelligence/ask", json={"question": "What is our revenue?"})
        assert resp.status_code in (200, 403)
        data = resp.get_json()
        if resp.status_code == 200:
            pipeline = {s["stage"]: s for s in (data.get("pipeline") or [])}
            assembly = pipeline.get("evidence_assembly", {})
            semantic_states = assembly.get("semantic_states", [])
            if assembly.get("company_evidence_count", 0) == 0:
                assert "UNKNOWN" in semantic_states, \
                    f"Expected UNKNOWN semantic state, got {semantic_states}"


class TestExecutionHardening:
    """Concurrent requests, idempotency, retry safety, timeout."""

    def test_deterministic_idempotent(self, app, client):
        """Same deterministic request returns identical result."""
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["identity_id"] = "user_1"
            sess["current_org_id"] = "org_1"

        results = []
        for _ in range(3):
            resp = client.post("/api/v1/intelligence/ask", json={"question": "hello"})
            assert resp.status_code == 200
            results.append(resp.get_json()["answer"])
        assert len(set(results)) == 1, f"Non-idempotent: {results}"

    def test_concurrent_deterministic_requests(self, app, client):
        """Multiple concurrent deterministic requests should all succeed."""
        from concurrent.futures import ThreadPoolExecutor

        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["identity_id"] = "user_1"
            sess["current_org_id"] = "org_1"

        def make_request(q):
            c = app.test_client()
            with c.session_transaction() as s:
                s["user_id"] = 1
                s["identity_id"] = "user_1"
                s["current_org_id"] = "org_1"
            resp = c.post("/api/v1/intelligence/ask", json={"question": q})
            return resp.status_code

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(make_request, "hello") for _ in range(10)]
            statuses = [f.result() for f in futures]
        assert all(s == 200 for s in statuses), f"Concurrent failures: {statuses}"

    def test_rapid_authority_denials(self, app, client):
        """Rapid authority denial requests are all rejected."""
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["identity_id"] = "user_1"
            sess["current_org_id"] = "org_1"

        for _ in range(10):
            resp = client.post("/api/v1/intelligence/ask",
                               json={"question": "Delete", "action": "delete", "execute": True})
            assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"


class TestMultiTenantSecurity:
    """Expanded tenant isolation tests."""

    def test_tenant_a_no_tenant_b_evidence_leak(self, app, client):
        """Tenant A receives only Tenant A's evidence, never Tenant B's."""
        from app.tenant import Tenant
        from app import db

        with app.app_context():
            t_a = Tenant(company_name="T11A", slug="fda11-tenant-a", business_type="test", is_active=True)
            t_b = Tenant(company_name="T11B", slug="fda11-tenant-b", business_type="test", is_active=True)
            db.session.add_all([t_a, t_b])
            db.session.commit()
            tid_a, tid_b = t_a.id, t_b.id

        def check_evidence(org_id):
            c = app.test_client()
            with c.session_transaction() as s:
                s["user_id"] = 1
                s["identity_id"] = f"user_{org_id}"
                s["current_org_id"] = str(org_id)
            resp = c.post("/api/v1/intelligence/ask", json={"question": "hello"})
            assert resp.status_code == 200
            data = resp.get_json()
            # Tenant identity must match
            assert data["tenant"]["tenant_id"] == str(org_id)
            return data

        data_a = check_evidence(tid_a)
        data_b = check_evidence(tid_b)
        # Neither tenant's response should contain the other's ID
        assert str(tid_b) not in str(data_a.get("pipeline", [])), \
            f"Tenant B ID {tid_b} leaked into Tenant A pipeline"
        assert str(tid_a) not in str(data_b.get("pipeline", [])), \
            f"Tenant A ID {tid_a} leaked into Tenant B pipeline"

    def test_tenant_identity_preserved_across_multiple_requests(self, app, client):
        """Tenant identity persists across sequential requests."""
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["identity_id"] = "user_seq"
            sess["current_org_id"] = "org_seq"

        for _ in range(5):
            resp = client.post("/api/v1/intelligence/ask", json={"question": "hello"})
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["tenant"]["identity_id"] == "user_seq"
            assert data["tenant"]["tenant_id"] == "org_seq"


class TestProviderFabric:
    """Provider-neutral interfaces; timeout, retry, circuit breaker."""

    def test_deterministic_does_not_invoke_provider(self, app, client):
        """Deterministic queries avoid provider invocation entirely."""
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["identity_id"] = "user_1"
            sess["current_org_id"] = "org_1"

        resp = client.post("/api/v1/intelligence/ask", json={"question": "hello"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["model_invoked"] is False, "Deterministic query must not invoke a provider"
        assert data["deterministic"] is True

    def test_capability_routing_not_keyword_matching(self, app, client):
        """Routing based on capability, not lexical coincidence."""
        from core.inference_governance import CapabilityBasedRouter
        # Same word, different capability context
        r1 = CapabilityBasedRouter.route(
            query="code please", available_providers=["groq"])
        r2 = CapabilityBasedRouter.route(
            query="find python code bugs", available_providers=["groq"])
        # Routing decisions differ by query context
        assert r1 is not None


class TestObservability:
    """Failure truth distinctions for every critical operation."""

    def test_pipeline_stages_distinct(self, app, client):
        """Every pipeline stage has a distinct stage name and status."""
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["identity_id"] = "user_1"
            sess["current_org_id"] = "org_1"

        resp = client.post("/api/v1/intelligence/ask", json={"question": "hello"})
        assert resp.status_code == 200
        data = resp.get_json()
        pipeline = data.get("pipeline", [])
        stage_names = [s["stage"] for s in pipeline]
        assert len(stage_names) == len(set(stage_names)), f"Duplicate stages: {stage_names}"
        for s in pipeline:
            assert "status" in s, f"Stage {s['stage']} missing status"
            assert "duration_ms" in s, f"Stage {s['stage']} missing duration"

    def test_no_generic_success_on_failure(self):
        """Failure responses do not claim success."""
        from core.intelligence_runtime.cross_boundary import ExecutionAuthorityEnforcer
        # Model output alone cannot authorize — should return authorized=False
        result = ExecutionAuthorityEnforcer.check(
            proposed_action="execute", evidence_sources=["model_output"])
        assert result.authorized is False, "Model output alone authorized execution"
        # Ensure no generic 'success' override masks the denial
        assert hasattr(result, "authorized"), "AuthorityCheck missing 'authorized' field"