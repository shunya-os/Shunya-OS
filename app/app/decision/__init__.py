"""SHUNYA — Decision Intelligence (Milestone V)

Evaluates possible courses of action and explains their consequences.
Never replaces human judgment, governance, or planning.

Produces a transparent decision space, not a single opaque answer.

Architecture:
  DecisionEngine          → Option generation, constraint, trade-off, ranking
  OptionGenerator         → Multiple feasible options (business-agnostic)
  ConstraintEngine        → Evaluate options against all constraints
  TradeoffAnalyzer        → Benefit, cost, risk, impact per option
  ObjectiveEngine         → Weighted multi-objective scoring
  ScenarioEvaluator       → Evaluate decisions under simulation scenarios
"""

from app.decision.models import (
    DecisionOption, DecisionConstraint, DecisionObjective,
    DecisionTradeoff, DecisionEvaluation, DecisionRecommendation,
    DecisionExplanation, DecisionSnapshot, DecisionContext,
    ObjectiveWeight, OptionGenerationRule, ScenarioEvalResult,
    DecisionConfig, DecisionFilter, DecisionStats,
    OptionCategory, ConstraintSeverity, RecommendationStatus,
)
from app.decision.engine import (
    DecisionEngine, OptionGenerator, ConstraintEngine,
    TradeoffAnalyzer, ObjectiveEngine, ScenarioEvaluator,
    get_decision_engine, reset_decision_engine,
)

__all__ = [
    "DecisionEngine", "OptionGenerator", "ConstraintEngine",
    "TradeoffAnalyzer", "ObjectiveEngine", "ScenarioEvaluator",
    "get_decision_engine", "reset_decision_engine",
    "DecisionOption", "DecisionConstraint", "DecisionObjective",
    "DecisionTradeoff", "DecisionEvaluation", "DecisionRecommendation",
    "DecisionExplanation", "DecisionSnapshot", "DecisionContext",
    "ObjectiveWeight", "OptionGenerationRule", "ScenarioEvalResult",
    "DecisionConfig", "DecisionFilter", "DecisionStats",
    "OptionCategory", "ConstraintSeverity", "RecommendationStatus",
]