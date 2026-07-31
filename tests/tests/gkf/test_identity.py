"""Tests for GKF identity — GKF-001A enriched."""

import pytest
from app.gkf.identity import (
    generate_collection_id, generate_volume_id, generate_chapter_id,
    generate_article_id, generate_governing_principle_id,
    generate_interpretation_id, generate_authority_id,
    generate_citation_id, generate_commentary_id, generate_example_id,
    generate_implementation_guidance_id, generate_reference_id,
    generate_evidence_id, generate_implementation_link_id,
    generate_amendment_id, generate_version_id,
    parse_gkf_identity, is_valid_gkf_identity,
    is_governing_principle_identity, is_principle_identity_stable,
    sanitize_name,
)


class TestCollectionId:
    def test_basic(self):
        assert generate_collection_id("SHUNYA Constitution") == "gkc_shunya_constitution"


class TestGoverningPrincipleId:
    def test_stable_no_location(self):
        pid = generate_governing_principle_id("gkc_test", "human_first")
        assert "art_" not in pid
        assert "vol_" not in pid

    def test_format(self):
        pid = generate_governing_principle_id("gkc_test", "human_first")
        assert pid == "gkc_test:gp_human_first"

    def test_legacy_pr_prefix_parsed(self):
        parsed = parse_gkf_identity("gkc_test:pr_human_first")
        assert parsed["element_type"] == "gkf_governing_principle"


class TestAuthorityId:
    def test_basic(self):
        aid = generate_authority_id("gkc_test", "founder")
        assert aid == "gkc_test:auth_founder"


class TestCitationId:
    def test_format(self):
        cid = generate_citation_id("gkc_test:gp_test", "https://example.com/rule")
        assert cid.startswith("gkc_test:gp_test:cit_")


class TestCommentaryId:
    def test_basic(self):
        cid = generate_commentary_id("gkc_test:gp_test", 1)
        assert cid == "gkc_test:gp_test:com_1"


class TestExampleId:
    def test_basic(self):
        eid = generate_example_id("gkc_test:gp_test", 1)
        assert eid == "gkc_test:gp_test:ex_1"


class TestImplementationGuidanceId:
    def test_basic(self):
        gid = generate_implementation_guidance_id("gkc_test:gp_test", "authz_pattern")
        assert gid == "gkc_test:gp_test:guidance_authz_pattern"


class TestParseIdentity:
    def test_parse_authority(self):
        r = parse_gkf_identity("gkc_test:auth_founder")
        assert r["element_type"] == "gkf_authority"

    def test_parse_citation(self):
        r = parse_gkf_identity("gkc_test:gp_test:cit_abc123")
        assert r["element_type"] == "gkf_citation"

    def test_parse_commentary(self):
        r = parse_gkf_identity("gkc_test:gp_test:com_1")
        assert r["element_type"] == "gkf_commentary"

    def test_parse_example(self):
        r = parse_gkf_identity("gkc_test:gp_test:ex_1")
        assert r["element_type"] == "gkf_example"

    def test_parse_guidance(self):
        r = parse_gkf_identity("gkc_test:gp_test:guidance_authz")
        assert r["element_type"] == "gkf_implementation_guidance"

    def test_parse_governing_principle(self):
        r = parse_gkf_identity("gkc_test:gp_human_first")
        assert r["element_type"] == "gkf_governing_principle"
        assert r["local_id"] == "human_first"


class TestValidation:
    def test_is_governing_principle(self):
        assert is_governing_principle_identity("gkc_test:gp_human_first")

    def test_not_governing_principle(self):
        assert not is_governing_principle_identity("gkc_test:art_1")

    def test_principle_stability(self):
        assert is_principle_identity_stable("gkc_test:gp_human_first")

    def test_principle_not_stable_for_article(self):
        assert not is_principle_identity_stable("gkc_test:art_1")


class TestSanitization:
    def test_lowercase(self):
        assert sanitize_name("HELLO") == "hello"