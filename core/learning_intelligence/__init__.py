"""Universal Learning Intelligence — UCP-11.

Model continuous learning. Not LMS, not education software. Model Learning.

Composes from: Journey, Relationship, Financial, Knowledge, Decision, Agreement,
Asset, and Initiative UCPs.

Supports: Skills, Knowledge Growth, Competencies, Certifications, Practice,
Experience, Coaching, Mentoring, Organizational Learning, AI-guided Learning.

No Learning Runtime. No LMS Runtime. No Education Runtime.
"""

from core.learning_intelligence.engine import LearningIntelligenceEngine
from core.learning_intelligence.models import (
    Certification,
    CoachingEngagement,
    Competency,
    CompetencyLevel,
    ExperienceRecord,
    KnowledgeGrowthEntry,
    LearningRecommendation,
    LearningProfile,
    LearningSession,
    MentoringRelationship,
    OrganizationalLearning,
    PracticeSession,
    Skill,
    SkillProficiency,
    LearningGoal,
    LearningGoalStatus,
    LearningPath,
    LearningPathStatus,
    LearningStyle,
    InteractionMode,
    AssessmentType,
)
from core.learning_intelligence.runtime import LearningIntelligenceRuntime

__all__ = [
    "LearningIntelligenceRuntime",
    "LearningIntelligenceEngine",
    "Skill",
    "LearningProfile",
    "LearningRecommendation",
    "KnowledgeGrowthEntry",
    "Competency",
    "Certification",
    "PracticeSession",
    "ExperienceRecord",
    "CoachingEngagement",
    "MentoringRelationship",
    "OrganizationalLearning",
    "LearningSession",
    "SkillProficiency",
    "CompetencyLevel",
    "LearningGoal",
    "LearningGoalStatus",
    "LearningPath",
    "LearningPathStatus",
    "LearningStyle",
    "InteractionMode",
    "AssessmentType",
]