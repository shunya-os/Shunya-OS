"""Universal Relationship Intelligence — UCP-02.

The canonical capability for understanding, maintaining, and strengthening
relationships between every person, organization, and Living Object.

Relationship Intelligence is universal. It does not model CRM, HR, or
Customer Success. These become compositions of Relationship Intelligence.

Capabilities:
    - Relationship graph (via RelationshipEngine)
    - Trust scoring and evolution
    - Sentiment tracking and trend analysis
    - Interaction history
    - Communication history
    - Shared journeys and milestones
    - Shared documents
    - Shared creative assets
    - Shared commitments
    - Relationship health assessment
    - AI-powered understanding and insights
    - Actionable recommendations
    - Reality integration via notify(notification)
    - Adaptive execution integration

Usage:
    from core.relationship_intelligence import (
        RelationshipIntelligenceRuntime,
        RelationshipProfile,
        TrustScore,
        SentimentRecord,
        RelationshipHealth,
        Insight,
        Recommendation,
        RelationshipRole,
        TrustLevel,
        SentimentTrend,
    )

    runtime = RelationshipIntelligenceRuntime()
    profile = runtime.get_or_create_profile(
        source_id="person_001",
        target_id="org_002",
        role="customer",
    )
    health = runtime.assess_relationship_health(profile.profile_id)
    recs = runtime.get_recommendations(profile.profile_id)
"""

from core.relationship_intelligence.engine import RelationshipIntelligenceEngine
from core.relationship_intelligence.models import (
    CommunicationRecord,
    CommitmentStatus,
    HealthDimension,
    Insight,
    InteractionRecord,
    InteractionType,
    Recommendation,
    RelationshipHealth,
    RelationshipProfile,
    RelationshipRole,
    SentimentRecord,
    SentimentTrend,
    SharedCommitment,
    SharedCreativeAsset,
    SharedDocument,
    SharedJourney,
    TrustLevel,
    TrustScore,
)
from core.relationship_intelligence.provider import (
    DefaultAIProvider,
    RelationshipAIProvider,
)
from core.relationship_intelligence.runtime import (
    RelationshipIntelligenceRuntime,
    role_to_type,
)

__all__ = [
    # Runtime
    "RelationshipIntelligenceRuntime",
    "RelationshipIntelligenceEngine",
    # Models
    "RelationshipProfile",
    "TrustScore",
    "SentimentRecord",
    "CommunicationRecord",
    "InteractionRecord",
    "SharedJourney",
    "SharedDocument",
    "SharedCreativeAsset",
    "SharedCommitment",
    "RelationshipHealth",
    "Insight",
    "Recommendation",
    # Enums
    "RelationshipRole",
    "TrustLevel",
    "SentimentTrend",
    "InteractionType",
    "CommitmentStatus",
    "HealthDimension",
    # Providers
    "RelationshipAIProvider",
    "DefaultAIProvider",
    # Utilities
    "role_to_type",
]