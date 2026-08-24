"""Workspace Experience Framework — Models, Constants, and Services."""

from datetime import datetime, timezone
from app import db
from sqlalchemy import Index


# ── Experience Catalog ─────────────────────────────────────────────────

EXPERIENCE_CATALOG = {
    "dashboard":       {"label": "Business Dashboard",   "category": "business",    "default": "always"},
    "knowledge":       {"label": "Company Knowledge",    "category": "business",    "default": "always"},
    "calendar":        {"label": "Calendar",             "category": "business",    "default": "always"},
    "tasks":           {"label": "Tasks",                "category": "business",    "default": "always"},
    "approvals":       {"label": "Approvals",            "category": "business",    "default": "always"},
    "executive":       {"label": "Executive Intelligence","category": "business",   "default": "always"},
    "communication":   {"label": "Internal Communication","category": "business",   "default": "always"},
    "music":           {"label": "Music",                "category": "optional",   "default": "controlled"},
    "videos":          {"label": "Video Platforms",      "category": "optional",   "default": "controlled"},
    "industry_news":   {"label": "Industry News",        "category": "optional",   "default": "controlled"},
    "personal_widgets":{"label": "Personal Widgets",     "category": "optional",   "default": "controlled"},
    "focus_timer":     {"label": "Focus Timer",          "category": "optional",   "default": "controlled"},
    "wellness":        {"label": "Wellness Features",    "category": "optional",   "default": "controlled"},
    "ai_coach":        {"label": "AI Coaching",          "category": "optional",   "default": "controlled"},
    "learning":        {"label": "Learning Resources",   "category": "optional",   "default": "controlled"},
    "travel_planning": {"label": "Travel Planning",      "category": "optional",   "default": "controlled"},
    "entertainment":   {"label": "General Entertainment","category": "restricted", "default": "restricted"},
    "social_media":    {"label": "Social Media",         "category": "restricted", "default": "restricted"},
    "external_media":  {"label": "External Media",       "category": "restricted", "default": "restricted"},
}

CONTEXT_MODES = {
    "focus":     {"label": "Focused Work",    "priority": "business_only"},
    "normal":    {"label": "Normal",          "priority": "normal"},
    "break":     {"label": "Break",           "priority": "surf_optional"},
    "learning":  {"label": "Learning",        "priority": "surf_educational"},
    "approval":  {"label": "Critical",        "priority": "business_only"},
}


# ── Policy Model ───────────────────────────────────────────────────────

class WorkspacePolicy(db.Model):
    __tablename__ = "wksp_policies"
    __table_args__ = (
        Index("ix_wksp_policy_level", "organization_id", "level", "level_id"),
        db.UniqueConstraint("organization_id", "level", "level_id", "experience_key",
            name="uq_wksp_policy"),
    )
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    level = db.Column(db.String(30), nullable=False)
    level_id = db.Column(db.Integer, nullable=True)
    experience_key = db.Column(db.String(60), nullable=False)
    setting = db.Column(db.String(30), nullable=False)
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "level": self.level, "level_id": self.level_id,
            "experience_key": self.experience_key, "setting": self.setting}


# ── Policy Engine ──────────────────────────────────────────────────────

def resolve_experience_setting(org_id, experience_key, user_roles=None):
    """Resolve effective setting using policy inheritance: individual → role → team → department → org."""
    catalog = EXPERIENCE_CATALOG.get(experience_key)
    if not catalog:
        return {"setting": "disabled", "reason": "Unknown experience", "source": "catalog"}
    default = catalog["default"]
    # Check hierarchy: org-level policy first (most general), then individual/role
    p = WorkspacePolicy.query.filter_by(
        organization_id=org_id, level="org", experience_key=experience_key).first()
    if p:
        return {"setting": p.setting, "reason": f"Set by org policy", "source": "org"}
    return {"setting": default, "reason": "Catalog default", "source": "catalog"}


def set_policy(org_id, level, experience_key, setting, level_id=None, created_by=""):
    existing = WorkspacePolicy.query.filter_by(
        organization_id=org_id, level=level, level_id=level_id,
        experience_key=experience_key).first()
    if existing:
        existing.setting = setting
        existing.updated_at = datetime.now(timezone.utc)
    else:
        p = WorkspacePolicy(organization_id=org_id, level=level, level_id=level_id,
            experience_key=experience_key, setting=setting, created_by=created_by)
        db.session.add(p)
    db.session.commit()
    return {"experience_key": experience_key, "level": level, "setting": setting}


def get_policy_summary(org_id):
    policies = WorkspacePolicy.query.filter_by(organization_id=org_id).all()
    summary = {}
    for p in policies:
        summary.setdefault(p.experience_key, {})
        summary[p.experience_key]["label"] = EXPERIENCE_CATALOG.get(p.experience_key, {}).get("label", p.experience_key)
        summary[p.experience_key][p.level] = p.setting
    return summary


def get_available_experiences(org_id, context_mode="normal", user_roles=None):
    context = CONTEXT_MODES.get(context_mode, CONTEXT_MODES["normal"])
    experiences = []
    for key, catalog in EXPERIENCE_CATALOG.items():
        resolved = resolve_experience_setting(org_id, key, user_roles)
        setting = resolved["setting"]
        if setting == "disabled":
            continue
        if context["priority"] == "business_only" and catalog["category"] != "business":
            continue
        if context["priority"] == "surf_optional" and catalog["category"] == "restricted":
            continue
        experiences.append({
            "key": key, "label": catalog["label"], "category": catalog["category"],
            "available": setting != "disabled", "setting": setting,
        })
    return {"context_mode": context_mode, "context_label": context["label"],
        "experiences": experiences, "total": len(experiences)}