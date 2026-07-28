"""SHUNYA — Context Fusion Engine (Phase M — ES-009).

Assembles bounded workspace context from identity, knowledge, and request
providers. Deterministic, budget-enforced, and fingerprinted.

Architectural authority: ES-009
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