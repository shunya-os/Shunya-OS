"""Universal Initiative Intelligence — Core Engine.

Pure computation: milestone reasoning, dependency analysis, risk prediction,
resource reasoning, health scoring, bottleneck detection, outcome prediction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.initiative_intelligence.models import (
    Initiative,
    InitiativeMilestone,
    InitiativeRecommendation,
    MilestoneStatus,
    RiskLevel,
    _generate_id,
    _now_iso,
)


class InitiativeIntelligenceEngine:
    """Pure computation engine for Universal Initiative Intelligence."""

    # ── Milestone Reasoning ─────────────────────────────────────────────

    def reason_about_milestones(self, initiative: Initiative) -> list[InitiativeRecommendation]:
        recs: list[InitiativeRecommendation] = []

        for m in initiative.milestones:
            if m.status == MilestoneStatus.DELAYED.value:
                recs.append(InitiativeRecommendation(
                    title=f"Milestone '{m.title}' is delayed",
                    description=m.description or f"Milestone {m.title} behind schedule",
                    priority="high", reasoning="Delayed milestone may affect dependent milestones",
                    confidence=0.8, affected_milestones=[m.milestone_id],
                    expected_impact="Downstream milestones will shift",
                    evidence=[{"type": "milestone_delayed", "milestone": m.title}]))
            elif m.status == MilestoneStatus.BLOCKED.value:
                recs.append(InitiativeRecommendation(
                    title=f"Milestone '{m.title}' is blocked",
                    description=f"Blocked milestone requires unblocking action",
                    priority="critical", reasoning="Blocked milestone halts dependent work",
                    confidence=0.9, affected_milestones=[m.milestone_id],
                    expected_impact="Critical path extended",
                    evidence=[{"type": "milestone_blocked", "milestone": m.title}]))

        del_count = len(initiative.delayed_milestones)
        if del_count >= 2:
            recs.append(InitiativeRecommendation(
                title=f"{del_count} milestones delayed — review timeline",
                description=f"Initiative has {del_count} delayed milestones",
                priority="high", reasoning="Multiple delays indicate systemic issue",
                confidence=0.75, affected_milestones=[m.milestone_id for m in initiative.delayed_milestones],
                expected_impact="Timeline may need revision",
                evidence=[{"type": "delayed_count", "value": del_count}]))

        return recs

    # ── Dependency Analysis ─────────────────────────────────────────────

    def analyze_dependencies(self, initiative: Initiative) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        milestone_map = {m.milestone_id: m for m in initiative.milestones}
        milestone_by_title = {m.title: m for m in initiative.milestones}

        for m in initiative.milestones:
            for dep_id in m.dependencies:
                dep = milestone_map.get(dep_id) or milestone_by_title.get(dep_id)
                if dep and dep.status != MilestoneStatus.COMPLETED.value:
                    issues.append({
                        "milestone": m.title,
                        "dependency": dep.title,
                        "dependency_status": dep.status,
                        "severity": "high",
                        "evidence": [{"type": "blocking_dependency", "value": dep.title}],
                    })

        return issues

    # ── Risk Prediction ─────────────────────────────────────────────────

    def predict_risks(self, initiative: Initiative) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []

        del_count = len(initiative.delayed_milestones)
        if del_count > 0:
            risks.append({"type": "timeline_risk", "level": "high" if del_count >= 3 else "medium",
                          "description": f"{del_count} milestone(s) delayed",
                          "probability": 0.4 + del_count * 0.1})

        block_count = len(initiative.blocked_milestones)
        if block_count > 0:
            risks.append({"type": "blocking_risk", "level": "critical",
                          "description": f"{block_count} milestone(s) blocked",
                          "probability": 0.8})

        if initiative.budget_utilization_pct > 80 and initiative.budget_utilization_pct < 100:
            risks.append({"type": "budget_risk", "level": "medium",
                          "description": f"{initiative.budget_utilization_pct}% budget used",
                          "probability": 0.5})
        elif initiative.budget_utilization_pct >= 100:
            risks.append({"type": "budget_risk", "level": "high",
                          "description": "Budget fully utilized",
                          "probability": 0.7})

        return risks

    # ── Initiative Health ───────────────────────────────────────────────

    def compute_health(self, initiative: Initiative) -> dict[str, Any]:
        score = 0.5

        if initiative.progress_pct > 0:
            score += 0.1
        if initiative.progress_pct > 50:
            score += 0.1

        del_pct = len(initiative.delayed_milestones) / max(len(initiative.milestones), 1)
        score -= del_pct * 0.3

        block_pct = len(initiative.blocked_milestones) / max(len(initiative.milestones), 1)
        score -= block_pct * 0.4

        if initiative.budget_utilization_pct < 100:
            score += 0.1
        if initiative.budget_utilization_pct > 100:
            score -= 0.2

        score = max(0.0, min(1.0, score))

        if score >= 0.7:
            level = "healthy"; assessment = "on_track"
        elif score >= 0.4:
            level = "fair"; assessment = "needs_attention"
        else:
            level = "at_risk"; assessment = "critical_intervention_needed"

        return {"score": round(score, 4), "level": level, "assessment": assessment,
                "progress_pct": initiative.progress_pct,
                "delayed_milestones": len(initiative.delayed_milestones),
                "blocked_milestones": len(initiative.blocked_milestones),
                "budget_utilization_pct": initiative.budget_utilization_pct}

    # ── Bottleneck Detection ────────────────────────────────────────────

    def detect_bottlenecks(self, initiative: Initiative) -> list[dict[str, Any]]:
        bottlenecks: list[dict[str, Any]] = []

        for m in initiative.milestones:
            if m.status in (MilestoneStatus.BLOCKED.value, MilestoneStatus.DELAYED.value):
                # Check dependents by milestone_id or title
                dependents = [dm for dm in initiative.milestones
                              if m.milestone_id in dm.dependencies or m.title in dm.dependencies]
                if dependents:
                    bottlenecks.append({
                        "bottleneck": m.title,
                        "status": m.status,
                        "blocking": len(dependents),
                        "blocked_milestones": [dm.title for dm in dependents],
                        "severity": "critical" if m.status == "blocked" else "high",
                    })
        return bottlenecks

    # ── Outcome Prediction ──────────────────────────────────────────────

    def predict_outcome(self, initiative: Initiative) -> dict[str, Any]:
        health = self.compute_health(initiative)
        delayed = len(initiative.delayed_milestones)

        if health["level"] == "at_risk":
            prediction = "unlikely"
            confidence = 0.4
        elif health["level"] == "fair" and delayed > 2:
            prediction = "possible_with_changes"
            confidence = 0.5
        elif health["level"] == "healthy":
            prediction = "likely"
            confidence = 0.8
        else:
            prediction = "possible"
            confidence = 0.6

        return {
            "prediction": prediction,
            "confidence": confidence,
            "health": health,
            "estimated_completion_pct": min(100, initiative.progress_pct + 20),
            "assessment": f"Outcome {prediction} with {confidence:.0%} confidence",
        }

    # ── Adaptive Replanning ─────────────────────────────────────────────

    def adaptive_replan(self, initiative: Initiative,
                         change_description: str) -> list[InitiativeRecommendation]:
        recs: list[InitiativeRecommendation] = []

        health = self.compute_health(initiative)

        if health["level"] != "healthy":
            recs.append(InitiativeRecommendation(
                title="Re-plan required — initiative health is not healthy",
                description=f"Initiative health: {health['level']}. {health['assessment']}",
                priority="high", reasoning="Health below threshold requires re-planning",
                confidence=0.7,
                expected_impact="Revised timeline and milestone plan",
                evidence=[{"type": "health_level", "value": health['level']},
                          {"type": "change_description", "value": change_description}]))

        blocked = initiative.blocked_milestones
        if blocked:
            recs.append(InitiativeRecommendation(
                title=f"Unblock {len(blocked)} milestone(s) through replanning",
                description=f"Blocked milestones: {', '.join(m.title for m in blocked)}",
                priority="critical", reasoning="Blocked milestones prevent progress",
                confidence=0.85,
                affected_milestones=[m.milestone_id for m in blocked],
                expected_impact="Progress resumes on critical path",
                evidence=[{"type": "blocked_count", "value": len(blocked)}]))

        return recs

    # ── Explainable Recommendation ──────────────────────────────────────

    def explain(self, rec: InitiativeRecommendation) -> dict[str, Any]:
        return {"recommendation": rec.title, "description": rec.description,
                "reasoning": rec.reasoning, "confidence": rec.confidence,
                "affected_milestones": rec.affected_milestones,
                "expected_impact": rec.expected_impact, "evidence": rec.evidence,
                "explanation": "Based on the following evidence:",
                "evidence_summary": [{"basis": e.get("type",""), "value": e.get("value","")} for e in rec.evidence]}

    # ── AI Context ──────────────────────────────────────────────────────

    def prepare_ai_context(self, initiative: Initiative) -> dict[str, Any]:
        return {
            "initiative": {"title": initiative.title, "type": initiative.initiative_type,
                           "status": initiative.status, "outcome": initiative.intended_outcome},
            "progress_pct": initiative.progress_pct, "milestones": len(initiative.milestones),
            "delayed": len(initiative.delayed_milestones), "blocked": len(initiative.blocked_milestones),
            "health": self.compute_health(initiative),
            "risks": self.predict_risks(initiative),
            "bottlenecks": self.detect_bottlenecks(initiative),
            "outcome": self.predict_outcome(initiative),
        }