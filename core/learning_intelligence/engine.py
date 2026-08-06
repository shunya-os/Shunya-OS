"""Universal Learning Intelligence — Core Engine.

Pure computation: skill gap analysis, proficiency tracking, growth measurement,
path recommendation, practice effectiveness, learning health assessment,
disruption handling, AI-guided learning orchestration.

No LMS Logic. No Education Logic.

Composes from: Journey, Relationship, Financial, Knowledge, Decision, Agreement,
Asset, and Initiative UCPs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.learning_intelligence.models import (
    AssessmentType,
    Competency,
    CompetencyLevel,
    Certification,
    CoachingEngagement,
    ExperienceRecord,
    InteractionMode,
    KnowledgeGrowthEntry,
    LearningGoal,
    LearningGoalStatus,
    LearningPath,
    LearningPathStatus,
    LearningRecommendation,
    LearningSession,
    LearningStyle,
    MentoringRelationship,
    OrganizationalLearning,
    PracticeSession,
    Skill,
    SkillProficiency,
    _generate_id,
    _now_iso,
)


class LearningIntelligenceEngine:
    """Pure computation engine for Universal Learning Intelligence."""

    # ── Skill Gap Analysis ────────────────────────────────────────────────

    def analyze_skill_gaps(self, learner: Any,
                           target_skills: list[dict[str, Any]]) -> list[LearningRecommendation]:
        """Analyze gaps between current and target skill levels."""
        recs: list[LearningRecommendation] = []
        skill_map = {s.name: s for s in learner.skills}

        for ts in target_skills:
            name = ts.get("name", "")
            target_prof = ts.get("proficiency_score", 0.7)
            target_prof_label = ts.get("proficiency", SkillProficiency.COMPETENT.value)

            current = skill_map.get(name)
            current_score = current.proficiency_score if current else 0.0

            if current_score < target_prof:
                gap = target_prof - current_score
                recs.append(LearningRecommendation(
                    title=f"Skill gap: {name}",
                    description=f"Current proficiency {current_score:.2f}, target {target_prof:.2f}",
                    priority="high" if gap > 0.4 else "medium",
                    reasoning=f"Learner is below target proficiency for {name}",
                    confidence=0.8,
                    assumptions=[f"Target proficiency of {target_prof} is appropriate", "Skill assessment is accurate"],
                    alternatives=[f"Consider alternative learning approaches for {name}", "Explore adjacent skills"],
                    expected_impact=f"Closing this gap will enable {ts.get('context', 'target outcomes')}",
                    affected_skills=[name],
                    evidence=[{"type": "current_proficiency", "value": current_score},
                              {"type": "target_proficiency", "value": target_prof},
                              {"type": "gap", "value": gap}]))

        return recs

    # ── Proficiency Tracking ─────────────────────────────────────────────

    def track_proficiency_growth(self, skill: Skill,
                                 practice_sessions: list[PracticeSession]) -> dict[str, Any]:
        """Track proficiency growth over time for a skill."""
        if not practice_sessions:
            return {"skill": skill.name, "current": skill.proficiency_score,
                    "growth_pct": 0, "trend": "stable", "sessions": 0}

        recent = sorted(practice_sessions, key=lambda s: s.created_at, reverse=True)
        scores = [s.effective_score for s in recent]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Simple trend: compare recent half vs earlier half
        mid = len(recent) // 2
        recent_avg = sum(scores[:mid]) / max(mid, 1)
        early_avg = sum(scores[mid:]) / max(len(scores) - mid, 1)

        if recent_avg > early_avg * 1.1:
            trend = "improving"
        elif recent_avg < early_avg * 0.9:
            trend = "declining"
        else:
            trend = "stable"

        growth_pct = ((avg_score - skill.proficiency_score) / max(skill.proficiency_score, 0.01)) * 100

        return {"skill": skill.name, "current": skill.proficiency_score,
                "average_practice_score": round(avg_score, 4),
                "growth_pct": round(growth_pct, 1), "trend": trend,
                "sessions": len(practice_sessions),
                "total_hours": sum(s.duration_minutes for s in practice_sessions) / 60}

    # ── Growth Measurement ───────────────────────────────────────────────

    def measure_knowledge_growth(self, entries: list[KnowledgeGrowthEntry]) -> dict[str, Any]:
        """Measure overall knowledge growth from growth entries."""
        if not entries:
            return {"total_entries": 0, "avg_growth_pct": 0, "domains": [], "trend": "stable"}

        domains: dict[str, list[float]] = {}
        for e in entries:
            domains.setdefault(e.domain, []).append(e.growth_pct)

        domain_avgs = {d: round(sum(v) / len(v), 1) for d, v in domains.items()}

        all_growth = [e.growth_pct for e in entries]
        avg_growth = sum(all_growth) / len(all_growth)

        # Trend based on recent vs older entries
        recent = entries[-5:]
        older = entries[:-5] or entries
        recent_avg = sum(e.growth_pct for e in recent) / len(recent)
        older_avg = sum(e.growth_pct for e in older) / len(older)

        trend = "accelerating" if recent_avg > older_avg * 1.1 else (
            "decelerating" if recent_avg < older_avg * 0.9 else "stable")

        return {"total_entries": len(entries), "avg_growth_pct": round(avg_growth, 1),
                "domains": domain_avgs, "trend": trend}

    # ── Path Recommendation ──────────────────────────────────────────────

    def recommend_learning_path(self, learner: Any,
                                target_skill: str,
                                available_hours: float = 0.0) -> LearningRecommendation:
        """Recommend a learning path for a target skill."""
        skill_map = {s.name: s for s in learner.skills}
        current = skill_map.get(target_skill)

        if not current:
            return LearningRecommendation(
                title=f"New skill: {target_skill}",
                description=f"Start learning {target_skill} from scratch",
                priority="medium",
                reasoning="Learner has no prior experience with this skill",
                confidence=0.7,
                assumptions=["Skill is relevant to learner's goals", "Foundational resources exist"],
                alternatives=["Consider prerequisite skills first", "Explore adjacent domains"],
                expected_impact=f"Gaining {target_skill} opens new capabilities",
                affected_skills=[target_skill],
                evidence=[{"type": "no_prior_experience", "value": target_skill}])

        gap = 1.0 - current.proficiency_score
        if gap < 0.1:
            return LearningRecommendation(
                title=f"Skill mastery: {target_skill}",
                description=f"Near mastery for {target_skill} — focus on teaching others",
                priority="low",
                reasoning="Learner has high proficiency, minimal structured study needed",
                confidence=0.9,
                assumptions=["Teaching reinforces mastery", "Learner can mentor others"],
                alternatives=["Pursue certification", "Contribute to open source"],
                expected_impact="Deepening expertise through peer teaching",
                affected_skills=[target_skill],
                evidence=[{"type": "near_mastery", "value": current.proficiency_score}])

        estimated_hours = gap * 40  # rough estimate
        pace = "intensive" if available_hours and available_hours >= 10 else "sustainable"

        return LearningRecommendation(
            title=f"Continue developing: {target_skill}",
            description=f"Estimated {estimated_hours:.0f}h to reach proficiency from {current.proficiency_score:.2f}",
            priority="medium",
            reasoning=f"Current level {current.proficiency_score:.2f}, target 1.0, gap {gap:.2f}",
            confidence=0.75,
            assumptions=[f"Learner can dedicate {estimated_hours:.0f}h", "Quality learning resources available"],
            alternatives=["Alternative learning modalities", "Project-based vs structured approach"],
            expected_impact=f"Reaching target proficiency unlocks {target_skill} applications",
            affected_skills=[target_skill],
            evidence=[{"type": "current_score", "value": current.proficiency_score},
                      {"type": "estimated_hours", "value": estimated_hours},
                      {"type": "available_hours_per_week", "value": available_hours}])

    # ── Practice Effectiveness ────────────────────────────────────────────

    def evaluate_practice_effectiveness(self,
                                        sessions: list[PracticeSession]) -> dict[str, Any]:
        """Evaluate the effectiveness of practice sessions."""
        if not sessions:
            return {"effectiveness_score": 0, "total_sessions": 0, "recommendation": "Start practicing"}

        scores = [s.effective_score for s in sessions]
        avg_score = sum(scores) / len(scores)
        total_hours = sum(s.duration_minutes for s in sessions) / 60

        # Score distribution
        high_performers = sum(1 for s in sessions if s.effective_score >= 0.8)
        low_performers = sum(1 for s in sessions if s.effective_score < 0.4)

        effectiveness = round(avg_score, 2)

        if effectiveness >= 0.7:
            rec = "effective_training"
            assessment = "Practice is effective, maintain current approach"
        elif effectiveness >= 0.4:
            rec = "needs_refinement"
            assessment = "Practice could be more effective — try structured deliberate practice"
        else:
            rec = "restructure_practice"
            assessment = "Practice approach needs restructuring — focus on fundamentals"

        return {"effectiveness_score": effectiveness,
                "total_sessions": len(sessions),
                "total_hours": round(total_hours, 1),
                "high_performance_sessions": high_performers,
                "low_performance_sessions": low_performers,
                "recommendation": rec,
                "assessment": assessment}

    # ── Learning Health Assessment ────────────────────────────────────────

    def assess_learning_health(self, learner: Any) -> dict[str, Any]:
        """Compute overall learning health for a learner."""
        score = 0.5

        # Skills diversity
        if len(learner.skills) >= 3:
            score += 0.1
        if len(learner.skills) >= 7:
            score += 0.05

        # Active learning paths
        active = learner.active_paths
        if active:
            score += 0.1
            # Check progress
            avg_progress = sum(p.progress_pct for p in active) / len(active)
            if avg_progress > 50:
                score += 0.05
            if avg_progress > 0:
                score += 0.05

        # Practice consistency
        recent_practice = [p for p in learner.practice_sessions
                           if (datetime.now(timezone.utc) -
                               datetime.fromisoformat(p.created_at.replace("Z", "+00:00"))).days <= 30]
        if len(recent_practice) >= 4:
            score += 0.1
        elif len(recent_practice) >= 1:
            score += 0.05

        # Knowledge growth
        recent_growth = [g for g in learner.knowledge_growth
                         if (datetime.now(timezone.utc) -
                             datetime.fromisoformat(g.created_at.replace("Z", "+00:00"))).days <= 90]
        if recent_growth:
            score += 0.05

        # Certifications
        if learner.completed_certifications:
            score += 0.05

        # Coaching / mentoring
        if learner.coaching_engagements or learner.mentoring_relationships:
            score += 0.05

        # Overdue goals penalty
        for p in learner.learning_paths:
            if p.overdue_goals:
                score -= 0.1 * len(p.overdue_goals)

        score = max(0.0, min(1.0, score))

        if score >= 0.7:
            level = "thriving"
            assessment = "Learning is on track — consistent growth observed"
        elif score >= 0.4:
            level = "developing"
            assessment = "Learning is progressing — more consistency would help"
        else:
            level = "at_risk"
            assessment = "Learning needs attention — establish regular practice"

        return {"score": round(score, 4), "level": level, "assessment": assessment,
                "total_skills": len(learner.skills),
                "active_paths": len(active),
                "avg_progress_pct": round(sum(p.progress_pct for p in active) / max(len(active), 1), 1),
                "recent_practice_sessions": len(recent_practice),
                "recent_growth_entries": len(recent_growth),
                "certifications": len(learner.completed_certifications)}

    # ── Disruption Handling ───────────────────────────────────────────────

    def handle_learning_disruption(self, learner: Any,
                                   path: LearningPath,
                                   disruption: str) -> list[LearningRecommendation]:
        """Handle a disruption to a learning path with adaptive recommendations."""
        recs: list[LearningRecommendation] = []

        # Assess impact of disruption
        overdue = path.overdue_goals
        if overdue:
            recs.append(LearningRecommendation(
                title=f"{len(overdue)} learning goal(s) overdue",
                description=f"Goals affected by disruption: {', '.join(g.title for g in overdue)}",
                priority="high",
                reasoning=f"Disruption has caused {len(overdue)} goals to fall behind schedule",
                confidence=0.85,
                assumptions=["Learner can reprioritize", "Additional time is available"],
                alternatives=["Extend deadline for each goal", "Reduce scope of learning path"],
                expected_impact="Addressing overdue goals restores learning momentum",
                affected_goals=[g.goal_id for g in overdue],
                evidence=[{"type": "disruption", "value": disruption},
                          {"type": "overdue_goals", "value": [g.title for g in overdue]}]))

        # Check proficiency regression
        skill_map = {s.name: s for s in learner.skills}
        regressed = [s for s in learner.skills if s.proficiency_score < 0.3]
        if regressed:
            recs.append(LearningRecommendation(
                title=f"{len(regressed)} skill(s) need reinforcement",
                description=f"Low-proficiency skills: {', '.join(s.name for s in regressed)}",
                priority="medium",
                reasoning="Prolonged disruption may cause skill decay",
                confidence=0.7,
                assumptions=["Reinforcement activities exist", "Learner can resume soon"],
                alternatives=["Focus on one skill at a time", "Use spaced repetition"],
                expected_impact="Reinforcing fundamentals prevents skill loss",
                affected_skills=[s.name for s in regressed],
                evidence=[{"type": "regressed_skills", "value": [s.name for s in regressed]}]))

        # Path adjustment recommendation
        recs.append(LearningRecommendation(
            title="Adapt learning path to disruption",
            description=f"Adjust path schedule and scope due to: {disruption}",
            priority="high",
            reasoning="Learning paths must adapt to changing circumstances",
            confidence=0.75,
            assumptions=["Flexible timeline is available", "Core objectives remain unchanged"],
            alternatives=["Switch to a different learning mode (e.g., AI-guided)",
                         "Reduce path to core essentials only"],
            expected_impact="Adapted path maintains progress despite disruption",
            affected_goals=[g.goal_id for g in path.goals],
            evidence=[{"type": "disruption", "value": disruption},
                      {"type": "path_progress", "value": path.progress_pct}]))

        return recs

    # ── AI-Guided Learning ────────────────────────────────────────────────

    def orchestrate_ai_guided_learning(self, learner: Any,
                                       target_skill: str) -> dict[str, Any]:
        """Prepare AI-guided learning context for a skill."""
        skill_map = {s.name: s for s in learner.skills}
        skill = skill_map.get(target_skill)
        proficiency = skill.proficiency_score if skill else 0.0

        # Determine learning stage
        if proficiency < 0.2:
            stage = "foundation"
            focus = "core_concepts"
            suggested_modes = [InteractionMode.AI_GUIDED.value,
                               InteractionMode.READING.value,
                               InteractionMode.SIMULATION.value]
        elif proficiency < 0.5:
            stage = "building"
            focus = "guided_practice"
            suggested_modes = [InteractionMode.AI_GUIDED.value,
                               InteractionMode.HANDS_ON.value,
                               InteractionMode.PROJECT.value]
        elif proficiency < 0.8:
            stage = "refining"
            focus = "challenging_applications"
            suggested_modes = [InteractionMode.PROJECT.value,
                               InteractionMode.PEER_REVIEW.value,
                               InteractionMode.AI_GUIDED.value]
        else:
            stage = "mastering"
            focus = "teaching_and_mentoring"
            suggested_modes = [InteractionMode.PEER_REVIEW.value,
                               InteractionMode.WORKSHOP.value,
                               InteractionMode.AI_GUIDED.value]

        return {"target_skill": target_skill,
                "current_proficiency": round(proficiency, 2),
                "learning_stage": stage,
                "focus": focus,
                "suggested_modes": suggested_modes,
                "prior_knowledge": [s.name for s in learner.skills
                                    if s.proficiency_score >= 0.5],
                "learner_style": learner.preferred_style,
                "evidence": [{"type": "proficiency_assessment", "value": proficiency},
                             {"type": "learning_stage", "value": stage}]}

    # ── Recommend Next Action ─────────────────────────────────────────────

    def recommend_next_action(self, learner: Any) -> LearningRecommendation:
        """Recommend the single best next learning action."""
        health = self.assess_learning_health(learner)

        if health["level"] == "at_risk":
            return LearningRecommendation(
                title="Start a new learning path or resume practice",
                description=f"Learning health is '{health['level']}' — {health['assessment']}",
                priority="high",
                reasoning="Learning has stalled. A structured path will rebuild momentum.",
                confidence=0.8,
                assumptions=["Learner has 30 minutes available daily", "A clear goal will motivate"],
                alternatives=["Set a smaller micro-goal first", "Find a study partner or mentor"],
                expected_impact="A learning path restores structure and measurable progress",
                evidence=[{"type": "health_level", "value": health["level"]},
                          {"type": "health_score", "value": health["score"]}])

        # Find lowest-proficiency skill
        if learner.skills:
            weakest = min(learner.skills, key=lambda s: s.proficiency_score)
            return LearningRecommendation(
                title=f"Practice: {weakest.name}",
                description=f"Current proficiency: {weakest.proficiency_score:.2f} — targeted practice will help",
                priority="medium",
                reasoning=f"'{weakest.name}' has the lowest proficiency among {len(learner.skills)} skills",
                confidence=0.7,
                assumptions=["Practice materials are available", "Learner can dedicate time"],
                alternatives=["Try a different approach (project-based, AI-guided)",
                             "Ask a mentor for guidance"],
                expected_impact=f"Improving {weakest.name} increases overall capability",
                affected_skills=[weakest.name],
                evidence=[{"type": "weakest_skill", "value": weakest.name},
                          {"type": "proficiency_score", "value": weakest.proficiency_score}])

        return LearningRecommendation(
            title="Start learning something new",
            description="No skills recorded yet. Pick a skill that excites you.",
            priority="medium",
            reasoning="Learner has no tracked skills. Starting is the first step.",
            confidence=0.9,
            assumptions=["Learner has identified a skill of interest"],
            alternatives=["Explore different domains", "Take a learning style assessment"],
            expected_impact="Building skills creates a foundation for growth",
            evidence=[{"type": "no_skills", "value": True}])

    # ── Explainable Recommendation ────────────────────────────────────────

    def explain(self, rec: LearningRecommendation) -> dict[str, Any]:
        """Generate an explanation for a recommendation."""
        return {
            "recommendation": rec.title,
            "description": rec.description,
            "reasoning": rec.reasoning,
            "confidence": rec.confidence,
            "assumptions": list(rec.assumptions),
            "alternatives": list(rec.alternatives),
            "expected_impact": rec.expected_impact,
            "affected_skills": rec.affected_skills,
            "affected_goals": rec.affected_goals,
            "evidence": list(rec.evidence),
            "evidence_summary": [{"basis": e.get("type", ""), "value": e.get("value", "")}
                                 for e in rec.evidence],
        }

    # ── AI Context ────────────────────────────────────────────────────────

    def prepare_ai_context(self, learner: Any) -> dict[str, Any]:
        """Prepare full AI context for a learner."""
        return {
            "learner": {"profile_id": learner.profile_id, "label": learner.label,
                        "style": learner.preferred_style},
            "health": self.assess_learning_health(learner),
            "skills": [{"name": s.name, "proficiency": s.proficiency,
                        "score": s.proficiency_score, "hours": s.hours_practiced}
                       for s in learner.skills],
            "active_paths": [{"title": p.title, "progress": p.progress_pct,
                              "overdue": len(p.overdue_goals),
                              "goals": len(p.goals)} for p in learner.active_paths],
            "certifications": len(learner.completed_certifications),
            "recent_practice": len([p for p in learner.practice_sessions
                                    if (datetime.now(timezone.utc) -
                                        datetime.fromisoformat(
                                            p.created_at.replace("Z", "+00:00"))).days <= 30]),
            "recommendation": self.recommend_next_action(learner).to_dict(),
        }