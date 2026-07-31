"""SHUNYA — Executive Intelligence (Milestone VI)

Final cognitive layer. Synthesizes validated organizational intelligence
into executive attention. Never invents information. Surfaces what
leadership should understand, why it matters, how urgent it is, what
decisions require attention, and what strategic action may be appropriate.

Architecture:
  ExecutiveSynthesisEngine   → Aggregate validated intelligence
  PriorityEngine             → Rank executive attention
  ExecutiveRiskIntelligence  → Strategic/operational risk aggregation
  ExecutiveOpportunityIntel  → Opportunity identification
  DecisionQueue              → Leadership decision surface
  ExecutiveHealthModel       → Multi-dimensional health, trend-aware
  ExecutiveNarrative         → Structured executive briefings
  ExecutiveAttentionModel    → Attention scoring and ranking
  ExecutiveExplainability    → Trace every insight to lineage
"""

from app.executive.models import (
    ExecutiveBrief, ExecutivePriority, ExecutiveRisk,
    ExecutiveOpportunity, ExecutiveDecisionRequest,
    ExecutiveHealth, ExecutiveTrend, ExecutiveNarrative,
    ExecutiveInsight, ExecutiveDigest,
    PriorityCategory, RiskCategory, OpportunityCategory,
    AttentionScore, HealthDimension, NarrativeSection,
    ExecutiveConfig, ExecutiveStats,
)
from app.executive.engine import (
    ExecutiveIntelligenceEngine,
    get_executive_engine, reset_executive_engine,
    ExecutiveSynthesisEngine, PriorityEngine,
    ExecutiveRiskIntelligence, ExecutiveOpportunityIntel,
    DecisionQueue, ExecutiveHealthModel,
    ExecutiveNarrativeGenerator, ExecutiveAttentionModel,
    ExecutiveExplainability,
)

__all__ = [
    "ExecutiveIntelligenceEngine",
    "get_executive_engine", "reset_executive_engine",
    "ExecutiveSynthesisEngine", "PriorityEngine",
    "ExecutiveRiskIntelligence", "ExecutiveOpportunityIntel",
    "DecisionQueue", "ExecutiveHealthModel",
    "ExecutiveNarrativeGenerator", "ExecutiveAttentionModel",
    "ExecutiveExplainability",
    "ExecutiveBrief", "ExecutivePriority", "ExecutiveRisk",
    "ExecutiveOpportunity", "ExecutiveDecisionRequest",
    "ExecutiveHealth", "ExecutiveTrend", "ExecutiveNarrative",
    "ExecutiveInsight", "ExecutiveDigest",
    "PriorityCategory", "RiskCategory", "OpportunityCategory",
    "AttentionScore", "HealthDimension", "NarrativeSection",
    "ExecutiveConfig", "ExecutiveStats",
]