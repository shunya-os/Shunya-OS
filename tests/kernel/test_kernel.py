"""Tests for SHUNYA Kernel — Universal Object, Identity, Space, Relationship.
"""

import pytest
from app.kernel.object import (
    UniversalObject, ObjectRegistry, ObjectStatus,
    EvidenceRef, RelationshipRef, get_registry, reset_registry,
)
from app.kernel.identity import (
    SHUNYAIdentity, IdentityStore, AuthMethodType,
    AuthenticationMethod, get_identity_store, reset_identity_store,
)
from app.kernel.space import (
    Space, SpaceStore, SpaceType, SpaceRole, get_space_store, reset_space_store,
)
from app.kernel.relationship import (
    Relationship, RelationshipEngine, RelationshipType,
    get_relationship_engine, reset_relationship_engine,
)


class TestUniversalObject:
    """UniversalObject contract enforcement."""

    def test_auto_generates_id(self):
        obj = UniversalObject(name="Test")
        assert obj.object_id != ""
        assert len(obj.object_id) > 20
        assert obj.is_active

    def test_has_required_fields(self):
        obj = UniversalObject(name="Required")
        assert hasattr(obj, "object_id")
        assert hasattr(obj, "status")
        assert hasattr(obj, "version")
        assert hasattr(obj, "confidence")
        assert hasattr(obj, "created_at")
        assert hasattr(obj, "updated_at")
        assert hasattr(obj, "evidence")
        assert hasattr(obj, "relationships")

    def test_evidence_attachment(self):
        obj = UniversalObject(name="Ev")
        ev = EvidenceRef(object_id="target", object_type="Test")
        obj.add_evidence(ev)
        assert len(obj.evidence) == 1

    def test_relationship_attachment(self):
        obj = UniversalObject(name="Rel")
        ref = RelationshipRef(object_id="target", object_type="Other")
        obj.add_relationship(ref)
        assert len(obj.relationships) == 1

    def test_lifecycle(self):
        obj = UniversalObject(name="Life")
        assert obj.status == ObjectStatus.ACTIVE.value
        obj.archive()
        assert obj.status == ObjectStatus.ARCHIVED.value
        obj.supersede()
        assert obj.status == ObjectStatus.SUPERSEDED.value

    def test_to_dict(self):
        obj = UniversalObject(name="Dict", object_type="Custom")
        d = obj.to_dict()
        assert d["name"] == "Dict"
        assert d["object_type"] == "Custom"
        assert "object_id" in d

    def test_registry(self):
        reg = get_registry()
        types = reg.types()
        assert "SHUNYAIdentity" in types
        assert "Space" in types


class TestSHUNYAIdentity:
    """SHUNYA Universal Identity."""

    def test_create_identity(self):
        identity = SHUNYAIdentity(display_name="Alice", primary_email="alice@test.com")
        assert identity.identity_id.startswith("sid_")
        assert identity.display_name == "Alice"

    def test_add_auth_method(self):
        identity = SHUNYAIdentity(display_name="Bob")
        method = AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value,
            identifier="bob@test.com",
            is_primary=True,
        )
        identity.add_auth_method(method)
        assert identity.has_auth_method(AuthMethodType.EMAIL.value, "bob@test.com")

    def test_multiple_auth_methods(self):
        identity = SHUNYAIdentity(display_name="Multi")
        identity.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value, identifier="a@test.com"))
        identity.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.GMAIL.value, identifier="a@gmail.com"))
        identity.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.PHONE.value, identifier="+1555123"))
        assert len(identity.auth_methods) == 3

    def test_deduplicate_auth_methods(self):
        identity = SHUNYAIdentity(display_name="Dedup")
        identity.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value, identifier="same@test.com"))
        identity.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value, identifier="same@test.com"))
        assert len(identity.auth_methods) == 1

    def test_remove_auth_method(self):
        identity = SHUNYAIdentity(display_name="Rem")
        identity.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value, identifier="rem@test.com"))
        assert identity.remove_auth_method(AuthMethodType.EMAIL.value, "rem@test.com")
        assert not identity.has_auth_method(AuthMethodType.EMAIL.value, "rem@test.com")

    def test_suggest_link(self):
        identity = SHUNYAIdentity(display_name="Linker")
        method = AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value, identifier="link@test.com")
        suggestion = identity.suggest_link(method, reason="Email match", confidence=0.9)
        assert suggestion.status == "suggested"
        assert len(identity.linking_suggestions) == 1

    def test_reject_link(self):
        identity = SHUNYAIdentity(display_name="Rejector")
        method = AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value, identifier="reject@test.com")
        identity.suggest_link(method)
        identity.reject_link(method)
        assert identity.linking_suggestions[0].status == "rejected"

    def test_detect_potential_links(self):
        a = SHUNYAIdentity(display_name="A")
        a.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value, identifier="shared@test.com"))
        b = SHUNYAIdentity(display_name="B")
        b.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.EMAIL.value, identifier="shared@test.com"))
        results = a.detect_potential_links([a, b])
        assert len(results) == 1
        assert results[0]["method"].identifier == "shared@test.com"

    def test_identity_store(self):
        reset_identity_store()
        store = get_identity_store()
        identity = store.create("Alice", "alice@test.com")
        assert store.get(identity.identity_id) is not None
        found = store.find_by_auth(AuthMethodType.EMAIL.value, "alice@test.com")
        assert found is not None
        assert found.identity_id == identity.identity_id


class TestSpace:
    """Space architecture."""

    def test_create_personal_space(self):
        space = Space(name="My Space", space_type=SpaceType.PERSONAL.value)
        assert space.space_id.startswith("spc_")
        assert space.space_type == SpaceType.PERSONAL.value

    def test_add_member(self):
        space = Space(name="Team Space", space_type=SpaceType.ORGANIZATION.value)
        space.add_member("sid_test123", role=SpaceRole.OWNER.value)
        assert space.has_member("sid_test123")
        assert space.get_member("sid_test123").role == SpaceRole.OWNER.value

    def test_remove_member(self):
        space = Space(name="Test")
        space.add_member("sid_remove")
        assert space.remove_member("sid_remove")
        assert not space.has_member("sid_remove")

    def test_space_store(self):
        reset_space_store()
        store = get_space_store()
        space = store.create("Personal", space_type=SpaceType.PERSONAL.value,
                             owner_id="sid_owner")
        assert store.get(space.space_id) is not None
        spaces = store.get_for_identity("sid_owner")
        assert len(spaces) == 1
        assert spaces[0].name == "Personal"


class TestRelationshipEngine:
    """Relationship engine — graph navigation."""

    def test_add_relationship(self):
        eng = get_relationship_engine()
        rel = Relationship(
            source_id="obj_a", target_id="obj_b",
            relationship_type=RelationshipType.RELATED_TO.value,
        )
        eng.add(rel)
        assert eng.count() == 1

    def test_bidirectional(self):
        eng = get_relationship_engine()
        fwd, rev = eng.add_bidirectional(
            "alice", "bob",
            RelationshipType.FOLLOWS.value,
            RelationshipType.PRECEDES.value,
        )
        assert fwd.source_id == "alice"
        assert rev.source_id == "bob"

    def test_traversal(self):
        eng = get_relationship_engine()
        eng.add_bidirectional("a", "b", "follows", "precedes")
        eng.add_bidirectional("b", "c", "follows", "precedes")
        results = eng.traverse("a", max_depth=2)
        assert 1 in results  # depth 1
        assert 2 in results  # depth 2

    def test_get_connected(self):
        eng = get_relationship_engine()
        eng.add_bidirectional("x", "y", "knows", "known_by")
        eng.add_bidirectional("x", "z", "knows", "known_by")
        connected = eng.get_connected("x")
        assert "y" in connected
        assert "z" in connected

    def test_remove(self):
        reset_relationship_engine()
        eng = get_relationship_engine()
        eng.add(Relationship(
            source_id="src", target_id="dst",
            relationship_type=RelationshipType.REFERENCES.value,
        ))
        assert eng.remove("src", "dst", RelationshipType.REFERENCES.value)
        assert eng.count() == 0

    def test_global_reset(self):
        reset_relationship_engine()
        eng = get_relationship_engine()
        assert eng.count() == 0