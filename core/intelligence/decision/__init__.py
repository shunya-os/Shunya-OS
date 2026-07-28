"""
SHUNYA — Decision Engine

Public API for the Decision Engine. Manages the complete decision lifecycle
from CANDIDATE through evaluation, approval, execution, and completion.

Capabilities:
    - Decision lifecycle management (CANDIDATE → COMPLETED/FAILED)
    - Policy rule evaluation (deterministic)
    - Valid transition enforcement
    - Evidence sufficiency validation
    - Decision option management
    - AI-assisted escalation for option generation

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §9 (Decision Engine)
"""

from __future__ import annotations

from core.intelligence.decision.engine import DecisionEngine
from core.intelligence.decision.models import (
    DECISION_VALID_TRANSITIONS,
    DecisionEscalationRequest,
    DecisionOption,
    DecisionRecord,
    DecisionStatus,
    EvidenceSufficiency,
    PolicyRule,
)

__all__ = [
    "DECISION_VALID_TRANSITIONS",
    "DecisionEngine",
    "DecisionEscalationRequest",
    "DecisionOption",
    "DecisionRecord",
    "DecisionStatus",
    "EvidenceSufficiency",
    "PolicyRule",
]