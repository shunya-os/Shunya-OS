"""SHUNYA M6 — Integration Service.

Handles in-app notifications, API key management, social media accounts,
ad campaigns, content generation, and third-party integrations.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from app import db
from app.integration.models import (
    AdCampaign,
    CachedEmail,
    CachedMedia,
    ContentGeneration,
    IntegrationConfig,
    IntegrationConnection,
    Notification,
    NotificationPreference,
    ScheduledPost,
    SocialAccount,
)

logger = logging.getLogger(__name__)


# =========================================================================
# NOTIFICATION SERVICE
# =========================================================================

def create_notification(
    identity_id: str,
    notification_type: str,
    title: str,
    body: str = "",
    object_id: str | None = None,
    space_id: str | None = None,
    conv_id: str | None = None,
) -> Notification:
    """Create a notification and attempt email dispatch if configured."""
    notif = Notification(
        identity_id=identity_id,
        notification_type=notification_type,
        title=title,
        body=body,
        object_id=object_id,
        space_id=space_id,
        conv_id=conv_id,
    )
    db.session.add(notif)
    db.session.commit()
    return notif


def get_notifications(
    identity_id: str,
    limit: int = 50,
    unread_only: bool = False,
) -> list[dict[str, Any]]:
    """Get notifications for an identity."""
    query = Notification.query.filter_by(identity_id=identity_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    notifs = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return [n.to_dict() for n in notifs]


def get_unread_count(identity_id: str) -> int:
    """Get the count of unread notifications."""
    return Notification.query.filter_by(
        identity_id=identity_id, is_read=False
    ).count()


def mark_as_read(notification_id: int) -> bool:
    """Mark a single notification as read."""
    notif = Notification.query.get(notification_id)
    if not notif:
        return False
    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.session.commit()
    return True


def mark_all_as_read(identity_id: str) -> int:
    """Mark all notifications as read for an identity."""
    notifs = Notification.query.filter_by(
        identity_id=identity_id, is_read=False
    ).all()
    now = datetime.now(timezone.utc)
    for n in notifs:
        n.is_read = True
        n.read_at = now
    db.session.commit()
    return len(notifs)


def get_preferences(identity_id: str) -> dict[str, Any]:
    """Get or create notification preferences."""
    prefs = NotificationPreference.query.filter_by(
        identity_id=identity_id
    ).first()
    if not prefs:
        prefs = NotificationPreference(identity_id=identity_id)
        db.session.add(prefs)
        db.session.commit()
    return prefs.to_dict()


def update_preferences(
    identity_id: str,
    email_notifications: bool | None = None,
    in_app_notifications: bool | None = None,
    digest_frequency: str | None = None,
    quiet_hours_start: str | None = None,
    quiet_hours_end: str | None = None,
) -> dict[str, Any]:
    """Update notification preferences."""
    prefs = NotificationPreference.query.filter_by(
        identity_id=identity_id
    ).first()
    if not prefs:
        prefs = NotificationPreference(identity_id=identity_id)
        db.session.add(prefs)

    if email_notifications is not None:
        prefs.email_notifications = email_notifications
    if in_app_notifications is not None:
        prefs.in_app_notifications = in_app_notifications
    if digest_frequency is not None:
        prefs.digest_frequency = digest_frequency
    if quiet_hours_start is not None:
        prefs.quiet_hours_start = quiet_hours_start
    if quiet_hours_end is not None:
        prefs.quiet_hours_end = quiet_hours_end

    db.session.commit()
    return prefs.to_dict()


# =========================================================================
# INTEGRATION CONNECTION SERVICE (OAuth)
# =========================================================================

def save_connection(
    identity_id: str,
    provider: str,
    access_token: str,
    refresh_token: str = "",
    label: str = "",
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    """Save or update an OAuth integration connection."""
    conn = IntegrationConnection.query.filter_by(
        identity_id=identity_id, provider=provider
    ).first()

    if conn:
        conn.access_token = access_token
        conn.refresh_token = refresh_token or conn.refresh_token
        conn.label = label or conn.label
        conn.token_expires_at = expires_at
        conn.is_active = True
    else:
        conn = IntegrationConnection(
            identity_id=identity_id,
            provider=provider,
            label=label,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at,
        )
        db.session.add(conn)

    db.session.commit()
    return conn.to_dict()


def get_connections(identity_id: str) -> list[dict[str, Any]]:
    """Get all OAuth integration connections."""
    conns = IntegrationConnection.query.filter_by(
        identity_id=identity_id
    ).all()
    return [c.to_dict() for c in conns]


def remove_connection(identity_id: str, provider: str) -> bool:
    """Remove an OAuth integration connection."""
    conn = IntegrationConnection.query.filter_by(
        identity_id=identity_id, provider=provider
    ).first()
    if not conn:
        return False
    conn.is_active = False
    db.session.commit()
    return True


# =========================================================================
# INTEGRATION CONFIG SERVICE (API keys for free services)
# =========================================================================

def list_providers() -> list[dict[str, Any]]:
    """Return the master list of all available integration providers."""
    return [
        # ── Stock Media ──
        {"id": "unsplash", "name": "Unsplash", "type": "stock_media", "icon": "📷",
         "description": "Free stock photos — 50 req/hr (free tier)", "free": True,
         "category": "Media & Design", "docs_url": "https://unsplash.com/developers"},
        {"id": "pexels", "name": "Pexels", "type": "stock_media", "icon": "🎬",
         "description": "Free stock photos & videos — 200 req/hr", "free": True,
         "category": "Media & Design", "docs_url": "https://www.pexels.com/api/"},
        {"id": "pixabay", "name": "Pixabay", "type": "stock_media", "icon": "🖼️",
         "description": "Free images, vectors, illustrations & videos", "free": True,
         "category": "Media & Design", "docs_url": "https://pixabay.com/service/about/api/"},
        {"id": "tenor", "name": "Tenor GIFs", "type": "stock_media", "icon": "🎭",
         "description": "GIF search engine (Google)", "free": True,
         "category": "Media & Design", "docs_url": "https://developers.google.com/tenor/guides/quickstart"},

        # ── Content Generation AI ──
        {"id": "groq", "name": "Groq AI", "type": "ai_content", "icon": "⚡",
         "description": "Free LLM inference (Llama, Mixtral) — 30 req/min", "free": True,
         "category": "AI & Content", "docs_url": "https://console.groq.com/docs"},
        {"id": "openai", "name": "OpenAI", "type": "ai_content", "icon": "🤖",
         "description": "GPT models for content generation", "free": False,
         "category": "AI & Content", "docs_url": "https://platform.openai.com/docs"},
        {"id": "together", "name": "Together AI", "type": "ai_content", "icon": "🔮",
         "description": "Open-source model inference", "free": True,
         "category": "AI & Content", "docs_url": "https://docs.together.ai/docs/quickstart"},
        {"id": "huggingface", "name": "Hugging Face", "type": "ai_content", "icon": "🤗",
         "description": "100K+ models, free inference API", "free": True,
         "category": "AI & Content", "docs_url": "https://huggingface.co/docs/api-inference/en/index"},
        {"id": "elevenlabs", "name": "ElevenLabs", "type": "ai_content", "icon": "🎙️",
         "description": "AI text-to-speech (10K chars/mo free)", "free": True,
         "category": "AI & Content", "docs_url": "https://elevenlabs.io/docs"},

        # ── Social Media ──
        {"id": "facebook", "name": "Facebook Page", "type": "social_media", "icon": "📘",
         "description": "Post to Facebook Pages, manage insights", "free": True,
         "category": "Social Media", "docs_url": "https://developers.facebook.com/docs/pages/"},
        {"id": "twitter", "name": "X (Twitter)", "type": "social_media", "icon": "🐦",
         "description": "Post tweets, read timeline (free tier: 1500 posts/mo)", "free": True,
         "category": "Social Media", "docs_url": "https://developer.twitter.com/en/docs/twitter-api"},
        {"id": "linkedin", "name": "LinkedIn", "type": "social_media", "icon": "💼",
         "description": "Share on LinkedIn, company pages", "free": True,
         "category": "Social Media", "docs_url": "https://developer.linkedin.com/docs"},
        {"id": "instagram", "name": "Instagram", "type": "social_media", "icon": "📸",
         "description": "Instagram Basic Display API, content posting", "free": True,
         "category": "Social Media", "docs_url": "https://developers.facebook.com/docs/instagram-basic-display-api/"},
        {"id": "youtube", "name": "YouTube", "type": "social_media", "icon": "▶️",
         "description": "YouTube Data API v3 (10K units/day free)", "free": True,
         "category": "Social Media", "docs_url": "https://developers.google.com/youtube/v3"},
        {"id": "pinterest", "name": "Pinterest", "type": "social_media", "icon": "📌",
         "description": "Pin content, manage boards", "free": True,
         "category": "Social Media", "docs_url": "https://developers.pinterest.com/docs/getting-started/"},
        {"id": "tiktok", "name": "TikTok", "type": "social_media", "icon": "🎵",
         "description": "TikTok API for content posting", "free": True,
         "category": "Social Media", "docs_url": "https://developers.tiktok.com/"},

        # ── Ad Campaigns ──
        {"id": "meta_ads", "name": "Meta Ads", "type": "advertising", "icon": "📊",
         "description": "Facebook & Instagram ad campaigns", "free": True,
         "category": "Advertising", "docs_url": "https://developers.facebook.com/docs/marketing-apis/"},
        {"id": "google_ads", "name": "Google Ads", "type": "advertising", "icon": "🔍",
         "description": "Google Search & Display advertising", "free": True,
         "category": "Advertising", "docs_url": "https://developers.google.com/google-ads/api/docs/start"},
        {"id": "linkedin_ads", "name": "LinkedIn Ads", "type": "advertising", "icon": "📈",
         "description": "LinkedIn sponsored content & ads", "free": True,
         "category": "Advertising", "docs_url": "https://developer.linkedin.com/docs/marketing/ads"},

        # ── Productivity & Office ──
        {"id": "microsoft_graph", "name": "Microsoft 365", "type": "productivity", "icon": "📄",
         "description": "Office 365, Excel, Word, Outlook, OneDrive APIs", "free": True,
         "category": "Productivity", "docs_url": "https://learn.microsoft.com/en-us/graph/"},
        {"id": "google_drive", "name": "Google Drive", "type": "productivity", "icon": "📁",
         "description": "Google Docs, Sheets, Drive API", "free": True,
         "category": "Productivity", "docs_url": "https://developers.google.com/drive"},

        # ── Communication ──
        {"id": "slack", "name": "Slack", "type": "communication", "icon": "💬",
         "description": "Slack messaging & notifications", "free": True,
         "category": "Communication", "docs_url": "https://api.slack.com/"},
        {"id": "discord", "name": "Discord", "type": "communication", "icon": "🎮",
         "description": "Discord bot & webhook integration", "free": True,
         "category": "Communication", "docs_url": "https://discord.com/developers/docs"},
        {"id": "telegram", "name": "Telegram", "type": "communication", "icon": "✈️",
         "description": "Telegram Bot API", "free": True,
         "category": "Communication", "docs_url": "https://core.telegram.org/bots/api"},
        {"id": "twilio", "name": "Twilio", "type": "communication", "icon": "📞",
         "description": "SMS, WhatsApp, Voice APIs", "free": False,
         "category": "Communication", "docs_url": "https://www.twilio.com/docs"},
        {"id": "sendgrid", "name": "SendGrid", "type": "communication", "icon": "📧",
         "description": "Email delivery (100 emails/day free)", "free": True,
         "category": "Communication", "docs_url": "https://docs.sendgrid.com/"},

        # ── Data & Analytics ──
        {"id": "openweather", "name": "OpenWeather", "type": "data", "icon": "🌤️",
         "description": "Weather data (1000 calls/day free)", "free": True,
         "category": "Data & Analytics", "docs_url": "https://openweathermap.org/api"},
        {"id": "newsapi", "name": "News API", "type": "data", "icon": "📰",
         "description": "News headlines & articles (100 req/day free)", "free": True,
         "category": "Data & Analytics", "docs_url": "https://newsapi.org/docs"},
        {"id": "google_maps", "name": "Google Maps", "type": "data", "icon": "🗺️",
         "description": "Maps, geocoding, places ($200/mo free credit)", "free": True,
         "category": "Data & Analytics", "docs_url": "https://developers.google.com/maps"},

        # ── Developer Tools ──
        {"id": "github", "name": "GitHub", "type": "developer", "icon": "🐙",
         "description": "GitHub API — repos, issues, PRs, actions", "free": True,
         "category": "Developer Tools", "docs_url": "https://docs.github.com/en/rest"},
        {"id": "gitlab", "name": "GitLab", "type": "developer", "icon": "🦊",
         "description": "GitLab API — repos, CI/CD, issues", "free": True,
         "category": "Developer Tools", "docs_url": "https://docs.gitlab.com/ee/api/"},

        # ── Marketing & CRM ──
        {"id": "mailchimp", "name": "Mailchimp", "type": "marketing", "icon": "🐵",
         "description": "Email marketing, audiences, campaigns", "free": True,
         "category": "Marketing & CRM", "docs_url": "https://mailchimp.com/developer/"},
        {"id": "hubspot", "name": "HubSpot", "type": "marketing", "icon": "🔄",
         "description": "CRM, marketing, sales hub APIs", "free": True,
         "category": "Marketing & CRM", "docs_url": "https://developers.hubspot.com/"},
        {"id": "stripe", "name": "Stripe", "type": "payments", "icon": "💳",
         "description": "Payment processing, subscriptions", "free": False,
         "category": "Marketing & CRM", "docs_url": "https://stripe.com/docs/api"},
    ]


def save_config(
    identity_id: str,
    provider: str,
    config_value: str | None = None,
    config_json: dict | None = None,
    label: str = "",
) -> dict[str, Any]:
    """Save or update an API key / config for a provider."""
    cfg = IntegrationConfig.query.filter_by(
        identity_id=identity_id, provider=provider
    ).first()

    if cfg:
        if config_value is not None:
            cfg.config_value = config_value
        if config_json is not None:
            cfg.config_json = config_json
        cfg.label = label or cfg.label
        cfg.is_active = True
    else:
        cfg = IntegrationConfig(
            identity_id=identity_id,
            provider=provider,
            config_value=config_value,
            config_json=config_json or {},
            label=label or provider,
        )
        db.session.add(cfg)

    db.session.commit()
    return cfg.to_dict(mask_secrets=True)


def get_config(identity_id: str, provider: str) -> dict[str, Any] | None:
    """Get a single config (masked secrets)."""
    cfg = IntegrationConfig.query.filter_by(
        identity_id=identity_id, provider=provider, is_active=True
    ).first()
    if not cfg:
        return None
    return cfg.to_dict(mask_secrets=True)


def get_config_value(identity_id: str, provider: str) -> str | None:
    """Get the raw config value (for internal use)."""
    cfg = IntegrationConfig.query.filter_by(
        identity_id=identity_id, provider=provider, is_active=True
    ).first()
    if not cfg:
        return None
    return cfg.config_value


def get_configs(identity_id: str) -> list[dict[str, Any]]:
    """Get all integration configs for an identity."""
    cfgs = IntegrationConfig.query.filter_by(
        identity_id=identity_id
    ).all()
    return [c.to_dict(mask_secrets=True) for c in cfgs]


def remove_config(identity_id: str, provider: str) -> bool:
    """Remove an integration config."""
    cfg = IntegrationConfig.query.filter_by(
        identity_id=identity_id, provider=provider
    ).first()
    if not cfg:
        return False
    cfg.is_active = False
    db.session.commit()
    return True


# =========================================================================
# SOCIAL MEDIA SERVICE
# =========================================================================

def list_social_accounts(identity_id: str) -> list[dict[str, Any]]:
    """List linked social media accounts."""
    accounts = SocialAccount.query.filter_by(
        identity_id=identity_id, is_active=True
    ).all()
    return [a.to_dict() for a in accounts]


def save_social_account(
    identity_id: str,
    platform: str,
    account_name: str,
    account_id: str | None = None,
    access_token: str = "",
    refresh_token: str = "",
    profile_picture_url: str | None = None,
    profile_url: str | None = None,
    follower_count: int | None = None,
) -> dict[str, Any]:
    """Link a social media account."""
    acct = SocialAccount.query.filter_by(
        identity_id=identity_id, platform=platform, account_id=account_id
    ).first()

    if acct:
        acct.account_name = account_name
        acct.access_token = access_token or acct.access_token
        acct.refresh_token = refresh_token or acct.refresh_token
        acct.profile_picture_url = profile_picture_url or acct.profile_picture_url
        acct.profile_url = profile_url or acct.profile_url
        if follower_count is not None:
            acct.follower_count = follower_count
        acct.is_active = True
    else:
        acct = SocialAccount(
            identity_id=identity_id,
            platform=platform,
            account_name=account_name,
            account_id=account_id,
            access_token=access_token,
            refresh_token=refresh_token,
            profile_picture_url=profile_picture_url,
            profile_url=profile_url,
            follower_count=follower_count or 0,
        )
        db.session.add(acct)

    db.session.commit()
    return acct.to_dict()


def remove_social_account(account_id: int) -> bool:
    """Remove a linked social account."""
    acct = SocialAccount.query.get(account_id)
    if not acct:
        return False
    acct.is_active = False
    db.session.commit()
    return True


# =========================================================================
# SCHEDULED POSTS SERVICE
# =========================================================================

def list_scheduled_posts(
    identity_id: str,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List scheduled/published posts."""
    query = ScheduledPost.query.filter_by(identity_id=identity_id)
    if status:
        query = query.filter_by(status=status)
    posts = query.order_by(ScheduledPost.scheduled_at.desc().nullslast()).all()
    return [p.to_dict() for p in posts]


def create_scheduled_post(
    identity_id: str,
    platform: str,
    content: str,
    media_urls: list[str] | None = None,
    scheduled_at: datetime | None = None,
) -> dict[str, Any]:
    """Create a new scheduled post."""
    post = ScheduledPost(
        identity_id=identity_id,
        platform=platform,
        content=content,
        media_urls=media_urls or [],
        scheduled_at=scheduled_at,
        status="scheduled" if scheduled_at else "draft",
    )
    db.session.add(post)
    db.session.commit()
    return post.to_dict()


def update_scheduled_post(
    post_id: int,
    content: str | None = None,
    media_urls: list[str] | None = None,
    scheduled_at: datetime | None = None,
    status: str | None = None,
) -> dict[str, Any] | None:
    """Update a scheduled post."""
    post = ScheduledPost.query.get(post_id)
    if not post:
        return None
    if content is not None:
        post.content = content
    if media_urls is not None:
        post.media_urls = media_urls
    if scheduled_at is not None:
        post.scheduled_at = scheduled_at
    if status is not None:
        post.status = status
    db.session.commit()
    return post.to_dict()


def delete_scheduled_post(post_id: int) -> bool:
    """Delete a scheduled post."""
    post = ScheduledPost.query.get(post_id)
    if not post:
        return False
    db.session.delete(post)
    db.session.commit()
    return True


# =========================================================================
# AD CAMPAIGN SERVICE
# =========================================================================

def list_ad_campaigns(
    identity_id: str,
    platform: str | None = None,
) -> list[dict[str, Any]]:
    """List ad campaigns."""
    query = AdCampaign.query.filter_by(identity_id=identity_id)
    if platform:
        query = query.filter_by(platform=platform)
    campaigns = query.order_by(AdCampaign.created_at.desc()).all()
    return [c.to_dict() for c in campaigns]


def create_ad_campaign(
    identity_id: str,
    platform: str,
    campaign_name: str,
    campaign_objective: str = "awareness",
    budget: float | None = None,
    budget_type: str = "daily",
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    targeting: dict | None = None,
    creative: dict | None = None,
) -> dict[str, Any]:
    """Create a new ad campaign."""
    campaign = AdCampaign(
        identity_id=identity_id,
        platform=platform,
        campaign_name=campaign_name,
        campaign_objective=campaign_objective,
        budget=budget,
        budget_type=budget_type,
        start_date=start_date,
        end_date=end_date,
        targeting=targeting or {},
        creative=creative or {},
        status="draft",
    )
    db.session.add(campaign)
    db.session.commit()
    return campaign.to_dict()


def update_ad_campaign(
    campaign_id: int,
    data: dict[str, Any],
) -> dict[str, Any] | None:
    """Update an ad campaign."""
    campaign = AdCampaign.query.get(campaign_id)
    if not campaign:
        return None
    for key in ("campaign_name", "campaign_objective", "budget", "budget_type",
                 "start_date", "end_date", "targeting", "creative", "status",
                 "external_campaign_id", "performance_metrics", "error_message"):
        if key in data:
            setattr(campaign, key, data[key])
    db.session.commit()
    return campaign.to_dict()


def delete_ad_campaign(campaign_id: int) -> bool:
    """Delete an ad campaign."""
    campaign = AdCampaign.query.get(campaign_id)
    if not campaign:
        return False
    db.session.delete(campaign)
    db.session.commit()
    return True


# =========================================================================
# CONTENT GENERATION SERVICE
# =========================================================================

def list_content_generations(
    identity_id: str,
    content_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List content generation history."""
    query = ContentGeneration.query.filter_by(identity_id=identity_id)
    if content_type:
        query = query.filter_by(content_type=content_type)
    items = query.order_by(ContentGeneration.created_at.desc()).limit(limit).all()
    return [i.to_dict() for i in items]


def save_content_generation(
    identity_id: str,
    content_type: str,
    prompt: str,
    generated_content: str | None = None,
    platform: str | None = None,
    tone: str = "professional",
    target_audience: str | None = None,
    word_count: int | None = None,
    ai_model: str = "groq",
) -> dict[str, Any]:
    """Save a content generation record."""
    gen = ContentGeneration(
        identity_id=identity_id,
        content_type=content_type,
        prompt=prompt,
        generated_content=generated_content,
        platform=platform,
        tone=tone,
        target_audience=target_audience,
        word_count=word_count,
        ai_model=ai_model,
    )
    db.session.add(gen)
    db.session.commit()
    return gen.to_dict()


def toggle_favorite_content(content_id: int) -> dict[str, Any] | None:
    """Toggle favorite status on a content generation."""
    gen = ContentGeneration.query.get(content_id)
    if not gen:
        return None
    gen.is_favorited = not gen.is_favorited
    db.session.commit()
    return gen.to_dict()


def delete_content_generation(content_id: int) -> bool:
    """Delete a content generation record."""
    gen = ContentGeneration.query.get(content_id)
    if not gen:
        return False
    db.session.delete(gen)
    db.session.commit()
    return True


def save_content_history(
    identity_id: str,
    content_type: str,
    label: str,
    content: str,
    platform: str | None = None,
    tone: str = "professional",
) -> dict[str, Any]:
    """Save arbitrary content to history (without regenerating)."""
    gen = ContentGeneration(
        identity_id=identity_id,
        content_type=content_type,
        prompt=label,
        generated_content=content,
        platform=platform,
        tone=tone,
        word_count=len(content.split()) if content else 0,
    )
    db.session.add(gen)
    db.session.commit()
    return gen.to_dict()


def update_content_generation(content_id: int, content: str) -> dict[str, Any] | None:
    """Update the generated content of an existing record."""
    gen = ContentGeneration.query.get(content_id)
    if not gen:
        return None
    gen.generated_content = content
    gen.word_count = len(content.split()) if content else 0
    db.session.commit()
    return gen.to_dict()


# =========================================================================
# CONTENT GENERATION AI (uses SHUNYA AI provider chain)
# =========================================================================

def generate_content(
    prompt: str,
    content_type: str = "blog_post",
    tone: str = "professional",
    platform: str | None = None,
    target_audience: str | None = None,
    word_count: int = 300,
    additional_instructions: str = "",
) -> dict[str, Any]:
    """Generate content using the SHUNYA AI provider chain.

    Returns: { "success": bool, "content": str, "error": str | None }
    """
    system_prompts = {
        "blog_post": "You are a professional blog writer. Write engaging, SEO-optimized blog content.",
        "social_post": "You are a social media content strategist. Write platform-optimized social posts.",
        "ad_copy": "You are an advertising copywriter. Write persuasive ad copy that converts.",
        "email": "You are an email marketing specialist. Write compelling email campaigns.",
        "landing_page": "You are a conversion copywriter. Write landing page content that drives action.",
        "product_desc": "You are an e-commerce copywriter. Write compelling product descriptions.",
        "seo_meta": "You are an SEO specialist. Write meta titles, descriptions, and keywords.",
        "press_release": "You are a PR professional. Write professional press releases.",
        "newsletter": "You are a newsletter editor. Write engaging newsletter content.",
        "script": "You are a script writer. Write engaging video/audio scripts.",
        "caption": "You are a social media caption writer. Write short, catchy captions.",
        "reply": "You are a customer communication specialist. Write professional replies.",
    }

    system_prompt = system_prompts.get(content_type, system_prompts["blog_post"])

    tone_guidance = {
        "professional": "Write in a professional, authoritative tone.",
        "casual": "Write in a friendly, conversational tone.",
        "humorous": "Write with a touch of humor and wit.",
        "inspirational": "Write in an uplifting, motivational tone.",
        "urgent": "Write with a sense of urgency and importance.",
        "luxury": "Write in an elegant, premium tone.",
        "technical": "Write with technical precision and detail.",
        "storytelling": "Write as a compelling narrative or story.",
    }

    tone_instruction = tone_guidance.get(tone, tone_guidance["professional"])

    full_prompt = f"""Content Type: {content_type.replace('_', ' ').title()}
Tone: {tone_instruction}
Target Length: ~{word_count} words
{f'Platform: {platform}' if platform else ''}
{f'Target Audience: {target_audience}' if target_audience else ''}
{f'Additional Instructions: {additional_instructions}' if additional_instructions else ''}

Topic/Task: {prompt}

Generate the content now:"""

    try:
        # Try using the SHUNYA AI provider chain directly
        from app.ai.provider import resolve_provider
        provider = resolve_provider()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt},
        ]
        result = provider.complete(
            messages=messages,
            temperature=0.7,
            max_tokens=min(word_count * 4, 2048),
        )
        if result and result.get("content"):
            return {"success": True, "content": result["content"], "error": None}
        if result and result.get("finish_reason") == "error":
            return {"success": False, "content": None, "error": result.get("error", "Provider error")}
        return {"success": False, "content": None, "error": "AI provider returned empty response"}
    except ImportError:
        # Fallback: try the AI chat route
        try:
            import requests
            resp = requests.post(
                "http://localhost:5001/api/v1/ai/chat",
                json={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": min(word_count * 4, 2048),
                },
                timeout=30,
            )
            if resp.ok:
                data = resp.json()
                content = data.get("content") or data.get("response") or data.get("message", "")
                if content:
                    return {"success": True, "content": content, "error": None}
            return {"success": False, "content": None, "error": f"AI service error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "content": None, "error": str(e)}
    except Exception as e:
        return {"success": False, "content": None, "error": str(e)}


# =========================================================================
# FREE API PROXY SERVICE
# =========================================================================

def proxy_unsplash_search(query: str, api_key: str, per_page: int = 20) -> list[dict[str, Any]]:
    """Proxy search to Unsplash API."""
    import requests
    params = {"query": query, "per_page": min(per_page, 30)}
    resp = requests.get(
        "https://api.unsplash.com/search/photos",
        headers={"Authorization": f"Client-ID {api_key}"},
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "id": r["id"],
            "thumb_url": r["urls"]["thumb"],
            "regular_url": r["urls"]["regular"],
            "full_url": r["urls"]["raw"],
            "alt": r.get("alt_description", ""),
            "author": r["user"]["name"],
            "author_url": r["user"]["links"]["html"],
            "download_url": r["links"]["download"],
            "width": r["width"],
            "height": r["height"],
        }
        for r in data.get("results", [])
    ]


def proxy_pexels_search(query: str, api_key: str, per_page: int = 20) -> list[dict[str, Any]]:
    """Proxy search to Pexels API."""
    import requests
    params = {"query": query, "per_page": min(per_page, 30)}
    resp = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key},
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "id": str(p["id"]),
            "thumb_url": p["src"]["tiny"],
            "regular_url": p["src"]["medium"],
            "full_url": p["src"]["original"],
            "alt": p.get("alt", ""),
            "author": p["photographer"],
            "author_url": p["photographer_url"],
            "download_url": p["url"],
            "width": p["width"],
            "height": p["height"],
        }
        for p in data.get("photos", [])
    ]


# =========================================================================
# Media Cache Helpers
# =========================================================================

import hashlib
from datetime import timedelta


def get_cached_media(provider: str, query: str, max_age_minutes: int = 60) -> list[dict[str, Any]] | None:
    """Get cached media results if they exist and are fresh."""
    qhash = hashlib.sha256(query.lower().strip().encode("utf-8")).hexdigest()
    expire_before = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
    cached = CachedMedia.query.filter_by(
        provider=provider, query_hash=qhash
    ).filter(CachedMedia.created_at >= expire_before).first()
    if cached:
        return cached.response_data
    return None


def set_cached_media(provider: str, query: str, data: list[dict[str, Any]], count: int, ttl_minutes: int = 60) -> None:
    """Store media results in cache."""
    qhash = hashlib.sha256(query.lower().strip().encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    # Remove old cache entry for same query
    CachedMedia.query.filter_by(provider=provider, query_hash=qhash).delete()
    cached = CachedMedia(
        provider=provider,
        query_hash=qhash,
        query=query,
        response_data=data,
        total_count=count,
        expires_at=expires_at,
    )
    db.session.add(cached)
    db.session.commit()


# =========================================================================
# Proxy: Pixabay
# =========================================================================


def proxy_pixabay_search(query: str, api_key: str, per_page: int = 20) -> list[dict[str, Any]]:
    """Proxy search to Pixabay API."""
    import requests
    params = {"key": api_key, "q": query, "per_page": min(per_page, 30), "safesearch": "true"}
    resp = requests.get("https://pixabay.com/api/", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "id": str(h["id"]),
            "thumb_url": h["webformatURL"],
            "regular_url": h["webformatURL"],
            "full_url": h["largeImageURL"],
            "alt": h.get("tags", ""),
            "author": h.get("user", ""),
            "author_url": f"https://pixabay.com/users/{h['user']}/",
            "download_url": h.get("pageURL", ""),
            "width": h.get("imageWidth", 0),
            "height": h.get("imageHeight", 0),
        }
        for h in data.get("hits", [])
    ]


# =========================================================================
# Proxy: Tenor (GIFs)
# =========================================================================


def proxy_tenor_search(query: str, api_key: str, limit: int = 20) -> list[dict[str, Any]]:
    """Proxy search to Tenor GIF API."""
    import requests
    params = {
        "key": api_key,
        "q": query,
        "limit": min(limit, 30),
        "media_filter": "gif,tinygif,mediumgif,nanomp4",
    }
    resp = requests.get("https://tenor.googleapis.com/v2/search", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "id": r["id"],
            "thumb_url": r.get("media_formats", {}).get("tinygif", {}).get("url", ""),
            "regular_url": r.get("media_formats", {}).get("mediumgif", {}).get("url", ""),
            "full_url": r.get("media_formats", {}).get("gif", {}).get("url", ""),
            "alt": r.get("content_description") or r.get("title", ""),
            "author": "",
            "author_url": "",
            "download_url": r.get("itemurl") or r.get("url", ""),
            "width": r.get("media_formats", {}).get("gif", {}).get("dims", [200, 200])[0],
            "height": r.get("media_formats", {}).get("gif", {}).get("dims", [200, 200])[1],
        }
        for r in data.get("results", [])
    ]


# =========================================================================
# Proxy: News API
# =========================================================================


def proxy_news_search(query: str, api_key: str) -> list[dict[str, Any]]:
    """Proxy search to News API."""
    import requests
    params = {"q": query, "apiKey": api_key, "pageSize": 20, "language": "en"}
    resp = requests.get("https://newsapi.org/v2/everything", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "title": a["title"],
            "description": a.get("description", ""),
            "url": a["url"],
            "url_to_image": a.get("urlToImage", ""),
            "source": a["source"]["name"],
            "published_at": a.get("publishedAt", ""),
            "author": a.get("author", ""),
        }
        for a in data.get("articles", [])
    ]


def proxy_openweather(city: str, api_key: str) -> dict[str, Any] | None:
    """Proxy query to OpenWeather API."""
    import requests
    params = {"q": city, "appid": api_key, "units": "metric"}
    resp = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=15)
    if not resp.ok:
        return None
    data = resp.json()
    return {
        "city": data.get("name", city),
        "country": data.get("sys", {}).get("country", ""),
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "wind_speed": data["wind"]["speed"],
        "visibility": data.get("visibility", 0),
    }


def proxy_youtube_search(query: str, api_key: str) -> list[dict[str, Any]]:
    """Proxy search to YouTube Data API."""
    import requests
    params = {"q": query, "key": api_key, "part": "snippet", "maxResults": 20, "type": "video"}
    resp = requests.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"].get("description", ""),
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
            "channel": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"],
        }
        for item in data.get("items", [])
        if item.get("id", {}).get("kind") == "youtube#video"
    ]


def proxy_github_search(query: str, api_key: str) -> list[dict[str, Any]]:
    """Proxy search to GitHub API."""
    import requests
    headers = {"Accept": "application/vnd.github.v3+json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    params = {"q": query, "per_page": 20, "sort": "stars", "order": "desc"}
    resp = requests.get("https://api.github.com/search/repositories", headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "id": r["id"],
            "name": r["full_name"],
            "description": r.get("description", ""),
            "url": r["html_url"],
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "language": r.get("language", ""),
            "owner": r["owner"]["login"],
            "owner_avatar": r["owner"]["avatar_url"],
        }
        for r in data.get("items", [])
    ]


def proxy_microsoft_graph(
    access_token: str,
    endpoint: str = "me",
    method: str = "GET",
    data: dict | None = None,
) -> dict[str, Any]:
    """Proxy request to Microsoft Graph API."""
    import requests
    url = f"https://graph.microsoft.com/v1.0/{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    if method == "GET":
        resp = requests.get(url, headers=headers, timeout=15)
    elif method == "POST":
        resp = requests.post(url, headers=headers, json=data or {}, timeout=15)
    elif method == "PATCH":
        resp = requests.patch(url, headers=headers, json=data or {}, timeout=15)
    else:
        return {"success": False, "error": f"Unsupported method: {method}"}

    if resp.ok:
        return {"success": True, "data": resp.json()}
    return {"success": False, "error": f"Graph API error ({resp.status_code}): {resp.text}"}


# =========================================================================
# PLATFORM-SPECIFIC SOCIAL POSTING (simulated — no real API keys)
# =========================================================================

def simulate_platform_post(platform: str, content: str) -> dict[str, Any]:
    """Simulate posting to a social platform (for demo/development).

    Real integration requires OAuth tokens for each platform.
    """
    platform_urls = {
        "twitter": "https://twitter.com/intent/tweet?text=",
        "facebook": "https://www.facebook.com/",
        "linkedin": "https://www.linkedin.com/feed/",
        "instagram": "https://www.instagram.com/",
        "pinterest": "https://www.pinterest.com/pin/create/button/",
        "tiktok": "https://www.tiktok.com/upload/",
    }
    url = platform_urls.get(platform, "https://" + platform + ".com")
    return {
        "success": True,
        "platform": platform,
        "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
        "post_url": url,
        "simulated": True,
        "message": f"Posted to {platform} (simulated — connect real account for actual posting)",
    }