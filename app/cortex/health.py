"""
SHUNYA Organizational Cortex — Universal Health Computation

Universal health dimensions, computed from runtime state.
Never manually assigned.
"""

from __future__ import annotations
from typing import Optional


# ─── Health dimension definitions ───

HEALTH_DIMENSIONS = [
    "execution_health",
    "decision_health",
    "knowledge_health",
    "evidence_health",
    "relationship_health",
    "operational_health",
    "learning_health",
    "trust_health",
]

HEALTH_LABELS = {
    "execution_health": "Execution Health",
    "decision_health": "Decision Health",
    "knowledge_health": "Knowledge Health",
    "evidence_health": "Evidence Health",
    "relationship_health": "Relationship Health",
    "operational_health": "Operational Health",
    "learning_health": "Learning Health",
    "trust_health": "Trust Health",
}


def compute_health(state) -> dict[str, float]:
    """Compute all health dimensions from an OrganizationState.

    Returns a dict of dimension_name -> score (0.0 to 1.0).
    Every dimension is computed, never manually assigned.
    """
    scores = {}

    # ─── Execution Health ───
    # Based on: active vs blocked commitments, execution backlog
    total = state.active_commitments + state.blocked_commitments + state.completed_commitments
    if total > 0:
        # Healthy = few blocked, many completed
        blocking_ratio = state.blocked_commitments / max(total, 1)
        completion_ratio = state.completed_commitments / max(total, 1)
        scores["execution_health"] = max(0.0, min(1.0, 0.7 - blocking_ratio * 0.5 + completion_ratio * 0.3))
    else:
        scores["execution_health"] = 0.5  # Neutral — no data

    # ─── Decision Health ───
    # Based on: waiting approvals vs active decisions, policy violations
    if state.total_decisions > 0:
        waiting_ratio = state.waiting_approval / max(state.total_decisions, 1)
        violation_penalty = state.policy_violations * 0.1
        scores["decision_health"] = max(0.0, min(1.0, 0.8 - waiting_ratio * 0.3 - violation_penalty))
    else:
        scores["decision_health"] = 0.5

    # ─── Knowledge Health ───
    # Based on: active observations vs stale observations
    if state.active_observations > 0 or state.stale_observations > 0:
        stale_ratio = state.stale_observations / max(state.active_observations + state.stale_observations, 1)
        scores["knowledge_health"] = max(0.0, min(1.0, 0.9 - stale_ratio * 0.4))
    else:
        scores["knowledge_health"] = 0.5

    # ─── Evidence Health ───
    # Based on: high vs low confidence insights
    if state.total_insights > 0:
        high_ratio = state.high_confidence_insights / max(state.total_insights, 1)
        low_penalty = state.low_confidence_insights * 0.05
        scores["evidence_health"] = max(0.0, min(1.0, high_ratio * 0.8 - low_penalty))
    else:
        scores["evidence_health"] = 0.5

    # ─── Relationship Health ───
    # Based on: resource contention, cross-functional dependencies
    contention_penalty = state.resource_contention * 0.15
    scores["relationship_health"] = max(0.0, min(1.0, 0.85 - contention_penalty))

    # ─── Operational Health ───
    # Based on: critical risks, emerging opportunities
    if state.critical_risks > 0 or state.emerging_opportunities > 0:
        risk_penalty = state.critical_risks * 0.1
        opportunity_bonus = state.emerging_opportunities * 0.05
        scores["operational_health"] = max(0.0, min(1.0, 0.75 - risk_penalty + opportunity_bonus))
    else:
        scores["operational_health"] = 0.5

    # ─── Learning Health ───
    # Based on: learning signals, high confidence learning
    if state.learning_signals > 0:
        high_conf_ratio = state.high_confidence_learning / max(state.learning_signals, 1)
        scores["learning_health"] = max(0.0, min(1.0, 0.5 + high_conf_ratio * 0.4))
    else:
        scores["learning_health"] = 0.3  # Low — no learning yet

    # ─── Trust Health ───
    # Composite of all other dimensions
    other_scores = [v for k, v in scores.items() if k != "trust_health"]
    if other_scores:
        scores["trust_health"] = sum(other_scores) / len(other_scores)
    else:
        scores["trust_health"] = 0.5

    return scores


def health_label(score: float) -> str:
    """Convert a numeric health score to a label."""
    if score >= 0.9:
        return "Excellent"
    elif score >= 0.75:
        return "Good"
    elif score >= 0.5:
        return "Fair"
    elif score >= 0.25:
        return "Poor"
    else:
        return "Critical"