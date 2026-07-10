"""
Planner Layer (Shunya)
Turns reasoned customer profiles into executable itineraries and proposals.
Supports multi-format output: PDF, infographic, short clip, email body.
"""

from datetime import datetime, timedelta
from typing import Optional
from .reasoning import CustomerProfile


class ItineraryDay:
    """A single day in an itinerary."""
    def __init__(self, day_num: int, title: str = ""):
        self.day_num = day_num
        self.title = title
        self.morning: str = ""
        self.afternoon: str = ""
        self.evening: str = ""
        self.accommodation: str = ""
        self.meals: list[str] = []
        self.transport: str = ""
        self.notes: list[str] = []


class ItineraryPlan:
    """Complete itinerary plan."""
    def __init__(self, profile: CustomerProfile):
        self.profile = profile
        self.days: list[ItineraryDay] = []
        self.total_estimated_cost: float = 0.0
        self.currency: str = "INR"
        self.tax_notes: list[str] = []
        self.disclaimers: list[str] = []
        self.generated_at = datetime.utcnow()

    def add_day(self, day: ItineraryDay):
        self.days.append(day)

    def to_dict(self) -> dict:
        return {
            "customer": self.profile.customer_name,
            "destination": self.profile.destination,
            "pax": self.profile.pax,
            "dates": self.profile.dates,
            "days": [
                {
                    "day": d.day_num,
                    "title": d.title,
                    "morning": d.morning,
                    "afternoon": d.afternoon,
                    "evening": d.evening,
                    "accommodation": d.accommodation,
                    "meals": d.meals,
                    "transport": d.transport,
                    "notes": d.notes,
                }
                for d in self.days
            ],
            "total_estimated_cost": self.total_estimated_cost,
            "currency": self.currency,
            "tax_notes": self.tax_notes,
            "disclaimers": self.disclaimers,
            "generated_at": self.generated_at.isoformat(),
        }


class PlannerLayer:
    """
    Generates itineraries and proposals from reasoned customer profiles.
    Produces structured data that the Workflow layer can deliver in any format.
    """

    def __init__(self):
        pass

    def create_itinerary(self, profile: CustomerProfile, strategy: dict) -> ItineraryPlan:
        """Create a structured itinerary plan from a customer profile and strategy."""
        plan = ItineraryPlan(profile)

        # Estimate duration from dates string
        duration = self._estimate_duration(profile.dates)
        if duration < 2:
            duration = 3  # minimum reasonable trip

        for i in range(duration):
            day = ItineraryDay(i + 1)
            if i == 0:
                day.title = "Arrival & Welcome"
                day.transport = "Airport pickup arranged"
            elif i == duration - 1:
                day.title = "Departure"
                day.morning = "Breakfast & Check-out"
                day.transport = "Airport drop-off arranged"
            else:
                day.title = f"Day {i + 1} - Explore {profile.destination}"
            day.meals = ["Breakfast"]
            plan.add_day(day)

        # Tax considerations
        if strategy.get("tax_considerations"):
            plan.tax_notes = strategy["tax_considerations"]

        plan.disclaimers = [
            "Prices are estimates and subject to change",
            "Visa fees and travel insurance not included",
            "Final itinerary confirmed 30 days before travel",
        ]

        return plan

    def generate_proposal_text(self, plan: ItineraryPlan) -> str:
        """Generate the proposal body text from a plan."""
        lines = []
        lines.append(f"# Travel Proposal for {plan.profile.customer_name}")
        lines.append(f"**Destination:** {plan.profile.destination}")
        lines.append(f"**Travelers:** {plan.profile.pax}")
        lines.append(f"**Dates:** {plan.profile.dates}")
        lines.append("")
        lines.append("## Itinerary Overview")
        lines.append("")

        for day in plan.days:
            lines.append(f"### Day {day.day_num}: {day.title}")
            if day.morning:
                lines.append(f"- **Morning:** {day.morning}")
            if day.afternoon:
                lines.append(f"- **Afternoon:** {day.afternoon}")
            if day.evening:
                lines.append(f"- **Evening:** {day.evening}")
            if day.accommodation:
                lines.append(f"- **Stay:** {day.accommodation}")
            if day.meals:
                lines.append(f"- **Meals:** {', '.join(day.meals)}")
            if day.transport:
                lines.append(f"- **Transport:** {day.transport}")
            lines.append("")

        if plan.tax_notes:
            lines.append("## Tax Information")
            for note in plan.tax_notes:
                lines.append(f"- {note}")
            lines.append("")

        if plan.disclaimers:
            lines.append("## Terms & Disclaimers")
            for d in plan.disclaimers:
                lines.append(f"- {d}")

        return "\n".join(lines)

    def _estimate_duration(self, dates_str: str) -> int:
        """Rough duration estimate from date string."""
        if not dates_str:
            return 3
        try:
            parts = dates_str.lower().replace("to", "-").replace("till", "-").replace("–", "-").replace("—", "-").split("-")
            if len(parts) >= 2:
                from datetime import datetime as dt
                fmt = "%d %B %Y" if "20" in parts[0] else "%d %B"
                try:
                    start = dt.strptime(parts[0].strip(), "%d %B %Y")
                    end = dt.strptime(parts[-1].strip(), "%d %B %Y")
                    return max(1, (end - start).days + 1)
                except ValueError:
                    pass
        except Exception:
            pass
        return 3