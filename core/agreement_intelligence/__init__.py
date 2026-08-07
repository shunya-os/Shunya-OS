"""Universal Agreement Intelligence — UCP-06.

Agreement Intelligence models commitments established between two or more parties.
It does not model legal software, contract management, or procurement systems.

Composes exclusively from frozen SHUNYA runtimes.
No Contract Runtime. No Procurement Runtime. No Legal Runtime.
"""

from core.agreement_intelligence.engine import AgreementIntelligenceEngine
from core.agreement_intelligence.models import (
    Agreement,
    AgreementProfile,
    AgreementRecommendation,
    AgreementStatus,
    AgreementType,
    Amendment,
    Condition,
    Milestone,
    Obligation,
    ObligationStatus,
    Party,
    RiskLevel,
)
from core.agreement_intelligence.runtime import AgreementIntelligenceRuntime

__all__ = [
    "AgreementIntelligenceRuntime", "AgreementIntelligenceEngine",
    "Agreement", "AgreementProfile", "AgreementRecommendation",
    "Amendment", "Condition", "Milestone", "Obligation", "Party",
    "AgreementStatus", "AgreementType", "ObligationStatus", "RiskLevel",
]