"""SHUNYA M6 — Connected Business Models.

Persistence models for notifications, integrations, email linking,
social media, ad campaigns, content generation, and API keys.
"""

from datetime import datetime

from app import db
from sqlalchemy import Index, Text


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class Notification(db.Model):
    """In-app notification for users. Supports entity linking, read tracking,
    and email dispatch status."""

    __tablename__ = "m6_notifications"
    __table_args__ = (
        Index("ix_m6_notif_user", "identity_id", "is_read", "created_at"),
        Index("ix_m6_notif_object", "object_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    notification_type = db.Column(db.String(40), nullable=False)
    # Types: entity_created, entity_updated, status_changed, commitment_due,
    #        conversation_new, reminder, system, automation_fired
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(Text, default="")
    object_id = db.Column(db.String(64), nullable=True)
    space_id = db.Column(db.String(64), nullable=True)
    conv_id = db.Column(db.String(64), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_email_sent = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "notification_type": self.notification_type,
            "title": self.title,
            "body": self.body,
            "object_id": self.object_id,
            "space_id": self.space_id,
            "conv_id": self.conv_id,
            "is_read": self.is_read,
            "is_email_sent": self.is_email_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }


# ---------------------------------------------------------------------------
# Integration Connection (OAuth / API keys)
# ---------------------------------------------------------------------------

class IntegrationConnection(db.Model):
    """OAuth connection to external services (email, calendar, etc.)."""

    __tablename__ = "m6_integrations"
    __table_args__ = (
        Index("ix_m6_integ_type", "identity_id", "provider"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    provider = db.Column(db.String(40), nullable=False)
    # Providers: gmail, outlook, google_calendar, outlook_calendar
    label = db.Column(db.String(255), default="")
    access_token = db.Column(db.Text, default="")
    refresh_token = db.Column(db.Text, default="")
    token_expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "provider": self.provider,
            "label": self.label,
            "is_active": self.is_active,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Integration Config (API keys for free services)
# ---------------------------------------------------------------------------

class IntegrationConfig(db.Model):
    """Stores API keys and configuration for free third-party integrations.

    Providers: unsplash, pexels, pixabay, tenor, openweather, newsapi,
               facebook, linkedin, twitter, instagram, google_ads, meta_ads,
               microsoft_graph, canva, reddit, spotify, youtube, github, gitlab,
               slack, discord, stripe, twilio, sendgrid, hubspot, mailchimp,
               openai, groq, together, cloudflare, huggingface, elevenlabs,
               google_maps, stripe
    """

    __tablename__ = "m6_integration_configs"
    __table_args__ = (
        Index("ix_m6_config_type", "identity_id", "provider", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    provider = db.Column(db.String(60), nullable=False)
    config_key = db.Column(db.String(120), nullable=False, default="api_key")
    config_value = db.Column(db.Text, nullable=True)
    config_json = db.Column(db.JSON, nullable=True, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    label = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, mask_secrets=True):
        d = {
            "id": self.id,
            "identity_id": self.identity_id,
            "provider": self.provider,
            "label": self.label or self.provider,
            "is_active": self.is_active,
            "has_config": bool(self.config_value or self.config_json),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if not mask_secrets:
            d["config_value"] = self.config_value
            d["config_json"] = self.config_json
        return d


# ---------------------------------------------------------------------------
# Social Media Account
# ---------------------------------------------------------------------------

class SocialAccount(db.Model):
    """Linked social media accounts for posting and management."""

    __tablename__ = "m6_social_accounts"
    __table_args__ = (
        Index("ix_m6_social_platform", "identity_id", "platform"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    platform = db.Column(db.String(40), nullable=False)
    # Platforms: facebook, twitter, linkedin, instagram, youtube, tiktok, pinterest
    account_name = db.Column(db.String(255), nullable=False)
    account_id = db.Column(db.String(255), nullable=True)
    access_token = db.Column(db.Text, default="")
    refresh_token = db.Column(db.Text, default="")
    token_expires_at = db.Column(db.DateTime, nullable=True)
    profile_picture_url = db.Column(db.String(500), nullable=True)
    profile_url = db.Column(db.String(500), nullable=True)
    follower_count = db.Column(db.Integer, nullable=True, default=0)
    is_active = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "platform": self.platform,
            "account_name": self.account_name,
            "account_id": self.account_id,
            "profile_picture_url": self.profile_picture_url,
            "profile_url": self.profile_url,
            "follower_count": self.follower_count,
            "is_active": self.is_active,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Scheduled Social Post
# ---------------------------------------------------------------------------

class ScheduledPost(db.Model):
    """Scheduled social media posts with content and targeting."""

    __tablename__ = "m6_scheduled_posts"

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    platform = db.Column(db.String(40), nullable=False)
    content = db.Column(Text, nullable=False)
    media_urls = db.Column(db.JSON, nullable=True, default=list)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="draft")
    # Status: draft, scheduled, published, failed, cancelled
    published_at = db.Column(db.DateTime, nullable=True)
    post_url = db.Column(db.String(500), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    engagement_metrics = db.Column(db.JSON, nullable=True, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "platform": self.platform,
            "content": self.content,
            "media_urls": self.media_urls or [],
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "post_url": self.post_url,
            "error_message": self.error_message,
            "engagement_metrics": self.engagement_metrics or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# Ad Campaign
# ---------------------------------------------------------------------------

class AdCampaign(db.Model):
    """Advertising campaign across platforms (Meta, Google, LinkedIn)."""

    __tablename__ = "m6_ad_campaigns"

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    platform = db.Column(db.String(40), nullable=False)
    # Platforms: meta_ads, google_ads, linkedin_ads, twitter_ads
    campaign_name = db.Column(db.String(255), nullable=False)
    campaign_objective = db.Column(db.String(80), default="awareness")
    # Objectives: awareness, traffic, engagement, leads, sales, conversions
    budget = db.Column(db.Float, nullable=True, default=0.0)
    budget_type = db.Column(db.String(20), default="daily")
    # daily, lifetime
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    targeting = db.Column(db.JSON, nullable=True, default=dict)
    creative = db.Column(db.JSON, nullable=True, default=dict)
    status = db.Column(db.String(20), default="draft")
    # Status: draft, active, paused, completed, failed, archived
    external_campaign_id = db.Column(db.String(255), nullable=True)
    performance_metrics = db.Column(db.JSON, nullable=True, default=dict)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "platform": self.platform,
            "campaign_name": self.campaign_name,
            "campaign_objective": self.campaign_objective,
            "budget": self.budget,
            "budget_type": self.budget_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "targeting": self.targeting or {},
            "creative": self.creative or {},
            "status": self.status,
            "external_campaign_id": self.external_campaign_id,
            "performance_metrics": self.performance_metrics or {},
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# Content Generation History
# ---------------------------------------------------------------------------

class ContentGeneration(db.Model):
    """History of AI-generated content pieces."""

    __tablename__ = "m6_content_generations"

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    content_type = db.Column(db.String(40), nullable=False)
    # Types: blog_post, social_post, ad_copy, email, landing_page, product_desc,
    #        seo_meta, press_release, newsletter, script, caption, reply
    platform = db.Column(db.String(40), nullable=True)
    prompt = db.Column(db.Text, nullable=False)
    generated_content = db.Column(db.Text, nullable=True)
    tone = db.Column(db.String(40), default="professional")
    target_audience = db.Column(db.String(255), nullable=True)
    word_count = db.Column(db.Integer, nullable=True)
    ai_model = db.Column(db.String(60), default="groq")
    is_favorited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "content_type": self.content_type,
            "platform": self.platform,
            "prompt": self.prompt,
            "generated_content": self.generated_content,
            "tone": self.tone,
            "target_audience": self.target_audience,
            "word_count": self.word_count,
            "ai_model": self.ai_model,
            "is_favorited": self.is_favorited,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Email Cache (synced emails linked to entities)
# ---------------------------------------------------------------------------

class CachedEmail(db.Model):
    """Cached email that has been synced and linked to entities."""

    __tablename__ = "m6_cached_emails"
    __table_args__ = (
        Index("ix_m6_email_msg", "message_id", unique=True),
        Index("ix_m6_email_object", "object_id"),
        Index("ix_m6_email_from", "from_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    message_id = db.Column(db.String(255), nullable=False)
    thread_id = db.Column(db.String(255), nullable=True)
    from_email = db.Column(db.String(255), nullable=False)
    from_name = db.Column(db.String(255), default="")
    to_email = db.Column(db.Text, default="")
    subject = db.Column(db.String(500), default="")
    body_preview = db.Column(db.String(500), default="")
    body_text = db.Column(Text, default="")
    received_at = db.Column(db.DateTime, nullable=True)
    object_id = db.Column(db.String(64), nullable=True)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "subject": self.subject,
            "body_preview": self.body_preview,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "object_id": self.object_id,
            "is_processed": self.is_processed,
        }


# ---------------------------------------------------------------------------
# Cached Media Results (proxy caching)
# ---------------------------------------------------------------------------


class CachedMedia(db.Model):
    """Cached media search results from external providers.

    Stores results from Unsplash, Pexels, Pixabay, Tenor, etc.
    so the proxy can return cached results without hitting the external API
    on every request.
    """

    __tablename__ = "m6_cached_media"
    __table_args__ = (
        Index("ix_m6_cached_provider_query", "provider", "query_hash"),
    )

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(40), nullable=False)
    # Providers: unsplash, pexels, pixabay, tenor
    query_hash = db.Column(db.String(64), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    response_data = db.Column(db.JSON, nullable=True, default=list)
    total_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "query": self.query,
            "total_count": self.total_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


# ---------------------------------------------------------------------------
# Notification Preference
# ---------------------------------------------------------------------------

class NotificationPreference(db.Model):
    """Per-user notification preferences."""

    __tablename__ = "m6_notif_prefs"

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    email_notifications = db.Column(db.Boolean, default=True)
    in_app_notifications = db.Column(db.Boolean, default=True)
    digest_frequency = db.Column(db.String(20), default="immediate")
    # immediate, daily, weekly
    quiet_hours_start = db.Column(db.String(5), default="")
    quiet_hours_end = db.Column(db.String(5), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "email_notifications": self.email_notifications,
            "in_app_notifications": self.in_app_notifications,
            "digest_frequency": self.digest_frequency,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
        }