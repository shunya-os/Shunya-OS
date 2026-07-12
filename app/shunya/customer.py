"""Shunya Customer Module — Relationship Intelligence & Briefing.

The Customer is the unit of compounding relationship intelligence.
This module generates AI-powered Relationship Briefs so every employee
feels "I know this customer" even if they have never spoken to them before.
"""
from datetime import datetime, date
from collections import defaultdict
from typing import Optional, List, Dict, Any
from app import db
from app.models import Customer, CustomerPreference, Opportunity, OpportunityActivity


class RelationshipBrief:
    """Generates the AI-powered relationship briefing for a customer.

    The brief restores relationship context so the employee understands
    who they're speaking to, what matters, and what to do next.
    """

    def __init__(self, customer: Customer):
        self.customer = customer
        self._preferences: List[CustomerPreference] = []
        self._opportunities: List[Opportunity] = []
        self._activity: List[OpportunityActivity] = []
        self._load()

    def _load(self):
        """Load all related data for this customer."""
        self._preferences = db.session.query(CustomerPreference).filter(
            CustomerPreference.customer_id == self.customer.id,
            CustomerPreference.is_active == True,
        ).order_by(CustomerPreference.confidence.desc()).all()

        self._opportunities = db.session.query(Opportunity).filter(
            Opportunity.customer_id == self.customer.id,
            Opportunity.status == "open",
        ).order_by(Opportunity.created_at.desc()).all()

        completed = db.session.query(Opportunity).filter(
            Opportunity.customer_id == self.customer.id,
            Opportunity.stage.in_(["outcome", "closed", "lost"]),
        ).order_by(Opportunity.updated_at.desc()).limit(1).all()

        # Load last few activities across all opportunities
        opp_ids = [o.id for o in self._opportunities] + [o.id for o in completed]
        if opp_ids:
            self._activity = db.session.query(OpportunityActivity).filter(
                OpportunityActivity.opportunity_id.in_(opp_ids),
            ).order_by(OpportunityActivity.created_at.desc()).limit(20).all()

        self._last_completed = completed[0] if completed else None

    # ------------------------------------------------------------------
    # Brief Sections
    # ------------------------------------------------------------------

    def get_relationship_header(self) -> Dict[str, Any]:
        """The top-level relationship summary."""
        c = self.customer
        return {
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "relationship_tenure_years": c.relationship_tenure_years,
            "relationship_health": c.relationship_health,
            "relationship_health_label": self._health_label(c.relationship_health),
            "total_experiences": c.total_experiences,
            "total_referrals": c.total_referrals,
            "preferred_channel": c.preferred_channel,
            "communication_style": c.communication_style or "unknown",
            "last_meaningful_interaction": c.last_meaningful_interaction.isoformat()
                if c.last_meaningful_interaction else None,
            "advisor_id": c.relationship_advisor_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }

    def get_preferences(self) -> List[Dict[str, Any]]:
        """Preferences with evidence, ready for display."""
        results = []
        for p in self._preferences:
            results.append(p.to_dict())
        return results

    def get_preferences_brief(self) -> List[str]:
        """Human-readable bullet points for the 'Before You Speak' section."""
        bullets = []
        pref_map = defaultdict(list)
        for p in self._preferences:
            pref_map[p.preference_type].append(p)

        # Travel pace
        if "travel_pace" in pref_map:
            p = pref_map["travel_pace"][0]
            bullets.append(f"Prefers {p.value} travel pace (confidence: {p.confidence})")

        # Hotel location
        if "hotel_location" in pref_map:
            p = pref_map["hotel_location"][0]
            val_labels = {"central_walkable": "central / walkable locations"}
            label = val_labels.get(p.value.split(",")[0], p.value.replace("_", " "))
            if p.confidence == "high":
                bullets.append(f"Prefers {label} — observed in {len(p.evidence)} trips")
            else:
                bullets.append(f"May prefer {label} (limited data)")

        # Budget range
        if "budget_range" in pref_map:
            p = pref_map["budget_range"][0]
            bullets.append(f"Budget range: {p.value}")

        # Communication
        if "communication_style" in pref_map:
            p = pref_map["communication_style"][0]
            bullets.append(f"Communication style: {p.value}")

        # Decision style
        if "decision_style" in pref_map:
            p = pref_map["decision_style"][0]
            style_labels = {
                "quick_decision": "Decides quickly with clear comparisons",
                "needs_time": "Takes time to decide — prefers 2-3 strong options",
                "consults_family": "Consults family before deciding",
            }
            bullets.append(style_labels.get(p.value, p.value.replace("_", " ")))

        # Airline preference
        if "airline" in pref_map:
            p = pref_map["airline"][0]
            bullets.append(f"Airline preference: {p.value}")

        # Room category
        if "room_category" in pref_map:
            p = pref_map["room_category"][0]
            bullets.append(f"Room preference: {p.value}")

        # Transfer preference
        if "transfer_preference" in pref_map:
            p = pref_map["transfer_preference"][0]
            bullets.append(f"Transfer preference: {p.value}")

        return bullets

    def get_one_thing_to_remember(self) -> Optional[str]:
        """The single most important thing the advisor should know."""
        # Priority: recent issues > last trip feedback > strong preference contradiction
        if self._last_completed:
            issues = self._last_completed.outcome_notes
            if issues and any(w in issues.lower() for w in ["delay", "issue", "problem", "complaint", "transfer"]):
                detail = issues[:200]
                return f"Last trip ({self._last_completed.title}) had: {detail}"

        # Check for issues mentioned in activity
        for a in self._activity:
            if a.activity_type == "experience_issue":
                return f"Issue noted during {a.title}: {a.description[:150]}"

        # Check for transfer-related preference
        for p in self._preferences:
            if p.preference_type == "transfer_preference" and p.confidence == "high":
                return f"Confirm transfer logistics before recommending flight timing (last trip had transfer feedback)"

        # Check for a notable contradiction
        for p in self._preferences:
            if p.contradictions:
                return f"{p.preference_type.replace('_', ' ').title()} choice varied once — confirm current preference"

        # Fallback: longest-tenure preference
        if self._preferences:
            p = self._preferences[-1]  # oldest
            return f"Observed: {p.value.replace('_', ' ')} ({p.preference_type.replace('_', ' ')}) — confirmed {p.last_confirmed.strftime('%b %Y') if p.last_confirmed else 'not yet confirmed'}"

        return None

    def get_active_opportunities(self) -> List[Dict[str, Any]]:
        """Current opportunities in play."""
        return [o.to_dict() for o in self._opportunities]

    def get_suggested_next_action(self) -> Optional[Dict[str, Any]]:
        """Recommend the next action based on customer state."""
        active = [o for o in self._opportunities if o.stage not in ("closed", "lost", "outcome")]

        if not active:
            # No active opportunities — suggest re-engagement
            days_since = None
            if self.customer.last_meaningful_interaction:
                delta = datetime.utcnow() - self.customer.last_meaningful_interaction
                days_since = delta.days

            if days_since and days_since > 90:
                return {
                    "action": "Re-engage customer",
                    "reason": f"No interaction in {days_since} days. Previous customer with {self.customer.total_experiences} experiences.",
                    "expected_impact": "Retention and potential new opportunity",
                }
            return None

        # Prioritize opportunities by stage
        stage_priority = {"enquiry": 0, "discovery": 1, "planning": 2,
                          "proposal": 3, "negotiation": 4, "booking": 5}
        active.sort(key=lambda o: stage_priority.get(o.stage, 99))

        o = active[0]

        if o.stage == "enquiry":
            return {
                "action": f"Have discovery conversation about {o.title or o.destination or 'their interest'}",
                "reason": "Understanding intent before building itinerary prevents rework",
                "expected_impact": "Faster qualification and more accurate proposal",
                "suggested_opening": f"Before I start hotels — are you imagining {o.destination or 'this trip'} as an active exploring trip or a relaxed holiday this time?",
            }

        if o.stage == "discovery" or o.stage == "planning":
            return {
                "action": f"Build and share proposal for {o.title or o.destination}",
                "reason": "Discovery phase complete — ready for proposal",
                "expected_impact": "Move toward booking conversation",
            }

        if o.stage == "proposal":
            # Check if we have previous decision patterns
            for p in self._preferences:
                if p.preference_type == "decision_style" and p.value == "needs_time":
                    return {
                        "action": f"Follow up on {o.title} proposal — customer takes time to decide",
                        "reason": "Previous behaviour shows they prefer 2-3 strong options and time to compare",
                        "expected_impact": "Patient follow-up increases conversion for this profile",
                        "suggested_opening": "No rush — I wanted to check if you had any questions about the options I shared.",
                    }

            # Default proposal follow-up
            days_since = (datetime.utcnow() - o.created_at).days if o.created_at else 0
            return {
                "action": f"Follow up on {o.title} proposal (sent {days_since} days ago)",
                "reason": "Proposal pending — timely follow-up increases conversion",
                "expected_impact": "Move toward booking or understand objections",
            }

        if o.stage == "negotiation":
            return {
                "action": f"Address open items on {o.title} negotiation",
                "reason": "Customer is actively negotiating — responsiveness matters most now",
                "expected_impact": "Close the deal",
            }

        if o.stage == "booking":
            return {
                "action": f"Confirm booking details for {o.title}",
                "reason": "Booking stage — ensure all confirmations are in place",
                "expected_impact": "Smooth pre-travel experience",
            }

        return None

    def get_lifetime_journey(self) -> List[Dict[str, Any]]:
        """Build a timeline of all opportunities for the lifetime journey view."""
        all_opps = db.session.query(Opportunity).filter(
            Opportunity.customer_id == self.customer.id,
        ).order_by(Opportunity.created_at.asc()).all()

        journey = []
        for o in all_opps:
            status_icon = "✅" if o.status == "won" else ("❌" if o.status == "lost" else "●")
            year = o.created_at.year if o.created_at else None
            journey.append({
                "year": year,
                "title": o.title or o.destination or "Untitled",
                "destination": o.destination,
                "status": o.status,
                "stage": o.stage,
                "icon": status_icon,
                "is_active": o.status == "open",
                "outcome_notes": o.outcome_notes[:100] if o.outcome_notes else None,
                "outcome_rating": o.outcome_rating,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            })

        # Add referrals as journey milestones
        if self.customer.total_referrals and self.customer.total_referrals > 0:
            journey.append({
                "year": None,
                "title": f"{self.customer.total_referrals} referral(s)",
                "destination": None,
                "status": "referral",
                "stage": None,
                "icon": "↗️",
                "is_active": False,
                "outcome_notes": None,
                "outcome_rating": None,
                "created_at": None,
            })

        return journey

    def get_traveller_graph(self) -> Dict[str, Any]:
        """Return the traveller graph for display."""
        return self.customer.traveller_graph or {}

    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Recent meaningful activity across all opportunities."""
        return [{
            "id": a.id,
            "activity_type": a.activity_type,
            "title": a.title,
            "description": a.description[:120],
            "created_at": a.created_at.isoformat() if a.created_at else "",
        } for a in self._activity[:limit]]

    # ------------------------------------------------------------------
    # Build the complete brief
    # ------------------------------------------------------------------

    def build(self) -> Dict[str, Any]:
        """Generate the complete Relationship Brief as a dict."""
        header = self.get_relationship_header()
        prefs_brief = self.get_preferences_brief()
        one_thing = self.get_one_thing_to_remember()
        next_action = self.get_suggested_next_action()
        active_opps = self.get_active_opportunities()
        journey = self.get_lifetime_journey()
        traveller_graph = self.get_traveller_graph()
        recent_activity = self.get_recent_activity()

        return {
            "customer_id": self.customer.id,
            "header": header,
            "before_you_speak": prefs_brief,
            "one_thing_to_remember": one_thing,
            "suggested_next_action": next_action,
            "active_opportunities": active_opps,
            "lifetime_journey": journey,
            "traveller_graph": traveller_graph,
            "recent_activity": recent_activity,
            "preferences_detail": self.get_preferences(),
            "brief_generated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _health_label(health: str) -> str:
        labels = {
            "new": "New Relationship",
            "learning": "Getting to Know",
            "established": "Established",
            "strong": "Strong",
            "at_risk": "At Risk",
            "lapsed": "Lapsed",
        }
        return labels.get(health, health.replace("_", " ").title())


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def get_customer_brief(customer_id: int) -> Dict[str, Any]:
    """Convenience: load a customer and return their full Relationship Brief."""
    customer = db.session.query(Customer).get(customer_id)
    if not customer:
        return {"error": "Customer not found"}
    return RelationshipBrief(customer).build()


def suggest_next_action_for_customer(customer_id: int) -> Optional[Dict]:
    """Lightweight: just return the suggested next action."""
    customer = db.session.query(Customer).get(customer_id)
    if not customer:
        return None
    return RelationshipBrief(customer).get_suggested_next_action()


def get_lifetime_journey(customer_id: int) -> List[Dict]:
    """Lightweight: just return the lifetime journey timeline."""
    customer = db.session.query(Customer).get(customer_id)
    if not customer:
        return []
    return RelationshipBrief(customer).get_lifetime_journey()