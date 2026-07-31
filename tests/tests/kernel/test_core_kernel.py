"""Tests for SHUNYA Core Kernel — UniversalObject Protocol Implementation.

Tests every mandatory section of the Universal Object Protocol as defined
in docs/canon/04_universal_object_protocol.md.
"""

import copy
import sys

import pytest

# Ensure the shunya_os root is on sys.path
sys.path.insert(0, "/home/shunya-deploy/shunya_os")

from core.kernel import (
    AccessControlEntry,
    AccessControlList,
    ActionDefinition,
    ActionResult,
    AuditEntry,
    DiffResult,
    EvidenceRef,
    IdentityAuthority,
    IdentityType,
    InteractionRecord,
    ObjectStatus,
    OwnerType,
    OwnershipRecord,
    RelationshipDirection,
    RelationshipRef,
    SearchResult,
    SourceType,
    StageTransition,
    TimelineEvent,
    UniversalObject,
    VersionRecord,
    generate_uuid7,
)


# =============================================================================
# UUID v7
# =============================================================================

class TestGenerateUUID7:
    def test_format(self):
        uid = generate_uuid7()
        parts = uid.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_uniqueness(self):
        uuids = {generate_uuid7() for _ in range(100)}
        assert len(uuids) == 100

    def test_version_bits(self):
        uid = generate_uuid7()
        # The 13th character should be '7' for UUID v7
        assert uid[14] == "7"


# =============================================================================
# §4 — Identity
# =============================================================================

class TestIdentity:
    def test_auto_generates_uuid7(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.object_id != ""
        assert len(obj.object_id) == 36
        assert obj.object_id[14] == "7"  # UUID v7 version nibble

    def test_custom_object_id(self):
        obj = UniversalObject(
            object_id="my-custom-id",
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.object_id == "my-custom-id"

    def test_identity_type_default(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.identity_type == IdentityType.PERMANENT

    def test_identity_authority_default(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.identity_authority == IdentityAuthority.OBJECT_FACTORY

    def test_custom_identity_type_and_authority(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
            identity_type=IdentityType.EXTERNAL,
            identity_authority=IdentityAuthority.IDENTITY_ENGINE,
        )
        assert obj.identity_type == IdentityType.EXTERNAL
        assert obj.identity_authority == IdentityAuthority.IDENTITY_ENGINE

    def test_external_ids(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
            external_ids={"crm": "CRM-123", "email": "user@example.com"},
        )
        assert obj.external_ids == {"crm": "CRM-123", "email": "user@example.com"}

    def test_add_remove_external_id(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_external_id("github", "gh_user")
        assert obj.external_ids["github"] == "gh_user"
        obj.remove_external_id("github")
        assert "github" not in obj.external_ids

    def test_aliases(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
            aliases=["John", "Johnny"],
        )
        assert obj.aliases == ["John", "Johnny"]

    def test_add_remove_alias(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_alias("JD")
        assert "JD" in obj.aliases
        obj.remove_alias("JD")
        assert "JD" not in obj.aliases

    def test_immutable_object_id(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        with pytest.raises(AttributeError):
            obj.object_id = "new-id"  # no setter

    def test_external_ids_returns_copy(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        ids = obj.external_ids
        ids["hacked"] = "yep"
        assert "hacked" not in obj.external_ids

    def test_aliases_returns_copy(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        aliases = obj.aliases
        aliases.append("hacked")
        assert "hacked" not in obj.aliases


# =============================================================================
# §3 — Mandatory Fields & §5 — Metadata
# =============================================================================

class TestMandatoryFields:
    def test_all_mandatory_fields_exist(self):
        obj = UniversalObject(
            object_type="human", name="John",
            created_by="creator_id", updated_by="creator_id",
            owner_id="org_id",
        )
        assert obj.object_id
        assert obj.object_type == "human"
        assert obj.name == "John"
        assert obj.status
        assert obj.version >= 1
        assert obj.created_at
        assert obj.updated_at
        assert obj.created_by == "creator_id"
        assert obj.updated_by == "creator_id"
        assert obj.owner_id == "org_id"

    def test_created_immutable(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        with pytest.raises(AttributeError):
            obj.created_at = "tomorrow"
        with pytest.raises(AttributeError):
            obj.created_by = "someone_else"

    def test_updated_at_bumps_on_change(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        before = obj.updated_at
        obj.name = "New Name"
        assert obj.updated_at >= before

    def test_source_default(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.source == SourceType.SYSTEM

    def test_custom_source(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
            source=SourceType.HUMAN,
            source_detail="manual_entry",
        )
        assert obj.source == SourceType.HUMAN
        assert obj.source_detail == "manual_entry"

    def test_custom_metadata(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
            custom_metadata={"batch": "b1", "pipeline": "ingest"},
        )
        assert obj.custom_metadata["batch"] == "b1"

    def test_tags(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
            tags=["alpha", "beta"],
        )
        assert obj.tags == ["alpha", "beta"]

    def test_tags_setter(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.tags = ["new", "tags"]
        assert obj.tags == ["new", "tags"]

    def test_tenant_and_space_id(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
            tenant_id="tenant_1", space_id="space_42",
        )
        assert obj.tenant_id == "tenant_1"
        assert obj.space_id == "space_42"


# =============================================================================
# §6 — Relationships
# =============================================================================

class TestRelationships:
    def test_add_relationship(self):
        obj = UniversalObject(
            object_type="human", name="Alice",
            created_by="s", updated_by="s", owner_id="o",
        )
        rel_id = obj.add_relationship("target_org", "member_of")
        rels = obj.get_relationships()
        assert len(rels) == 1
        assert rels[0].relationship_type == "member_of"
        assert rels[0].target_id == "target_org"
        assert rels[0].relationship_id == rel_id

    def test_add_relationship_with_all_params(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        rel_id = obj.add_relationship(
            "target", "owns",
            metadata={"since": "2026"},
            direction=RelationshipDirection.HIERARCHICAL,
            strength=0.95,
            label="Manager",
            evidence_ids=["ev_001"],
        )
        rels = obj.get_relationships()
        assert rels[0].direction == RelationshipDirection.HIERARCHICAL
        assert rels[0].strength == 0.95
        assert rels[0].label == "Manager"
        assert rels[0].evidence_ids == ["ev_001"]

    def test_remove_relationship(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        rel_id = obj.add_relationship("target", "knows")
        obj.remove_relationship(rel_id)
        assert len(obj.get_relationships()) == 0

    def test_remove_missing_raises(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        with pytest.raises(ValueError):
            obj.remove_relationship("ghost")

    def test_get_relationships_filter(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_relationship("a", "follows")
        obj.add_relationship("b", "follows")
        obj.add_relationship("c", "blocks")
        rels = obj.get_relationships(relationship_type="follows")
        assert len(rels) == 2
        rels2 = obj.get_relationships(direction=RelationshipDirection.DIRECTIONAL)
        assert len(rels2) == 3

    def test_get_related_objects(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_relationship("target_1", "knows")
        obj.add_relationship("target_2", "knows")
        obj.add_relationship("other", "blocks")
        related = obj.get_related_objects(relationship_type="knows")
        assert sorted(related) == sorted(["target_1", "target_2"])

    def test_relationships_readonly(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        rels = obj.relationships
        assert isinstance(rels, list)


# =============================================================================
# §7 — Timeline
# =============================================================================

class TestTimeline:
    def test_creation_event(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="creator", updated_by="creator", owner_id="o",
        )
        events = obj.get_events()
        assert len(events) == 1
        assert events[0].event_type == "object_created"
        assert events[0].actor_id == "creator"

    def test_add_event(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        eid = obj.add_event("custom_event", {"key": "val"}, "actor_1")
        events = obj.get_events(event_type="custom_event")
        assert len(events) == 1
        assert events[0].data["key"] == "val"

    def test_get_latest_events(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        for i in range(10):
            obj.add_event(f"ev_{i}", {"n": i}, "actor")
        latest = obj.get_latest_events(3)
        assert len(latest) == 3
        # Latest should be ev_9, ev_8, ev_7
        assert latest[0].event_type == "ev_9"

    def test_get_events_pagination(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        for i in range(5):
            obj.add_event("ev", {"n": i}, "actor")
        events = obj.get_events(limit=3, offset=2)
        assert len(events) == 3

    def test_get_timeline_summary(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_event("ev_a", {}, "a")
        obj.add_event("ev_b", {}, "b")
        summary = obj.get_timeline_summary()
        assert summary["total_events"] == 3
        assert summary["event_types"]["object_created"] == 1
        assert summary["event_types"]["ev_a"] == 1
        assert summary["first_event"] is not None
        assert summary["last_event"] is not None


# =============================================================================
# §8 — Lifecycle
# =============================================================================

class TestLifecycle:
    def test_default_stage_pending(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.current_stage == "pending"

    def test_transition_valid(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.transition("active", reason="ready")
        assert obj.current_stage == "active"
        assert obj.status == "active"

    def test_transition_invalid(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        with pytest.raises(ValueError, match="Cannot transition"):
            obj.transition("archived", actor_id="s")  # pending -> archived invalid

    def test_transition_to_same_is_noop(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.transition("pending")
        assert obj.current_stage == "pending"

    def test_can_transition_to(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.can_transition_to("active") is True
        assert obj.can_transition_to("archived") is False

    def test_full_lifecycle(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.transition("active", actor_id="a")
        obj.transition("archived", actor_id="a")
        obj.transition("active", actor_id="a")
        obj.transition("deleted", actor_id="a")
        assert obj.current_stage == "deleted"
        assert obj.is_active is False

    def test_lifecycle_history(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.transition("active", reason="approve", actor_id="admin")
        hist = obj.get_lifecycle_history()
        assert len(hist) == 1
        assert hist[0].from_stage == "pending"
        assert hist[0].to_stage == "active"
        assert hist[0].reason == "approve"


# =============================================================================
# §9 — Status
# =============================================================================

class TestStatus:
    def test_is_active_default(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.is_active is True  # pending is active

    def test_is_active_archived(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.transition("active")
        obj.transition("archived")
        assert obj.is_active is False

    def test_is_active_deleted(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.transition("active")
        obj.transition("deleted")
        assert obj.is_active is False

    def test_status_detail(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.status_detail = "verified"
        assert obj.status_detail == "verified"


# =============================================================================
# §10 — Ownership
# =============================================================================

class TestOwnership:
    def test_default_owner(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="owner_123",
        )
        assert obj.owner_id == "owner_123"
        assert obj.owner_type == OwnerType.HUMAN

    def test_custom_owner_type(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="org_1",
            owner_type=OwnerType.ORGANIZATION,
        )
        assert obj.owner_type == OwnerType.ORGANIZATION

    def test_is_owned_by(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="owner_123",
        )
        assert obj.is_owned_by("owner_123") is True
        assert obj.is_owned_by("stranger") is False

    def test_transfer(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="old_owner",
        )
        obj.transfer("new_owner", reason="org_restructure")
        assert obj.owner_id == "new_owner"
        assert len(obj.owner_history) == 2
        assert obj.owner_history[1].reason == "org_restructure"

    def test_owner_history_immutable(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="owner_1",
        )
        hist = obj.owner_history
        hist.append(OwnershipRecord())
        assert len(obj.owner_history) == 1  # copy protection


# =============================================================================
# §11 — Permissions
# =============================================================================

class TestPermissions:
    def test_owner_has_full_access(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        assert obj.check_permission("admin", "view") is True
        assert obj.check_permission("admin", "update") is True
        assert obj.check_permission("admin", "delete") is True

    def test_stranger_no_access(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="owner",
        )
        assert obj.check_permission("stranger", "view") is False

    def test_grant_and_check(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        obj.grant("viewer_1", "viewer")
        assert obj.check_permission("viewer_1", "view") is True
        assert obj.check_permission("viewer_1", "update") is False

    def test_grant_editor(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        obj.grant("editor_1", "editor")
        assert obj.check_permission("editor_1", "update") is True
        assert obj.check_permission("editor_1", "delete") is False

    def test_grant_admin(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        obj.grant("admin_1", "admin")
        assert obj.check_permission("admin_1", "delete") is True

    def test_revoke(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        obj.grant("user_x", "editor")
        assert obj.check_permission("user_x", "update") is True
        obj.revoke("user_x", "editor")
        assert obj.check_permission("user_x", "update") is False

    def test_get_effective_permissions(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        obj.grant("user_y", "editor", scope="update")
        perms = obj.get_effective_permissions("user_y")
        assert len(perms) == 1
        assert perms[0]["role"] == "editor"


# =============================================================================
# §12 — Evidence
# =============================================================================

class TestEvidence:
    def test_add_evidence(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_evidence("ev_001", description="Contract")
        active = obj.get_evidence()
        assert len(active) == 1
        assert active[0].evidence_id == "ev_001"
        assert active[0].description == "Contract"

    def test_remove_evidence_supersedes(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_evidence("ev_001")
        obj.add_evidence("ev_002")
        assert len(obj.get_evidence()) == 2
        obj.remove_evidence("ev_001")
        assert len(obj.get_evidence()) == 1
        assert obj.get_evidence()[0].evidence_id == "ev_002"

    def test_get_evidence_chain(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_evidence("ev_001")
        obj.add_evidence("ev_002")
        obj.remove_evidence("ev_001")
        chain = obj.get_evidence_chain()
        assert len(chain) == 2
        assert chain[0]["active"] is False  # superseded
        assert chain[1]["active"] is True

    def test_remove_missing_evidence_raises(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        with pytest.raises(ValueError):
            obj.remove_evidence("ghost")

    def test_confidence_no_evidence(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.get_confidence() == 0.0

    def test_confidence_with_evidence(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        for i in range(5):
            obj.add_evidence(f"ev_{i}")
        assert obj.get_confidence() > 0.0

    def test_confidence_derived_not_asserted(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        # Confidence is read-only property derived from evidence
        with pytest.raises(AttributeError):
            obj.confidence = 0.99


# =============================================================================
# §13 — Memory (OPTIONAL)
# =============================================================================

class TestMemory:
    def test_associate_memory(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.associate_memory("mem_001")
        assert "mem_001" in obj.memory_ids

    def test_get_memories(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.associate_memory("mem_001")
        obj.associate_memory("mem_002")
        assert len(obj.get_memories()) == 2

    def test_no_duplicate_memory(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.associate_memory("mem_001")
        obj.associate_memory("mem_001")
        assert len(obj.memory_ids) == 1


# =============================================================================
# §14 — AI Context
# =============================================================================

class TestAIContext:
    def test_ai_summary_autogenerated(self):
        obj = UniversalObject(
            object_type="human", name="Alice",
            created_by="s", updated_by="s", owner_id="o",
            description="A test human",
        )
        summary = obj.ai_summary
        assert "human" in summary
        assert "Alice" in summary

    def test_ai_understanding_autogenerated(self):
        obj = UniversalObject(
            object_type="human", name="Alice",
            created_by="s", updated_by="s", owner_id="o",
        )
        understanding = obj.ai_understanding
        assert "Human" in understanding
        assert "consent" in understanding

    def test_ai_understanding_organization(self):
        obj = UniversalObject(
            object_type="organization", name="Acme",
            created_by="s", updated_by="s", owner_id="o",
        )
        understanding = obj.ai_understanding
        assert "Organization" in understanding
        assert "governance" in understanding

    def test_ai_understanding_system(self):
        obj = UniversalObject(
            object_type="agent", name="Bot",
            created_by="s", updated_by="s", owner_id="o",
        )
        understanding = obj.ai_understanding
        assert "System/AI" in understanding

    def test_get_ai_context(self):
        obj = UniversalObject(
            object_type="human", name="Alice",
            created_by="s", updated_by="s", owner_id="o",
        )
        ctx = obj.get_ai_context()
        assert "Object: Alice (human)" in ctx
        assert "ID:" in ctx
        assert "Version:" in ctx

    def test_interaction_history(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        iid = obj.add_interaction("query", "Asked about status", "ai_1")
        assert len(obj.interaction_history) == 1
        assert obj.interaction_history[0].interaction_type == "query"

    def test_relevant_objects_includes_relationships(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_relationship("rel_obj_1", "knows")
        relevant = obj.relevant_objects
        assert "rel_obj_1" in relevant


# =============================================================================
# §15 — Search
# =============================================================================

class TestSearch:
    def test_search(self):
        obj = UniversalObject(
            object_type="human", name="Alice Wonderland",
            created_by="s", updated_by="s", owner_id="o",
        )
        results = obj.search("alice")
        assert len(results) >= 1
        assert results[0].score > 0

    def test_search_by_field(self):
        obj = UniversalObject(
            object_type="human", name="Bob",
            created_by="s", updated_by="s", owner_id="o",
        )
        results = obj.search_by_field("name", "bob")
        assert len(results) == 1

    def test_search_by_field_invalid_raises(self):
        obj = UniversalObject(
            object_type="human", name="Bob",
            created_by="s", updated_by="s", owner_id="o",
        )
        with pytest.raises(ValueError):
            obj.search_by_field("nonexistent", "x")

    def test_search_terms(self):
        obj = UniversalObject(
            object_type="human", name="Bob Smith",
            created_by="s", updated_by="s", owner_id="o",
            tags=["admin", "engineering"],
        )
        terms = obj.search_terms
        assert "bob" in terms
        assert "smith" in terms

    def test_search_index(self):
        obj = UniversalObject(
            object_type="document", name="README",
            created_by="s", updated_by="s", owner_id="o",
        )
        index = obj.search_index
        assert "readme" in index
        assert "document" in index

    def test_searchable_fields(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert "name" in obj.searchable_fields
        assert "object_type" in obj.searchable_fields


# =============================================================================
# §16 — Audit
# =============================================================================

class TestAudit:
    def test_creation_is_logged(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="creator", updated_by="creator", owner_id="o",
        )
        log = obj.get_audit_log()
        assert len(log) == 1
        assert log[0].action == "object_created"
        assert log[0].actor_id == "creator"

    def test_log_action(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        eid = obj.log_action("custom_action", "actor_1", "Did something")
        log = obj.get_audit_log(action="custom_action")
        assert len(log) == 1

    def test_get_audit_log_filters(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.grant("user_1", "viewer", granted_by="admin")  # logs an audit entry
        log = obj.get_audit_log(action="grant")
        assert len(log) == 1

    def test_verify_integrity(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.verify_integrity() is True

    def test_tamper_detection(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.grant("u1", "viewer", granted_by="admin")
        assert obj.verify_integrity() is True
        # Tamper with an entry
        obj._audit_log[1].detail = "TAMPERED"
        assert obj.verify_integrity() is False


# =============================================================================
# §17 — Actions
# =============================================================================

class TestActions:
    def test_required_actions_exist(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        names = {a.name for a in obj.available_actions}
        required = {"view", "update", "delete", "add_evidence",
                     "add_relationship", "get_timeline", "get_audit_log"}
        assert required.issubset(names)

    def test_execute_view(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        result = obj.execute_action("view", actor_id="admin")
        assert result.success is True
        assert result.action == "view"
        assert "object_id" in result.result

    def test_execute_update(self):
        obj = UniversalObject(
            object_type="test", name="Old Name",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        result = obj.execute_action(
            "update", {"fields": {"name": "New Name"}}, actor_id="admin",
        )
        assert result.success is True
        assert obj.name == "New Name"

    def test_execute_delete(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        obj.transition("active")
        result = obj.execute_action(
            "delete", {"reason": "cleanup"}, actor_id="admin",
        )
        assert result.success is True
        assert obj.status == "deleted"

    def test_execute_permission_denied(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        result = obj.execute_action("delete", actor_id="stranger")
        assert result.success is False
        assert "Permission denied" in result.error

    def test_get_available_actions_filtered(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        obj.grant("viewer_1", "viewer")
        actions = obj.get_available_actions("viewer_1")
        names = {a.name for a in actions}
        assert "view" in names
        assert "delete" not in names

    def test_is_action_available(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        assert obj.is_action_available("view", "admin") is True
        assert obj.is_action_available("nonexistent", "admin") is False

    def test_custom_action(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        def doubler(instance, params, actor_id):
            return {"result": params.get("x", 0) * 2}
        obj.register_action(
            "double", "Double", "Doubles a number", doubler,
        )
        result = obj.execute_action("double", {"x": 21}, actor_id="admin")
        assert result.success is True
        assert result.result["result"] == 42

    def test_unknown_action(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="admin", updated_by="admin", owner_id="admin",
        )
        result = obj.execute_action("nonexistent", actor_id="admin")
        assert result.success is False
        assert "Unknown action" in result.error


# =============================================================================
# §18 — Versioning
# =============================================================================

class TestVersioning:
    def test_initial_version(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.version == 1

    def test_version_bumps_on_modification(self):
        obj = UniversalObject(
            object_type="test", name="Original",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.name = "Modified"
        assert obj.version == 2

    def test_get_version(self):
        obj = UniversalObject(
            object_type="test", name="Original",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.name = "Modified"
        snapshot = obj.get_version(1)
        assert snapshot is not None
        assert snapshot["name"] == "Original"

    def test_get_version_nonexistent(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj.get_version(999) is None

    def test_get_latest_version(self):
        obj = UniversalObject(
            object_type="test", name="Original",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.name = "Modified"
        latest = obj.get_latest_version()
        assert latest["name"] == "Modified"

    def test_compare_versions(self):
        obj = UniversalObject(
            object_type="test", name="Original",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.name = "Modified"
        diff = obj.compare_versions(1, obj.version)
        assert diff.version_from == 1
        assert diff.version_to == 2
        assert "name" in diff.changed_fields
        assert diff.changed_fields["name"] == ("Original", "Modified")

    def test_compare_versions_nonexistent_raises(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        with pytest.raises(ValueError):
            obj.compare_versions(1, 999)

    def test_version_history(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert len(obj.version_history) >= 1
        assert obj.version_history[0].version == 1


# =============================================================================
# Serialization Round-Trip
# =============================================================================

class TestSerialization:
    def test_to_dict_has_all_top_keys(self):
        obj = UniversalObject(
            object_type="human", name="Alice",
            created_by="c", updated_by="c", owner_id="o",
        )
        d = obj.to_dict()
        assert d["object_id"]
        assert d["object_type"] == "human"
        assert d["name"] == "Alice"
        assert "identity" in d
        assert "metadata" in d
        assert "relationships" in d
        assert "timeline" in d
        assert "lifecycle" in d
        assert "status" in d
        assert "ownership" in d
        assert "permissions" in d
        assert "evidence" in d
        assert "ai_context" in d
        assert "audit" in d
        assert "actions" in d
        assert "versioning" in d

    def test_round_trip_full(self):
        obj = UniversalObject(
            object_type="human", name="Alice",
            created_by="creator_1", updated_by="creator_1",
            owner_id="org_1",
            description="Test person",
            tags=["user", "active"],
            external_ids={"crm": "C-001"},
            aliases=["Ali"],
            source="human",
            source_detail="manual",
            custom_metadata={"pipeline": "ingest"},
        )
        obj.add_relationship("target_org", "member_of", label="Employee")
        obj.add_evidence("ev_001", description="Contract")
        obj.transition("active", reason="verified")

        data = obj.to_dict()
        restored = UniversalObject.from_dict(data)

        assert restored.object_id == obj.object_id
        assert restored.object_type == obj.object_type
        assert restored.name == obj.name
        assert restored.description == obj.description
        assert restored.status == obj.status
        assert restored.version == obj.version
        assert restored.owner_id == obj.owner_id
        assert restored.created_by == obj.created_by
        assert restored.tags == obj.tags
        assert restored.external_ids == obj.external_ids
        assert restored.aliases == obj.aliases
        assert restored.source == obj.source
        assert len(restored.relationships) == len(obj.relationships)
        assert restored.verify_integrity() is True

    def test_round_trip_with_flat_dict(self):
        data = {
            "object_id": "custom-id",
            "object_type": "widget",
            "name": "Widget",
            "status": "active",
            "owner_id": "owner_1",
            "created_by": "sys",
            "updated_by": "sys",
        }
        obj = UniversalObject.from_dict(data)
        assert obj.object_id == "custom-id"
        assert obj.status == "active"
        assert obj.name == "Widget"


# =============================================================================
# Equality & Hashing
# =============================================================================

class TestEquality:
    def test_equal_same_object(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert obj == obj

    def test_not_equal_different_id(self):
        a = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        b = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert a != b

    def test_hashable(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        s = {obj, obj}
        assert len(s) == 1

    def test_str_repr(self):
        obj = UniversalObject(
            object_type="human", name="Alice",
            created_by="s", updated_by="s", owner_id="o",
        )
        assert "Alice" in str(obj)
        assert "Alice" in repr(obj)


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    def test_large_aliases(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        aliases = [f"alias_{i}" for i in range(100)]
        for a in aliases:
            obj.add_alias(a)
        assert len(obj.aliases) == 100

    def test_many_relationships(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        for i in range(50):
            obj.add_relationship(f"target_{i}", f"type_{i % 3}")
        assert len(obj.get_relationships()) == 50
        filtered = obj.get_relationships(relationship_type="type_0")
        assert len(filtered) == 17  # 50/3 ≈ 17

    def test_status_updated_timestamps(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        t1 = obj.status_updated_at
        obj.transition("active", actor_id="admin")
        t2 = obj.status_updated_at
        assert t2 >= t1
        assert obj.status_updated_by == "admin"

    def test_confidence_with_all_superseded(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_evidence("ev_001")
        obj.add_evidence("ev_002")
        obj.remove_evidence("ev_001")
        obj.remove_evidence("ev_002")
        assert obj.get_confidence() == 0.0

    def test_empty_timeline_summary(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        # Fresh object always has 1 event, so let's check an edge
        summary = obj.get_timeline_summary()
        assert summary["total_events"] >= 1

    def test_transition_with_evidence(self):
        obj = UniversalObject(
            object_type="test", name="T",
            created_by="s", updated_by="s", owner_id="o",
        )
        obj.add_evidence("ev_approval")
        obj.transition("active", evidence_ids=["ev_approval"], reason="verified")
        hist = obj.get_lifecycle_history()
        assert hist[0].evidence_ids == ["ev_approval"]