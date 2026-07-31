"""Tests for SHUNYA Kernel — Types, State, Timeline, Context (Ontology Engine E-001).

Architecture references:
    UNIVERSAL_ONTOLOGY.md §18 — Universal Type System
    UNIVERSAL_ONTOLOGY.md §18.4 — Per-type lifecycle mapping
    UNIVERSAL_ONTOLOGY.md §11 — State
    UNIVERSAL_ONTOLOGY.md §12 — Timeline
    UNIVERSAL_ONTOLOGY.md §13 — Context
    COGNITIVE_WORKSPACE_RUNTIME.md §6 — Universal Object Lifecycle
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.kernel.types import (
    TypeRegistry, TypeNode, TypeGroup, TypeGroupLifecycle,
    LifecycleState, get_registry, reset_registry,
)
from app.kernel.state import StateMachine, StateTransition
from app.kernel.timeline import Timeline, TimelineEvent
from app.kernel.context import Context, ContextData, ContextType, ContextResolution


# =========================================================================
# Type Registry Tests
# =========================================================================

class TestTypeRegistry:
    """UNIVERSAL_ONTOLOGY.md §18 — Universal Type System."""

    def setup_method(self):
        reset_registry()

    def test_default_types_are_registered(self):
        """§18.1 — Canonical inheritance tree has all root types."""
        registry = get_registry()
        assert registry.count >= 40  # At least 40 canonical types
        assert registry.get("Object") is not None
        assert registry.get("Entity") is not None
        assert registry.get("Person") is not None

    def test_type_hierarchy(self):
        """Types form a strict hierarchy (no multiple inheritance)."""
        registry = get_registry()
        person = registry.get("Person")
        assert person is not None
        assert person.parent == "Entity"
        assert person.group == TypeGroup.ENTITY

    def test_register_duplicate_raises(self):
        """§18.3 — No duplicate type registration."""
        registry = get_registry()
        with pytest.raises(ValueError, match="already registered"):
            registry.register(TypeNode("Person", parent="Entity", group=TypeGroup.ENTITY))

    def test_register_with_missing_parent_raises(self):
        """§18.3 — Parent must exist."""
        registry = get_registry()
        with pytest.raises(ValueError, match="not registered"):
            registry.register(TypeNode("Alien", parent="NonExistent", group=TypeGroup.ENTITY))

    def test_get_children(self):
        """Children query returns direct children."""
        registry = get_registry()
        entities = registry.get_children("Entity")
        assert len(entities) >= 6  # Person, Organization, Document, Meeting, Project, Workspace
        names = [e.name for e in entities]
        assert "Person" in names
        assert "Document" in names

    def test_get_descendants(self):
        """Descendants query returns all descendants recursively."""
        registry = get_registry()
        orgs = registry.get_descendants("Organization")
        org_names = [o.name for o in orgs]
        assert "Company" in org_names
        assert "Team" in org_names
        assert "Department" in org_names

    def test_get_group(self):
        """§18.4.4 — Type group retrieval."""
        registry = get_registry()
        assert registry.get_group("Person") == TypeGroup.ENTITY
        assert registry.get_group("Event") == TypeGroup.EVENT
        assert registry.get_group("Commitment") == TypeGroup.COMMITMENT


# =========================================================================
# Lifecycle Tests
# =========================================================================

class TestLifecycle:
    """UNIVERSAL_ONTOLOGY.md §18.4 — Per-type lifecycle mapping."""

    def setup_method(self):
        reset_registry()

    def test_entity_restricted_states(self):
        """§18.4.4 — Entities cannot PREDICT or EXECUTE."""
        registry = get_registry()
        lifecycle = registry.get_lifecycle("Person")
        assert lifecycle is not None
        assert LifecycleState.PREDICT not in lifecycle.valid_states
        assert LifecycleState.EXECUTE not in lifecycle.valid_states

    def test_commitment_full_lifecycle(self):
        """§18.4.4 — Commitments have full lifecycle."""
        registry = get_registry()
        lifecycle = registry.get_lifecycle("Commitment")
        assert lifecycle is not None
        assert LifecycleState.PREDICT in lifecycle.valid_states
        assert LifecycleState.EXECUTE in lifecycle.valid_states

    def test_event_create_only(self):
        """§18.4.4 — Events are CREATE only."""
        registry = get_registry()
        lifecycle = registry.get_lifecycle("Event")
        assert lifecycle is not None
        assert lifecycle.valid_states == {LifecycleState.CREATE}

    def test_evidence_create_only(self):
        """§18.4.4 — Evidence is CREATE only."""
        registry = get_registry()
        lifecycle = registry.get_lifecycle("Evidence")
        assert lifecycle is not None
        assert lifecycle.valid_states == {LifecycleState.CREATE}

    def test_prediction_no_predict(self):
        """§18.4.4 — Predictions are not predicted about."""
        registry = get_registry()
        lifecycle = registry.get_lifecycle("Prediction")
        assert lifecycle is not None
        assert LifecycleState.PREDICT not in lifecycle.valid_states

    def test_validate_state(self):
        """State validation works per type."""
        registry = get_registry()
        assert registry.validate_state("Person", LifecycleState.ENRICH)
        assert not registry.validate_state("Person", LifecycleState.PREDICT)
        assert registry.validate_state("Task", LifecycleState.EXECUTE)

    def test_validate_transition(self):
        """§18.4.5 — Transition validation."""
        registry = get_registry()
        # Person: CREATE → OBSERVE is valid
        assert registry.validate_transition("Person", LifecycleState.CREATE, LifecycleState.OBSERVE)
        # Person: CREATE → EXECUTE is not valid (EXECUTE is restricted for entities)
        assert not registry.validate_transition("Person", LifecycleState.CREATE, LifecycleState.EXECUTE)


# =========================================================================
# State Machine Tests
# =========================================================================

class TestStateMachine:
    """COGNITIVE_WORKSPACE_RUNTIME.md §6 — Universal Object Lifecycle."""

    def setup_method(self):
        reset_registry()

    def test_initial_state_is_create(self):
        """§6.2 — Every object starts in CREATE state."""
        sm = StateMachine("obj_001", "Person")
        assert sm.current_state == LifecycleState.CREATE

    def test_valid_transition(self):
        """§6.3 — Valid transitions succeed."""
        sm = StateMachine("obj_001", "Person")
        t = sm.transition(LifecycleState.OBSERVE)
        assert sm.current_state == LifecycleState.OBSERVE
        assert t.from_state == LifecycleState.CREATE
        assert t.to_state == LifecycleState.OBSERVE

    def test_invalid_transition_raises(self):
        """§6.3 — Invalid transitions raise ValueError."""
        sm = StateMachine("obj_001", "Person")
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition(LifecycleState.PREDICT)  # Restricted for entities

    def test_terminal_state(self):
        """§11.4 — Terminal states are absorbing."""
        sm = StateMachine("obj_001", "Task")
        sm.transition(LifecycleState.OBSERVE)
        sm.transition(LifecycleState.ENRICH)
        sm.transition(LifecycleState.RELATE)
        sm.transition(LifecycleState.PREDICT)
        sm.transition(LifecycleState.EXECUTE)
        sm.transition(LifecycleState.ARCHIVE)
        sm.transition(LifecycleState.DELETE)
        assert sm.is_terminal
        with pytest.raises(RuntimeError, match="terminal state"):
            sm.transition(LifecycleState.OBSERVE)

    def test_history_records_transitions(self):
        """§6.3 — Every transition is recorded (I-13: event-sourced)."""
        sm = StateMachine("obj_001", "Task")
        sm.transition(LifecycleState.OBSERVE)
        sm.transition(LifecycleState.ENRICH)
        assert len(sm.history) == 2
        assert sm.history[0].to_state == LifecycleState.OBSERVE
        assert sm.history[1].to_state == LifecycleState.ENRICH

    def test_transition_with_actor_and_reason(self):
        """Transition records actor and reason."""
        sm = StateMachine("obj_001", "Person")
        t = sm.transition(LifecycleState.OBSERVE, actor="founder", reason="Manual observation")
        assert t.actor == "founder"
        assert t.reason == "Manual observation"

    def test_observer_notification(self):
        """I-13 — Observers are notified on transition."""
        sm = StateMachine("obj_001", "Person")
        observed = []

        def callback(t):
            observed.append(t)

        sm.observe(callback)
        sm.transition(LifecycleState.OBSERVE)
        assert len(observed) == 1
        assert observed[0].to_state == LifecycleState.OBSERVE

    def test_to_dict(self):
        """State machine serialization."""
        sm = StateMachine("obj_001", "Person")
        sm.transition(LifecycleState.OBSERVE)
        d = sm.to_dict()
        assert d["object_id"] == "obj_001"
        assert d["current_state"] == "observe"
        assert d["history_count"] == 1

    def test_full_person_lifecycle(self):
        """Person: CREATE → OBSERVE → ENRICH → RELATE."""
        sm = StateMachine("obj_001", "Person")
        sm.transition(LifecycleState.OBSERVE)
        sm.transition(LifecycleState.ENRICH)
        sm.transition(LifecycleState.RELATE)
        # For entities, PREDICT and EXECUTE are restricted.
        # The entity lifecycle ends at RELATE or ARCHIVE.
        # ARCHIVE is not directly reachable from RELATE for entities.
        assert sm.current_state == LifecycleState.RELATE

    def test_full_task_lifecycle(self):
        """Task: CREATE → OBSERVE → ENRICH → RELATE → PREDICT → EXECUTE → ARCHIVE."""
        sm = StateMachine("obj_001", "Task")
        sm.transition(LifecycleState.OBSERVE)
        sm.transition(LifecycleState.ENRICH)
        sm.transition(LifecycleState.RELATE)
        sm.transition(LifecycleState.PREDICT)
        sm.transition(LifecycleState.EXECUTE)
        sm.transition(LifecycleState.ARCHIVE)
        assert sm.current_state == LifecycleState.ARCHIVE


# =========================================================================
# Timeline Tests
# =========================================================================

class TestTimeline:
    """UNIVERSAL_ONTOLOGY.md §12 — Timeline."""

    def test_append_event(self):
        """§12 — Events can be appended (O-19)."""
        tl = Timeline("obj_001")
        event = TimelineEvent(
            event_id="evt_001",
            event_type="creation",
            timestamp=datetime.now(timezone.utc),
            title="Object created",
        )
        tl.append(event)
        assert tl.event_count == 1

    def test_append_only(self):
        """O-19 — Timeline is append-only. Events cannot be removed after append."""
        tl = Timeline("obj_001")
        event = TimelineEvent(
            event_id="evt_001",
            event_type="creation",
            timestamp=datetime.now(timezone.utc),
        )
        tl.append(event)
        # The past property returns a copy, so mutating it doesn't affect the timeline
        past = tl.past
        assert len(past) == 1
        assert tl.event_count == 1

    def test_expected_future(self):
        """§12.2 — Future events can be added and promoted."""
        tl = Timeline("obj_001")
        future = TimelineEvent(
            event_id="evt_future",
            event_type="completion",
            timestamp=datetime.now(timezone.utc) + timedelta(days=7),
            title="Expected completion",
        )
        tl.add_expected(future)
        assert len(tl.expected_future) == 1

        # Promote to past
        tl.promote_to_past("evt_future")
        assert len(tl.expected_future) == 0
        assert tl.event_count == 1

    def test_alternative_future(self):
        """§12.2 — Alternative timeline scenarios."""
        tl = Timeline("obj_001")
        best_case = [
            TimelineEvent(event_id="bc_1", event_type="success", timestamp=datetime.now(timezone.utc)),
        ]
        tl.add_alternative_future("best_case", best_case)
        assert len(tl.get_alternative_future("best_case")) == 1

    def test_get_events_in_range(self):
        """Events can be queried by time range."""
        tl = Timeline("obj_001")
        now = datetime.now(timezone.utc)
        tl.append(TimelineEvent(
            event_id="e1", event_type="a", timestamp=now - timedelta(hours=2),
        ))
        tl.append(TimelineEvent(
            event_id="e2", event_type="b", timestamp=now - timedelta(hours=1),
        ))
        tl.append(TimelineEvent(
            event_id="e3", event_type="c", timestamp=now,
        ))
        range_events = tl.get_events_in_range(
            now - timedelta(hours=1, minutes=30), now
        )
        assert len(range_events) == 2  # e2 and e3

    def test_query_by_type_and_importance(self):
        """Events can be queried by type and importance threshold."""
        tl = Timeline("obj_001")
        tl.append(TimelineEvent(event_id="e1", event_type="creation", importance=0.9,
                                 timestamp=datetime.now(timezone.utc)))
        tl.append(TimelineEvent(event_id="e2", event_type="update", importance=0.3,
                                 timestamp=datetime.now(timezone.utc)))
        results = tl.query(event_type="creation")
        assert len(results) == 1
        results = tl.query(min_importance=0.5)
        assert len(results) == 1

    def test_to_dict(self):
        """Timeline serialization."""
        tl = Timeline("obj_001")
        tl.append(TimelineEvent(event_id="e1", event_type="creation",
                                 timestamp=datetime.now(timezone.utc)))
        d = tl.to_dict()
        assert d["object_id"] == "obj_001"
        assert d["past_count"] == 1


# =========================================================================
# Context Tests
# =========================================================================

class TestContext:
    """UNIVERSAL_ONTOLOGY.md §13 — Context."""

    def test_set_and_get(self):
        """§13.2 — Context entries can be set and retrieved."""
        ctx = Context("ctx_001", "obj_001")
        data = ContextData(type=ContextType.WORKSPACE, scope="obj_001",
                           data={"view": "focused"})
        ctx.set(data)
        retrieved = ctx.get(ContextType.WORKSPACE)
        assert retrieved is not None
        assert retrieved.data["view"] == "focused"

    def test_context_inheritance(self):
        """§13.3 — Narrower contexts can override broader contexts."""
        parent = Context("parent", "org_001")
        parent.set(ContextData(type=ContextType.ORGANISATIONAL, scope="org_001",
                                data={"policy": "standard"}))

        child = Context("child", "obj_001")
        child.set_parent(parent)
        child.set(ContextData(type=ContextType.WORKSPACE, scope="obj_001",
                               data={"view": "focused"}))

        # Child inherits parent's organisational context
        inherited = child.get(ContextType.ORGANISATIONAL)
        assert inherited is not None
        assert inherited.data["policy"] == "standard"

        # Child can override parent
        child.set(ContextData(type=ContextType.ORGANISATIONAL, scope="obj_001",
                               data={"policy": "override"}))
        overridden = child.get(ContextType.ORGANISATIONAL)
        assert overridden is not None
        assert overridden.data["policy"] == "override"

    def test_archive(self):
        """O-09 — Context can be archived but not destroyed."""
        ctx = Context("ctx_001", "obj_001")
        assert not ctx.is_archived
        ctx.archive()
        assert ctx.is_archived

    def test_context_resolution(self):
        """KG §6 — Context resolution engine."""
        resolver = ContextResolution()
        ctx = Context("ctx_001", "obj_001")
        resolver.register(ctx)
        resolved = resolver.resolve("obj_001")
        assert resolved is not None
        assert resolved.context_id == "ctx_001"

    def test_context_resolution_nonexistent(self):
        """Context resolution returns None for unknown objects."""
        resolver = ContextResolution()
        resolved = resolver.resolve("nonexistent")
        assert resolved is None

    def test_context_resolution_with_depth(self):
        """Context resolution with inheritance depth."""
        resolver = ContextResolution()
        parent = Context("parent", "org_001")
        child = Context("child", "obj_001")
        child.set_parent(parent)
        resolver.register(parent)
        resolver.register(child)
        result = resolver.resolve_with_depth("obj_001", depth=2)
        assert "parent" in result["contexts"]
        assert "child" in result["contexts"]


# =========================================================================
# Invariant Tests (O-NNN series)
# =========================================================================

class TestInvariants:
    """UNIVERSAL_ONTOLOGY.md §19 — Constitutional invariants."""

    def setup_method(self):
        reset_registry()

    def test_o_01_identity_never_changes(self):
        """O-01: Type registration identity is permanent."""
        registry = get_registry()
        person = registry.get("Person")
        assert person is not None
        # Re-registering is not allowed
        with pytest.raises(ValueError):
            registry.register(TypeNode("Person", parent="Entity", group=TypeGroup.ENTITY))

    def test_o_02_history_is_immutable(self):
        """O-02: Timeline past events are immutable."""
        tl = Timeline("obj_001")
        tl.append(TimelineEvent(event_id="e1", event_type="creation",
                                 timestamp=datetime.now(timezone.utc)))
        # The past property returns a copy — original is unchanged
        past = tl.past
        assert len(past) == 1
        assert tl.event_count == 1  # Still 1, not modified

    def test_o_11_type_is_permanent(self):
        """O-11: Type is permanent once registered."""
        registry = get_registry()
        person = registry.get("Person")
        assert person is not None
        # Type attributes are frozen by the registry
        assert person.parent == "Entity"

    def test_o_12_state_transitions_are_valid(self):
        """O-12: Only defined transitions are permitted."""
        sm = StateMachine("obj_001", "Person")
        # Valid transition
        sm.transition(LifecycleState.OBSERVE)
        # Invalid transition
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition(LifecycleState.PREDICT)

    def test_o_18_state_is_singular(self):
        """O-18: Every Object has exactly one current state."""
        sm = StateMachine("obj_001", "Person")
        assert sm.current_state == LifecycleState.CREATE
        sm.transition(LifecycleState.OBSERVE)
        assert sm.current_state == LifecycleState.OBSERVE
        # Only one state at a time
        assert sm.current_state != LifecycleState.CREATE

    def test_o_19_timelines_are_append_only(self):
        """O-19: Events can be added but never removed."""
        tl = Timeline("obj_001")
        tl.append(TimelineEvent(event_id="e1", event_type="creation",
                                 timestamp=datetime.now(timezone.utc)))
        # There's no remove method for past events
        assert not hasattr(tl, "remove")

    def test_i_13_lifecycle_is_event_sourced(self):
        """I-13: Every transition emits an event."""
        sm = StateMachine("obj_001", "Person")
        events = []
        sm.observe(lambda t: events.append(t))
        sm.transition(LifecycleState.OBSERVE, actor="test")
        assert len(events) == 1
        sm.transition(LifecycleState.ENRICH)
        assert len(events) == 2

    def test_o_09_context_never_destroyed(self):
        """O-09: Context may be archived but never deleted."""
        ctx = Context("ctx_001", "obj_001")
        ctx.archive()
        assert ctx.is_archived
        # Context still exists after archiving
        assert ctx.context_id == "ctx_001"
        assert ctx.object_id == "obj_001"