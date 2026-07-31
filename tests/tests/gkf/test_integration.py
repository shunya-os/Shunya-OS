"""Integration tests for GKF — graph node creation and provenance integration.

GKF-001A: Tests for enrichment models integrated with graph and provenance.
"""

import pytest
from app.gkf.models import (
    GovernedCollection, Article, GoverningPrinciple, GKFEvidence,
    Amendment, GKFVersion, Authority, Citation, Commentary, Example,
    ImplementationGuidance,
)
from app.graph.node import Node, InMemoryNodeStore, NodeStatus
from app.evidence.models import Evidence, InMemoryEvidenceStore
from app.evidence.provenance_models import ProvenanceGraph, Citation as ProvCitation


class TestGraphNodeIntegration:
    def test_governing_principle_as_graph_node(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="human_first", statement="People first.")
        node = Node(node_id=gp.governing_principle_id, node_type="gkf_governing_principle",
                     attributes={"name": gp.name, "statement": gp.statement})
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(gp.governing_principle_id)
        assert retrieved is not None

    def test_authority_as_graph_node(self):
        a = Authority(collection_id="gkc_test", name="founder", authority_type="founder")
        node = Node(node_id=a.authority_id, node_type="gkf_authority",
                     attributes={"name": a.name, "authority_type": a.authority_type})
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(a.authority_id)
        assert retrieved is not None

    def test_citation_as_graph_node(self):
        c = Citation(source_id="gkc_test:gp_test", external_source="GDPR")
        node = Node(node_id=c.citation_id, node_type="gkf_citation",
                     attributes={"external_source": c.external_source})
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(c.citation_id)
        assert retrieved is not None

    def test_commentary_as_graph_node(self):
        c = Commentary(governing_principle_id="gkc_test:gp_test", number=1, body="Explanation")
        node = Node(node_id=c.commentary_id, node_type="gkf_commentary",
                     attributes={"body": c.body})
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(c.commentary_id)
        assert retrieved is not None

    def test_example_as_graph_node(self):
        e = Example(governing_principle_id="gkc_test:gp_test", number=1, body="Illustration")
        node = Node(node_id=e.example_id, node_type="gkf_example",
                     attributes={"body": e.body})
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(e.example_id)
        assert retrieved is not None

    def test_implementation_guidance_as_graph_node(self):
        g = ImplementationGuidance(governing_principle_id="gkc_test:gp_test", name="authz",
                                    body="Use RBAC")
        node = Node(node_id=g.guidance_id, node_type="gkf_implementation_guidance",
                     attributes={"name": g.name, "body": g.body})
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(g.guidance_id)
        assert retrieved is not None


class TestProvenanceIntegration:
    def test_gp_provenance_with_authority(self):
        pg = ProvenanceGraph()
        gp = GoverningPrinciple(collection_id="gkc_test", name="human_first", statement="X",
                                 authority_id="gkc_test:auth_founder")
        pg.set_origin(gp.governing_principle_id, "gkc_test:auth_founder")
        assert pg.get_origin(gp.governing_principle_id) == "gkc_test:auth_founder"

    def test_citation_provenance_chain(self):
        pg = ProvCitation(citing_evidence_id="gkc_test:gp_test", cited_evidence_id="GDPR")
        assert pg.citing_evidence_id == "gkc_test:gp_test"


class TestEvidenceStoreIntegration:
    def test_gkf_evidence_stored(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="test")
        ev = Evidence(evidence_id=e.evidence_id, target_id=e.collection_id,
                       target_type="gkf_collection")
        store = InMemoryEvidenceStore()
        store.create(ev)
        assert store.get(e.evidence_id) is not None


class TestIdentityCrossReference:
    def test_governing_principle_id_consistent(self):
        from app.gkf.identity import generate_governing_principle_id
        pid1 = generate_governing_principle_id("gkc_test", "agency")
        gp = GoverningPrinciple(collection_id="gkc_test", name="agency", statement="X")
        assert pid1 == gp.governing_principle_id

    def test_authority_id_consistent(self):
        from app.gkf.identity import generate_authority_id
        aid1 = generate_authority_id("gkc_test", "founder")
        a = Authority(collection_id="gkc_test", name="founder")
        assert aid1 == a.authority_id