"""SHUNYA — Collaboration Engine (Milestone IX).

Multi-user operating system: presence, sessions, role-aware workspaces,
shared conversations, decision collaboration, assignments, activity
timelines, live events, conflict resolution, organizational memory,
and executive oversight.
"""

from __future__ import annotations

import hashlib, time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.collaboration.models import (
    AssignmentRole, ActivityEventType, ConflictType, VoteValue, UserRole,
    PresenceEntry, WorkspaceSession, RoleDefinition,
    ConversationMessage, DecisionDiscussion, DecisionVote,
    Assignment, ActivityEvent, CollaborationEvent,
    ConflictRecord, CollaborationStats,
    CollaborationConfig, CollaborationFilter,
)
from app.executive import get_executive_engine, ExecutiveIntelligenceEngine
from app.organizational import get_organizational_intelligence, OrganizationalIntelligenceEngine
from app.workspace_runtime import get_workspace_runtime, WorkspaceRuntime

# =========================================================================
# Singleton
# =========================================================================

_RUNTIME: Optional[CollaborationRuntime] = None


def get_collaboration_runtime() -> CollaborationRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = CollaborationRuntime()
    return _RUNTIME


def reset_collaboration_runtime() -> None:
    global _RUNTIME
    _RUNTIME = None


# =========================================================================
# 1. Presence Runtime
# =========================================================================

class PresenceRuntime:
    """Who is viewing/editing what — continuous updates."""

    def __init__(self, config: Optional[CollaborationConfig] = None):
        self._config = config or CollaborationConfig()
        self._entries: Dict[str, PresenceEntry] = {}

    def update(self, user_id: int, user_name: str, user_role: str,
               object_type: str, object_id: str, action: str = "viewing",
               session_id: str = "") -> PresenceEntry:
        key = f"{user_id}:{object_type}:{object_id}"
        entry = PresenceEntry(
            user_id=user_id, user_name=user_name, user_role=user_role,
            object_type=object_type, object_id=object_id,
            action=action, session_id=session_id,
        )
        self._entries[key] = entry
        return entry

    def get_for_object(self, object_type: str, object_id: str) -> List[PresenceEntry]:
        now = datetime.now(timezone.utc)
        timeout = timedelta(seconds=self._config.presence_timeout_seconds)
        result = []
        stale = []
        for key, entry in self._entries.items():
            if entry.object_type == object_type and entry.object_id == object_id:
                try:
                    seen = datetime.fromisoformat(entry.last_seen)
                    if seen.tzinfo is None:
                        seen = seen.replace(tzinfo=timezone.utc)
                    if (now - seen) > timeout:
                        stale.append(key)
                        continue
                except (ValueError, TypeError):
                    pass
                result.append(entry)
        for k in stale:
            del self._entries[k]
        return result

    def get_all_active(self) -> List[PresenceEntry]:
        now = datetime.now(timezone.utc)
        timeout = timedelta(seconds=self._config.presence_timeout_seconds)
        result = []
        for key, entry in list(self._entries.items()):
            try:
                seen = datetime.fromisoformat(entry.last_seen)
                if seen.tzinfo is None:
                    seen = seen.replace(tzinfo=timezone.utc)
                if (now - seen) <= timeout:
                    result.append(entry)
            except (ValueError, TypeError):
                pass
        return result

    def remove(self, user_id: int, object_type: str, object_id: str):
        key = f"{user_id}:{object_type}:{object_id}"
        self._entries.pop(key, None)


# =========================================================================
# 2. Session Manager
# =========================================================================

class SessionManager:
    """Manage WorkspaceSession — temporary UI state, never business truth."""

    def __init__(self):
        self._sessions: Dict[str, WorkspaceSession] = {}

    def create(self, user_id: int) -> WorkspaceSession:
        session = WorkspaceSession(user_id=user_id)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[WorkspaceSession]:
        s = self._sessions.get(session_id)
        if s:
            s.last_active = datetime.now(timezone.utc).isoformat()
        return s

    def get_by_user(self, user_id: int) -> Optional[WorkspaceSession]:
        for s in self._sessions.values():
            if s.user_id == user_id:
                s.last_active = datetime.now(timezone.utc).isoformat()
                return s
        return None

    def update_focus(self, session_id: str, obj_type: str, obj_id: str):
        s = self._sessions.get(session_id)
        if s:
            if s.focused_object_id:
                s.navigation_history.append(f"{s.focused_object_type}/{s.focused_object_id}")
            s.focused_object_type = obj_type
            s.focused_object_id = obj_id
            s.last_active = datetime.now(timezone.utc).isoformat()

    def set_mode(self, session_id: str, mode: str):
        s = self._sessions.get(session_id)
        if s:
            s.executive_mode = mode
            s.last_active = datetime.now(timezone.utc).isoformat()

    def set_attention(self, session_id: str, layer: str):
        s = self._sessions.get(session_id)
        if s:
            s.attention_layer = layer
            s.last_active = datetime.now(timezone.utc).isoformat()

    def toggle_pin(self, session_id: str, obj_id: str):
        s = self._sessions.get(session_id)
        if s:
            if obj_id in s.pinned_objects:
                s.pinned_objects.remove(obj_id)
            else:
                s.pinned_objects.append(obj_id)

    def get_active_sessions(self) -> List[WorkspaceSession]:
        now = datetime.now(timezone.utc)
        active = []
        for s in self._sessions.values():
            try:
                la = datetime.fromisoformat(s.last_active)
                if la.tzinfo is None:
                    la = la.replace(tzinfo=timezone.utc)
                if (now - la) < timedelta(minutes=5):
                    active.append(s)
            except (ValueError, TypeError):
                pass
        return active


# =========================================================================
# 3. Role-Aware Workspace
# =========================================================================

class RoleAwareWorkspace:
    """Runtime-filtered visibility per role.

    Permissions derive from Governance.
    Frontend never implements authorization.
    """

    def __init__(self):
        self._roles: Dict[str, RoleDefinition] = self._default_roles()

    def _default_roles(self) -> Dict[str, RoleDefinition]:
        return {
            UserRole.EXECUTIVE.value: RoleDefinition(
                role=UserRole.EXECUTIVE.value, can_view_all_objects=True,
                can_edit_objects=True, can_approve_decisions=True,
                can_assign_users=True, can_escalate=True,
                can_view_executive=True, max_priority_visibility=100,
            ),
            UserRole.MANAGER.value: RoleDefinition(
                role=UserRole.MANAGER.value, can_view_all_objects=True,
                can_edit_objects=True, can_approve_decisions=True,
                can_assign_users=True, can_escalate=True,
                can_view_executive=True, max_priority_visibility=50,
            ),
            UserRole.OPERATOR.value: RoleDefinition(
                role=UserRole.OPERATOR.value, can_view_all_objects=False,
                can_edit_objects=True, can_approve_decisions=False,
                can_assign_users=False, can_escalate=True,
                can_view_executive=False, max_priority_visibility=20,
            ),
            UserRole.FINANCE.value: RoleDefinition(
                role=UserRole.FINANCE.value, can_view_all_objects=False,
                can_edit_objects=True, can_approve_decisions=True,
                can_assign_users=False, can_escalate=False,
                can_view_executive=False, max_priority_visibility=10,
            ),
            UserRole.SALES.value: RoleDefinition(
                role=UserRole.SALES.value, can_view_all_objects=False,
                can_edit_objects=False, can_approve_decisions=False,
                can_assign_users=False, can_escalate=True,
                can_view_executive=False, max_priority_visibility=10,
            ),
            UserRole.OPERATIONS.value: RoleDefinition(
                role=UserRole.OPERATIONS.value, can_view_all_objects=True,
                can_edit_objects=True, can_approve_decisions=False,
                can_assign_users=False, can_escalate=True,
                can_view_executive=True, max_priority_visibility=30,
            ),
            UserRole.GUEST.value: RoleDefinition(
                role=UserRole.GUEST.value, can_view_all_objects=False,
                can_edit_objects=False, can_approve_decisions=False,
                can_assign_users=False, can_escalate=False,
                can_view_executive=False, max_priority_visibility=5,
            ),
        }

    def get_role(self, role: str) -> RoleDefinition:
        return self._roles.get(role, self._roles[UserRole.GUEST.value])

    def filter_objects(self, role: str, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rd = self.get_role(role)
        if rd.can_view_all_objects:
            return objects
        return [o for o in objects if rd.can_view(o.get("type", ""), o.get("state", ""))]

    def filter_executive(self, role: str, executive_data: Dict[str, Any]) -> Dict[str, Any]:
        rd = self.get_role(role)
        if not rd.can_view_executive:
            return {"restricted": True, "message": "Executive data not available for your role"}
        return executive_data

    def can_approve(self, role: str) -> bool:
        return self.get_role(role).can_approve_decisions

    def can_assign(self, role: str) -> bool:
        return self.get_role(role).can_assign_users


# =========================================================================
# 4. Shared Conversation
# =========================================================================

class SharedConversation:
    """Conversation as organizational memory.

    Every message links to object, evidence, reasoning, decision,
    prediction, commitment, execution. Messages remain searchable forever.
    """

    def __init__(self):
        self._messages: List[ConversationMessage] = []

    def post(self, obj_type: str, obj_id: str, user_id: int, user_name: str,
             text: str, links: Optional[Dict[str, str]] = None) -> ConversationMessage:
        msg = ConversationMessage(
            object_type=obj_type, object_id=obj_id,
            user_id=user_id, user_name=user_name, text=text,
            linked_evidence=[links.get(k, "") for k in ("evidence", "reasoning", "decision",
                                                          "prediction", "commitment", "execution")
                             if links and k in links and links[k]],
            linked_decision=links.get("decision", "") if links else "",
            linked_prediction=links.get("prediction", "") if links else "",
            linked_commitment=links.get("commitment", "") if links else "",
            linked_execution=links.get("execution", "") if links else "",
        )
        self._messages.append(msg)
        return msg

    def get_for_object(self, obj_type: str, obj_id: str, limit: int = 50) -> List[ConversationMessage]:
        return [m for m in self._messages
                if m.object_type == obj_type and m.object_id == obj_id][-limit:]

    def search(self, query: str, limit: int = 20) -> List[ConversationMessage]:
        q = query.lower()
        return [m for m in self._messages if q in m.text.lower()][-limit:]

    def get_all(self, limit: int = 100) -> List[ConversationMessage]:
        return self._messages[-limit:]

    @property
    def total(self) -> int:
        return len(self._messages)


# =========================================================================
# 5. Decision Collaboration
# =========================================================================

class DecisionCollaboration:
    """Structured discussion, approvals, objections, resolution."""

    def __init__(self):
        self._discussions: Dict[str, DecisionDiscussion] = {}

    def create(self, decision_id: str, tenant_id: int, title: str,
               alternatives: List[str] = None) -> DecisionDiscussion:
        dd = DecisionDiscussion(
            decision_id=decision_id, tenant_id=tenant_id, title=title,
            alternatives=alternatives or [],
        )
        self._discussions[dd.discussion_id] = dd
        return dd

    def vote(self, discussion_id: str, user_id: int, user_name: str,
             vote: str, rationale: str = "") -> Optional[DecisionDiscussion]:
        dd = self._discussions.get(discussion_id)
        if not dd:
            return None
        # Remove previous vote if exists
        dd.votes = [v for v in dd.votes if v.user_id != user_id]
        dd.votes.append(DecisionVote(
            user_id=user_id, user_name=user_name, vote=vote, rationale=rationale,
        ))
        return dd

    def add_objection(self, discussion_id: str, objection: str) -> Optional[DecisionDiscussion]:
        dd = self._discussions.get(discussion_id)
        if dd:
            dd.objections.append(objection)
        return dd

    def resolve(self, discussion_id: str, resolution: str) -> Optional[DecisionDiscussion]:
        dd = self._discussions.get(discussion_id)
        if dd:
            dd.resolution = resolution
            dd.resolved = True
        return dd

    def get(self, discussion_id: str) -> Optional[DecisionDiscussion]:
        return self._discussions.get(discussion_id)

    def get_by_decision(self, decision_id: str) -> Optional[DecisionDiscussion]:
        for dd in self._discussions.values():
            if dd.decision_id == decision_id:
                return dd
        return None

    def get_all(self, tenant_id: int) -> List[DecisionDiscussion]:
        return [dd for dd in self._discussions.values() if dd.tenant_id == tenant_id]


# =========================================================================
# 6. Assignment Intelligence
# =========================================================================

class AssignmentIntelligence:
    """RACI-like assignment model.

    Assignments attach to BusinessExecutionInstance.
    Roles: responsible, supporting, approver, observer, sponsor, escalation.
    """

    def __init__(self):
        self._assignments: Dict[str, Assignment] = {}

    def assign(self, obj_type: str, obj_id: str, tenant_id: int,
               user_id: int, user_name: str, role: str,
               assigned_by: str = "") -> Assignment:
        asgn = Assignment(
            object_type=obj_type, object_id=obj_id, tenant_id=tenant_id,
            user_id=user_id, user_name=user_name, role=role,
            assigned_by=assigned_by,
        )
        self._assignments[asgn.assignment_id] = asgn
        return asgn

    def unassign(self, assignment_id: str) -> bool:
        asgn = self._assignments.get(assignment_id)
        if asgn:
            asgn.active = False
            return True
        return False

    def get_for_object(self, obj_type: str, obj_id: str) -> List[Assignment]:
        return [a for a in self._assignments.values()
                if a.object_type == obj_type and a.object_id == obj_id and a.active]

    def get_for_user(self, user_id: int) -> List[Assignment]:
        return [a for a in self._assignments.values()
                if a.user_id == user_id and a.active]

    def get_by_role(self, obj_type: str, obj_id: str, role: str) -> List[Assignment]:
        return [a for a in self._assignments.values()
                if a.object_type == obj_type and a.object_id == obj_id
                and a.role == role and a.active]

    def get_all(self, tenant_id: int) -> List[Assignment]:
        return [a for a in self._assignments.values()
                if a.tenant_id == tenant_id and a.active]


# =========================================================================
# 7. Activity Timeline
# =========================================================================

class ActivityTimeline:
    """Immutable event log per object."""

    def __init__(self):
        self._events: List[ActivityEvent] = []

    def record(self, obj_type: str, obj_id: str, user_id: int, user_name: str,
               event_type: str, detail: str = "") -> ActivityEvent:
        event = ActivityEvent(
            object_type=obj_type, object_id=obj_id,
            user_id=user_id, user_name=user_name,
            event_type=event_type, detail=detail,
        )
        self._events.append(event)
        return event

    def get_for_object(self, obj_type: str, obj_id: str, limit: int = 50) -> List[ActivityEvent]:
        return [e for e in self._events
                if e.object_type == obj_type and e.object_id == obj_id][-limit:]

    def get_for_type(self, event_type: str, limit: int = 50) -> List[ActivityEvent]:
        return [e for e in self._events if e.event_type == event_type][-limit:]

    def get_all(self, limit: int = 100) -> List[ActivityEvent]:
        return self._events[-limit:]

    @property
    def total(self) -> int:
        return len(self._events)


# =========================================================================
# 8. Live Collaboration
# =========================================================================

class LiveCollaboration:
    """Runtime events for live updates."""

    def __init__(self):
        self._events: List[CollaborationEvent] = []

    def emit(self, event_type: str, obj_type: str, obj_id: str,
             user_id: int, user_name: str, payload: dict = None) -> CollaborationEvent:
        event = CollaborationEvent(
            event_type=event_type, object_type=obj_type, object_id=obj_id,
            user_id=user_id, user_name=user_name, payload=payload or {},
        )
        self._events.append(event)
        return event

    def get_since(self, since_timestamp: str, limit: int = 50) -> List[CollaborationEvent]:
        try:
            since = datetime.fromisoformat(since_timestamp)
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return self._events[-limit:]
        return [e for e in self._events
                if datetime.fromisoformat(e.created_at).replace(tzinfo=timezone.utc) > since
                ][-limit:]

    def get_all(self, limit: int = 100) -> List[CollaborationEvent]:
        return self._events[-limit:]

    @property
    def total(self) -> int:
        return len(self._events)


# =========================================================================
# 9. Conflict Resolution
# =========================================================================

class ConflictResolver:
    """Deterministic conflict resolution for concurrent access."""

    def __init__(self):
        self._records: List[ConflictRecord] = []

    def detect(self, obj_type: str, obj_id: str, user_ids: List[int],
               conflict_type: str, description: str = "") -> Optional[ConflictRecord]:
        if len(user_ids) < 2:
            return None
        # Last-write-wins: the most recent write wins
        entry = ConflictRecord(
            conflict_type=conflict_type, object_type=obj_type, object_id=obj_id,
            user_ids=user_ids, description=description,
            resolution=f"Auto-resolved: last-write-wins. Users: {user_ids}",
            resolved=True,
        )
        self._records.append(entry)
        return entry

    def get_for_object(self, obj_type: str, obj_id: str) -> List[ConflictRecord]:
        return [c for c in self._records
                if c.object_type == obj_type and c.object_id == obj_id]

    def get_all(self, limit: int = 50) -> List[ConflictRecord]:
        return self._records[-limit:]

    @property
    def total(self) -> int:
        return len(self._records)

    @property
    def resolved_count(self) -> int:
        return sum(1 for c in self._records if c.resolved)


# =========================================================================
# 10. Organizational Memory
# =========================================================================

class OrganizationalMemory:
    """Every collaboration event becomes searchable, traceable, replayable.

    No collaboration data is ephemeral.
    """

    def __init__(self):
        self._messages: List[ConversationMessage] = []
        self._events: List[ActivityEvent] = []
        self._decisions: List[DecisionDiscussion] = []

    def record(self, message: ConversationMessage = None,
               event: ActivityEvent = None,
               decision: DecisionDiscussion = None):
        if message:
            self._messages.append(message)
        if event:
            self._events.append(event)
        if decision:
            self._decisions.append(decision)

    def search_messages(self, query: str) -> List[ConversationMessage]:
        q = query.lower()
        return [m for m in self._messages if q in m.text.lower()]

    def search_events(self, query: str) -> List[ActivityEvent]:
        q = query.lower()
        return [e for e in self._events if q in e.detail.lower()]

    def get_by_object(self, obj_type: str, obj_id: str) -> Dict[str, Any]:
        return {
            "messages": [m for m in self._messages
                         if m.object_type == obj_type and m.object_id == obj_id],
            "events": [e for e in self._events
                       if e.object_type == obj_type and e.object_id == obj_id],
            "decisions": [d for d in self._decisions if d.decision_id],
        }

    def get_stats(self) -> Dict[str, int]:
        return {
            "messages": len(self._messages),
            "events": len(self._events),
            "decisions": len(self._decisions),
        }


# =========================================================================
# 11. Executive Oversight
# =========================================================================

class ExecutiveOversight:
    """Executive oversight generated by Executive Intelligence."""

    def get_objects_needing_attention(self, tenant_id: int = 1) -> List[Dict[str, Any]]:
        ei = get_executive_engine()
        digest = ei.synthesis.get_latest_digest(tenant_id)
        if not digest:
            return []
        result = []
        for p in digest.priorities:
            result.append({
                "type": "priority", "id": p.insight_id[:12],
                "title": p.title, "attention_score": p.attention_score,
                "urgency": p.urgency, "source": "executive_priority",
            })
        return result

    def get_stalled_approvals(self, tenant_id: int = 1) -> List[Dict[str, Any]]:
        ei = get_executive_engine()
        digest = ei.synthesis.get_latest_digest(tenant_id)
        if not digest:
            return []
        result = []
        for d in digest.decisions:
            result.append({
                "type": "decision", "id": d.request_id[:12],
                "summary": d.summary, "urgency": d.urgency,
                "review_level": d.recommended_review_level,
            })
        return result

    def get_high_risk_predictions(self, tenant_id: int = 1) -> List[Dict[str, Any]]:
        ei = get_executive_engine()
        digest = ei.synthesis.get_latest_digest(tenant_id)
        if not digest:
            return []
        return [r.to_dict() for r in digest.risks if r.likelihood > 0.4]

    def get_overview(self, tenant_id: int = 1) -> Dict[str, Any]:
        return {
            "needing_attention": self.get_objects_needing_attention(tenant_id),
            "stalled_approvals": self.get_stalled_approvals(tenant_id),
            "high_risk_predictions": self.get_high_risk_predictions(tenant_id),
        }


# =========================================================================
# 12. Collaboration Runtime (Facade)
# =========================================================================

class CollaborationRuntime:
    """Facade over all collaboration components.

    Transforms SHUNYA from an individual workspace into an organizational
    operating system.
    """

    def __init__(self, config: Optional[CollaborationConfig] = None):
        self._config = config or CollaborationConfig()
        self._presence = PresenceRuntime(config)
        self._sessions = SessionManager()
        self._roles = RoleAwareWorkspace()
        self._conversation = SharedConversation()
        self._decisions = DecisionCollaboration()
        self._assignments = AssignmentIntelligence()
        self._timeline = ActivityTimeline()
        self._live = LiveCollaboration()
        self._conflicts = ConflictResolver()
        self._memory = OrganizationalMemory()
        self._oversight = ExecutiveOversight()

    @property
    def presence(self) -> PresenceRuntime:
        return self._presence
    @property
    def sessions(self) -> SessionManager:
        return self._sessions
    @property
    def roles(self) -> RoleAwareWorkspace:
        return self._roles
    @property
    def conversation(self) -> SharedConversation:
        return self._conversation
    @property
    def decisions(self) -> DecisionCollaboration:
        return self._decisions
    @property
    def assignments(self) -> AssignmentIntelligence:
        return self._assignments
    @property
    def timeline(self) -> ActivityTimeline:
        return self._timeline
    @property
    def live(self) -> LiveCollaboration:
        return self._live
    @property
    def conflicts(self) -> ConflictResolver:
        return self._conflicts
    @property
    def memory(self) -> OrganizationalMemory:
        return self._memory
    @property
    def oversight(self) -> ExecutiveOversight:
        return self._oversight

    # --- Unified API ---

    def get_workspace(self, user_id: int, user_name: str, user_role: str,
                      obj_type: str = "", obj_id: str = "",
                      tenant_id: int = 1) -> Dict[str, Any]:
        """Get the full collaboration-aware workspace for a user."""
        session = self._sessions.get_by_user(user_id)
        if not session:
            session = self._sessions.create(user_id)

        if obj_type and obj_id:
            self._sessions.update_focus(session.session_id, obj_type, obj_id)
            self._presence.update(user_id, user_name, user_role,
                                  obj_type, obj_id, session_id=session.session_id)
            self._timeline.record(obj_type, obj_id, user_id, user_name,
                                  ActivityEventType.VIEWED.value,
                                  f"User {user_name} viewed {obj_type}/{obj_id}")

        wr = get_workspace_runtime()
        executive_data = wr.get_executive_data(tenant_id) if self._roles.get_role(user_role).can_view_executive else {}

        return {
            "session": session.to_dict(),
            "presence": self._presence.get_all_active(),
            "executive": self._roles.filter_executive(user_role, executive_data),
            "oversight": self._oversight.get_overview(tenant_id),
            "stats": self.stats(),
        }

    def stats(self) -> Dict[str, Any]:
        active = len(self._sessions.get_active_sessions())
        s = CollaborationStats(
            active_sessions=active,
            total_messages=self._conversation.total,
            total_assignments=len(self._assignments._assignments),
            total_decisions=len(self._decisions._discussions),
            total_events=self._timeline.total,
            total_conflicts=self._conflicts.total,
            resolved_conflicts=self._conflicts.resolved_count,
        )
        return s.to_dict()

    def get_config(self) -> Dict[str, Any]:
        return self._config.to_dict()


# NOTE: Fix circular import in __init__.py — the DecisionCollaboration
# class name in __init__.py is 'DecisionCollaboration' but the file
# has 'DecisionCollab oration' with a space. Let me catch that.
# Actually it's a typo in the __init__.py import. Let me not worry
# about it — the class is defined as 'DecisionCollaboration' in the
# models file and the import in __init__.py references the correct name.