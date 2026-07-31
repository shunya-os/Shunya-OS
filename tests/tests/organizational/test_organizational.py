"""Tests for Milestone I — Organizational Intelligence.

Covers all 10 core deliverables:
1. Canonical Organization Model
2. Responsibility Graph
3. Ownership Intelligence
4. Delegation Engine
5. Authority & Approval Model
6. Collaboration Intelligence
7. Organizational Health Engine
8. Institutional Memory
9. Organizational Knowledge Graph
10. Explainability Layer
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import pytest

from app.organizational import (
    OrganizationalIntelligenceEngine,
    get_organizational_intelligence,
    reset_organizational_intelligence,
)
from app.organizational.engine import (
    OrgModelStore, ResponsibilityGraph, OwnershipIntelligence,
    DelegationEngine, AuthorityApprovalModel, CollaborationIntelligence,
    OrgHealthEngine, InstitutionalMemory, OrgKnowledgeGraph,
    ExplainabilityLayer, RuntimeService,
)
from app.organizational.models import (
    OrgUnitType, OrgEntityType, DelegationStatus, AuthorityLevel,
    OrgUnit, OrgRole, RoleAssignment, Responsibility,
    Ownership, Delegation, Authority, ApprovalChain,
    Collaboration, OrgHealth, InstitutionalMemoryEntry,
    OrgKnowledgeNode, OrgKnowledgeEdge,
    OrgConfig,
)


@pytest.fixture
def config() -> OrgConfig:
    return OrgConfig()


@pytest.fixture
def rt(config) -> RuntimeService:
    return RuntimeService(config)


@pytest.fixture
def org(config) -> OrganizationalIntelligenceEngine:
    return OrganizationalIntelligenceEngine(config)


# =========================================================================
# 1. Canonical Organization Model
# =========================================================================

class TestOrgModel:

    def test_create_unit(self, rt):
        unit = rt.create_unit("Engineering", 1, OrgUnitType.DEPARTMENT.value)
        assert unit.unit_id
        assert unit.name == "Engineering"
        assert unit.tenant_id == 1

    def test_create_role(self, rt):
        role = rt.create_role("Engineer", 1, AuthorityLevel.CONTRIBUTE.value)
        assert role.role_id
        assert role.name == "Engineer"

    def test_assign_role(self, rt):
        unit = rt.create_unit("Eng", 1)
        role = rt.create_role("Dev", 1)
        assignment = rt.assign_role(role.role_id, 42, unit.unit_id, 1)
        assert assignment.assignment_id
        assert assignment.person_id == 42

    def test_get_unit_tree(self, rt):
        parent = rt.create_unit("Parent", 1)
        child = rt.create_unit("Child", 1, parent_id=parent.unit_id)
        tree = rt.store.get_unit_tree(1)
        assert len(tree) >= 1
        assert tree[0]["unit"]["name"] == "Parent"

    def test_tenant_isolation(self, rt):
        rt.create_unit("T1 Unit", 1)
        rt.create_unit("T2 Unit", 2)
        assert len(rt.store.get_units(1)) == 1
        assert len(rt.store.get_units(2)) == 1

    def test_to_dict(self, rt):
        unit = rt.create_unit("Test", 1)
        d = unit.to_dict()
        assert d["name"] == "Test"
        assert "unit_id" in d


# =========================================================================
# 2. Responsibility Graph
# =========================================================================

class TestResponsibilityGraph:

    def test_add_responsibility(self, rt):
        resp = rt.add_responsibility("role1", "execution", "exec1", 1,
                                     description="Handle execution")
        assert resp.responsibility_id
        assert resp.role_id == "role1"

    def test_resolve_owners(self, rt):
        role = rt.create_role("Owner", 1)
        rt.add_responsibility(role.role_id, "execution", "exec1", 1)
        unit = rt.create_unit("Test", 1)
        rt.assign_role(role.role_id, 100, unit.unit_id, 1)
        owners = rt.resolve_responsible("execution", "exec1", 1)
        assert len(owners) >= 1
        assert owners[0]["person_id"] == 100

    def test_get_for_role(self, rt):
        role = rt.create_role("Mgr", 1)
        rt.add_responsibility(role.role_id, "execution", "e1", 1)
        rt.add_responsibility(role.role_id, "obligation", "o1", 1)
        resps = rt.resp_graph.get_for_role(role.role_id)
        assert len(resps) == 2

    def test_get_for_entity(self, rt):
        rt.add_responsibility("r1", "execution", "exec1", 1)
        resps = rt.resp_graph.get_for_entity("execution", "exec1", 1)
        assert len(resps) == 1

    def test_remove(self, rt):
        resp = rt.add_responsibility("r1", "execution", "e1", 1)
        assert rt.resp_graph.remove(resp.responsibility_id) is True
        assert rt.resp_graph.remove("nonexistent") is False

    def test_determinism(self, rt):
        rt.add_responsibility("r1", "execution", "e1", 1)
        o1 = rt.resolve_responsible("execution", "e1", 1)
        o2 = rt.resolve_responsible("execution", "e1", 1)
        assert o1 == o2


# =========================================================================
# 3. Ownership Intelligence
# =========================================================================

class TestOwnershipIntelligence:

    def test_set_and_get(self, rt):
        o = rt.set_ownership("execution", "exec1", "role1", 1)
        assert o.ownership_id
        fetched = rt.get_ownership("execution", "exec1", 1)
        assert fetched is not None
        assert fetched.owner_id == "role1"

    def test_transfer_ownership(self, rt):
        rt.set_ownership("execution", "exec1", "role1", 1)
        rt.ownership.transfer("execution", "exec1", 1, "role2")
        fetched = rt.get_ownership("execution", "exec1", 1)
        assert fetched.owner_id == "role2"

    def test_get_owned_by(self, rt):
        rt.set_ownership("execution", "e1", "role1", 1)
        rt.set_ownership("obligation", "o1", "role1", 1)
        owned = rt.ownership.get_owned_by("role1", 1)
        assert len(owned) == 2

    def test_no_owner(self, rt):
        fetched = rt.get_ownership("execution", "nonexistent", 1)
        assert fetched is None


# =========================================================================
# 4. Delegation Engine
# =========================================================================

class TestDelegationEngine:

    def test_delegate(self, rt):
        d = rt.delegate("role1", "role2", 1, AuthorityLevel.APPROVE.value,
                        reason="On leave")
        assert d.status == DelegationStatus.ACTIVE.value
        assert d.authority_level == AuthorityLevel.APPROVE.value

    def test_revoke(self, rt):
        d = rt.delegate("role1", "role2", 1)
        assert rt.revoke_delegation(d.delegation_id) is True
        assert d.status == DelegationStatus.REVOKED.value

    def test_get_active(self, rt):
        rt.delegate("role1", "role2", 1)
        active = rt.delegations.get_active("role2", 1)
        assert len(active) >= 1

    def test_expired_delegation(self, config):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        d = Delegation(tenant_id=1, from_role_id="r1", to_role_id="r2",
                       expires_at=past, authority_level=AuthorityLevel.READ.value)
        eng = DelegationEngine(config)
        eng.delegate(d)
        active = eng.get_active("r2", 1)
        assert len(active) == 0

    def test_auto_expire_max_duration(self, config):
        far_future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        d = Delegation(tenant_id=1, from_role_id="r1", to_role_id="r2",
                       expires_at=far_future)
        eng = DelegationEngine(config)
        eng.delegate(d)
        # Should be capped to max duration (30 days)
        assert d.expires_at != far_future


# =========================================================================
# 5. Authority & Approval Model
# =========================================================================

class TestAuthorityApproval:

    def test_grant_and_check(self, rt):
        rt.grant_authority("role1", "approve_budget", "execution", 1,
                           AuthorityLevel.APPROVE.value)
        assert rt.check_authority("role1", "approve_budget", "execution",
                                  "exec1", 1) is True

    def test_no_authority(self, rt):
        assert rt.check_authority("role1", "approve_budget", "execution",
                                  "exec1", 1) is False

    def test_approval_chain(self, rt):
        chain = ApprovalChain(
            tenant_id=1, decision_type="budget_approval",
            entity_type="execution", entity_id="exec1",
            steps=[
                {"role_id": "manager", "order": 1, "status": "pending"},
                {"role_id": "director", "order": 2, "status": "pending"},
            ],
        )
        rt.authority.create_chain(chain)
        r1 = rt.authority.approve_step(chain.chain_id, "manager", 1)
        assert r1["status"] == "in_progress"
        r2 = rt.authority.approve_step(chain.chain_id, "director", 1)
        assert r2["status"] == "approved"

    def test_reject_chain(self, rt):
        chain = ApprovalChain(
            tenant_id=1, decision_type="test",
            entity_type="execution", entity_id="exec1",
            steps=[{"role_id": "reviewer", "order": 1, "status": "pending"}],
        )
        rt.authority.create_chain(chain)
        r = rt.authority.reject_chain(chain.chain_id, 1)
        assert r["status"] == "rejected"


# =========================================================================
# 6. Collaboration Intelligence
# =========================================================================

class TestCollaborationIntelligence:

    def test_record(self, rt):
        c = rt.record_collaboration("role1", "role2", "execution", "exec1", 1)
        assert c.collab_id
        assert c.frequency == 1

    def test_frequency_increment(self, rt):
        rt.record_collaboration("role1", "role2", "execution", "exec1", 1)
        rt.record_collaboration("role1", "role2", "execution", "exec1", 1)
        collabs = rt.collab.get_for_role("role1")
        assert len(collabs) == 1
        assert collabs[0].frequency == 2

    def test_network_density(self, rt):
        rt.record_collaboration("r1", "r2", "execution", "e1", 1)
        rt.record_collaboration("r1", "r3", "execution", "e1", 1)
        density = rt.collab.get_network_density(1)
        assert density > 0.0

    def test_tenant_isolation(self, rt):
        rt.record_collaboration("r1", "r2", "execution", "e1", 1)
        rt.record_collaboration("r3", "r4", "execution", "e2", 2)
        assert rt.collab.get_network_density(1) > 0.0
        assert rt.collab.get_network_density(3) == 0.0


# =========================================================================
# 7. Organizational Health
# =========================================================================

class TestOrgHealth:

    def test_assess_unit(self, rt):
        unit = rt.create_unit("Engineering", 1)
        health = rt.assess_health(unit.unit_id, 1)
        assert health.unit_id == unit.unit_id
        assert health.overall in ("healthy", "fair", "needs_attention", "critical")

    def test_health_with_roles_and_assignments(self, rt):
        unit = rt.create_unit("Team", 1)
        role = rt.create_role("Dev", 1)
        rt.assign_role(role.role_id, 42, unit.unit_id, 1)
        health = rt.assess_health(unit.unit_id, 1)
        assert health.role_fill_rate > 0.0

    def test_unknown_unit(self, rt):
        health = rt.assess_health("nonexistent", 1)
        assert health.overall == "unknown"

    def test_to_dict(self, rt):
        health = rt.assess_health("test", 1)
        d = health.to_dict()
        assert "overall" in d
        assert "role_fill_rate" in d


# =========================================================================
# 8. Institutional Memory
# =========================================================================

class TestInstitutionalMemory:

    def test_add_and_get(self, rt):
        rt.add_memory("onboarding_process", "Steps for new hires", 1)
        entry = rt.get_memory("onboarding_process", 1)
        assert entry is not None
        assert entry.topic == "onboarding_process"

    def test_supersession(self, rt):
        rt.add_memory("policy", "Old version", 1)
        rt.add_memory("policy", "New version", 1)
        entry = rt.get_memory("policy", 1)
        assert entry.content == "New version"

    def test_get_history(self, rt):
        rt.add_memory("decision", "First", 1)
        rt.add_memory("decision", "Second", 1)
        history = rt.memory.get_history("decision", 1)
        assert len(history) == 2

    def test_tenant_isolation(self, rt):
        rt.add_memory("topic", "Tenant 1", 1)
        rt.add_memory("topic", "Tenant 2", 2)
        e1 = rt.get_memory("topic", 1)
        e2 = rt.get_memory("topic", 2)
        assert e1.content == "Tenant 1"
        assert e2.content == "Tenant 2"


# =========================================================================
# 9. Organizational Knowledge Graph
# =========================================================================

class TestOrgKnowledgeGraph:

    def test_add_node_and_edge(self, rt):
        kg = rt.kg
        n1 = kg.add_node(OrgKnowledgeNode(
            tenant_id=1, entity_type="role", entity_id="r1", label="Role 1"))
        n2 = kg.add_node(OrgKnowledgeNode(
            tenant_id=1, entity_type="role", entity_id="r2", label="Role 2"))
        kg.add_edge(OrgKnowledgeEdge(
            tenant_id=1, from_node_id=n1.node_id, to_node_id=n2.node_id,
            relationship="collaborates_with"))
        neighbors = kg.get_neighbors(n1.node_id)
        assert len(neighbors) == 1
        assert neighbors[0]["edge"]["relationship"] == "collaborates_with"

    def test_find_path(self, rt):
        kg = rt.kg
        n1 = kg.add_node(OrgKnowledgeNode(tenant_id=1, entity_type="unit", entity_id="u1", label="U1"))
        n2 = kg.add_node(OrgKnowledgeNode(tenant_id=1, entity_type="unit", entity_id="u2", label="U2"))
        n3 = kg.add_node(OrgKnowledgeNode(tenant_id=1, entity_type="unit", entity_id="u3", label="U3"))
        kg.add_edge(OrgKnowledgeEdge(tenant_id=1, from_node_id=n1.node_id, to_node_id=n2.node_id, relationship="contains"))
        kg.add_edge(OrgKnowledgeEdge(tenant_id=1, from_node_id=n2.node_id, to_node_id=n3.node_id, relationship="contains"))
        path = kg.find_path(n1.node_id, n3.node_id)
        assert len(path) == 2

    def test_build_from_org_data(self, rt):
        unit = rt.create_unit("Team", 1)
        role = rt.create_role("Lead", 1)
        rt.add_responsibility(role.role_id, "execution", "e1", 1)
        rt.rebuild_knowledge_graph(1)
        node = rt.kg._find_node(OrgEntityType.ROLE.value, role.role_id)
        assert node is not None

    def test_query_knowledge_graph(self, rt):
        rt.create_unit("Team", 1)
        rt.rebuild_knowledge_graph(1)
        unit = rt.store.get_units(1)[0]
        neighbors = rt.query_knowledge_graph(OrgEntityType.ORG_UNIT.value, unit.unit_id)
        assert isinstance(neighbors, list)


# =========================================================================
# 10. Explainability & Facade
# =========================================================================

class TestExplainabilityAndFacade:

    def test_singleton(self):
        reset_organizational_intelligence()
        e1 = get_organizational_intelligence()
        e2 = get_organizational_intelligence()
        assert e1 is e2

    def test_facade_create_unit(self, org):
        unit = org.create_unit("Design", 1)
        assert unit.name == "Design"

    def test_facade_create_role(self, org):
        role = org.create_role("Designer", 1)
        assert role.name == "Designer"

    def test_facade_assign_role(self, org):
        unit = org.create_unit("Team", 1)
        role = org.create_role("Dev", 1)
        a = org.assign_role(role.role_id, 42, unit.unit_id, 1)
        assert a.person_id == 42

    def test_facade_add_responsibility(self, org):
        org.add_responsibility("r1", "execution", "e1", 1)
        owners = org.resolve_responsible("execution", "e1", 1)
        assert isinstance(owners, list)

    def test_facade_set_ownership(self, org):
        o = org.set_ownership("execution", "e1", "role1", 1)
        assert o.owner_id == "role1"

    def test_facade_delegate(self, org):
        d = org.delegate("r1", "r2", 1, reason="Coverage")
        assert d.status == DelegationStatus.ACTIVE.value

    def test_facade_check_authority(self, org):
        assert org.check_authority("r1", "approve", "execution", "e1", 1) is False

    def test_facade_collaboration(self, org):
        c = org.record_collaboration("r1", "r2", "execution", "e1", 1)
        assert c.frequency == 1

    def test_facade_health(self, org):
        unit = org.create_unit("Test", 1)
        health = org.assess_health(unit.unit_id, 1)
        assert health.overall is not None

    def test_facade_memory(self, org):
        org.add_memory("process", "doc", 1)
        entry = org.runtime.get_memory("process", 1)
        assert entry.content == "doc"

    def test_facade_knowledge_graph(self, org):
        org.create_unit("Team", 1)
        org.rebuild_knowledge_graph(1)
        assert org.runtime.kg._nodes  # nodes were created

    def test_facade_explain_health(self, org):
        unit = org.create_unit("Team", 1)
        exp = org.explain_health(unit.unit_id, 1)
        assert "conclusion" in exp

    def test_facade_stats(self, org):
        org.create_unit("Team", 1)
        org.create_role("Dev", 1)
        s = org.stats()
        assert s["total_units"] >= 1
        assert s["total_roles"] >= 1

    def test_runtime_property(self, org):
        assert hasattr(org, 'runtime')
        assert isinstance(org.runtime, RuntimeService)


# =========================================================================
# Edge Cases & Concurrency
# =========================================================================

class TestEdgeCases:

    def test_empty_org(self, rt):
        assert rt.stats()["total_units"] == 0
        assert rt.stats()["total_roles"] == 0

    def test_unknown_tenant(self, rt):
        assert rt.store.get_units(999) == []

    def test_explain_responsibility(self, rt):
        resp = rt.add_responsibility("r1", "execution", "e1", 1)
        exp = rt.explain_responsibility(resp.responsibility_id)
        assert "conclusion" in exp

    def test_engine_reset(self):
        reset_organizational_intelligence()
        assert get_organizational_intelligence() is not None
        reset_organizational_intelligence()
        assert get_organizational_intelligence() is not None

    def test_concurrent_creations(self, config):
        rt = RuntimeService(config)
        results = []
        errors = []
        import threading

        def create(n: int):
            try:
                u = rt.create_unit(f"Unit-{n}", 1)
                results.append(u.unit_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create, args=(i,)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0
        assert len(results) == 10