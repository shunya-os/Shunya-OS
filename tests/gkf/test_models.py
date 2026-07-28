"""Tests for GKF models — GKF-001A semantic enrichment."""

import pytest
from datetime import datetime
from app.gkf.enums import (
    AmendmentType, AuthorityType, ElementStatus, GKFNodeType, SemanticCategory,
)
from app.gkf.models import (
    GovernedCollection, Volume, Chapter, Article, GoverningPrinciple,
    Interpretation, Reference, Citation, Authority, Commentary, Example,
    GKFEvidence, ImplementationLink, ImplementationGuidance,
    Amendment, GKFVersion,
)
from app.gkf.identity import is_principle_identity_stable


class TestGovernedCollection:
    def test_minimal(self):
        gc = GovernedCollection(name="Test")
        assert gc.collection_id.startswith("gkc_")

    def test_to_dict(self):
        gc = GovernedCollection(name="Test")
        d = gc.to_dict()
        assert d["node_type"] == GKFNodeType.COLLECTION.value


class TestVolume:
    def test_auto_id(self):
        v = Volume(collection_id="gkc_test", number=1)
        assert v.volume_id == "gkc_test:vol_1"


class TestChapter:
    def test_auto_id(self):
        ch = Chapter(volume_id="gkc_test:vol_1", number=1)
        assert ch.chapter_id == "gkc_test:vol_1:ch_1"


class TestArticle:
    def test_auto_id(self):
        a = Article(collection_id="gkc_test", number=1)
        assert a.article_id == "gkc_test:art_1"

    def test_to_dict(self):
        a = Article(collection_id="gkc_test", number=1, title="Test")
        d = a.to_dict()
        assert d["node_type"] == GKFNodeType.ARTICLE.value


class TestGoverningPrinciple:
    def test_auto_id_stable(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="human_first", statement="X")
        assert gp.governing_principle_id == "gkc_test:gp_human_first"
        assert is_principle_identity_stable(gp.governing_principle_id)

    def test_no_location_in_id(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="agency", statement="X")
        assert "art_" not in gp.governing_principle_id
        assert "vol_" not in gp.governing_principle_id

    def test_is_active(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X")
        assert gp.is_active

    def test_is_superseded(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X",
                                 status=ElementStatus.SUPERSEDED.value)
        assert gp.is_superseded

    def test_with_authority(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X",
                                 authority_id="gkc_test:auth_founder")
        assert gp.authority_id == "gkc_test:auth_founder"

    def test_with_category(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X",
                                 category=SemanticCategory.GOVERNANCE.value)
        assert gp.category == "governance"

    def test_immutable(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X")
        with pytest.raises(Exception):
            gp.statement = "Y"

    def test_to_dict_includes_authority(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X",
                                 authority_id="gkc_test:auth_founder")
        d = gp.to_dict()
        assert d["authority_id"] == "gkc_test:auth_founder"
        assert d["node_type"] == GKFNodeType.GOVERNING_PRINCIPLE.value

    def test_to_dict_no_authority_omits_field(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X")
        d = gp.to_dict()
        assert "authority_id" not in d or d["authority_id"] == ""


class TestInterpretation:
    def test_auto_id(self):
        i = Interpretation(governing_principle_id="gkc_test:gp_test", number=1)
        assert i.interpretation_id == "gkc_test:gp_test:int_1"

    def test_to_dict(self):
        i = Interpretation(governing_principle_id="gkc_test:gp_test", number=1, statement="X")
        d = i.to_dict()
        assert d["governing_principle_id"] == "gkc_test:gp_test"


class TestReference:
    def test_auto_id(self):
        r = Reference(source_id="a", target_id="b")
        assert r.reference_id is not None

    def test_to_dict(self):
        r = Reference(source_id="a", target_id="b", relationship="supports")
        d = r.to_dict()
        assert d["relationship"] == "supports"


class TestCitation:
    def test_auto_id(self):
        c = Citation(source_id="gkc_test:gp_test", external_source="GDPR")
        assert c.citation_id.startswith("gkc_test:gp_test:cit_")

    def test_external_url(self):
        c = Citation(source_id="gkc_test:gp_test", external_source="GDPR",
                      external_url="https://gdpr.eu/article-5")
        assert c.external_url.startswith("https://")

    def test_with_title_and_excerpt(self):
        c = Citation(source_id="a", external_source="b",
                      title="GDPR Article 5", excerpt="Personal data shall be...")
        assert c.title == "GDPR Article 5"
        assert "Personal data" in c.excerpt

    def test_immutable(self):
        c = Citation(source_id="a", external_source="b")
        with pytest.raises(Exception):
            c.title = "new"

    def test_to_dict(self):
        c = Citation(source_id="a", external_source="b")
        d = c.to_dict()
        assert d["node_type"] == GKFNodeType.CITATION.value
        assert d["external_source"] == "b"


class TestAuthority:
    def test_auto_id(self):
        a = Authority(collection_id="gkc_test", name="founder")
        assert a.authority_id == "gkc_test:auth_founder"

    def test_all_types(self):
        for at in AuthorityType:
            a = Authority(collection_id="gkc_test", name=at.value, authority_type=at.value)
            assert a.authority_type == at.value

    def test_with_jurisdiction(self):
        a = Authority(collection_id="gkc_test", name="GDPR Board",
                       authority_type=AuthorityType.REGULATORY.value,
                       jurisdiction="European Union")
        assert a.jurisdiction == "European Union"

    def test_immutable(self):
        a = Authority(collection_id="gkc_test", name="founder")
        with pytest.raises(Exception):
            a.description = "new"

    def test_to_dict(self):
        a = Authority(collection_id="gkc_test", name="founder",
                       authority_type=AuthorityType.FOUNDER.value)
        d = a.to_dict()
        assert d["node_type"] == GKFNodeType.AUTHORITY.value
        assert d["authority_type"] == "founder"


class TestCommentary:
    def test_auto_id(self):
        c = Commentary(governing_principle_id="gkc_test:gp_test", number=1)
        assert c.commentary_id == "gkc_test:gp_test:com_1"

    def test_with_author(self):
        c = Commentary(governing_principle_id="gkc_test:gp_test", number=1,
                        body="This means X.", author="Legal Team")
        assert c.author == "Legal Team"

    def test_immutable(self):
        c = Commentary(governing_principle_id="gkc_test:gp_test", number=1)
        with pytest.raises(Exception):
            c.body = "new"

    def test_to_dict(self):
        c = Commentary(governing_principle_id="gkc_test:gp_test", number=1, body="Explanation")
        d = c.to_dict()
        assert d["node_type"] == GKFNodeType.COMMENTARY.value
        assert d["body"] == "Explanation"


class TestExample:
    def test_auto_id(self):
        e = Example(governing_principle_id="gkc_test:gp_test", number=1)
        assert e.example_id == "gkc_test:gp_test:ex_1"

    def test_with_body_and_scenario(self):
        e = Example(governing_principle_id="gkc_test:gp_test", number=1,
                     body="User clicks Save.", scenario="Save document flow")
        assert e.body == "User clicks Save."
        assert e.scenario == "Save document flow"

    def test_to_dict(self):
        e = Example(governing_principle_id="gkc_test:gp_test", number=1, body="Example")
        d = e.to_dict()
        assert d["node_type"] == GKFNodeType.EXAMPLE.value
        assert d["body"] == "Example"


class TestImplementationGuidance:
    def test_auto_id(self):
        g = ImplementationGuidance(governing_principle_id="gkc_test:gp_test", name="authz")
        assert g.guidance_id == "gkc_test:gp_test:guidance_authz"

    def test_with_body_and_category(self):
        g = ImplementationGuidance(governing_principle_id="gkc_test:gp_test", name="authz",
                                    body="Use RBAC with attribute-based fallback.",
                                    category="security")
        assert "RBAC" in g.body
        assert g.category == "security"

    def test_to_dict(self):
        g = ImplementationGuidance(governing_principle_id="gkc_test:gp_test", name="authz")
        d = g.to_dict()
        assert d["node_type"] == GKFNodeType.IMPLEMENTATION_GUIDANCE.value
        assert d["name"] == "authz"


class TestGKFEvidence:
    def test_auto_id(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="test")
        assert e.evidence_id.startswith("gkc_test:ev_")

    def test_to_dict(self):
        e = GKFEvidence(collection_id="gkc_test", source_type="document", local_id="test")
        d = e.to_dict()
        assert d["node_type"] == GKFNodeType.EVIDENCE.value


class TestImplementationLink:
    def test_auto_id(self):
        il = ImplementationLink(governing_principle_id="gkc_test:gp_test", module_path="app.py")
        assert il.link_id.startswith("gkc_test:gp_test:impl_")

    def test_to_dict(self):
        il = ImplementationLink(governing_principle_id="gkc_test:gp_test", module_path="app.py",
                                 code_reference="class X", status="implemented")
        d = il.to_dict()
        assert d["node_type"] == GKFNodeType.IMPLEMENTATION_LINK.value


class TestAmendment:
    def test_auto_id(self):
        a = Amendment(target_id="gkc_test:art_1", number=1)
        assert a.amendment_id == "gkc_test:art_1:amd_1"

    def test_all_types(self):
        for at in AmendmentType:
            a = Amendment(target_id="gkc_test:art_1", number=1, amendment_type=at.value)
            assert a.amendment_type == at.value


class TestGKFVersion:
    def test_auto_id(self):
        v = GKFVersion(element_id="gkc_test:art_1", number=1)
        assert v.version_id == "gkc_test:art_1:v1"

    def test_with_content(self):
        v = GKFVersion(element_id="gkc_test:art_1", number=1, content={"body": "X"})
        assert v.content["body"] == "X"


class TestCrossModel:
    def test_gp_to_authority_link(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X",
                                 authority_id="gkc_test:auth_founder")
        a = Authority(collection_id="gkc_test", name="founder")
        assert gp.authority_id == a.authority_id

    def test_gp_to_commentary_chain(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X")
        c = Commentary(governing_principle_id=gp.governing_principle_id, number=1)
        assert gp.governing_principle_id in c.commentary_id

    def test_gp_to_example_chain(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X")
        e = Example(governing_principle_id=gp.governing_principle_id, number=1)
        assert gp.governing_principle_id in e.example_id

    def test_gp_to_guidance_chain(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X")
        g = ImplementationGuidance(governing_principle_id=gp.governing_principle_id, name="how")
        assert gp.governing_principle_id in g.guidance_id

    def test_citation_and_reference_separate(self):
        r = Reference(source_id="a", target_id="b")
        c = Citation(source_id="a", external_source="GDPR")
        assert r.reference_id != c.citation_id
        assert r.node_type != c.node_type


class TestEdgeCases:
    def test_empty_governing_principle_statement(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="")
        assert gp.statement == ""

    def test_authority_with_metadata(self):
        a = Authority(collection_id="gkc_test", name="founder", metadata={"established": "2026-01-01"})
        assert a.metadata["established"] == "2026-01-01"

    def test_commentary_non_binding(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="People first.")
        c = Commentary(governing_principle_id=gp.governing_principle_id, number=1,
                        body="This might mean...")
        assert c.body != gp.statement  # Commentary cannot override

    def test_example_never_governing(self):
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="Governing.")
        e = Example(governing_principle_id=gp.governing_principle_id, number=1, body="Illustration.")
        assert e.body != gp.statement
        assert not hasattr(e, "statement")

    def test_implementation_guidance_separate_from_link(self):
        link = ImplementationLink(governing_principle_id="gkc_test:gp_test", module_path="app.py")
        g = ImplementationGuidance(governing_principle_id="gkc_test:gp_test", name="how")
        assert link.link_id != g.guidance_id
        assert link.node_type != g.node_type

    def test_authority_type_default_empty(self):
        a = Authority(collection_id="gkc_test", name="custom")
        assert a.authority_type == ""

    def test_citation_default_fields(self):
        c = Citation(source_id="a", external_source="b")
        assert c.title == ""
        assert c.excerpt == ""

    def test_commentary_auto_timestamp(self):
        c = Commentary(governing_principle_id="gkc_test:gp_test", number=1)
        datetime.fromisoformat(c.established)

    def test_node_type_property_on_new_models(self):
        assert Authority(collection_id="gkc_test", name="founder").node_type == GKFNodeType.AUTHORITY.value
        assert Citation(source_id="a", external_source="b").node_type == GKFNodeType.CITATION.value
        assert Commentary(governing_principle_id="gkc_test:gp_test", number=1).node_type == GKFNodeType.COMMENTARY.value
        assert Example(governing_principle_id="gkc_test:gp_test", number=1).node_type == GKFNodeType.EXAMPLE.value
        guidance = ImplementationGuidance(governing_principle_id="gkc_test:gp_test", name="t")
        assert guidance.node_type == GKFNodeType.IMPLEMENTATION_GUIDANCE.value
        gp = GoverningPrinciple(collection_id="gkc_test", name="test", statement="X")
        assert gp.node_type == GKFNodeType.GOVERNING_PRINCIPLE.value