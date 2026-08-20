"""G4 — Universal Revenue, Relationship & Commercial Execution.

The commercial domain is NOT a CRM. It is a universal, business-agnostic
representation of the path:

RELATIONSHIP → OPPORTUNITY/NEED → UNDERSTANDING → COMMERCIAL CONTEXT
→ PROPOSAL/OFFER → NEGOTIATION/DECISION → AGREEMENT/COMMITMENT
→ EXECUTION → OUTCOME → RELATIONSHIP MEMORY → FUTURE INTELLIGENCE

No industry-specific terms (lead, customer, deal, quote) are hardcoded
into the canonical model. Business vocabulary adapts at the presentation
layer through CommercialType configuration.
"""
from flask import Blueprint

commercial_bp = Blueprint(
    "commercial", __name__, url_prefix="/api/v1/commercial"
)