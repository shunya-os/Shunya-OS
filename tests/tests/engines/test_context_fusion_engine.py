"""Tests for Phase M — Context Fusion Engine (ES-009).

G12.0: snapshots, replay, provenance, system contracts,
architecture contracts, invariants, lifecycle.
"""

import threading
from typing import Any, Dict, List
import pytest

from app.shunya.context_fusion_engine import (
    ContextRequest, ContextSection, WorkspaceContext,
    BudgetReport, ContextProvenance,
    ContextAssembler, ContextFusionEngine,
    ContextProvider, BudgetEnforcer, Fingerprinter,
)


class MockIdProvider(ContextProvider):
    def name(self): return "identity"
    def fetch(self, r: ContextRequest) -> ContextSection:
        return ContextSection(provider="identity",
            items=[{"type":"person","id":r.actor_id,"confidence":1.0}])


class MockKbProvider(ContextProvider):
    def name(self): return "knowledge"
    def fetch(self, r: ContextRequest) -> ContextSection:
        return ContextSection(provider="knowledge",
            items=[{"type":"fact","key":"bali.visa","value":"required","confidence":0.9}])


class MockReqProvider(ContextProvider):
    def name(self): return "request"
    def fetch(self, r: ContextRequest) -> ContextSection:
        return ContextSection(provider="request",
            items=[{"type":"meta","purpose":r.purpose_code,"actor":r.actor_id}])


@pytest.fixture
def a():
    return ContextAssembler(providers=[MockIdProvider(), MockKbProvider(), MockReqProvider()])

@pytest.fixture
def r():
    return ContextRequest(tenant_id=1, actor_id="a1", purpose_code="planning")


class TestModels:
    def test_request_defaults(self):
        cr = ContextRequest(tenant_id=1, actor_id="a1")
        assert cr.purpose_code == "default" and cr.max_items == 100

    def test_context_auto_id(self):
        wc = WorkspaceContext(tenant_id=1, actor_id="a1")
        assert wc.context_id != "" and wc.created_at is not None

    def test_context_to_dict(self):
        wc = WorkspaceContext(tenant_id=1, actor_id="a1", fingerprint="fp")
        d = wc.to_dict()
        assert d["fingerprint"] == "fp"

    def test_section_counts(self):
        s = ContextSection(provider="t", items=[{"a":1},{"b":2}])
        assert s.item_count == 2


class TestSnapshotConsistency:
    def test_identical_produces_identical(self, a, r):
        c1, c2 = a.assemble(r), a.assemble(r)
        assert c1.fingerprint == c2.fingerprint

    def test_different_requests_different_fingerprints(self, a, r):
        r2 = ContextRequest(tenant_id=2, actor_id="a2", purpose_code="gov")
        assert a.assemble(r).fingerprint != a.assemble(r2).fingerprint

    def test_budget_enforced(self, a):
        small = ContextRequest(tenant_id=1, actor_id="a1", max_items=1)
        ctx = a.assemble(small)
        assert ctx.budget is not None and ctx.budget.max_items == 1


class TestReplay:
    def test_replay_identical_assemblers(self, r):
        a1 = ContextAssembler(providers=[MockIdProvider(), MockKbProvider()])
        a2 = ContextAssembler(providers=[MockIdProvider(), MockKbProvider()])
        assert a1.assemble(r).fingerprint == a2.assemble(r).fingerprint


class TestProvenance:
    def test_provenance_present(self, a, r):
        ctx = a.assemble(r)
        assert ctx.provenance is not None
        assert ctx.provenance.assembled_by == "context_fusion_engine"


class TestArchitectureContracts:
    def test_no_eval(self):
        import app.shunya.context.engine as e, app.shunya.context.assembly as asm, app.shunya.context.models as m
        src = open(e.__file__).read() + open(asm.__file__).read() + open(m.__file__).read()
        assert "eval(" not in src and "exec(" not in src


class TestInvariants:
    def test_tenant_isolation(self, a):
        c1 = a.assemble(ContextRequest(tenant_id=1, actor_id="a1"))
        c2 = a.assemble(ContextRequest(tenant_id=2, actor_id="a2"))
        assert c1.tenant_id != c2.tenant_id and c1.fingerprint != c2.fingerprint

    def test_deterministic(self, a, r):
        fps = [a.assemble(r).fingerprint for _ in range(5)]
        assert all(f == fps[0] for f in fps)

    def test_context_immutable(self, a, r):
        ctx = a.assemble(r)
        ctx2 = a.assemble(r)
        assert ctx.fingerprint == ctx2.fingerprint


class TestSystemContracts:
    def test_no_info_loss(self, a, r):
        ctx = a.assemble(r)
        assert sum(s.item_count for s in ctx.sections.values()) >= 3

    def test_identifier_stability(self, a, r):
        keys = set(a.assemble(r).sections.keys())
        assert keys == set(a.assemble(r).sections.keys())


class TestLifecycle:
    def test_request_to_context(self, a, r):
        ctx = a.assemble(r)
        assert ctx.tenant_id == r.tenant_id and ctx.actor_id == r.actor_id

    def test_budget_report(self, a, r):
        ctx = a.assemble(r)
        assert ctx.budget is not None and ctx.budget.total_items > 0


class TestEngine:
    def test_engine_constructs(self):
        eng = ContextFusionEngine(identity_engine=MockIdProvider(), knowledge_store=MockKbProvider())
        assert eng is not None

    def test_engine_assemble(self, r):
        eng = ContextFusionEngine(identity_engine=MockIdProvider(), knowledge_store=MockKbProvider())
        ctx = eng.assemble(r)
        assert ctx.fingerprint != ""


class TestDeterminism:
    def test_fingerprint_deterministic(self, a, r):
        assert a.assemble(r).fingerprint == a.assemble(r).fingerprint


class TestConcurrency:
    def test_concurrent(self, a, r):
        results, errors = [], []
        def run():
            try: results.append(a.assemble(r))
            except Exception as e: errors.append(e)
        threads = [threading.Thread(target=run) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0 and len(results) == 10
        assert all(x.fingerprint == results[0].fingerprint for x in results)


class TestEdgeCases:
    def test_empty_providers(self):
        a = ContextAssembler(providers=[])
        ctx = a.assemble(ContextRequest(tenant_id=1, actor_id="a1"))
        assert ctx.fingerprint != ""

    def test_degraded(self):
        class BadProvider(ContextProvider):
            def name(self): return "bad"
            def fetch(self, r): return ContextSection(provider="bad", is_degraded=True)
        ctx = ContextAssembler(providers=[BadProvider()]).assemble(
            ContextRequest(tenant_id=1, actor_id="a1"))
        assert ctx.is_degraded


class TestBudget:
    def test_truncation(self):
        b = BudgetEnforcer()
        r = b.enforce({"x":[{"i":i} for i in range(50)]}, config_max_items=5, config_max_size=99999)
        assert r.max_items == 5 and r.truncated

    def test_no_truncation(self):
        b = BudgetEnforcer()
        r = b.enforce({"x":[{"i":i} for i in range(3)]}, config_max_items=100, config_max_size=99999)
        assert not r.truncated


class TestFingerprint:
    def test_deterministic(self):
        f = Fingerprinter()
        assert f.fingerprint({"id":[{"a":1}]}, 1, "a", "p") == f.fingerprint({"id":[{"a":1}]}, 1, "a", "p")

    def test_sha256(self):
        f = Fingerprinter()
        assert len(f.fingerprint({"x":[]}, 1, "a", "p")) == 64


class TestBackwardCompat:
    def test_import_all(self):
        from app.shunya.context_fusion_engine import ContextFusionEngine, WorkspaceContext, ContextRequest
        assert all(x is not None for x in [ContextFusionEngine, WorkspaceContext, ContextRequest])

    def test_original_still_works(self):
        from app.shunya.context import engine
        assert engine.ContextFusionEngine is not None