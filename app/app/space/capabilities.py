"""SHUNYA Phase A1A — Space Capability Framework.

Every Space advertises capabilities instead of assuming all panels
are equally relevant. Capabilities drive UI visibility rather than
hardcoded entity types.

Capability → Panel → Renderer → Widget

Applications register capabilities. The Space runtime discovers them.
No application may modify the Space model directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.space.models import UniversalSpace, SpacePanel


# =========================================================================
# Capability Definition
# =========================================================================


@dataclass
class Capability:
    """A capability that a Space can advertise.

    Capabilities are registered by applications and discovered
    by the Space runtime. They drive which panels are visible.
    """
    name: str
    label: str
    description: str = ""
    panels: List[SpacePanel] = field(default_factory=list)
    """Panels that this capability enables."""
    icon: str = "⚡"
    priority: int = 50
    """Lower priority = rendered first."""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "panels": [p.value for p in self.panels],
            "icon": self.icon,
            "priority": self.priority,
        }


# =========================================================================
# Built-in Capabilities
# =========================================================================

# Each capability maps to a set of panels.
# These are the canonical capabilities every Space can have.

CAPABILITY_COMMUNICATION = Capability(
    name="communication",
    label="Communication",
    description="Messages, emails, calls, meetings",
    panels=[SpacePanel.COMMUNICATIONS],
    icon="💬",
    priority=10,
)

CAPABILITY_PLANNING = Capability(
    name="planning",
    label="Planning",
    description="Plans, goals, milestones",
    panels=[SpacePanel.PLANS],
    icon="🎯",
    priority=20,
)

CAPABILITY_EXECUTION = Capability(
    name="execution",
    label="Execution",
    description="Active tasks, checkpoints, workflows",
    panels=[SpacePanel.EXECUTION],
    icon="⚡",
    priority=30,
)

CAPABILITY_FINANCE = Capability(
    name="finance",
    label="Finance",
    description="Invoices, payments, budgets, metrics",
    panels=[SpacePanel.METRICS],
    icon="💰",
    priority=40,
)

CAPABILITY_KNOWLEDGE = Capability(
    name="knowledge",
    label="Knowledge",
    description="Documents, files, notes, research",
    panels=[SpacePanel.KNOWLEDGE, SpacePanel.DOCUMENTS],
    icon="🧠",
    priority=50,
)

CAPABILITY_TIMELINE = Capability(
    name="timeline",
    label="Timeline",
    description="Chronological event history",
    panels=[SpacePanel.TIMELINE],
    icon="📅",
    priority=60,
)

CAPABILITY_RELATIONSHIPS = Capability(
    name="relationships",
    label="Relationships",
    description="Graph connections to other entities",
    panels=[SpacePanel.RELATIONSHIPS],
    icon="🔗",
    priority=70,
)

CAPABILITY_RESPONSIBILITIES = Capability(
    name="responsibilities",
    label="Responsibilities",
    description="Who owns what",
    panels=[SpacePanel.RESPONSIBILITIES],
    icon="👤",
    priority=80,
)

CAPABILITY_AI = Capability(
    name="ai",
    label="AI",
    description="AI understanding, insights, analysis",
    panels=[SpacePanel.AI_UNDERSTANDING],
    icon="🤖",
    priority=90,
)

CAPABILITY_CONTEXT = Capability(
    name="context",
    label="Context",
    description="Space state, position, continuity",
    panels=[SpacePanel.CONTEXT],
    icon="📋",
    priority=100,
)

# All capabilities registry
ALL_CAPABILITIES: Dict[str, Capability] = {
    "communication": CAPABILITY_COMMUNICATION,
    "planning": CAPABILITY_PLANNING,
    "execution": CAPABILITY_EXECUTION,
    "finance": CAPABILITY_FINANCE,
    "knowledge": CAPABILITY_KNOWLEDGE,
    "timeline": CAPABILITY_TIMELINE,
    "relationships": CAPABILITY_RELATIONSHIPS,
    "responsibilities": CAPABILITY_RESPONSIBILITIES,
    "ai": CAPABILITY_AI,
    "context": CAPABILITY_CONTEXT,
}


# =========================================================================
# Default Capability Profiles (illustrative only)
# =========================================================================

# Customer Space: Communication, Planning, Finance, Knowledge, Timeline, AI
CUSTOMER_CAPABILITIES = [
    "communication", "planning", "finance", "knowledge", "timeline", "ai",
]

# Knowledge Space: Knowledge, AI, Timeline
KNOWLEDGE_CAPABILITIES = [
    "knowledge", "ai", "timeline",
]

# Project Space: Planning, Execution, Timeline, Knowledge, Relationships
PROJECT_CAPABILITIES = [
    "planning", "execution", "timeline", "knowledge", "relationships",
]

# Supplier Space: Communication, Finance, Timeline, Relationships
SUPPLIER_CAPABILITIES = [
    "communication", "finance", "timeline", "relationships",
]

# Employee Space: Communication, Responsibilities, Timeline, Knowledge, AI
EMPLOYEE_CAPABILITIES = [
    "communication", "responsibilities", "timeline", "knowledge", "ai",
]

# Invoice Space: Finance, Timeline, Relationships
INVOICE_CAPABILITIES = [
    "finance", "timeline", "relationships",
]

# Company Space: Everything
COMPANY_CAPABILITIES = list(ALL_CAPABILITIES.keys())

# Default: minimal set for any unknown type
DEFAULT_CAPABILITIES = [
    "context", "relationships", "timeline", "ai",
]


# =========================================================================
# Capability Registry
# =========================================================================


class CapabilityRegistry:
    """Registry of capabilities and their Space-type mappings.

    Applications register capabilities.
    The Space runtime discovers them dynamically.
    No application may modify the Space model directly.
    """

    def __init__(self):
        self._capabilities: Dict[str, Capability] = dict(ALL_CAPABILITIES)
        self._type_mappings: Dict[str, List[str]] = {}
        """entity_type -> [capability_name, ...]"""

    # ------------------------------------------------------------------
    # Capability registration
    # ------------------------------------------------------------------

    def register_capability(self, capability: Capability) -> None:
        """Register a new capability type."""
        self._capabilities[capability.name] = capability

    def get_capability(self, name: str) -> Optional[Capability]:
        return self._capabilities.get(name)

    def list_capabilities(self) -> List[Capability]:
        return sorted(
            self._capabilities.values(),
            key=lambda c: c.priority,
        )

    # ------------------------------------------------------------------
    # Type-to-capability mapping
    # ------------------------------------------------------------------

    def map_type(self, entity_type: str,
                 capability_names: List[str]) -> None:
        """Map an entity type to a set of capabilities."""
        valid = [n for n in capability_names if n in self._capabilities]
        self._type_mappings[entity_type] = valid

    def get_capabilities_for(self, entity_type: str) -> List[Capability]:
        """Get capabilities for a Space type.

        Falls back to DEFAULT_CAPABILITIES if no mapping exists.
        """
        names = self._type_mappings.get(entity_type, DEFAULT_CAPABILITIES)
        return [
            self._capabilities[n] for n in names
            if n in self._capabilities
        ]

    def get_panels_for(self, entity_type: str) -> List[SpacePanel]:
        """Get all panels enabled by capabilities for this Space type."""
        panels = set()
        for cap in self.get_capabilities_for(entity_type):
            for p in cap.panels:
                panels.add(p)
        return sorted(panels, key=lambda p: list(SpacePanel).index(p))

    # ------------------------------------------------------------------
    # Dynamic discovery
    # ------------------------------------------------------------------

    def discover_capabilities(self, space: UniversalSpace) -> List[Capability]:
        """Discover capabilities for a Space instance.

        Checks type mapping first, then falls back to defaults.
        """
        return self.get_capabilities_for(space.entity_type)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self._capabilities = dict(ALL_CAPABILITIES)
        self._type_mappings.clear()

    def load_default_mappings(self) -> None:
        """Load the default capability profiles."""
        self.map_type("customer", CUSTOMER_CAPABILITIES)
        self.map_type("knowledge", KNOWLEDGE_CAPABILITIES)
        self.map_type("project", PROJECT_CAPABILITIES)
        self.map_type("supplier", SUPPLIER_CAPABILITIES)
        self.map_type("employee", EMPLOYEE_CAPABILITIES)
        self.map_type("invoice", INVOICE_CAPABILITIES)
        self.map_type("company", COMPANY_CAPABILITIES)


# =========================================================================
# Singleton
# =========================================================================

_registry: Optional[CapabilityRegistry] = None


def get_registry() -> CapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = None