"""UniversalObject Protocol Compliance Test.

Verifies that core/kernel/object.py::UniversalObject implements all
15 mandatory sections of the Universal Object Protocol as defined in
docs/canon/04_universal_object_protocol.md.
"""

import pytest

from core.kernel import UniversalObject, ObjectStatus


@pytest.fixture
def obj() -> UniversalObject:
    return UniversalObject(
        object_type="test_entity",
        name="Test Object",
        created_by="tester",
        updated_by="tester",
        owner_id="owner_123",
    )


class TestProtocolIdentitySection:
    """§4 — Identity."""

    def test_has_object_id(self, obj: UniversalObject) -> None:
        assert obj.object_id

    def test_supports_external_ids(self, obj: UniversalObject) -> None:
        obj.add_external_id("crm", "CRM-123")
        assert obj.external_ids.get("crm") == "CRM-123"

    def test_supports_aliases(self, obj: UniversalObject) -> None:
        obj.add_alias("Alias Name")
        assert "Alias Name" in obj.aliases


class TestProtocolMetadataSection:
    """§5 — Metadata."""

    def test_has_created_at(self, obj: UniversalObject) -> None:
        assert obj.created_at

    def test_has_source(self, obj: UniversalObject) -> None:
        assert obj.source


class TestProtocolRelationshipsSection:
    """§6 — Relationships."""

    def test_can_add_relationship(self, obj: UniversalObject) -> None:
        obj.add_relationship(target_id="other_obj", relationship_type="depends_on")
        rels = obj.get_relationships()
        assert any(r.target_id == "other_obj" for r in rels)


class TestProtocolTimelineSection:
    """§7 — Timeline."""

    def test_has_initial_event(self, obj: UniversalObject) -> None:
        events = obj.get_events()
        assert len(events) >= 1

    def test_can_add_event(self, obj: UniversalObject) -> None:
        obj.add_event("test_event", {"key": "value"}, source="tester")
        events = obj.get_events()
        assert any(e.event_type == "test_event" for e in events)


class TestProtocolLifecycleSection:
    """§8 — Lifecycle."""

    def test_default_transitions(self, obj: UniversalObject) -> None:
        assert obj.current_stage == "pending"
        obj.transition("active", reason="verification")
        assert obj.current_stage == "active"


class TestProtocolStatusSection:
    """§9 — Status."""

    def test_has_status(self, obj: UniversalObject) -> None:
        assert obj.status is not None

    def test_status_update_records_actor(self, obj: UniversalObject) -> None:
        obj.transition("active", reason="test")
        assert obj.status_updated_by is not None


class TestProtocolOwnershipSection:
    """§10 — Ownership."""

    def test_has_owner(self, obj: UniversalObject) -> None:
        assert obj.owner_id == "owner_123"

    def test_transfer_ownership(self, obj: UniversalObject) -> None:
        obj.transfer("new_owner", reason="reassignment")
        assert obj.owner_id == "new_owner"
        assert len(obj.owner_history) == 2


class TestProtocolPermissionsSection:
    """§11 — Permissions."""

    def test_has_acl(self, obj: UniversalObject) -> None:
        assert obj.acl is not None

    def test_can_grant_access(self, obj: UniversalObject) -> None:
        obj.grant("viewer_1", role="viewer", granted_by="admin")
        assert obj.check_permission("viewer_1", "view") is True


class TestProtocolEvidenceSection:
    """§12 — Evidence."""

    def test_can_add_evidence(self, obj: UniversalObject) -> None:
        obj.add_evidence("ev_001")
        ids = [e.evidence_id for e in obj.get_evidence()]
        assert "ev_001" in ids


class TestProtocolMemorySection:
    """§13 — Memory (OPTIONAL)."""

    def test_can_record_memory(self, obj: UniversalObject) -> None:
        obj.associate_memory("mem_001")
        assert "mem_001" in obj.memory_ids


class TestProtocolAIContextSection:
    """§14 — AI Context."""

    def test_can_generate_context(self, obj: UniversalObject) -> None:
        ctx = obj.get_ai_context()
        assert isinstance(ctx, str)


class TestProtocolSearchSection:
    """§15 — Search."""

    def test_search_returns_results(self, obj: UniversalObject) -> None:
        results = obj.search("Test")
        assert isinstance(results, list)


class TestProtocolAuditSection:
    """§16 — Audit."""

    def test_has_audit_log(self, obj: UniversalObject) -> None:
        log = obj.get_audit_log()
        assert len(log) >= 1

    def test_creation_audit_entry(self, obj: UniversalObject) -> None:
        log = obj.get_audit_log()
        assert log[0].action == "object_created"


class TestProtocolActionsSection:
    """§17 — Actions."""

    def test_has_available_actions(self, obj: UniversalObject) -> None:
        actions = obj.get_available_actions("owner_123")
        assert len(actions) >= 3

    def test_can_execute_action(self, obj: UniversalObject) -> None:
        result = obj.execute_action("view", actor_id="owner_123")
        assert result.success is True


class TestProtocolVersioningSection:
    """§18 — Versioning."""

    def test_starts_at_version_1(self, obj: UniversalObject) -> None:
        assert obj.version == 1

    def test_version_bumps_on_update(self, obj: UniversalObject) -> None:
        obj.name = "Updated Name"
        assert obj.version >= 2

    def test_has_version_history(self, obj: UniversalObject) -> None:
        history = obj.version_history
        assert len(history) >= 1