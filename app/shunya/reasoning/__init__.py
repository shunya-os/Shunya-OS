"""Reasoning — Goal/Fact/Decision contracts, RuleReasoner, and ReasoningEngine.

Port of the half-done TypeScript architecture.
Produces decisions/recommendations from goals, facts, and context.

Reasoning does NOT execute work. It produces:
- Outcome: decision or recommendation
- Confidence: how sure it is
- Evidence: what facts support this
- Explanation: why this makes sense
"""
from typing import Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from app import db
from app.models import Entity, EntityDefinition, KnowledgeEntry, ActivityLog


# ═══════════════════════════════════════════════════════════════════════════ #
# Reasoning contracts — Goal, Fact, Decision, ReasoningRequest
# ═══════════════════════════════════════════════════════════════════════════ #


class ReasoningStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


@dataclass
class Goal:
    """A desired outcome or objective."""
    id: str
    description: str
    status: ReasoningStatus = ReasoningStatus.PENDING
    priority: int = 5  # 1-10


@dataclass
class Fact:
    """A known piece of information about the system state."""
    id: str
    statement: str
    source: str = "system"  # system, user, ai, external
    confidence: float = 1.0
    timestamp: Optional[str] = None


@dataclass
class Decision:
    """A decision made by the reasoning engine."""
    outcome: str
    confidence: float
    rationale: str
    facts_used: List[str] = field(default_factory=list)
    goals_addressed: List[str] = field(default_factory=list)


@dataclass
class ReasoningRequest:
    query: str
    goals: List[Goal] = field(default_factory=list)
    facts: List[Fact] = field(default_factory=list)
    context: dict = field(default_factory=dict)


@dataclass
class ReasoningResult:
    decision: Decision
    confidence: float
    reasoning_trace: List[str] = field(default_factory=list)
    alternative_decisions: List[Decision] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════ #
# RuleReasoner — rule-based engine evaluating facts against goals
# ═══════════════════════════════════════════════════════════════════════════ #

# In-memory trace store for debugging via /admin/api/reasoning/trace
_last_reasoning_trace: list = []


def get_last_reasoning_trace() -> list:
    """Return the last reasoning trace for the admin debug endpoint."""
    return _last_reasoning_trace


class RuleReasoner:
    """Rule-based reasoner that evaluates facts against goals."""

    _shared_traces: list = []  # class-level trace accumulator

    def __init__(self):
        self.rules: list = []
        self.facts: dict[str, Fact] = {}
        self.goals: dict[str, Goal] = {}

    def add_rule(self, name: str, condition_fn: Callable, action_fn: Callable,
                 priority: int = 5):
        self.rules.append({
            'name': name,
            'condition': condition_fn,
            'action': action_fn,
            'priority': priority,
        })
        self.rules.sort(key=lambda r: r['priority'], reverse=True)

    def add_fact(self, fact: Fact):
        self.facts[fact.id] = fact

    def add_goal(self, goal: Goal):
        self.goals[goal.id] = goal

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        """Run reasoning: evaluate rules against current facts + goals."""
        global _last_reasoning_trace
        trace = [f"Reasoning on: {request.query}"]

        # Add request facts to knowledge base
        for f in request.facts:
            self.add_fact(f)
        for g in request.goals:
            self.add_goal(g)

        # Evaluate each rule
        triggered = []
        for rule in self.rules:
            try:
                if rule['condition'](self.facts, self.goals):
                    action_result = rule['action'](
                        self.facts, self.goals, request
                    )
                    triggered.append((rule['name'], action_result))
                    trace.append(
                        f"Rule '{rule['name']}' fired \u2192 {action_result}"
                    )
            except Exception as e:
                trace.append(f"Rule '{rule['name']}' error: {e}")

        # Build decision
        best = triggered[0] if triggered else (None, "No rules triggered")
        confidence = min(
            1.0, len(triggered) / max(len(self.rules), 1)
        )

        alt_decisions = []
        for t in triggered[1:]:
            alt_decisions.append(Decision(
                outcome=str(t[1]),
                confidence=0.5,
                rationale=f"Alternative: {t[0]}",
            ))

        decision = Decision(
            outcome=str(best[1]),
            confidence=confidence,
            rationale=best[0] or "No rules matched",
            facts_used=[f.id for f in self.facts.values()],
            goals_addressed=[g.id for g in self.goals.values()],
        )

        result = ReasoningResult(
            decision=decision,
            confidence=confidence,
            reasoning_trace=trace,
            alternative_decisions=alt_decisions,
        )

        # Store for admin debug endpoint
        _last_reasoning_trace.clear()
        _last_reasoning_trace.append({
            "query": request.query,
            "decision": decision.outcome,
            "confidence": confidence,
            "rationale": decision.rationale,
            "trace": trace,
            "facts_used": decision.facts_used,
            "goals_addressed": decision.goals_addressed,
            "rule_count": len(self.rules),
            "fired_count": len(triggered),
            "alternative_count": len(alt_decisions),
        })

        return result


# ═══════════════════════════════════════════════════════════════════════════ #
# Legacy contracts — kept for backward compatibility
# ═══════════════════════════════════════════════════════════════════════════ #


@dataclass
class Recommendation:
    """A reasoned recommendation with evidence."""
    title: str
    decision: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    explanation: str = ""
    trade_offs: List[str] = field(default_factory=list)
    alternatives: List[dict] = field(default_factory=list)
    next_action: str = ""


class ReasoningEngine:
    """Produces decisions and recommendations from context."""

    @staticmethod
    def recommend_next_action(tenant_id: int, entity_id: int) -> Recommendation:
        """Recommend the next best action for a specific entity."""
        entity = db.session.get(Entity, entity_id)
        if not entity:
            return Recommendation(
                title="Entity not found", decision="", confidence=0
            )

        definition = entity.definition
        entity_type = definition.label if definition else "Record"
        status = entity.status
        statuses = definition.statuses if definition else []

        # Find current position in the status flow
        current_idx = (
            statuses.index(status) if status in statuses else -1
        )
        next_status = (
            statuses[current_idx + 1]
            if current_idx >= 0 and current_idx < len(statuses) - 1
            else None
        )

        evidence = []
        trade_offs = []

        # Check how long entity has been in current status
        days_in_status = 0
        if entity.updated_at:
            days_in_status = (datetime.utcnow() - entity.updated_at).days

        if days_in_status > 3:
            evidence.append(
                f"Has been in '{status}' for {days_in_status} days"
            )
            trade_offs.append(
                "Risk of losing momentum if not progressed"
            )

        # Check budget
        budget = entity.data.get("budget", 0)
        if budget and float(budget) > 0:
            evidence.append(f"Budget: \u20b9{float(budget):,.0f}")
            if float(budget) > 200000:
                trade_offs.append(
                    "High-value \u2014 may need senior approval"
                )

        # Check recent activity
        recent_activities = ActivityLog.query.filter_by(
            tenant_id=tenant_id, entity_id=entity_id
        ).count()

        if recent_activities == 0:
            evidence.append("No activity logged yet")
        else:
            evidence.append(f"{recent_activities} activities logged")

        # Build recommendation
        if next_status:
            decision = (
                f"Move from '{status}' to '{next_status}'"
            )
            explanation = (
                f"This {entity_type} is ready to progress "
                "to the next stage."
            )
            next_action_text = f"Update status to {next_status}"
        elif days_in_status > 5:
            decision = (
                f"Review {entity_type} \u2014 "
                f"no movement in {days_in_status} days"
            )
            explanation = (
                f"This {entity_type} needs attention "
                "to prevent it from going cold."
            )
            next_action_text = "Follow up with the customer"
        else:
            decision = "Continue monitoring"
            explanation = "No action needed at this time."
            next_action_text = ""

        return Recommendation(
            title=f"Next step for {entity.display_name}",
            decision=decision,
            confidence=0.8 if next_status else 0.5,
            evidence=evidence,
            explanation=explanation,
            trade_offs=trade_offs,
            next_action=next_action_text,
        )

    @staticmethod
    def compare_options(
        tenant_id: int, entity_type: str,
        entity_ids: List[int],
    ) -> dict:
        """Compare multiple entities with trade-offs."""
        entities = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.id.in_(entity_ids),
        ).all()

        comparison = []
        for e in entities:
            comparison.append({
                "name": e.display_name,
                "data": e.data,
                "status": e.status,
            })

        return {
            "comparison": comparison,
            "recommendation": "Compare based on your priorities",
            "trade_offs": (
                "Consider budget, timeline, and preferences"
            ),
        }


__all__ = [
    "ReasoningStatus",
    "Goal",
    "Fact",
    "Decision",
    "ReasoningRequest",
    "ReasoningResult",
    "RuleReasoner",
    "get_last_reasoning_trace",
    "Recommendation",
    "ReasoningEngine",
]