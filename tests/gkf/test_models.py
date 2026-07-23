"""Tests for all GKF data models — 11 element types.

Tests: construction, immutability, to_dict, auto-generation,
edge cases, failure cases, serialization, property helpers.
"""

import pytest
from datetime import datetime
from app.gkf.enums import AmendmentType, ElementStatus, GKFNodeType
from app.gkf.models import (
    GovernedCollection, Volume, Chapter, Article, Principle,
    Interpretation, Reference, GKFEvidence, ImplementationLink,
    Amendment, GKFVersion,
)
from app.gkf.identity import is_principle_identity_stable


# =========================================================================
# GovernedCollection Tests
# =========================================================================

class TestGovernedCollection:
    def test_minimal_construction(self):
        gc = GovernedCollection(name="Test Collection")
        assert gc.collection_id.startswith("gkc_")
        assert gc.name == "Test Collection"
        assert gc.status == ElementStatus.DRAFT.value

    def test_explicit_identity(self):
        gc = GovernedCollection(collection_id="gkc_my_collection", name="My Collection")
        assert gc.collection_id == "gkc_my_collection"

    def test_full_construction(self):
        gc = GovernedCollection(
            collection_id="gkc_test",
            name="Test",
            description="A test collection",
            jurisdiction="SHUNYA OS",
            status=ElementStatus.ACTIVE.value,
            established="2026-01-01T00:00:00",
        )
        assert gc.jurisdiction == "SHUNYA OS"
        assert gc.description == "A test collection"

    def test_immutable(self):
        gc = GovernedCollection(name="Test")
        with pytest.raises(Exception):
            gc.name = "New Name"

    def test_to_dict(self):
        gc = GovernedCollection(name="Test")
        d = gc.to_dict()
        assert d["node_type"] == GKFNodeType.COLLECTION.value
        assert d["name"] == "Test"
        assert d["status"] == ElementStatus.DRAFT.value

    def test_node_type_property(self):
        gc = GovernedCollection(name="Test")
        assert gc.node_type == GKFNodeType.COLLECTION.value

    def test_auto_established_timestamp(self):
        gc = GovernedCollection(name="Test")
        datetime.fromisoformat(gc.established)


class TestVolume:
    def test_minimal_explicit(self):
        v = Volume(collection_id="gkc_test", number=1)
        assert v.volume_id == "gkc_test:vol_1"

    def test_explicit_id(self):
        v = Volume(volume_id="gkc_test:vol_5", collection_id="gkc_test", number=5)
        assert v.volume_id == "gkc_test:vol_5"

    def test_immutable(self):
        v = Volume(collection_id="gkc_test", number=1)
        with pytest.raises(Exception):
            v.title = "New Title"

    def test_to_dict(self):
        v = Volume(collection_id="gkc_test", number=1, title="Rights")
        d = v.to_dict()
        assert d["node_type"] == GKFNodeType.VOLUME.value
        assert d["number"] == 1
        assert d["title"] == "Rights"

    def test_node_type(self):
        v = Volume(collection_id="gkc_test", number=1)
        assert v.node_type == GKFNodeType.VOLUME.value


class TestChapter:
    def test_auto_id(self):
        ch = Chapter(volume_id="gkc_test:vol_1", number=1)
        assert ch.chapter_id == "gkc_test:vol_1:ch_1"

    def test_explicit_id(self):
        ch = Chapter(chapter_id="gkc_test:vol_1:ch_3", volume_id="gkc_test:vol_1", number=3)
        assert ch.chapter_id == "gkc_test:vol_1:ch_3"

    def test_immutable(self):
        ch = Chapter(volume_id="gkc_test:vol_1", number=1)
        with pytest.raises(Exception):
            ch.title = "New"

    def test_to_dict(self):
        ch = Chapter(volume_id="gkc_test:vol_1", number=1, title="First Chapter")
        d = ch.to_dict()
        assert d["node_type"] == GKFNodeType.CHAPTER.value
        assert d["number"] == 1
        assert d["title"] == "First Chapter"


class TestArticle:
    def test_auto_id(self):
        a = Article(collection_id="gkc_test", number=1)
        assert a.article_id == "gkc_test:art_1"

    def test_with_body(self):
        a = Article(collection_id="gkc_test", number=1, title="Human First", body="No system behavior...")
        assert a.body == "No system behavior..."
        assert a.version == 1

    def test_default_status_draft(self):
        a = Article(collection_id="gkc_test", number=1)
        assert a.status == ElementStatus.DRAFT.value

    def test_immutable(self):
        a = Article(collection_id="gkc_test", number=1)
        with pytest.raises(Exception):
            a.body = "new"

    def test_to_dict(self):
        a = Article(collection_id="gkc_test", number=1, title="Test", body="Body")
        d = a.to_dict()
        assert d["node_type"] == GKFNodeType.ARTICLE.value
        assert d["number"] == 1
        assert d["body"] == "Body"


class TestPrinciple:
    """Principles are the primary semantic objects — stable identity."""

    def test_auto_id_stable(self):
        p = Principle(collection_id="gkc_test", name="human_first", statement="Never override human will.")
        assert p.principle_id == "gkc_test:pr_human_first"
        assert is_principle_identity_stable(p.principle_id)

    def test_principle_id_does_not_contain_location(self):
        p = Principle(collection_id="gkc_test", name="agency", statement="Humans choose.")
        assert "art_" not in p.principle_id
        assert "vol_" not in p.principle_id
        assert "ch_" not in p.principle_id

    def test_default_status_active(self):
        p = Principle(collection_id="gkc_test", name="test", statement="X")
        assert p.status == ElementStatus.ACTIVE.value

    def test_is_active(self):
        p = Principle(collection_id="gkc_test", name="test", statement="X")
        assert p.is_active
        assert not p.is_superseded

    def test_is_superseded(self):
        p = Principle(collection_id="gkc_test", name="test", statement="X", status=ElementStatus.SUPERSEDED.value)
        assert p.is_superseded
        assert not p.is_active

    def test_with_category(self):
        p = Principle(collection_id="gkc_test", name="privacy", statement="X", category="privacy")
        assert p.category == "privacy"

    def test_immutable(self):
        p = Principle(collection_id="gkc_test", name="test", statement="X")
        with pytest.raises(Exception):
            p.statement = "Y"

    def test_to_dict(self):
        p = Principle(collection_id="gkc_test", name="human_first", statement="People first.")
        d = p.to_dict()
        assert d["node_type"] == GKFNodeType.PRINCIPLE.value
        assert d["name"] == "human_first"
        assert d["statement"] == "People first."

    def test_principle_governs(self):
        """Principles are the primary semantic objects per §2.2."""
        p = Principle(collection_id="gkc_test", name="test", statement="Governing statement.")
        d = p.to_dict()
        assert d["statement"] == "Governing statement."


class TestInterpretation:
    def test_auto_id(self):
        i = Interpretation(principle_id="gkc_test:pr_test", number=1)
        assert i.interpretation_id == "gkc_test:pr_test:int_1"

    def test_with_authority(self):
        i = Interpretation(principle_id="gkc_test:pr_test", number=1, authority="Founder")
        assert i.authority == "Founder"

    def test_immutable(self):
        i = Interpretation(principle_id="gkc_test:pr_test", number=1)
        with pytest.raises(Exception):
            i.statement = "new"

    def test_to_dict(self):
        i = Interpretation(principle_id="gkc_test:pr_test", number=1, statement="Clarification.")
        d = i.to_dict()
        assert d["node_type"] == GKFNodeType.INTERPRETATION.value
        assert d["statement"] == "Clarification."


class TestReference:
    def test_auto_id(self):
        r = Reference(source_id="gkc_test:art_1", target_id="gkc_test:art_2")
        assert r.reference_id.startswith("gkc_test:art_1:ref_")

    def test_with_relationship(self):
        r = Reference(source_id="gkc_test:art_1", target_id="gkc_test:art_2", relationship="depends_on")
        assert r.relationship == "depends_on"

    def test_immutable(self):
        r = Reference(source_id="gkc_test:art_1", target_id="gkc_test:art_2")
        with pytest.raises(Exception):
            r.source_id = "new"

    def test_to_dict(self):
        r = Reference(source_id="a", target_id="b", relationship="supports")
        d = r.to_dict()
        assert d["node_type"] == GKFNodeType.REFERENCE.value
        assert d["relationship"] == "supports"


class TestGKFEvidence:
    def test_auto_id(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="constitution")
        assert e.evidence_id == "gkc_test:ev_document_constitution"

    def test_with_body(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="test",
                         title="Founder Directive", authority="Founder", body="The system must...")
        assert e.title == "Founder Directive"
        assert e.authority == "Founder"

    def test_immutable(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="test")
        with pytest.raises(Exception):
            e.title = "new"

    def test_to_dict(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="test")
        d = e.to_dict()
        assert d["node_type"] == GKFNodeType.EVIDENCE.value
        assert d["source_type"] == "document"


class TestImplementationLink:
    def test_auto_id(self):
        il = ImplementationLink(principle_id="gkc_test:pr_test", module_path="app/kernel/object.py")
        assert il.link_id.startswith("gkc_test:pr_test:impl_")

    def test_with_code_reference(self):
        il = ImplementationLink(principle_id="gkc_test:pr_test", module_path="app/kernel",
                                 code_reference="class Object", status="implemented")
        assert il.code_reference == "class Object"
        assert il.status == "implemented"

    def test_immutable(self):
        il = ImplementationLink(principle_id="gkc_test:pr_test", module_path="app.py")
        with pytest.raises(Exception):
            il.status = "new"

    def test_to_dict(self):
        il = ImplementationLink(principle_id="gkc_test:pr_test", module_path="app.py")
        d = il.to_dict()
        assert d["node_type"] == GKFNodeType.IMPLEMENTATION_LINK.value
        assert d["module_path"] == "app.py"


class TestAmendment:
    def test_auto_id(self):
        a = Amendment(target_id="gkc_test:art_1", number=1)
        assert a.amendment_id == "gkc_test:art_1:amd_1"

    def test_default_type(self):
        a = Amendment(target_id="gkc_test:art_1", number=1)
        assert a.amendment_type == AmendmentType.MODIFICATION.value

    def test_addition_type(self):
        a = Amendment(target_id="gkc_test:art_1", number=1, amendment_type=AmendmentType.ADDITION.value)
        assert a.amendment_type == "addition"

    def test_supersession_type(self):
        a = Amendment(target_id="gkc_test:art_1", number=1, amendment_type=AmendmentType.SUPERSESSION.value)
        assert a.amendment_type == "supersession"

    def test_all_amendment_types(self):
        for at in AmendmentType:
            a = Amendment(target_id="gkc_test:art_1", number=1, amendment_type=at.value)
            assert a.amendment_type == at.value

    def test_immutable(self):
        a = Amendment(target_id="gkc_test:art_1", number=1)
        with pytest.raises(Exception):
            a.reason = "new"

    def test_to_dict(self):
        a = Amendment(target_id="gkc_test:art_1", number=2, reason="Updated wording")
        d = a.to_dict()
        assert d["node_type"] == GKFNodeType.AMENDMENT.value
        assert d["number"] == 2
        assert d["reason"] == "Updated wording"


class TestGKFVersion:
    def test_auto_id(self):
        v = GKFVersion(element_id="gkc_test:art_1", number=1)
        assert v.version_id == "gkc_test:art_1:v1"

    def test_with_content(self):
        v = GKFVersion(element_id="gkc_test:art_1", number=1, content={"body": "Original text"})
        assert v.content["body"] == "Original text"

    def test_immutable(self):
        v = GKFVersion(element_id="gkc_test:art_1", number=1)
        with pytest.raises(Exception):
            v.number = 2

    def test_to_dict(self):
        v = GKFVersion(element_id="gkc_test:art_1", number=1, content={"body": "X"})
        d = v.to_dict()
        assert d["node_type"] == GKFNodeType.VERSION.value
        assert d["number"] == 1
        assert d["content"]["body"] == "X"


# =========================================================================
# Cross-Model Consistency
# =========================================================================

class TestCrossModelConsistency:
    def test_article_and_principle_independent_ids(self):
        """Articles and Principles have independent identity schemes."""
        a = Article(collection_id="gkc_test", number=1)
        p = Principle(collection_id="gkc_test", name="human_first", statement="X")
        assert a.article_id != p.principle_id
        assert a.article_id.endswith("art_1")
        assert p.principle_id.endswith("pr_human_first")

    def test_principle_to_interpretation_chain(self):
        p = Principle(collection_id="gkc_test", name="test", statement="X")
        i = Interpretation(principle_id=p.principle_id, number=1)
        assert p.principle_id in i.interpretation_id

    def test_element_to_version_chain(self):
        a = Article(collection_id="gkc_test", number=1)
        v = GKFVersion(element_id=a.article_id, number=1)
        assert v.element_id == a.article_id

    def test_principle_to_implementation_link_chain(self):
        p = Principle(collection_id="gkc_test", name="test", statement="X")
        il = ImplementationLink(principle_id=p.principle_id, module_path="app.py")
        assert p.principle_id in il.link_id

    def test_article_to_amendment_chain(self):
        a = Article(collection_id="gkc_test", number=1)
        am = Amendment(target_id=a.article_id, number=1)
        assert am.target_id == a.article_id


# =========================================================================
# Edge Cases
# =========================================================================

class TestEdgeCases:
    def test_empty_article_body(self):
        a = Article(collection_id="gkc_test", number=1)
        assert a.body == ""

    def test_long_principle_statement(self):
        long_stmt = "X " * 100
        p = Principle(collection_id="gkc_test", name="test", statement=long_stmt)
        assert len(p.statement) > 100

    def test_metadata_flexibility(self):
        gc = GovernedCollection(name="Test", metadata={"custom": "value", "tags": ["a", "b"]})
        assert gc.metadata["custom"] == "value"
        assert "b" in gc.metadata["tags"]

    def test_multiple_interpretations(self):
        p = Principle(collection_id="gkc_test", name="test", statement="X")
        i1 = Interpretation(principle_id=p.principle_id, number=1)
        i2 = Interpretation(principle_id=p.principle_id, number=2)
        assert i1.interpretation_id != i2.interpretation_id

    def test_auto_timestamp_on_evidence(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="test")
        datetime.fromisoformat(e.established)

    def test_auto_timestamp_on_amendment(self):
        a = Amendment(target_id="gkc_test:art_1", number=1)
        datetime.fromisoformat(a.established)

    def test_auto_timestamp_on_interpretation(self):
        i = Interpretation(principle_id="gkc_test:pr_test", number=1)
        datetime.fromisoformat(i.established)

    def test_evidence_with_multiple_source_types(self):
        for st in ["founder_directive", "constitutional_document", "adr", "statute", "policy", "contract"]:
            e = GKFEvidence(collection_id="gkc_test", source_type=st, local_id=st)
            assert e.source_type == st

    def test_article_versions_increment(self):
        a1 = Article(collection_id="gkc_test", number=1, version=1)
        a2 = Article(collection_id="gkc_test", number=1, version=2)
        assert a1.version == 1
        assert a2.version == 2
        assert a1.article_id == a2.article_id

    def test_principle_with_special_name_chars(self):
        p = Principle(collection_id="gkc_test", name="data-privacy_rule_42", statement="X")
        assert "data" in p.principle_id
        assert "privacy" in p.principle_id

    def test_collection_with_full_metadata(self):
        gc = GovernedCollection(
            name="GDPR",
            description="General Data Protection Regulation",
            jurisdiction="European Union",
            status=ElementStatus.ACTIVE.value,
        )
        assert gc.jurisdiction == "European Union"

    def test_volume_with_description(self):
        v = Volume(collection_id="gkc_test", number=1, title="Rights", description="Fundamental rights")
        assert v.description == "Fundamental rights"

    def test_chapter_without_number(self):
        ch = Chapter(volume_id="gkc_test:vol_1", number=0)
        assert ch.chapter_id == "gkc_test:vol_1:ch_0"

    def test_interpretation_with_metadata(self):
        i = Interpretation(
            principle_id="gkc_test:pr_test", number=1,
            statement="Clarification text",
            authority="Founder",
            metadata={"source": "directive_001"},
        )
        assert i.metadata["source"] == "directive_001"

    def test_reference_to_same_element(self):
        r = Reference(source_id="gkc_test:art_1", target_id="gkc_test:art_1")
        assert r.reference_id is not None

    def test_implementation_link_statuses(self):
        for status in ["implemented", "partial", "planned", "not_applicable"]:
            il = ImplementationLink(
                principle_id="gkc_test:pr_test", module_path="app.py",
                status=status,
            )
            assert il.status == status

    def test_amendment_with_all_types(self):
        for at in AmendmentType:
            a = Amendment(target_id="gkc_test:art_1", number=1, amendment_type=at.value, reason=f"Test {at.value}")
            assert a.reason.startswith("Test")

    def test_version_with_content_preserved(self):
        v1 = GKFVersion(element_id="gkc_test:art_1", number=1, content={"body": "Original"})
        v2 = GKFVersion(element_id="gkc_test:art_1", number=2, content={"body": "Amended"})
        assert v1.content["body"] == "Original"
        assert v2.content["body"] == "Amended"

    def test_principle_to_dict_has_all_fields(self):
        p = Principle(
            collection_id="gkc_test", name="agency",
            statement="Humans choose.", category="human_agency",
        )
        d = p.to_dict()
        assert d["principle_id"] == "gkc_test:pr_agency"
        assert d["name"] == "agency"
        assert d["statement"] == "Humans choose."
        assert d["category"] == "human_agency"
        assert d["status"] == ElementStatus.ACTIVE.value

    def test_article_to_dict_has_version(self):
        a = Article(collection_id="gkc_test", number=1, title="Test", body="B", version=3)
        d = a.to_dict()
        assert d["version"] == 3
        assert d["body"] == "B"

    def test_evidence_to_dict_with_source_path(self):
        e = GKFEvidence(
            collection_id="gkc_test", source_type="document", local_id="constitution",
            source_path="architecture/SHUNYA_CONSTITUTION.md",
        )
        d = e.to_dict()
        assert d["source_path"] == "architecture/SHUNYA_CONSTITUTION.md"

    def test_amendment_to_dict_with_reason(self):
        a = Amendment(target_id="gkc_test:art_1", number=2, reason="Clarified wording", amendment_type=AmendmentType.MODIFICATION.value)
        d = a.to_dict()
        assert d["amendment_type"] == "modification"
        assert d["reason"] == "Clarified wording"

    def test_collection_node_type_enum_match(self):
        gc = GovernedCollection(name="Test")
        assert gc.node_type == GKFNodeType.COLLECTION.value

    def test_principle_node_type_enum_match(self):
        p = Principle(collection_id="gkc_test", name="test", statement="X")
        assert p.node_type == GKFNodeType.PRINCIPLE.value

    def test_reference_node_type_enum_match(self):
        r = Reference(source_id="a", target_id="b")
        assert r.node_type == GKFNodeType.REFERENCE.value