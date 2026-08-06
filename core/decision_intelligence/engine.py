"""Universal Decision Intelligence — Core Engine.

The DecisionIntelligenceEngine is the reasoning core of UCP-05.
It composes from every frozen Universal Capability to determine
what should happen next.

Pure computation — no storage, no side effects.
"""

from __future__ import annotations

from typing import Any

from core.decision_intelligence.models import (
    CertaintyLevel,
    ConstraintType,
    Decision,
    DecisionConstraint,
    DecisionOption,
    DecisionProfile,
    ImpactAssessment,
    ImpactType,
    PriorityLevel,
    _generate_id,
    _now_iso,
)


class DecisionIntelligenceEngine:
    """Pure computation engine for Universal Decision Intelligence.

    Every method is a pure function: input → output, no state.
    Composes from all frozen UCPs to generate evidence-backed decisions.
    """

    # ── Option Generation ───────────────────────────────────────────────

    def generate_options(
        self,
        decision: Decision,
        predefined_options: list[dict[str, Any]] | None = None,
    ) -> list[DecisionOption]:
        """Generate decision options from context and constraints.

        If predefined options are provided, they are used directly.
        Otherwise, options are generated from the decision context.
        """
        options: list[DecisionOption] = []

        if predefined_options:
            for opt in predefined_options:
                options.append(DecisionOption(
                    title=opt.get("title", "Option"),
                    description=opt.get("description", ""),
                    assumptions=opt.get("assumptions", []),
                    evidence=[{"type": "provided", "detail": "User-defined option"}],
                ))
        else:
            # Generate default options from decision context
            options.append(DecisionOption(
                title="Proceed",
                description=f"Move forward with {decision.title}",
                assumptions=["Current conditions remain stable"],
                evidence=[{"type": "default", "detail": "Default option — proceed"}],
            ))
            options.append(DecisionOption(
                title="Delay",
                description=f"Postpone {decision.title} until better information available",
                assumptions=["Delay will not cause significant harm"],
                evidence=[{"type": "default", "detail": "Default option — delay"}],
            ))
            options.append(DecisionOption(
                title="Decline",
                description=f"Decline or do not pursue {decision.title}",
                assumptions=["No action is better than the wrong action"],
                evidence=[{"type": "default", "detail": "Default option — decline"}],
            ))

        return options

    # ── Evidence Aggregation ────────────────────────────────────────────

    def aggregate_evidence(
        self,
        decision: Decision,
        options: list[DecisionOption],
        knowledge_evidence: list[dict[str, Any]] | None = None,
        relationship_evidence: list[dict[str, Any]] | None = None,
        financial_evidence: list[dict[str, Any]] | None = None,
    ) -> list[DecisionOption]:
        """Aggregate evidence from all UCPs into decision options.

        Evidence from Knowledge Intelligence, Relationship Intelligence,
        and Financial Intelligence is folded into each option's evaluation.
        """
        for option in options:
            all_evidence = list(option.evidence)

            if knowledge_evidence:
                for ke in knowledge_evidence:
                    if self._evidence_applies(ke, option):
                        all_evidence.append({**ke, "source": "knowledge_intelligence"})

            if relationship_evidence:
                for re in relationship_evidence:
                    if self._evidence_applies(re, option):
                        all_evidence.append({**re, "source": "relationship_intelligence"})

            if financial_evidence:
                for fe in financial_evidence:
                    if self._evidence_applies(fe, option):
                        all_evidence.append({**fe, "source": "financial_intelligence"})

            option.evidence = all_evidence

        return options

    def _evidence_applies(self, evidence: dict[str, Any], option: DecisionOption) -> bool:
        """Check if evidence applies to a given option."""
        # Simple heuristic: if evidence mentions the option title or is general
        evidence_text = str(evidence.get("detail", "")).lower()
        option_text = option.title.lower()
        if option_text in evidence_text or "general" in evidence.get("scope", "general"):
            return True
        return True  # Default: apply all evidence

    # ── Multi-Dimensional Impact Analysis ───────────────────────────────

    def analyze_impacts(
        self,
        decision: Decision,
        option: DecisionOption,
        financial_data: dict[str, Any] | None = None,
        relationship_data: dict[str, Any] | None = None,
    ) -> DecisionOption:
        """Analyze impacts across all dimensions for a single option."""
        impacts: list[ImpactAssessment] = []

        # Financial impact
        if financial_data:
            fin_impact = financial_data.get("financial_impact", 0)
            impacts.append(ImpactAssessment(
                impact_type=ImpactType.FINANCIAL.value,
                description=f"Financial impact: {fin_impact:+.0f}",
                magnitude=min(1.0, abs(fin_impact) / 100000),
                direction="positive" if fin_impact >= 0 else "negative",
                certainty=CertaintyLevel.LIKELY.value,
                value={"amount": fin_impact, "currency": financial_data.get("currency", "INR")},
                evidence=[{"type": "financial_analysis", "value": fin_impact}],
            ))

        # Relationship impact
        if relationship_data:
            rel_impact = relationship_data.get("relationship_impact", 0.0)
            direction = "positive" if rel_impact >= 0.5 else "neutral" if rel_impact >= 0 else "negative"
            impacts.append(ImpactAssessment(
                impact_type=ImpactType.RELATIONSHIP.value,
                description=f"Relationship impact: {rel_impact:.2f} trust score change",
                magnitude=abs(rel_impact),
                direction=direction,
                certainty=CertaintyLevel.POSSIBLE.value,
                evidence=[{"type": "relationship_analysis", "value": rel_impact}],
            ))

        # Time impact (estimated from context)
        time_impact = self._estimate_time_impact(decision, option)
        impacts.append(ImpactAssessment(
            impact_type=ImpactType.TIME.value,
            description=time_impact["description"],
            magnitude=time_impact["magnitude"],
            direction=time_impact["direction"],
            certainty=CertaintyLevel.LIKELY.value,
            evidence=[{"type": "time_analysis", "value": time_impact}],
        ))

        # Resource impact
        resource_impact = self._estimate_resource_impact(decision, option)
        impacts.append(ImpactAssessment(
            impact_type=ImpactType.RESOURCE.value,
            description=resource_impact["description"],
            magnitude=resource_impact["magnitude"],
            direction=resource_impact["direction"],
            certainty=CertaintyLevel.POSSIBLE.value,
            evidence=[{"type": "resource_analysis", "value": resource_impact}],
        ))

        option.impacts = impacts
        return option

    def _estimate_time_impact(self, decision: Decision, option: DecisionOption) -> dict[str, Any]:
        """Estimate time impact of a decision option."""
        if "delay" in option.title.lower() or "defer" in option.title.lower():
            return {"description": "Delays decision by weeks-months", "magnitude": 0.6, "direction": "negative"}
        if "decline" in option.title.lower() or "reject" in option.title.lower():
            return {"description": "No time investment required", "magnitude": 0.0, "direction": "neutral"}
        return {"description": "Requires moderate time investment", "magnitude": 0.3, "direction": "negative"}

    def _estimate_resource_impact(self, decision: Decision, option: DecisionOption) -> dict[str, Any]:
        """Estimate resource impact of a decision option."""
        if "delay" in option.title.lower() or "decline" in option.title.lower():
            return {"description": "Minimal resource consumption", "magnitude": 0.1, "direction": "positive"}
        return {"description": "Requires resource allocation", "magnitude": 0.3, "direction": "negative"}

    # ── Constraint Satisfaction ─────────────────────────────────────────

    def evaluate_constraints(
        self,
        constraints: list[DecisionConstraint],
        option: DecisionOption,
        context: dict[str, Any] | None = None,
    ) -> DecisionOption:
        """Evaluate which constraints an option satisfies or violates."""
        satisfied: list[str] = []
        violated: list[str] = []
        ctx = context or {}

        for constraint in constraints:
            if constraint.constraint_type == ConstraintType.BUDGET.value:
                cost = ctx.get("estimated_cost", 0)
                if constraint.max_value > 0 and cost <= constraint.max_value:
                    satisfied.append(constraint.constraint_id)
                    satisfied.append(f"Budget: within {constraint.max_value}")
                elif constraint.max_value > 0 and cost > constraint.max_value:
                    violated.append(constraint.constraint_id)
                    violated.append(f"Budget: exceeds {constraint.max_value} by {cost - constraint.max_value}")
                else:
                    satisfied.append(constraint.constraint_id)

            elif constraint.constraint_type == ConstraintType.TIME.value:
                duration = ctx.get("estimated_duration_days", 0)
                if constraint.max_value > 0 and duration <= constraint.max_value:
                    satisfied.append(constraint.constraint_id)
                elif constraint.max_value > 0 and duration > constraint.max_value:
                    violated.append(constraint.constraint_id)
                else:
                    satisfied.append(constraint.constraint_id)

            elif constraint.constraint_type == ConstraintType.RESOURCE.value:
                utilization = ctx.get("resource_utilization", 0)
                if constraint.max_value > 0 and utilization <= constraint.max_value:
                    satisfied.append(constraint.constraint_id)
                elif constraint.max_value > 0 and utilization > constraint.max_value:
                    violated.append(constraint.constraint_id)
                else:
                    satisfied.append(constraint.constraint_id)

            else:
                satisfied.append(constraint.constraint_id)

        option.constraints_satisfied = list(set(satisfied))
        option.constraints_violated = list(set(violated))
        return option

    # ── Risk Analysis ───────────────────────────────────────────────────

    def analyze_risks(
        self,
        decision: Decision,
        option: DecisionOption,
    ) -> DecisionOption:
        """Analyze risks associated with a decision option."""
        risks: list[dict[str, Any]] = []

        # Financial risk
        fin_impact = next((i for i in option.impacts if i.impact_type == ImpactType.FINANCIAL.value), None)
        if fin_impact and fin_impact.direction == "negative":
            risks.append({
                "type": "financial_loss",
                "description": f"Potential financial loss of {fin_impact.value.get('amount', 0)}",
                "severity": "high" if fin_impact.magnitude > 0.6 else "medium",
                "probability": "possible",
            })

        # Constraint violation risk
        if option.constraints_violated:
            risks.append({
                "type": "constraint_violation",
                "description": f"Violates: {', '.join(option.constraints_violated[:3])}",
                "severity": "high",
                "probability": "certain",
            })

        # General risk for "proceed" options
        if "proceed" in option.title.lower() or "proceed" in option.description.lower():
            risks.append({
                "type": "execution_risk",
                "description": "Unknown outcomes from proceeding",
                "severity": "medium",
                "probability": "possible",
            })

        # Delay risk
        if "delay" in option.title.lower():
            risks.append({
                "type": "opportunity_cost",
                "description": "Opportunity lost during delay",
                "severity": "medium",
                "probability": "likely",
            })

        option.risks = risks
        return option

    # ── Opportunity Analysis ────────────────────────────────────────────

    def analyze_opportunities(
        self,
        decision: Decision,
        option: DecisionOption,
    ) -> DecisionOption:
        """Analyze opportunities associated with a decision option."""
        opportunities: list[dict[str, Any]] = []

        fin_impact = next((i for i in option.impacts if i.impact_type == ImpactType.FINANCIAL.value), None)
        if fin_impact and fin_impact.direction == "positive" and fin_impact.magnitude > 0.3:
            opportunities.append({
                "type": "financial_gain",
                "description": f"Potential gain of {fin_impact.value.get('amount', 0)}",
                "magnitude": fin_impact.magnitude,
            })

        rel_impact = next((i for i in option.impacts if i.impact_type == ImpactType.RELATIONSHIP.value), None)
        if rel_impact and rel_impact.direction == "positive":
            opportunities.append({
                "type": "relationship_strengthening",
                "description": "Strengthens relationships",
                "magnitude": rel_impact.magnitude,
            })

        if "delay" not in option.title.lower() and "decline" not in option.title.lower():
            opportunities.append({
                "type": "progression",
                "description": f"Moves forward on '{decision.title}'",
                "magnitude": 0.5,
            })

        option.metadata["opportunities"] = opportunities
        return option

    # ── Priority Scoring ────────────────────────────────────────────────

    def score_options(
        self,
        decision: Decision,
        options: list[DecisionOption],
        weights: dict[str, float] | None = None,
    ) -> list[DecisionOption]:
        """Score each option across all dimensions.

        Default weights: financial=0.30, relationship=0.20, time=0.15,
        resource=0.10, risk=0.15, opportunity=0.10
        """
        w = weights or {
            ImpactType.FINANCIAL.value: 0.30,
            ImpactType.RELATIONSHIP.value: 0.20,
            ImpactType.TIME.value: 0.15,
            ImpactType.RESOURCE.value: 0.10,
            "risk": 0.15,  # negative weight — lower risk = higher score
            "opportunity": 0.10,
            "constraints": 0.10,  # bonus for satisfying constraints
        }

        for option in options:
            score = 0.0
            confidence = 0.0

            # Impact scores
            for impact in option.impacts:
                weight = w.get(impact.impact_type, 0.1)
                direction = 1.0 if impact.direction == "positive" else -1.0 if impact.direction == "negative" else 0.0
                score += direction * impact.magnitude * weight
                confidence += 0.15 * (1.0 - abs(impact.magnitude - 0.5) * 2) * weight

            # Risk penalty
            risk_weight = w.get("risk", 0.15)
            for risk in option.risks:
                severity_penalty = {"low": 0.1, "medium": 0.3, "high": 0.5}.get(risk.get("severity", "medium"), 0.3)
                score -= risk_weight * severity_penalty

            # Opportunity bonus
            opp_weight = w.get("opportunity", 0.10)
            opportunities = option.metadata.get("opportunities", [])
            for opp in opportunities:
                score += opp_weight * opp.get("magnitude", 0.3)

            # Constraint bonus
            constraint_weight = w.get("constraints", 0.10)
            if option.constraints_satisfied and not option.constraints_violated:
                score += constraint_weight * 0.5
            elif option.constraints_violated:
                score -= constraint_weight * 0.5

            # Normalize to 0-1
            score = max(0.0, min(1.0, (score + 1.0) / 2.0))
            confidence = max(0.0, min(1.0, confidence + 0.3))

            option.overall_score = round(score, 4)
            option.confidence = round(confidence, 4)

            # Priority
            if score >= 0.75:
                option.priority = PriorityLevel.HIGH.value
            elif score >= 0.55:
                option.priority = PriorityLevel.MEDIUM.value
            elif score >= 0.35:
                option.priority = PriorityLevel.LOW.value
            else:
                option.priority = PriorityLevel.NEGLIGIBLE.value

        return sorted(options, key=lambda o: o.overall_score, reverse=True)

    # ── Uncertainty Reasoning ───────────────────────────────────────────

    def reason_about_uncertainty(
        self,
        options: list[DecisionOption],
    ) -> list[dict[str, Any]]:
        """Analyze uncertainty across all options."""
        uncertainties: list[dict[str, Any]] = []

        for option in options:
            if option.confidence < 0.5:
                uncertainties.append({
                    "option_id": option.option_id,
                    "title": option.title,
                    "confidence": option.confidence,
                    "uncertainty_factors": [
                        "Limited evidence",
                        "Multiple unknown impacts",
                    ],
                    "recommendation": "Gather more information before deciding",
                })

        return uncertainties

    # ── Final Recommendation ────────────────────────────────────────────

    def generate_recommendation(
        self,
        decision: Decision,
        options: list[DecisionOption],
        reasoning_notes: str = "",
    ) -> Decision:
        """Generate the final decision recommendation with full reasoning.

        Every recommendation exposes:
        - reasoning
        - evidence
        - confidence
        - assumptions
        - alternatives
        - expected outcome
        """
        if not options:
            decision.final_recommendation = "Insufficient options to recommend"
            decision.final_confidence = 0.0
            decision.reasoning = "No options were generated for evaluation"
            return decision

        best = options[0]

        # Build reasoning
        reasoning_parts = [f"Recommended: {best.title}"]
        reasoning_parts.append(f"Overall score: {best.overall_score:.2f} (confidence: {best.confidence:.2f})")

        for impact in best.impacts:
            reasoning_parts.append(
                f"- {impact.impact_type}: {impact.direction} ({impact.magnitude:.2f}) — {impact.description}"
            )

        if best.constraints_violated:
            reasoning_parts.append(f"- Constraint violations: {', '.join(best.constraints_violated)}")

        if best.risks:
            reasoning_parts.append(f"- Risks: {', '.join(r['description'] for r in best.risks[:3])}")

        opportunities = best.metadata.get("opportunities", [])
        if opportunities:
            reasoning_parts.append(f"- Opportunities: {', '.join(o['description'] for o in opportunities[:3])}")

        # Build expected outcome
        expected_outcome = f"Choosing '{best.title}' is expected to:"
        for impact in best.impacts:
            expected_outcome += f"\n- {impact.impact_type}: {impact.description}"

        decision.options = options
        decision.selected_option_id = best.option_id
        decision.final_recommendation = f"Choose '{best.title}' (score: {best.overall_score:.2f})"
        decision.final_confidence = best.confidence
        decision.reasoning = "\n".join(reasoning_parts)
        decision.assumptions = best.assumptions
        decision.expected_outcome = expected_outcome
        decision.status = "recommended"

        return decision

    # ── Continuous Re-evaluation ────────────────────────────────────────

    def re_evaluate(
        self,
        decision: Decision,
        new_evidence: list[dict[str, Any]],
        new_context: dict[str, Any] | None = None,
    ) -> Decision:
        """Re-evaluate a decision with new evidence.

        This enables continuous re-evaluation as situations change.
        """
        if not decision.is_decided:
            # Add new evidence to all options
            for option in decision.options:
                option.evidence.extend(new_evidence)

            # Re-score with new context
            ctx = new_context or {}
            for option in decision.options:
                option = self.evaluate_constraints(decision.constraints, option, ctx)
                option = self.analyze_risks(decision, option)
                option = self.analyze_opportunities(decision, option)

            decision = self.generate_recommendation(decision, decision.options)

        decision.updated_at = _now_iso()
        return decision

    # ── AI Context ──────────────────────────────────────────────────────

    def prepare_ai_context(self, decision: Decision) -> dict[str, Any]:
        """Prepare structured context for AI understanding."""
        return {
            "decision": {
                "title": decision.title,
                "context": decision.context,
                "category": decision.category,
                "status": decision.status,
            },
            "options": [
                {
                    "title": o.title,
                    "score": o.overall_score,
                    "confidence": o.confidence,
                    "priority": o.priority,
                    "impacts": {i.impact_type: {"direction": i.direction, "magnitude": i.magnitude}
                                for i in o.impacts},
                    "constraint_status": {
                        "satisfied": len(o.constraints_satisfied),
                        "violated": len(o.constraints_violated),
                    },
                    "risks": len(o.risks),
                }
                for o in decision.ranked_options
            ],
            "recommendation": decision.final_recommendation,
            "confidence": decision.final_confidence,
            "reasoning": decision.reasoning,
            "assumptions": decision.assumptions,
            "expected_outcome": decision.expected_outcome,
        }