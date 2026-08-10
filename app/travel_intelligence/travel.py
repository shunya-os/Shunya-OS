"""DCP-01A — Universal Journey Intelligence.

SHUNYA does not manage travel. SHUNYA understands and fulfils human journeys.
Vacations, business trips, relocations, education, medical travel, pilgrimages,
destination weddings, and enterprise travel are all different expressions of
the same Journey Intelligence. Industries specialize the capability.

Composed entirely from frozen platform runtimes. No new foundational architecture.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── Journey Types ────────────────────────────────────────────────
# Metadata differences. Not implementation differences.
# A Journey is a Journey. The type defines purpose, not execution.

JOURNEY_TYPES = {
    "family_holiday":    {"label": "Family Holiday",    "purpose": "Create shared memories",       "default_budget": 500000},
    "honeymoon":         {"label": "Honeymoon",         "purpose": "Celebrate a new beginning",    "default_budget": 350000},
    "solo_travel":       {"label": "Solo Travel",       "purpose": "Explore and discover yourself","default_budget": 200000},
    "corporate_travel":  {"label": "Corporate Travel",  "purpose": "Conduct business",             "default_budget": 1500000},
    "destination_wedding":{"label": "Destination Wedding","purpose": "Celebrate marriage",          "default_budget": 2000000},
    "medical_travel":    {"label": "Medical Travel",    "purpose": "Access healthcare",            "default_budget": 500000},
    "education_abroad":  {"label": "Education Abroad",  "purpose": "Study abroad",                 "default_budget": 800000},
    "pilgrimage":        {"label": "Pilgrimage",        "purpose": "Spiritual journey",            "default_budget": 150000},
    "conference":        {"label": "Conference",        "purpose": "Attend professional event",    "default_budget": 200000},
    "relocation":        {"label": "Relocation",        "purpose": "Move to a new city",           "default_budget": 1000000},
    "weekend_escape":    {"label": "Weekend Escape",    "purpose": "Quick recharge",               "default_budget": 100000},
    "business_meeting":  {"label": "Business Meeting",  "purpose": "Meet clients or partners",     "default_budget": 100000},
}


# ── Journey Living Object ────────────────────────────────────────
# A Journey is a Living Object. Travel artifacts are relationships.

@dataclass
class JourneyDay:
    day: int
    date: str
    location: str
    activities: list[str] = field(default_factory=list)
    accommodation: str = ""
    notes: str = ""


@dataclass
class Journey:
    journey_id: str
    title: str
    journey_type: str = "family_holiday"
    purpose: str = ""
    destination: str = ""
    start_date: str = ""
    end_date: str = ""
    participants: int = 2
    budget: float = 0.0
    status: str = "planning"
    itinerary: list[JourneyDay] = field(default_factory=list)
    documents: list[dict] = field(default_factory=list)
    creatives: list[dict] = field(default_factory=list)
    communications: list[dict] = field(default_factory=list)
    bookings: list[dict] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "journey_id": self.journey_id,
            "title": self.title,
            "journey_type": self.journey_type,
            "purpose": self.purpose,
            "destination": self.destination,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "participants": self.participants,
            "budget": self.budget,
            "status": self.status,
            "itinerary_days": len(self.itinerary),
            "documents": len(self.documents),
            "creatives": len(self.creatives),
            "communications": len(self.communications),
            "bookings": len(self.bookings),
            "risks": self.risks,
            "recommendations": self.recommendations,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Journey Intelligence ─────────────────────────────────────────
# Composes existing runtimes. Does not introduce new runtime architecture.

class JourneyIntelligence:
    """Universal Journey Intelligence.
    
    Composes: Composer, Document, Creative, Communication, Execution, Reality, Cognition.
    No new runtimes. A Journey is composed from Living Objects.
    """

    def __init__(self):
        self._journeys: dict[str, Journey] = {}

    # ── Journey Planning ──

    def plan_journey(self, title: str, destination: str, start_date: str, end_date: str,
                     journey_type: str = "family_holiday", participants: int = 2,
                     budget: float = 0.0) -> Journey:
        type_info = JOURNEY_TYPES.get(journey_type, JOURNEY_TYPES["family_holiday"])
        now = datetime.now(timezone.utc).isoformat()
        journey = Journey(
            journey_id=f"jny_{uuid.uuid4().hex[:12]}",
            title=title,
            journey_type=journey_type,
            purpose=type_info["purpose"],
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            participants=participants,
            budget=budget or type_info["default_budget"],
            created_at=now,
            updated_at=now,
        )
        # Generate itinerary
        dates = self._parse_date_range(start_date, end_date)
        for i, d in enumerate(dates, 1):
            journey.itinerary.append(JourneyDay(
                day=i, date=d, location=destination,
                activities=self._suggest_activities(destination, journey_type, i),
            ))
        self._journeys[journey.journey_id] = journey
        self._compose(journey)
        self._emit_reality(journey, "journey_planned")
        return journey

    def get_journey(self, journey_id: str) -> Optional[Journey]:
        return self._journeys.get(journey_id)

    def list_journeys(self, journey_type: Optional[str] = None, status: Optional[str] = None) -> list[Journey]:
        journeys = list(self._journeys.values())
        if journey_type:
            journeys = [j for j in journeys if j.journey_type == journey_type]
        if status:
            journeys = [j for j in journeys if j.status == status]
        journeys.sort(key=lambda j: j.updated_at, reverse=True)
        return journeys

    # ── Runtime Composition ──

    def _compose(self, journey: Journey) -> None:
        self._compose_objects(journey)
        self._compose_documents(journey)
        self._compose_creatives(journey)
        self._compose_execution(journey)

    def _compose_objects(self, journey: Journey) -> None:
        try:
            from app.objects.service import ObjectService
            for day in journey.itinerary:
                ObjectService.create_object(
                    object_type="event",
                    state={"title": f"Day {day.day}: {day.location}", "intent": "travel"}
                )
        except Exception:
            pass

    def _compose_documents(self, journey: Journey) -> None:
        try:
            from app.document_runtime.runtime import get_document_runtime
            rt = get_document_runtime()
            itinerary_text = self._build_itinerary_text(journey)
            rt.create_document(title=f"{journey.title} — Itinerary", content=itinerary_text,
                               doc_type="itinerary", purpose=journey.purpose)
            rt.create_document(title=f"{journey.title} — Proposal", content=f"Journey proposal for {journey.destination}",
                               doc_type="proposal", purpose=journey.purpose)
            rt.create_document(title=f"{journey.title} — Quotation", content=f"Budget: {journey.budget}",
                               doc_type="document", purpose="Price quotation")
            rt.create_document(title=f"{journey.title} — Invoice", content=f"Final invoice for {journey.destination}",
                               doc_type="invoice", purpose="Request payment")
            journey.documents = [{"type": "itinerary"}, {"type": "proposal"}, {"type": "quotation"}, {"type": "invoice"}]
        except Exception:
            pass

    def _compose_creatives(self, journey: Journey) -> None:
        try:
            from app.creative_runtime.runtime import get_creative_runtime
            rt = get_creative_runtime()
            assets = rt.generate_representations(title=journey.title, intent="explain")
            journey.creatives = [{"asset_id": a.asset_id, "title": a.title, "creative_type": a.creative_type} for a in assets]
        except Exception:
            pass

    def _compose_execution(self, journey: Journey) -> None:
        try:
            from app.execution.runtime import get_execution_runtime
            rt = get_execution_runtime()
            ex = rt.create_execution(title=f"Journey: {journey.title}", intent="travel",
                                      goal=journey.purpose, completion_criteria="Journey completed")
            ex.transition("Planned")
            journey.documents.append({"type": "execution", "execution_id": ex.execution_id, "title": ex.title})
        except Exception:
            pass

    # ── Universal Journey Intelligence ──

    def recommend_destinations(self, journey_type: str, budget: float = 0,
                                participants: int = 2, duration_days: int = 5) -> list[dict]:
        """Recommend destinations based on journey type, budget, and group."""
        recommendations = {
            "family_holiday": [
                {"destination": "Sri Lanka", "reason": "Safe, affordable, diverse activities for all ages",
                 "estimated_cost": 15000 * duration_days * participants},
                {"destination": "Bali", "reason": "Beach, culture, and kid-friendly resorts",
                 "estimated_cost": 20000 * duration_days * participants},
                {"destination": "Singapore", "reason": "Clean, efficient, and family-friendly attractions",
                 "estimated_cost": 25000 * duration_days * participants},
            ],
            "honeymoon": [
                {"destination": "Bali", "reason": "Romantic villas, sunset views, and private experiences",
                 "estimated_cost": 20000 * duration_days * participants},
                {"destination": "Maldives", "reason": "Ultimate privacy and overwater luxury",
                 "estimated_cost": 35000 * duration_days * participants},
                {"destination": "Santorini", "reason": "Iconic sunsets and intimate ambiance",
                 "estimated_cost": 40000 * duration_days * participants},
            ],
            "solo_travel": [
                {"destination": "Thailand", "reason": "Budget-friendly, social hostels, and solo-friendly culture",
                 "estimated_cost": 8000 * duration_days * participants},
                {"destination": "Vietnam", "reason": "Affordable, safe, and rich in adventure",
                 "estimated_cost": 7000 * duration_days * participants},
                {"destination": "Portugal", "reason": "Welcoming, walkable cities, and vibrant hostels",
                 "estimated_cost": 15000 * duration_days * participants},
            ],
            "corporate_travel": [
                {"destination": "Dubai", "reason": "Business hub, excellent infrastructure, and networking",
                 "estimated_cost": 30000 * duration_days * participants},
                {"destination": "Singapore", "reason": "Efficient, safe, and Asia-Pacific business hub",
                 "estimated_cost": 25000 * duration_days * participants},
                {"destination": "London", "reason": "Global business center with diverse industry connections",
                 "estimated_cost": 35000 * duration_days * participants},
            ],
            "destination_wedding": [
                {"destination": "Bali", "reason": "World-class wedding venues with stunning backdrops",
                 "estimated_cost": 50000 * duration_days * participants},
                {"destination": "Udaipur", "reason": "Royal palaces and fairy-tale wedding settings",
                 "estimated_cost": 30000 * duration_days * participants},
                {"destination": "Tuscany", "reason": "Vineyard estates and timeless romance",
                 "estimated_cost": 60000 * duration_days * participants},
            ],
            "medical_travel": [
                {"destination": "Chennai", "reason": "World-class hospitals at affordable rates",
                 "estimated_cost": 10000 * duration_days * participants},
                {"destination": "Bangkok", "reason": "JCI-accredited hospitals with international standards",
                 "estimated_cost": 12000 * duration_days * participants},
                {"destination": "Singapore", "reason": "Top-tier medical facilities and English-speaking staff",
                 "estimated_cost": 25000 * duration_days * participants},
            ],
            "education_abroad": [
                {"destination": "Canada", "reason": "High-quality education and welcoming immigration policies",
                 "estimated_cost": 30000 * duration_days * participants},
                {"destination": "Australia", "reason": "Top universities and excellent student support",
                 "estimated_cost": 35000 * duration_days * participants},
                {"destination": "Germany", "reason": "Low or no tuition fees for international students",
                 "estimated_cost": 15000 * duration_days * participants},
            ],
            "pilgrimage": [
                {"destination": "Varanasi", "reason": "Most sacred city for spiritual seekers",
                 "estimated_cost": 5000 * duration_days * participants},
                {"destination": "Jerusalem", "reason": "Sacred destination for multiple faiths",
                 "estimated_cost": 20000 * duration_days * participants},
                {"destination": "Mecca", "reason": "The holiest city in Islam",
                 "estimated_cost": 25000 * duration_days * participants},
            ],
        }
        return recommendations.get(journey_type, recommendations["family_holiday"])

    def optimize_journey(self, journey_id: str) -> Optional[dict]:
        """Analyze and recommend improvements for a journey."""
        journey = self._journeys.get(journey_id)
        if not journey:
            return None

        optimizations = []
        type_info = JOURNEY_TYPES.get(journey.journey_type, {})

        # Budget optimization
        estimated = self._estimate_journey_cost(journey)
        if estimated > journey.budget:
            optimizations.append(f"Estimated cost (₹{estimated:,.0f}) exceeds budget (₹{journey.budget:,.0f}) — reduce duration or upgrade budget")
        elif estimated < journey.budget * 0.6:
            optimizations.append(f"Budget (₹{journey.budget:,.0f}) is well above estimate (₹{estimated:,.0f}) — consider premium experiences")

        # Duration suitability
        days = len(journey.itinerary)
        if days < 3 and journey.journey_type in ("family_holiday", "honeymoon"):
            optimizations.append(f"Short duration ({days} days) — consider extending for a more relaxed pace")
        elif days > 10 and journey.journey_type == "conference":
            optimizations.append(f"Long duration ({days} days) — consider splitting into work + leisure")

        # Participant suitability
        if journey.participants > 4 and journey.journey_type == "solo_travel":
            optimizations.append("Solo travel with multiple participants — consider private tour instead")
        if journey.participants == 1 and journey.journey_type == "family_holiday":
            optimizations.append("Family holiday with one participant — verify journey type")

        # Season timing
        season = self._get_season(journey.destination, journey.start_date)
        if season:
            optimizations.append(season)

        journey.recommendations = optimizations
        return {"journey_id": journey_id, "optimizations": optimizations}

    def analyze_journey(self, journey_id: str) -> dict:
        """Analyze journey for risks, missing documents, and recommendations."""
        journey = self._journeys.get(journey_id)
        if not journey:
            return {"error": "Journey not found"}

        risks = []
        recommendations = []

        # Document checks
        doc_types = {d.get("type", "") for d in journey.documents}
        required = ["itinerary", "proposal", "quotation", "invoice"]
        missing = [d for d in required if d not in doc_types]
        if missing:
            risks.append(f"Missing documents: {', '.join(missing)}")
            recommendations.append(f"Generate: {', '.join(missing)}")

        # Journey-type-specific checks
        if journey.journey_type == "medical_travel":
            recommendations.append("Verify medical records and hospital appointments")
            recommendations.append("Check travel insurance covers medical procedures")
            risks.append("Medical documentation required for treatment")
        elif journey.journey_type == "education_abroad":
            recommendations.append("Verify student visa processing times")
            recommendations.append("Check university acceptance and accommodation")
            risks.append("Visa and admission documentation critical")
        elif journey.journey_type == "pilgrimage":
            recommendations.append("Check religious visa requirements")
            recommendations.append("Verify vaccination and health requirements")
        elif journey.journey_type == "destination_wedding":
            recommendations.append("Verify marriage license requirements")
            recommendations.append("Check legal documentation for destination wedding")
            risks.append("Legal marriage documentation may require additional processing")

        # Universal checks
        recommendations.append("Verify passport validity for all participants")
        recommendations.append("Consider travel insurance")

        # Budget
        estimated = self._estimate_journey_cost(journey)
        if estimated > journey.budget:
            risks.append(f"Estimated cost (₹{estimated:,.0f}) exceeds budget (₹{journey.budget:,.0f})")

        journey.risks = risks
        journey.recommendations = recommendations
        return {
            "journey_id": journey_id,
            "title": journey.title,
            "type": journey.journey_type,
            "risks": risks,
            "recommendations": recommendations,
            "budget_status": "over budget" if estimated > journey.budget else "within budget",
        }

    def generate_proposal(self, journey_id: str) -> Optional[str]:
        journey = self._journeys.get(journey_id)
        if not journey:
            return None
        type_info = JOURNEY_TYPES.get(journey.journey_type, {})
        return (
            f"# {journey.title} — Journey Proposal\n\n"
            f"**Type:** {type_info.get('label', 'Journey')}\n"
            f"**Purpose:** {journey.purpose}\n"
            f"**Destination:** {journey.destination}\n"
            f"**Dates:** {journey.start_date} to {journey.end_date}\n"
            f"**Participants:** {journey.participants}\n"
            f"**Budget:** ₹{journey.budget:,.0f}\n\n"
            f"## Itinerary\n\n"
            + "\n".join(f"**Day {d.day} ({d.date}):** {d.location}\n- " + "\n- ".join(d.activities)
                        for d in journey.itinerary) +
            "\n\n**Estimated Cost:** ₹{:,}\n".format(self._estimate_journey_cost(journey))
        )

    # ── Disruption Handling ──

    def handle_disruption(self, journey_id: str, disruption_type: str,
                          details: dict | None = None) -> dict:
        journey = self._journeys.get(journey_id)
        if not journey:
            return {"error": "Journey not found"}
        journey.status = "disrupted"
        actions = []
        details = details or {}

        if disruption_type == "flight_cancelled":
            for day in journey.itinerary[1:]:
                day.activities = ["Rescheduled — disruption recovery"] + day.activities
            actions.extend(["Flight cancelled — rebooked", "Itinerary adjusted", "Accommodation notified"])
        elif disruption_type == "weather":
            day_num = details.get("day", 1)
            for day in journey.itinerary:
                if day.day == day_num:
                    day.activities = ["Indoor activities", "Local experiences", "Flexible schedule"]
            actions.append(f"Weather disruption on Day {day_num} — indoor alternatives arranged")
        elif disruption_type == "health_emergency":
            actions.append("Medical assistance arranged")
            actions.append("Travel insurance notified")
            actions.append("Family notified")
        elif disruption_type == "visa_issue":
            actions.append("Visa processing delay — contingency plan activated")
            actions.append("Embassy contacted for expedited processing")

        # Adaptive execution
        try:
            from app.execution.runtime import get_execution_runtime
            rt = get_execution_runtime()
            for d in journey.documents:
                if d.get("type") == "execution":
                    rt.adapt(d.get("execution_id"), {"type": disruption_type, **details})
                    actions.append("Execution adapted to reality change")
        except Exception:
            pass

        journey.risks.append(f"Disruption: {disruption_type}")
        self._emit_reality(journey, f"disruption_{disruption_type}")
        return {"journey_id": journey_id, "disruption": disruption_type, "actions": actions}

    def generate_communication(self, journey_id: str, comm_type: str = "hotel") -> str:
        journey = self._journeys.get(journey_id)
        if not journey:
            return ""
        if comm_type == "hotel":
            return (f"Subject: Booking Inquiry — {journey.title}\n\n"
                    f"Inquiry for {journey.participants} guests at {journey.destination} "
                    f"from {journey.start_date} to {journey.end_date}.\n\n"
                    f"Please provide availability, rates, and cancellation policy.\n\nBest regards,\nSHUNYA")
        elif comm_type == "airline":
            return (f"Subject: Group Booking Request — {journey.title}\n\n"
                    f"Requesting group fare for {journey.participants} passengers "
                    f"to {journey.destination} departing {journey.start_date}.\n\nThank you.")
        return ""

    # ── Helpers ──

    def _parse_date_range(self, start: str, end: str) -> list[str]:
        try:
            s = datetime.strptime(start, "%Y-%m-%d").date()
            e = datetime.strptime(end, "%Y-%m-%d").date()
            dates = []
            current = s
            while current <= e:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
            return dates
        except Exception:
            return [start, end]

    def _suggest_activities(self, destination: str, journey_type: str, day: int) -> list[str]:
        dest_lower = destination.lower()
        dest_activities = {
            "sri lanka": [
                ["Colombo city tour", "Gangaramaya Temple", "Galle Face Green"],
                ["Sigiriya Rock Fortress", "Dambulla Cave Temple"],
                ["Kandy — Temple of the Tooth", "Cultural dance performance"],
                ["Nuwara Eliya tea plantation", "Train ride through hills"],
                ["Galle Fort walking tour", "Unawatuna beach"],
                ["Bentota river safari", "Turtle hatchery"],
                ["Departure"],
            ],
            "bali": [
                ["Seminyak beach sunset", "Welcome dinner"],
                ["Ubud monkey forest", "Tegallalang rice terraces"],
                ["Uluwatu temple", "Kecak fire dance"],
                ["Nusa Penida day trip", "Snorkeling"],
                ["Waterbom Bali", "Spa and wellness"],
                ["Tanah Lot temple", "Departure"],
            ],
            "maldives": [
                ["Speedboat transfer", "Sunset dolphin cruise"],
                ["Snorkeling", "Private beach dinner"],
                ["Scuba diving", "Sandbank picnic"],
                ["Water sports", "Sunset fishing"],
                ["Spa day", "Overwater villa"],
                ["Departure"],
            ],
            "dubai": [
                ["Burj Khalifa", "Dubai Mall"],
                ["Desert safari", "BBQ dinner"],
                ["Dubai Marina", "Palm Jumeirah"],
                ["Gold Souk", "Abra ride"],
                ["Museum of the Future", "Global Village"],
                ["Departure"],
            ],
        }
        default = [
            ["Arrival", "Welcome"], ["City tour", "Local cuisine"], ["Excursion", "Exploration"],
            ["Outdoor adventure", "Sunset"], ["Spa", "Farewell dinner"], ["Departure"],
        ]
        ad = dest_activities.get(dest_lower, default)
        if day <= len(ad):
            return ad[day - 1]
        # Journey-type-specific additions
        type_extras = {
            "destination_wedding": ["Wedding venue inspection", "Catering tasting", "Photography walkthrough", "Guest accommodation check"],
            "medical_travel": ["Hospital consultation", "Pre-op assessment", "Pharmacy visit", "Follow-up appointment"],
            "education_abroad": ["University campus tour", "Student accommodation viewing", "Local bank account setup", "SIM card purchase"],
        }
        extras = type_extras.get(journey_type, ["Free time", "Optional activities"])
        idx = (day - len(ad) - 1) % len(extras)
        return [extras[idx]]

    def _estimate_journey_cost(self, journey: Journey) -> float:
        base = {"sri lanka": 15000, "bali": 20000, "maldives": 35000, "dubai": 30000}
        days = 5
        if journey.start_date and journey.end_date:
            try:
                s = datetime.strptime(journey.start_date, "%Y-%m-%d")
                e = datetime.strptime(journey.end_date, "%Y-%m-%d")
                days = max(1, (e - s).days)
            except Exception:
                days = 5
        rate = 0
        for k, v in base.items():
            if k in journey.destination.lower():
                rate = v
                break
        if rate == 0:
            rate = 20000
        return rate * days * journey.participants

    def _get_season(self, destination: str, date_str: str) -> Optional[str]:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            month = dt.month
            dest_lower = destination.lower()
            seasons = {
                "sri lanka": ("Peak season (Dec–Mar)" if month in (12, 1, 2, 3)
                              else "Shoulder season" if month in (4, 11) else "Off-peak — better rates"),
                "bali": ("Dry season (Apr–Oct) — ideal" if month in (4, 5, 6, 7, 8, 9, 10)
                         else "Wet season — fewer crowds, lower rates"),
                "maldives": ("Peak season (Nov–Apr)" if month in (11, 12, 1, 2, 3, 4)
                             else "Off-peak — better value"),
            }
            return seasons.get(dest_lower, None)
        except Exception:
            return None

    def _build_itinerary_text(self, journey: Journey) -> str:
        lines = [f"# {journey.title} — Itinerary",
                 f"**Type:** {JOURNEY_TYPES.get(journey.journey_type, {}).get('label', 'Journey')}",
                 f"**Destination:** {journey.destination}",
                 f"**Dates:** {journey.start_date} to {journey.end_date}",
                 f"**Participants:** {journey.participants}", ""]
        for day in journey.itinerary:
            lines.append(f"## Day {day.day} — {day.date}")
            lines.append(f"**Location:** {day.location}")
            for a in day.activities:
                lines.append(f"- {a}")
            lines.append("")
        return "\n".join(lines)

    def _emit_reality(self, journey: Journey, event_type: str):
        try:
            from app.reality_engine.engine import get_reality_engine
            get_reality_engine().notify({"type": event_type, "identity_id": "system",
                "journey_id": journey.journey_id, "title": journey.title,
                "journey_type": journey.journey_type, "status": journey.status})
        except Exception:
            pass


# ── Singleton ────────────────────────────────────────────────────

_INSTANCE: Optional[JourneyIntelligence] = None

def get_journey_intelligence() -> JourneyIntelligence:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = JourneyIntelligence()
    return _INSTANCE

# Backward compatibility alias
get_travel_intelligence = get_journey_intelligence