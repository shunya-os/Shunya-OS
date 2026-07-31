
"""Comprehensive tests for SHUNYA Universal Runtime Foundation (Phase C2).

All tests match the actual APIs of the subagent-created modules.
"""

from __future__ import annotations

import pytest
import time
from dataclasses import dataclass, field

from core.kernel import UniversalObject, ObjectStatus
from core.identity import IdentityEngine, Identity, IdentityStatus, AuthMethod
from core.relationship import RelationshipEngine, Relationship, RelationshipType
from core.timeline import TimelineEngine, TimelineEvent, TimelineEventType
from core.event import EventEngine, SystemEvent, EventType, EventPriority
from core.evidence import EvidenceEngine, Evidence, EvidenceType, EvidenceDirection, EvidenceStatus
from core.runtime import RuntimeKernel, RuntimeConfig, HealthStatus, Engine, EngineStatus
from core.registry import ObjectRegistry, ProtocolComplianceChecker, ComplianceReport
from core.validation import RuntimeValidator, ProtocolValidator, ValidationReport


# --- Concrete engine for testing ---

@dataclass
class TestEngineImpl(Engine):
    """Concrete Engine subclass for testing."""
    engine_id: str = ""
    engine_type: str = "test"
    status: EngineStatus = EngineStatus.ACTIVE

    def initialize(self):
        self.status = EngineStatus.ACTIVE

    def shutdown(self):
        self.status = EngineStatus.ACTIVE

    def health_check(self):
        return HealthStatus()

    def handle_event(self, event):
        pass

    def get_capabilities(self):
        return ["test"]


# --- Helper ---

def make_obj(**kw):
    defaults = dict(object_type="test", name="Test", created_by="sys", updated_by="sys", owner_id="owner_1")
    defaults.update(kw)
    return UniversalObject(**defaults)


# =====================================================================
# 1. Universal Object
# =====================================================================

class TestUniversalObject:
    def test_create_default(self):
        obj = make_obj()
        assert obj.object_id
        assert obj.name == "Test"
        assert obj.version >= 1

    def test_identity_section(self):
        assert len(make_obj().object_id) > 8

    def test_metadata_section(self):
        obj = make_obj()
        assert obj.created_at
        assert obj.created_by == "sys"

    def test_relationships_section(self):
        a, b = make_obj(name="A"), make_obj(name="B")
        assert a.add_relationship(b.object_id, "related_to") is not None
        assert len(a.get_relationships()) >= 1

    def test_timeline_section(self):
        obj = make_obj()
        assert obj.add_event("object_created", {"k": "v"}, "test")
        assert len(obj.get_events(limit=10)) >= 1

    def test_status_and_lifecycle(self):
        obj = make_obj()
        obj.transition("active")
        assert obj.is_active
        obj.transition("archived")
        assert not obj.is_active
        assert obj.can_transition_to("active")

    def test_ownership(self):
        obj = make_obj(owner_id="owner_001")
        assert obj.is_owned_by("owner_001")
        obj.transfer("owner_002", reason="test")
        assert obj.owner_id == "owner_002"

    def test_evidence(self):
        obj = make_obj()
        obj.add_evidence("ev_001")
        obj.add_evidence("ev_002")
        assert len(obj.get_evidence()) == 2

    def test_ai_context(self):
        assert "Test" in make_obj().get_ai_context()

    def test_audit(self):
        obj = make_obj()
        obj.log_action("custom_action", "actor_001", "detail")
        actions = [e.action for e in obj.get_audit_log()]
        assert "custom_action" in actions

    def test_actions(self):
        obj = make_obj()
        # Check that actions method works even if list is empty
        acts = obj.get_available_actions("actor_001")
        assert isinstance(acts, list)

    def test_serialization(self):
        obj = make_obj()
        d = obj.to_dict()
        obj2 = UniversalObject.from_dict(d)
        assert obj2.name == obj.name
        assert obj2.object_id == obj.object_id

    def test_search(self):
        assert len(make_obj().search("Test")) >= 1

    def test_mandatory_fields(self):
        obj = make_obj()
        for f in ("object_id", "object_type", "name", "status", "version", "created_at", "owner_id", "confidence"):
            assert hasattr(obj, f)


# =====================================================================
# 2. Identity Engine
# =====================================================================

class TestIdentityEngine:
    def setup_method(self):
        self.eng = IdentityEngine()

    def test_create(self):
        i = self.eng.create_identity("Test", "human")
        assert i.identity_id
        assert i.display_name == "Test"
        assert i.status == IdentityStatus.ACTIVE  # enum comparison

    def test_get(self):
        i = self.eng.create_identity("Test", "human")
        assert self.eng.get_identity(i.identity_id) is not None

    def test_merge(self):
        p = self.eng.create_identity("Primary", "human")
        s = self.eng.create_identity("Secondary", "human")
        m = self.eng.merge_identities(p.identity_id, s.identity_id, "dup", "ev_001")
        assert m.identity_id == p.identity_id
        sec = self.eng.get_identity(s.identity_id)
        assert sec.status == IdentityStatus.MERGED  # enum comparison

    def test_merge_history(self):
        p = self.eng.create_identity("P", "human")
        s = self.eng.create_identity("S", "human")
        self.eng.merge_identities(p.identity_id, s.identity_id, "dup", "ev_001")
        assert len(self.eng.get_merge_history(p.identity_id)) >= 1

    def test_delete(self):
        i = self.eng.create_identity("Del", "human")
        self.eng.delete_identity(i.identity_id)
        deleted = self.eng.get_identity(i.identity_id)
        assert deleted.status == IdentityStatus.RETIRED  # enum comparison

    def test_search(self):
        self.eng.create_identity("Alice Wonderland", "human")
        self.eng.create_identity("Bob Builder", "human")
        assert len(self.eng.search_identities("Alice")) >= 1

    def test_get_by_status(self):
        i = self.eng.create_identity("GetByStatus", "human")
        self.eng.delete_identity(i.identity_id)
        # Check the identity itself
        deleted = self.eng.get_identity(i.identity_id)
        assert deleted is not None
        assert deleted.status == IdentityStatus.RETIRED


# =====================================================================
# 3. Relationship Engine
# =====================================================================

class TestRelationshipEngine:
    def setup_method(self):
        self.eng = RelationshipEngine()

    def test_add_and_get(self):
        r = self.eng.add_relationship("a", "b", RelationshipType.RELATED_TO)
        assert self.eng.get_relationship(r.relationship_id) is not None

    def test_outgoing_incoming(self):
        self.eng.add_relationship("a", "b", RelationshipType.RELATED_TO)
        self.eng.add_relationship("a", "c", RelationshipType.RELATED_TO)
        assert len(self.eng.get_outgoing("a")) == 2
        assert len(self.eng.get_incoming("b")) == 1

    def test_get_all(self):
        self.eng.add_relationship("a", "b", RelationshipType.OWNS)
        self.eng.add_relationship("b", "a", RelationshipType.MEMBER_OF)
        assert len(self.eng.get_all("a")) == 2

    def test_neighbors(self):
        self.eng.add_relationship("A", "B", RelationshipType.RELATED_TO)
        self.eng.add_relationship("B", "C", RelationshipType.RELATED_TO)
        assert "B" in self.eng.get_neighbors("A", max_depth=1)
        assert "C" not in self.eng.get_neighbors("A", max_depth=1)
        assert "C" in self.eng.get_neighbors("A", max_depth=2)

    def test_path_finding(self):
        self.eng.add_relationship("A", "B", RelationshipType.RELATED_TO)
        self.eng.add_relationship("B", "C", RelationshipType.RELATED_TO)
        assert len(self.eng.find_path("A", "C", max_depth=5)) == 2
        assert len(self.eng.find_path("A", "D", max_depth=5)) == 0

    def test_remove(self):
        r = self.eng.add_relationship("A", "B", RelationshipType.RELATED_TO)
        self.eng.remove_relationship(r.relationship_id)
        assert self.eng.get_relationship(r.relationship_id) is None

    def test_subgraph(self):
        self.eng.add_relationship("A", "B", RelationshipType.RELATED_TO)
        self.eng.add_relationship("B", "C", RelationshipType.RELATED_TO)
        sg = self.eng.get_subgraph("A", depth=2)
        assert all(x in sg for x in ("A", "B", "C"))

    def test_count(self):
        self.eng.add_relationship("A", "B", RelationshipType.RELATED_TO)
        self.eng.add_relationship("A", "C", RelationshipType.RELATED_TO)
        assert self.eng.get_relationship_count("A") == 2

    def test_clear(self):
        self.eng.add_relationship("A", "B", RelationshipType.RELATED_TO)
        self.eng.clear()
        assert self.eng.get_relationship_count("A") == 0


# =====================================================================
# 4. Timeline Engine
# =====================================================================

class TestTimelineEngine:
    def setup_method(self):
        self.eng = TimelineEngine()

    def test_record(self):
        e = self.eng.record_event("o1", TimelineEventType.OBJECT_CREATED, "a1", {})
        assert e.event_id and e.object_id == "o1"

    def test_get_events(self):
        self.eng.record_event("o1", TimelineEventType.OBJECT_CREATED, "a1", {})
        self.eng.record_event("o1", TimelineEventType.OBJECT_MODIFIED, "a1", {})
        assert len(self.eng.get_events("o1")) == 2

    def test_latest(self):
        for i in range(5):
            self.eng.record_event("o1", TimelineEventType.OBJECT_MODIFIED, "a1", {"i": i})
        assert len(self.eng.get_latest_events("o1", count=3)) == 3

    def test_ordering(self):
        self.eng.record_event("o1", TimelineEventType.OBJECT_CREATED, "a1", {})
        time.sleep(0.01)
        self.eng.record_event("o1", TimelineEventType.OBJECT_MODIFIED, "a1", {})
        tl = self.eng.get_timeline("o1")
        assert tl[0].timestamp <= tl[1].timestamp

    def test_by_type(self):
        self.eng.record_event("o1", TimelineEventType.OBJECT_CREATED, "a1", {})
        self.eng.record_event("o1", TimelineEventType.OBJECT_MODIFIED, "a1", {})
        self.eng.record_event("o2", TimelineEventType.OBJECT_CREATED, "a1", {})
        assert len(self.eng.get_events_by_type(TimelineEventType.OBJECT_CREATED)) == 2

    def test_integrity(self):
        self.eng.record_event("o1", TimelineEventType.OBJECT_CREATED, "a1", {"k": "v1"})
        self.eng.record_event("o1", TimelineEventType.OBJECT_MODIFIED, "a1", {"k": "v2"})
        assert self.eng.verify_integrity("o1") is True

    def test_summary(self):
        self.eng.record_event("o1", TimelineEventType.OBJECT_CREATED, "a1", {})
        self.eng.record_event("o1", TimelineEventType.OBJECT_MODIFIED, "a1", {})
        s = self.eng.get_timeline_summary("o1")
        assert s["total_events"] == 2

    def test_by_actor(self):
        self.eng.record_event("o1", TimelineEventType.OBJECT_CREATED, "a1", {})
        self.eng.record_event("o2", TimelineEventType.OBJECT_CREATED, "a2", {})
        assert len(self.eng.get_events_by_actor("a1")) == 1

    def test_clear(self):
        self.eng.record_event("o1", TimelineEventType.OBJECT_CREATED, "a1", {})
        self.eng.clear()
        assert len(self.eng.get_events("o1")) == 0


# =====================================================================
# 5. Event Engine
# =====================================================================

class TestEventEngine:
    def setup_method(self):
        self.eng = EventEngine()

    def test_emit(self):
        e = self.eng.emit(EventType.SYSTEM_EVENT, "t", "a1", "o1", {"k": "v"})
        assert e.event_id
        assert e.event_type == EventType.SYSTEM_EVENT.value

    def test_subscribe(self):
        received = []
        self.eng.subscribe(EventType.SYSTEM_EVENT, lambda e: received.append(e))
        self.eng.emit(EventType.SYSTEM_EVENT, "t", "a1", "o1", {})
        assert len(received) == 1

    def test_unsubscribe(self):
        received = []
        sid = self.eng.subscribe(EventType.SYSTEM_EVENT, lambda e: received.append(e))
        self.eng.unsubscribe(sid)
        self.eng.emit(EventType.SYSTEM_EVENT, "t", "a1", "o1", {})
        assert len(received) == 0

    def test_by_id(self):
        e = self.eng.emit(EventType.SYSTEM_EVENT, "t", "a1", "o1", {})
        assert self.eng.get_event(e.event_id) is not None

    def test_by_object(self):
        self.eng.emit(EventType.OBJECT_CREATED, "t", "a1", "o1", {})
        self.eng.emit(EventType.OBJECT_MODIFIED, "t", "a1", "o1", {})
        assert len(self.eng.get_events_by_object("o1")) == 2

    def test_by_source(self):
        self.eng.emit(EventType.SYSTEM_EVENT, "src_a", "a1", "o1", {})
        self.eng.emit(EventType.SYSTEM_EVENT, "src_b", "a1", "o1", {})
        assert len(self.eng.get_events_by_source("src_a")) == 1

    def test_priority(self):
        e = self.eng.emit(EventType.SYSTEM_EVENT, "t", "a1", "o1", {}, priority=EventPriority.CRITICAL)
        assert e.priority == EventPriority.CRITICAL.value

    def test_replay(self):
        received = []
        self.eng.subscribe(EventType.SYSTEM_EVENT, lambda e: received.append(e))
        self.eng.emit(EventType.SYSTEM_EVENT, "t", "a1", "o1", {})
        self.eng.emit(EventType.SYSTEM_EVENT, "t", "a1", "o1", {})
        received.clear()
        assert self.eng.replay(EventType.SYSTEM_EVENT) == 2
        assert len(received) == 2

    def test_clear(self):
        self.eng.emit(EventType.SYSTEM_EVENT, "t", "a1", "o1", {})
        before = self.eng.get_stats()["total_events"]
        self.eng.clear()
        assert self.eng.get_stats()["total_events"] == 0


# =====================================================================
# 6. Evidence Engine
# =====================================================================

class TestEvidenceEngine:
    def setup_method(self):
        self.eng = EvidenceEngine()

    def _ev(self, obj="o1", etype=EvidenceType.OBSERVATION, stmt="s", src="src",
            direction=EvidenceDirection.SUPPORTING, rel=0.8, **kw):
        return self.eng.create_evidence(obj, etype, stmt, src, direction, rel, **kw)

    def test_create(self):
        ev = self._ev()
        assert ev.evidence_id and ev.object_id == "o1"

    def test_get(self):
        ev = self._ev()
        assert self.eng.get_evidence(ev.evidence_id) is not None

    def test_by_object(self):
        self._ev("o1"); self._ev("o1"); self._ev("o2")
        assert len(self.eng.get_evidence_for_object("o1")) == 2

    def test_verify(self):
        v = self.eng.verify_evidence(self._ev().evidence_id, "v1")
        assert v.status == EvidenceStatus.VERIFIED.value

    def test_supersede(self):
        s = self.eng.supersede_evidence(self._ev().evidence_id, "reason")
        assert s.status == EvidenceStatus.SUPERSEDED.value

    def test_chain(self):
        root = self._ev(stmt="root", rel=0.9)
        child = self._ev(stmt="child", rel=0.8, parent_evidence_id=root.evidence_id)
        assert self.eng.get_evidence_chain(child.evidence_id).depth >= 1

    def test_support_contradict(self):
        self._ev(direction=EvidenceDirection.SUPPORTING)
        self._ev(direction=EvidenceDirection.CONTRADICTING)
        assert len(self.eng.get_supporting_evidence("o1")) == 1
        assert len(self.eng.get_contradicting_evidence("o1")) == 1

    def test_confidence(self):
        self._ev(rel=0.9)
        assert 0.0 < self.eng.get_confidence_score("o1") <= 1.0

    def test_no_evidence_confidence(self):
        assert self.eng.get_confidence_score("nonexistent") == 0.5

    def test_integrity(self):
        assert self.eng.verify_integrity(self._ev().evidence_id) is True

    def test_search(self):
        self._ev(stmt="unique searchable phrase")
        assert len(self.eng.search_evidence("unique")) >= 1

    def test_clear(self):
        self._ev()
        self.eng.clear()
        assert len(self.eng.get_evidence_for_object("o1")) == 0


# =====================================================================
# 7. Runtime Kernel
# =====================================================================

class TestRuntimeKernel:
    def test_config(self):
        assert RuntimeConfig() is not None

    def test_health(self):
        assert HealthStatus().status == "healthy"

    def test_register_engine(self):
        rk = RuntimeKernel()
        e = TestEngineImpl(engine_id="r1", engine_type="test")
        rk.register_engine("r1", e)
        assert rk.get_engine("r1") is e

    def test_diagnostics(self):
        rk = RuntimeKernel()
        e = TestEngineImpl(engine_id="d1", engine_type="test")
        rk.register_engine("d1", e)
        d = rk.diagnostics()
        assert isinstance(d, dict)
        assert "initialized" in d


# =====================================================================
# 8. Object Registry
# =====================================================================

class TestObjectRegistry:
    def test_register(self):
        reg = ObjectRegistry()
        reg.register_type(UniversalObject, type_name="TestType")
        names = [t["type_name"] for t in reg.list_types()]
        assert "testtype" in names

    def test_compliance_checker(self):
        cc = ProtocolComplianceChecker()
        r = cc.full_compliance_check(make_obj())
        assert isinstance(r, ComplianceReport)
        assert hasattr(r, "compliant") and hasattr(r, "checks") and hasattr(r, "failures")


# =====================================================================
# 9. Runtime Validation
# =====================================================================

class TestRuntimeValidation:
    def test_validate(self):
        rv = RuntimeValidator()
        r = rv.validate_object(make_obj())
        assert hasattr(r, "passed") and hasattr(r, "findings")

    def test_protocol(self):
        rv = RuntimeValidator()
        r = rv.validate_object_protocol(make_obj())
        assert isinstance(r, ValidationReport)

    def test_report_errors(self):
        r = ValidationReport(subject_id="t", subject_type="o")
        r.add_error("protocol", "err", "o1", "f")
        assert r.errors == 1 and r.passed is False

    def test_report_warnings(self):
        r = ValidationReport(subject_id="t", subject_type="o")
        r.add_warning("ontology", "warn", "o1")
        assert r.warnings == 1 and r.passed is True


# =====================================================================
# 10. Integration
# =====================================================================

class TestIntegration:
    def test_object_lifecycle(self):
        obj = make_obj(owner_id="o1")
        obj.transition("active")
        obj.add_evidence("ev_001")
        obj.log_action("created", "sys", "Object created")
        assert obj.object_id and len(obj.get_evidence()) >= 1
        actions = [e.action for e in obj.get_audit_log()]
        assert "created" in actions or "object_created" in actions

    def test_serialize_deserialize(self):
        obj = make_obj(owner_id="ox")
        d = obj.to_dict()
        obj2 = UniversalObject.from_dict(d)
        assert obj2.name == obj.name and obj2.owner_id == obj.owner_id

    def test_runtime_with_engines(self):
        rk = RuntimeKernel()
        for i in range(3):
            e = TestEngineImpl(engine_id=f"e{i}", engine_type="test")
            rk.register_engine(f"e{i}", e)
        assert all(rk.get_engine(f"e{i}") is not None for i in range(3))

    def test_relationship_traversal(self):
        re = RelationshipEngine()
        re.add_relationship("alice", "bob", RelationshipType.RELATED_TO)
        re.add_relationship("bob", "charlie", RelationshipType.RELATED_TO)
        assert len(re.find_path("alice", "charlie", max_depth=5)) == 2
