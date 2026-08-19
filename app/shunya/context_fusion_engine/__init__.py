"""
SHUNYA — Context Fusion Engine

GATE 2.1 CONSOLIDATION: QUARANTINED — This module re-exports from
app/shunya/context/ which is itself a legacy duplicate of the canonical
context assembly at core/intelligence/context_assembly/.

The canonical persistent memory store is app/memory/ (MemoryService, FDA3).
The canonical runtime context assembly is core/intelligence/context_assembly/.

Kept for backward compatibility only. New code should use
core/intelligence/context_assembly/ for runtime context needs.
"""

# Re-export canonical types from existing implementation
from app.shunya.context.models import (
    ContextRequest, ContextSection, WorkspaceContext,
    BudgetReport, ContextProvenance,
)
from app.shunya.context.assembly import ContextAssembler
from app.shunya.context.engine import ContextFusionEngine
from app.shunya.context.providers import (
    ContextProvider, IdentityContextProvider,
    KnowledgeContextProvider, RequestContextProvider,
)
from app.shunya.context.budget import BudgetEnforcer
from app.shunya.context.fingerprint import Fingerprinter

__all__ = [
    "ContextRequest", "ContextSection", "WorkspaceContext",
    "BudgetReport", "ContextProvenance",
    "ContextAssembler", "ContextFusionEngine",
    "ContextProvider", "IdentityContextProvider",
    "KnowledgeContextProvider", "RequestContextProvider",
    "BudgetEnforcer", "Fingerprinter",
]