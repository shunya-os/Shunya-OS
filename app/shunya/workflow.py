"""
Workflow Layer (Shunya)
Orchestrates the full pipeline: Knowledge → Reasoning → Planner → Delivery.
Coordinates lead lifecycle, proposal generation, and follow-ups.
"""

from typing import Optional
from .knowledge import KnowledgeLayer
from .reasoning import ReasoningLayer, CustomerProfile
from .planner import PlannerLayer, ItineraryPlan
from sqlalchemy import func


class WorkflowResult:
    """Result of running the full pipeline."""
    def __init__(self):
        self.profile: Optional[CustomerProfile] = None
        self.strategy: Optional[dict] = None
        self.plan: Optional[ItineraryPlan] = None
        self.proposal_text: str = ""
        self.lead_id: Optional[int] = None
        self.errors: list[str] = []

    def success(self) -> bool:
        return len(self.errors) == 0 and self.plan is not None

    def to_dict(self) -> dict:
        return {
            "success": self.success(),
            "lead_id": self.lead_id,
            "errors": self.errors,
            "customer": self.profile.customer_name if self.profile else "",
            "destination": self.profile.destination if self.profile else "",
            "itinerary_days": len(self.plan.days) if self.plan else 0,
            "proposal_length": len(self.proposal_text),
        }


class WorkflowLayer:
    """
    The top-level orchestrator. Chains Knowledge → Reasoning → Planner.
    Manages lead lifecycle: new → analysis → proposal → converted.
    """

    def __init__(self, db_session=None):
        self.knowledge = KnowledgeLayer(db_session)
        self.reasoning = ReasoningLayer(self.knowledge)
        self.planner = PlannerLayer()
        self._db = db_session

    def process_inquiry(self, inquiry: dict) -> WorkflowResult:
        """
        Run the full pipeline on a customer inquiry.
        Knowledge → Reasoning → Planner → Output
        """
        result = WorkflowResult()

        try:
            # Step 1: Reason about the inquiry
            profile = self.reasoning.analyze_inquiry(inquiry)
            result.profile = profile

            # Step 2: Develop strategy
            strategy = self.reasoning.suggest_approach(profile)
            result.strategy = strategy

            # Step 3: Build itinerary
            plan = self.planner.create_itinerary(profile, strategy)
            result.plan = plan

            # Step 4: Generate proposal text
            result.proposal_text = self.planner.generate_proposal_text(plan)

        except Exception as e:
            result.errors.append(str(e))

        return result

    def create_lead_from_inquiry(self, inquiry: dict) -> Optional[int]:
        """Create a database lead record from an inquiry dict."""
        if not self._db:
            return None

        from app.models import Lead, next_inquiry_code

        code = next_inquiry_code(self._db)
        lead = Lead(
            code=code,
            source=inquiry.get("source", "telegram"),
            customer_name=inquiry.get("customer_name", ""),
            phone=inquiry.get("phone", ""),
            destination=inquiry.get("destination", ""),
            pax=inquiry.get("pax", ""),
            dates=inquiry.get("dates", ""),
            notes=inquiry.get("notes", ""),
        )
        self._db.add(lead)
        self._db.commit()
        return lead.id

    def get_lead_status_summary(self, db_session) -> list[dict]:
        """Get a summary of all leads for the dashboard."""
        from app.models import Lead, Payment, Invoice

        leads = db_session.query(Lead).order_by(Lead.created_at.desc()).limit(20).all()
        summary = []
        for lead in leads:
            total_paid = float(
                db_session.query(func.coalesce(func.sum(Payment.amount), 0))
                .filter(Payment.lead_id == lead.id, Payment.type == "guest_payment")
                .scalar() or 0
            )
            invoice_count = db_session.query(func.count(Invoice.id)).filter(Invoice.lead_id == lead.id).scalar() or 0
            summary.append({
                "code": lead.code,
                "customer": lead.customer_name,
                "destination": lead.destination,
                "status": lead.status,
                "total_paid": float(total_paid),
                "invoices": invoice_count,
                "created": lead.created_at.isoformat(),
            })
        return summary