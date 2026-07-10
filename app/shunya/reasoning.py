"""
Shunya — Reasoning Layer v3 (Evidence + Confidence)

Upgraded to output:
- Decision: best recommendation
- Confidence: 0.0 to 1.0 score
- Evidence: list of facts used
- Explanation: why this decision was made
- Alternatives: other viable options considered
"""

import re
from typing import Optional
from dataclasses import dataclass, field
from .knowledge import KnowledgeLayer, Destination


@dataclass
class ReasoningEvidence:
    """A single piece of evidence supporting a reasoning decision."""
    fact_key: str = ""
    value: str = ""
    relevance: float = 0.5
    source: str = "knowledge_base"


@dataclass
class ReasoningResult:
    """Complete reasoning output with evidence chain."""
    decision: str = ""
    confidence: float = 0.0
    evidence: list[ReasoningEvidence] = field(default_factory=list)
    explanation: str = ""
    alternatives: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "confidence": round(self.confidence, 2),
            "evidence": [{"fact": e.fact_key, "value": e.value[:100], "relevance": e.relevance} for e in self.evidence],
            "explanation": self.explanation,
            "alternatives": self.alternatives,
            "risks": self.risk_flags,
        }


class CustomerProfile:
    OCCASIONS = ["honeymoon", "wedding", "anniversary", "birthday",
                 "family trip", "business", "friends trip", "solo",
                 "destination wedding", "pre-wedding shoot"]

    def __init__(self, inquiry: dict):
        self.raw_inquiry = inquiry
        self.customer_name = inquiry.get("customer_name", "")
        self.destination = inquiry.get("destination", "")
        self.pax = inquiry.get("pax", "")
        self.dates = inquiry.get("dates", "")
        self.notes = inquiry.get("notes", "")
        self.phone = inquiry.get("phone", "")
        self.budget_estimate = None
        self.group_type = "unknown"
        self.occasion = ""
        self.interests = []
        self.requirements = []
        self.risk_factors = []
        self.destination_info = None
        self.reasoning_result = ReasoningResult()

    def infer_group_type(self):
        pax = str(self.pax).lower()
        notes = str(self.notes).lower()
        combined = f"{pax} {notes}"
        if "solo" in combined or "single" in combined:
            self.group_type = "solo"
        elif any(w in combined for w in ["couple", "honeymoon", "romantic"]):
            self.group_type = "couple"
        elif any(w in combined for w in ["family", "kids", "children", "child"]):
            self.group_type = "family"
        elif any(w in combined for w in ["group", "friends", "corporate"]):
            self.group_type = "group"
        else:
            try:
                nums = [int(s) for s in pax.split() if s.isdigit()]
                if nums:
                    n = nums[0]
                    self.group_type = "couple" if n <= 2 else "family" if n <= 5 else "group"
            except (ValueError, AttributeError):
                pass
        if self.group_type == "unknown":
            self.group_type = "couple"

    def infer_occasion(self):
        text = f"{self.notes} {self.destination} {self.customer_name}".lower()
        for occ in self.OCCASIONS:
            if occ in text:
                self.occasion = occ
                return
        self.occasion = "vacation" if self.group_type == "couple" else "travel"

    def estimate_budget_daily(self):
        if not self.destination_info:
            return 5000, "INR"
        country = self.destination_info.country.lower()
        mapping = {"maldives": (15000, "INR"), "indonesia": (6000, "INR"),
                   "sri lanka": (4000, "INR"), "thailand": (5000, "INR")}
        for k, v in mapping.items():
            if k in country:
                return v
        return 5000, "INR"


class ReasoningLayer:
    """Analyzes inquiries with evidence chains and confidence scoring."""

    def __init__(self, knowledge: KnowledgeLayer, knowledge_store=None):
        self.knowledge = knowledge
        self._store = knowledge_store

    def analyze_inquiry(self, inquiry: dict) -> CustomerProfile:
        profile = CustomerProfile(inquiry)
        profile.infer_group_type()
        profile.infer_occasion()

        dest = self.knowledge.search_destination(profile.destination)
        profile.destination_info = dest

        evidence = []

        if dest:
            evidence.append(ReasoningEvidence(
                fact_key=f"destination.{dest.name.lower()}",
                value=f"Destination {dest.name} found in knowledge base",
                relevance=0.9, source="knowledge_base"
            ))

            if "wedding" in profile.occasion or "wedding" in str(profile.notes).lower():
                wedding_info = self.knowledge.get_wedding_requirements(profile.destination)
                profile.requirements.append(f"Wedding: {wedding_info[:200]}")
                evidence.append(ReasoningEvidence(
                    fact_key="policy.wedding_requirements",
                    value=wedding_info[:150], relevance=0.85, source="knowledge_base"
                ))

            if dest.weather_notes:
                profile.requirements.append(f"Weather: {dest.weather_notes[:150]}")
                evidence.append(ReasoningEvidence(
                    fact_key=f"destination.{dest.name.lower()}.weather",
                    value=dest.weather_notes[:150], relevance=0.7, source="knowledge_base"
                ))

            if dest.top_venues:
                profile.interests.append(f"Venues: {', '.join(dest.top_venues[:3])}")

        # Check immutable knowledge store for additional facts
        if self._store:
            for key_suffix in [f"destination.{profile.destination.lower()}.visa",
                               f"destination.{profile.destination.lower()}.taxes",
                               f"destination.{profile.destination.lower()}.weather"]:
                fact = self._store.get(key_suffix)
                if fact:
                    evidence.append(ReasoningEvidence(
                        fact_key=key_suffix, value=str(fact["value"])[:150],
                        relevance=0.8, source="immutable_knowledge_store"
                    ))

        past = self.knowledge.get_past_itineraries(destination=profile.destination, limit=3)
        if past:
            profile.requirements.append(f"Reference past trips: {len(past)} available")
            evidence.append(ReasoningEvidence(
                fact_key="itinerary_refs", value=f"{len(past)} past itineraries",
                relevance=0.6, source="database"
            ))

        daily, curr = profile.estimate_budget_daily()
        profile.budget_estimate = daily

        # Build reasoning result
        dest_name = profile.destination or "Unknown"
        confidence = 0.9 if dest else 0.3

        explanation_parts = []
        if dest:
            explanation_parts.append(f"Destination '{dest.name}' is recognized with high confidence")
            if profile.occasion:
                explanation_parts.append(f"Occasion detected as '{profile.occasion}'")
            if profile.group_type:
                explanation_parts.append(f"Group type inferred as '{profile.group_type}'")
        else:
            explanation_parts.append(f"Destination '{dest_name}' not found in knowledge base — proceeding with low confidence")
            profile.risk_factors.append(f"Destination '{dest_name}' not in knowledge base")

        explanation_parts.append(f"Estimated daily budget: ₹{daily:.0f} per person")

        profile.reasoning_result = ReasoningResult(
            decision=f"Plan {profile.occasion or 'travel'} trip to {dest_name} for {profile.group_type}",
            confidence=confidence,
            evidence=evidence,
            explanation=" | ".join(explanation_parts),
            alternatives=[f"Alternative: {alt}" for alt in (dest.top_venues[:2] if dest and dest.top_venues else [])],
            risk_flags=profile.risk_factors,
        )
        return profile

    def suggest_approach(self, profile: CustomerProfile) -> dict:
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
            "reasoning_evidence": profile.reasoning_result.to_dict(),
            "reasoning_confidence": profile.reasoning_result.confidence,
        }
        dest = profile.destination_info
        if dest:
            if dest.visa_info:
                strategy["requires_visa_assistance"] = True
                strategy["notes"].append(f"Visa: {dest.visa_info[:150]}")
            if dest.top_venues:
                strategy["venue_suggestions"] = dest.top_venues[:5]
        if profile.occasion in ("wedding", "destination wedding"):
            strategy["recommended_lead_time_days"] = 120
        elif profile.occasion == "honeymoon":
            strategy["recommended_lead_time_days"] = 90
        if profile.risk_factors:
            strategy["notes"].extend(profile.risk_factors)
        return strategy