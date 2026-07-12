"""Shunya Advisory Context — Generalized Relationship Intelligence.

Powers: Bird, Employee Copilot, Customer Advisor, Manager Coach, Founder Chief of Staff.
Same intelligence architecture. Different context. Different authority. Different language.

The AdvisoryContext produces Advice containing: observation, risk, alternatives,
recommendation, reason, expected outcome, and next best action.
"""
from datetime import datetime
from collections import defaultdict
from typing import Optional, List, Dict, Any
from app import db
from app.models import (
    Person, Relationship, RelationshipPreference,
    Opportunity, OpportunityActivity, Experience, Observation, Outcome
)


class AdvisoryContext:
    """Generalized intelligence context for any subject in the system.

    Produces structured Advice — not raw data. The employee should feel
    "I know this relationship" even if they've never spoken to them before.
    """

    def __init__(self, subject: Any, subject_type: str = "relationship",
                 user_role: str = "agent", tenant_id: int = None):
        self.subject = subject
        self.subject_type = subject_type
        self.user_role = user_role
        self.tenant_id = tenant_id or getattr(subject, 'tenant_id', None)

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def build(self) -> Dict[str, Any]:
        """Generate the complete Advice output for this context."""
        if self.subject_type == "relationship":
            return self._build_relationship_advice()
        elif self.subject_type == "opportunity":
            return self._build_opportunity_advice()
        return {"error": f"Unknown subject_type: {self.subject_type}"}

    # ------------------------------------------------------------------
    # Relationship Advice
    # ------------------------------------------------------------------

    def _build_relationship_advice(self) -> Dict[str, Any]:
        rel: Relationship = self.subject
        prefs = self._load_preferences(rel.id)
        active_opps = self._load_active_opportunities(rel.id)
        completed = self._load_completed_experiences(rel.id)

        before_you_speak = self._generate_before_you_speak(prefs, completed)
        one_thing = self._generate_one_thing(completed)
        next_action = self._suggest_next_action(active_opps, prefs, rel)
        journey = self._build_lifetime_journey(rel.id)

        return {
            "subject_type": "relationship",
            "relationship_id": rel.id,
            "header": self._relationship_header(rel),
            "before_you_speak": before_you_speak,
            "one_thing_to_remember": one_thing,
            "suggested_next_action": next_action,
            "active_opportunities": [o.to_dict() for o in active_opps],
            "lifetime_journey": journey,
            "traveller_graph": rel.traveller_graph or {},
            "preferences_detail": [p.to_dict() for p in prefs],
            "advice_generated_at": datetime.utcnow().isoformat(),
        }

    def _relationship_header(self, rel: Relationship) -> Dict:
        person = rel.person
        return {
            "name": rel.display_name or person.name,
            "email": rel.email or person.email,
            "phone": rel.phone or person.phone,
            "photo_url": person.photo_url if person else "",
            "tenure_years": rel.tenure_years,
            "health": rel.health,
            "health_label": self._health_label(rel.health),
            "total_experiences": rel.total_experiences,
            "total_referrals": rel.total_referrals,
            "preferred_channel": rel.preferred_channel,
            "communication_style": rel.communication_style or "unknown",
            "last_meaningful_interaction": rel.last_meaningful_interaction.isoformat()
                if rel.last_meaningful_interaction else None,
            "advisor_id": rel.advisor_id,
        }

    def _load_preferences(self, rel_id: int) -> List[RelationshipPreference]:
        return db.session.query(RelationshipPreference).filter(
            RelationshipPreference.relationship_id == rel_id,
            RelationshipPreference.is_active == True,
        ).order_by(RelationshipPreference.confidence.desc()).all()

    def _load_active_opportunities(self, rel_id: int) -> List[Opportunity]:
        return db.session.query(Opportunity).filter(
            Opportunity.relationship_id == rel_id,
            Opportunity.status == "open",
        ).order_by(Opportunity.updated_at.desc()).all()

    def _load_completed_experiences(self, rel_id: int) -> List[Experience]:
        """Load last 5 completed experiences with their outcomes."""
        exps = db.session.query(Experience).filter(
            Experience.relationship_id == rel_id,
        ).order_by(Experience.updated_at.desc()).limit(5).all()
        # Attach outcomes
        for exp in exps:
            exp._outcomes = db.session.query(Outcome).filter(
                Outcome.experience_id == exp.id,
            ).all()
        return exps

    def _generate_before_you_speak(self, prefs: List[RelationshipPreference],
                                    experiences: List[Experience]) -> List[str]:
        bullets = []
        pref_map = defaultdict(list)
        for p in prefs:
            pref_map[p.preference_type].append(p)

        if "travel_pace" in pref_map:
            p = pref_map["travel_pace"][0]
            bullets.append(f"Travel pace: {p.value.replace('_', ' ')} (confidence: {p.confidence})")

        if "hotel_location" in pref_map:
            p = pref_map["hotel_location"][0]
            label = p.value.replace("_", " ")
            evidence_count = len(p.evidence)
            if p.confidence == "high":
                bullets.append(f"Prefers {label} — observed across {evidence_count} trip(s)")
            else:
                bullets.append(f"May prefer {label}")

        if "budget_range" in pref_map:
            p = pref_map["budget_range"][0]
            bullets.append(f"Budget: {p.value}")

        if "airline" in pref_map:
            p = pref_map["airline"][0]
            bullets.append(f"Airline preference: {p.value}")

        if "room_category" in pref_map:
            p = pref_map["room_category"][0]
            bullets.append(f"Room preference: {p.value}")

        if "transfer_preference" in pref_map:
            p = pref_map["transfer_preference"][0]
            bullets.append(f"Transfer preference: {p.value}")

        if "decision_style" in pref_map:
            p = pref_map["decision_style"][0]
            style_labels = {
                "quick_decision": "Decides quickly with clear comparisons",
                "needs_time": "Takes time to decide — prefers 2-3 strong options",
                "consults_family": "Consults family before deciding",
                "price_sensitive": "Compares prices carefully before deciding",
            }
            bullets.append(style_labels.get(p.value, p.value.replace("_", " ")))

        # Recent experience signals
        for exp in experiences[:3]:
            if exp.exceptions:
                for exc in exp.exceptions[:2]:
                    bullets.append(f"Issue during {exp.title}: {exc.get('issue', '')} ({exc.get('severity', '')})")
            if exp.satisfaction_signals:
                for sig in exp.satisfaction_signals[:2]:
                    if sig.get("sentiment") == "negative":
                        bullets.append(f"Feedback ({exp.title}): {sig.get('text', '')[:80]}")

        return bullets

    def _generate_one_thing(self, experiences: List[Experience]) -> Optional[str]:
        """The single most important thing to know before speaking."""
        for exp in experiences:
            if exp.exceptions:
                worst = max(exp.exceptions, key=lambda e: {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(e.get("severity", "low"), 0))
                return f"{exp.title}: {worst.get('issue', 'Issue')} ({worst.get('severity', '')}) — {worst.get('detail', worst.get('recovery', ''))}"
            if exp.feedback and len(exp.feedback) > 10:
                return f"Feedback from {exp.title}: {exp.feedback[:120]}"

        for exp in experiences:
            for sig in exp.satisfaction_signals or []:
                if sig.get("sentiment") == "negative":
                    return f"{exp.title}: {sig.get('text', '')[:120]}"

        if experiences:
            return f"Last completed: {experiences[0].title} — check outcome before speaking"

        return None

    def _suggest_next_action(self, active_opps: List[Opportunity],
                              prefs: List[RelationshipPreference],
                              rel: Relationship) -> Optional[Dict]:
        if not active_opps:
            if rel.last_meaningful_interaction:
                delta = (datetime.utcnow() - rel.last_meaningful_interaction).days
                if delta > 90:
                    return {
                        "action": "Re-engage relationship",
                        "reason": f"No interaction in {delta} days. {rel.total_experiences} previous experiences.",
                        "expected_impact": "Retention and potential new opportunity",
                    }
            return None

        stage_priority = {"enquiry": 0, "discovery": 1, "planning": 2,
                          "proposal": 3, "negotiation": 4, "booking": 5}
        active_opps.sort(key=lambda o: stage_priority.get(o.stage, 99))
        o = active_opps[0]

        if o.stage == "enquiry":
            return {
                "action": f"Discovery conversation about {o.title or o.destination or 'their interest'}",
                "reason": "Understanding intent before building itinerary prevents rework",
                "expected_impact": "Faster qualification and more accurate proposal",
                "suggested_opening": f"Before I start hotels — are you imagining {o.destination or 'this trip'} as an exploring trip or a comfortable family holiday this time?",
            }

        if o.stage == "discovery" or o.stage == "planning":
            return {
                "action": f"Build proposal for {o.title or o.destination}",
                "reason": "Discovery phase complete — ready for proposal",
                "expected_impact": "Move toward booking conversation",
            }

        if o.stage == "proposal":
            for p in prefs:
                if p.preference_type == "decision_style" and p.value == "needs_time":
                    return {
                        "action": f"Follow up on {o.title} — customer takes time to decide",
                        "reason": "Previous behaviour shows they deliberate — patient follow-up increases conversion",
                        "suggested_opening": "No rush — wanted to check if you had questions about the options.",
                    }
            return {
                "action": f"Follow up on {o.title} proposal",
                "reason": "Proposal pending — timely follow-up increases conversion",
            }

        if o.stage == "negotiation":
            return {
                "action": f"Address open negotiation items for {o.title}",
                "reason": "Customer is actively negotiating — responsiveness matters most now",
            }

        if o.stage == "booking":
            return {
                "action": f"Confirm booking details for {o.title}",
                "reason": "Booking stage — ensure all confirmations in place for smooth experience",
            }

        return None

    def _build_lifetime_journey(self, rel_id: int) -> List[Dict]:
        all_opps = db.session.query(Opportunity).filter(
            Opportunity.relationship_id == rel_id,
        ).order_by(Opportunity.created_at.asc()).all()

        journey = []
        for o in all_opps:
            status_icon = "✅" if o.status == "won" else ("❌" if o.status == "lost" else "●")
            year = (o.enquiry_date or o.created_at).year if (o.enquiry_date or o.created_at) else None

            # Get related experience outcome
            exp = db.session.query(Experience).filter(
                Experience.opportunity_id == o.id,
            ).first()

            journey.append({
                "year": year,
                "title": o.title or o.destination or "Untitled",
                "destination": o.destination,
                "status": o.status,
                "stage": o.stage,
                "icon": status_icon,
                "is_active": o.status == "open",
                "experience_rating": exp.overall_rating if exp else None,
                "experience_issues": len(exp.exceptions) if exp and exp.exceptions else None,
                "experience_feedback": (exp.feedback[:80] if exp and exp.feedback else None),
            })

        # Add referrals as milestones
        rel = db.session.query(Relationship).get(rel_id)
        if rel and rel.total_referrals and rel.total_referrals > 0:
            journey.append({
                "year": None,
                "title": f"{rel.total_referrals} referral(s)",
                "destination": None,
                "status": "referral",
                "icon": "↗️",
                "is_active": False,
            })

        return journey

    # ------------------------------------------------------------------
    # Opportunity Advice (lightweight)
    # ------------------------------------------------------------------

    def _build_opportunity_advice(self) -> Dict[str, Any]:
        opp: Opportunity = self.subject
        return {
            "subject_type": "opportunity",
            "opportunity_id": opp.id,
            "stage": opp.stage,
            "status": opp.status,
            "priority": opp.priority,
            "probability": opp.probability,
            "risk": opp.risk,
            "next_stage": self._next_stage(opp.stage),
            "blockers": self._detect_blockers(opp),
            "suggested_action": self._suggest_opportunity_action(opp),
            "advice_generated_at": datetime.utcnow().isoformat(),
        }

    def _next_stage(self, current: str) -> Optional[str]:
        stages = ["enquiry", "discovery", "planning", "proposal",
                   "negotiation", "booking", "experience", "outcome", "closed"]
        try:
            idx = stages.index(current)
            return stages[idx + 1] if idx + 1 < len(stages) else None
        except ValueError:
            return None

    def _detect_blockers(self, opp: Opportunity) -> List[Dict]:
        blockers = []
        if opp.stage == "planning" and not opp.destination:
            blockers.append({"type": "missing_destination", "severity": "high"})
        if opp.stage == "proposal" and not opp.estimated_budget:
            blockers.append({"type": "missing_budget", "severity": "medium"})
        if opp.stage in ("booking", "experience") and not opp.bookings:
            blockers.append({"type": "no_bookings", "severity": "critical"})
        return blockers

    def _suggest_opportunity_action(self, opp: Opportunity) -> Optional[Dict]:
        stage_actions = {
            "enquiry": "Qualify intent and schedule discovery call",
            "discovery": "Document preferences and build initial plan",
            "planning": "Finalize destination and dates, begin itinerary",
            "proposal": "Share quote and await decision",
            "negotiation": "Address open items and close terms",
            "booking": "Confirm all bookings and send pre-trip documents",
            "experience": "Monitor in-trip experience and handle exceptions",
            "outcome": "Collect feedback and extract lessons",
            "closed": "Update relationship memory with outcome",
        }
        action = stage_actions.get(opp.stage, "Review opportunity")
        return {"action": action, "stage": opp.stage}

    # ------------------------------------------------------------------
    # Statics
    # ------------------------------------------------------------------

    @staticmethod
    def for_relationship(rel_id: int) -> Dict[str, Any]:
        rel = db.session.query(Relationship).get(rel_id)
        if not rel:
            return {"error": "Relationship not found"}
        return AdvisoryContext(rel, "relationship").build()

    @staticmethod
    def for_opportunity(opp_id: int) -> Dict[str, Any]:
        opp = db.session.query(Opportunity).get(opp_id)
        if not opp:
            return {"error": "Opportunity not found"}
        return AdvisoryContext(opp, "opportunity").build()

    @staticmethod
    def suggest_next_for_relationship(rel_id: int) -> Optional[Dict]:
        rel = db.session.query(Relationship).get(rel_id)
        if not rel:
            return None
        ctx = AdvisoryContext(rel, "relationship")
        prefs = ctx._load_preferences(rel.id)
        active = ctx._load_active_opportunities(rel.id)
        return ctx._suggest_next_action(active, prefs, rel)

    @staticmethod
    def lifetime_journey(rel_id: int) -> List[Dict]:
        rel = db.session.query(Relationship).get(rel_id)
        if not rel:
            return []
        ctx = AdvisoryContext(rel, "relationship")
        return ctx._build_lifetime_journey(rel.id)

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