"""
Shunya — Feature Request System + Approval Workflow (Phase 3H)

Team members request features in plain language.
AI assesses: feasibility, effort, impact.
Admin approves/modifies/rejects with one click.
"""

from datetime import datetime
from app import db
from app.module_builder import ModuleBuilder, ModuleBlueprint
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey


class FeatureRequest(db.Model):
    """A feature request from a team member."""
    __tablename__ = "feature_requests"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    requested_by = Column(String(120), default="")
    requested_by_id = Column(Integer, nullable=True)
    ai_assessment = Column(Text, default="")       # AI's analysis
    estimated_effort = Column(String(30), default="medium")  # low, medium, high
    estimated_impact = Column(String(30), default="medium")  # low, medium, high
    blueprint_id = Column(Integer, nullable=True)  # Link to module blueprint if applicable
    status = Column(String(30), default="pending")  # pending, under_review, approved, rejected, built
    admin_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "requested_by": self.requested_by,
            "ai_assessment": self.ai_assessment,
            "estimated_effort": self.estimated_effort,
            "estimated_impact": self.estimated_impact,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "created_at": self.created_at.isoformat(),
        }


class ApprovalWorkflow:
    """Manages the AI proposes → admin approves lifecycle."""

    def __init__(self):
        self.builder = ModuleBuilder()

    def submit_feature_request(self, title: str, description: str = "",
                                requested_by: str = "", requested_by_id: int = None,
                                tenant_id: int = None) -> FeatureRequest:
        """Team member submits a feature request. AI auto-assesses it."""
        req = FeatureRequest(
            tenant_id=tenant_id,
            title=title[:255],
            description=description,
            requested_by=requested_by,
            requested_by_id=requested_by_id,
            status="pending",
        )

        # AI assesses the request
        try:
            parsed = self.builder.parse_prompt(f"{title}. {description}")
            num_fields = len(parsed["fields"])
            effort = "low" if num_fields <= 3 else "medium" if num_fields <= 6 else "high"
            impact = self._assess_impact(title, description)
            has_clear_structure = num_fields > 0

            req.ai_assessment = (
                f"AI Analysis: This request {'can be clearly structured' if has_clear_structure else 'needs more detail'}. "
                f"Detected {num_fields} field(s) for entity '{parsed['entity']}'. "
                f"Suggested module name: {parsed['label']}."
            )
            req.estimated_effort = effort
            req.estimated_impact = impact
        except Exception:
            req.ai_assessment = "AI analysis pending."

        db.session.add(req)
        db.session.commit()

        # If AI can build it, auto-propose a blueprint
        if has_clear_structure:
            try:
                prompt = f"{title}. {description}"
                blueprint = self.builder.propose(prompt, proposed_by=f"AI (requested by {requested_by})",
                                                  tenant_id=tenant_id)
                req.blueprint_id = blueprint.id
                req.status = "under_review"
                db.session.commit()
            except Exception:
                pass

        return req

    def _assess_impact(self, title: str, description: str) -> str:
        """Estimate business impact from request text."""
        high = ["revenue", "conversion", "client", "customer", "payment", "booking",
                "sales", "lead", "critical", "blocking", "urgent", "important"]
        low = ["cosmetic", "minor", "small", "nice to have", "optional"]

        text = f"{title} {description}".lower()
        high_score = sum(1 for w in high if w in text)
        low_score = sum(1 for w in low if w in text)

        if high_score > low_score + 1:
            return "high"
        elif low_score > high_score:
            return "low"
        return "medium"

    def get_pending_requests(self, tenant_id: int = None) -> list[FeatureRequest]:
        query = FeatureRequest.query.filter(
            FeatureRequest.status.in_(["pending", "under_review"])
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(FeatureRequest.created_at.desc()).all()

    def get_all_requests(self, tenant_id: int = None) -> list[FeatureRequest]:
        query = FeatureRequest.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(FeatureRequest.created_at.desc()).all()

    def approve_request(self, req_id: int, admin_name: str = "admin",
                        admin_notes: str = "") -> FeatureRequest:
        """Approve a feature request and build its module."""
        req = db.session.get(FeatureRequest, req_id)
        if not req:
            return None
        req.status = "approved"
        req.admin_notes = admin_notes or req.admin_notes
        req.resolved_at = datetime.utcnow()
        db.session.commit()

        # Build the module if a blueprint exists
        if req.blueprint_id:
            blueprint = db.session.get(ModuleBlueprint, req.blueprint_id)
            if blueprint and blueprint.status == "proposed":
                self.builder.approve(req.blueprint_id, approved_by=admin_name)
                req.status = "built"
                db.session.commit()
        return req

    def reject_request(self, req_id: int, admin_name: str = "admin",
                       reason: str = "") -> FeatureRequest:
        req = db.session.get(FeatureRequest, req_id)
        if not req:
            return None
        req.status = "rejected"
        req.admin_notes = reason
        req.resolved_at = datetime.utcnow()
        db.session.commit()
        if req.blueprint_id:
            self.builder.reject(req.blueprint_id)
        return req