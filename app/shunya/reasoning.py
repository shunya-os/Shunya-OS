"""
Reasoning Layer (Shunya)
Analyzes customer inquiries against knowledge base and past data.
Produces structured recommendations for the Planner layer.
"""

from typing import Optional
from .knowledge import KnowledgeLayer


class CustomerProfile:
    """Represents the analyzed customer needs."""
    def __init__(self, inquiry: dict):
        self.raw_inquiry = inquiry
        self.customer_name = inquiry.get("customer_name", "")
        self.destination = inquiry.get("destination", "")
        self.pax = inquiry.get("pax", "")
        self.dates = inquiry.get("dates", "")
        self.notes = inquiry.get("notes", "")
        self.budget_estimate: Optional[float] = None
        self.group_type: str = "unknown"  # couple/family/group/solo
        self.interests: list[str] = []
        self.requirements: list[str] = []
        self.risk_factors: list[str] = []


class ReasoningLayer:
    """
    Analyzes inquiries — matches customer needs against knowledge base,
    identifies requirements, risks, and preferences.
    """

    def __init__(self, knowledge: KnowledgeLayer):
        self.knowledge = knowledge

    def analyze_inquiry(self, inquiry: dict) -> CustomerProfile:
        """Analyze a raw inquiry and produce a customer profile."""
        profile = CustomerProfile(inquiry)

        # Infer group type from pax
        pax_str = str(profile.pax).lower()
        if "couple" in pax_str or "2" in pax_str:
            profile.group_type = "couple"
        elif "family" in pax_str or "group" in pax_str:
            profile.group_type = "family"
        elif "solo" in pax_str or "1" in pax_str:
            profile.group_type = "solo"
        else:
            profile.group_type = "group"

        # Check for destination knowledge
        dest_info = self.knowledge.search_destination(profile.destination)
        if dest_info and dest_info.local_taxes:
            profile.requirements.append(
                f"Local tax: {dest_info.local_taxes[0].get('name', 'Tax')} "
                f"at {dest_info.local_taxes[0].get('rate', 0) * 100:.0f}%"
            )

        # Check past itineraries for reference
        past = self.knowledge.get_past_itineraries(destination=profile.destination, limit=3)
        if past:
            profile.requirements.append(f"Reference: {len(past)} past itineraries available")

        return profile

    def suggest_approach(self, profile: CustomerProfile) -> dict:
        """
        Given a customer profile, suggest the best approach for the Planner.
        Returns a strategy dict.
        """
        strategy = {
            "destination": profile.destination,
            "group_type": profile.group_type,
            "requires_visa_assistance": False,
            "requires_airport_transfer": True,
            "recommended_lead_time_days": 60,
            "tax_considerations": [],
            "notes": [],
        }

        dest_info = self.knowledge.search_destination(profile.destination)
        if dest_info:
            if dest_info.visa_requirements:
                strategy["requires_visa_assistance"] = True
                strategy["notes"].append(
                    f"Visa: {', '.join(dest_info.visa_requirements)}"
                )

        # Past itineraries for reference pricing
        past = self.knowledge.get_past_itineraries(destination=profile.destination, limit=3)
        if past:
            strategy["notes"].append(f"Based on {len(past)} past similar trips")

        return strategy