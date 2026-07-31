"""Tests for Memory & Knowledge Runtime."""

import pytest

from core.memory_knowledge_runtime import (
    EmbeddingProvider,
    MemoryKnowledgeRuntime,
    MemoryType,
    RetrievalQuery,
)


@pytest.fixture
def runtime():
    return MemoryKnowledgeRuntime()


class TestStoreAndRetrieve:
    def test_store(self, runtime):
        obj = runtime.store("user:1", {"name": "Alice"}, MemoryType.OBJECT)
        assert obj.key == "user:1"
        assert obj.value["name"] == "Alice"
        assert obj.lifecycle.value == "indexed"

    def test_get_by_id(self, runtime):
        obj = runtime.store("k1", "v1")
        fetched = runtime.get(obj.memory_id)
        assert fetched.key == "k1"

    def test_get_by_key(self, runtime):
        runtime.store("k2", "v2")
        fetched = runtime.get_by_key("k2")
        assert fetched.value == "v2"

    def test_update(self, runtime):
        runtime.store("k3", "v3a")
        obj = runtime.store("k3", "v3b")
        assert obj.version == 2

    def test_delete(self, runtime):
        obj = runtime.store("k4", "v4")
        assert runtime.delete(obj.memory_id) is True
        assert runtime.get(obj.memory_id) is None

    def test_delete_nonexistent(self, runtime):
        assert runtime.delete("nonexistent") is False


class TestMemoryTypes:
    def test_semantic(self, runtime):
        obj = runtime.store("fact:earth_round", True, MemoryType.SEMANTIC)
        assert obj.memory_type == MemoryType.SEMANTIC

    def test_episodic(self, runtime):
        obj = runtime.store("event:login", {"time": "now"}, MemoryType.EPISODIC)
        assert obj.memory_type == MemoryType.EPISODIC

    def test_procedural(self, runtime):
        obj = runtime.store("howto:reset_password", ["step1", "step2"], MemoryType.PROCEDURAL)
        assert obj.memory_type == MemoryType.PROCEDURAL


class TestKnowledgeGraph:
    def test_relate(self, runtime):
        a = runtime.store("person:1", "Alice")
        b = runtime.store("person:2", "Bob")
        edge = runtime.relate(a.memory_id, b.memory_id, "knows")
        assert edge.relationship_type == "knows"

    def test_get_relationships(self, runtime):
        a = runtime.store("x", "X")
        b = runtime.store("y", "Y")
        runtime.relate(a.memory_id, b.memory_id, "connects")
        edges = runtime.get_relationships(a.memory_id)
        assert len(edges) == 1

    def test_traverse(self, runtime):
        a = runtime.store("a", "A")
        b = runtime.store("b", "B")
        c = runtime.store("c", "C")
        runtime.relate(a.memory_id, b.memory_id, "links")
        runtime.relate(b.memory_id, c.memory_id, "links")
        results = runtime.traverse(a.memory_id, max_depth=2)
        assert len(results) >= 2


class TestEvidence:
    def test_add_evidence(self, runtime):
        obj = runtime.store("k", "v")
        ev = runtime.add_evidence(obj.memory_id, "test", {"score": 95})
        assert ev.source == "test"

    def test_get_evidence(self, runtime):
        obj = runtime.store("ke", "ve")
        runtime.add_evidence(obj.memory_id, "src1", "data1")
        runtime.add_evidence(obj.memory_id, "src2", "data2")
        assert len(runtime.get_evidence(obj.memory_id)) == 2


class TestSearch:
    def test_keyword_search(self, runtime):
        runtime.store("doc:1", "The quick brown fox")
        runtime.store("doc:2", "Jumped over the lazy dog")
        q = RetrievalQuery(query="brown fox", top_k=5)
        results = runtime.search(q)
        assert len(results) >= 1
        assert any("brown" in r.snippet for r in results)

    def test_search_with_types(self, runtime):
        runtime.store("doc:3", "semantic data", MemoryType.SEMANTIC)
        runtime.store("obj:1", "object data", MemoryType.OBJECT)
        q = RetrievalQuery(query="data", memory_types=[MemoryType.SEMANTIC])
        results = runtime.search(q)
        assert all(r.memory_type == MemoryType.SEMANTIC for r in results)


class TestObservability:
    def test_stats(self, runtime):
        runtime.store("s1", "x")
        runtime.store("s2", "y")
        stats = runtime.get_stats()
        assert stats.total_objects == 2

    def test_traces(self, runtime):
        runtime.store("t1", "val")
        traces = runtime.get_traces()
        assert len(traces) >= 1

    def test_health(self, runtime):
        runtime.store("h1", "data")
        hc = runtime.health_check()
        assert hc["status"] == "healthy"
        assert hc["total_objects"] == 1


class TestEmbedding:
    def test_custom_embedder(self):
        class TinyEmbedder(EmbeddingProvider):
            def __init__(self):
                super().__init__(dimensions=4)
        ep = TinyEmbedder()
        r = MemoryKnowledgeRuntime(embedding_provider=ep)
        obj = r.store("e1", "test text")
        assert obj.embedding is not None
        assert len(obj.embedding) == 4

    def test_similarity_search(self, runtime):
        runtime.store("sim:1", "apple orange banana", tags=["fruit"])
        runtime.store("sim:2", "car truck bus", tags=["vehicle"])
        q = RetrievalQuery(query="fruit apple", top_k=5)
        results = runtime.search(q)
        assert len(results) >= 1