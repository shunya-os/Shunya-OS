"""Shunya Marketing & Growth Module — Campaigns, Lead Gen, Content, Social, Webinars.

Every business needs to grow. This module provides:
- Campaign management (multi-channel campaigns)
- Email campaign tracking
- Lead generation source tracking
- Content asset library
- Social media post management
- Webinar & event management
"""
import json
from datetime import datetime, timedelta
from collections import defaultdict
from flask import g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog

# ---------------------------------------------------------------------------
# Entity Type Definitions
# ---------------------------------------------------------------------------

MARKETING_ENTITY_TYPES = {
    "campaign": {
        "label": "Campaign",
        "icon": "🚀",
        "schema": [
            {"name": "name", "label": "Campaign Name", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "goal", "label": "Goal", "type": "select",
             "options": ["brand_awareness", "lead_generation", "sales", "engagement", "retention", "other"]},
            {"name": "target_audience", "label": "Target Audience", "type": "text"},
            {"name": "budget", "label": "Budget", "type": "number"},
            {"name": "spent", "label": "Spent", "type": "number"},
            {"name": "channels", "label": "Channels", "type": "select",
             "options": ["email", "social", "paid_ads", "seo", "events", "content", "referral", "other"]},
            {"name": "start_date", "label": "Start Date", "type": "date"},
            {"name": "end_date", "label": "End Date", "type": "date"},
            {"name": "kpis", "label": "KPIs", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["planning", "active", "paused", "completed", "archived"],
        "layout": "kanban",
        "searchable_fields": ["name", "description", "goal", "target_audience"],
    },
    "email_campaign": {
        "label": "Email Campaign",
        "icon": "📧",
        "schema": [
            {"name": "name", "label": "Campaign Name", "type": "text", "required": True},
            {"name": "subject_line", "label": "Subject Line", "type": "text", "required": True},
            {"name": "preview_text", "label": "Preview Text", "type": "text"},
            {"name": "sender_name", "label": "Sender Name", "type": "text"},
            {"name": "sender_email", "label": "Sender Email", "type": "text"},
            {"name": "recipient_list", "label": "Recipient List", "type": "text"},
            {"name": "content", "label": "Email Content", "type": "textarea"},
            {"name": "scheduled_at", "label": "Scheduled At", "type": "datetime-local"},
            {"name": "sent_count", "label": "Sent Count", "type": "number"},
            {"name": "open_count", "label": "Opens", "type": "number"},
            {"name": "click_count", "label": "Clicks", "type": "number"},
            {"name": "bounce_count", "label": "Bounces", "type": "number"},
            {"name": "unsubscribe_count", "label": "Unsubscribes", "type": "number"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["draft", "scheduled", "sending", "sent", "paused", "cancelled"],
        "layout": "table",
        "searchable_fields": ["name", "subject_line", "sender_name", "sender_email"],
    },
    "lead_generator": {
        "label": "Lead Generator",
        "icon": "🎯",
        "schema": [
            {"name": "name", "label": "Source Name", "type": "text", "required": True},
            {"name": "source", "label": "Source Type", "type": "select",
             "options": ["website", "referral", "social_media", "paid_ads", "event", "content", "cold_outreach", "partner", "other"]},
            {"name": "target_leads", "label": "Target Leads", "type": "number"},
            {"name": "leads_generated", "label": "Leads Generated", "type": "number"},
            {"name": "qualified_leads", "label": "Qualified Leads", "type": "number"},
            {"name": "conversion_rate", "label": "Conversion Rate (%)", "type": "number"},
            {"name": "cost_per_lead", "label": "Cost Per Lead (₹)", "type": "number"},
            {"name": "budget", "label": "Budget (₹)", "type": "number"},
            {"name": "start_date", "label": "Start Date", "type": "date"},
            {"name": "end_date", "label": "End Date", "type": "date"},
            {"name": "assigned_to", "label": "Assigned To", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["active", "paused", "completed", "archived"],
        "layout": "table",
        "searchable_fields": ["name", "source", "assigned_to"],
    },
    "content_asset": {
        "label": "Content Asset",
        "icon": "📝",
        "schema": [
            {"name": "title", "label": "Title", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "content_type", "label": "Content Type", "type": "select",
             "options": ["blog", "video", "infographic", "ebook", "social_post", "template", "whitepaper", "case_study", "other"]},
            {"name": "url", "label": "URL", "type": "text"},
            {"name": "file_path", "label": "File Path", "type": "text"},
            {"name": "author", "label": "Author", "type": "text"},
            {"name": "tags", "label": "Tags", "type": "text"},
            {"name": "target_keywords", "label": "Target Keywords", "type": "text"},
            {"name": "campaign", "label": "Campaign", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["draft", "review", "approved", "published", "archived"],
        "layout": "cards",
        "searchable_fields": ["title", "description", "author", "tags", "target_keywords"],
    },
    "social_post": {
        "label": "Social Post",
        "icon": "📱",
        "schema": [
            {"name": "content", "label": "Post Content", "type": "textarea", "required": True},
            {"name": "platform", "label": "Platform", "type": "select",
             "options": ["linkedin", "twitter", "instagram", "facebook", "tiktok", "youtube", "other"]},
            {"name": "scheduled_at", "label": "Scheduled At", "type": "datetime-local"},
            {"name": "published_at", "label": "Published At", "type": "datetime-local"},
            {"name": "post_url", "label": "Post URL", "type": "text"},
            {"name": "engagement_likes", "label": "Likes", "type": "number"},
            {"name": "engagement_shares", "label": "Shares", "type": "number"},
            {"name": "engagement_comments", "label": "Comments", "type": "number"},
            {"name": "reach", "label": "Reach", "type": "number"},
            {"name": "hashtags", "label": "Hashtags", "type": "text"},
            {"name": "media_urls", "label": "Media URLs", "type": "text"},
            {"name": "campaign", "label": "Campaign", "type": "text"},
        ],
        "statuses": ["draft", "scheduled", "published", "failed", "archived"],
        "layout": "table",
        "searchable_fields": ["content", "platform", "hashtags", "campaign"],
    },
    "webinar": {
        "label": "Webinar",
        "icon": "🎥",
        "schema": [
            {"name": "title", "label": "Title", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "presenter", "label": "Presenter", "type": "text"},
            {"name": "date", "label": "Date", "type": "date"},
            {"name": "time", "label": "Time", "type": "text"},
            {"name": "duration_minutes", "label": "Duration (min)", "type": "number"},
            {"name": "registration_url", "label": "Registration URL", "type": "text"},
            {"name": "platforms", "label": "Platform", "type": "text"},
            {"name": "max_attendees", "label": "Max Attendees", "type": "number"},
            {"name": "registered_count", "label": "Registered", "type": "number"},
            {"name": "attended_count", "label": "Attended", "type": "number"},
            {"name": "recording_url", "label": "Recording URL", "type": "text"},
            {"name": "slides_url", "label": "Slides URL", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["planned", "scheduled", "live", "completed", "cancelled"],
        "layout": "table",
        "searchable_fields": ["title", "description", "presenter"],
    },
}


# ---------------------------------------------------------------------------
# Marketing Dashboard — Analytics & Insights
# ---------------------------------------------------------------------------

class MarketingDashboard:
    """Aggregate marketing metrics from entity data."""

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._defs = {}  # cache for entity definitions

    def _get_def(self, etype: str):
        """Get or cache entity definition by type."""
        if etype not in self._defs:
            self._defs[etype] = db.session.query(EntityDefinition).filter_by(
                tenant_id=self.tenant_id, type=etype
            ).first()
        return self._defs[etype]

    def _get_entities(self, etype: str, archived: bool = False):
        """Get all entities of a type for this tenant."""
        edef = self._get_def(etype)
        if not edef:
            return []
        q = db.session.query(Entity).filter_by(
            tenant_id=self.tenant_id,
            definition_id=edef.id,
            is_archived=archived,
        )
        return q.all()

    def ensure_types(self):
        """Ensure all marketing entity types exist for this tenant."""
        for etype, config in MARKETING_ENTITY_TYPES.items():
            existing = db.session.query(EntityDefinition).filter_by(
                tenant_id=self.tenant_id, type=etype
            ).first()
            if existing:
                continue
            definition = EntityDefinition(
                tenant_id=self.tenant_id,
                type=etype,
                label=config["label"],
                label_plural=f"{config['label']}s",
                icon=config["icon"],
                schema=config["schema"],
                statuses=config["statuses"],
                layout=config["layout"],
                searchable_fields=config["searchable_fields"],
                primary_field=config["schema"][0]["name"] if config["schema"] else "name",
            )
            db.session.add(definition)
        db.session.commit()

    def get_overview(self) -> dict:
        """Top-level marketing KPIs."""
        campaigns = self._get_entities("campaign")
        email_campaigns = self._get_entities("email_campaign")
        lead_generators = self._get_entities("lead_generator")
        content_assets = self._get_entities("content_asset")
        social_posts = self._get_entities("social_post")
        webinars = self._get_entities("webinar")

        active_campaigns = sum(1 for c in campaigns if c.status == "active")
        total_budget = sum(float(c.data.get("budget", 0) or 0) for c in campaigns)
        total_spent = sum(float(c.data.get("spent", 0) or 0) for c in campaigns)
        total_leads = sum(int(g.data.get("leads_generated", 0) or 0) for g in lead_generators)
        total_qualified = sum(int(g.data.get("qualified_leads", 0) or 0) for g in lead_generators)
        total_email_sent = sum(int(e.data.get("sent_count", 0) or 0) for e in email_campaigns)
        total_email_opens = sum(int(e.data.get("open_count", 0) or 0) for e in email_campaigns)
        total_registered = sum(int(w.data.get("registered_count", 0) or 0) for w in webinars)
        total_attended = sum(int(w.data.get("attended_count", 0) or 0) for w in webinars)

        return {
            "total_campaigns": len(campaigns),
            "active_campaigns": active_campaigns,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "budget_utilization": round((total_spent / total_budget * 100) if total_budget else 0, 1),
            "total_leads": total_leads,
            "qualified_leads": total_qualified,
            "lead_qualification_rate": round((total_qualified / total_leads * 100) if total_leads else 0, 1),
            "total_email_campaigns": len(email_campaigns),
            "total_email_sent": total_email_sent,
            "total_email_opens": total_email_opens,
            "email_open_rate": round((total_email_opens / total_email_sent * 100) if total_email_sent else 0, 1),
            "total_content_assets": len(content_assets),
            "published_content": sum(1 for c in content_assets if c.status == "published"),
            "total_social_posts": len(social_posts),
            "published_posts": sum(1 for p in social_posts if p.status == "published"),
            "total_webinars": len(webinars),
            "webinar_attendance_rate": round((total_attended / total_registered * 100) if total_registered else 0, 1),
        }

    def get_campaign_stats(self) -> list:
        """Per-campaign performance data."""
        campaigns = self._get_entities("campaign")
        results = []
        for c in campaigns:
            budget = float(c.data.get("budget", 0) or 0)
            spent = float(c.data.get("spent", 0) or 0)
            results.append({
                "id": c.id,
                "code": c.code,
                "name": c.data.get("name", c.display_name),
                "goal": c.data.get("goal", "other"),
                "status": c.status,
                "budget": budget,
                "spent": spent,
                "utilization": round((spent / budget * 100) if budget else 0, 1),
                "channel": c.data.get("channels", ""),
                "start_date": str(c.data.get("start_date", "")),
                "end_date": str(c.data.get("end_date", "")),
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })
        return results

    def get_lead_metrics(self) -> dict:
        """Lead generation source analysis."""
        generators = self._get_entities("lead_generator")
        by_source = defaultdict(lambda: {
            "count": 0, "leads": 0, "qualified": 0, "budget": 0.0, "cpl_total": 0.0,
        })
        for g in generators:
            source = g.data.get("source", "other")
            by_source[source]["count"] += 1
            by_source[source]["leads"] += int(g.data.get("leads_generated", 0) or 0)
            by_source[source]["qualified"] += int(g.data.get("qualified_leads", 0) or 0)
            by_source[source]["budget"] += float(g.data.get("budget", 0) or 0)
            cpl = float(g.data.get("cost_per_lead", 0) or 0)
            if cpl:
                by_source[source]["cpl_total"] += cpl

        source_breakdown = []
        for source, data in sorted(by_source.items(), key=lambda x: x[1]["leads"], reverse=True):
            qual_rate = round((data["qualified"] / data["leads"] * 100) if data["leads"] else 0, 1)
            avg_cpl = round(data["cpl_total"] / data["count"], 2) if data["count"] else 0
            source_breakdown.append({
                "source": source,
                "count": data["count"],
                "leads": data["leads"],
                "qualified": data["qualified"],
                "qualification_rate": qual_rate,
                "budget": data["budget"],
                "avg_cpl": avg_cpl,
            })

        total_leads = sum(s["leads"] for s in source_breakdown)
        total_qualified = sum(s["qualified"] for s in source_breakdown)

        return {
            "total_sources": len(generators),
            "active_sources": sum(1 for g in generators if g.status == "active"),
            "total_leads": total_leads,
            "total_qualified": total_qualified,
            "overall_qualification_rate": round((total_qualified / total_leads * 100) if total_leads else 0, 1),
            "source_breakdown": source_breakdown,
        }