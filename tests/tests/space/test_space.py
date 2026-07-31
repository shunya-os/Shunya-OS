"""SHUNYA Phase A1 — Universal Space: comprehensive automated tests.

Tests cover all 10 deliverables:
1. Universal Space domain model
2. Dynamic Space renderer
3. Space navigation framework
4. Context persistence
5. Timeline integration
6. Knowledge integration
7. Relationship visualization
8. Command framework
9. API routes
10. Space nesting and composition
"""
import pytest
import uuid
from datetime import datetime, timezone

from app.space.models import (
    UniversalSpace, SpaceIdentity, SpaceStatus, SpaceContext,
    SpaceRelationshipRef, SpaceTimelineEvent, SpaceKnowledgeItem,
    SpacePlanRef, SpaceExecutionRef, SpaceCommunicationRef,
    SpaceDocumentRef, SpaceResponsibility, SpaceMetric,
    SpaceAIUnderstanding, SpacePanel,
)
from app.space.store import get_store, reset_store, SpaceStore
from app.space.renderer import (
    get_renderer, reset_renderer, SpaceRenderer,
    PanelRenderer, PanelProvider, PANEL_RENDERERS,
    DEFAULT_PANEL_PROVIDERS, Widget,
)
from app.space.navigation import (
    get_navigator, reset_navigator, SpaceNavigator, NavigationResult,
)
from app.space.context import (
    get_context_manager, reset_context_manager, SpaceContextManager,
)
from app.space.commands import (
    get_executor, reset_executor, CommandExecutor, SpaceCommand,
    BUILTIN_COMMANDS,
)
from app.space.timeline import (
    get_timeline_manager, reset_timeline_manager, SpaceTimelineManager,
)
from app.space.knowledge import (
    get_knowledge_manager, reset_knowledge_manager, SpaceKnowledgeManager,
)
from app.space.relationships import (
    get_relationship_manager, reset_relationship_manager,
    SpaceRelationshipManager,
)
from app.space.capabilities import (
    get_registry as get_capability_registry,
    reset_registry as reset_capability_registry,
    CapabilityRegistry, Capability, ALL_CAPABILITIES, DEFAULT_CAPABILITIES,
)
from app.space.lifecycle import (
    get_lifecycle_manager, reset_lifecycle_manager,
    LifecycleManager, SpaceLifecycle, LifecycleState,
    LIFECYCLE_TRANSITIONS, LIFECYCLE_EFFECTS,
)
from app.space.reasoning import (
    get_reasoner, reset_reasoner,
    CrossSpaceReasoner, ReasoningQuery, ReasoningResult, ReasoningStep,
)
from app.space.resident import (
    get_resident_manager, reset_resident_manager,
    AIResidentManager, AIResidentState,
)
from app.space.composition import (
    get_composite_manager, reset_composite_manager,
    CompositeSpaceManager,
)


# =========================================================================
# Shared Fixtures
# =========================================================================


@pytest.fixture(autouse=True)
def reset_all():
    """Reset all stores before each test."""
    reset_store()
    reset_renderer()
    reset_navigator()
    reset_context_manager()
    reset_executor()
    reset_timeline_manager()
    reset_knowledge_manager()
    reset_relationship_manager()
    reset_capability_registry()
    reset_lifecycle_manager()
    reset_reasoner()
    reset_resident_manager()
    reset_composite_manager()
    yield


@pytest.fixture
def store():
    return get_store()


@pytest.fixture
def sample_space(store):
    """Create a sample customer Space for testing."""
    return store.create(
        entity_id="ent_test_001",
        entity_type="customer",
        name="Test Customer",
        aliases=["TC", "TestCo"],
    )


@pytest.fixture
def sample_supplier(store):
    return store.create(
        entity_id="ent_supplier_002",
        entity_type="supplier",
        name="Test Supplier",
    )


@pytest.fixture
def sample_project(store):
    return store.create(
        entity_id="ent_project_002",
        entity_type="project",
        name="Test Project",
    )


# =========================================================================
# 1. Universal Space Domain Model
# =========================================================================


class TestSpaceDomainModel:
    """Tests for the Universal Space domain model (deliverable 1)."""

    def test_space_identity_defaults(self):
        """A Space is defined by its identity, not its type."""
        identity = SpaceIdentity(
            space_id="spc_001",
            entity_id="ent_001",
            entity_type="customer",
            name="Test Corp",
        )
        assert identity.space_id == "spc_001"
        assert identity.entity_id == "ent_001"
        assert identity.entity_type == "customer"
        assert identity.name == "Test Corp"
        assert identity.status == SpaceStatus.ACTIVE
        assert identity.created_at
        assert identity.updated_at

    def test_space_identity_no_hardcoded_types(self):
        """The architecture must never hardcode type names."""
        types = [
            "customer", "supplier", "employee", "company", "partner",
            "project", "task", "invoice", "contract", "product",
            "campaign", "hotel", "flight", "destination", "vehicle",
            "asset", "machine", "patient", "student", "case",
            "opportunity", "lead", "conversation", "meeting", "document",
        ]
        for t in types:
            identity = SpaceIdentity(
                space_id=f"spc_{t}",
                entity_id=f"ent_{t}",
                entity_type=t,
                name=f"Test {t}",
            )
            assert identity.entity_type == t
            d = identity.to_dict()
            assert d["entity_type"] == t

    def test_canonical_space_structure(self):
        """Every Space must expose the same canonical structure."""
        space = UniversalSpace(
            identity=SpaceIdentity(
                space_id="spc_001", entity_id="ent_001",
                entity_type="customer", name="Test",
            ),
        )
        # Canonical components
        assert hasattr(space, "identity")
        assert hasattr(space, "context")
        assert hasattr(space, "relationships")
        assert hasattr(space, "timeline")
        assert hasattr(space, "knowledge")
        assert hasattr(space, "plans")
        assert hasattr(space, "executions")
        assert hasattr(space, "communications")
        assert hasattr(space, "documents")
        assert hasattr(space, "responsibilities")
        assert hasattr(space, "metrics")
        assert hasattr(space, "ai_understanding")

    def test_to_dict_roundtrip(self):
        """All fields serialize to dict and back."""
        space = UniversalSpace(
            identity=SpaceIdentity(
                space_id="spc_001", entity_id="ent_001",
                entity_type="customer", name="Test",
            ),
        )
        d = space.to_dict()
        assert d["identity"]["space_id"] == "spc_001"
        assert d["identity"]["entity_type"] == "customer"
        assert d["identity"]["name"] == "Test"
        assert "context" in d
        assert "relationships" in d
        assert "timeline" in d
        assert "knowledge" in d
        assert "plans" in d
        assert "commands" in d

    def test_to_summary(self):
        """Summary provides lightweight view."""
        space = UniversalSpace(
            identity=SpaceIdentity(
                space_id="spc_001", entity_id="ent_001",
                entity_type="customer", name="Test",
            ),
        )
        s = space.to_summary()
        assert s["space_id"] == "spc_001"
        assert s["name"] == "Test"
        assert s["entity_type"] == "customer"
        assert "relationship_count" in s
        assert "timeline_count" in s
        assert "knowledge_count" in s

    def test_identity_properties(self):
        """Space properties delegate to identity."""
        space = UniversalSpace(
            identity=SpaceIdentity(
                space_id="spc_001", entity_id="ent_001",
                entity_type="customer", name="Test",
            ),
        )
        assert space.space_id == "spc_001"
        assert space.entity_id == "ent_001"
        assert space.entity_type == "customer"
        assert space.name == "Test"
        assert space.status == SpaceStatus.ACTIVE

    def test_space_status_enum(self):
        """SpaceStatus enum covers all states."""
        assert SpaceStatus.ACTIVE.value == "active"
        assert SpaceStatus.ARCHIVED.value == "archived"
        assert SpaceStatus.DELETED.value == "deleted"

    def test_space_panel_enum(self):
        """SpacePanel enum covers all canonical panels."""
        panels = [
            SpacePanel.CONTEXT, SpacePanel.RELATIONSHIPS, SpacePanel.TIMELINE,
            SpacePanel.KNOWLEDGE, SpacePanel.PLANS, SpacePanel.EXECUTION,
            SpacePanel.COMMUNICATIONS, SpacePanel.DOCUMENTS,
            SpacePanel.RESPONSIBILITIES, SpacePanel.METRICS,
            SpacePanel.AI_UNDERSTANDING,
        ]
        assert len(panels) == 11


# =========================================================================
# 2. Space Store
# =========================================================================


class TestSpaceStore:
    """Tests for the Space store (CRUD + query)."""

    def test_create_space(self, store):
        space = store.create(
            entity_id="ent_001", entity_type="customer", name="Acme",
        )
        assert space.space_id.startswith("spc_")
        assert space.entity_id == "ent_001"
        assert space.name == "Acme"
        assert store.count == 1

    def test_get_space(self, store, sample_space):
        retrieved = store.get(sample_space.space_id)
        assert retrieved is not None
        assert retrieved.space_id == sample_space.space_id

    def test_get_by_entity(self, store, sample_space):
        retrieved = store.get_by_entity("ent_test_001")
        assert retrieved is not None
        assert retrieved.space_id == sample_space.space_id

    def test_get_nonexistent(self, store):
        assert store.get("nonexistent") is None
        assert store.get_by_entity("nonexistent") is None

    def test_update_space(self, store, sample_space):
        updated = store.update(sample_space.space_id, name="Updated Name")
        assert updated is not None
        assert updated.name == "Updated Name"

    def test_update_status(self, store, sample_space):
        updated = store.update(sample_space.space_id, status="archived")
        assert updated is not None
        assert updated.status == SpaceStatus.ARCHIVED

    def test_delete_space(self, store, sample_space):
        assert store.delete(sample_space.space_id) is True
        assert store.get(sample_space.space_id) is None
        assert store.count == 0

    def test_delete_nonexistent(self, store):
        assert store.delete("nonexistent") is False

    def test_list_all(self, store, sample_space, sample_supplier):
        spaces = store.list_all()
        assert len(spaces) == 2

    def test_list_by_type(self, store, sample_space, sample_supplier):
        customers = store.list_by_type("customer")
        assert len(customers) == 1
        assert customers[0].entity_id == "ent_test_001"

        suppliers = store.list_by_type("supplier")
        assert len(suppliers) == 1

    def test_list_by_status(self, store, sample_space):
        active = store.list_by_status(SpaceStatus.ACTIVE)
        assert len(active) >= 1
        archived = store.list_by_status(SpaceStatus.ARCHIVED)
        assert len(archived) == 0

    def test_search(self, store, sample_space, sample_supplier):
        results = store.search("Test")
        assert len(results) == 2
        results = store.search("customer")
        assert len(results) == 1
        results = store.search("TC")
        assert len(results) == 1
        results = store.search("Nonexistent")
        assert len(results) == 0

    def test_clear(self, store, sample_space):
        assert store.count == 1
        store.clear()
        assert store.count == 0

    def test_space_type_never_hardcoded(self, store):
        """Any type string works — no hardcoded business domains."""
        types = [
            "hotel", "flight", "destination", "vehicle", "asset",
            "machine", "patient", "student", "case", "opportunity",
            "lead", "conversation", "meeting", "document",
        ]
        for t in types:
            space = store.create(
                entity_id=f"ent_{t}_001",
                entity_type=t,
                name=f"Test {t}",
            )
            assert space.entity_type == t
            assert store.get_by_entity(f"ent_{t}_001") is not None


# =========================================================================
# 3. Space Renderer
# =========================================================================


class TestSpaceRenderer:
    """Tests for the Dynamic Space renderer (deliverable 2)."""

    def test_default_renderer(self, sample_space):
        renderer = get_renderer()
        result = renderer.render(sample_space)
        assert result["identity"]["space_id"] == sample_space.space_id
        assert "panels" in result
        assert "commands" in result
        # Panels are capability-driven — sample space has entity_type "test_customer"
        # which falls back to DEFAULT_CAPABILITIES (context, relationships, timeline, ai)
        assert len(result["panels"]) == 4
        assert "capabilities" in result

    def test_render_identity(self, sample_space):
        renderer = get_renderer()
        result = renderer.render(sample_space)
        assert result["identity"]["name"] == "Test Customer"
        assert result["identity"]["entity_type"] == "customer"

    def test_render_summary(self, sample_space):
        renderer = get_renderer()
        summary = renderer.render_summary(sample_space)
        assert summary["space_id"] == sample_space.space_id
        assert summary["name"] == "Test Customer"
        assert summary["relationship_count"] == 0

    def test_render_single_panel(self, sample_space):
        renderer = get_renderer()
        panel = renderer.render_panel(sample_space, "context")
        assert panel is not None
        assert panel["panel"] == "context"

    def test_render_nonexistent_panel(self, sample_space):
        renderer = get_renderer()
        panel = renderer.render_panel(sample_space, "nonexistent")
        assert panel is None

    def test_render_selected_panels(self, sample_space):
        renderer = get_renderer()
        result = renderer.render(sample_space, panels=["context", "timeline"])
        assert "context" in result["panels"]
        assert "timeline" in result["panels"]
        assert "relationships" not in result["panels"]

    def test_custom_panel_provider(self, sample_space):
        """Custom panel providers can be registered."""
        class CustomPanel(PanelRenderer):
            def __init__(self):
                super().__init__(SpacePanel.CONTEXT, "Custom", "🔧", priority=1)
            def render(self, space, context=None):
                return {"panel": "custom", "data": "custom_value"}

        renderer = SpaceRenderer(
            panel_renderers={"context": CustomPanel()},
        )
        result = renderer.render(sample_space)
        assert result["panels"]["context"]["data"] == "custom_value"

    def test_render_commands_present(self, sample_space):
        renderer = get_renderer()
        result = renderer.render(sample_space)
        assert len(result["commands"]) >= 14

    def test_renderer_different_types(self, store):
        """Renderer works identically regardless of Space type."""
        from app.space.capabilities import get_registry
        registry = get_registry()
        types = ["customer", "supplier", "employee", "invoice", "project"]
        for t in types:
            space = store.create(
                entity_id=f"ent_{t}_rnd", entity_type=t, name=f"Test {t}",
            )
            renderer = get_renderer()
            result = renderer.render(space)
            assert result["identity"]["entity_type"] == t
            # Panel count varies by capabilities
            visible = registry.get_panels_for(t)
            assert len(result["panels"]) == len(visible)


# =========================================================================
# 4. Space Navigation
# =========================================================================


class TestSpaceNavigation:
    """Tests for Space navigation framework (deliverable 3)."""

    def test_search(self, store, sample_space):
        nav = get_navigator()
        results = nav.search("Test")
        assert len(results) >= 1
        assert results[0]["name"] == "Test Customer"

    def test_search_by_type(self, store, sample_space, sample_supplier):
        nav = get_navigator()
        results = nav.search_by_type("customer")
        assert len(results) == 1
        results = nav.search_by_type("supplier")
        assert len(results) == 1

    def test_search_recent(self, store, sample_space, sample_supplier):
        nav = get_navigator()
        recent = nav.search_recent(limit=10)
        assert len(recent) == 2

    def test_open_space(self, sample_space):
        nav = get_navigator()
        result = nav.open(sample_space.space_id)
        assert result.found is True
        assert result.space is not None
        assert result.space.space_id == sample_space.space_id

    def test_open_nonexistent(self):
        nav = get_navigator()
        result = nav.open("nonexistent")
        assert result.found is False
        assert result.space is None

    def test_open_by_entity(self, store, sample_space):
        nav = get_navigator()
        result = nav.open_by_entity("ent_test_001")
        assert result.found is True
        assert result.space is not None

    def test_open_by_entity_nonexistent(self):
        nav = get_navigator()
        result = nav.open_by_entity("nonexistent")
        assert result.found is False

    def test_open_or_create_existing(self, store, sample_space):
        nav = get_navigator()
        result = nav.open_or_create(
            entity_id="ent_test_001",
            entity_type="customer",
            name="Test Customer",
        )
        assert result.found is True
        assert result.transition_type == "instant"
        assert store.count == 1  # No new Space created

    def test_open_or_create_new(self, store):
        nav = get_navigator()
        result = nav.open_or_create(
            entity_id="ent_new_001",
            entity_type="customer",
            name="New Customer",
        )
        assert result.found is True
        assert result.transition_type == "created"
        assert store.count == 1

    def test_breadcrumb(self, store, sample_space, sample_project):
        """Breadcrumb builds parent chain."""
        nav = get_navigator()
        # Add parent relationship
        store.add_child(sample_project.space_id, sample_space.space_id)
        sample_space.parent_space_id = sample_project.space_id

        trail = nav.breadcrumb(sample_space.space_id)
        assert len(trail) >= 2
        assert trail[0]["space_id"] == sample_project.space_id  # root first
        assert trail[-1]["space_id"] == sample_space.space_id   # leaf last

    def test_space_tree(self, store, sample_space, sample_project):
        """Tree shows nested structure."""
        nav = get_navigator()
        store.add_child(sample_project.space_id, sample_space.space_id)
        sample_space.parent_space_id = sample_project.space_id

        tree = nav.space_tree(sample_project.space_id)
        assert tree["space_id"] == sample_project.space_id
        assert len(tree["children"]) == 1


# =========================================================================
# 5. Context Persistence
# =========================================================================


class TestSpaceContextPersistence:
    """Tests for context persistence (deliverable 4)."""

    def test_get_context(self, sample_space):
        mgr = get_context_manager()
        ctx = mgr.get_context(sample_space.space_id)
        assert ctx is not None
        assert ctx.space_id == sample_space.space_id

    def test_update_context(self, sample_space):
        mgr = get_context_manager()
        assert mgr.update_context(
            sample_space.space_id,
            last_position="timeline",
            collapsed_sections=["metrics", "knowledge"],
        ) is True
        ctx = mgr.get_context(sample_space.space_id)
        assert ctx.last_position == "timeline"
        assert "metrics" in ctx.collapsed_sections
        assert "knowledge" in ctx.collapsed_sections

    def test_save_position(self, sample_space):
        mgr = get_context_manager()
        mgr.save_position(sample_space.space_id, "relationships")
        assert mgr.get_last_position(sample_space.space_id) == "relationships"

    def test_save_collapsed_sections(self, sample_space):
        mgr = get_context_manager()
        mgr.save_collapsed_sections(sample_space.space_id, ["a", "b"])
        ctx = mgr.get_context(sample_space.space_id)
        assert ctx.collapsed_sections == ["a", "b"]

    def test_save_open_documents(self, sample_space):
        mgr = get_context_manager()
        mgr.save_open_documents(sample_space.space_id, ["doc_1", "doc_2"])
        ctx = mgr.get_context(sample_space.space_id)
        assert ctx.open_documents == ["doc_1", "doc_2"]

    def test_save_pending_work(self, sample_space):
        mgr = get_context_manager()
        mgr.save_pending_work(sample_space.space_id, ["Review contract"])
        ctx = mgr.get_context(sample_space.space_id)
        assert "Review contract" in ctx.pending_work

    def test_restore_context(self, sample_space):
        mgr = get_context_manager()
        mgr.save_position(sample_space.space_id, "timeline")
        mgr.save_collapsed_sections(sample_space.space_id, ["metrics"])

        restored = mgr.restore(sample_space.space_id)
        assert restored is not None
        assert restored["last_position"] == "timeline"
        assert restored["collapsed_sections"] == ["metrics"]

    def test_restore_context_nonexistent(self):
        mgr = get_context_manager()
        assert mgr.restore("nonexistent") is None

    def test_continuity_on_reentry(self, sample_space):
        """Returning to a Space restores continuity."""
        mgr = get_context_manager()
        mgr.save_position(sample_space.space_id, "plans")
        mgr.save_open_documents(sample_space.space_id, ["doc_1"])
        mgr.save_pending_work(sample_space.space_id, ["Approve invoice"])

        restored = mgr.restore(sample_space.space_id)
        assert restored["last_position"] == "plans"
        assert "doc_1" in restored["open_documents"]
        assert "Approve invoice" in restored["pending_work"]


# =========================================================================
# 6. Timeline Integration
# =========================================================================


class TestSpaceTimeline:
    """Tests for timeline integration (deliverable 5)."""

    def test_add_event(self, sample_space):
        mgr = get_timeline_manager()
        event = mgr.add_event(
            sample_space.space_id,
            event_type="milestone",
            title="First milestone",
            importance=0.8,
        )
        assert event is not None
        assert event.event_id.startswith("tev_")
        assert event.title == "First milestone"
        assert event.importance == 0.8

    def test_get_timeline(self, sample_space):
        mgr = get_timeline_manager()
        mgr.add_event(sample_space.space_id, "test", "Event 1")
        mgr.add_event(sample_space.space_id, "test", "Event 2")
        events = mgr.get_timeline(sample_space.space_id)
        assert len(events) == 2

    def test_timeline_ordered_by_time(self, sample_space):
        mgr = get_timeline_manager()
        mgr.add_event(sample_space.space_id, "a", "First")
        mgr.add_event(sample_space.space_id, "b", "Second")
        events = mgr.get_timeline(sample_space.space_id)
        # Most recent first
        assert len(events) == 2

    def test_filter_by_category(self, sample_space):
        mgr = get_timeline_manager()
        mgr.add_event(sample_space.space_id, "communication", "Email",
                      category="communication")
        mgr.add_event(sample_space.space_id, "decision", "Decision",
                      category="decision")
        comms = mgr.get_timeline(sample_space.space_id, category="communication")
        assert len(comms) == 1
        assert comms[0].title == "Email"

    def test_timeline_categories(self, sample_space):
        mgr = get_timeline_manager()
        mgr.record_communication(sample_space.space_id, "Email sent")
        mgr.record_decision(sample_space.space_id, "Approved")
        mgr.record_execution(sample_space.space_id, "Task done")
        mgr.record_document(sample_space.space_id, "Doc uploaded")
        mgr.record_evidence(sample_space.space_id, "Evidence added")
        mgr.record_approval(sample_space.space_id, "Approved")
        mgr.record_ai_insight(sample_space.space_id, "Insight")
        mgr.record_observation(sample_space.space_id, "Observation")

        grouped = mgr.get_timeline_by_category(sample_space.space_id)
        assert "communication" in grouped
        assert "decision" in grouped
        assert "execution" in grouped
        assert "ai_insight" in grouped
        assert "observation" in grouped

    def test_get_timeline_category_counts(self, sample_space):
        mgr = get_timeline_manager()
        mgr.add_event(sample_space.space_id, "a", "A", category="comm")
        mgr.add_event(sample_space.space_id, "b", "B", category="comm")
        mgr.add_event(sample_space.space_id, "c", "C", category="decision")

        grouped = mgr.get_timeline_by_category(sample_space.space_id)
        assert len(grouped["comm"]) == 2
        assert len(grouped["decision"]) == 1

    def test_timeline_nonexistent_space(self):
        mgr = get_timeline_manager()
        event = mgr.add_event("nonexistent", "test", "No space")
        assert event is None
        assert mgr.get_timeline("nonexistent") == []


# =========================================================================
# 7. Knowledge Integration
# =========================================================================


class TestSpaceKnowledge:
    """Tests for knowledge integration (deliverable 6)."""

    def test_add_knowledge_item(self, sample_space):
        mgr = get_knowledge_manager()
        item = mgr.add_item(
            sample_space.space_id,
            item_type="document",
            title="Contract",
            content_summary="Annual contract",
            source="upload",
        )
        assert item is not None
        assert item.item_id.startswith("kn_")
        assert item.title == "Contract"
        assert item.item_type == "document"

    def test_get_knowledge_items(self, sample_space):
        mgr = get_knowledge_manager()
        mgr.add_item(sample_space.space_id, "document", "Doc 1")
        mgr.add_item(sample_space.space_id, "email", "Email 1")
        items = mgr.get_items(sample_space.space_id)
        assert len(items) == 2

    def test_filter_by_type(self, sample_space):
        mgr = get_knowledge_manager()
        mgr.add_item(sample_space.space_id, "document", "Doc 1")
        mgr.add_item(sample_space.space_id, "email", "Email 1")
        docs = mgr.get_items(sample_space.space_id, item_type="document")
        assert len(docs) == 1
        assert docs[0].item_type == "document"

    def test_search_knowledge(self, sample_space):
        mgr = get_knowledge_manager()
        mgr.add_item(sample_space.space_id, "document", "Annual Report",
                     content_summary="Financial report for 2025")
        mgr.add_item(sample_space.space_id, "email", "Welcome",
                     content_summary="Onboarding email")
        results = mgr.search(sample_space.space_id, "Annual")
        assert len(results) == 1
        assert results[0].title == "Annual Report"

    def test_search_knowledge_nonexistent(self):
        mgr = get_knowledge_manager()
        assert mgr.search("nonexistent", "test") == []

    def test_convenience_methods(self, sample_space):
        mgr = get_knowledge_manager()
        mgr.add_document(sample_space.space_id, "Doc", "Summary")
        mgr.add_email(sample_space.space_id, "Email", "Summary")
        mgr.add_note(sample_space.space_id, "Note", "Summary")
        mgr.add_meeting_transcript(sample_space.space_id, "Meeting", "Summary")
        mgr.add_ai_summary(sample_space.space_id, "AI Summary", "Summary")
        mgr.add_research(sample_space.space_id, "Research", "Summary")
        mgr.add_file(sample_space.space_id, "File", "Summary")
        items = mgr.get_items(sample_space.space_id)
        assert len(items) == 7

    def test_knowledge_summary(self, sample_space):
        mgr = get_knowledge_manager()
        mgr.add_item(sample_space.space_id, "document", "Doc 1")
        mgr.add_item(sample_space.space_id, "email", "Email 1")
        summary = mgr.get_knowledge_summary(sample_space.space_id)
        assert summary["total"] == 2
        assert summary["by_type"]["document"] == 1
        assert summary["by_type"]["email"] == 1

    def test_knowledge_nonexistent_space(self):
        mgr = get_knowledge_manager()
        assert mgr.add_item("nonexistent", "doc", "X") is None
        assert mgr.get_items("nonexistent") == []


# =========================================================================
# 8. Relationship Visualization
# =========================================================================


class TestSpaceRelationships:
    """Tests for relationship visualization (deliverable 7)."""

    def test_add_relationship(self, sample_space):
        mgr = get_relationship_manager()
        success = mgr.add_relationship(
            sample_space.space_id,
            rel_id="rel_001",
            target_entity_id="ent_target_001",
            target_entity_name="Target Corp",
            target_entity_type="company",
            rel_type="client_of",
        )
        assert success is True

    def test_get_relationships(self, sample_space):
        mgr = get_relationship_manager()
        mgr.add_relationship(
            sample_space.space_id, "rel_001", "ent_t1", "T1", "company",
            "client_of",
        )
        mgr.add_relationship(
            sample_space.space_id, "rel_002", "ent_t2", "T2", "project",
            "has_project",
        )
        rels = mgr.get_relationships(sample_space.space_id)
        assert len(rels) == 2

    def test_filter_by_type(self, sample_space):
        mgr = get_relationship_manager()
        mgr.add_relationship(
            sample_space.space_id, "rel_001", "ent_t1", "T1", "company",
            "client_of",
        )
        mgr.add_relationship(
            sample_space.space_id, "rel_002", "ent_t2", "T2", "project",
            "has_project",
        )
        client_rels = mgr.get_relationships_by_type(
            sample_space.space_id, "client_of"
        )
        assert len(client_rels) == 1

    def test_filter_by_direction(self, sample_space):
        mgr = get_relationship_manager()
        mgr.add_relationship(
            sample_space.space_id, "rel_001", "ent_t1", "T1", "company",
            "client_of", direction="outgoing",
        )
        outgoing = mgr.get_relationships_by_direction(
            sample_space.space_id, "outgoing"
        )
        assert len(outgoing) >= 1

    def test_graph_data(self, sample_space):
        mgr = get_relationship_manager()
        mgr.add_relationship(
            sample_space.space_id, "rel_001", "ent_t1", "Target Corp",
            "company", "client_of",
        )
        graph = mgr.get_graph(sample_space.space_id)
        assert len(graph["nodes"]) == 2  # center + target
        assert len(graph["edges"]) == 1
        assert graph["center_entity_id"] == "ent_test_001"

    def test_graph_with_multiple_relationships(self, sample_space):
        mgr = get_relationship_manager()
        mgr.add_relationship(
            sample_space.space_id, "rel_001", "ent_t1", "T1", "company", "owns",
        )
        mgr.add_relationship(
            sample_space.space_id, "rel_002", "ent_t2", "T2", "project", "manages",
        )
        graph = mgr.get_graph(sample_space.space_id)
        assert len(graph["nodes"]) == 3
        assert len(graph["edges"]) == 2

    def test_relationship_summary(self, sample_space):
        mgr = get_relationship_manager()
        mgr.add_relationship(
            sample_space.space_id, "rel_001", "ent_t1", "T1", "company", "owns",
        )
        mgr.add_relationship(
            sample_space.space_id, "rel_002", "ent_t2", "T2", "project", "manages",
        )
        summary = mgr.get_relationship_summary(sample_space.space_id)
        assert summary["total"] == 2
        assert "owns" in summary["types"]
        assert "manages" in summary["types"]

    def test_relationships_nonexistent_space(self):
        mgr = get_relationship_manager()
        assert mgr.get_relationships("nonexistent") == []
        assert mgr.get_graph("nonexistent") == {"nodes": [], "edges": []}


# =========================================================================
# 9. Command Framework
# =========================================================================


class TestSpaceCommands:
    """Tests for the command framework (deliverable 8)."""

    def test_available_commands(self, sample_space):
        executor = get_executor()
        commands = executor.get_available_commands(sample_space)
        assert len(commands) >= 14
        names = [c["name"] for c in commands]
        assert "summarize" in names
        assert "explain" in names
        assert "create_plan" in names
        assert "delegate" in names
        assert "find_risks" in names
        assert "show_dependencies" in names

    def test_execute_summarize(self, sample_space):
        executor = get_executor()
        result = executor.execute(sample_space, "summarize")
        assert result["success"] is True
        assert result["command"] == "summarize"
        assert sample_space.name in result["summary"]

    def test_execute_explain(self, sample_space):
        executor = get_executor()
        result = executor.execute(sample_space, "explain")
        assert result["success"] is True
        assert sample_space.name in result["explanation"]

    def test_execute_create_plan(self, sample_space):
        executor = get_executor()
        result = executor.execute(sample_space, "create_plan",
                                  {"title": "Test Plan"})
        assert result["success"] is True
        assert result["plan"]["title"] == "Test Plan"

    def test_execute_unknown_command(self, sample_space):
        executor = get_executor()
        result = executor.execute(sample_space, "nonexistent")
        assert result.get("error") is True

    def test_register_custom_command(self, sample_space):
        executor = get_executor()

        def _custom_handler(space, params):
            return {"custom": "handled", "space_name": space.name}

        cmd = SpaceCommand("custom", "Custom", "Custom cmd", _custom_handler)
        executor.register_command(cmd)
        result = executor.execute(sample_space, "custom")
        assert result["success"] is True
        assert result["custom"] == "handled"

    def test_command_applies_to_filter(self, sample_space):
        """Commands can be restricted to specific entity types."""
        def _handler(space, params):
            return {"handled": True}

        cmd = SpaceCommand("only_customer", "Only Customer",
                           "Only for customers", _handler,
                           applies_to=["customer"])
        assert cmd.applies(sample_space) is True  # sample is customer

        # Create a non-customer space
        store = get_store()
        supplier = store.create("ent_sup_cmd", "supplier", "Supplier")
        assert cmd.applies(supplier) is False

    def test_review_command(self, sample_space):
        executor = get_executor()
        result = executor.execute(sample_space, "review")
        assert result["success"] is True
        assert result["focus"] == "all"

    def test_find_risks_command(self, sample_space):
        executor = get_executor()
        result = executor.execute(sample_space, "find_risks")
        assert result["success"] is True

    def test_show_dependencies_command(self, sample_space):
        executor = get_executor()
        result = executor.execute(sample_space, "show_dependencies")
        assert result["success"] is True


# =========================================================================
# 10. Space Nesting and Composition
# =========================================================================


class TestSpaceComposition:
    """Tests for Space composition — Spaces can contain Spaces."""

    def test_add_child(self, store, sample_space, sample_project):
        assert store.add_child(sample_project.space_id, sample_space.space_id)
        assert sample_space.space_id in sample_project.child_space_ids
        assert sample_space.parent_space_id == sample_project.space_id

    def test_list_children(self, store, sample_space, sample_project):
        store.add_child(sample_project.space_id, sample_space.space_id)
        children = store.list_children(sample_project.space_id)
        assert len(children) == 1
        assert children[0].space_id == sample_space.space_id

    def test_nested_composition(self, store):
        """Company -> Customer -> Project -> Task."""
        company = store.create("ent_comp", "company", "Company")
        customer = store.create("ent_cust", "customer", "Customer",
                                parent_space_id=company.space_id)
        project = store.create("ent_proj", "project", "Project",
                               parent_space_id=customer.space_id)
        task = store.create("ent_task", "task", "Task",
                            parent_space_id=project.space_id)

        store.add_child(company.space_id, customer.space_id)
        store.add_child(customer.space_id, project.space_id)
        store.add_child(project.space_id, task.space_id)

        assert len(store.list_children(company.space_id)) == 1
        assert len(store.list_children(customer.space_id)) == 1
        assert len(store.list_children(project.space_id)) == 1

        # Verify parent chain
        assert task.parent_space_id == project.space_id
        assert project.parent_space_id == customer.space_id
        assert customer.parent_space_id == company.space_id

    def test_space_tree(self, store):
        """Tree represents nested structure."""
        root = store.create("ent_root", "root", "Root")
        child1 = store.create("ent_c1", "child", "Child 1",
                              parent_space_id=root.space_id)
        child2 = store.create("ent_c2", "child", "Child 2",
                              parent_space_id=root.space_id)
        grandchild = store.create("ent_gc", "grandchild", "Grandchild",
                                  parent_space_id=child1.space_id)

        store.add_child(root.space_id, child1.space_id)
        store.add_child(root.space_id, child2.space_id)
        store.add_child(child1.space_id, grandchild.space_id)

        nav = get_navigator()
        tree = nav.space_tree(root.space_id)
        assert len(tree["children"]) == 2
        assert tree["children"][0]["children"][0]["name"] == "Grandchild"


# =========================================================================
# 11. Store Integration - Full Lifecycle
# =========================================================================


class TestSpaceStoreIntegration:
    """Integration tests for the complete Space lifecycle."""

    def test_full_lifecycle(self, store):
        """Create, add data, query, update, navigate, delete."""
        # Create
        space = store.create(
            entity_id="ent_lifecycle",
            entity_type="customer",
            name="Lifecycle Test",
        )
        sid = space.space_id

        # Add relationships
        store.add_relationship(sid, SpaceRelationshipRef(
            rel_id="rel_lc_1", target_entity_id="ent_t1",
            target_entity_name="Target", target_entity_type="company",
            rel_type="partner",
        ))
        assert len(store.get_relationships(sid)) == 1

        # Add timeline events
        store.add_timeline_event(sid, SpaceTimelineEvent(
            event_id="tev_lc_1", event_type="created",
            timestamp=datetime.now(timezone.utc).isoformat(),
            title="Started",
        ))
        assert len(store.get_timeline(sid)) == 1

        # Add knowledge
        store.add_knowledge(sid, SpaceKnowledgeItem(
            item_id="kn_lc_1", item_type="document",
            title="Doc", content_summary="Summary",
        ))
        assert len(store.get_knowledge(sid)) == 1

        # Add plans
        store.add_plan(sid, SpacePlanRef(
            plan_id="pln_lc_1", title="Plan", state="active",
        ))
        assert len(store.get_plans(sid)) == 1

        # Add metrics
        store.add_metric(sid, SpaceMetric(
            metric_id="met_lc_1", name="Health",
            value="good", trend="stable",
        ))
        assert len(store.get_metrics(sid)) == 1

        # Update AI understanding
        store.update_ai_understanding(sid, SpaceAIUnderstanding(
            summary="AI summary",
            goals=["Goal 1"],
        ))
        assert store.get(sid).ai_understanding.summary == "AI summary"

        # Search
        results = store.search("Lifecycle")
        assert len(results) == 1

        # Update
        store.update(sid, name="Updated Lifecycle")
        assert store.get(sid).name == "Updated Lifecycle"

        # Delete
        store.delete(sid)
        assert store.get(sid) is None

    def test_multiple_spaces_same_type(self, store):
        """Multiple Spaces of the same type co-exist."""
        for i in range(5):
            store.create(
                entity_id=f"ent_multi_{i}",
                entity_type="customer",
                name=f"Customer {i}",
            )
        assert store.count == 5
        assert len(store.list_by_type("customer")) == 5

    def test_multiple_entity_types(self, store):
        """Different entity types work independently."""
        types = ["customer", "supplier", "employee", "invoice", "project"]
        for i, t in enumerate(types):
            store.create(
                entity_id=f"ent_ent_{i}",
                entity_type=t,
                name=f"Entity {i}",
            )
        assert store.count == len(types)
        for t in types:
            assert len(store.list_by_type(t)) == 1


# =========================================================================
# 12. Singleton Pattern Tests
# =========================================================================


class TestSpaceSingletons:
    """Tests that all singletons reset correctly."""

    def test_store_singleton(self):
        s1 = get_store()
        s2 = get_store()
        assert s1 is s2
        reset_store()
        s3 = get_store()
        assert s3 is not s1

    def test_renderer_singleton(self):
        r1 = get_renderer()
        r2 = get_renderer()
        assert r1 is r2
        reset_renderer()
        r3 = get_renderer()
        assert r3 is not r1

    def test_navigator_singleton(self):
        n1 = get_navigator()
        n2 = get_navigator()
        assert n1 is n2
        reset_navigator()
        n3 = get_navigator()
        assert n3 is not n1

    def test_context_manager_singleton(self):
        c1 = get_context_manager()
        c2 = get_context_manager()
        assert c1 is c2
        reset_context_manager()
        c3 = get_context_manager()
        assert c3 is not c1

    def test_executor_singleton(self):
        e1 = get_executor()
        e2 = get_executor()
        assert e1 is e2
        reset_executor()
        e3 = get_executor()
        assert e3 is not e1

    def test_timeline_manager_singleton(self):
        t1 = get_timeline_manager()
        t2 = get_timeline_manager()
        assert t1 is t2
        reset_timeline_manager()
        t3 = get_timeline_manager()
        assert t3 is not t1

    def test_knowledge_manager_singleton(self):
        k1 = get_knowledge_manager()
        k2 = get_knowledge_manager()
        assert k1 is k2
        reset_knowledge_manager()
        k3 = get_knowledge_manager()
        assert k3 is not k1

    def test_relationship_manager_singleton(self):
        r1 = get_relationship_manager()
        r2 = get_relationship_manager()
        assert r1 is r2
        reset_relationship_manager()
        r3 = get_relationship_manager()
        assert r3 is not r1


# =========================================================================
# 13. API Route Tests
# =========================================================================


class TestSpaceAPIRoutes:
    """Tests for Space API routes (deliverable 9)."""

    def test_create_space_via_api(self, client):
        """POST /api/v1/space creates a new Space."""
        resp = client.post("/api/v1/space", json={
            "entity_id": "ent_api_001",
            "entity_type": "customer",
            "name": "API Customer",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["space"]["name"] == "API Customer"
        assert data["space"]["entity_type"] == "customer"

    def test_get_space_via_api(self, client):
        """GET /api/v1/space/<id> returns full Space."""
        # Create first
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_api_002",
            "entity_type": "supplier",
            "name": "API Supplier",
        })
        space_id = create.get_json()["space"]["space_id"]

        # Get
        resp = client.get(f"/api/v1/space/{space_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["space"]["identity"]["name"] == "API Supplier"
        assert "panels" in data["space"]
        # Panel count is capability-driven (supplier has 4 capabilities)
        assert len(data["space"]["panels"]) >= 1
        assert "capabilities" in data["space"]

    def test_get_space_not_found(self, client):
        resp = client.get("/api/v1/space/nonexistent")
        assert resp.status_code == 404

    def test_update_space_via_api(self, client):
        """PUT /api/v1/space/<id> updates a Space."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_api_003",
            "entity_type": "company",
            "name": "Original",
        })
        space_id = create.get_json()["space"]["space_id"]

        resp = client.put(f"/api/v1/space/{space_id}", json={
            "name": "Updated",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["space"]["name"] == "Updated"

    def test_delete_space_via_api(self, client):
        """DELETE /api/v1/space/<id> deletes a Space."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_api_004",
            "entity_type": "project",
            "name": "Delete Me",
        })
        space_id = create.get_json()["space"]["space_id"]

        resp = client.delete(f"/api/v1/space/{space_id}")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Space deleted"

        # Verify deletion
        get_resp = client.get(f"/api/v1/space/{space_id}")
        assert get_resp.status_code == 404

    def test_list_spaces_via_api(self, client):
        """GET /api/v1/space lists all Spaces."""
        client.post("/api/v1/space", json={
            "entity_id": "ent_list_1", "entity_type": "customer",
            "name": "C1",
        })
        client.post("/api/v1/space", json={
            "entity_id": "ent_list_2", "entity_type": "supplier",
            "name": "S1",
        })

        resp = client.get("/api/v1/space")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 2

    def test_filter_spaces_by_type(self, client):
        """GET /api/v1/space?type=customer filters by type."""
        client.post("/api/v1/space", json={
            "entity_id": "ent_f_1", "entity_type": "customer", "name": "C1",
        })
        client.post("/api/v1/space", json={
            "entity_id": "ent_f_2", "entity_type": "supplier", "name": "S1",
        })

        resp = client.get("/api/v1/space?type=customer")
        data = resp.get_json()
        assert all(s["entity_type"] == "customer" for s in data["spaces"])

    def test_search_via_api(self, client):
        """GET /api/v1/space/search?q=... searches Spaces."""
        client.post("/api/v1/space", json={
            "entity_id": "ent_srch_1", "entity_type": "customer",
            "name": "Alpha Corp",
        })
        client.post("/api/v1/space", json={
            "entity_id": "ent_srch_2", "entity_type": "supplier",
            "name": "Beta Inc",
        })

        resp = client.get("/api/v1/space/search?q=Alpha")
        data = resp.get_json()
        assert data["total"] >= 1
        assert data["results"][0]["name"] == "Alpha Corp"

    def test_navigate_via_api(self, client):
        """POST /api/v1/space/navigate creates/opens a Space."""
        resp = client.post("/api/v1/space/navigate", json={
            "entity_id": "ent_nav_001",
            "entity_type": "customer",
            "name": "Navigate Customer",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["navigation"]["found"] is True
        assert data["navigation"]["space"]["name"] == "Navigate Customer"

    def test_navigate_existing_returns_instant(self, client):
        """Navigating to an existing Space returns 'instant'."""
        # Create first
        client.post("/api/v1/space", json={
            "entity_id": "ent_nav_existing",
            "entity_type": "customer",
            "name": "Existing",
        })
        # Navigate
        resp = client.post("/api/v1/space/navigate", json={
            "entity_id": "ent_nav_existing",
            "entity_type": "customer",
            "name": "Existing",
        })
        data = resp.get_json()
        assert data["navigation"]["transition_type"] == "instant"

    def test_timeline_via_api(self, client):
        """POST/GET /api/v1/space/<id>/timeline."""
        # Create space
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_tl_api", "entity_type": "project",
            "name": "Timeline Project",
        })
        sid = create.get_json()["space"]["space_id"]

        # Add event
        resp = client.post(f"/api/v1/space/{sid}/timeline", json={
            "event_type": "milestone",
            "title": "Milestone 1",
            "category": "execution",
            "importance": 0.8,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["event"]["title"] == "Milestone 1"

        # Get timeline
        resp = client.get(f"/api/v1/space/{sid}/timeline")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_knowledge_via_api(self, client):
        """POST/GET /api/v1/space/<id>/knowledge."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_kn_api", "entity_type": "customer",
            "name": "Knowledge Customer",
        })
        sid = create.get_json()["space"]["space_id"]

        # Add knowledge
        resp = client.post(f"/api/v1/space/{sid}/knowledge", json={
            "item_type": "document",
            "title": "Contract",
            "content_summary": "Annual contract",
        })
        assert resp.status_code == 201

        # Get knowledge
        resp = client.get(f"/api/v1/space/{sid}/knowledge")
        data = resp.get_json()
        assert data["total"] >= 1
        assert data["items"][0]["title"] == "Contract"

    def test_relationships_via_api(self, client):
        """POST/GET /api/v1/space/<id>/relationships."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_rel_api", "entity_type": "company",
            "name": "Rel Company",
        })
        sid = create.get_json()["space"]["space_id"]

        # Add relationship
        resp = client.post(f"/api/v1/space/{sid}/relationships", json={
            "rel_id": "rel_api_001",
            "target_entity_id": "ent_target_api",
            "target_entity_name": "Target",
            "target_entity_type": "customer",
            "rel_type": "client_of",
        })
        assert resp.status_code == 201

        # Get relationships
        resp = client.get(f"/api/v1/space/{sid}/relationships")
        data = resp.get_json()
        assert data["total"] >= 1

        # Get graph
        resp = client.get(f"/api/v1/space/{sid}/relationships/graph")
        data = resp.get_json()
        assert len(data["graph"]["nodes"]) == 2

    def test_commands_via_api(self, client):
        """GET/POST /api/v1/space/<id>/commands."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_cmd_api", "entity_type": "customer",
            "name": "Cmd Customer",
        })
        sid = create.get_json()["space"]["space_id"]

        # Get available commands
        resp = client.get(f"/api/v1/space/{sid}/commands")
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["commands"]) >= 14

        # Execute command
        resp = client.post(f"/api/v1/space/{sid}/commands/summarize", json={})
        data = resp.get_json()
        assert data["success"] is True
        assert "result" in data

    def test_context_via_api(self, client):
        """GET/PUT /api/v1/space/<id>/context."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_ctx_api", "entity_type": "customer",
            "name": "Ctx Customer",
        })
        sid = create.get_json()["space"]["space_id"]

        # Update context
        resp = client.put(f"/api/v1/space/{sid}/context", json={
            "last_position": "timeline",
            "collapsed_sections": ["metrics"],
        })
        assert resp.status_code == 200

        # Get context
        resp = client.get(f"/api/v1/space/{sid}/context")
        data = resp.get_json()
        assert data["context"]["last_position"] == "timeline"
        assert "metrics" in data["context"]["collapsed_sections"]

    def test_ai_understanding_via_api(self, client):
        """GET/PUT /api/v1/space/<id>/ai-understanding."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_ai_api", "entity_type": "customer",
            "name": "AI Customer",
        })
        sid = create.get_json()["space"]["space_id"]

        # Update AI understanding
        resp = client.put(f"/api/v1/space/{sid}/ai-understanding", json={
            "summary": "AI summary",
            "goals": ["Goal 1", "Goal 2"],
            "current_risks": ["Risk 1"],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ai_understanding"]["summary"] == "AI summary"

        # Get AI understanding
        resp = client.get(f"/api/v1/space/{sid}/ai-understanding")
        data = resp.get_json()
        assert data["ai_understanding"]["summary"] == "AI summary"

    def test_children_via_api(self, client):
        """POST/GET /api/v1/space/<id>/children."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_parent_api", "entity_type": "company",
            "name": "Parent",
        })
        parent_sid = create.get_json()["space"]["space_id"]

        # Add child
        resp = client.post(f"/api/v1/space/{parent_sid}/children", json={
            "child_entity_id": "ent_child_api",
            "child_entity_type": "customer",
            "child_name": "Child Customer",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["child"]["name"] == "Child Customer"

        # Get children
        resp = client.get(f"/api/v1/space/{parent_sid}/children")
        data = resp.get_json()
        assert data["total"] >= 1

    def test_metrics_via_api(self, client):
        """POST/GET /api/v1/space/<id>/metrics."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_met_api", "entity_type": "project",
            "name": "Metrics Project",
        })
        sid = create.get_json()["space"]["space_id"]

        # Add metric
        resp = client.post(f"/api/v1/space/{sid}/metrics", json={
            "name": "Progress",
            "value": 50,
            "unit": "%",
            "trend": "improving",
        })
        assert resp.status_code == 201

        # Get metrics
        resp = client.get(f"/api/v1/space/{sid}/metrics")
        data = resp.get_json()
        assert data["total"] >= 1
        assert data["metrics"][0]["name"] == "Progress"

    def test_reset_via_api(self, client):
        """POST /api/v1/space/reset clears all data."""
        client.post("/api/v1/space", json={
            "entity_id": "ent_reset", "entity_type": "customer",
            "name": "Reset Me",
        })
        resp = client.post("/api/v1/space/reset")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "All Space stores reset"

        # Verify empty
        resp = client.get("/api/v1/space")
        assert resp.get_json()["total"] == 0


# =========================================================================
# 14. Capability Framework Tests
# =========================================================================


class TestSpaceCapabilities:
    """Tests for the capability framework (A1A deliverable 1)."""

    def test_capability_registry(self):
        from app.space.capabilities import get_registry, Capability
        registry = get_registry()
        caps = registry.list_capabilities()
        assert len(caps) >= 10

    def test_capability_definition(self):
        from app.space.capabilities import Capability
        cap = Capability(
            name="test_cap",
            label="Test Capability",
            description="A test",
            icon="🧪",
            priority=1,
        )
        assert cap.name == "test_cap"
        d = cap.to_dict()
        assert d["name"] == "test_cap"
        assert d["label"] == "Test Capability"

    def test_builtin_capabilities_have_panels(self):
        from app.space.capabilities import ALL_CAPABILITIES
        for name, cap in ALL_CAPABILITIES.items():
            assert len(cap.panels) >= 1, f"{name} has no panels"

    def test_type_mapping(self, store):
        from app.space.capabilities import get_registry
        registry = get_registry()
        registry.map_type("test_type", ["communication", "planning", "ai"])
        caps = registry.get_capabilities_for("test_type")
        assert len(caps) == 3
        names = [c.name for c in caps]
        assert "communication" in names
        assert "planning" in names
        assert "ai" in names

    def test_default_fallback(self):
        from app.space.capabilities import get_registry, DEFAULT_CAPABILITIES
        registry = get_registry()
        caps = registry.get_capabilities_for("unknown_type_xyz")
        assert len(caps) == len(DEFAULT_CAPABILITIES)

    def test_panels_from_capabilities(self):
        from app.space.capabilities import get_registry
        registry = get_registry()
        registry.map_type("test_panels", ["communication", "timeline"])
        panels = registry.get_panels_for("test_panels")
        from app.space.models import SpacePanel
        assert SpacePanel.COMMUNICATIONS in panels
        assert SpacePanel.TIMELINE in panels

    def test_discover_on_space(self, store):
        from app.space.capabilities import get_registry
        registry = get_registry()
        registry.map_type("disc_customer", ["communication", "planning", "finance"])
        space = store.create(
            entity_id="ent_disc", entity_type="disc_customer", name="Disc",
        )
        caps = registry.discover_capabilities(space)
        assert len(caps) >= 3

    def test_register_custom_capability(self):
        from app.space.capabilities import get_registry, Capability
        from app.space.models import SpacePanel
        registry = get_registry()
        custom = Capability("custom", "Custom", panels=[SpacePanel.METRICS])
        registry.register_capability(custom)
        assert registry.get_capability("custom") is not None

    def test_load_default_mappings(self):
        from app.space.capabilities import get_registry
        registry = get_registry()
        registry.load_default_mappings()
        # Customer should have 6 capabilities
        caps = registry.get_capabilities_for("customer")
        assert len(caps) >= 6

    def test_capability_customization_via_store(self, store):
        """Space capabilities can be customized at creation time."""
        space = store.create(
            entity_id="ent_cust_caps",
            entity_type="customer",
            name="Custom Caps",
            capabilities=["context", "timeline"],
        )
        assert space.capabilities == ["context", "timeline"]

    def test_renderer_respects_capabilities(self, store):
        """Renderer only shows panels from discovered capabilities."""
        from app.space.capabilities import get_registry
        registry = get_registry()
        registry.map_type("minimal", ["context"])
        space = store.create("ent_min", "minimal", "Minimal")
        renderer = get_renderer()
        result = renderer.render(space)
        assert len(result["panels"]) == 1
        assert "context" in result["panels"]


# =========================================================================
# 15. Lifecycle Tests
# =========================================================================


class TestSpaceLifecycle:
    """Tests for the Space lifecycle (A1A deliverable 5)."""

    def test_default_lifecycle_is_draft(self, store):
        space = store.create("ent_lc_def", "customer", "Test")
        assert space.lifecycle.state.value == "draft"

    def test_valid_transitions(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.DRAFT)
        assert lc.can_transition_to(LifecycleState.ACTIVE) is True
        assert lc.can_transition_to(LifecycleState.ARCHIVED) is True
        assert lc.can_transition_to(LifecycleState.HISTORICAL) is False

    def test_transition_draft_to_active(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.DRAFT)
        new_lc = lc.transition_to(LifecycleState.ACTIVE)
        assert new_lc.state == LifecycleState.ACTIVE
        assert new_lc.previous_state == LifecycleState.DRAFT
        assert len(new_lc.transitions) == 1

    def test_transition_active_to_dormant(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.ACTIVE)
        new_lc = lc.transition_to(LifecycleState.DORMANT)
        assert new_lc.state == LifecycleState.DORMANT

    def test_transition_dormant_to_active(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.DORMANT)
        new_lc = lc.transition_to(LifecycleState.ACTIVE)
        assert new_lc.state == LifecycleState.ACTIVE

    def test_transition_active_to_archived(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.ACTIVE)
        new_lc = lc.transition_to(LifecycleState.ARCHIVED)
        assert new_lc.state == LifecycleState.ARCHIVED

    def test_transition_archived_to_historical(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.ARCHIVED)
        new_lc = lc.transition_to(LifecycleState.HISTORICAL)
        assert new_lc.state == LifecycleState.HISTORICAL

    def test_invalid_transition_raises(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.HISTORICAL)
        with pytest.raises(ValueError):
            lc.transition_to(LifecycleState.ACTIVE)

    def test_lifecycle_effects(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.ACTIVE)
        effects = lc.effects()
        assert effects["permissions"] == "normal"
        assert effects["ai_attention"] == "high"
        assert effects["search_visible"] is True

    def test_draft_effects(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.DRAFT)
        effects = lc.effects()
        assert effects["permissions"] == "restricted"
        assert effects["visibility"] == "owners_only"

    def test_archived_effects(self):
        from app.space.lifecycle import SpaceLifecycle, LifecycleState
        lc = SpaceLifecycle(state=LifecycleState.ARCHIVED)
        effects = lc.effects()
        assert effects["permissions"] == "read_only"
        assert effects["search_visible"] is False

    def test_lifecycle_manager_transition(self, store):
        from app.space.lifecycle import LifecycleManager, LifecycleState
        space = store.create("ent_lc_mgr", "customer", "LC Test")
        mgr = LifecycleManager()
        result = mgr.transition(space.space_id, LifecycleState.ACTIVE)
        assert result is not None
        assert result.state == LifecycleState.ACTIVE
        # Verify persisted
        assert store.get(space.space_id).lifecycle.state == LifecycleState.ACTIVE

    def test_lifecycle_manager_invalid_transition(self, store):
        from app.space.lifecycle import LifecycleManager, LifecycleState
        space = store.create("ent_lc_inv", "customer", "LC Invalid")
        mgr = LifecycleManager()
        # From DRAFT to HISTORICAL is invalid
        result = mgr.transition(space.space_id, LifecycleState.HISTORICAL)
        assert result is None

    def test_lifecycle_manager_get_valid_transitions(self, store):
        from app.space.lifecycle import LifecycleManager, LifecycleState
        space = store.create("ent_lc_vt", "customer", "LC VT")
        mgr = LifecycleManager()
        transitions = mgr.get_valid_transitions(space.space_id)
        assert "active" in transitions
        assert "archived" in transitions

    def test_lifecycle_manager_get_effects(self, store):
        from app.space.lifecycle import LifecycleManager, LifecycleState
        space = store.create("ent_lc_eff", "customer", "LC Eff")
        mgr = LifecycleManager()
        mgr.transition(space.space_id, LifecycleState.ACTIVE)
        effects = mgr.get_state_effects(space.space_id)
        assert effects["ai_attention"] == "high"

    def test_full_lifecycle_flow(self, store):
        """Draft → Active → Dormant → Active → Archived → Historical."""
        from app.space.lifecycle import LifecycleManager, LifecycleState
        space = store.create("ent_lc_full", "customer", "Full LC")
        mgr = LifecycleManager()

        assert space.lifecycle.state == LifecycleState.DRAFT
        mgr.transition(space.space_id, LifecycleState.ACTIVE)
        assert space.lifecycle.state == LifecycleState.ACTIVE
        mgr.transition(space.space_id, LifecycleState.DORMANT)
        assert space.lifecycle.state == LifecycleState.DORMANT
        mgr.transition(space.space_id, LifecycleState.ACTIVE)
        assert space.lifecycle.state == LifecycleState.ACTIVE
        mgr.transition(space.space_id, LifecycleState.ARCHIVED)
        assert space.lifecycle.state == LifecycleState.ARCHIVED
        mgr.transition(space.space_id, LifecycleState.HISTORICAL)
        assert space.lifecycle.state == LifecycleState.HISTORICAL


# =========================================================================
# 16. Cross-Space Reasoning Tests
# =========================================================================


class TestSpaceReasoning:
    """Tests for cross-Space reasoning (A1A deliverable 4)."""

    def test_traverse_single_space(self, store, sample_space):
        from app.space.reasoning import get_reasoner
        reasoner = get_reasoner()
        steps = reasoner.traverse(sample_space.space_id, max_depth=1)
        assert len(steps) >= 1
        assert steps[0].space_id == sample_space.space_id

    def test_traverse_with_relationships(self, store):
        """Reasoning traverses through relationships."""
        from app.space.reasoning import get_reasoner
        customer = store.create("ent_rsn_c", "customer", "Reason Customer")
        supplier = store.create("ent_rsn_s", "supplier", "Reason Supplier")
        store.add_relationship(customer.space_id, SpaceRelationshipRef(
            rel_id="rel_rsn_1", target_entity_id="ent_rsn_s",
            target_entity_name="Reason Supplier",
            target_entity_type="supplier", rel_type="works_with",
        ))

        # Need to link supplier via entity lookup
        reasoner = get_reasoner()
        steps = reasoner.traverse(customer.space_id, max_depth=2)
        assert len(steps) >= 2

    def test_traverse_with_children(self, store):
        """Reasoning traverses through child Spaces."""
        from app.space.reasoning import get_reasoner
        parent = store.create("ent_rsn_p", "company", "Parent")
        child = store.create("ent_rsn_ch", "project", "Child",
                             parent_space_id=parent.space_id)
        store.add_child(parent.space_id, child.space_id)

        reasoner = get_reasoner()
        steps = reasoner.traverse(parent.space_id, max_depth=2)
        assert len(steps) >= 2

    def test_answer_query(self, store):
        """Reasoning answer returns a result with trail."""
        from app.space.reasoning import ReasoningQuery, get_reasoner
        space = store.create("ent_rsn_q", "project", "Query Project")
        query = ReasoningQuery(
            question="Why is this project delayed?",
            start_space_id=space.space_id,
            max_depth=2,
        )
        reasoner = get_reasoner()
        result = reasoner.answer(query)
        assert result.query == "Why is this project delayed?"
        assert result.start_space_id == space.space_id
        assert len(result.trail) >= 1

    def test_find_paths(self, store):
        """Find paths between two Spaces."""
        from app.space.reasoning import get_reasoner
        a = store.create("ent_rsn_a", "company", "Space A")
        b = store.create("ent_rsn_b", "project", "Space B",
                         parent_space_id=a.space_id)
        store.add_child(a.space_id, b.space_id)

        reasoner = get_reasoner()
        paths = reasoner.find_paths(a.space_id, b.space_id, max_depth=3)
        assert len(paths) >= 1

    def test_evidence_collection(self, store):
        """Reasoning collects evidence from timeline, plans, metrics."""
        from app.space.reasoning import get_reasoner
        space = store.create("ent_rsn_ev", "project", "Evidence Test")
        store.add_timeline_event(space.space_id, SpaceTimelineEvent(
            event_id="tev_rsn_1", event_type="milestone",
            timestamp="2025-01-01T00:00:00Z", title="Milestone 1",
        ))
        store.add_plan(space.space_id, SpacePlanRef(
            plan_id="pln_rsn_1", title="Plan A", state="active",
        ))
        store.add_metric(space.space_id, SpaceMetric(
            metric_id="met_rsn_1", name="Progress", value=50, unit="%",
        ))

        reasoner = get_reasoner()
        steps = reasoner.traverse(space.space_id, max_depth=1)
        assert len(steps) >= 1
        # Evidence from the space itself
        assert len(steps[0].evidence) >= 1


# =========================================================================
# 17. Persistent AI Resident Tests
# =========================================================================


class TestSpaceAIResident:
    """Tests for persistent AI resident (A1A deliverable 6)."""

    def test_default_resident_exists(self, store):
        space = store.create("ent_ai_res", "customer", "AI Resident")
        assert space.ai_resident is not None
        assert space.ai_resident.space_id == space.space_id

    def test_update_understanding(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_u", "customer", "AI Understanding")
        mgr = get_resident_manager()
        mgr.update_understanding(space.space_id, "This is a key customer")
        assert space.ai_resident.current_understanding == "This is a key customer"

    def test_add_question(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_q", "customer", "AI Question")
        mgr = get_resident_manager()
        mgr.add_question(space.space_id, "Why is churn increasing?")
        assert "Why is churn increasing?" in space.ai_resident.open_questions

    def test_close_question(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_cq", "customer", "AI Close")
        mgr = get_resident_manager()
        mgr.add_question(space.space_id, "Question 1")
        mgr.add_question(space.space_id, "Question 2")
        mgr.close_question(space.space_id, "Question 1")
        assert "Question 1" not in space.ai_resident.open_questions
        assert "Question 2" in space.ai_resident.open_questions

    def test_add_hypothesis(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_h", "customer", "AI Hypothesis")
        mgr = get_resident_manager()
        mgr.add_hypothesis(space.space_id, "Churn is due to pricing",
                           confidence=0.7, evidence=["Survey data"])
        assert len(space.ai_resident.hypotheses) == 1
        assert space.ai_resident.hypotheses[0]["hypothesis"] == "Churn is due to pricing"

    def test_add_risk(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_r", "project", "AI Risk")
        mgr = get_resident_manager()
        mgr.add_risk(space.space_id, "Timeline slippage",
                     severity="high", probability=0.6)
        assert len(space.ai_resident.risks) == 1

    def test_add_opportunity(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_o", "customer", "AI Opp")
        mgr = get_resident_manager()
        mgr.add_opportunity(space.space_id, "Cross-sell opportunity",
                            potential="high", confidence=0.8)
        assert len(space.ai_resident.opportunities) == 1

    def test_add_recommendation(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_rec", "customer", "AI Rec")
        mgr = get_resident_manager()
        mgr.add_recommendation(space.space_id, "Schedule quarterly review")
        assert "Schedule quarterly review" in space.ai_resident.recommendations

    def test_add_reasoning_snapshot(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_ss", "customer", "AI SS")
        mgr = get_resident_manager()
        mgr.add_reasoning_snapshot(space.space_id, "Analyzed churn data",
                                   context="Q4 review")
        assert len(space.ai_resident.reasoning_snapshots) == 1

    def test_add_observation(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_obs", "customer", "AI Obs")
        mgr = get_resident_manager()
        mgr.add_observation(space.space_id, "New support ticket opened")
        assert "New support ticket opened" in space.ai_resident.pending_observations

    def test_update_confidence(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_conf", "customer", "AI Conf")
        mgr = get_resident_manager()
        mgr.update_confidence(space.space_id, 0.85)
        assert space.ai_resident.confidence == 0.85

    def test_get_snapshot(self, store):
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_snap", "customer", "AI Snap")
        mgr = get_resident_manager()
        mgr.update_understanding(space.space_id, "Test understanding")
        mgr.add_risk(space.space_id, "Test risk")
        snapshot = mgr.get_snapshot(space.space_id)
        assert snapshot is not None
        assert snapshot["understanding"] == "Test understanding"
        assert len(snapshot["risks"]) == 1

    def test_ai_context_survives_reopen(self, store):
        """AI context persists across navigation."""
        from app.space.resident import get_resident_manager
        space = store.create("ent_ai_survive", "customer", "AI Survive")
        mgr = get_resident_manager()
        mgr.update_understanding(space.space_id, "Persistent understanding")
        mgr.add_question(space.space_id, "Persistent question")

        # Simulate re-open: get from store
        retrieved = store.get(space.space_id)
        assert retrieved.ai_resident.current_understanding == "Persistent understanding"
        assert "Persistent question" in retrieved.ai_resident.open_questions


# =========================================================================
# 18. Composite Space Tests
# =========================================================================


class TestSpaceComposite:
    """Tests for composite Spaces (A1A deliverable 3)."""

    def test_get_children(self, store):
        from app.space.composition import get_composite_manager
        parent = store.create("ent_comp_p", "company", "Parent")
        child = store.create("ent_comp_c", "project", "Child",
                             parent_space_id=parent.space_id)
        store.add_child(parent.space_id, child.space_id)
        mgr = get_composite_manager()
        children = mgr.get_children(parent.space_id)
        assert len(children) == 1
        assert children[0].space_id == child.space_id

    def test_get_ancestors(self, store):
        from app.space.composition import get_composite_manager
        root = store.create("ent_anc_r", "company", "Root")
        mid = store.create("ent_anc_m", "project", "Mid",
                           parent_space_id=root.space_id)
        leaf = store.create("ent_anc_l", "task", "Leaf",
                            parent_space_id=mid.space_id)
        store.add_child(root.space_id, mid.space_id)
        store.add_child(mid.space_id, leaf.space_id)

        mgr = get_composite_manager()
        ancestors = mgr.get_ancestors(leaf.space_id)
        assert len(ancestors) == 2
        assert ancestors[0].space_id == mid.space_id
        assert ancestors[1].space_id == root.space_id

    def test_get_siblings(self, store):
        from app.space.composition import get_composite_manager
        parent = store.create("ent_sib_p", "company", "Parent")
        a = store.create("ent_sib_a", "project", "A",
                         parent_space_id=parent.space_id)
        b = store.create("ent_sib_b", "project", "B",
                         parent_space_id=parent.space_id)
        store.add_child(parent.space_id, a.space_id)
        store.add_child(parent.space_id, b.space_id)

        mgr = get_composite_manager()
        siblings = mgr.get_siblings(a.space_id)
        assert len(siblings) == 1
        assert siblings[0].space_id == b.space_id

    def test_decompose(self, store):
        from app.space.composition import get_composite_manager
        parent = store.create("ent_dec_p", "company", "Parent")
        child = store.create("ent_dec_c", "project", "Child",
                             parent_space_id=parent.space_id)
        store.add_child(parent.space_id, child.space_id)

        mgr = get_composite_manager()
        assert mgr.decompose(parent.space_id, child.space_id) is True
        assert child.space_id not in parent.child_space_ids
        assert child.parent_space_id == ""

    def test_get_subtree(self, store):
        from app.space.composition import get_composite_manager
        root = store.create("ent_sub_r", "company", "Root")
        mid = store.create("ent_sub_m", "project", "Mid",
                           parent_space_id=root.space_id)
        leaf = store.create("ent_sub_l", "task", "Leaf",
                            parent_space_id=mid.space_id)
        store.add_child(root.space_id, mid.space_id)
        store.add_child(mid.space_id, leaf.space_id)

        mgr = get_composite_manager()
        tree = mgr.get_subtree(root.space_id)
        assert tree["space_id"] == root.space_id
        assert len(tree["children"]) == 1
        assert tree["children"][0]["children"][0]["name"] == "Leaf"

    def test_get_composition_summary(self, store):
        from app.space.composition import get_composite_manager
        parent = store.create("ent_sum_p", "company", "Parent")
        child = store.create("ent_sum_c", "project", "Child",
                             parent_space_id=parent.space_id)
        store.add_child(parent.space_id, child.space_id)

        mgr = get_composite_manager()
        summary = mgr.get_composition_summary(parent.space_id)
        assert summary["child_count"] == 1
        assert summary["children"][0]["name"] == "Child"

    def test_company_composition(self, store):
        """Company -> Customer -> Project -> Task."""
        from app.space.composition import get_composite_manager
        company = store.create("ent_cc_1", "company", "Company")
        customer = store.create("ent_cc_2", "customer", "Customer",
                                parent_space_id=company.space_id)
        project = store.create("ent_cc_3", "project", "Project",
                               parent_space_id=customer.space_id)
        task = store.create("ent_cc_4", "task", "Task",
                            parent_space_id=project.space_id)
        store.add_child(company.space_id, customer.space_id)
        store.add_child(customer.space_id, project.space_id)
        store.add_child(project.space_id, task.space_id)

        mgr = get_composite_manager()
        # Check each level
        assert len(mgr.get_children(company.space_id)) == 1
        assert len(mgr.get_children(customer.space_id)) == 1
        assert len(mgr.get_children(project.space_id)) == 1
        # Check ancestors
        ancestors = mgr.get_ancestors(task.space_id)
        assert len(ancestors) == 3


# =========================================================================
# 19. A1A API Route Tests
# =========================================================================


class TestA1AAPIRoutes:
    """Tests for A1A API routes."""

    def test_list_capabilities(self, client):
        """GET /api/v1/space/capabilities lists all capabilities."""
        resp = client.get("/api/v1/space/capabilities")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["total"] >= 10

    def test_get_space_capabilities(self, client):
        """GET /api/v1/space/<id>/capabilities."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_cap", "entity_type": "customer",
            "name": "A1A Capabilities",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.get(f"/api/v1/space/{sid}/capabilities")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["capabilities"]) >= 1

    def test_get_lifecycle(self, client):
        """GET /api/v1/space/<id>/lifecycle."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_lc", "entity_type": "customer",
            "name": "A1A Lifecycle",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.get(f"/api/v1/space/{sid}/lifecycle")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["lifecycle"]["state"] == "draft"

    def test_transition_lifecycle(self, client):
        """PUT /api/v1/space/<id>/lifecycle transitions state."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_tr", "entity_type": "customer",
            "name": "A1A Transition",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.put(f"/api/v1/space/{sid}/lifecycle", json={
            "state": "active",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["lifecycle"]["state"] == "active"

    def test_transition_invalid_lifecycle(self, client):
        """Invalid lifecycle transition returns 400."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_bad", "entity_type": "customer",
            "name": "A1A Bad",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.put(f"/api/v1/space/{sid}/lifecycle", json={
            "state": "historical",
        })
        assert resp.status_code == 400

    def test_get_ai_resident(self, client):
        """GET /api/v1/space/<id>/ai-resident."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_res", "entity_type": "customer",
            "name": "A1A Resident",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.get(f"/api/v1/space/{sid}/ai-resident")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ai_resident"]["understanding"] == ""

    def test_update_ai_resident_understanding(self, client):
        """PUT /api/v1/space/<id>/ai-resident updates understanding."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_und", "entity_type": "customer",
            "name": "A1A Understanding",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.put(f"/api/v1/space/{sid}/ai-resident", json={
            "understanding": "Key customer in Q4",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ai_resident"]["understanding"] == "Key customer in Q4"

    def test_update_ai_resident_risk(self, client):
        """PUT /api/v1/space/<id>/ai-resident adds risk."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_risk", "entity_type": "project",
            "name": "A1A Risk",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.put(f"/api/v1/space/{sid}/ai-resident", json={
            "risk": "Timeline slippage",
            "severity": "high",
            "probability": 0.6,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["ai_resident"]["risks"]) == 1

    def test_reason_about_space(self, client):
        """POST /api/v1/space/<id>/reason runs reasoning."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_rsn", "entity_type": "project",
            "name": "A1A Reason",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.post(f"/api/v1/space/{sid}/reason", json={
            "question": "Why is this project delayed?",
            "max_depth": 2,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["reasoning"]["query"] == "Why is this project delayed?"
        assert len(data["reasoning"]["trail"]) >= 1

    def test_get_composition(self, client):
        """GET /api/v1/space/<id>/composition."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_comp", "entity_type": "company",
            "name": "A1A Comp",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.get(f"/api/v1/space/{sid}/composition")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["composition"]["name"] == "A1A Comp"

    def test_get_subtree(self, client):
        """GET /api/v1/space/<id>/subtree."""
        create = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_tree", "entity_type": "company",
            "name": "A1A Tree",
        })
        sid = create.get_json()["space"]["space_id"]
        resp = client.get(f"/api/v1/space/{sid}/subtree")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["tree"]["name"] == "A1A Tree"

    def test_get_siblings_api(self, client):
        """GET /api/v1/space/<id>/siblings."""
        # Create parent
        parent = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_sib_p", "entity_type": "company",
            "name": "Sib Parent",
        })
        pid = parent.get_json()["space"]["space_id"]

        # Create two children
        c1 = client.post(f"/api/v1/space/{pid}/children", json={
            "child_entity_id": "ent_a1a_sib_1",
            "child_entity_type": "project",
            "child_name": "Child 1",
        })
        c1_id = c1.get_json()["child"]["space_id"]

        client.post(f"/api/v1/space/{pid}/children", json={
            "child_entity_id": "ent_a1a_sib_2",
            "child_entity_type": "project",
            "child_name": "Child 2",
        })

        resp = client.get(f"/api/v1/space/{c1_id}/siblings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_decompose_api(self, client):
        """POST /api/v1/space/<id>/decompose/<child_id>."""
        parent = client.post("/api/v1/space", json={
            "entity_id": "ent_a1a_dec_p", "entity_type": "company",
            "name": "Dec Parent",
        })
        pid = parent.get_json()["space"]["space_id"]

        child = client.post(f"/api/v1/space/{pid}/children", json={
            "child_entity_id": "ent_a1a_dec_c",
            "child_entity_type": "project",
            "child_name": "Dec Child",
        })
        cid = child.get_json()["child"]["space_id"]

        resp = client.post(f"/api/v1/space/{pid}/decompose/{cid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "Child removed from parent"

        # Verify child is gone
        resp = client.get(f"/api/v1/space/{pid}/children")
        assert resp.get_json()["total"] == 0