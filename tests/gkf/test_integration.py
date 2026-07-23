"""Integration tests for GKF — graph node creation and provenance integration.

Tests that GKF elements can be stored as graph nodes and linked
to provenance records using the existing architecture.
"""

import pytest
from app.gkf.models import (
    GovernedCollection, Article, Principle, GKFEvidence,
    Amendment, GKFVersion, Reference,
)
from app.gkf.identity import generate_collection_id, generate_principle_id, generate_article_id
from app.graph.node import Node, InMemoryNodeStore, NodeStatus
from app.evidence.models import Evidence, InMemoryEvidenceStore
from app.evidence.provenance_models import ProvenanceGraph, SourceIdentity


# =========================================================================
# Graph Integration
# =========================================================================

class TestGraphNodeCreation:
    """GKF elements can be stored as graph Nodes."""

    def test_collection_as_graph_node(self):
        gc = GovernedCollection(name="SHUNYA Constitution")
        node = Node(
            node_id=gc.collection_id,
            node_type="gkf_collection",
            attributes={"name": gc.name, "status": gc.status},
            status=NodeStatus.ACTIVE,
        )
        store = InMemoryNodeStore()
        stored = store.create(node)
        retrieved = store.get(gc.collection_id)
        assert retrieved is not None
        assert retrieved.node_id == gc.collection_id
        assert retrieved.attributes["name"] == "SHUNYA Constitution"

    def test_principle_as_graph_node(self):
        p = Principle(collection_id="gkc_shunya_constitution", name="human_first", statement="People first.")
        node = Node(
            node_id=p.principle_id,
            node_type="gkf_principle",
            attributes={
                "name": p.name,
                "statement": p.statement,
                "status": p.status,
            },
            status=NodeStatus.ACTIVE,
        )
        store = InMemoryNodeStore()
        stored = store.create(node)
        retrieved = store.get(p.principle_id)
        assert retrieved is not None
        assert retrieved.attributes["statement"] == "People first."

    def test_article_as_graph_node(self):
        a = Article(collection_id="gkc_shunya_constitution", number=1, title="Human First")
        node = Node(
            node_id=a.article_id,
            node_type="gkf_article",
            attributes={"number": a.number, "title": a.title, "version": a.version},
        )
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(a.article_id)
        assert retrieved is not None

    def test_evidence_as_graph_node(self):
        e = GKFEvidence(collection_id="gkc_shunya_constitution", source_type="document", local_id="constitution")
        node = Node(
            node_id=e.evidence_id,
            node_type="gkf_evidence",
            attributes={"source_type": e.source_type, "title": e.title},
        )
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(e.evidence_id)
        assert retrieved is not None

    def test_amendment_as_graph_node(self):
        a = Amendment(target_id="gkc_shunya_constitution:art_1", number=1)
        node = Node(
            node_id=a.amendment_id,
            node_type="gkf_amendment",
            attributes={"amendment_type": a.amendment_type, "target_id": a.target_id},
        )
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(a.amendment_id)
        assert retrieved is not None

    def test_version_as_graph_node(self):
        v = GKFVersion(element_id="gkc_shunya_constitution:art_1", number=1)
        node = Node(
            node_id=v.version_id,
            node_type="gkf_version",
            attributes={"element_id": v.element_id, "number": v.number},
        )
        store = InMemoryNodeStore()
        store.create(node)
        retrieved = store.get(v.version_id)
        assert retrieved is not None


# =========================================================================
# Provenance Integration
# =========================================================================

class TestProvenanceIntegration:
    """GKF elements can be linked to provenance records."""

    def test_principle_provenance_origin(self):
        pg = ProvenanceGraph()
        p = Principle(collection_id="gkc_shunya_constitution", name="human_first", statement="People first.")
        pg.set_origin(p.principle_id, "src_founder_directive")
        assert pg.get_origin(p.principle_id) == "src_founder_directive"

    def test_evidence_chain_for_article(self):
        pg = ProvenanceGraph()
        a = Article(collection_id="gkc_shunya_constitution", number=1)
        e = GKFEvidence(collection_id="gkc_shunya_constitution", source_type="document", local_id="constitution")
        pg.set_origin(a.article_id, e.evidence_id)
        assert pg.get_origin(a.article_id) == e.evidence_id

    def test_principle_derivation_from_article(self):
        pg = ProvenanceGraph()
        a = Article(collection_id="gkc_shunya_constitution", number=1)
        p = Principle(collection_id="gkc_shunya_constitution", name="human_first", statement="X")
        pg.add_derivation(p.principle_id, a.article_id)
        assert pg.get_derivation(p.principle_id) == a.article_id

    def test_amendment_citation(self):
        from app.evidence.provenance_models import Citation
        pg = ProvenanceGraph()
        a = Article(collection_id="gkc_test", number=1, body="Original")
        am = Amendment(target_id=a.article_id, number=1, reason="Updated body")
        c = Citation(citing_evidence_id=am.amendment_id, cited_evidence_id=a.article_id)
        pg.add_citation(c)
        assert len(pg.get_citations(am.amendment_id)) == 1

    def test_full_gkf_provenance_chain(self):
        """A complete GKF provenance chain: Collection → Article → Principle."""
        pg = ProvenanceGraph()
        gc = GovernedCollection(name="SHUNYA Constitution")
        a = Article(collection_id=gc.collection_id, number=1)
        p = Principle(collection_id=gc.collection_id, name="human_first", statement="People first.")

        pg.set_origin(a.article_id, gc.collection_id)
        pg.add_derivation(p.principle_id, a.article_id)

        article_prov = pg.get_full_provenance(a.article_id)
        principle_prov = pg.get_full_provenance(p.principle_id)

        assert article_prov["origin"] == gc.collection_id
        assert principle_prov["derivation"] == a.article_id
        assert a.article_id in principle_prov["derivation_chain"]


# =========================================================================
# Evidence Store Integration
# =========================================================================

class TestEvidenceStoreIntegration:
    """GKF evidence can be stored in the Evidence Store."""

    def test_evidence_can_be_stored(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="constitution")
        ev = Evidence(
            evidence_id=e.evidence_id,
            target_id=e.collection_id,
            target_type="gkf_collection",
            metadata={"source_type": e.source_type, "source_path": e.source_path},
        )
        store = InMemoryEvidenceStore()
        stored = store.create(ev)
        retrieved = store.get(e.evidence_id)
        assert retrieved is not None
        assert retrieved.evidence_id == e.evidence_id

    def test_evidence_identity_unique(self):
        e1 = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="test")
        e2 = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="other")
        ev1 = Evidence(evidence_id=e1.evidence_id, target_id="t1", target_type="test")
        ev2 = Evidence(evidence_id=e2.evidence_id, target_id="t2", target_type="test")
        store = InMemoryEvidenceStore()
        store.create(ev1)
        store.create(ev2)
        assert store.count() == 2


# =========================================================================
# Identity Cross-Reference Tests
# =========================================================================

class TestIdentityCrossReference:
    def test_principle_identity_consistent_across_models(self):
        """Principle identity generated via both model and identity function."""
        pid1 = generate_principle_id("gkc_test", "agency")
        p = Principle(collection_id="gkc_test", name="agency", statement="X")
        assert pid1 == p.principle_id

    def test_article_identity_consistent(self):
        aid1 = generate_article_id("gkc_test", 1)
        a = Article(collection_id="gkc_test", number=1)
        assert aid1 == a.article_id

    def test_collection_identity_consistent(self):
        cid1 = generate_collection_id("SHUNYA Constitution")
        gc = GovernedCollection(name="SHUNYA Constitution")
        assert cid1 == gc.collection_id