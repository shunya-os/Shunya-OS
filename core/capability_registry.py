"""
SHUNYAAI Capability Registry — Governed bridge between the intelligence
command surface and all SHUNYA capabilities.

Every capability defines:
  name:        canonical identifier
  purpose:     what it does
  inputs:      required context
  outputs:     what it produces
  permissions: required auth level
  can_read:    whether it can read data
  can_write:   whether it can modify data
  can_execute: whether it can execute actions
  engine:      the module that implements it
  status:      AVAILABLE / UNWIRED / DEPRECATED
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Capability:
    name: str
    purpose: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    can_read: bool = True
    can_write: bool = False
    can_execute: bool = False
    engine: str = ""
    status: str = "AVAILABLE"  # AVAILABLE | UNWIRED | DEPRECATED


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class CapabilityRegistry:
    """Canonical capability registry. Every SHUNYA capability is registered here."""

    def __init__(self):
        self._capabilities: dict[str, Capability] = {}

    def register(self, cap: Capability) -> None:
        self._capabilities[cap.name] = cap

    def get(self, name: str) -> Capability | None:
        return self._capabilities.get(name)

    def list(self, status: str | None = None) -> list[Capability]:
        if status:
            return [c for c in self._capabilities.values() if c.status == status]
        return list(self._capabilities.values())

    def find(self, query: str) -> list[Capability]:
        """Find capabilities matching a natural-language query."""
        q = query.lower()
        return [
            c for c in self._capabilities.values()
            if q in c.name.lower() or q in c.purpose.lower()
        ]

    def route(self, query: str) -> list[Capability]:
        """Route a query to the most relevant capabilities."""
        return self.find(query)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_registry: CapabilityRegistry | None = None


def get_registry() -> CapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
        _register_core_capabilities(_registry)
    return _registry


def _register_core_capabilities(r: CapabilityRegistry) -> None:
    """Register all core SHUNYA capabilities."""

    # --- Identity ---
    r.register(Capability(
        name="identity",
        purpose="Resolve user identity, session, and authentication",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="app.auth",
        status="AVAILABLE",
    ))

    # --- Memory ---
    r.register(Capability(
        name="memory",
        purpose="Store and retrieve user/workspace memory",
        permissions=["authenticated"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.memory",
        status="AVAILABLE",
    ))

    # --- Knowledge ---
    r.register(Capability(
        name="knowledge",
        purpose="Query and reason over ingested knowledge",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.knowledge_intelligence",
        status="UNWIRED",
    ))

    # --- Documents ---
    r.register(Capability(
        name="documents",
        purpose="Upload, extract, search, and retrieve documents",
        permissions=["authenticated"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.documents_api",
        status="AVAILABLE",
    ))

    # --- Search ---
    r.register(Capability(
        name="search",
        purpose="Universal search across all entities",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="app.search",
        status="AVAILABLE",
    ))

    # --- Objects ---
    r.register(Capability(
        name="objects",
        purpose="CRUD operations on business objects",
        permissions=["authenticated"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.objects",
        status="AVAILABLE",
    ))

    # --- Intelligence Engines ---
    r.register(Capability(
        name="perception",
        purpose="Perceive and interpret user input and environmental signals",
        inputs=["user_input", "context"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.intelligence.perception",
        status="UNWIRED",
    ))
    r.register(Capability(
        name="reasoning",
        purpose="Multi-step reasoning, inference, and logic",
        inputs=["question", "context", "evidence"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.intelligence.reasoning",
        status="UNWIRED",
    ))
    r.register(Capability(
        name="planning",
        purpose="Plan multi-step actions and workflows",
        inputs=["goal", "context", "capabilities"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.intelligence.planning",
        status="UNWIRED",
    ))
    r.register(Capability(
        name="decision",
        purpose="Evaluate options and make decisions",
        inputs=["options", "criteria", "context"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.intelligence.decision",
        status="UNWIRED",
    ))
    r.register(Capability(
        name="reflection",
        purpose="Self-evaluate and improve responses",
        inputs=["response", "outcome", "feedback"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.intelligence.reflection",
        status="UNWIRED",
    ))
    r.register(Capability(
        name="learning",
        purpose="Learn from feedback, outcomes, and patterns",
        inputs=["observation", "outcome", "feedback"],
        can_read=True, can_write=True, can_execute=False,
        engine="core.intelligence.learning",
        status="UNWIRED",
    ))
    r.register(Capability(
        name="confidence",
        purpose="Score confidence of responses and decisions",
        inputs=["response", "evidence", "context"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.intelligence.confidence",
        status="UNWIRED",
    ))

    # --- UCP Domain Engines ---
    r.register(Capability(
        name="relationships",
        purpose="Relationship intelligence — profile, trust, sentiment",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.relationship_intelligence",
        status="UNWIRED",
    ))
    r.register(Capability(
        name="finance",
        purpose="Financial intelligence — invoices, ledger, payments, budgets",
        permissions=["authenticated", "finance.read"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.financial_intelligence",
        status="UNWIRED",
    ))
    r.register(Capability(
        name="operations",
        purpose="Operations intelligence — workflows, jobs, execution",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.operations_intelligence",
        status="UNWIRED",
    ))

    # --- Execution ---
    r.register(Capability(
        name="execution",
        purpose="Execute actions, track outcomes, and produce evidence",
        permissions=["authenticated", "execution.execute"],
        can_read=True, can_write=True, can_execute=True,
        engine="app.execution_engine",
        status="AVAILABLE",
    ))

    # --- Search ---
    r.register(Capability(
        name="web_search",
        purpose="Search the web for external information",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="app.search",
        status="AVAILABLE",
    ))

    # --- CRM ---
    r.register(Capability(
        name="crm",
        purpose="Lead management, CRM lifecycle, follow-up",
        permissions=["authenticated", "crm.read"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.crm",
        status="AVAILABLE",
    ))

    # --- Finance Records ---
    r.register(Capability(
        name="invoices",
        purpose="Invoice management, approval, ledger, payment",
        permissions=["authenticated", "finance.read"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.finance",
        status="AVAILABLE",
    ))

    # --- Workspace ---
    r.register(Capability(
        name="workspace",
        purpose="Workspace context, switching, and isolation",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="app.workspace",
        status="AVAILABLE",
    ))
