"""Onboarding Intelligence Engine — progressive business discovery through guided conversation."""

from datetime import datetime, date
from app import db
from app.models import Organization, OrgMember
from app.relationship.models import CanonicalRelationship


# ── Progressive Question Engine ────────────────────────────────────────

# Stage 1: Identity — learn the company basics
STAGE1_QUESTIONS = {
    "company_name": {"q": "What is your company called?", "field": "company_name", "required": True},
    "industry": {"q": "What industry are you in?", "field": "industry", "options": [
        "Technology / SaaS", "Retail / E-commerce", "Manufacturing",
        "Professional Services", "Healthcare", "Hospitality / Travel",
        "Education", "Construction / Real Estate", "Financial Services",
        "Other"]},
    "team_size": {"q": "How many people are in your team?", "field": "team_size",
        "options": ["1 (just me)", "2-10", "11-50", "51-200", "201-1000", "1000+"]},
    "primary_goal": {"q": "What is the main thing you want SHUNYA to help with?", "field": "primary_goal",
        "options": ["Understand our customers better", "Generate proposals faster",
            "Track finances and accounting", "Manage projects and tasks",
            "Automate approvals and workflows", "All of the above"]},
}

# Stage 2: Relationships — learn who matters
STAGE2_QUESTIONS = {
    "customer_count": {"q": "Approximately how many customers do you have?",
        "options": ["0-10", "11-50", "51-200", "201-1000", "1000+"]},
    "key_customers": {"q": "Can you name your 3 most important customers?",
        "placeholder": "e.g. Acme Corp, Beta Inc, Gamma LLC"},
    "has_suppliers": {"q": "Do you work with suppliers or vendors?",
        "options": ["Yes", "No"]},
    "approval_flow": {"q": "Who approves important decisions in your company?",
        "placeholder": "e.g. Founder approves everything >₹50k, Finance Manager approves up to ₹50k"},
}

# Stage 3: Operations — learn how work happens
STAGE3_QUESTIONS = {
    "work_volume": {"q": "How many proposals or quotes do you create in a typical month?",
        "options": ["0-5", "6-20", "21-50", "50+", "Not sure"]},
    "existing_tools": {"q": "What tools do you currently use for business operations?",
        "placeholder": "e.g. Gmail, Excel, Tally, Zoho, Salesforce, QuickBooks"},
    "pain_points": {"q": "What is the most frustrating part of your current workflow?",
        "placeholder": "e.g. Chasing payments, manual proposals, disconnected systems"},
}


class OnboardingSession:
    """Tracks a business onboarding journey through progressive discovery stages."""

    def __init__(self, organization_id, identity_id):
        self.org_id = organization_id
        self.identity_id = identity_id
        self.stage = 1
        self.question_index = 0
        self.answers = {}
        self.completed_stages = set()

    def current_question(self):
        """Get the next unanswered question based on current stage."""
        if self.stage == 1:
            questions = STAGE1_QUESTIONS
        elif self.stage == 2:
            questions = STAGE2_QUESTIONS
        elif self.stage == 3:
            questions = STAGE3_QUESTIONS
        else:
            return None

        keys = list(questions.keys())
        while self.question_index < len(keys):
            key = keys[self.question_index]
            if key not in self.answers:
                q = questions[key]
                return {"key": key, "stage": self.stage, "question": q["q"],
                    "options": q.get("options"), "placeholder": q.get("placeholder", ""),
                    "required": q.get("required", False),
                    "progress": f"Stage {self.stage}/4 — {self._stage_name(self.stage)}",
                    "pct": self._progress_pct()}
            self.question_index += 1
        return None

    def answer(self, key, value):
        """Record an answer and advance the session."""
        self.answers[key] = value
        self.question_index += 1
        # Check if stage is complete
        stage_questions = {1: STAGE1_QUESTIONS, 2: STAGE2_QUESTIONS, 3: STAGE3_QUESTIONS}.get(self.stage, {})
        all_answered = all(k in self.answers for k in stage_questions)
        if all_answered:
            self.completed_stages.add(self.stage)
            if self.stage < 3:
                self.stage += 1
                self.question_index = 0

        # Build canonical models from answers
        results = self._process_answers()
        return {"stage": self.stage, "completed_stages": sorted(self.completed_stages),
            "next_question": self.current_question(), "built": results}

    def _stage_name(self, stage):
        return {1: "Identity", 2: "Relationships", 3: "Operations", 4: "Intelligence"}.get(stage, "")

    def _progress_pct(self):
        total = len(STAGE1_QUESTIONS) + len(STAGE2_QUESTIONS) + len(STAGE3_QUESTIONS)
        answered = len(self.answers)
        return min(int(answered / total * 100), 100)

    def _process_answers(self):
        """Convert answers into canonical models where possible."""
        built = {}
        # Stage 1: Update organization
        if "company_name" in self.answers:
            org = db.session.get(Organization, self.org_id)
            if org:
                old_name = org.name
                if not old_name or old_name == "Default Organization":
                    org.name = self.answers["company_name"]
                    db.session.commit()
                    built["organization_name"] = self.answers["company_name"]

        # Stage 2: Create a relationship from key customers
        if "key_customers" in self.answers:
            names = [n.strip() for n in self.answers["key_customers"].split(",") if n.strip()]
            for name in names[:3]:
                existing = CanonicalRelationship.query.filter_by(
                    organization_id=self.org_id, display_name=name).first()
                if not existing:
                    rel = CanonicalRelationship(
                        organization_id=self.org_id, display_name=name,
                        relationship_type="customer",
                        notes=f"Discovered during onboarding",
                    )
                    db.session.add(rel)
                    db.session.flush()
                    built.setdefault("relationships", []).append({"display_name": name, "id": rel.id})
            if built.get("relationships"):
                db.session.commit()

        return built


# ── Session Store ──────────────────────────────────────────────────────

_sessions = {}  # In-memory for now; persists within a session


def get_or_create_session(org_id, identity_id):
    """Get existing onboarding session or create a new one."""
    key = f"{org_id}:{identity_id}"
    if key not in _sessions:
        _sessions[key] = OnboardingSession(org_id, identity_id)
    return _sessions[key]


def reset_session(org_id, identity_id):
    """Reset onboarding progress."""
    key = f"{org_id}:{identity_id}"
    _sessions.pop(key, None)


# ── Day-One Dashboard ──────────────────────────────────────────────────

def get_day_one_dashboard(org_id):
    """Generate the day-one view — never empty, always shows progress."""
    org = db.session.get(Organization, org_id)
    rel_count = CanonicalRelationship.query.filter_by(organization_id=org_id).count()
    from app.finance.models import FinInvoice as Invoice
    inv_count = Invoice.query.filter_by(organization_id=org_id).count()

    dashboard = {
        "organization": org.name if org else "Your Organization",
        "understood": {
            "customers": rel_count,
            "invoices": inv_count,
        },
        "insights": [],
        "recommended_actions": [],
    }

    # Progressive insights based on what's been discovered
    if rel_count == 0:
        dashboard["insights"].append({
            "type": "onboarding",
            "message": "I'm ready to learn about your business. Let's start with who your customers are.",
            "confidence": "high",
            "action": "Begin onboarding",
        })
        dashboard["recommended_actions"].append({
            "action": "Start guided onboarding",
            "reason": "I'll ask questions and build your business profile automatically.",
            "expected_benefit": "SHUNYA understands your company in minutes",
        })
    else:
        dashboard["insights"].append({
            "type": "discovered",
            "message": f"I've identified {rel_count} customer relationship(s) so far.",
            "confidence": "high",
        })
        if inv_count == 0:
            dashboard["recommended_actions"].append({
                "action": "Create your first invoice",
                "reason": "I noticed you have customers but no invoices yet.",
                "expected_benefit": "Start tracking revenue",
            })
        else:
            dashboard["insights"].append({
                "type": "financial",
                "message": f"{inv_count} invoice(s) recorded. Ready for financial analysis.",
                "confidence": "high",
            })

    dashboard["insights"].append({
        "type": "capability",
        "message": "I can generate proposals, track payments, run financial forecasts, and answer questions about your business.",
        "confidence": "high",
    })

    return dashboard