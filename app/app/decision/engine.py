"""SHUNYA — Decision Intelligence Engine (Milestone V).

Evaluates possible courses of action and explains their consequences.
Never says "this is the correct decision."

Produces a transparent decision space: options, constraints, trade-offs,
objectives, rankings, and explanations.

Reads from all existing intelligence modules — never writes to them.
"""

from __future__ import annotations

import hashlib, time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.decision.models import (
    OptionCategory, ConstraintSeverity, RecommendationStatus,
    DecisionContext, DecisionOption, DecisionConstraint,
    DecisionObjective, DecisionTradeoff, ObjectiveWeight,
    DecisionEvaluation, DecisionRecommendation, DecisionExplanation,
    DecisionSnapshot, ScenarioEvalResult,
    OptionGenerationRule,
    DecisionConfig, DecisionFilter, DecisionStats,
)
from app.execution import (
    ExecutionService, BusinessExecutionInstance, ExecState, ObligationState,
)
from app.execution_intelligence import (
    get_execution_intelligence, ExecutionIntelligenceEngine,
    HealthStatus, ActionPriority, RiskLevel,
)
from app.learning_intelligence import (
    get_learning_intelligence, LearningIntelligenceEngine,
)
from app.prediction import (
    get_prediction_engine, PredictionAndSimulationEngine,
    PredictionCategory, SimulationInput, ScenarioBranch,
)
from app.orchestrator import (
    get_orchestrator, OrchestratorEngine,
)
from app.organizational import (
    get_organizational_intelligence, OrganizationalIntelligenceEngine,
)

# =========================================================================
# Singleton
# =========================================================================

_ENGINE: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = DecisionEngine()
    return _ENGINE


def reset_decision_engine() -> None:
    global _ENGINE
    _ENGINE = None


# =========================================================================
# 1. Option Generator
# =========================================================================

class OptionGenerator:
    """Generate multiple feasible decision options.

    Business-agnostic: uses execution state, not domain knowledge.
    Never fewer than one option.
    """

    def __init__(self, config: Optional[DecisionConfig] = None):
        self._config = config or DecisionConfig()
        self._rules = self._default_rules()

    def generate(self, ctx: DecisionContext) -> List[DecisionOption]:
        """Generate decision options based on context."""
        options: List[DecisionOption] = []
        exec_state = ctx.execution_state.get("state", "active")

        for rule in self._rules:
            if not self._rule_applies(rule, ctx):
                continue
            option = DecisionOption(
                category=rule.generate,
                label=self._label_for(rule.generate),
                description=self._description_for(rule.generate, exec_state),
                rationale=self._rationale_for(rule.generate, ctx),
            )
            options.append(option)

        # Always include PROCEED and MARK_INFEASIBLE as fallbacks
        if not any(o.category == OptionCategory.PROCEED.value for o in options):
            options.append(DecisionOption(
                category=OptionCategory.PROCEED.value,
                label="Proceed as planned",
                description="Continue execution without changes.",
                rationale="Default option — proceed is always available.",
            ))
        if not any(o.category == OptionCategory.MARK_INFEASIBLE.value for o in options):
            options.append(DecisionOption(
                category=OptionCategory.MARK_INFEASIBLE.value,
                label="Mark infeasible",
                description="Declare execution infeasible under current constraints.",
                rationale="Fallback — infeasibility is always an option.",
            ))

        # Cap at max
        max_opts = self._config.max_options_generated
        if len(options) > max_opts:
            options = options[:max_opts]

        for o in options:
            if not o.option_id:
                raw = f"opt:{o.category}:{ctx.execution_id}:{ctx.tenant_id}"
                o.option_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

        return options

    def _default_rules(self) -> List[OptionGenerationRule]:
        return [
            OptionGenerationRule("r1", ["blocked", "at_risk"], OptionCategory.PROCEED.value,
                                 "state in (blocked, at_risk) and can_unblock", 10),
            OptionGenerationRule("r2", ["active", "blocked"], OptionCategory.DELAY.value,
                                 "has_overdue_obligations", 20),
            OptionGenerationRule("r3", ["blocked", "at_risk", "failed"],
                                 OptionCategory.ESCALATE.value, "has_active_exceptions", 30),
            OptionGenerationRule("r4", ["blocked", "active"],
                                 OptionCategory.DELEGATE.value, "has_assignable_obligations", 40),
            OptionGenerationRule("r5", ["blocked", "at_risk"],
                                 OptionCategory.REQUEST_APPROVAL.value, "pending_approval_required", 50),
            OptionGenerationRule("r6", ["blocked", "active"],
                                 OptionCategory.ACQUIRE_RESOURCES.value, "resource_shortfall", 60),
            OptionGenerationRule("r7", ["active"],
                                 OptionCategory.SPLIT_EXECUTION.value, "multiple_independent_obligations", 70),
            OptionGenerationRule("r8", ["active", "blocked", "at_risk"],
                                 OptionCategory.REVISE_COMMITMENT.value, "commitment_scope_changed", 80),
            OptionGenerationRule("r9", ["active", "blocked", "at_risk", "failed"],
                                 OptionCategory.RE_PLAN.value, "current_plan_ineffective", 90),
        ]

    def _rule_applies(self, rule: OptionGenerationRule, ctx: DecisionContext) -> bool:
        state = ctx.execution_state.get("state", "active")
        if state not in rule.trigger_states:
            return False
        return True  # Simplified — real condition evaluation would check ctx fields

    def _label_for(self, category: str) -> str:
        labels = {
            OptionCategory.PROCEED.value: "Proceed as planned",
            OptionCategory.DELAY.value: "Delay execution",
            OptionCategory.ESCALATE.value: "Escalate to supervisor",
            OptionCategory.DELEGATE.value: "Delegate obligations",
            OptionCategory.REQUEST_APPROVAL.value: "Request approval",
            OptionCategory.ACQUIRE_RESOURCES.value: "Acquire additional resources",
            OptionCategory.SPLIT_EXECUTION.value: "Split into sub-executions",
            OptionCategory.REVISE_COMMITMENT.value: "Revise commitment scope",
            OptionCategory.RE_PLAN.value: "Re-plan execution",
            OptionCategory.MARK_INFEASIBLE.value: "Mark infeasible",
        }
        return labels.get(category, category)

    def _description_for(self, category: str, state: str) -> str:
        descs = {
            OptionCategory.PROCEED.value: f"Continue execution in current state ({state}).",
            OptionCategory.DELAY.value: "Postpone execution to resolve blocking issues.",
            OptionCategory.ESCALATE.value: "Escalate decision to higher authority.",
            OptionCategory.DELEGATE.value: "Reassign obligations to available roles.",
            OptionCategory.REQUEST_APPROVAL.value: "Submit for governance approval.",
            OptionCategory.ACQUIRE_RESOURCES.value: "Allocate additional budget or personnel.",
            OptionCategory.SPLIT_EXECUTION.value: "Divide execution into independent sub-executions.",
            OptionCategory.REVISE_COMMITMENT.value: "Adjust commitment parameters to match reality.",
            OptionCategory.RE_PLAN.value: "Generate new execution plan from current state.",
            OptionCategory.MARK_INFEASIBLE.value: "Execution cannot proceed under current constraints.",
        }
        return descs.get(category, category)

    def _rationale_for(self, category: str, ctx: DecisionContext) -> str:
        rationales = {
            OptionCategory.PROCEED.value: "Execution is in viable state with no blocking constraints.",
            OptionCategory.DELAY.value: "Delaying may resolve timeline conflicts.",
            OptionCategory.ESCALATE.value: "Decision requires authority beyond current scope.",
            OptionCategory.DELEGATE.value: "Available roles may reduce workload on current assignee.",
            OptionCategory.REQUEST_APPROVAL.value: "Policy requires approval for this action.",
            OptionCategory.ACQUIRE_RESOURCES.value: "Current resource allocation is insufficient.",
            OptionCategory.SPLIT_EXECUTION.value: "Parallel execution may reduce overall timeline.",
            OptionCategory.REVISE_COMMITMENT.value: "Current commitment scope no longer matches reality.",
            OptionCategory.RE_PLAN.value: "Current plan metrics suggest suboptimal path.",
            OptionCategory.MARK_INFEASIBLE.value: "No viable path forward under current constraints.",
        }
        return rationales.get(category, category)


# =========================================================================
# 2. Constraint Engine
# =========================================================================

class ConstraintEngine:
    """Evaluate every option against all constraints.

    Constraints: governance, policy, resource, execution state,
    organizational ownership, risk tolerance, deadlines, objectives.
    All violations are explicit.
    """

    def evaluate(self, option: DecisionOption, ctx: DecisionContext,
                 exec_svc: Optional[ExecutionService] = None) -> List[DecisionConstraint]:
        constraints: List[DecisionConstraint] = []

        # C1: State transition validity
        state = ctx.execution_state.get("state", "active")
        constraints.append(self._check_state_transition(option.category, state))

        # C2: Resource availability
        constraints.append(self._check_resources(option.category, ctx))

        # C3: Organizational ownership
        constraints.append(self._check_ownership(option.category, ctx))

        # C4: Deadline feasibility
        constraints.append(self._check_deadlines(option.category, ctx))

        # C5: Risk tolerance
        constraints.append(self._check_risk(option.category, ctx))

        # C6: Governance compatibility
        constraints.append(self._check_governance(option.category, ctx))

        # C7: Prediction consistency
        constraints.append(self._check_prediction(option.category, ctx))

        option.constraints = constraints
        return constraints

    def _check_state_transition(self, category: str, state: str) -> DecisionConstraint:
        allowed = {
            OptionCategory.PROCEED.value: ["active", "pending"],
            OptionCategory.DELAY.value: ["active", "blocked", "at_risk"],
            OptionCategory.ESCALATE.value: ["blocked", "at_risk", "active"],
            OptionCategory.DELEGATE.value: ["active", "blocked"],
            OptionCategory.REQUEST_APPROVAL.value: ["active", "blocked", "at_risk"],
            OptionCategory.ACQUIRE_RESOURCES.value: ["active", "blocked"],
            OptionCategory.SPLIT_EXECUTION.value: ["active"],
            OptionCategory.REVISE_COMMITMENT.value: ["active", "blocked", "at_risk", "pending"],
            OptionCategory.RE_PLAN.value: ["active", "blocked", "at_risk", "failed"],
            OptionCategory.MARK_INFEASIBLE.value: ["blocked", "at_risk", "failed"],
        }
        allowed_states = allowed.get(category, ["active"])
        violated = state not in allowed_states
        return DecisionConstraint(
            name="state_transition_validity",
            description=f"Option {category} valid for state {state}",
            severity=ConstraintSeverity.FATAL.value if violated else ConstraintSeverity.INFO.value,
            violated=violated,
            detail=f"State '{state}' not in allowed states {allowed_states}" if violated else "OK",
            source="execution_state",
        )

    def _check_resources(self, category: str, ctx: DecisionContext) -> DecisionConstraint:
        alloc = ctx.execution_state.get("resource_allocations", [])
        cons = ctx.execution_state.get("resource_consumptions", [])
        utilization = 0.0
        allocated = sum(a.get("quantity", 0) for a in alloc if isinstance(a, dict))
        consumed = sum(c.get("quantity", 0) for c in cons if isinstance(c, dict))
        if allocated > 0:
            utilization = consumed / allocated
        violated = utilization > 0.95 and category in (
            OptionCategory.PROCEED.value, OptionCategory.ACQUIRE_RESOURCES.value)
        return DecisionConstraint(
            name="resource_availability",
            description=f"Resource utilization: {utilization:.1%}",
            severity=ConstraintSeverity.HIGH.value if violated else ConstraintSeverity.LOW.value,
            violated=violated,
            detail=f"Utilization {utilization:.1%} may be insufficient" if violated else f"Utilization {utilization:.1%}",
            source="resources",
        )

    def _check_ownership(self, category: str, ctx: DecisionContext) -> DecisionConstraint:
        org = ctx.organization_state.get("insights", [])
        violated = category == OptionCategory.DELEGATE.value and not org
        return DecisionConstraint(
            name="organizational_ownership",
            description="Available org roles for delegation",
            severity=ConstraintSeverity.MEDIUM.value if violated else ConstraintSeverity.INFO.value,
            violated=violated,
            detail="No org insights available for delegation" if violated else "Roles available",
            source="organizational",
        )

    def _check_deadlines(self, category: str, ctx: DecisionContext) -> DecisionConstraint:
        has_due = ctx.execution_state.get("obligations", [])
        violated = category == OptionCategory.DELAY.value and not has_due
        return DecisionConstraint(
            name="deadline_feasibility",
            description="Delay feasible given deadlines",
            severity=ConstraintSeverity.LOW.value,
            violated=violated,
            detail="No due obligations to delay" if violated else "Deadlines present",
            source="execution",
        )

    def _check_risk(self, category: str, ctx: DecisionContext) -> DecisionConstraint:
        risk_level = ctx.prediction_snapshot.get("risk_level", "low")
        high_risk = risk_level in ("high", "critical")
        violated = high_risk and category == OptionCategory.PROCEED.value
        return DecisionConstraint(
            name="risk_tolerance",
            description=f"Current risk level: {risk_level}",
            severity=ConstraintSeverity.HIGH.value if violated else ConstraintSeverity.INFO.value,
            violated=violated,
            detail=f"High risk ({risk_level}) may make proceed inadvisable" if violated else "Risk acceptable",
            source="prediction",
        )

    def _check_governance(self, category: str, ctx: DecisionContext) -> DecisionConstraint:
        gov = ctx.governance_state.get("approved", True)
        violated = not gov and category in (
            OptionCategory.PROCEED.value, OptionCategory.RE_PLAN.value)
        return DecisionConstraint(
            name="governance_compatibility",
            description="Option compatible with governance decisions",
            severity=ConstraintSeverity.FATAL.value if violated else ConstraintSeverity.INFO.value,
            violated=violated,
            detail="Governance has not approved proceeding" if violated else "Governance OK",
            source="governance",
        )

    def _check_prediction(self, category: str, ctx: DecisionContext) -> DecisionConstraint:
        delay_prob = ctx.prediction_snapshot.get("delay_probability", 0.0)
        violated = delay_prob > 0.8 and category == OptionCategory.DELAY.value
        return DecisionConstraint(
            name="prediction_consistency",
            description=f"Delay probability: {delay_prob:.1%}",
            severity=ConstraintSeverity.MEDIUM.value if violated else ConstraintSeverity.INFO.value,
            violated=violated,
            detail="Delay already highly probable" if violated else "Consistent with predictions",
            source="prediction",
        )


# =========================================================================
# 3. Trade-off Analyzer
# =========================================================================

class TradeoffAnalyzer:
    """Calculate trade-offs for every option.

    Dimensions: expected benefit, cost, risk, organizational impact,
    timeline impact, resource impact, prediction confidence, opportunity cost.
    Every trade-off cites evidence.
    """

    def analyze(self, option: DecisionOption, ctx: DecisionContext,
                exec_intel: Optional[ExecutionIntelligenceEngine] = None,
                learn_intel: Optional[LearningIntelligenceEngine] = None
                ) -> List[DecisionTradeoff]:
        tradeoffs: List[DecisionTradeoff] = []

        tradeoffs.append(self._calc_benefit(option.category, ctx))
        tradeoffs.append(self._calc_cost(option.category, ctx))
        tradeoffs.append(self._calc_risk(option.category, ctx))
        tradeoffs.append(self._calc_org_impact(option.category, ctx))
        tradeoffs.append(self._calc_timeline(option.category, ctx))
        tradeoffs.append(self._calc_resource(option.category, ctx))
        tradeoffs.append(self._calc_confidence(option.category, ctx))
        tradeoffs.append(self._calc_opportunity_cost(option.category, ctx))

        option.tradeoffs = tradeoffs
        return tradeoffs

    def _calc_benefit(self, category: str, ctx: DecisionContext) -> DecisionTradeoff:
        base = {
            OptionCategory.PROCEED.value: 0.7,
            OptionCategory.DELAY.value: 0.5,
            OptionCategory.ESCALATE.value: 0.6,
            OptionCategory.DELEGATE.value: 0.5,
            OptionCategory.REQUEST_APPROVAL.value: 0.4,
            OptionCategory.ACQUIRE_RESOURCES.value: 0.7,
            OptionCategory.SPLIT_EXECUTION.value: 0.6,
            OptionCategory.REVISE_COMMITMENT.value: 0.5,
            OptionCategory.RE_PLAN.value: 0.5,
            OptionCategory.MARK_INFEASIBLE.value: 0.2,
        }
        score = base.get(category, 0.5)
        return DecisionTradeoff(
            dimension="benefit", score=score,
            evidence=[f"category={category}", f"base_score={score}"],
            detail=f"Expected benefit of {category} option",
        )

    def _calc_cost(self, category: str, ctx: DecisionContext) -> DecisionTradeoff:
        base = {
            OptionCategory.PROCEED.value: 0.8,
            OptionCategory.DELAY.value: 0.5,
            OptionCategory.ESCALATE.value: 0.4,
            OptionCategory.DELEGATE.value: 0.6,
            OptionCategory.REQUEST_APPROVAL.value: 0.7,
            OptionCategory.ACQUIRE_RESOURCES.value: 0.3,
            OptionCategory.SPLIT_EXECUTION.value: 0.4,
            OptionCategory.REVISE_COMMITMENT.value: 0.5,
            OptionCategory.RE_PLAN.value: 0.4,
            OptionCategory.MARK_INFEASIBLE.value: 0.1,
        }
        # Cost is inverted: higher score = lower cost
        score = base.get(category, 0.5)
        return DecisionTradeoff(
            dimension="cost", score=score,
            evidence=[f"category={category}", f"cost_efficiency={score}"],
            detail=f"Cost efficiency of {category} option",
        )

    def _calc_risk(self, category: str, ctx: DecisionContext) -> DecisionTradeoff:
        base = {
            OptionCategory.PROCEED.value: 0.6,
            OptionCategory.DELAY.value: 0.5,
            OptionCategory.ESCALATE.value: 0.7,
            OptionCategory.DELEGATE.value: 0.6,
            OptionCategory.REQUEST_APPROVAL.value: 0.7,
            OptionCategory.ACQUIRE_RESOURCES.value: 0.5,
            OptionCategory.SPLIT_EXECUTION.value: 0.5,
            OptionCategory.REVISE_COMMITMENT.value: 0.6,
            OptionCategory.RE_PLAN.value: 0.5,
            OptionCategory.MARK_INFEASIBLE.value: 0.3,
        }
        score = base.get(category, 0.5)
        return DecisionTradeoff(
            dimension="risk", score=score,
            evidence=[f"category={category}", f"risk_exposure={score}"],
            detail=f"Risk exposure of {category} option",
        )

    def _calc_org_impact(self, category: str, ctx: DecisionContext) -> DecisionTradeoff:
        base = {
            OptionCategory.PROCEED.value: 0.7,
            OptionCategory.DELAY.value: 0.5,
            OptionCategory.ESCALATE.value: 0.3,
            OptionCategory.DELEGATE.value: 0.5,
            OptionCategory.REQUEST_APPROVAL.value: 0.6,
            OptionCategory.ACQUIRE_RESOURCES.value: 0.4,
            OptionCategory.SPLIT_EXECUTION.value: 0.5,
            OptionCategory.REVISE_COMMITMENT.value: 0.5,
            OptionCategory.RE_PLAN.value: 0.5,
            OptionCategory.MARK_INFEASIBLE.value: 0.2,
        }
        score = base.get(category, 0.5)
        return DecisionTradeoff(
            dimension="organizational_impact", score=score,
            evidence=[f"category={category}", f"org_impact={score}"],
            detail=f"Organizational impact of {category}",
        )

    def _calc_timeline(self, category: str, ctx: DecisionContext) -> DecisionTradeoff:
        base = {
            OptionCategory.PROCEED.value: 0.7,
            OptionCategory.DELAY.value: 0.3,
            OptionCategory.ESCALATE.value: 0.4,
            OptionCategory.DELEGATE.value: 0.5,
            OptionCategory.REQUEST_APPROVAL.value: 0.4,
            OptionCategory.ACQUIRE_RESOURCES.value: 0.5,
            OptionCategory.SPLIT_EXECUTION.value: 0.6,
            OptionCategory.REVISE_COMMITMENT.value: 0.5,
            OptionCategory.RE_PLAN.value: 0.4,
            OptionCategory.MARK_INFEASIBLE.value: 0.1,
        }
        score = base.get(category, 0.5)
        return DecisionTradeoff(
            dimension="timeline_impact", score=score,
            evidence=[f"category={category}", f"timeline_score={score}"],
            detail=f"Timeline impact of {category} option",
        )

    def _calc_resource(self, category: str, ctx: DecisionContext) -> DecisionTradeoff:
        base = {
            OptionCategory.PROCEED.value: 0.7,
            OptionCategory.DELAY.value: 0.5,
            OptionCategory.ESCALATE.value: 0.6,
            OptionCategory.DELEGATE.value: 0.5,
            OptionCategory.REQUEST_APPROVAL.value: 0.6,
            OptionCategory.ACQUIRE_RESOURCES.value: 0.3,
            OptionCategory.SPLIT_EXECUTION.value: 0.4,
            OptionCategory.REVISE_COMMITMENT.value: 0.5,
            OptionCategory.RE_PLAN.value: 0.5,
            OptionCategory.MARK_INFEASIBLE.value: 0.2,
        }
        score = base.get(category, 0.5)
        return DecisionTradeoff(
            dimension="resource_impact", score=score,
            evidence=[f"category={category}", f"resource_efficiency={score}"],
            detail=f"Resource impact of {category}",
        )

    def _calc_confidence(self, category: str, ctx: DecisionContext) -> DecisionTradeoff:
        pred_conf = min(0.9, max(0.3, len(ctx.prediction_snapshot) * 0.1))
        # Combine with category-specific confidence
        base = {
            OptionCategory.PROCEED.value: 0.7,
            OptionCategory.DELAY.value: 0.5,
            OptionCategory.MARK_INFEASIBLE.value: 0.9,
        }
        cat_conf = base.get(category, 0.6)
        score = (pred_conf + cat_conf) / 2
        return DecisionTradeoff(
            dimension="prediction_confidence", score=score,
            evidence=[f"prediction_data={len(ctx.prediction_snapshot)}",
                      f"category_confidence={cat_conf}"],
            detail=f"Confidence in predictions for this option",
        )

    def _calc_opportunity_cost(self, category: str, ctx: DecisionContext) -> DecisionTradeoff:
        # Opportunity cost is the inverse of expected benefit of alternative options
        base = {
            OptionCategory.PROCEED.value: 0.5,
            OptionCategory.DELAY.value: 0.4,
            OptionCategory.ESCALATE.value: 0.4,
            OptionCategory.DELEGATE.value: 0.5,
            OptionCategory.REQUEST_APPROVAL.value: 0.5,
            OptionCategory.ACQUIRE_RESOURCES.value: 0.4,
            OptionCategory.SPLIT_EXECUTION.value: 0.5,
            OptionCategory.REVISE_COMMITMENT.value: 0.5,
            OptionCategory.RE_PLAN.value: 0.5,
            OptionCategory.MARK_INFEASIBLE.value: 0.7,
        }
        # Higher score = lower opportunity cost (inverted)
        score = base.get(category, 0.5)
        return DecisionTradeoff(
            dimension="opportunity_cost", score=score,
            evidence=[f"category={category}", f"opp_cost={score}"],
            detail=f"Opportunity cost of {category} option",
        )


# =========================================================================
# 4. Objective Engine
# =========================================================================

class ObjectiveEngine:
    """Score options against multiple weighted objectives.

    Objectives are transparent and weighted. Default set:
    - completion_probability (25%)
    - delay_minimization (20%)
    - cost_efficiency (15%)
    - risk_reduction (20%)
    - resource_efficiency (20%)
    """

    def __init__(self, config: Optional[DecisionConfig] = None):
        self._config = config or DecisionConfig()

    def score(self, option: DecisionOption, ctx: DecisionContext,
              objectives: Optional[List[DecisionObjective]] = None) -> float:
        if not objectives:
            objectives = self._default_objectives()

        total_weight = sum(o.weight for o in objectives)
        if total_weight == 0:
            return 0.0

        weighted_sum = 0.0
        for obj in objectives:
            score = self._score_objective(obj, option, ctx)
            obj.current_score = score
            weighted_sum += score * obj.weight

        option.overall_score = weighted_sum / total_weight
        return option.overall_score

    def _default_objectives(self) -> List[DecisionObjective]:
        return [
            DecisionObjective(objective_id="obj1", name="completion_probability",
                              description="Maximize probability of completion",
                              weight=0.25, direction="maximize"),
            DecisionObjective(objective_id="obj2", name="delay_minimization",
                              description="Minimize expected delay",
                              weight=0.20, direction="minimize"),
            DecisionObjective(objective_id="obj3", name="cost_efficiency",
                              description="Maximize resource efficiency",
                              weight=0.15, direction="maximize"),
            DecisionObjective(objective_id="obj4", name="risk_reduction",
                              description="Minimize risk exposure",
                              weight=0.20, direction="minimize"),
            DecisionObjective(objective_id="obj5", name="resource_efficiency",
                              description="Maximize resource efficiency",
                              weight=0.20, direction="maximize"),
        ]

    def _score_objective(self, obj: DecisionObjective, option: DecisionOption,
                         ctx: DecisionContext) -> float:
        tradeoff_map = {
            "completion_probability": "benefit",
            "delay_minimization": "timeline_impact",
            "cost_efficiency": "cost",
            "risk_reduction": "risk",
            "resource_efficiency": "resource_impact",
        }
        dim = tradeoff_map.get(obj.name)
        if dim:
            for t in option.tradeoffs:
                if t.dimension == dim:
                    score = t.score
                    if obj.direction == "minimize":
                        score = 1.0 - score
                    return score
        return 0.5

    def get_objectives(self, ctx: DecisionContext) -> List[DecisionObjective]:
        if ctx.objectives:
            return ctx.objectives
        return self._default_objectives()


# =========================================================================
# 5. Scenario Evaluator
# =========================================================================

class ScenarioEvaluator:
    """Evaluate decision options under multiple scenarios.

    For each option, assesses: current reality, best case, worst case,
    and alternative scenarios. Presents comparison.
    """

    def evaluate(self, option: DecisionOption, ctx: DecisionContext,
                 pred_engine: Optional[PredictionAndSimulationEngine] = None
                 ) -> ScenarioEvalResult:
        base_score = option.overall_score

        # Current reality
        current = {"score": base_score, "scenario": "current_reality"}

        # Best case: optimistic adjustment
        best = {"score": min(1.0, base_score * 1.3), "scenario": "best_case"}

        # Worst case: pessimistic adjustment
        worst = {"score": max(0.0, base_score * 0.6), "scenario": "worst_case"}

        # Consensus: average of all scenarios
        consensus = (current["score"] + best["score"] + worst["score"]) / 3

        return ScenarioEvalResult(
            option_id=option.option_id,
            option_label=option.label,
            current_reality=current,
            best_case=best,
            worst_case=worst,
            consensus_score=round(consensus, 4),
            evidence=[f"base_score={base_score:.2f}",
                      f"best={best['score']:.2f}", f"worst={worst['score']:.2f}"],
        )


# =========================================================================
# 6. Decision Engine (Facade)
# =========================================================================

class DecisionEngine:
    """Facade over all Decision Intelligence components.

    Produces a transparent decision space: feasible options, constraints,
    trade-offs, objective scores, rankings, and explanations.

    Never says "this is the correct decision."
    """

    def __init__(self, config: Optional[DecisionConfig] = None):
        self._config = config or DecisionConfig()
        self._option_gen = OptionGenerator(config)
        self._constraint_eng = ConstraintEngine()
        self._tradeoff = TradeoffAnalyzer()
        self._objectives = ObjectiveEngine(config)
        self._scenario_eval = ScenarioEvaluator()
        self._evaluations: List[DecisionEvaluation] = []
        self._latencies: List[float] = []

    @property
    def option_gen(self) -> OptionGenerator:
        return self._option_gen
    @property
    def constraint_eng(self) -> ConstraintEngine:
        return self._constraint_eng
    @property
    def tradeoff_analyzer(self) -> TradeoffAnalyzer:
        return self._tradeoff
    @property
    def objective_eng(self) -> ObjectiveEngine:
        return self._objectives

    def evaluate(self, ctx: DecisionContext,
                 exec_svc: Optional[ExecutionService] = None) -> DecisionEvaluation:
        """Full decision evaluation: generate, constrain, trade-off, score, rank."""
        start = time.time()

        # 1. Generate options
        options = self._option_gen.generate(ctx)

        # 2. Evaluate constraints
        for opt in options:
            self._constraint_eng.evaluate(opt, ctx, exec_svc)

        # 3. Analyze trade-offs
        for opt in options:
            self._tradeoff.analyze(opt, ctx)

        # 4. Score against objectives
        objectives = self._objectives.get_objectives(ctx)
        for opt in options:
            self._objectives.score(opt, ctx, objectives)

        # 5. Rank options
        options.sort(key=lambda o: o.overall_score, reverse=True)

        # 6. Separate feasible vs infeasible
        feasible = [o for o in options
                    if not any(c.violated and c.severity == ConstraintSeverity.FATAL.value
                               for c in o.constraints)]
        infeasible = [o for o in options if o not in feasible]

        # 7. Build recommendation
        top = feasible[0] if feasible else (options[0] if options else None)
        recommendation = DecisionRecommendation(
            ranked_options=feasible,
            rejected_options=infeasible,
            top_option_id=top.option_id if top else None,
            rationale=f"Top option: {top.label if top else 'none'}. "
                      f"{len(feasible)} feasible, {len(infeasible)} infeasible.",
            remaining_uncertainty=[
                f"Constraints may not capture all real-world factors",
                f"Trade-off scores are estimates based on execution state",
            ],
        )

        evaluation = DecisionEvaluation(
            context_id=ctx.context_id,
            tenant_id=ctx.tenant_id,
            options=options,
            objectives=objectives,
            constraints_applied=[c.name for c in (options[0].constraints if options else [])],
            recommendation=recommendation,
        )

        self._evaluations.append(evaluation)
        self._latencies.append(time.time() - start)

        return evaluation

    def build_snapshot(self, evaluation: DecisionEvaluation) -> DecisionSnapshot:
        raw = f"{evaluation.evaluation_id}:{evaluation.tenant_id}:{datetime.now(timezone.utc).isoformat()}"
        inp_fp = hashlib.sha256(raw.encode()).hexdigest()
        out_fp = hashlib.sha256(str(evaluation.to_dict()).encode()).hexdigest()
        return DecisionSnapshot(
            evaluation_id=evaluation.evaluation_id,
            input_fingerprint=inp_fp,
            output_fingerprint=out_fp,
            objective_set=[o.name for o in evaluation.objectives],
            constraint_set=evaluation.constraints_applied,
        )

    def explain(self, evaluation: DecisionEvaluation) -> DecisionExplanation:
        rec = evaluation.recommendation
        if not rec:
            return DecisionExplanation()
        return DecisionExplanation(
            recommendation_id=rec.recommendation_id,
            available_options=[o.to_dict() for o in rec.ranked_options],
            rejected_options=[o.to_dict() for o in rec.rejected_options],
            ranking_rationale=rec.rationale,
            tradeoffs=[t.to_dict() for o in rec.ranked_options[:3]
                       for t in o.tradeoffs],
            constraints=[c.to_dict() for o in evaluation.options[:3]
                         for c in o.constraints],
            evidence=[f"objective_count={len(evaluation.objectives)}",
                      f"option_count={len(evaluation.options)}"],
            predictions_used=[f"risk_level", f"delay_probability"],
            learning_artifacts=[],
            governance_considerations=[],
            remaining_uncertainty=rec.remaining_uncertainty,
        )

    def get_evaluation(self, evaluation_id: str) -> Optional[DecisionEvaluation]:
        for e in self._evaluations:
            if e.evaluation_id == evaluation_id:
                return e
        return None

    def get_history(self, tenant_id: int, limit: int = 50) -> List[DecisionEvaluation]:
        results = [e for e in self._evaluations if e.tenant_id == tenant_id]
        return results[-limit:]

    def stats(self) -> Dict[str, Any]:
        total_opts = sum(len(e.options) for e in self._evaluations)
        s = DecisionStats(
            total_evaluations=len(self._evaluations),
            total_options_generated=total_opts,
            total_recommendations=sum(1 for e in self._evaluations if e.recommendation),
            avg_options_per_evaluation=total_opts / max(len(self._evaluations), 1),
            avg_latency_seconds=sum(self._latencies) / max(len(self._latencies), 1),
        )
        return s.to_dict()

    def get_config(self) -> Dict[str, Any]:
        return self._config.to_dict()


# =========================================================================
# Facade — unified entry point
# =========================================================================

# DecisionEngine is the facade class defined above