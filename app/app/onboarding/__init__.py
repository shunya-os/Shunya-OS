"""Universal Business Discovery & Day-One Operational Readiness.

The gap between SHUNYA today and SHUNYA that can onboard a real company.
"""

# ── Architecture: The Onboarding Stack ─────────────────────────────────
#
#  Discovery Sources          Intake Layer           Canonical Models
# ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
# │ Conversation      │    │ Intent Parser     │    │ Organization      │
# │ Documents (PDF)  │ →  │ Entity Extractor  │ →  │ Relationship      │
# │ Email/MBOX       │    │ Relationship Mgr  │    │ Proposal          │
# │ CSV/Excel        │    │ Conflict Detector │    │ Invoice           │
# │ Images (OCR)     │    │ Progressive Q     │    │ Payment           │
# │ Existing systems │    │ Confidence Scorer │    │ ...               │
# └──────────────────┘    └──────────────────┘    └──────────────────┘
#                                                     │
#                Day-One Productivity                 ▼
#          ┌──────────────────────────────┐    ┌──────────────────┐
#          │ Auto-summarise discovered    │    │ Timeline         │
#          │ Draft proposals from context │    │ AI Memory        │
#          │ Identify risks/opportunities │    │ Knowledge        │
#          │ Prepare executive summary    │    │ Executive Intel  │
#          │ Suggest next actions         │    └──────────────────┘
#          └──────────────────────────────┘

from flask import Blueprint

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/api/v1/onboarding")


def register_routes():
    from app.onboarding import routes  # noqa: F401


register_routes()


# ── Gap Analysis (Current vs Required) ─────────────────────────────────

GAPS = {
    "onboarding_wizard": {
        "exists": False,
        "priority": "P0 — must exist before any company can onboard",
        "effort": "3-5 days",
        "design": "Conversation-driven: 'Tell me about your company' → progressively adaptive questions → SHUNYA builds canonical models in real-time"
    },
    "document_intake": {
        "exists": False,
        "priority": "P0 — most companies have their data in documents",
        "effort": "5-7 days",
        "design": "Upload PDF/Word/Excel/CSV → extract entities → match to canonical models (customers, invoices, suppliers) → user confirms"
    },
    "email_intake": {
        "exists": False,
        "priority": "P1 — important for communication continuity",
        "effort": "5-7 days",
        "design": "MBOX/IMAP import → extract contacts, commitments, invoice data → build relationship timeline"
    },
    "empty_state_ban": {
        "exists": False,
        "priority": "P0 — constitutionally forbidden",
        "effort": "1 day",
        "design": "Every authenticated page: if no data, show discovery progress + recommended next actions instead of blank screen"
    },
    "day_one_productivity": {
        "exists": "partial",
        "priority": "P1 — proposals and invoices work, but auto-summaries and suggestions don't",
        "effort": "2-3 days",
        "design": "After any data enters, auto-generate: executive summary, risk observations, next-action recommendations"
    },
    "multi_business_validation": {
        "exists": False,
        "priority": "P1 — need to prove adaptability",
        "effort": "2-3 days",
        "design": "Seed 6 business types with realistic data, validate every workflow works for each"
    },
}


def assess_readiness() -> dict:
    """Produce a readiness summary."""
    total = len(GAPS)
    resolved = sum(1 for g in GAPS.values() if g.get("exists"))
    return {
        "readiness_pct": round(resolved / total * 100) if total else 0,
        "gaps_resolved": resolved,
        "gaps_total": total,
        "estimated_build_days": sum(
            int(g["effort"].split("-")[0]) if "-" in g["effort"] else int(g["effort"].split()[0])
            for g in GAPS.values() if not g["exists"]
        ),
        "p0_gaps": sum(1 for g in GAPS.values() if "P0" in g.get("priority", "") and not g.get("exists")),
    }