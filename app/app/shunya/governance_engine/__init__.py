"""SHUNYA — Governance Engine (Phase H — ES-001).

The Governance Engine is the independent validation gate between Planning
and Execution. Every proposed action — whether a complex plan from the
Planner Layer or a single action request — must pass through governance
before reaching the Executor.

The engine implements a deterministic 6-stage pipeline:
  1. Input Validation
  2. Context Enrichment
  3. Constitutional Validation
  4. Policy Evaluation
  5. Risk Assessment
  6. Verdict Production

The engine does NOT:
  - Execute actions (Executor Engine)
  - Mutate knowledge (Knowledge Engine)
  - Reason on behalf of the Reasoning Engine
  - Access credentials (Credential Store)
  - Generate plans (Planner Engine)
  - Learn from outcomes (Learning Engine)
  - Observe reality (Observer Engine)

Architectural authority: ES-001 — Governance Engine Specification
"""

from app.shunya.governance_engine.models import (
    # Enums
    ActionType, VerdictDecision, PolicySeverity, PolicyScope,
    GovernanceState, FailureMode,

    # Core models
    Policy, PolicyViolation, PolicyRegistry,
    ContextEnrichment, AuditEntry,
    GovernanceInput, GovernanceVerdict,
    GovernanceStats,
)

from app.shunya.governance_engine.engine import (
    GovernanceEngine, get_governance_engine, reset_governance_engine,
)

# Legacy backward-compatible exports (maintains existing call sites)
from app.shunya.governance_engine._legacy_governance import (
    GovernanceLayer,
    GovernanceVerdict as LegacyGovernanceVerdict,
)

__all__ = [
    # Enums
    "ActionType", "VerdictDecision", "PolicySeverity", "PolicyScope",
    "GovernanceState", "FailureMode",

    # Core models
    "Policy", "PolicyViolation", "PolicyRegistry",
    "ContextEnrichment", "AuditEntry",
    "GovernanceInput", "GovernanceVerdict",
    "GovernanceStats",

    # Engine
    "GovernanceEngine", "get_governance_engine", "reset_governance_engine",

    # Legacy exports (backward compatibility)
    "GovernanceLayer",
]