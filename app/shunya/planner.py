"""
Shunya — Planner Layer (Unit 4, v2)

Generates structured itineraries, proposal text, and HTML proposals.
Multi-format ready: supports text, HTML, and template-based output.
"""

from datetime import datetime, timedelta
from typing import Optional
from ._legacy_reasoning import CustomerProfile


class ItineraryDay:
    """A single day in an itinerary."""

    def __init__(self, day_num: int, title: str = ""):
        self.day_num = day_num
        self.title = title
        self.morning: str = ""
        self.afternoon: str = ""
        self.evening: str = ""
        self.accommodation: str = ""
        self.meals: list[str] = None
        self.transport: str = ""
        self.notes: list[str] = None

    def to_dict(self) -> dict:
        return {
            "day": self.day_num,
            "title": self.title,
            "morning": self.morning,
            "afternoon": self.afternoon,
            "evening": self.evening,
            "accommodation": self.accommodation,
            "meals": self.meals or [],
            "transport": self.transport,
            "notes": self.notes or [],
        }


class ItineraryPlan:
    """Complete itinerary plan with metadata."""

    def __init__(self, profile: CustomerProfile):
        self.profile = profile
        self.days: list[ItineraryDay] = []
        self.total_estimated_cost: float = 0.0
        self.currency: str = "INR"
        self.tax_notes: list[str] = []
        self.disclaimers: list[str] = []
        self.generated_at = datetime.utcnow()
        self.template_name: str = "standard"

    def add_day(self, day: ItineraryDay):
        self.days.append(day)

    def to_dict(self) -> dict:
        return {
            "customer": self.profile.customer_name,
            "destination": self.profile.destination,
            "pax": self.profile.pax,
            "dates": self.profile.dates,
            "occasion": self.profile.occasion,
            "group_type": self.profile.group_type,
            "template": self.template_name,
            "days": [d.to_dict() for d in self.days],
            "total_estimated_cost": self.total_estimated_cost,
            "currency": self.currency,
            "tax_notes": self.tax_notes,
            "disclaimers": self.disclaimers,
            "generated_at": self.generated_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Day templates for different occasions
# ---------------------------------------------------------------------------

_OCCASION_TEMPLATES = {
    "wedding": [
        ("Arrival & Check-in", "Airport pickup and transfer to resort", "Check-in, welcome drinks", "Welcome dinner at hotel restaurant"),
        ("Wedding Prep", "Wedding setup & decoration review", "Getting ready, pre-ceremony photos", "Wedding ceremony & reception dinner"),
        ("Post-Wedding Relax", "Leisure breakfast", "Couple photoshoot, spa", "Candlelight dinner on beach"),
        ("Departure", "Breakfast & check-out", "Airport drop-off", ""),
    ],
    "honeymoon": [
        ("Arrival & Romance", "Airport pickup to resort", "Check-in, welcome champagne", "Romantic dinner on the beach"),
        ("Explore & Indulge", "Breakfast in room", "Sightseeing or spa", "Sunset cruise with dinner"),
        ("Relax & Depart", "Leisure breakfast, checkout", "Last-minute shopping, airport", ""),
    ],
    "destination wedding": [
        ("Guest Arrivals", "Airport pickups, resort check-ins", "Welcome kit distribution", "Welcome dinner for all guests"),
        ("Pre-Wedding Events", "Mehendi/Haldi ceremony", "Sangeet or cocktail night", "Rehearsal dinner"),
        ("Wedding Day", "Wedding setup final review", "Ceremony & lunch reception", "Evening party / dinner"),
        ("Post-Wedding", "Thanksgiving brunch", "Couple departure / guest excursions", "Farewell dinner"),
    ],
    "family trip": [
        ("Arrival & Settle", "Airport pickup", "Check-in, kids' activities", "Family dinner"),
        ("Adventure Day", "Breakfast, excursion", "Sightseeing & activities", "Evening show or stroll"),
        ("Relax & Depart", "Breakfast and pool time", "Checkout & airport transfer", ""),
    ],
}


def _get_occasion_template(occasion: str, duration: int) -> list[tuple[str, str, str, str]]:
    """Get a day template for the given occasion, truncated/padded to duration."""
    for key in [occasion, "honeymoon", "family trip", "destination wedding"]:
        if key in _OCCASION_TEMPLATES:
            template = _OCCASION_TEMPLATES[key]
            # Pad or truncate to match duration
            if len(template) < duration:
                # Pad with generic days
                generic = ("Explore & Experience", "Breakfast", "Sightseeing/activities", "Dinner & leisure")
                template = template + [generic] * (duration - len(template))
            return template[:duration]
    # Default generic template
    return [
        ("Arrival & Welcome", "Airport pickup", "Check-in and orientation", "Welcome dinner"),
        *[("Explore Day", "Breakfast", "Sightseeing", "Dinner") for _ in range(duration - 2)],
        ("Departure", "Breakfast & checkout", "Airport transfer", ""),
    ]


class PlannerLayer:
    """Generates itineraries and proposals from reasoned customer profiles."""

    def __init__(self):
        pass

    def create_itinerary(self, profile: CustomerProfile, strategy: dict) -> ItineraryPlan:
        plan = ItineraryPlan(profile)
        duration = self._estimate_duration(profile.dates)
        if duration < 2:
            duration = 3

        # Select template based on occasion
        template = _get_occasion_template(profile.occasion, duration)
        if profile.occasion in ("wedding", "destination wedding"):
            plan.template_name = "wedding"
        elif profile.occasion == "honeymoon":
            plan.template_name = "romance"

        for i in range(duration):
            day = ItineraryDay(i + 1)
            if i < len(template):
                day.title = template[i][0]
                day.morning = template[i][1]
                day.afternoon = template[i][2]
                day.evening = template[i][3]
            day.meals = ["Breakfast"]
            if i < duration - 1:
                day.meals.append("Dinner")
            day.accommodation = strategy.get("venue_suggestions", [""])[0] if strategy.get("venue_suggestions") else ""
            day.transport = "Airport transfer included" if i in (0, duration - 1) else strategy.get("transport_notes", "Private vehicle")
            plan.add_day(day)

        # Cost estimate
        daily_budget = strategy.get("daily_budget_per_person", 5000)
        pax_count = 2  # default
        try:
            nums = [int(s) for s in str(profile.pax).split() if s.isdigit()]
            if nums:
                pax_count = nums[0]
        except (ValueError, AttributeError):
            pass
        plan.total_estimated_cost = daily_budget * duration * pax_count

        # Tax notes
        if strategy.get("tax_considerations"):
            plan.tax_notes = strategy["tax_considerations"]
        if strategy.get("currency"):
            plan.currency = strategy["currency"]

        plan.disclaimers = [
            "Prices are estimates and subject to change based on season and availability.",
            "Visa fees, travel insurance, and personal expenses not included.",
            "Final itinerary confirmed 30 days before travel.",
            "Airport transfers included unless specified otherwise.",
        ]

        return plan

    def generate_proposal_text(self, plan: ItineraryPlan) -> str:
        """Generate markdown proposal text."""
        lines = []
        lines.append(f"# Travel Proposal for {plan.profile.customer_name or 'Valued Guest'}")
        lines.append("---")
        lines.append(f"**Destination:** {plan.profile.destination}")
        lines.append(f"**Travelers:** {plan.profile.pax or 'TBD'}")
        lines.append(f"**Dates:** {plan.profile.dates or 'TBD'}")
        lines.append(f"**Occasion:** {plan.profile.occasion.replace('_', ' ').title()}")
        lines.append(f"**Group Type:** {plan.profile.group_type.title()}")
        lines.append("")
        lines.append("## Itinerary Overview")
        lines.append("")

        for day in plan.days:
            lines.append(f"### Day {day.day_num}: {day.title}")
            if day.morning:
                lines.append(f"- 🌅 **Morning:** {day.morning}")
            if day.afternoon:
                lines.append(f"- ☀️ **Afternoon:** {day.afternoon}")
            if day.evening:
                lines.append(f"- 🌙 **Evening:** {day.evening}")
            if day.accommodation:
                lines.append(f"- 🏨 **Stay:** {day.accommodation}")
            if day.meals:
                lines.append(f"- 🍽️ **Meals:** {', '.join(day.meals)}")
            if day.transport:
                lines.append(f"- 🚗 **Transport:** {day.transport}")
            lines.append("")

        lines.append(f"## Estimated Budget")
        lines.append(f"**{plan.currency} {plan.total_estimated_cost:,.0f}** (approx)")
        lines.append("")

        if plan.tax_notes:
            lines.append("## Tax & Fee Information")
            for note in plan.tax_notes:
                lines.append(f"- {note}")
            lines.append("")

        if plan.disclaimers:
            lines.append("## Terms & Disclaimers")
            for d in plan.disclaimers:
                lines.append(f"- {d}")

        return "\n".join(lines)

    def generate_proposal_html(self, plan: ItineraryPlan) -> str:
        """Generate HTML proposal for email or inline display."""
        days_html = ""
        for day in plan.days:
            items = ""
            if day.morning:
                items += f"<li><strong>Morning:</strong> {day.morning}</li>"
            if day.afternoon:
                items += f"<li><strong>Afternoon:</strong> {day.afternoon}</li>"
            if day.evening:
                items += f"<li><strong>Evening:</strong> {day.evening}</li>"
            if day.accommodation:
                items += f"<li><strong>Stay:</strong> {day.accommodation}</li>"
            if day.meals:
                items += f"<li><strong>Meals:</strong> {', '.join(day.meals)}</li>"
            if day.transport:
                items += f"<li><strong>Transport:</strong> {day.transport}</li>"
            days_html += f"""
            <div style="margin:12px 0;padding:12px;background:#f9fafb;border-radius:8px">
                <h4 style="margin:0 0 8px">Day {day.day_num}: {day.title}</h4>
                <ul style="margin:0;padding-left:20px">{items}</ul>
            </div>"""

        tax_html = ""
        if plan.tax_notes:
            tax_html = "<h3>Tax & Fees</h3><ul>" + "".join(f"<li>{n}</li>" for n in plan.tax_notes) + "</ul>"

        return f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>body{{font-family:Arial,sans-serif;color:#111;max-width:700px;margin:auto;padding:20px}}</style>
</head><body>
<h1 style="color:#2563eb">AI@shunyaos.com — Travel Proposal</h1>
<table style="width:100%;border-collapse:collapse;margin:12px 0">
<tr><td><strong>Destination</strong></td><td>{plan.profile.destination}</td></tr>
<tr><td><strong>Travelers</strong></td><td>{plan.profile.pax or 'TBD'}</td></tr>
<tr><td><strong>Dates</strong></td><td>{plan.profile.dates or 'TBD'}</td></tr>
<tr><td><strong>Occasion</strong></td><td>{plan.profile.occasion.replace('_',' ').title()}</td></tr>
</table>
<h2>Itinerary</h2>
{days_html}
<h2>Estimated Budget</h2>
<p><strong>{plan.currency} {plan.total_estimated_cost:,.0f}</strong></p>
{tax_html}
<h3>Terms</h3>
<ul>{"".join(f'<li>{d}</li>' for d in plan.disclaimers)}</ul>
<p style="color:#6b7280;font-size:12px;margin-top:24px">Generated by AI@shunyaos.com · SHUNYA OS</p>
</body></html>"""

    def generate_proposal_teach(self, plan: ItineraryPlan) -> str:
        """Generate a teach-the-user proposal that explains WHY, not just WHAT."""
        lines = []
        lines.append(f"# ✈️ Your {plan.profile.occasion.title()} Trip to {plan.profile.destination}")
        lines.append("")
        lines.append(f"**Hi {plan.profile.customer_name or 'there'}!** Here's your personalized travel plan.")
        lines.append("")
        lines.append("## 🎯 Why This Plan?")
        lines.append(f"- **Destination:** {plan.profile.destination} — selected because it matches your interest in a {plan.profile.occasion} trip")
        lines.append(f"- **Duration:** {len(plan.days)} days — optimized for your available dates")
        lines.append(f"- **Group:** {plan.profile.group_type.title()} travel — itinerary paced accordingly")
        lines.append(f"- **Budget:** Est. {plan.currency} {plan.total_estimated_cost:,.0f} — based on destination average costs")
        lines.append("")
        lines.append("## 📅 Your Day-by-Day Plan")
        lines.append("")
        for day in plan.days:
            lines.append(f"### Day {day.day_num}: {day.title}")
            if day.morning: lines.append(f"- 🌅 **Morning:** {day.morning}")
            if day.afternoon: lines.append(f"- ☀️ **Afternoon:** {day.afternoon}")
            if day.evening: lines.append(f"- 🌙 **Evening:** {day.evening}")
            if day.accommodation: lines.append(f"- 🏨 **Stay:** {day.accommodation}")
            lines.append("")
        lines.append("## 💡 What to Know")
        for note in plan.tax_notes:
            lines.append(f"- 💰 {note}")
        lines.append(f"- ✅ Best time: {plan.profile.destination_info.weather_notes[:120] if plan.profile.destination_info and plan.profile.destination_info.weather_notes else 'Check seasonal forecasts'}")
        lines.append("")
        lines.append("## 📋 Next Steps")
        lines.append("1. Review and confirm your travel dates")
        lines.append("2. We'll handle the bookings — flights, hotel, transfers")
        lines.append("3. Receive your final itinerary 2 weeks before departure")
        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by AI@shunyaos.com · I'm here to help you make better travel decisions*")
        return "\n".join(lines)

    def generate_proposal(self, plan: ItineraryPlan, fmt: str = "text") -> str:
        """Generate proposal in the requested format."""
        formats = {
            "text": self.generate_proposal_text,
            "markdown": self.generate_proposal_text,
            "html": self.generate_proposal_html,
        }
        generator = formats.get(fmt, formats["text"])
        return generator(plan)

    def _estimate_duration(self, dates_str: str) -> int:
        if not dates_str:
            return 3
        try:
            raw = dates_str.replace("to", "-").replace("till", "-").replace("–", "-").replace("—", "-")
            parts = [p.strip() for p in raw.split("-") if p.strip()]
            if len(parts) >= 2:
                # Try standard date formats first
                for fmt in ("%d %b %Y", "%d %B %Y", "%d %b", "%d %B",
                           "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                    try:
                        start = datetime.strptime(parts[0], fmt)
                        end = datetime.strptime(parts[-1], fmt)
                        return max(1, (end - start).days + 1)
                    except ValueError:
                        continue
                # Handle "10-14 Jan 2027" → start day=10, end day=14, month+year from last part
                if parts[0].isdigit() and len(parts) > 1:
                    end_parts = parts[-1].split()
                    if len(end_parts) >= 2:
                        start_str = f"{parts[0]} {' '.join(end_parts[1:])}".strip()
                        end_str = parts[-1].strip()
                        for fmt in ("%d %b %Y", "%d %B %Y", "%d %b", "%d %B"):
                            try:
                                start = datetime.strptime(start_str, fmt)
                                end = datetime.strptime(end_str, fmt)
                                return max(1, (end - start).days + 1)
                            except ValueError:
                                continue
        except Exception:
            pass
        return 3