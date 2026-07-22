"""SHUNYA — Reasoning Engine Foundation (Phase F — Canonical).

The Reasoning Engine evaluates a WorkspaceContext and produces an
immutable ReasoningResult that identifies:
  - What is true        (findings with finding_type="observation")
  - What is missing     (findings with finding_type="gap")
  - What is conflicting (contradictions)
  - What is risky       (findings with finding_type="risk")
  - What requires attention (attention_items)

The engine is DETERMINISTIC — identical inputs always produce
identical outputs. It does NOT generate plans, execute actions,
invoke LLMs, produce prompts, or make autonomous decisions.

Architectural authority: G5.7 — Canonical Phase F Architecture Decision

Deprecated aliases (one phase cycle):
  Observation -> Finding
  Conflict -> Contradiction
  Gap -> Finding (finding_type="gap")
  Risk -> Finding (finding_type="risk")
  ConflictSeverity -> ContradictionSeverity
  ConfidenceAssessment -> ConfidenceScore
  ObservationType -> FindingType
  GapSeverity -> FindingSeverity
  RiskSeverity -> FindingSeverity
"""

from app.shunya.reasoning.models import (
    ReasoningResult, Finding, Contradiction, Assumption, Constraint,
    ConfidenceScore, EvidenceReference, ReasoningMetadata,
    FindingType, FindingSeverity, ContradictionType,
    ContradictionSeverity, ConfidenceLevel,
    # Deprecated aliases (public for backward compatibility)
    Observation, Conflict, Gap, Risk,
    ConfidenceAssessment, ObservationType, ConflictSeverity,
    GapSeverity, RiskSeverity,
)
from app.shunya.reasoning.engine import (
    ReasoningEngine, get_reasoning_engine, reset_reasoning_engine,
)
from app.shunya.reasoning.registry import RuleRegistry, RuleDefinition, RuleResult
from app.shunya.reasoning.rules import register_standard_rules, ALL_STANDARD_RULES
from app.shunya.reasoning.confidence import ConfidenceEngine
from app.shunya.reasoning.evidence_graph import EvidenceGraph, EvidenceNode

__all__ = [
    "ReasoningResult", "Finding", "Contradiction", "Assumption", "Constraint",
    "ConfidenceScore", "EvidenceReference", "ReasoningMetadata",
    "FindingType", "FindingSeverity", "ContradictionType",
    "ContradictionSeverity", "ConfidenceLevel",
    "ReasoningEngine", "get_reasoning_engine", "reset_reasoning_engine",
    "RuleRegistry", "RuleDefinition", "RuleResult",
    "register_standard_rules", "ALL_STANDARD_RULES",
    "ConfidenceEngine",
    "EvidenceGraph", "EvidenceNode",
    # Deprecated aliases
    "Observation", "Conflict", "Gap", "Risk",
    "ConfidenceAssessment", "ObservationType", "ConflictSeverity",
    "GapSeverity", "RiskSeverity",
]