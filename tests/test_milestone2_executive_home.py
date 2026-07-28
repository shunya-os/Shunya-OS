"""E2E Tests for Milestone 2 — Executive Home.

Tests the complete Executive Home surface:
  Morning Brief, Recommendations, Business Health,
  Recent Activity, Continue Working — all from real state.

Uses the canonical Flask app fixture from conftest.py.
"""

from __future__ import annotations

from app.founder.executive_home_service import (
    build_business_health,
    build_continue_working,
    build_executive_home,
    build_morning_brief,
    build_recent_activity,
    build_recommendations,
)
from core.os import reset_os


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_identity(app):
    """Sign in to create an OS identity and return the identity_id."""
    from app import db
    from app.adapters.os_adapter import sign_in
    result = sign_in(email="nishesh@shunyaos.com", name="Nishesh")
    assert result["success"], f"Sign in failed: {result}"
    return result["identity_id"]


def _seed_test_data(app, identity_id: str) -> None:
    """Seed test data into DB models for Executive Home testing."""
    from app import db
    from app.founder.models import (
        FounderConversation,
        FounderMessage,
        FounderObject,
        FounderSpace,
    )

    space1 = FounderSpace(
        space_id="test_spc_001", name="My Business",
        space_type="organization", identity_id=identity_id,
    )
    space2 = FounderSpace(
        space_id="test_spc_002", name="Side Project",
        space_type="project", identity_id=identity_id,
    )
    db.session.add_all([space1, space2])
    db.session.flush()

    obj1 = FounderObject(
        object_id="test_obj_001", space_id="test_spc_001",
        name="Business Plan", object_type="Document",
        content="Our business plan for 2026.", created_by=identity_id,
    )
    obj2 = FounderObject(
        object_id="test_obj_002", space_id="test_spc_001",
        name="Customer List", object_type="Spreadsheet",
        content="All active customers.", created_by=identity_id,
    )
    obj3 = FounderObject(
        object_id="test_obj_003", space_id="test_spc_002",
        name="App Design", object_type="Design",
        content="Figma mockups for v2.", created_by=identity_id,
    )
    db.session.add_all([obj1, obj2, obj3])
    db.session.flush()

    conv = FounderConversation(
        conv_id="test_conv_001", object_id="test_obj_001",
        title="About Business Plan", identity_id=identity_id,
    )
    db.session.add(conv)
    db.session.flush()

    msg1 = FounderMessage(conv_id="test_conv_001", role="human",
                          content="Can you review this business plan?")
    msg2 = FounderMessage(conv_id="test_conv_001", role="assistant",
                          content="I've reviewed it. The financial projections look solid.")
    msg3 = FounderMessage(conv_id="test_conv_001", role="human",
                          content="What about the marketing section?")
    db.session.add_all([msg1, msg2, msg3])
    db.session.commit()


# ---------------------------------------------------------------------------
# Tests: Morning Brief
# ---------------------------------------------------------------------------


class TestMorningBrief:
    """Morning Brief generation from real runtime state."""

    def test_empty_state_returns_quiet_brief(self, app):
        """Founder with no activity gets a quiet morning brief."""
        identity_id = _make_identity(app)
        brief = build_morning_brief(identity_id=identity_id)
        assert isinstance(brief, dict)
        assert "items" in brief
        assert "summary" in brief
        assert brief["summary"]["active_spaces"] == 0
        assert brief["summary"]["active_objects"] == 0
        assert brief["summary"]["pending_conversations"] == 0
        assert len(brief["items"]) >= 1
        for item in brief["items"]:
            assert "title" in item
            assert "priority" in item
            assert "focus" in item

    def test_with_data_shows_recent_activity(self, app):
        """Brief includes recently created and updated objects."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        brief = build_morning_brief(identity_id=identity_id)
        assert brief["summary"]["active_spaces"] == 2
        assert brief["summary"]["active_objects"] >= 3
        assert brief["summary"]["pending_conversations"] >= 1
        assert len(brief["items"]) >= 1
        conv_items = [i for i in brief["items"] if "Conversation" in i.get("title", "")]
        assert len(conv_items) >= 1
        assert conv_items[0]["focus"] is not None
        assert conv_items[0]["focus"].get("object_id") == "test_obj_001"

    def test_multiple_spaces_aggregated(self, app):
        """Brief aggregates data across all spaces."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        brief = build_morning_brief(identity_id=identity_id)
        assert brief["summary"]["active_spaces"] == 2

    def test_all_items_have_required_fields(self, app):
        """Every brief item has title, priority, focus."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        brief = build_morning_brief(identity_id=identity_id)
        for item in brief["items"]:
            assert "title" in item, f"Item missing title: {item}"
            assert "priority" in item, f"Item missing priority: {item}"
            assert item["priority"] in ("info", "attention", "warning"), \
                f"Unknown priority: {item['priority']}"
            assert "focus" in item, f"Item missing focus: {item}"

    def test_items_limited_to_max_eight(self, app):
        """Brief caps at 8 items."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        brief = build_morning_brief(identity_id=identity_id)
        assert len(brief["items"]) <= 8


# ---------------------------------------------------------------------------
# Tests: Recommendations
# ---------------------------------------------------------------------------


class TestRecommendations:
    """SHUNYA Recommendations from current business state."""

    def test_empty_state_recommends_first_space(self, app):
        """Founder with nothing gets a recommendation to create a space."""
        identity_id = _make_identity(app)
        recs = build_recommendations(identity_id=identity_id)
        assert isinstance(recs, list)
        assert len(recs) >= 1
        first = recs[0]
        assert "title" in first
        assert "explanation" in first
        assert "why" in first
        assert "priority" in first
        assert "originating_runtime" in first
        assert "action" in first
        assert first["action"]["type"] == "navigate"

    def test_new_space_recommends_first_object(self, app):
        """Space with no objects recommends creating one."""
        from app import db
        from app.founder.models import FounderSpace
        identity_id = _make_identity(app)
        space = FounderSpace(
            space_id="spc_empty", name="Empty Space",
            space_type="organization", identity_id=identity_id,
        )
        db.session.add(space)
        db.session.commit()
        recs = build_recommendations(identity_id=identity_id)
        assert len(recs) >= 1
        assert "object" in recs[0]["title"].lower()

    def test_recommendations_are_explainable(self, app):
        """Every recommendation has explanation and reasoning."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        recs = build_recommendations(identity_id=identity_id)
        for rec in recs:
            assert rec.get("explanation"), f"Missing explanation: {rec['title']}"
            assert rec.get("why"), f"Missing why: {rec['title']}"

    def test_recommendations_are_actionable(self, app):
        """Every recommendation has an action."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        recs = build_recommendations(identity_id=identity_id)
        for rec in recs:
            assert "action" in rec, f"Missing action: {rec['title']}"
            assert "type" in rec["action"]
            assert "label" in rec["action"]

    def test_recommendations_have_originating_runtime(self, app):
        """Every recommendation traces to an originating runtime."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        recs = build_recommendations(identity_id=identity_id)
        for rec in recs:
            assert rec.get("originating_runtime"), f"Missing runtime: {rec['title']}"

    def test_recommendations_capped_at_five(self, app):
        """Max 5 recommendations returned."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        recs = build_recommendations(identity_id=identity_id)
        assert len(recs) <= 5


# ---------------------------------------------------------------------------
# Tests: Business Health
# ---------------------------------------------------------------------------


class TestBusinessHealth:
    """Business Health from runtime state."""

    def test_empty_state_returns_cold_start(self, app):
        """No data = cold_start assessment."""
        identity_id = _make_identity(app)
        health = build_business_health(identity_id=identity_id)
        assert isinstance(health, dict)
        assert health["assessment"] == "cold_start"
        assert health["spaces"] == 0
        assert health["objects"] == 0

    def test_with_data_shows_counts(self, app):
        """Health shows real object/space/conversation counts."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        health = build_business_health(identity_id=identity_id)
        assert health["spaces"] == 2
        assert health["objects"] >= 3
        assert health["active_conversations"] >= 1

    def test_pipeline_status_returned(self, app):
        """Health includes pipeline status."""
        identity_id = _make_identity(app)
        health = build_business_health(identity_id=identity_id)
        assert "pipeline_status" in health
        assert "real_runtimes" in health
        assert "mock_runtimes" in health


# ---------------------------------------------------------------------------
# Tests: Recent Activity
# ---------------------------------------------------------------------------


class TestRecentActivity:
    """Recent Activity feed from persistent state."""

    def test_empty_state_returns_empty_list(self, app):
        """No activity = empty list."""
        identity_id = _make_identity(app)
        activity = build_recent_activity(identity_id=identity_id)
        assert isinstance(activity, list)
        assert len(activity) == 0

    def test_with_data_shows_objects(self, app):
        """Activity includes recently created objects."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        activity = build_recent_activity(identity_id=identity_id)
        assert len(activity) >= 3

    def test_activity_items_have_required_fields(self, app):
        """Every activity item has type, title, subtitle."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        activity = build_recent_activity(identity_id=identity_id)
        for a in activity:
            assert "type" in a, f"Missing type: {a}"
            assert "title" in a, f"Missing title: {a}"
            assert "subtitle" in a, f"Missing subtitle: {a}"
            assert "focus" in a, f"Missing focus: {a}"

    def test_activity_capped_at_limit(self, app):
        """Activity respects the limit parameter."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        activity = build_recent_activity(identity_id=identity_id, limit=3)
        assert len(activity) <= 3

    def test_dedup_same_object_type(self, app):
        """Same object doesn't appear twice in the same type category."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        activity = build_recent_activity(identity_id=identity_id)
        # Check that no type+object_id combination appears twice
        seen = set()
        for a in activity:
            key = (a.get("type"), a.get("focus", {}).get("object_id"))
            if key[1]:  # only check entries with an object_id
                assert key not in seen, f"Duplicate type+object_id: {key}"
                seen.add(key)


# ---------------------------------------------------------------------------
# Tests: Continue Working
# ---------------------------------------------------------------------------


class TestContinueWorking:
    """Continue Working from persisted state."""

    def test_empty_state_returns_empty_list(self, app):
        """No prior work = empty list."""
        identity_id = _make_identity(app)
        items = build_continue_working(identity_id=identity_id)
        assert isinstance(items, list)
        assert len(items) == 0

    def test_most_recently_updated_appears(self, app):
        """Recently updated objects appear as continue working items."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        items = build_continue_working(identity_id=identity_id)
        assert len(items) >= 3

    def test_items_have_navigation_data(self, app):
        """Every item includes focus for navigation."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        items = build_continue_working(identity_id=identity_id)
        for item in items:
            assert "focus" in item, f"Missing focus: {item}"
            assert item["focus"].get("object_id"), f"Missing object_id in focus: {item}"

    def test_items_capped_at_limit(self, app):
        """Continue working respects limit."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        items = build_continue_working(identity_id=identity_id, limit=3)
        assert len(items) <= 3


# ---------------------------------------------------------------------------
# Tests: Executive Home (integration)
# ---------------------------------------------------------------------------


class TestExecutiveHomeIntegration:
    """Full Executive Home assembly."""

    def test_complete_payload_structure(self, app):
        """Executive Home returns all required sections."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        home = build_executive_home(identity_id=identity_id)
        assert "morning_brief" in home
        assert "recommendations" in home
        assert "business_health" in home
        assert "recent_activity" in home
        assert "continue_working" in home

    def test_empty_state_payload(self, app):
        """Founder with no history gets a complete but empty payload."""
        identity_id = _make_identity(app)
        home = build_executive_home(identity_id=identity_id)
        assert len(home["recent_activity"]) == 0
        assert len(home["continue_working"]) == 0
        assert len(home["morning_brief"]["items"]) >= 1
        assert len(home["recommendations"]) >= 1

    def test_payload_no_placeholder_data(self, app):
        """No hardcoded demo/placeholder data in any section."""
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        home = build_executive_home(identity_id=identity_id)
        forbidden = ["lorem", "ipsum", "placeholder", "demo", "fake", "mock data"]
        all_text = str(home).lower()
        for word in forbidden:
            assert word not in all_text, f"Found forbidden word: {word}"

    def test_all_data_traces_to_reality(self, app):
        """Every item with focus points to a real object."""
        from app.founder.models import FounderObject
        identity_id = _make_identity(app)
        _seed_test_data(app, identity_id)
        home = build_executive_home(identity_id=identity_id)

        for item in home["morning_brief"]["items"]:
            focus = item.get("focus", {})
            oid = focus.get("object_id")
            if oid:
                found = FounderObject.query.filter_by(object_id=oid).first()
                assert found is not None, f"Brief item points to nonexistent object: {oid}"

        for a in home["recent_activity"]:
            focus = a.get("focus", {})
            oid = focus.get("object_id")
            if oid:
                found = FounderObject.query.filter_by(object_id=oid).first()
                assert found is not None, f"Activity item points to nonexistent object: {oid}"

    def test_refresh_persistence(self, app):
        """Subsequent calls reflect state changes."""
        identity_id = _make_identity(app)
        home1 = build_executive_home(identity_id=identity_id)
        assert home1["business_health"]["spaces"] == 0

        _seed_test_data(app, identity_id)

        home2 = build_executive_home(identity_id=identity_id)
        assert home2["business_health"]["spaces"] == 2

    def test_multiple_spaces(self, app):
        """Multiple spaces are all reflected."""
        from app import db
        from app.founder.models import FounderSpace
        identity_id = _make_identity(app)
        for i in range(3):
            space = FounderSpace(
                space_id=f"mspc_{i}", name=f"Space {'ABC'[i]}",
                space_type="organization", identity_id=identity_id,
            )
            db.session.add(space)
        db.session.commit()
        home = build_executive_home(identity_id=identity_id)
        assert home["business_health"]["spaces"] == 3
        assert home["morning_brief"]["summary"]["active_spaces"] == 3