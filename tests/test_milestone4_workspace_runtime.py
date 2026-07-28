"""Tests for Milestone 4 — Intelligent Workspace Runtime.

Tests all 10 required capabilities:
1. Workspace Summary — deterministic executive summary from persisted state
2. AI Understanding Panel — structured explanation with confidence + missing info
3. Relationship Intelligence — navigable related objects grouped by type
4. Activity Timeline — complete chronological history
5. Conversation Workspace — threaded discussion integrated with object
6. Next Actions — deterministic suggestions from runtime state
7. Missing Context Detection — active identification of understanding gaps
8. Workspace Health — deterministic, explainable health assessment
9. Evidence Explorer — every statement traceable to provenance
10. Navigation Canon — context-preserving movement between objects

Plus regression tests for Milestones 1–3.
"""
from __future__ import annotations

from datetime import datetime

from app.founder.workspace_intelligence import (
    acknowledge_next_action,
    build_activity_timeline,
    build_ai_understanding,
    build_evidence_explorer,
    build_full_workspace,
    build_next_actions,
    build_relationship_intelligence,
    build_workspace_summary,
    compute_workspace_health,
    detect_missing_context,
    dismiss_missing_context,
    get_conversation_workspace,
    get_navigation_history,
    navigate_to_object,
)
from core.os import reset_os


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_identity(app):
    from app.adapters.os_adapter import sign_in
    result = sign_in(email="nishesh@shunyaos.com", name="Nishesh")
    assert result["success"], f"Sign in failed: {result}"
    return result["identity_id"]


def _seed_workspace_data(app, identity_id):
    """Seed data for testing M4 workspace intelligence.

    Creates: 2 spaces, 3 objects (one with conversation, one orphan,
    one with relationships), 2 relationships.
    """
    from app import db
    from app.founder.models import (
        BusinessRelationship,
        FounderConversation,
        FounderMessage,
        FounderObject,
        FounderSpace,
    )

    space = FounderSpace(
        space_id="m4_spc_001", name="M4 Test Space",
        space_type="organization", identity_id=identity_id,
    )
    db.session.add(space)
    db.session.flush()

    # Object 1: fully featured (has content, conversation, messages)
    obj1 = FounderObject(
        object_id="m4_obj_001", space_id="m4_spc_001",
        name="Active Proposal", object_type="Document",
        content="This is a proposal for the Q3 marketing campaign.",
        created_by=identity_id,
        created_at=datetime(2026, 7, 1),
        updated_at=datetime(2026, 7, 20),
    )
    db.session.add(obj1)
    db.session.flush()

    conv1 = FounderConversation(
        conv_id="m4_conv_001", object_id="m4_obj_001",
        title="About Active Proposal", identity_id=identity_id,
    )
    db.session.add(conv1)
    db.session.flush()

    for i in range(3):
        db.session.add(FounderMessage(
            conv_id="m4_conv_001", role="human",
            content=f"Question {i} about the proposal",
            created_at=datetime(2026, 7, 15),
        ))
        db.session.add(FounderMessage(
            conv_id="m4_conv_001", role="assistant",
            content=f"Answer {i} regarding the proposal details",
            created_at=datetime(2026, 7, 15),
        ))

    # Object 2: minimal (no content, no conversation, no owner)
    obj2 = FounderObject(
        object_id="m4_obj_002", space_id="m4_spc_001",
        name="Old Report", object_type="Document",
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
    )
    db.session.add(obj2)

    # Object 3: recent, no conversation
    obj3 = FounderObject(
        object_id="m4_obj_003", space_id="m4_spc_001",
        name="New Idea", object_type="Note",
        content="Brainstorming notes for new feature.",
        created_by=identity_id,
        created_at=datetime(2026, 7, 25),
        updated_at=datetime(2026, 7, 25),
    )
    db.session.add(obj3)

    # Relationships
    rel1 = BusinessRelationship(
        rel_id="m4_rel_001", space_id="m4_spc_001",
        rel_type="customer", name="Acme Corp",
        company="Acme Corporation", created_by=identity_id,
    )
    db.session.add(rel1)
    rel2 = BusinessRelationship(
        rel_id="m4_rel_002", space_id="m4_spc_001",
        rel_type="supplier", name="Global Supplies Inc",
        company="Global Supplies", created_by=identity_id,
    )
    db.session.add(rel2)

    db.session.commit()


# ===========================================================================
# 1. Workspace Summary
# ===========================================================================

class TestWorkspaceSummary:
    """Workspace Summary — deterministic executive summary."""

    def test_summary_returns_basic_info(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_workspace_summary("m4_obj_001")
        assert result["object_id"] == "m4_obj_001"
        assert result["name"] == "Active Proposal"
        assert result["object_type"] == "Document"
        assert result["status"] == "active"
        assert result["created_by"] == identity_id

    def test_summary_includes_space_name(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_workspace_summary("m4_obj_001")
        assert result["space_name"] == "M4 Test Space"
        assert result["space_id"] == "m4_spc_001"

    def test_summary_activity_label_reflects_recency(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_workspace_summary("m4_obj_002")  # old object
        assert "No activity" in result["activity_label"]
        assert result["activity_days_since_update"] > 500

    def test_summary_conversation_count(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_workspace_summary("m4_obj_001")
        assert result["conversation_count"] == 1
        assert result["message_count"] >= 6

    def test_summary_relationship_count(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_workspace_summary("m4_obj_001")
        assert result["relationship_count"] == 2

    def test_summary_empty_object_returns_no_error(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_workspace_summary("nonexistent")
        assert "error" in result

    def test_summary_no_placeholder_data(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_workspace_summary("m4_obj_001")
        text = str(result).lower()
        for word in ["lorem", "ipsum", "placeholder", "fake"]:
            assert word not in text, f"Found forbidden: {word}"


# ===========================================================================
# 2. AI Understanding Panel
# ===========================================================================

class TestAIUnderstanding:
    """AI Understanding — structured explanation with confidence."""

    def test_ai_understanding_what_is(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_ai_understanding("m4_obj_001")
        assert "document" in result["what_is"].lower()
        assert "active proposal" in result["what_is"].lower()

    def test_ai_understanding_why_exists(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_ai_understanding("m4_obj_001")
        assert "Created by" in result["why_exists"]
        assert identity_id[:10] in result["why_exists"]

    def test_ai_understanding_confidence_for_complete_object(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_ai_understanding("m4_obj_001")
        assert result["confidence"]["score"] >= 0.5
        assert result["confidence"]["label"] in ("medium", "high")

    def test_ai_understanding_confidence_for_minimal_object(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_ai_understanding("m4_obj_002")  # minimal
        # Minimal object still benefits from space + type attribution
        assert result["confidence"]["score"] < 0.5

    def test_ai_understanding_missing_info(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_ai_understanding("m4_obj_002")
        missing_types = [m["field"] for m in result["missing_information"]]
        assert "content" in missing_types
        assert "owner" in missing_types

    def test_ai_understanding_influencing_relationships(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_ai_understanding("m4_obj_001")
        assert len(result["influencing_relationships"]) >= 2

    def test_ai_understanding_nonexistent_object(self, app):
        result = build_ai_understanding("nonexistent")
        assert "error" in result

    def test_ai_understanding_confidence_has_factors(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_ai_understanding("m4_obj_001")
        assert len(result["confidence"]["factors"]) >= 3


# ===========================================================================
# 3. Relationship Intelligence
# ===========================================================================

class TestRelationshipIntelligence:
    """Relationship Intelligence — navigable related objects by type."""

    def test_relationship_groups_exist(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_relationship_intelligence("m4_obj_001")
        assert "groups" in result
        assert len(result["groups"]) >= 1

    def test_relationship_business_group(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_relationship_intelligence("m4_obj_001")
        groups = {g["group_type"]: g for g in result["groups"]}
        assert "business_relationship" in groups
        assert len(groups["business_relationship"]["items"]) >= 2

    def test_relationship_same_space_group(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_relationship_intelligence("m4_obj_001")
        groups = {g["group_type"]: g for g in result["groups"]}
        assert "same_space" in groups
        # 2 other objects in same space (obj2, obj3)
        assert len(groups["same_space"]["items"]) >= 2

    def test_relationship_items_have_required_fields(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_relationship_intelligence("m4_obj_001")
        for group in result["groups"]:
            for item in group["items"]:
                assert item.get("object_id"), f"Missing object_id in {item}"
                assert item.get("name"), f"Missing name in {item}"

    def test_relationship_nonexistent_object(self, app):
        result = build_relationship_intelligence("nonexistent")
        assert "error" in result


# ===========================================================================
# 4. Activity Timeline
# ===========================================================================

class TestActivityTimeline:
    """Activity Timeline — chronological history."""

    def test_timeline_has_creation_event(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        timeline = build_activity_timeline("m4_obj_001")
        types = [e["event_type"] for e in timeline]
        assert "created" in types

    def test_timeline_has_conversation_events(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        timeline = build_activity_timeline("m4_obj_001")
        types = [e["event_type"] for e in timeline]
        assert "conversation" in types
        assert "message" in types

    def test_timeline_reverse_chronological(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        timeline = build_activity_timeline("m4_obj_001")
        timestamps = [e.get("created_at", "") for e in timeline if e.get("created_at")]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_timeline_events_have_required_fields(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        timeline = build_activity_timeline("m4_obj_001")
        for e in timeline:
            assert e.get("event_type"), f"Missing event_type"
            assert e.get("title"), f"Missing title"
            assert e.get("provenance"), f"Missing provenance"

    def test_timeline_empty_for_nonexistent(self, app):
        timeline = build_activity_timeline("nonexistent")
        assert timeline == []

    def test_timeline_events_have_importance(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        timeline = build_activity_timeline("m4_obj_001")
        for e in timeline:
            assert e.get("importance") in ("normal", "high", "system")


# ===========================================================================
# 5. Conversation Workspace
# ===========================================================================

class TestConversationWorkspace:
    """Conversation Workspace — integrated threaded discussion."""

    def test_conversation_returns_correct_object(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = get_conversation_workspace("m4_obj_001")
        assert result["object_id"] == "m4_obj_001"
        assert result["status"] == "active"

    def test_conversation_has_messages(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = get_conversation_workspace("m4_obj_001")
        assert len(result["messages"]) >= 6

    def test_conversation_no_conversation_for_orphan(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = get_conversation_workspace("m4_obj_002")
        assert result["conversation"] is None
        assert result["status"] == "no_conversation"

    def test_conversation_messages_ordered_by_time(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = get_conversation_workspace("m4_obj_001")
        timestamps = [m["created_at"] for m in result["messages"] if m.get("created_at")]
        assert timestamps == sorted(timestamps)

    def test_conversation_nonexistent_object(self, app):
        result = get_conversation_workspace("nonexistent")
        assert "error" in result


# ===========================================================================
# 6. Next Actions
# ===========================================================================

class TestNextActions:
    """Next Actions — deterministic suggestions from runtime state."""

    def test_next_actions_generated_for_minimal_object(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        actions = build_next_actions("m4_obj_002")  # no content, no owner, no conv
        types = [a["action_type"] for a in actions if a["status"] == "pending"]
        assert "start_conversation" in types
        assert "add_content" in types
        assert "add_owner" in types

    def test_next_actions_not_generated_for_full_object(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        actions = build_next_actions("m4_obj_001")  # has everything
        pending_types = [a["action_type"] for a in actions if a["status"] == "pending"]
        # Should not suggest things that already exist
        assert "add_content" not in pending_types

    def test_next_actions_have_explanation(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        actions = build_next_actions("m4_obj_002")
        for a in actions:
            assert a.get("explanation"), f"Missing explanation for {a['action_type']}"
            assert a.get("supporting_evidence"), f"Missing evidence for {a['action_type']}"

    def test_next_actions_have_priority_score(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        actions = build_next_actions("m4_obj_002")
        for a in actions:
            assert 0 <= a["priority_score"] <= 1, f"Invalid score: {a['priority_score']}"

    def test_next_actions_persist_across_calls(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        actions1 = build_next_actions("m4_obj_002")
        actions2 = build_next_actions("m4_obj_002")
        assert len(actions2) >= len(actions1)

    def test_next_action_acknowledge(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        actions = build_next_actions("m4_obj_002")
        pending = [a for a in actions if a["status"] == "pending"]
        if pending:
            result = acknowledge_next_action(pending[0]["id"])
            assert result == "completed"

    def test_next_actions_no_placeholder(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        actions = build_next_actions("m4_obj_002")
        text = str(actions).lower()
        assert "lorem" not in text
        assert "ipsum" not in text


# ===========================================================================
# 7. Missing Context Detection
# ===========================================================================

class TestMissingContext:
    """Missing Context Detection — active identification of gaps."""

    def test_missing_context_detects_owner(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        gaps = detect_missing_context("m4_obj_002")  # no owner
        types = [g["context_type"] for g in gaps]
        assert "missing_owner" in types

    def test_missing_context_detects_content(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        gaps = detect_missing_context("m4_obj_002")  # no content
        types = [g["context_type"] for g in gaps]
        assert "missing_notes" in types

    def test_missing_context_detects_conversation(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        gaps = detect_missing_context("m4_obj_003")  # no conversation
        types = [g["context_type"] for g in gaps]
        assert "missing_conversation" in types

    def test_missing_context_not_generated_for_complete_object(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        gaps = detect_missing_context("m4_obj_001")  # fully featured
        # Should not have owner/content/conversation gaps
        gap_types = [g["context_type"] for g in gaps]
        assert "missing_owner" not in gap_types
        assert "missing_notes" not in gap_types
        assert "missing_conversation" not in gap_types

    def test_missing_context_has_severity(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        gaps = detect_missing_context("m4_obj_002")
        for g in gaps:
            assert g.get("severity") in ("info", "suggestion", "recommendation")

    def test_missing_context_dismiss(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        gaps = detect_missing_context("m4_obj_002")
        if gaps:
            result = dismiss_missing_context(gaps[0]["id"])
            assert result == "addressed"

    def test_missing_context_persists(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        gaps1 = detect_missing_context("m4_obj_002")
        gaps2 = detect_missing_context("m4_obj_002")
        assert len(gaps2) >= len(gaps1)


# ===========================================================================
# 8. Workspace Health
# ===========================================================================

class TestWorkspaceHealth:
    """Workspace Health — deterministic explainable assessment."""

    def test_health_computes_overall_score(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = compute_workspace_health("m4_obj_001")
        assert 0 <= result["overall_score"] <= 1

    def test_health_complete_object_high_score(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = compute_workspace_health("m4_obj_001")  # fully featured
        assert result["overall_score"] >= 0.5
        assert result["label"] in ("healthy", "needs_attention")

    def test_health_minimal_object_low_score(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = compute_workspace_health("m4_obj_002")  # minimal
        assert result["overall_score"] < 0.5
        assert result["label"] in ("needs_attention", "critical")

    def test_health_has_breakdown_with_all_dimensions(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = compute_workspace_health("m4_obj_001")
        bd = result["breakdown"]
        for dim in ("completeness", "activity", "relationships", "conversations", "commitments"):
            assert dim in bd, f"Missing dimension: {dim}"
            assert "score" in bd[dim]
            assert "factors" in bd[dim]

    def test_health_is_deterministic(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result1 = compute_workspace_health("m4_obj_001")
        result2 = compute_workspace_health("m4_obj_001")
        assert result1["overall_score"] == result2["overall_score"]
        assert result1["breakdown"]["completeness"]["score"] == result2["breakdown"]["completeness"]["score"]

    def test_health_persists_snapshot(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        from app.founder.workspace_models import WorkspaceHealthSnapshot
        before = WorkspaceHealthSnapshot.query.filter_by(object_id="m4_obj_001").count()
        compute_workspace_health("m4_obj_001")
        after = WorkspaceHealthSnapshot.query.filter_by(object_id="m4_obj_001").count()
        assert after > before

    def test_health_label_is_meaningful(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = compute_workspace_health("m4_obj_001")
        assert result["label"] in ("healthy", "needs_attention", "critical")

    def test_health_nonexistent_object(self, app):
        result = compute_workspace_health("nonexistent")
        assert "error" in result


# ===========================================================================
# 9. Evidence Explorer
# ===========================================================================

class TestEvidenceExplorer:
    """Evidence Explorer — every statement traceable to provenance."""

    def test_evidence_has_provenance_entries(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        evidence = build_evidence_explorer("m4_obj_001")
        assert len(evidence) >= 3

    def test_evidence_each_entry_has_required_fields(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        evidence = build_evidence_explorer("m4_obj_001")
        for e in evidence:
            assert e.get("statement"), f"Missing statement"
            assert e.get("source_type"), f"Missing source_type"
            assert e.get("provenance"), f"Missing provenance"
            assert e.get("confidence"), f"Missing confidence"

    def test_evidence_confidence_is_certain(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        evidence = build_evidence_explorer("m4_obj_001")
        for e in evidence:
            assert e["confidence"] == "certain"

    def test_evidence_source_types_present(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        evidence = build_evidence_explorer("m4_obj_001")
        types = set(e["source_type"] for e in evidence)
        assert "object" in types
        assert "relationship" in types
        assert "conversation" in types

    def test_evidence_empty_for_nonexistent(self, app):
        evidence = build_evidence_explorer("nonexistent")
        assert evidence == []


# ===========================================================================
# 10. Navigation Canon
# ===========================================================================

class TestNavigationCanon:
    """Navigation Canon — context-preserving movement between objects."""

    def test_navigate_records_trail(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = navigate_to_object(
            source_object_id="m4_obj_001",
            target_object_id="m4_obj_002",
            identity_id=identity_id,
            relationship_type="same_space",
        )
        assert result["navigation_recorded"] is True
        assert result["target_object_id"] == "m4_obj_002"
        assert result["source_object_id"] == "m4_obj_001"

    def test_navigate_returns_target_context(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = navigate_to_object(
            source_object_id="m4_obj_001",
            target_object_id="m4_obj_003",
            identity_id=identity_id,
        )
        assert result["target_name"] == "New Idea"
        assert result["target_type"] == "Note"

    def test_navigate_nonexistent_target(self, app):
        identity_id = _make_identity(app)
        result = navigate_to_object(
            source_object_id="m4_obj_001",
            target_object_id="nonexistent",
            identity_id=identity_id,
        )
        assert "error" in result

    def test_navigation_history_records_trail(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        navigate_to_object("m4_obj_001", "m4_obj_002", identity_id, "same_space")
        navigate_to_object("m4_obj_002", "m4_obj_003", identity_id, "same_space")
        history = get_navigation_history(identity_id)
        assert len(history) >= 2
        assert history[0]["source_object_id"] == "m4_obj_002"
        assert history[0]["target_object_id"] == "m4_obj_003"

    def test_navigation_history_empty(self, app):
        identity_id = _make_identity(app)
        history = get_navigation_history("no_nav_user")
        assert history == []


# ===========================================================================
# Full Workspace Assembly
# ===========================================================================

class TestFullWorkspace:
    """Full workspace assembly returns all panels."""

    def test_full_workspace_contains_all_panels(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_full_workspace("m4_obj_001")
        assert "summary" in result
        assert "ai_understanding" in result
        assert "relationships" in result
        assert "timeline" in result
        assert "conversation" in result
        assert "next_actions" in result
        assert "missing_context" in result
        assert "health" in result
        assert "evidence" in result

    def test_full_workspace_summary_has_data(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_full_workspace("m4_obj_001")
        assert result["summary"]["name"] == "Active Proposal"

    def test_full_workspace_nonexistent(self, app):
        result = build_full_workspace("nonexistent")
        assert "error" in result

    def test_full_workspace_no_placeholder(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_full_workspace("m4_obj_001")
        text = str(result).lower()
        for word in ["lorem", "ipsum", "placeholder", "fake"]:
            assert word not in text, f"Found forbidden: {word}"


# ===========================================================================
# Refresh Persistence
# ===========================================================================

class TestRefreshPersistence:
    """Subsequent calls reflect state changes."""

    def test_workspace_updates_after_object_changes(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        from app import db
        from app.founder.models import FounderObject

        # Get baseline health for minimal object
        health_before = compute_workspace_health("m4_obj_002")

        # Improve the object
        obj = FounderObject.query.filter_by(object_id="m4_obj_002").first()
        obj.content = "Now this object has meaningful content added."
        obj.created_by = identity_id
        db.session.commit()

        # Recompute
        health_after = compute_workspace_health("m4_obj_002")
        assert health_after["overall_score"] > health_before["overall_score"]

    def test_next_actions_update_after_completion(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        actions = build_next_actions("m4_obj_002")
        pending = [a for a in actions if a["status"] == "pending"]
        if pending:
            acknowledge_next_action(pending[0]["id"])
            actions_after = build_next_actions("m4_obj_002")
            completed_ids = [a["id"] for a in actions_after if a["status"] == "completed"]
            assert pending[0]["id"] in completed_ids


# ===========================================================================
# Multi-Space Behaviour
# ===========================================================================

class TestMultiSpaceBehaviour:
    """Workspace intelligence works across multiple spaces."""

    def test_multiple_spaces_relationship_groups(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        from app import db
        from app.founder.models import FounderSpace

        # Create a second space with an object
        space2 = FounderSpace(
            space_id="m4_spc_002", name="Second Space",
            space_type="project", identity_id=identity_id,
        )
        db.session.add(space2)
        db.session.commit()

        # Object in first space still works fine
        result = build_relationship_intelligence("m4_obj_001")
        assert len(result["groups"]) >= 1

    def test_health_works_across_spaces(self, app):
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        from app import db
        from app.founder.models import FounderObject, FounderSpace

        space3 = FounderSpace(
            space_id="m4_spc_003", name="Third Space",
            space_type="personal", identity_id=identity_id,
        )
        db.session.add(space3)
        db.session.flush()

        obj = FounderObject(
            object_id="m4_obj_004", space_id="m4_spc_003",
            name="Personal Note", object_type="Note",
            content="A personal note.", created_by=identity_id,
        )
        db.session.add(obj)
        db.session.commit()

        health = compute_workspace_health("m4_obj_004")
        assert 0 <= health["overall_score"] <= 1


# ===========================================================================
# Regression — Milestones 1–3
# ===========================================================================

class TestMilestoneRegression:
    """Regression tests ensuring Milestones 1–3 still pass."""

    def test_m1_identity_signin(self, app):
        """Milestone 1: Sign in creates identity."""
        from app.adapters.os_adapter import sign_in
        result = sign_in(email="regression@test.com", name="Regression")
        assert result["success"]
        assert result.get("identity_id")

    def test_m1_create_space(self, app):
        """Milestone 1: Can create a space."""
        identity_id = _make_identity(app)
        from app.adapters.os_adapter import create_space
        result = create_space(
            name="Regression Space",
            identity_id=identity_id,
        )
        assert result["success"] or result.get("object_id")

    def test_m1_create_object(self, app):
        """Milestone 1: Can create an object in a space."""
        identity_id = _make_identity(app)
        from app import db
        from app.founder.models import FounderSpace
        space = FounderSpace(
            space_id="reg_spc_001", name="Reg Space",
            identity_id=identity_id,
        )
        db.session.add(space)
        db.session.commit()

        from app.adapters.os_adapter import create_object
        result = create_object(
            name="Reg Object", object_type="Document",
            space_id="reg_spc_001", identity_id=identity_id,
        )
        assert result["success"] or result.get("object_id")

    def test_m2_morning_brief(self, app):
        """Milestone 2: Morning brief works with data."""
        from app.founder.executive_home_service import build_morning_brief
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        brief = build_morning_brief(identity_id)
        assert "items" in brief
        assert "summary" in brief

    def test_m2_executive_home(self, app):
        """Milestone 2: Executive home assembles cleanly."""
        from app.adapters.os_adapter import get_executive_home
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = get_executive_home(identity_id=identity_id)
        assert result["success"]

    def test_m3_insight_generation(self, app):
        """Milestone 3: Insights are generated from data."""
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_insights(identity_id=identity_id)
        assert result["summary"]["total_insights"] > 0

    def test_m3_insight_structure(self, app):
        """Milestone 3: All insights have required fields."""
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_insights(identity_id=identity_id)
        for ins in result["insights"]:
            assert ins.get("id")
            assert ins.get("type")
            assert ins.get("title")
            assert ins.get("what")
            assert ins.get("evidence")
            assert ins.get("next_steps")
            assert ins.get("priority_score") is not None

    def test_m3_priority_scoring_deterministic(self, app):
        """Milestone 3: Priority scores are reproducible."""
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        r1 = build_insights(identity_id=identity_id)
        r2 = build_insights(identity_id=identity_id)
        s1 = [(i["id"], i["priority_score"]) for i in r1["insights"]]
        s2 = [(i["id"], i["priority_score"]) for i in r2["insights"]]
        assert s1 == s2

    def test_m3_no_placeholder_text(self, app):
        """Milestone 3: No placeholder patterns in any insight."""
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        _seed_workspace_data(app, identity_id)
        result = build_insights(identity_id=identity_id)
        text = str(result).lower()
        for word in ["lorem", "ipsum", "placeholder", "fake"]:
            assert word not in text, f"Found forbidden: {word}"