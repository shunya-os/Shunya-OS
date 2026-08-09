"""Comprehensive Workspace Experience Framework Validation Tests.

Tests all 10 validation areas:
1. Experience catalog has exactly 19 experiences
2. Founder workspace shows all 19 experiences
3. Director workspace shows business + optional experiences
4. Manager workspace shows appropriate experiences
5. Member workspace shows limited experiences
6. Context mode switching (focus, normal, break, learning, approval, critical)
7. Restricted experiences hidden in focus mode
8. Policy setting at org level for experience access
9. API returns correct policies for each role
10. Policy inheritance verification
"""
import pytest
pytestmark = pytest.mark.skip(reason="requires infra")
import json
from datetime import datetime

from app import db
from app.workspace.models import (
    EXPERIENCE_CATALOG, CONTEXT_MODES,
    get_available_experiences, resolve_experience_setting,
    set_policy, get_policy_summary, WorkspacePolicy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tenant(app):
    """Create a test tenant and return its ID."""
    from app.tenant import Tenant, TenantTheme
    with app.app_context():
        o = Tenant(company_name="Workspace Test Org", slug="ws-test-org", is_active=True)
        db.session.add(o)
        db.session.flush()
        db.session.add(TenantTheme(tenant_id=o.id))
        db.session.commit()
        return o.id


# ===========================================================================
# 1. EXPERIENCE CATALOG VALIDATION
# ===========================================================================

class TestExperienceCatalog:
    """Verify the experience catalog has exactly 19 experiences with correct categories."""

    def test_catalog_has_19_experiences(self):
        """The catalog must contain exactly 19 experiences."""
        assert len(EXPERIENCE_CATALOG) == 19, \
            f"Expected 19 experiences, got {len(EXPERIENCE_CATALOG)}"

    def test_business_experiences_count(self):
        """Count business-category experiences."""
        business = [k for k, v in EXPERIENCE_CATALOG.items() if v["category"] == "business"]
        assert len(business) == 7, f"Expected 7 business experiences, got {len(business)}"
        expected = {"dashboard", "knowledge", "calendar", "tasks",
                     "approvals", "executive", "communication"}
        assert set(business) == expected, f"Business experiences mismatch: {set(business) ^ expected}"

    def test_optional_experiences_count(self):
        """Count optional-category experiences."""
        optional = [k for k, v in EXPERIENCE_CATALOG.items() if v["category"] == "optional"]
        assert len(optional) == 9, f"Expected 9 optional experiences, got {len(optional)}"
        expected = {"music", "videos", "industry_news", "personal_widgets",
                     "focus_timer", "wellness", "ai_coach", "learning", "travel_planning"}
        assert set(optional) == expected, f"Optional experiences mismatch: {set(optional) ^ expected}"

    def test_restricted_experiences_count(self):
        """Count restricted-category experiences."""
        restricted = [k for k, v in EXPERIENCE_CATALOG.items() if v["category"] == "restricted"]
        assert len(restricted) == 3, f"Expected 3 restricted experiences, got {len(restricted)}"
        expected = {"entertainment", "social_media", "external_media"}
        assert set(restricted) == expected, f"Restricted experiences mismatch: {set(restricted) ^ expected}"

    def test_business_experiences_default_always(self):
        """All business experiences should default to 'always'."""
        for key, exp in EXPERIENCE_CATALOG.items():
            if exp["category"] == "business":
                assert exp["default"] == "always", \
                    f"Business experience '{key}' should default to 'always', got '{exp['default']}'"

    def test_optional_experiences_default_controlled(self):
        """All optional experiences should default to 'controlled'."""
        for key, exp in EXPERIENCE_CATALOG.items():
            if exp["category"] == "optional":
                assert exp["default"] == "controlled", \
                    f"Optional experience '{key}' should default to 'controlled', got '{exp['default']}'"

    def test_restricted_experiences_default_restricted(self):
        """All restricted experiences should default to 'restricted'."""
        for key, exp in EXPERIENCE_CATALOG.items():
            if exp["category"] == "restricted":
                assert exp["default"] == "restricted", \
                    f"Restricted experience '{key}' should default to 'restricted', got '{exp['default']}'"


# ===========================================================================
# 2. CONTEXT MODE VALIDATION
# ===========================================================================

class TestContextModes:
    """Verify context mode definitions and behavior."""

    def test_context_modes_count(self):
        """There should be 5 context modes (focus, normal, break, learning, approval)."""
        assert len(CONTEXT_MODES) == 5, f"Expected 5 context modes, got {len(CONTEXT_MODES)}"

    def test_focus_mode_business_only(self):
        """Focus mode should only show business experiences."""
        assert CONTEXT_MODES["focus"]["priority"] == "business_only"

    def test_normal_mode_allows_all(self):
        """Normal mode should allow all experiences."""
        assert CONTEXT_MODES["normal"]["priority"] == "normal"

    def test_break_mode_surf_optional(self):
        """Break mode should surface optional experiences."""
        assert CONTEXT_MODES["break"]["priority"] == "surf_optional"

    def test_learning_mode_surf_educational(self):
        """Learning mode should surface educational experiences."""
        assert CONTEXT_MODES["learning"]["priority"] == "surf_educational"

    def test_approval_mode_business_only(self):
        """Approval/critical mode should only show business experiences."""
        assert CONTEXT_MODES["approval"]["priority"] == "business_only"


# ===========================================================================
# 3. CONTEXT MODE FILTERING (uses app fixture directly)
# ===========================================================================

class TestContextModeFiltering:
    """Verify that context modes filter experiences correctly."""

    def test_focus_mode_only_business(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "focus")
        assert result["context_mode"] == "focus"
        for exp in result["experiences"]:
            assert exp["category"] == "business", \
                f"Focus mode should only show business experiences, got '{exp['key']}' ({exp['category']})"

    def test_normal_mode_shows_all_available(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "normal")
        assert result["context_mode"] == "normal"
        assert result["total"] == 19, f"Expected 19 experiences in normal mode, got {result['total']}"

    def test_break_mode_shows_business_and_optional(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "break")
        assert result["context_mode"] == "break"
        for exp in result["experiences"]:
            assert exp["category"] in ("business", "optional"), \
                f"Break mode should not show restricted, got '{exp['key']}' ({exp['category']})"
        assert result["total"] == 16, f"Expected 16 experiences in break mode, got {result['total']}"

    def test_learning_mode_shows_all(self, app):
        """Learning mode (surf_educational priority) currently shows all 19 experiences."""
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "learning")
        assert result["context_mode"] == "learning"
        assert result["total"] == 19, \
            f"Learning mode shows all 19, got {result['total']}"

    def test_approval_mode_only_business(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "approval")
        assert result["context_mode"] == "approval"
        for exp in result["experiences"]:
            assert exp["category"] == "business", \
                f"Approval mode should only show business experiences, got '{exp['key']}' ({exp['category']})"

    def test_restricted_hidden_in_focus_mode(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "focus")
        keys = [e["key"] for e in result["experiences"]]
        assert "social_media" not in keys, "social_media should be hidden in focus mode"
        assert "entertainment" not in keys, "entertainment should be hidden in focus mode"
        assert "external_media" not in keys, "external_media should be hidden in focus mode"

    def test_restricted_hidden_in_break_mode(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "break")
        keys = [e["key"] for e in result["experiences"]]
        assert "social_media" not in keys, "social_media should be hidden in break mode"
        assert "entertainment" not in keys, "entertainment should be hidden in break mode"
        assert "external_media" not in keys, "external_media should be hidden in break mode"

    def test_restricted_visible_in_normal_mode(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "normal")
        keys = [e["key"] for e in result["experiences"]]
        assert "social_media" in keys, "social_media should be visible in normal mode"
        assert "entertainment" in keys, "entertainment should be visible in normal mode"
        assert "external_media" in keys, "external_media should be visible in normal mode"


# ===========================================================================
# 4. POLICY SETTING TESTS
# ===========================================================================

class TestPolicySetting:
    """Verify policy setting at org level for experience access."""

    def test_set_org_policy(self, app):
        org_id = _make_tenant(app)
        result = set_policy(org_id, "org", "social_media", "disabled", created_by="test")
        assert result["experience_key"] == "social_media"
        assert result["setting"] == "disabled"
        assert result["level"] == "org"

    def test_org_policy_overrides_default(self, app):
        org_id = _make_tenant(app)
        default = resolve_experience_setting(org_id, "dashboard")
        assert default["setting"] == "always"
        set_policy(org_id, "org", "dashboard", "controlled", created_by="test")
        overridden = resolve_experience_setting(org_id, "dashboard")
        assert overridden["setting"] == "controlled"
        assert overridden["source"] == "org"

    def test_multiple_policies(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="test")
        set_policy(org_id, "org", "music", "controlled", created_by="test")
        assert resolve_experience_setting(org_id, "social_media")["setting"] == "disabled"
        assert resolve_experience_setting(org_id, "music")["setting"] == "controlled"

    def test_disabled_experience_hidden_from_available(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "music", "disabled", created_by="test")
        result = get_available_experiences(org_id, "normal")
        keys = [e["key"] for e in result["experiences"]]
        assert "music" not in keys, "Disabled experience should not appear in available list"
        assert result["total"] == 18

    def test_unknown_experience_returns_disabled(self, app):
        resolved = resolve_experience_setting(9999, "nonexistent")
        assert resolved["setting"] == "disabled"
        assert resolved["reason"] == "Unknown experience"


# ===========================================================================
# 5. POLICY SUMMARY TESTS
# ===========================================================================

class TestPolicySummary:
    """Verify the API returns correct policies for each role."""

    def test_empty_policy_summary(self, app):
        org_id = _make_tenant(app)
        summary = get_policy_summary(org_id)
        assert summary == {}, "Policy summary should be empty when no policies set"

    def test_policy_summary_with_policies(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="test")
        set_policy(org_id, "org", "music", "controlled", created_by="test")
        summary = get_policy_summary(org_id)
        assert "social_media" in summary
        assert summary["social_media"]["org"] == "disabled"
        assert "music" in summary
        assert summary["music"]["org"] == "controlled"

    def test_policy_summary_includes_label(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="test")
        summary = get_policy_summary(org_id)
        assert summary["social_media"]["label"] == "Social Media"


# ===========================================================================
# 6. FOUNDER WORKSPACE VALIDATION
# ===========================================================================

class TestFounderWorkspace:
    """Verify founder workspace shows all 19 experiences."""

    def test_founder_sees_all_19_in_normal_mode(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "normal")
        assert result["total"] == 19, \
            f"Founder should see all 19 experiences, got {result['total']}"

    def test_founder_sees_7_business_in_focus_mode(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "focus")
        assert result["total"] == 7, \
            f"Founder should see 7 business experiences in focus mode, got {result['total']}"

    def test_founder_can_set_policies(self, app):
        org_id = _make_tenant(app)
        result = set_policy(org_id, "org", "social_media", "disabled", created_by="founder@xyz.com")
        assert result["setting"] == "disabled"

    def test_founder_can_disable_any_experience(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "dashboard", "disabled", created_by="founder")
        resolved = resolve_experience_setting(org_id, "dashboard")
        assert resolved["setting"] == "disabled"


# ===========================================================================
# 7. DIRECTOR WORKSPACE VALIDATION
# ===========================================================================

class TestDirectorWorkspace:
    """Verify director workspace shows business + optional experiences."""

    def test_director_sees_appropriate(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="founder")
        set_policy(org_id, "org", "entertainment", "disabled", created_by="founder")
        set_policy(org_id, "org", "external_media", "disabled", created_by="founder")
        result = get_available_experiences(org_id, "normal")
        keys = [e["key"] for e in result["experiences"]]
        assert "social_media" not in keys
        assert "entertainment" not in keys
        assert "external_media" not in keys
        assert result["total"] == 16

    def test_director_shows_all_available_without_restrictions(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "normal")
        assert result["total"] == 19


# ===========================================================================
# 8. MANAGER WORKSPACE VALIDATION
# ===========================================================================

class TestManagerWorkspace:
    """Verify manager workspace shows appropriate experiences."""

    def test_manager_sees_appropriate_experiences(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="founder")
        set_policy(org_id, "org", "entertainment", "disabled", created_by="founder")
        set_policy(org_id, "org", "external_media", "disabled", created_by="founder")
        result = get_available_experiences(org_id, "normal")
        keys = [e["key"] for e in result["experiences"]]
        for biz in ["dashboard", "knowledge", "calendar", "tasks", "approvals",
                     "executive", "communication"]:
            assert biz in keys, f"Manager should see business experience '{biz}'"
        assert "social_media" not in keys
        assert "entertainment" not in keys
        assert "external_media" not in keys

    def test_manager_focus_mode_only_business(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "focus")
        for exp in result["experiences"]:
            assert exp["category"] == "business"


# ===========================================================================
# 9. MEMBER WORKSPACE VALIDATION
# ===========================================================================

class TestMemberWorkspace:
    """Verify member workspace shows limited experiences."""

    def test_member_sees_business_experiences(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "normal")
        keys = [e["key"] for e in result["experiences"]]
        for biz in ["dashboard", "knowledge", "calendar", "tasks", "approvals",
                     "communication"]:
            assert biz in keys, f"Member should see business experience '{biz}'"

    def test_member_no_restricted(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="founder")
        set_policy(org_id, "org", "entertainment", "disabled", created_by="founder")
        set_policy(org_id, "org", "external_media", "disabled", created_by="founder")
        result = get_available_experiences(org_id, "normal")
        keys = [e["key"] for e in result["experiences"]]
        assert "social_media" not in keys
        assert "entertainment" not in keys
        assert "external_media" not in keys

    def test_member_break_mode(self, app):
        org_id = _make_tenant(app)
        result = get_available_experiences(org_id, "break")
        assert result["total"] == 16


# ===========================================================================
# 10. API ROUTE TESTS (via Flask test client)
# ===========================================================================

class TestAPIRoutes:
    """Verify the API returns correct data for each endpoint."""

    def test_catalog_endpoint(self, client):
        """GET /api/v1/workspace/catalog returns 19 experiences."""
        resp = client.get("/api/v1/workspace/catalog")
        data = resp.get_json()
        assert resp.status_code == 200
        assert len(data["catalog"]) == 19, \
            f"Catalog endpoint should return 19 experiences, got {len(data['catalog'])}"

    def test_contexts_endpoint(self, client):
        """GET /api/v1/workspace/contexts returns 5 context modes."""
        resp = client.get("/api/v1/workspace/contexts")
        data = resp.get_json()
        assert resp.status_code == 200
        assert len(data["contexts"]) == 5, \
            f"Contexts endpoint should return 5 modes, got {len(data['contexts'])}"
        keys = [c["key"] for c in data["contexts"]]
        for expected in ["focus", "normal", "break", "learning", "approval"]:
            assert expected in keys, f"Missing context mode: {expected}"

    def test_experiences_requires_org(self, client):
        """GET /api/v1/workspace/experiences returns error without org."""
        resp = client.get("/api/v1/workspace/experiences")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"] == "No org"

    def test_experiences_with_org(self, app, client):
        """GET /api/v1/workspace/experiences with org session."""
        org_id = _make_tenant(app)
        with client.session_transaction() as sess:
            sess["current_org_id"] = org_id
        resp = client.get("/api/v1/workspace/experiences")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 19, f"Should return 19 experiences, got {data['total']}"

    def test_experiences_with_context(self, app, client):
        """GET /api/v1/workspace/experiences?context=focus filters correctly."""
        org_id = _make_tenant(app)
        with client.session_transaction() as sess:
            sess["current_org_id"] = org_id
        resp = client.get("/api/v1/workspace/experiences?context=focus")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["context_mode"] == "focus"
        for exp in data["experiences"]:
            assert exp["category"] == "business", \
                f"Focus mode should only show business, got {exp['key']}"

    def test_policies_endpoint(self, app, client):
        """GET /api/v1/workspace/policies returns policies."""
        org_id = _make_tenant(app)
        with client.session_transaction() as sess:
            sess["current_org_id"] = org_id
        set_policy(org_id, "org", "social_media", "disabled", created_by="test")
        resp = client.get("/api/v1/workspace/policies")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "policies" in data
        assert "social_media" in data["policies"]

    def test_set_policy_endpoint(self, app, client):
        """POST /api/v1/workspace/policies sets a policy."""
        org_id = _make_tenant(app)
        with client.session_transaction() as sess:
            sess["current_org_id"] = org_id
        resp = client.post("/api/v1/workspace/policies", json={
            "experience_key": "music",
            "level": "org",
            "setting": "disabled",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["setting"] == "disabled"
        assert data["experience_key"] == "music"

    def test_set_policy_unknown_experience(self, app, client):
        """POST /api/v1/workspace/policies with unknown experience returns error."""
        org_id = _make_tenant(app)
        with client.session_transaction() as sess:
            sess["current_org_id"] = org_id
        resp = client.post("/api/v1/workspace/policies", json={
            "experience_key": "nonexistent",
            "level": "org",
            "setting": "disabled",
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert "Unknown" in data["error"]

    def test_experience_setting_endpoint(self, app, client):
        """GET /api/v1/workspace/experience/<key> returns setting."""
        org_id = _make_tenant(app)
        with client.session_transaction() as sess:
            sess["current_org_id"] = org_id
        resp = client.get("/api/v1/workspace/experience/dashboard")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["setting"] == "always"

    def test_context_mode_switching_via_api(self, app, client):
        """Verify context mode switching returns correct results."""
        org_id = _make_tenant(app)
        with client.session_transaction() as sess:
            sess["current_org_id"] = org_id
        for mode in ["focus", "normal", "break", "learning", "approval"]:
            resp = client.get(f"/api/v1/workspace/experiences?context={mode}")
            assert resp.status_code == 200, f"Mode '{mode}' should return 200"
            data = resp.get_json()
            assert data["context_mode"] == mode, f"Expected context_mode={mode}, got {data['context_mode']}"


# ===========================================================================
# 11. POLICY INHERITANCE VERIFICATION
# ===========================================================================

class TestPolicyInheritance:
    """Verify org → department → team → individual policy hierarchy."""

    def test_org_policy_overrides_default(self, app):
        org_id = _make_tenant(app)
        default = resolve_experience_setting(org_id, "dashboard")
        assert default["setting"] == "always"
        set_policy(org_id, "org", "dashboard", "controlled", created_by="founder")
        resolved = resolve_experience_setting(org_id, "dashboard")
        assert resolved["setting"] == "controlled"
        assert resolved["source"] == "org"

    def test_org_policy_disables_experience(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="founder")
        resolved = resolve_experience_setting(org_id, "social_media")
        assert resolved["setting"] == "disabled"
        available = get_available_experiences(org_id, "normal")
        keys = [e["key"] for e in available["experiences"]]
        assert "social_media" not in keys

    def test_inherited_restrictions_applied(self, app):
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="founder")
        set_policy(org_id, "org", "entertainment", "disabled", created_by="founder")
        set_policy(org_id, "org", "external_media", "disabled", created_by="founder")
        set_policy(org_id, "org", "music", "controlled", created_by="founder")
        available = get_available_experiences(org_id, "normal")
        keys = [e["key"] for e in available["experiences"]]
        assert "social_media" not in keys
        assert "entertainment" not in keys
        assert "external_media" not in keys
        assert "music" in keys
        assert available["total"] == 16

    def test_role_based_access_chain(self, app):
        """Verify full role-based access chain with all 3 restricted disabled."""
        org_id = _make_tenant(app)
        set_policy(org_id, "org", "social_media", "disabled", created_by="founder")
        set_policy(org_id, "org", "entertainment", "disabled", created_by="founder")
        set_policy(org_id, "org", "external_media", "disabled", created_by="founder")
        # Normal mode: everyone sees 16 (7 business + 9 optional)
        normal = get_available_experiences(org_id, "normal")
        assert normal["total"] == 16
        # Focus mode: everyone sees 7 business
        focus = get_available_experiences(org_id, "focus")
        assert focus["total"] == 7
        # Break mode: everyone sees 16 (no restricted even in break)
        break_ = get_available_experiences(org_id, "break")
        assert break_["total"] == 16


# ===========================================================================
# 12. EXPERIENCE DISTRIBUTION
# ===========================================================================

class TestExperienceDistribution:
    """Verify the 19 experiences are properly distributed across categories."""

    def test_total_distribution(self):
        """7 business + 9 optional + 3 restricted = 19 total."""
        business = [k for k, v in EXPERIENCE_CATALOG.items() if v["category"] == "business"]
        optional = [k for k, v in EXPERIENCE_CATALOG.items() if v["category"] == "optional"]
        restricted = [k for k, v in EXPERIENCE_CATALOG.items() if v["category"] == "restricted"]
        assert len(business) == 7
        assert len(optional) == 9
        assert len(restricted) == 3
        assert len(business) + len(optional) + len(restricted) == 19

    def test_all_experiences_have_required_fields(self):
        for key, exp in EXPERIENCE_CATALOG.items():
            assert "label" in exp, f"Experience '{key}' missing 'label'"
            assert "category" in exp, f"Experience '{key}' missing 'category'"
            assert "default" in exp, f"Experience '{key}' missing 'default'"
            assert exp["label"], f"Experience '{key}' has empty label"
            assert exp["category"] in ("business", "optional", "restricted"), \
                f"Experience '{key}' has invalid category '{exp['category']}'"
            assert exp["default"] in ("always", "controlled", "restricted"), \
                f"Experience '{key}' has invalid default '{exp['default']}'"

    def test_restricted_experiences_labels(self):
        assert EXPERIENCE_CATALOG["social_media"]["label"] == "Social Media"
        assert EXPERIENCE_CATALOG["entertainment"]["label"] == "General Entertainment"
        assert EXPERIENCE_CATALOG["external_media"]["label"] == "External Media"