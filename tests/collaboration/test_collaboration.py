"""Tests for Milestone IX — Collaboration & Multi-user OS."""
import pytest
from app.collaboration import (
    CollaborationRuntime, get_collaboration_runtime, reset_collaboration_runtime,
)
from app.collaboration.models import (
    UserRole, AssignmentRole, ActivityEventType, ConflictType, VoteValue,
    PresenceEntry, WorkspaceSession, ConversationMessage,
    Assignment, ActivityEvent, CollaborationEvent, DecisionDiscussion, ConflictRecord,
)
from app.collaboration.engine import (
    PresenceRuntime, SessionManager, RoleAwareWorkspace,
    SharedConversation, DecisionCollaboration, AssignmentIntelligence,
    ActivityTimeline, LiveCollaboration, ConflictResolver, OrganizationalMemory, ExecutiveOversight,
)


@pytest.fixture
def rt() -> CollaborationRuntime:
    reset_collaboration_runtime()
    return get_collaboration_runtime()


# =========================================================================
# 1. Presence
# =========================================================================
class TestPresence:
    def test_update(self):
        pr = PresenceRuntime()
        e = pr.update(1, "Alice", "executive", "execution", "e1")
        assert e.user_name == "Alice"
        assert e.object_id == "e1"

    def test_get_for_object(self):
        pr = PresenceRuntime()
        pr.update(1, "A", "exec", "execution", "e1")
        pr.update(2, "B", "mgr", "execution", "e1")
        pr.update(3, "C", "op", "execution", "e2")
        assert len(pr.get_for_object("execution", "e1")) == 2

    def test_remove(self):
        pr = PresenceRuntime()
        pr.update(1, "A", "exec", "execution", "e1")
        pr.remove(1, "execution", "e1")
        assert len(pr.get_for_object("execution", "e1")) == 0


# =========================================================================
# 2. Sessions
# =========================================================================
class TestSessions:
    def test_create(self):
        sm = SessionManager()
        s = sm.create(1)
        assert s.session_id
        assert s.user_id == 1

    def test_focus(self):
        sm = SessionManager()
        s = sm.create(1)
        sm.update_focus(s.session_id, "execution", "e1")
        assert sm.get(s.session_id).focused_object_id == "e1"

    def test_pin_toggle(self):
        sm = SessionManager()
        s = sm.create(1)
        sm.toggle_pin(s.session_id, "obj1")
        s2 = sm.get(s.session_id)
        assert "obj1" in s2.pinned_objects
        sm.toggle_pin(s.session_id, "obj1")
        s3 = sm.get(s.session_id)
        assert "obj1" not in s3.pinned_objects


# =========================================================================
# 3. Role-Aware Workspace
# =========================================================================
class TestRoles:
    def test_executive_can_view(self):
        rw = RoleAwareWorkspace()
        assert rw.get_role("executive").can_view_all_objects is True

    def test_guest_cannot_view(self):
        rw = RoleAwareWorkspace()
        assert rw.get_role("guest").can_view_all_objects is False

    def test_executive_can_approve(self):
        rw = RoleAwareWorkspace()
        assert rw.can_approve("executive") is True

    def test_operator_cannot_approve(self):
        rw = RoleAwareWorkspace()
        assert rw.can_approve("operator") is False

    def test_filter_executive_restricted(self):
        rw = RoleAwareWorkspace()
        result = rw.filter_executive("operator", {"health": 0.8})
        assert result.get("restricted") is True


# =========================================================================
# 4. Shared Conversation
# =========================================================================
class TestConversation:
    def test_post(self):
        sc = SharedConversation()
        msg = sc.post("execution", "e1", 1, "Alice", "What is blocking this?")
        assert msg.text == "What is blocking this?"

    def test_get_for_object(self):
        sc = SharedConversation()
        sc.post("execution", "e1", 1, "A", "msg1")
        sc.post("execution", "e1", 2, "B", "msg2")
        sc.post("execution", "e2", 1, "A", "msg3")
        assert len(sc.get_for_object("execution", "e1")) == 2

    def test_search(self):
        sc = SharedConversation()
        sc.post("execution", "e1", 1, "A", "blocked payment")
        sc.post("execution", "e1", 2, "B", "approved")
        assert len(sc.search("blocked")) == 1

    def test_links(self):
        sc = SharedConversation()
        msg = sc.post("execution", "e1", 1, "A", "check evidence",
                       links={"evidence": "ev1", "decision": "d1"})
        assert len(msg.linked_evidence) >= 1


# =========================================================================
# 5. Decision Collaboration
# =========================================================================
class TestDecisionCollaboration:
    def test_create(self):
        dc = DecisionCollaboration()
        dd = dc.create("d1", 1, "Resource allocation")
        assert dd.title == "Resource allocation"

    def test_vote(self):
        dc = DecisionCollaboration()
        dd = dc.create("d1", 1, "test")
        dc.vote(dd.discussion_id, 1, "Alice", "approve", "Looks good")
        assert len(dd.votes) == 1
        assert dd.votes[0].vote == "approve"

    def test_resolve(self):
        dc = DecisionCollaboration()
        dd = dc.create("d1", 1, "test")
        dc.resolve(dd.discussion_id, "Approved by executive")
        assert dd.resolved is True

    def test_objection(self):
        dc = DecisionCollaboration()
        dd = dc.create("d1", 1, "test")
        dc.add_objection(dd.discussion_id, "Budget not approved")
        assert len(dd.objections) == 1


# =========================================================================
# 6. Assignment Intelligence
# =========================================================================
class TestAssignments:
    def test_assign(self):
        ai = AssignmentIntelligence()
        a = ai.assign("execution", "e1", 1, 1, "Alice", "responsible")
        assert a.role == "responsible"
        assert a.active is True

    def test_unassign(self):
        ai = AssignmentIntelligence()
        a = ai.assign("execution", "e1", 1, 1, "A", "responsible")
        ai.unassign(a.assignment_id)
        assert ai.get_for_object("execution", "e1") == []

    def test_get_by_role(self):
        ai = AssignmentIntelligence()
        ai.assign("execution", "e1", 1, 1, "A", "responsible")
        ai.assign("execution", "e1", 1, 2, "B", "approver")
        assert len(ai.get_by_role("execution", "e1", "responsible")) == 1
        assert len(ai.get_by_role("execution", "e1", "approver")) == 1


# =========================================================================
# 7. Activity Timeline
# =========================================================================
class TestTimeline:
    def test_record(self):
        at = ActivityTimeline()
        e = at.record("execution", "e1", 1, "A", "viewed")
        assert e.event_type == "viewed"

    def test_get_for_object(self):
        at = ActivityTimeline()
        at.record("execution", "e1", 1, "A", "viewed")
        at.record("execution", "e1", 2, "B", "commented")
        at.record("execution", "e2", 1, "A", "viewed")
        assert len(at.get_for_object("execution", "e1")) == 2


# =========================================================================
# 8. Live Collaboration
# =========================================================================
class TestLive:
    def test_emit(self):
        lc = LiveCollaboration()
        e = lc.emit("presence", "execution", "e1", 1, "Alice")
        assert e.event_type == "presence"

    def test_get_since(self):
        lc = LiveCollaboration()
        lc.emit("presence", "execution", "e1", 1, "A")
        import time; time.sleep(0.01)
        ts = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        lc.emit("comment", "execution", "e1", 2, "B")
        events = lc.get_since(ts)
        assert len(events) >= 1


# =========================================================================
# 9. Conflict Resolution
# =========================================================================
class TestConflicts:
    def test_detect(self):
        cr = ConflictResolver()
        c = cr.detect("execution", "e1", [1, 2], "concurrent_edit")
        assert c is not None
        assert c.resolved is True

    def test_single_user_no_conflict(self):
        cr = ConflictResolver()
        c = cr.detect("execution", "e1", [1], "concurrent_edit")
        assert c is None


# =========================================================================
# 10. Organizational Memory
# =========================================================================
class TestMemory:
    def test_record(self):
        om = OrganizationalMemory()
        msg = ConversationMessage(object_type="execution", object_id="e1", text="test")
        om.record(message=msg)
        assert om.get_stats()["messages"] == 1

    def test_search(self):
        om = OrganizationalMemory()
        m1 = ConversationMessage(object_type="execution", object_id="e1", text="blocked payment")
        m2 = ConversationMessage(object_type="execution", object_id="e1", text="approved")
        om.record(message=m1)
        om.record(message=m2)
        assert len(om.search_messages("blocked")) == 1


# =========================================================================
# 11. Executive Oversight
# =========================================================================
class TestOversight:
    def test_overview(self, rt):
        # Executive oversight requires executive intelligence to have data
        overview = rt.oversight.get_overview(1)
        assert "needing_attention" in overview
        assert "stalled_approvals" in overview
        assert "high_risk_predictions" in overview


# =========================================================================
# 12. Integration
# =========================================================================
class TestIntegration:
    def test_get_workspace(self, rt):
        w = rt.get_workspace(1, "Alice", "executive", "execution", "e1")
        assert "session" in w
        assert "presence" in w
        assert "stats" in w

    def test_stats(self, rt):
        s = rt.stats()
        assert "active_sessions" in s

    def test_singleton(self):
        reset_collaboration_runtime()
        r1 = get_collaboration_runtime()
        r2 = get_collaboration_runtime()
        assert r1 is r2

    def test_to_dict_presence(self):
        p = PresenceEntry(user_id=1, user_name="A", object_type="execution", object_id="e1")
        d = p.to_dict()
        assert "user_name" in d

    def test_to_dict_session(self):
        s = WorkspaceSession(user_id=1)
        d = s.to_dict()
        assert "session_id" in d

    def test_assignment_to_dict(self):
        a = Assignment(object_type="execution", object_id="e1", tenant_id=1,
                       user_id=1, user_name="A", role="responsible")
        d = a.to_dict()
        assert "role" in d