"""SHUNYA Phase A1 — Space Package.
Phase A1A — Capabilities, lifecycle, composition, reasoning, AI resident.

The Universal SHUNYA Space is the primary interaction model.
Every entity in the Business Graph becomes a Space.
"""
from app.space.models import (
    UniversalSpace,
    SpaceIdentity, SpaceStatus, SpaceContext,
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
    get_executor, reset_executor, CommandExecutor,
    SpaceCommand, BUILTIN_COMMANDS,
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

# Phase A1A exports
from app.space.capabilities import (
    get_registry as get_capability_registry,
    reset_registry as reset_capability_registry,
    CapabilityRegistry, Capability, ALL_CAPABILITIES,
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

__all__ = [
    # Core model
    "UniversalSpace",
    "SpaceIdentity", "SpaceStatus", "SpaceContext",
    "SpaceRelationshipRef", "SpaceTimelineEvent", "SpaceKnowledgeItem",
    "SpacePlanRef", "SpaceExecutionRef", "SpaceCommunicationRef",
    "SpaceDocumentRef", "SpaceResponsibility", "SpaceMetric",
    "SpaceAIUnderstanding", "SpacePanel",

    # Store
    "get_store", "reset_store", "SpaceStore",

    # Renderer
    "get_renderer", "reset_renderer", "SpaceRenderer",
    "PanelRenderer", "PanelProvider", "PANEL_RENDERERS",
    "DEFAULT_PANEL_PROVIDERS", "Widget",

    # Navigation
    "get_navigator", "reset_navigator", "SpaceNavigator", "NavigationResult",

    # Context
    "get_context_manager", "reset_context_manager", "SpaceContextManager",

    # Commands
    "get_executor", "reset_executor", "CommandExecutor",
    "SpaceCommand", "BUILTIN_COMMANDS",

    # Timeline
    "get_timeline_manager", "reset_timeline_manager", "SpaceTimelineManager",

    # Knowledge
    "get_knowledge_manager", "reset_knowledge_manager",
    "SpaceKnowledgeManager",

    # Relationships
    "get_relationship_manager", "reset_relationship_manager",
    "SpaceRelationshipManager",

    # Capabilities (A1A)
    "get_capability_registry", "reset_capability_registry",
    "CapabilityRegistry", "Capability", "ALL_CAPABILITIES",

    # Lifecycle (A1A)
    "get_lifecycle_manager", "reset_lifecycle_manager",
    "LifecycleManager", "SpaceLifecycle", "LifecycleState",
    "LIFECYCLE_TRANSITIONS", "LIFECYCLE_EFFECTS",

    # Reasoning (A1A)
    "get_reasoner", "reset_reasoner",
    "CrossSpaceReasoner", "ReasoningQuery", "ReasoningResult", "ReasoningStep",

    # AI Resident (A1A)
    "get_resident_manager", "reset_resident_manager",
    "AIResidentManager", "AIResidentState",

    # Composition (A1A)
    "get_composite_manager", "reset_composite_manager",
    "CompositeSpaceManager",
]