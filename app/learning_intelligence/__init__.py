"""SHUNYA — Learning Intelligence Engine (Milestone II)

Continuously improves recommendations using historical evidence while
preserving deterministic, explainable behavior. Reads from existing
ClosedLearningLoop and ES-007 Learning Engine — never duplicates state.

Architecture:
  PatternRecognitionEngine    → Identify recurring patterns from outcomes
  OutcomeLearningEngine       → Learn success/failure rates per dimension
  RecommendationLearning      → Refine next-action recommendations
  ConfidenceModel             → Explicit factor-based confidence scoring
  SimilarityEngine            → Find similar executions/obligations
  OrganizationalLearning      → Cross-role and cross-unit learning patterns
  KnowledgeEvolution          → How learned insights evolve and decay
  LearningMemory              → Store and query learning artifacts
  ExplainabilityLayer         → Trace every learned conclusion to evidence
  RuntimeService              → Coordination of all engines
"""

from app.learning_intelligence.models import (
    LearningCategory, PatternStrength, ConfidenceFactor, SimilarityMetric,
    LearnedPattern, OutcomeProfile, RefinedRecommendation,
    ConfidenceAssessment, FactorContribution,
    SimilarExecution, SimilarityResult,
    OrgLearningProfile, OrgLearningInsight,
    KnowledgeEpoch, EvolutionEntry,
    LearningArtifact, LearningMemoryEntry,
    LearnerConfig, LearnerFilter, LearnerStats,
)
from app.learning_intelligence.engine import (
    LearningIntelligenceEngine,
    get_learning_intelligence,
    reset_learning_intelligence,
    PatternRecognitionEngine,
    OutcomeLearningEngine,
    RecommendationLearning,
    ConfidenceModel,
    SimilarityEngine,
    OrganizationalLearning,
    KnowledgeEvolution,
    LearningMemory,
    ExplainabilityLayer,
    RuntimeService,
)

__all__ = [
    "LearningIntelligenceEngine",
    "get_learning_intelligence", "reset_learning_intelligence",
    "PatternRecognitionEngine", "OutcomeLearningEngine",
    "RecommendationLearning", "ConfidenceModel",
    "SimilarityEngine", "OrganizationalLearning",
    "KnowledgeEvolution", "LearningMemory",
    "ExplainabilityLayer", "RuntimeService",
    "LearningCategory", "PatternStrength", "ConfidenceFactor", "SimilarityMetric",
    "LearnedPattern", "OutcomeProfile", "RefinedRecommendation",
    "ConfidenceAssessment", "FactorContribution",
    "SimilarExecution", "SimilarityResult",
    "OrgLearningProfile", "OrgLearningInsight",
    "KnowledgeEpoch", "EvolutionEntry",
    "LearningArtifact", "LearningMemoryEntry",
    "LearnerConfig", "LearnerFilter", "LearnerStats",
]