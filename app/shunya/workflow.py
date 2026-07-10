"""
Shunya — Workflow Layer (Unit 4, v2)

Orchestrates: Knowledge → Reasoning → Planner → Delivery.
Manages lead lifecycle, proposal generation, and multi-format output.
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
        self.proposal_html: str = ""
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
            "occasion": self.profile.occasion if self.profile else "",
            "group_type": self.profile.group_type if self.profile else "",
            "itinerary_days": len(self.plan.days) if self.plan else 0,
            "proposal_length": len(self.proposal_text),
            "budget_estimate": self.strategy.get("daily_budget_per_person", 0) if self.strategy else 0,
        }


class WorkflowLayer:
    """
    Top-level orchestrator. Chains Knowledge → Reasoning → Planner.
    Handles format selection, lead lifecycle, and proposal delivery.
    """

    def __init__(self, db_session=None):
        self.knowledge = KnowledgeLayer(db_session)
        self.reasoning = ReasoningLayer(self.knowledge)
        self.planner = PlannerLayer()
        self._db = db_session

    def process_inquiry(self, inquiry: dict, fmt: str = "text") -> WorkflowResult:
        """
        Run the full pipeline on an inquiry.

        Args:
            inquiry: dict with customer_name, destination, pax, dates, notes, phone, source
            fmt: output format — "text" (markdown), "html", or "all"

        Returns:
            WorkflowResult with profile, strategy, plan, and proposal text/html
        """
        result = WorkflowResult()

        try:
            # Step 1: Analyze
            profile = self.reasoning.analyze_inquiry(inquiry)
            result.profile = profile

            # Step 2: Strategy
            strategy = self.reasoning.suggest_approach(profile)
            result.strategy = strategy

            # Step 3: Build itinerary
            plan = self.planner.create_itinerary(profile, strategy)
            result.plan = plan

            # Step 4: Generate proposals
            if fmt in ("text", "markdown", "all"):
                result.proposal_text = self.planner.generate_proposal_text(plan)
            if fmt in ("html", "all"):
                result.proposal_html = self.planner.generate_proposal_html(plan)

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
            email=inquiry.get("email", ""),
            destination=inquiry.get("destination", ""),
            pax=inquiry.get("pax", ""),
            dates=inquiry.get("dates", ""),
            budget=inquiry.get("budget", 0),
            notes=inquiry.get("notes", ""),
        )
        self._db.add(lead)
        self._db.commit()
        # Log activity
        try:
            from app.models import ActivityLog
            log = ActivityLog(lead_id=lead.id, action="created",
                              detail="Lead created via Shunya pipeline", user="AI@panchi.club")
            self._db.add(log)
            self._db.commit()
        except Exception:
            self._db.rollback()
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
            invoice_count = db_session.query(func.count(Invoice.id)).filter(
                Invoice.lead_id == lead.id
            ).scalar() or 0
            summary.append({
                "code": lead.code,
                "customer": lead.customer_name,
                "destination": lead.destination,
                "status": lead.status,
                "total_paid": total_paid,
                "invoices": invoice_count,
                "created": lead.created_at.isoformat(),
            })
        return summary