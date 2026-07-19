"""SHUNYA — Learning Engine (Phase K — ES-007).

The Learning Engine transforms verified observations into long-term
improvement. It closes the Compounding Intelligence Loop by analyzing
observations, discovering patterns, evaluating outcomes, calibrating
confidence, and producing governance-validated proposals.

The engine implements a deterministic 9-stage pipeline:
  1. Learning Intake
  2. Pattern Discovery
  3. Correlation Analysis
  4. Outcome Evaluation
  5. Confidence Calibration
  6. Improvement Recommendation
  7. Knowledge Proposal
  8. Governance Review Package
  9. Continuous Learning Archive

The engine does NOT:
  - Modify knowledge directly (Knowledge Engine)
  - Bypass governance (Governance Engine)
  - Rewrite history (Immutability)
  - Fabricate learning (must be grounded in observations)
  - Execute actions (Executor Engine)
  - Approve changes (Governance Engine)
  - Mutate evidence (Architectural Invariant)

Architectural authority: ES-007 — Learning Engine Specification
"""

from app.shunya.learning_engine.models import (
    # Enums
    LearningType, PatternType, FrequencyTrend,
    RecurrenceType, KnowledgeProposalState, FailureMode,

    # Core models
    PatternScope, Recurrence, Pattern,
    LearningRecommendation, ConfidenceCalibration,
    OutcomeEvaluation, KnowledgeProposal, PerformanceInsight,
    LearningInput, LearningOutput,
    LearningStats,
)

from app.shunya.learning_engine.engine import (
    LearningEngine, get_learning_engine, reset_learning_engine,
)

# Legacy backward-compatible exports
from app.shunya.learning_engine._legacy_learning import (
    LearningLayer,
)

__all__ = [
    # Enums
    "LearningType", "PatternType", "FrequencyTrend",
    "RecurrenceType", "KnowledgeProposalState", "FailureMode",

    # Models
    "PatternScope", "Recurrence", "Pattern",
    "LearningRecommendation", "ConfidenceCalibration",
    "OutcomeEvaluation", "KnowledgeProposal", "PerformanceInsight",
    "LearningInput", "LearningOutput",
    "LearningStats",

    # Engine
    "LearningEngine", "get_learning_engine", "reset_learning_engine",

    # Legacy
    "LearningLayer",
]