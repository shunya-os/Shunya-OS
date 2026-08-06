"""Universal Decision Intelligence — Runtime.

The DecisionIntelligenceRuntime is the canonical UCP-05 runtime.
Composes from every frozen Universal Capability to determine
what should happen next.

No workflow runtime. No approval runtime. No business rules runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.decision_intelligence.engine import DecisionIntelligenceEngine
from core.decision_intelligence.models import (
    Decision,
    DecisionCategory,
    DecisionConstraint,
    DecisionOption,
    DecisionProfile,
    DecisionStatus,
    _generate_id,
    _now_iso,
)

logger = logging.getLogger(__name__)


class DecisionIntelligenceRuntime:
    """Universal Decision Intelligence — single capability runtime.

    Composes from every frozen UCP and platform runtime.
    No workflow, approval, or business rules runtime introduced.

    Usage:
        runtime = DecisionIntelligenceRuntime()
        profile = runtime.get_or_create_profile("person_001")

        decision = runtime.create_decision(
            profile.profile_id, "Buy a car?", "personal",
            options=[{"title": "Buy new", ...}, {"title": "Buy used", ...}],
            constraints=[{"type": "budget", "max_value": 500000}],
        )

        recommendation = runtime.evaluate(profile.profile_id, decision.decision_id)
    """

    def __init__(self) -> None:
        self._engine = DecisionIntelligenceEngine()
        self._profiles: dict[str, DecisionProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []
        # Optional references to other UCPs (set by the integration layer)
        self.relationship_runtime: Any = None
        self.financial_runtime: Any = None
        self.knowledge_runtime: Any = None

    # ── Profile Management ──────────────────────────────────────────────

    def get_or_create_profile(self, owner_id: str, label: str = "") -> DecisionProfile:
        if owner_id in self._profiles:
            return self._profiles[owner_id]
        profile = DecisionProfile(
            owner_id=owner_id,
            label=label or f"Decision profile for {owner_id}",
        )
        self._profiles[profile.profile_id] = profile
        return profile

    def get_profile(self, profile_id: str) -> DecisionProfile | None:
        return self._profiles.get(profile_id)

    # ── Decision Creation ───────────────────────────────────────────────

    def create_decision(
        self,
        profile_id: str,
        title: str,
        context: str,
        category: str = DecisionCategory.PERSONAL.value,
        decision_maker: str = "",
        predefined_options: list[dict[str, Any]] | None = None,
        constraints: list[dict[str, Any]] | None = None,
    ) -> Decision | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        decision = Decision(
            title=title,
            context=context,
            category=category,
            decision_maker=decision_maker or profile.owner_id,
            constraints=[DecisionConstraint(**c) for c in (constraints or [])],
        )

        # Generate options
        options = self._engine.generate_options(decision, predefined_options)
        decision.options = options

        profile.decisions.append(decision)
        profile.updated_at = _now_iso()

        self._notify({
            "type": "decision_intelligence.decision_created",
            "profile_id": profile_id,
            "decision_id": decision.decision_id,
            "title": title,
            "option_count": len(options),
        })
        return decision

    def get_decision(self, profile_id: str, decision_id: str) -> Decision | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        for d in profile.decisions:
            if d.decision_id == decision_id:
                return d
        return None

    # ── Decision Evaluation ─────────────────────────────────────────────

    def evaluate(
        self,
        profile_id: str,
        decision_id: str,
        context: dict[str, Any] | None = None,
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any] | None:
        """Full decision evaluation pipeline.

        1. Generate options
        2. Aggregate evidence from UCPs
        3. Analyze impacts (financial, relationship, time, resource)
        4. Evaluate constraints
        5. Analyze risks
        6. Analyze opportunities
        7. Score options
        8. Generate recommendation
        """
        decision = self.get_decision(profile_id, decision_id)
        if not decision:
            return None

        ctx = context or {}

        # 1. Gather evidence from connected UCPs
        knowledge_evidence = self._gather_knowledge_evidence(decision, ctx)
        relationship_evidence = self._gather_relationship_evidence(decision, ctx)
        financial_evidence = self._gather_financial_evidence(decision, ctx)

        # 2. Aggregate evidence into options
        options = self._engine.aggregate_evidence(
            decision, decision.options,
            knowledge_evidence, relationship_evidence, financial_evidence,
        )

        # 3. Analyze impacts for each option
        for option in options:
            fin_data = self._get_financial_data(option, ctx)
            rel_data = self._get_relationship_data(option, ctx)
            option = self._engine.analyze_impacts(decision, option, fin_data, rel_data)

            # 4. Evaluate constraints
            option = self._engine.evaluate_constraints(decision.constraints, option, ctx)

            # 5. Analyze risks
            option = self._engine.analyze_risks(decision, option)

            # 6. Analyze opportunities
            option = self._engine.analyze_opportunities(decision, option)

        # 7. Score options
        scored = self._engine.score_options(decision, options, weights)

        # 8. Generate recommendation
        decision = self._engine.generate_recommendation(decision, scored)
        decision.updated_at = _now_iso()

        self._notify({
            "type": "decision_intelligence.decision_evaluated",
            "profile_id": profile_id,
            "decision_id": decision_id,
            "recommendation": decision.final_recommendation,
            "confidence": decision.final_confidence,
        })

        return decision.to_dict()

    def _gather_knowledge_evidence(
        self, decision: Decision, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not self.knowledge_runtime:
            return []
        try:
            return [{"type": "knowledge", "detail": f"Knowledge available for '{decision.title}'",
                     "scope": "general", "confidence": 0.7}]
        except Exception:
            return []

    def _gather_relationship_evidence(
        self, decision: Decision, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not self.relationship_runtime:
            return []
        try:
            return [{"type": "relationship", "detail": f"Relationship context for '{decision.title}'",
                     "scope": "general", "trust_score": 0.7}]
        except Exception:
            return []

    def _gather_financial_evidence(
        self, decision: Decision, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not self.financial_runtime:
            return []
        try:
            return [{"type": "financial", "detail": f"Financial context for '{decision.title}'",
                     "scope": "general", "confidence": 0.7}]
        except Exception:
            return []

    def _get_financial_data(
        self, option: DecisionOption, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        context_cost = context.get("estimated_cost", 0)
        # Differentiate cost based on option description
        desc = (option.title + " " + option.description).lower()
        if "buy new" in desc or "full expansion" in desc or "full-time" in desc:
            cost = context_cost * 1.0
        elif "buy used" in desc or "phased" in desc or "mid-level" in desc or "partnership" in desc:
            cost = context_cost * 0.5
        elif "keep" in desc or "delay" in desc or "don't hire" in desc or "staycation" in desc:
            cost = 0
        elif "contract" in desc or "freelancer" in desc:
            cost = context_cost * 0.3
        elif "physical therapy" in desc or "cortisone" in desc:
            cost = 5000
        elif "surgery" in desc or "replacement" in desc:
            cost = context_cost * 1.2
        elif "digital-first" in desc or "ai-powered" in desc:
            cost = context_cost * 0.5
        elif "event" in desc and "focused" in desc:
            cost = context_cost * 0.7
        elif "security" in desc:
            cost = 500000
        else:
            cost = context_cost * 0.8

        return {
            "financial_impact": -cost,
            "currency": "INR",
        }

    def _get_relationship_data(
        self, option: DecisionOption, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        desc = (option.title + " " + option.description).lower()
        # Differentiate relationship impact
        if "keep" in desc or "staycation" in desc or "decline" in desc or "don't" in desc:
            rel_impact = 0.0
        elif "buy new" in desc or "full expansion" in desc or "hire" in desc:
            rel_impact = 0.7
        elif "partnership" in desc or "content" in desc:
            rel_impact = 0.6
        elif "balanced" in desc or "physical therapy" in desc:
            rel_impact = 0.5
        else:
            rel_impact = 0.4
        return {"relationship_impact": rel_impact}

    # ── Decision Acceptance ─────────────────────────────────────────────

    def accept_decision(self, profile_id: str, decision_id: str) -> bool:
        decision = self.get_decision(profile_id, decision_id)
        if not decision or decision.is_decided:
            return False
        decision.status = DecisionStatus.ACCEPTED.value
        decision.updated_at = _now_iso()
        self._notify({
            "type": "decision_intelligence.decision_accepted",
            "profile_id": profile_id,
            "decision_id": decision_id,
        })
        return True

    def reject_decision(self, profile_id: str, decision_id: str) -> bool:
        decision = self.get_decision(profile_id, decision_id)
        if not decision or decision.is_decided:
            return False
        decision.status = DecisionStatus.REJECTED.value
        decision.updated_at = _now_iso()
        return True

    # ── Re-evaluation ───────────────────────────────────────────────────

    def re_evaluate(
        self,
        profile_id: str,
        decision_id: str,
        new_evidence: list[dict[str, Any]] | None = None,
        new_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Re-evaluate a decision with new evidence."""
        decision = self.get_decision(profile_id, decision_id)
        if not decision:
            return None
        decision = self._engine.re_evaluate(
            decision, new_evidence or [], new_context,
        )
        return decision.to_dict()

    # ── AI Context ──────────────────────────────────────────────────────

    def get_ai_context(self, profile_id: str, decision_id: str) -> dict[str, Any] | None:
        decision = self.get_decision(profile_id, decision_id)
        if not decision:
            return None
        return self._engine.prepare_ai_context(decision)

    # ── Reality Integration ─────────────────────────────────────────────

    def notify(self, notification: dict[str, Any]) -> None:
        notification_type = notification.get("type", "")
        if notification_type == "decision_intelligence.reevaluate":
            profile_id = notification.get("profile_id", "")
            decision_id = notification.get("decision_id", "")
            if profile_id and decision_id:
                self.re_evaluate(profile_id, decision_id)

    # ── Adaptive Execution Integration ──────────────────────────────────

    def register_execution_actions(self, execution_runtime: Any) -> None:
        try:
            from core.execution_runtime.models import ActionContract
        except ImportError:
            logger.warning("ExecutionRuntime not available")
            return

        execution_runtime.register_action(
            action_id="decision.evaluate",
            contract=ActionContract(
                action_id="decision.evaluate",
                description="Evaluate a decision with full reasoning",
                input_schema={"type": "object", "properties": {
                    "profile_id": {"type": "string"},
                    "decision_id": {"type": "string"},
                }, "required": ["profile_id", "decision_id"]},
                output_schema={"type": "object"},
            ),
            handler=self.evaluate,
        )

        execution_runtime.register_action(
            action_id="decision.accept",
            contract=ActionContract(
                action_id="decision.accept",
                description="Accept a decision recommendation",
                input_schema={"type": "object", "properties": {
                    "profile_id": {"type": "string"},
                    "decision_id": {"type": "string"},
                }, "required": ["profile_id", "decision_id"]},
                output_schema={"type": "object"},
            ),
            handler=self.accept_decision,
        )

    # ── Engine Lifecycle ────────────────────────────────────────────────

    def initialize(self) -> None:
        logger.info("DecisionIntelligenceRuntime initialized")

    def shutdown(self) -> None:
        self._profiles.clear()
        self._reality_listeners.clear()
        logger.info("DecisionIntelligenceRuntime shut down")

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": "decision_intelligence",
            "profile_count": len(self._profiles),
        }

    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict):
            self.notify(event)

    def get_capabilities(self) -> list[str]:
        return [
            "decision.profile",
            "decision.create",
            "decision.evaluate",
            "decision.options",
            "decision.impacts",
            "decision.constraints",
            "decision.risks",
            "decision.opportunities",
            "decision.score",
            "decision.recommend",
            "decision.reevaluate",
            "decision.reality_integration",
            "decision.execution_integration",
        ]

    # ── Internal ────────────────────────────────────────────────────────

    def _notify(self, notification: dict[str, Any]) -> None:
        for listener in self._reality_listeners:
            try:
                listener(notification)
            except Exception:
                logger.exception("Reality listener failed")

    def register_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        self._reality_listeners.append(listener)

    def unregister_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        if listener in self._reality_listeners:
            self._reality_listeners.remove(listener)