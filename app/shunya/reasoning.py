"""
Shunya — Reasoning Layer (Unit 4, v2)

Analyzes customer inquiries against knowledge base.
Detects occasions, infers group types, estimates budgets, flags risks.
"""

from typing import Optional
from .knowledge import KnowledgeLayer, Destination


class CustomerProfile:
    """Analyzed customer needs from a raw inquiry."""

    OCCASIONS = ["honeymoon", "wedding", "anniversary", "birthday",
                 "family trip", "business", "friends trip", "solo",
                 "destination wedding", "pre-wedding shoot", "honeymoon"]

    def __init__(self, inquiry: dict):
        self.raw_inquiry = inquiry
        self.customer_name = inquiry.get("customer_name", "")
        self.destination = inquiry.get("destination", "")
        self.pax = inquiry.get("pax", "")
        self.dates = inquiry.get("dates", "")
        self.notes = inquiry.get("notes", "")
        self.phone = inquiry.get("phone", "")
        self.budget_estimate: Optional[float] = None
        self.group_type: str = "unknown"
        self.occasion: str = ""
        self.interests: list[str] = []
        self.requirements: list[str] = []
        self.risk_factors: list[str] = []
        self.destination_info: Optional[Destination] = None

    def infer_group_type(self):
        pax = str(self.pax).lower()
        notes = str(self.notes).lower()
        combined = f"{pax} {notes}"

        if "solo" in combined or "single" in combined or ("1 " in combined and "adult" in combined):
            self.group_type = "solo"
        elif any(w in combined for w in ["couple", "honeymoon", "romantic", "just the two"]):
            self.group_type = "couple"
        elif any(w in combined for w in ["family", "kids", "children", "child", "baby"]):
            self.group_type = "family"
        elif any(w in combined for w in ["group", "friends", "corporate", "team"]):
            self.group_type = "group"
        else:
            # Try from pax count
            try:
                nums = [int(s) for s in pax.split() if s.isdigit()]
                if nums:
                    n = nums[0]
                    if n <= 2:
                        self.group_type = "couple"
                    elif n <= 5:
                        self.group_type = "family"
                    else:
                        self.group_type = "group"
            except (ValueError, AttributeError):
                pass
        if self.group_type == "unknown":
            self.group_type = "couple"  # best default for travel

    def infer_occasion(self):
        text = f"{self.notes} {self.destination} {self.customer_name}".lower()
        for occ in self.OCCASIONS:
            if occ in text:
                self.occasion = occ
                return
        # Default based on group type
        if self.group_type == "couple":
            self.occasion = "vacation"
        else:
            self.occasion = "travel"

    def estimate_budget_daily(self) -> tuple[float, str]:
        """Returns (daily budget per person, currency) based on destination."""
        dest = self.destination_info
        if not dest:
            return 5000, "INR"

        country = dest.country.lower()
        if "maldives" in country:
            return 15000, "INR"  # 2-3x premium
        elif "indonesia" in country:
            return 6000, "INR"
        elif "sri lanka" in country:
            return 4000, "INR"
        elif "thailand" in country:
            return 5000, "INR"
        else:
            return 5000, "INR"

    def to_dict(self) -> dict:
        return {
            "customer_name": self.customer_name,
            "destination": self.destination,
            "pax": self.pax,
            "dates": self.dates,
            "group_type": self.group_type,
            "occasion": self.occasion,
            "budget_estimate": self.budget_estimate,
            "interests": self.interests,
            "requirements": self.requirements,
            "risk_factors": self.risk_factors,
        }


class ReasoningLayer:
    """Analyzes inquiries — matches against knowledge, identifies risks, suggests approach."""

    def __init__(self, knowledge: KnowledgeLayer):
        self.knowledge = knowledge

    def analyze_inquiry(self, inquiry: dict) -> CustomerProfile:
        profile = CustomerProfile(inquiry)
        profile.infer_group_type()
        profile.infer_occasion()

        # Look up destination
        dest = self.knowledge.search_destination(profile.destination)
        profile.destination_info = dest

        if dest:
            # Add wedding requirements if applicable
            if "wedding" in profile.occasion or "wedding" in str(profile.notes).lower():
                wedding_info = self.knowledge.get_wedding_requirements(profile.destination)
                profile.requirements.append(f"Wedding: {wedding_info[:200]}")

            # Tax notes
            for tax in dest.local_taxes:
                profile.requirements.append(
                    f"Tax: {tax.get('name', '')} at {tax.get('rate', 0) * 100:.0f}%"
                )

            # Venue suggestions
            if dest.top_venues:
                profile.interests.append(f"Venues: {', '.join(dest.top_venues[:3])}")

            # Weather
            if dest.weather_notes:
                profile.requirements.append(f"Weather: {dest.weather_notes[:150]}")

        # Past itineraries for reference
        past = self.knowledge.get_past_itineraries(destination=profile.destination, limit=3)
        if past:
            profile.requirements.append(f"Reference past trips: {len(past)} available")

        # Estimate budget
        daily, curr = profile.estimate_budget_daily()
        profile.budget_estimate = daily

        return profile

    def suggest_approach(self, profile: CustomerProfile) -> dict:
        """Generate a strategy dict for the Planner layer."""
        strategy = {
            "destination": profile.destination,
            "group_type": profile.group_type,
            "occasion": profile.occasion,
            "requires_visa_assistance": False,
            "requires_airport_transfer": True,
            "recommended_lead_time_days": 60,
            "daily_budget_per_person": profile.budget_estimate or 5000,
            "currency": "INR",
            "tax_considerations": [],
            "notes": [],
            "venue_suggestions": profile.interests[:3],
        }

        dest = profile.destination_info
        if dest:
            if dest.visa_info:
                strategy["requires_visa_assistance"] = True
                strategy["notes"].append(f"Visa: {dest.visa_info[:150]}")

            if dest.transport_notes:
                strategy["notes"].append(f"Transport: {dest.transport_notes[:150]}")

            if dest.top_venues:
                strategy["venue_suggestions"] = dest.top_venues[:5]

        # Occasion-specific lead time
        if profile.occasion in ("wedding", "destination wedding"):
            strategy["recommended_lead_time_days"] = 120
        elif profile.occasion == "honeymoon":
            strategy["recommended_lead_time_days"] = 90

        if profile.risk_factors:
            strategy["notes"].extend(profile.risk_factors)

        return strategy