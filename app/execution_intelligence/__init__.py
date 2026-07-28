"""SHUNYA — Execution Intelligence Engine (Phase N+2)

Deterministic intelligence layer on top of BusinessExecutionInstance.
Provides health assessment, timeline prediction, dependency analysis,
risk detection, next-action recommendations, portfolio aggregation,
and full explainability — all business-agnostic and evidence-backed.

Architecture:
  ExecutionHealthEngine       → Health scores + explanations
  TimelineIntelligenceEngine  → Progress tracking + completion prediction
  DependencyGraphEngine       → Critical path + bottleneck analysis
  RiskDetectionEngine         → At-risk detection + early warnings
  NextActionEngine            → Recommended next actions
  PortfolioIntelligence       → Cross-execution aggregation
  ExplainabilityLayer         → Traceable evidence for every output
  RuntimeService              → Coordination of all engines
  PublicAPI                   → Clean consumer interface
"""

from app.execution_intelligence.engine import (
    ExecutionIntelligenceEngine,
    get_execution_intelligence,
    reset_execution_intelligence,
    # Engines
    ExecutionHealthEngine,
    TimelineIntelligenceEngine,
    DependencyGraphEngine,
    RiskDetectionEngine,
    NextActionEngine,
    PortfolioIntelligence,
    ExplainabilityLayer,
)
from app.execution_intelligence.models import (
    # Core types
    HealthAssessment, HealthDimension, HealthStatus,
    TimelineSnapshot, CompletionPrediction,
    DependencyNode, DependencyEdge, CriticalPath,
    RiskAssessment, RiskLevel, RiskFactor,
    NextAction, ActionPriority,
    PortfolioSummary, PortfolioBreakdown,
    EvidenceTrace, Explanation,
    RuntimeConfig, QueryFilter,
)

__all__ = [
    "ExecutionIntelligenceEngine",
    "get_execution_intelligence",
    "reset_execution_intelligence",
    # Engines
    "ExecutionHealthEngine",
    "TimelineIntelligenceEngine",
    "DependencyGraphEngine",
    "RiskDetectionEngine",
    "NextActionEngine",
    "PortfolioIntelligence",
    "ExplainabilityLayer",
    # Core types
    "HealthAssessment", "HealthDimension", "HealthStatus",
    "TimelineSnapshot", "CompletionPrediction",
    "DependencyNode", "DependencyEdge", "CriticalPath",
    "RiskAssessment", "RiskLevel", "RiskFactor",
    "NextAction", "ActionPriority",
    "PortfolioSummary", "PortfolioBreakdown",
    "EvidenceTrace", "Explanation",
    "RuntimeConfig", "QueryFilter",
]
