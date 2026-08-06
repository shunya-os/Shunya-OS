"""UCP-11 Verification — Universal Learning Intelligence.

Verifies 8 scenarios through the same capability:
1. Personal skill development
2. Professional certification
3. Team upskilling
4. Organizational learning programme
5. Mentoring relationship
6. Coaching engagement
7. AI-guided learning path
8. Learning disruption with adaptive execution

No Learning Runtime. No LMS Runtime. No Education Runtime.
"""

from __future__ import annotations
from typing import Any
from core.learning_intelligence import (
    LearningIntelligenceRuntime,
    SkillProficiency,
    CompetencyLevel,
    InteractionMode,
    LearningStyle,
    LearningGoalStatus,
    LearningPathStatus,
)


def test_personal_skill_development() -> dict[str, Any]:
    """1. Personal skill development — learner builds coding skills."""
    r = LearningIntelligenceRuntime()
    r.get_or_create_profile("person_anika", "Anika — Personal Skill Development")

    # Add 3 skills at different levels
    r.add_skill("person_anika", "Python", "technical",
                "Python programming language", SkillProficiency.NOVICE.value, 0.25)
    r.add_skill("person_anika", "JavaScript", "technical",
                "JavaScript programming", SkillProficiency.ADVANCED_BEGINNER.value, 0.35)
    r.add_skill("person_anika", "Git", "technical",
                "Version control", SkillProficiency.COMPETENT.value, 0.55)

    # Create learning path with goals
    path = r.create_learning_path("person_anika", "Python Web Development",
                                   "Build full-stack web apps with Python",
                                   InteractionMode.MIXED.value,
                                   target_skills=["Python", "JavaScript", "HTML/CSS"])
    assert path is not None
    assert len(path.goals) == 0

    r.add_goal_to_path("person_anika", path.path_id,
                        "Learn Flask basics", "Build a simple Flask REST API",
                        "Build and deploy a REST API", "2026-12-01",
                        skill_ids=["Python"])
    r.add_goal_to_path("person_anika", path.path_id,
                        "Build portfolio project", "Complete a full-stack project",
                        "Deploy portfolio app", "2027-02-01",
                        skill_ids=["Python", "JavaScript"])

    assert len(path.goals) == 2

    # Record practice
    r.record_practice("person_anika", [path.target_skills[0]],
                       "Flask tutorial", duration_minutes=120,
                       performance_score=0.7, insights=["Learned routing and templates"])

    r.update_skill_proficiency("person_anika",
                                r._resolve("person_anika").skills[0].skill_id,
                                0.35, SkillProficiency.ADVANCED_BEGINNER.value)

    # Analyze
    analysis = r.analyze("person_anika")
    assert analysis is not None
    assert "health" in analysis
    assert "growth" in analysis

    return {"scenario": "1. Personal Skill Development", "entity": "Anika — Python Web Dev",
            "skills": len(r._resolve("person_anika").skills),
            "goals": len(path.goals), "health": analysis["health"]["level"],
            "passed": True}


def test_professional_certification() -> dict[str, Any]:
    """2. Professional certification — earning a formal credential."""
    r = LearningIntelligenceRuntime()
    r.get_or_create_profile("professional_dev", "Dev — Professional Certification")

    # Add prerequisite skills
    r.add_skill("professional_dev", "AWS Basics", "cloud",
                "Fundamentals of AWS", SkillProficiency.COMPETENT.value, 0.6)
    r.add_skill("professional_dev", "Linux", "systems",
                "Linux administration", SkillProficiency.PROFICIENT.value, 0.75)

    # Create study path
    path = r.create_learning_path("professional_dev", "AWS Solutions Architect Prep",
                                   "Prepare for AWS SAA-C03 exam",
                                   InteractionMode.SELF_STUDY.value,
                                   target_skills=["AWS Basics", "Linux", "Networking"])
    assert path is not None

    r.add_goal_to_path("professional_dev", path.path_id,
                        "Complete all exam domains",
                        "Study all 4 exam domains thoroughly",
                        "Score 80%+ on practice exams", "2026-11-15")
    r.add_goal_to_path("professional_dev", path.path_id,
                        "Pass certification exam",
                        "Achieve AWS Solutions Architect Associate",
                        "Certification earned", "2026-12-01")

    # Study sessions
    r.add_session_to_path("professional_dev", path.path_id,
                           "Domain 1: Design Secure Architectures",
                           InteractionMode.READING.value, 180, "Security")
    r.add_session_to_path("professional_dev", path.path_id,
                           "Domain 2: Resilient Architectures",
                           InteractionMode.READING.value, 150, "Resilience")

    # Add certification
    cert = r.add_certification("professional_dev", "AWS Solutions Architect Associate",
                                "Amazon Web Services",
                                skill_ids=["AWS Basics", "Linux"],
                                credential_url="https://aws.amazon.com/certification/")
    assert cert is not None
    assert cert.issuing_body == "Amazon Web Services"

    # Add competency
    comp = r.add_competency("professional_dev", "Cloud Architecture",
                             "Design and implement cloud solutions",
                             CompetencyLevel.APPLICATION.value,
                             skill_ids=["AWS Basics", "Linux"])
    assert comp is not None

    recs = r.get_recommendations("professional_dev")
    assert recs is not None

    return {"scenario": "2. Professional Certification", "entity": "Dev — AWS SAA",
            "skills": len(r._resolve("professional_dev").skills),
            "certifications": len(r._resolve("professional_dev").certifications),
            "competencies": len(r._resolve("professional_dev").competencies),
            "recommendations": len(recs), "passed": True}


def test_team_upskilling() -> dict[str, Any]:
    """3. Team upskilling — team collectively builds new capabilities."""
    r = LearningIntelligenceRuntime()
    profile = r.get_or_create_profile("team_alpha", "Team Alpha — Upskilling")

    # Team members learn in parallel
    for member, skill_name, base_score in [
        ("Alice", "Kubernetes", 0.3),
        ("Bob", "Kubernetes", 0.2),
        ("Carol", "Kubernetes", 0.1),
    ]:
        path = r.create_learning_path(member, f"Learn Kubernetes - {member}",
                                       "Container orchestration skills",
                                       InteractionMode.GROUP.value,
                                       target_skills=["Kubernetes", "Docker"])
        assert path is not None
        r.add_goal_to_path(member, path.path_id,
                            f"{member}: Deploy first cluster",
                            f"Deploy a Kubernetes cluster from scratch")
        r.record_practice(member, ["Kubernetes", "Docker"],
                           f"{member} K8s practice", duration_minutes=90,
                           performance_score=0.3)

    profile.preferred_style = LearningStyle.MIXED.value
    profile.total_learning_hours = 12.5

    # Team-level organizational learning
    ol = r.start_org_learning("team_alpha", "team_alpha",
                               "Kubernetes Upskilling Programme",
                               "Team-wide Kubernetes training initiative",
                               initiative_ids=["init_001", "init_002"])
    assert ol is not None
    ol.total_learners = 3
    ol.total_capabilities = 2
    ol.learning_culture_score = 0.65

    analysis = r.analyze("team_alpha")
    assert analysis is not None
    assert analysis["health"]["score"] > 0

    return {"scenario": "3. Team Upskilling", "entity": "Team Alpha — Kubernetes",
            "total_learners": ol.total_learners,
            "total_capabilities": ol.total_capabilities,
            "learning_culture_score": ol.learning_culture_score,
            "health": analysis["health"]["level"], "passed": True}


def test_org_learning_programme() -> dict[str, Any]:
    """4. Organizational learning programme — enterprise-wide capability building."""
    r = LearningIntelligenceRuntime()
    r.get_or_create_profile("org_leadership", "Acme Corp — Leadership Programme")

    # Multiple learning paths for leadership programme
    paths_data = [
        ("Strategic Thinking", 0.6, 3),
        ("Data-Driven Decision Making", 0.4, 2),
        ("Team Leadership", 0.7, 4),
    ]

    for pname, progress, goals_count in paths_data:
        path = r.create_learning_path("org_leadership", pname,
                                       f"Leadership module: {pname}",
                                       InteractionMode.WORKSHOP.value,
                                       ai_guided=True)
        assert path is not None
        for i in range(goals_count):
            r.add_goal_to_path("org_leadership", path.path_id,
                                f"{pname} Goal {i+1}", f"Sub-goal for {pname}")
        path.status = LearningPathStatus.ACTIVE.value

    # Organizational learning programme
    ol = r.start_org_learning("org_leadership", "acme_corp",
                               "Acme Leadership Development Programme",
                               "Comprehensive leadership capability building for all managers",
                               initiative_ids=["leadership_2026"])
    assert ol is not None
    ol.total_learners = 45
    ol.total_capabilities = 8
    ol.learning_culture_score = 0.72
    ol.impact_metrics = {
        "employee_engagement": 0.78,
        "internal_promotions": 0.35,
        "retention_rate": 0.92,
    }

    # Add knowledge growth
    r.record_knowledge_growth("org_leadership", "k_001",
                               "Strategic frameworks", "leadership",
                               0.3, 0.65, trigger="workshop")

    analysis = r.analyze("org_leadership")
    assert analysis is not None
    assert analysis["health"]["level"] is not None

    return {"scenario": "4. Organizational Learning Programme", "entity": "Acme Corp — Leadership",
            "total_learners": ol.total_learners,
            "total_capabilities": ol.total_capabilities,
            "learning_culture_score": ol.learning_culture_score,
            "active_paths": len(r._resolve("org_leadership").active_paths),
            "health": analysis["health"]["level"], "passed": True}


def test_mentoring_relationship() -> dict[str, Any]:
    """5. Mentoring relationship — experienced guidance for career growth."""
    r = LearningIntelligenceRuntime()
    r.get_or_create_profile("junior_priya", "Priya — Mentee")

    r.add_skill("junior_priya", "React", "frontend",
                "React.js development", SkillProficiency.NOVICE.value, 0.2)
    r.add_skill("junior_priya", "TypeScript", "frontend",
                "TypeScript programming", SkillProficiency.ADVANCED_BEGINNER.value, 0.3)

    # Start mentoring relationship
    mentor_rel = r.start_mentoring(
        "junior_priya", "senior_ravi",
        "Frontend Engineering Mentorship",
        "React and TypeScript mastery",
        format="biweekly",
    )
    assert mentor_rel is not None
    mentor_rel.frequency = "biweekly"
    mentor_rel.topics_covered = ["React hooks", "State management", "TypeScript generics"]
    mentor_rel.milestones = [
        {"title": "Complete React fundamentals", "status": "completed"},
        {"title": "Build sample app", "status": "in_progress"},
        {"title": "Contribute to team project", "status": "pending"},
    ]
    mentor_rel.satisfaction_score = 0.85
    mentor_rel.duration_months = 3

    # Priya creates a learning path guided by mentor
    path = r.create_learning_path("junior_priya", "React Mastery with Mentor",
                                   "Guided by Ravi, mentor from frontend team",
                                   InteractionMode.ONE_ON_ONE.value,
                                   target_skills=["React", "TypeScript", "CSS"],
                                   ai_guided=False)
    assert path is not None
    path.mentor_id = "senior_ravi"

    analysis = r.analyze("junior_priya")
    assert analysis is not None

    return {"scenario": "5. Mentoring Relationship", "entity": "Priya — Frontend Mentorship",
            "skills": len(r._resolve("junior_priya").skills),
            "mentor_topics": len(mentor_rel.topics_covered),
            "satisfaction": mentor_rel.satisfaction_score,
            "health": analysis["health"]["level"], "passed": True}


def test_coaching_engagement() -> dict[str, Any]:
    """6. Coaching engagement — structured coaching for specific growth."""
    r = LearningIntelligenceRuntime()
    r.get_or_create_profile("manager_kiran", "Kiran — Coaching")

    # Kiran has management skills but needs coaching
    r.add_skill("manager_kiran", "Team Management", "leadership",
                "Managing engineering teams", SkillProficiency.COMPETENT.value, 0.55)
    r.add_skill("manager_kiran", "Conflict Resolution", "soft",
                "Resolving team conflicts", SkillProficiency.NOVICE.value, 0.15)
    r.add_skill("manager_kiran", "Strategic Planning", "leadership",
                "Long-term planning", SkillProficiency.ADVANCED_BEGINNER.value, 0.3)

    # Coaching engagement
    coaching = r.start_coaching(
        "manager_kiran", "coach_sunita",
        "Leadership Coaching for Engineering Managers",
        "Develop strategic leadership and team management capabilities",
        goals=[
            "Improve team delegation skills",
            "Develop strategic planning capability",
            "Enhance conflict resolution approach",
        ]
    )
    assert coaching is not None
    coaching.focus_areas = ["Delegation", "Strategic thinking", "Conflict resolution"]
    coaching.session_count = 4
    coaching.total_hours = 8.0
    coaching.outcomes = [
        "Created team development plan",
        "Completed 360-degree feedback review",
        "Developed quarterly strategy document",
    ]

    # Record experience
    r.record_experience("manager_kiran", "Led quarterly planning session",
                         "Facilitated the Q4 planning session with cross-functional team",
                         "New responsibility as team lead",
                         skills_gained=["Strategic Planning", "Facilitation"],
                         lessons_learned=["Break down strategy into actionable OKRs",
                                          "Align team goals with org priorities"],
                         domain="leadership")

    analysis = r.analyze("manager_kiran")
    assert analysis is not None

    return {"scenario": "6. Coaching Engagement", "entity": "Kiran — Leadership Coaching",
            "skills": len(r._resolve("manager_kiran").skills),
            "coaching_sessions": coaching.session_count,
            "coaching_hours": coaching.total_hours,
            "experiences": len(r._resolve("manager_kiran").experiences),
            "health": analysis["health"]["level"], "passed": True}


def test_ai_guided_learning_path() -> dict[str, Any]:
    """7. AI-guided learning path — AI tailors the learning experience."""
    r = LearningIntelligenceRuntime()
    r.get_or_create_profile("ai_learner_sam", "Sam — AI-Guided Learning")

    # Sam has some existing skills
    r.add_skill("ai_learner_sam", "Python", "technical",
                "Python programming", SkillProficiency.COMPETENT.value, 0.55)
    r.add_skill("ai_learner_sam", "Data Analysis", "data",
                "Data analysis with Python", SkillProficiency.ADVANCED_BEGINNER.value, 0.3)
    r.add_skill("ai_learner_sam", "SQL", "data",
                "SQL querying", SkillProficiency.PROFICIENT.value, 0.7)

    profile = r._resolve("ai_learner_sam")
    profile.preferred_style = LearningStyle.VISUAL.value

    # Create AI-guided learning path
    path = r.create_learning_path("ai_learner_sam", "Machine Learning Foundations",
                                   "AI-recommended path to ML basics",
                                   InteractionMode.AI_GUIDED.value,
                                   target_skills=["Machine Learning", "Statistics"],
                                   ai_guided=True)
    assert path is not None
    path.assessment_type = "portfolio"

    r.add_goal_to_path("ai_learner_sam", path.path_id,
                        "Understand ML fundamentals",
                        "Supervised, unsupervised, reinforcement learning basics",
                        "Explain key ML concepts confidently", "2026-11-01")
    r.add_goal_to_path("ai_learner_sam", path.path_id,
                        "Build first ML model",
                        "Train and evaluate a model on real data",
                        "Deploy a working ML model", "2027-01-01")

    # AI-guided sessions
    r.add_session_to_path("ai_learner_sam", path.path_id,
                           "Introduction to ML Concepts",
                           InteractionMode.AI_GUIDED.value, 90, "Fundamentals",
                           ai_guidance="Explain supervised vs unsupervised learning with visual examples")
    r.add_session_to_path("ai_learner_sam", path.path_id,
                           "Python ML Libraries",
                           InteractionMode.AI_GUIDED.value, 120, "Tools",
                           ai_guidance="Walk through scikit-learn with interactive code examples")

    # Get AI guidance
    guidance = r.get_ai_guidance("ai_learner_sam", "Machine Learning")
    assert guidance is not None
    assert "learning_stage" in guidance
    assert "suggested_modes" in guidance
    assert "focus" in guidance

    recs = r.get_path_recommendation("ai_learner_sam", "Machine Learning",
                                      available_hours=8.0)
    assert recs is not None

    return {"scenario": "7. AI-Guided Learning Path", "entity": "Sam — ML Foundations",
            "skills": len(profile.skills),
            "learning_stage": guidance["learning_stage"],
            "suggested_modes": len(guidance["suggested_modes"]),
            "recommendation": recs["title"],
            "passed": True}


def test_learning_disruption_adaptive() -> dict[str, Any]:
    """8. Learning disruption with adaptive execution — path adapts to change."""
    r = LearningIntelligenceRuntime()
    r.get_or_create_profile("busy_learner_raj", "Raj — Disrupted Learning")

    # Initial skills
    r.add_skill("busy_learner_raj", "Go", "technical",
                "Go programming", SkillProficiency.ADVANCED_BEGINNER.value, 0.3)
    r.add_skill("busy_learner_raj", "Docker", "devops",
                "Containerization", SkillProficiency.COMPETENT.value, 0.5)
    r.add_skill("busy_learner_raj", "Kubernetes", "devops",
                "Container orchestration", SkillProficiency.NOVICE.value, 0.15)

    # Learning path with tight deadlines
    path = r.create_learning_path("busy_learner_raj", "Go Backend Developer",
                                   "Become a Go backend developer in 3 months",
                                   InteractionMode.SELF_STUDY.value,
                                   target_skills=["Go", "PostgreSQL", "gRPC"])
    assert path is not None

    # Add goals with aggressive dates that will become overdue
    r.add_goal_to_path("busy_learner_raj", path.path_id,
                        "Go syntax and fundamentals",
                        "Master Go syntax, types, and concurrency",
                        "Write production Go code", "2026-03-01",
                        skill_ids=["Go"])
    r.add_goal_to_path("busy_learner_raj", path.path_id,
                        "Build REST API in Go",
                        "Build a REST API using Gin framework",
                        "Deploy a Go API service", "2026-04-01",
                        skill_ids=["Go"])
    r.add_goal_to_path("busy_learner_raj", path.path_id,
                        "Database integration",
                        "PostgreSQL with Go",
                        "Implement database layer", "2026-05-01",
                        skill_ids=["Go"])

    assert len(path.goals) == 3

    # Some practice recorded
    r.record_practice("busy_learner_raj", ["Go"],
                       "Go basics tutorial", duration_minutes=60,
                       performance_score=0.6, insights=["Learned goroutines basics"])
    r.record_practice("busy_learner_raj", ["Go"],
                       "Go HTTP server", duration_minutes=90,
                       performance_score=0.5, errors_made=3,
                       insights=["Need more work on error handling"])

    # Simulate disruption
    disruption = "Raj's team was reassigned to a critical production issue, " \
                 "requiring 3 weeks of full-time focus. All learning activities paused."

    # Handle disruption
    recs = r.handle_disruption("busy_learner_raj", path.path_id, disruption)
    assert len(recs) >= 1
    for rec in recs:
        assert "reasoning" in rec
        assert "evidence" in rec
        assert "assumptions" in rec
        assert "alternatives" in rec
        assert "expected_impact" in rec

    # Mark first 2 goals as overdue
    r.update_goal_progress("busy_learner_raj", path.path_id,
                            path.goals[0].goal_id, 30)
    r.update_goal_progress("busy_learner_raj", path.path_id,
                            path.goals[1].goal_id, 10)

    # Get recommendations which should include disruption guidance
    all_recs = r.get_recommendations("busy_learner_raj")
    assert len(all_recs) >= 1

    # Verify LearningRecommendation structure
    for rec in recs:
        assert "reasoning" in rec, f"Missing reasoning in: {rec.get('title', 'unknown')}"
        assert "evidence" in rec, f"Missing evidence in: {rec.get('title', 'unknown')}"
        assert "confidence" in rec, f"Missing confidence in: {rec.get('title', 'unknown')}"
        assert "assumptions" in rec, f"Missing assumptions in: {rec.get('title', 'unknown')}"
        assert "alternatives" in rec, f"Missing alternatives in: {rec.get('title', 'unknown')}"
        assert "expected_impact" in rec, f"Missing expected_impact in: {rec.get('title', 'unknown')}"

    return {"scenario": "8. Learning Disruption + Adaptive Execution",
            "entity": "Raj — Go Backend Dev",
            "skills": len(r._resolve("busy_learner_raj").skills),
            "goals": len(path.goals),
            "disruption_recs": len(recs),
            "total_recs": len(all_recs),
            "passed": True}


def run_all() -> list[dict[str, Any]]:
    tests = [
        ("Personal Skill Development", test_personal_skill_development),
        ("Professional Certification", test_professional_certification),
        ("Team Upskilling", test_team_upskilling),
        ("Org Learning Programme", test_org_learning_programme),
        ("Mentoring Relationship", test_mentoring_relationship),
        ("Coaching Engagement", test_coaching_engagement),
        ("AI-Guided Learning Path", test_ai_guided_learning_path),
        ("Disruption + Adaptive Execution", test_learning_disruption_adaptive),
    ]
    results = []
    for n, fn in tests:
        try:
            r = fn()
            r["test_name"] = n
            r["status"] = "PASS"
            r["error"] = None
        except Exception as e:
            import traceback
            r = {"test_name": n, "scenario": n, "status": "FAIL",
                 "error": str(e), "traceback": traceback.format_exc(), "passed": False}
        results.append(r)
    return results


if __name__ == "__main__":
    print("UCP-11 — Universal Learning Intelligence: Verification Report")
    print("=" * 70)
    results = run_all()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    for r in results:
        s = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"\n  {s} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("skills") is not None:
            print(f"         Skills: {r['skills']}")
        if r.get("goals") is not None:
            print(f"         Goals: {r['goals']}")
        if r.get("health"):
            print(f"         Health: {r['health']}")
        if r.get("certifications") is not None:
            print(f"         Certifications: {r['certifications']}")
        if r.get("competencies") is not None:
            print(f"         Competencies: {r['competencies']}")
        if r.get("coaching_sessions") is not None:
            print(f"         Coaching sessions: {r['coaching_sessions']}")
        if r.get("learning_stage"):
            print(f"         Learning stage: {r['learning_stage']}")
        if r.get("disruption_recs") is not None:
            print(f"         Disruption recs: {r['disruption_recs']}")
        if r.get("recommendations") is not None:
            print(f"         Recommendations: {r['recommendations']}")
        if r.get("error"):
            print(f"         ERROR: {r['error']}")
    print(f"\n  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    if not failed:
        print("\n  ✅ UCP-11 VERIFICATION PASSED: All 8 learning scenarios through one capability.")
        print("  No Learning Runtime. No LMS Runtime. No Education Runtime.")