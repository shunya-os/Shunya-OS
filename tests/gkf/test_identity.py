"""Tests for GKF identity generation, parsing, and validation."""

import pytest
from app.gkf.identity import (
    generate_collection_id,
    generate_volume_id,
    generate_chapter_id,
    generate_article_id,
    generate_principle_id,
    generate_interpretation_id,
    generate_reference_id,
    generate_evidence_id,
    generate_implementation_link_id,
    generate_amendment_id,
    generate_version_id,
    parse_gkf_identity,
    is_valid_gkf_identity,
    is_principle_identity,
    is_principle_identity_stable,
    sanitize_name,
)


# =========================================================================
# Generation Tests
# =========================================================================

class TestCollectionIdentity:
    def test_basic(self):
        assert generate_collection_id("SHUNYA Constitution") == "gkc_shunya_constitution"

    def test_simple_name(self):
        assert generate_collection_id("GDPR") == "gkc_gdpr"

    def test_name_with_spaces(self):
        assert generate_collection_id("My Collection") == "gkc_my_collection"


class TestVolumeIdentity:
    def test_basic(self):
        assert generate_volume_id("gkc_shunya_constitution", 1) == "gkc_shunya_constitution:vol_1"

    def test_multiple_volumes(self):
        assert generate_volume_id("gkc_test", 2) == "gkc_test:vol_2"


class TestChapterIdentity:
    def test_basic(self):
        cid = generate_chapter_id("gkc_test:vol_1", 1)
        assert cid == "gkc_test:vol_1:ch_1"


class TestArticleIdentity:
    def test_basic(self):
        assert generate_article_id("gkc_shunya_constitution", 1) == "gkc_shunya_constitution:art_1"

    def test_article_10(self):
        assert generate_article_id("gkc_shunya_constitution", 10) == "gkc_shunya_constitution:art_10"


class TestPrincipleIdentity:
    """Principle identities are STABLE — they do NOT encode document location."""

    def test_principle_does_not_contain_article_number(self):
        pid = generate_principle_id("gkc_shunya_constitution", "human_first")
        assert "art_" not in pid
        assert "vol_" not in pid
        assert "ch_" not in pid

    def test_principle_format(self):
        pid = generate_principle_id("gkc_shunya_constitution", "human_first")
        assert pid == "gkc_shunya_constitution:pr_human_first"
        assert is_principle_identity(pid)
        assert is_principle_identity_stable(pid)

    def test_principle_name_with_spaces(self):
        pid = generate_principle_id("gkc_test", "privacy by design")
        assert pid == "gkc_test:pr_privacy_by_design"

    def test_principle_name_with_numbers(self):
        pid = generate_principle_id("gkc_test", "rule_42")
        assert pid == "gkc_test:pr_rule_42"


class TestInterpretationIdentity:
    def test_basic(self):
        iid = generate_interpretation_id("gkc_test:pr_human_first", 1)
        assert iid == "gkc_test:pr_human_first:int_1"

    def test_multiple_interpretations(self):
        iid = generate_interpretation_id("gkc_test:pr_agency", 3)
        assert iid == "gkc_test:pr_agency:int_3"


class TestReferenceIdentity:
    def test_basic(self):
        rid = generate_reference_id("gkc_test:art_1", "gkc_test:art_2")
        assert rid.startswith("gkc_test:art_1:ref_")
        assert len(rid) > len("gkc_test:art_1:ref_")


class TestEvidenceIdentity:
    def test_founder_directive(self):
        eid = generate_evidence_id("gkc_shunya_constitution", "founder_directive", "genesis")
        assert eid == "gkc_shunya_constitution:ev_founder_directive_genesis"

    def test_document_source(self):
        eid = generate_evidence_id("gkc_shunya_constitution", "document", "constitution")
        assert eid == "gkc_shunya_constitution:ev_document_constitution"


class TestImplementationLinkIdentity:
    def test_basic(self):
        lid = generate_implementation_link_id("gkc_test:pr_human_first", "app/kernel/object.py")
        assert lid.startswith("gkc_test:pr_human_first:impl_")


class TestAmendmentIdentity:
    def test_basic(self):
        aid = generate_amendment_id("gkc_test:art_1", 1)
        assert aid == "gkc_test:art_1:amd_1"


class TestVersionIdentity:
    def test_basic(self):
        vid = generate_version_id("gkc_test:art_1", 1)
        assert vid == "gkc_test:art_1:v1"

    def test_version_3(self):
        vid = generate_version_id("gkc_test:pr_human_first", 3)
        assert vid == "gkc_test:pr_human_first:v3"


# =========================================================================
# Parsing Tests
# =========================================================================

class TestParseIdentity:
    def test_parse_collection(self):
        result = parse_gkf_identity("gkc_shunya_constitution")
        assert result["element_type"] == "gkf_collection"
        assert result["collection_id"] == "gkc_shunya_constitution"

    def test_parse_article(self):
        result = parse_gkf_identity("gkc_shunya_constitution:art_1")
        assert result["element_type"] == "gkf_article"
        assert result["collection_id"] == "gkc_shunya_constitution"
        assert "local_id" in result

    def test_parse_principle(self):
        result = parse_gkf_identity("gkc_shunya_constitution:pr_human_first")
        assert result["element_type"] == "gkf_principle"
        assert result["collection_id"] == "gkc_shunya_constitution"
        assert result["local_id"] == "human_first"

    def test_parse_volume(self):
        result = parse_gkf_identity("gkc_shunya_constitution:vol_1")
        assert result["element_type"] == "gkf_volume"
        assert result["volume_id"] == "vol_1"

    def test_parse_version(self):
        result = parse_gkf_identity("gkc_shunya_constitution:art_1:v1")
        assert result["element_type"] == "gkf_version"
        assert "element_id" in result

    def test_parse_amendment(self):
        result = parse_gkf_identity("gkc_test:art_1:amd_1")
        assert result["element_type"] == "gkf_amendment"

    def test_parse_evidence(self):
        result = parse_gkf_identity("gkc_test:ev_constitution")
        assert result["element_type"] == "gkf_evidence"

    def test_parse_empty_raises(self):
        with pytest.raises(ValueError):
            parse_gkf_identity("")

    def test_parse_invalid_prefix_raises(self):
        with pytest.raises(ValueError):
            parse_gkf_identity("invalid_prefix")


# =========================================================================
# Validation Tests
# =========================================================================

class TestIdentityValidation:
    def test_valid_identity(self):
        assert is_valid_gkf_identity("gkc_shunya_constitution:art_1")

    def test_invalid_identity(self):
        assert not is_valid_gkf_identity("not_a_gkf_id")

    def test_empty_identity(self):
        assert not is_valid_gkf_identity("")

    def test_principle_identity_check(self):
        assert is_principle_identity("gkc_test:pr_human_first")
        assert not is_principle_identity("gkc_test:art_1")
        assert not is_principle_identity("gkc_test:vol_1")

    def test_principle_stability_all_pass(self):
        """Real principle identities from the architecture."""
        assert is_principle_identity_stable("gkc_shunya_constitution:pr_human_first")
        assert is_principle_identity_stable("gkc_shunya_constitution:pr_agency")
        assert is_principle_identity_stable("gkc_shunya_constitution:pr_permission")
        assert is_principle_identity_stable("gkc_shunya_constitution:pr_calm")

    def test_non_principle_not_stable(self):
        assert not is_principle_identity_stable("gkc_test:art_1")


# =========================================================================
# Sanitization Tests
# =========================================================================

class TestSanitization:
    def test_lowercase(self):
        assert sanitize_name("HELLO") == "hello"

    def test_spaces_to_underscores(self):
        assert sanitize_name("Hello World") == "hello_world"

    def test_hyphens_to_underscores(self):
        assert sanitize_name("my-name") == "my_name"

    def test_already_clean(self):
        assert sanitize_name("clean") == "clean"

    def test_mixed(self):
        assert sanitize_name("The SHUNYA OS") == "the_shunya_os"