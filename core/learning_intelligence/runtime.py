"""Universal Learning Intelligence — Runtime.

LearningIntelligenceRuntime composes from all frozen UCPs.
No Learning Runtime. No LMS Runtime. No Education Runtime.

Composes from: Journey, Relationship, Financial, Knowledge, Decision, Agreement,
Asset, and Initiative UCPs.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.learning_intelligence.engine import LearningIntelligenceEngine
from core.learning_intelligence.models import (
    AssessmentType,
    Certification,
    CoachingEngagement,
    Competency,
    CompetencyLevel,
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

logger = logging.getLogger(__name__)


class LearningIntelligenceRuntime:
    """Runtime for Universal Learning Intelligence.

    Composes from frozen UCPs:
    - Journey UCP (learning journeys)
    - Relationship UCP (coach/mentor relationships)
    - Financial UCP (learning budget/investment)
    - Knowledge UCP (knowledge objects & growth)
    - Decision UCP (learning decisions)
    - Agreement UCP (learning commitments)
    - Asset UCP (learning materials as assets)
    - Initiative UCP (learning programs as initiatives)
    """

    def __init__(self) -> None:
        self._engine = LearningIntelligenceEngine()
        self._profiles: dict[str, Any] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    # ── Profile Management ────────────────────────────────────────────────

    def get_or_create_profile(self, owner_id: str, label: str = "") -> Any:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        from core.learning_intelligence.models import LearningProfile
        p = LearningProfile(
            owner_id=owner_id,
            label=label or f"Learning profile for {owner_id}",
        )
        self._profiles[p.profile_id] = p
        return p

    def _resolve(self, owner_id: str) -> Any | None:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        return None

    # ── Skill Operations ─────────────────────────────────────────────────

    def add_skill(self, owner_id: str, name: str, category: str = "",
                  description: str = "", proficiency: str = SkillProficiency.UNKNOWN.value,
                  proficiency_score: float = 0.0) -> Skill | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        skill = Skill(name=name, owner_id=owner_id, category=category,
                      description=description, proficiency=proficiency,
                      proficiency_score=proficiency_score)
        profile.skills.append(skill)
        self._notify({"type": "learning.skill.added", "owner_id": owner_id,
                       "skill_id": skill.skill_id, "name": name})
        return skill

    def update_skill_proficiency(self, owner_id: str, skill_id: str,
                                  proficiency_score: float, proficiency: str = "") -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        for s in profile.skills:
            if s.skill_id == skill_id:
                old_score = s.proficiency_score
                s.proficiency_score = proficiency_score
                if proficiency:
                    s.proficiency = proficiency
                s.updated_at = _now_iso()
                # Record knowledge growth
                entry = KnowledgeGrowthEntry(
                    owner_id=owner_id,
                    knowledge_id=skill_id,
                    title=f"Skill growth: {s.name}",
                    domain=s.category,
                    previous_confidence=old_score,
                    new_confidence=proficiency_score,
                    delta=proficiency_score - old_score,
                    trigger="practice",
                )
                profile.knowledge_growth.append(entry)
                self._notify({"type": "learning.skill.updated", "owner_id": owner_id,
                               "skill_id": skill_id, "old_score": old_score,
                               "new_score": proficiency_score})
                return True
        return False

    # ── Learning Path Operations ─────────────────────────────────────────

    def create_learning_path(self, owner_id: str, title: str,
                              description: str = "",
                              mode: str = InteractionMode.MIXED.value,
                              target_skills: list[str] | None = None,
                              ai_guided: bool = False) -> LearningPath | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        path = LearningPath(
            owner_id=owner_id,
            title=title,
            description=description,
            mode=mode,
            target_skills=target_skills or [],
            ai_guided=ai_guided,
        )
        profile.learning_paths.append(path)
        self._notify({"type": "learning.path.created", "owner_id": owner_id,
                       "path_id": path.path_id, "title": title})
        return path

    def add_goal_to_path(self, owner_id: str, path_id: str,
                          title: str, description: str = "",
                          desired_outcome: str = "", target_date: str = "",
                          skill_ids: list[str] | None = None) -> LearningGoal | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        for p in profile.learning_paths:
            if p.path_id == path_id:
                goal = LearningGoal(
                    owner_id=owner_id,
                    learning_path_id=path_id,
                    title=title,
                    description=description,
                    desired_outcome=desired_outcome,
                    target_date=target_date,
                    skill_ids=skill_ids or [],
                )
                p.goals.append(goal)
                p.updated_at = _now_iso()
                return goal
        return None

    def add_session_to_path(self, owner_id: str, path_id: str,
                             title: str, mode: str = InteractionMode.SELF_STUDY.value,
                             duration_minutes: float = 0.0,
                             focus_area: str = "", ai_guidance: str = "") -> LearningSession | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        for p in profile.learning_paths:
            if p.path_id == path_id:
                session = LearningSession(
                    owner_id=owner_id,
                    learning_path_id=path_id,
                    title=title,
                    mode=mode,
                    duration_minutes=duration_minutes,
                    focus_area=focus_area,
                    ai_guidance=ai_guidance,
                )
                p.sessions.append(session)
                p.completed_hours += duration_minutes / 60
                p.updated_at = _now_iso()
                profile.total_learning_hours += duration_minutes / 60
                return session
        return None

    def update_goal_progress(self, owner_id: str, path_id: str,
                              goal_id: str, progress_pct: float,
                              status: str = "") -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        for p in profile.learning_paths:
            if p.path_id == path_id:
                for g in p.goals:
                    if g.goal_id == goal_id:
                        g.progress_pct = progress_pct
                        if status:
                            g.status = status
                        g.updated_at = _now_iso()
                        p.updated_at = _now_iso()
                        return True
        return False

    # ── Practice Operations ──────────────────────────────────────────────

    def record_practice(self, owner_id: str, skill_ids: list[str],
                         title: str, duration_minutes: float = 0.0,
                         performance_score: float = 0.0,
                         errors_made: int = 0,
                         insights: list[str] | None = None,
                         intensity: str = "medium") -> PracticeSession | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        session = PracticeSession(
            owner_id=owner_id,
            skill_ids=skill_ids,
            title=title,
            duration_minutes=duration_minutes,
            performance_score=performance_score,
            errors_made=errors_made,
            insights=insights or [],
            intensity=intensity,
        )
        profile.practice_sessions.append(session)

        # Update skill hours
        for sid in skill_ids:
            for s in profile.skills:
                if s.skill_id == sid:
                    s.hours_practiced += duration_minutes / 60
                    s.last_practiced = _now_iso()
                    s.updated_at = _now_iso()

        profile.total_learning_hours += duration_minutes / 60
        self._notify({"type": "learning.practice.recorded", "owner_id": owner_id,
                       "skill_ids": skill_ids, "score": performance_score})
        return session

    # ── Experience Operations ────────────────────────────────────────────

    def record_experience(self, owner_id: str, title: str,
                           description: str = "", context: str = "",
                           skills_gained: list[str] | None = None,
                           lessons_learned: list[str] | None = None,
                           domain: str = "") -> ExperienceRecord | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        exp = ExperienceRecord(
            owner_id=owner_id, title=title, description=description,
            context=context, skills_gained=skills_gained or [],
            lessons_learned=lessons_learned or [], domain=domain,
        )
        profile.experiences.append(exp)
        profile.total_learning_hours += 1  # nominal
        return exp

    # ── Certification Operations ─────────────────────────────────────────

    def add_certification(self, owner_id: str, name: str,
                           issuing_body: str = "",
                           skill_ids: list[str] | None = None,
                           issue_date: str = "", expiry_date: str = "",
                           credential_url: str = "") -> Certification | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        cert = Certification(
            owner_id=owner_id, name=name, issuing_body=issuing_body,
            skill_ids=skill_ids or [], issue_date=issue_date,
            expiry_date=expiry_date, credential_url=credential_url,
        )
        profile.certifications.append(cert)
        self._notify({"type": "learning.certification.added", "owner_id": owner_id,
                       "certification": name})
        return cert

    # ── Competency Operations ────────────────────────────────────────────

    def add_competency(self, owner_id: str, name: str,
                        description: str = "",
                        level: str = CompetencyLevel.AWARENESS.value,
                        skill_ids: list[str] | None = None) -> Competency | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        comp = Competency(
            owner_id=owner_id, name=name, description=description,
            level=level, skill_ids=skill_ids or [],
        )
        profile.competencies.append(comp)
        return comp

    # ── Coaching & Mentoring Operations ──────────────────────────────────

    def start_coaching(self, owner_id: str, coach_id: str,
                        title: str, purpose: str = "",
                        relationship_profile_id: str = "",
                        goals: list[str] | None = None) -> CoachingEngagement | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        engagement = CoachingEngagement(
            owner_id=owner_id, coach_id=coach_id, title=title,
            purpose=purpose, relationship_profile_id=relationship_profile_id,
            goals=goals or [],
        )
        profile.coaching_engagements.append(engagement)
        self._notify({"type": "learning.coaching.started", "owner_id": owner_id,
                       "coach_id": coach_id, "title": title})
        return engagement

    def start_mentoring(self, owner_id: str, mentor_id: str,
                         title: str, focus_area: str = "",
                         relationship_profile_id: str = "",
                         format: str = "regular_meetings") -> MentoringRelationship | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        rel = MentoringRelationship(
            owner_id=owner_id, mentor_id=mentor_id, title=title,
            focus_area=focus_area, relationship_profile_id=relationship_profile_id,
            format=format,
        )
        profile.mentoring_relationships.append(rel)
        self._notify({"type": "learning.mentoring.started", "owner_id": owner_id,
                       "mentor_id": mentor_id, "title": title})
        return rel

    # ── Organizational Learning ──────────────────────────────────────────

    def start_org_learning(self, owner_id: str, org_id: str,
                            name: str, description: str = "",
                            initiative_ids: list[str] | None = None) -> OrganizationalLearning | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        ol = OrganizationalLearning(
            owner_id=owner_id, org_id=org_id, name=name,
            description=description, initiative_ids=initiative_ids or [],
        )
        profile.organizational_learning.append(ol)
        self._notify({"type": "learning.org_learning.started", "owner_id": owner_id,
                       "org_id": org_id, "name": name})
        return ol

    # ── Knowledge Growth ─────────────────────────────────────────────────

    def record_knowledge_growth(self, owner_id: str, knowledge_id: str,
                                 title: str, domain: str,
                                 previous_confidence: float,
                                 new_confidence: float,
                                 trigger: str = "") -> KnowledgeGrowthEntry | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        entry = KnowledgeGrowthEntry(
            owner_id=owner_id, knowledge_id=knowledge_id, title=title,
            domain=domain, previous_confidence=previous_confidence,
            new_confidence=new_confidence,
            delta=new_confidence - previous_confidence,
            trigger=trigger,
        )
        profile.knowledge_growth.append(entry)
        return entry

    # ── Analysis & Recommendations ───────────────────────────────────────

    def analyze(self, owner_id: str) -> dict[str, Any] | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        return {
            "profile_id": profile.profile_id,
            "health": self._engine.assess_learning_health(profile),
            "growth": self._engine.measure_knowledge_growth(profile.knowledge_growth),
            "next_action": self._engine.recommend_next_action(profile).to_dict(),
            "skills": [{"name": s.name, "proficiency": s.proficiency,
                         "score": s.proficiency_score} for s in profile.skills],
            "active_paths": [{"title": p.title, "progress": p.progress_pct,
                              "goals": len(p.goals), "sessions": len(p.sessions)}
                             for p in profile.active_paths],
            "certifications": len(profile.completed_certifications),
            "practice_effectiveness": self._engine.evaluate_practice_effectiveness(
                profile.practice_sessions),
        }

    def get_skill_gaps(self, owner_id: str,
                        target_skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
        profile = self._resolve(owner_id)
        if not profile:
            return []
        recs = self._engine.analyze_skill_gaps(profile, target_skills)
        return [r.to_dict() for r in recs]

    def get_recommendations(self, owner_id: str) -> list[dict[str, Any]]:
        profile = self._resolve(owner_id)
        if not profile:
            return []
        recs = [self._engine.recommend_next_action(profile)]
        # Path-level recommendations
        for p in profile.active_paths:
            if p.overdue_goals:
                recs.extend(self._engine.handle_learning_disruption(
                    profile, p, "Overdue goals detected"))
        return [r.to_dict() for r in recs]

    def get_path_recommendation(self, owner_id: str,
                                 target_skill: str,
                                 available_hours: float = 0.0) -> dict[str, Any] | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        return self._engine.recommend_learning_path(profile, target_skill, available_hours).to_dict()

    def handle_disruption(self, owner_id: str, path_id: str,
                           disruption: str) -> list[dict[str, Any]]:
        profile = self._resolve(owner_id)
        if not profile:
            return []
        for p in profile.learning_paths:
            if p.path_id == path_id:
                recs = self._engine.handle_learning_disruption(profile, p, disruption)
                return [r.to_dict() for r in recs]
        return []

    def get_ai_guidance(self, owner_id: str,
                         target_skill: str) -> dict[str, Any] | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        return self._engine.orchestrate_ai_guided_learning(profile, target_skill)

    def explain(self, rec: dict[str, Any]) -> dict[str, Any]:
        rec_obj = LearningRecommendation(**rec)
        return self._engine.explain(rec_obj)

    # ── Lifecycle ────────────────────────────────────────────────────────

    def initialize(self) -> None:
        logger.info("LearningIntelligenceRuntime initialized")

    def shutdown(self) -> None:
        self._profiles.clear()
        self._reality_listeners.clear()

    def health_check(self) -> dict:
        return {"status": "healthy", "runtime": "learning_intelligence",
                "profile_count": len(self._profiles)}

    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict):
            self.notify(event)

    def get_capabilities(self) -> list[str]:
        return ["learning.profile", "learning.skills", "learning.paths",
                "learning.goals", "learning.practice", "learning.certifications",
                "learning.competencies", "learning.coaching", "learning.mentoring",
                "learning.org_learning", "learning.knowledge_growth",
                "learning.recommendations", "learning.ai_guidance",
                "learning.disruption", "learning.reality_integration"]

    # ── Reality Integration ──────────────────────────────────────────────

    def notify(self, notification: dict[str, Any]) -> None:
        pass

    def _notify(self, n: dict) -> None:
        for l in self._reality_listeners:
            try:
                l(n)
            except Exception:
                pass

    def register_reality_listener(self, l: Callable) -> None:
        self._reality_listeners.append(l)

    def unregister_reality_listener(self, l: Callable) -> None:
        if l in self._reality_listeners:
            self._reality_listeners.remove(l)