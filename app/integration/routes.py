"""SHUNYA M6 — Connected Business Routes.

Integration settings, notification management, API key management,
social media, ad campaigns, content generation, and proxy services.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session

from app.integration.service import (
    create_ad_campaign,
    create_notification,
    create_scheduled_post,
    delete_ad_campaign,
    delete_content_generation,
    delete_scheduled_post,
    generate_content,
    get_config,
    get_configs,
    get_config_value,
    get_connections,
    get_notifications,
    get_preferences,
    get_unread_count,
    list_ad_campaigns,
    list_content_generations,
    list_providers,
    list_scheduled_posts,
    list_social_accounts,
    mark_all_as_read,
    mark_as_read,
    proxy_github_search,
    proxy_microsoft_graph,
    proxy_news_search,
    proxy_openweather,
    proxy_pexels_search,
    proxy_pixabay_search,
    proxy_tenor_search,
    proxy_unsplash_search,
    proxy_youtube_search,
    remove_config,
    remove_connection,
    remove_social_account,
    save_config,
    save_connection,
    save_content_generation,
    save_content_history,
    save_social_account,
    simulate_platform_post,
    toggle_favorite_content,
    update_ad_campaign,
    update_content_generation,
    update_preferences,
    update_scheduled_post,
)

logger = logging.getLogger(__name__)

integration_bp = Blueprint("integration", __name__, url_prefix="/api/v1/integration")


def _founder_required() -> bool:
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    return bool(user_id and identity_id)


def _get_identity_id() -> str | None:
    return session.get("identity_id")


# =========================================================================
# NOTIFICATIONS
# =========================================================================

@integration_bp.route("/notifications", methods=["GET"])
def api_get_notifications():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    notifs = get_notifications(identity_id=identity_id, unread_only=unread_only)
    return jsonify({"success": True, "data": notifs, "count": len(notifs)})


@integration_bp.route("/notifications/unread-count", methods=["GET"])
def api_unread_count():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    count = get_unread_count(identity_id=identity_id)
    return jsonify({"success": True, "data": {"unread_count": count}})


@integration_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
def api_mark_read(notif_id: int):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    result = mark_as_read(notif_id)
    return jsonify({"success": result})


@integration_bp.route("/notifications/read-all", methods=["POST"])
def api_mark_all_read():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    count = mark_all_as_read(identity_id=identity_id)
    return jsonify({"success": True, "data": {"marked_read": count}})


# =========================================================================
# NOTIFICATION PREFERENCES
# =========================================================================

@integration_bp.route("/notifications/preferences", methods=["GET"])
def api_get_preferences():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    return jsonify({"success": True, "data": get_preferences(identity_id)})


@integration_bp.route("/notifications/preferences", methods=["PUT"])
def api_update_preferences():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    data = request.get_json(silent=True) or {}
    result = update_preferences(
        identity_id=identity_id,
        email_notifications=data.get("email_notifications"),
        in_app_notifications=data.get("in_app_notifications"),
        digest_frequency=data.get("digest_frequency"),
        quiet_hours_start=data.get("quiet_hours_start"),
        quiet_hours_end=data.get("quiet_hours_end"),
    )
    return jsonify({"success": True, "data": result})


# =========================================================================
# INTEGRATION CONNECTIONS (OAuth)
# =========================================================================

@integration_bp.route("/connections", methods=["GET"])
def api_get_connections():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    return jsonify({"success": True, "data": get_connections(identity_id)})


@integration_bp.route("/connections/<provider>", methods=["DELETE"])
def api_remove_connection(provider: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    result = remove_connection(identity_id=identity_id, provider=provider)
    return jsonify({"success": result})


# =========================================================================
# INTEGRATION CONFIGS (API Keys)
# =========================================================================

@integration_bp.route("/providers", methods=["GET"])
def api_list_providers():
    """List all available integration providers."""
    return jsonify({
        "success": True,
        "data": list_providers(),
    })


@integration_bp.route("/configs", methods=["GET"])
def api_get_configs():
    """Get all API key configs for the current user."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    return jsonify({"success": True, "data": get_configs(identity_id)})


@integration_bp.route("/configs/<provider>", methods=["GET"])
def api_get_config(provider: str):
    """Get a single provider config."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    cfg = get_config(identity_id, provider)
    if not cfg:
        return jsonify({"success": False, "error": "Config not found"}), 404
    return jsonify({"success": True, "data": cfg})


@integration_bp.route("/configs/<provider>", methods=["PUT"])
def api_save_config(provider: str):
    """Save or update an API key config."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    data = request.get_json(silent=True) or {}
    result = save_config(
        identity_id=identity_id,
        provider=provider,
        config_value=data.get("api_key") or data.get("config_value"),
        config_json=data.get("config_json"),
        label=data.get("label", ""),
    )
    return jsonify({"success": True, "data": result})


@integration_bp.route("/configs/<provider>", methods=["DELETE"])
def api_remove_config(provider: str):
    """Remove an API key config."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    result = remove_config(identity_id, provider)
    return jsonify({"success": result})


# =========================================================================
# SOCIAL MEDIA ACCOUNTS
# =========================================================================

@integration_bp.route("/social/accounts", methods=["GET"])
def api_list_social_accounts():
    """List linked social media accounts."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    return jsonify({"success": True, "data": list_social_accounts(identity_id)})


@integration_bp.route("/social/accounts", methods=["POST"])
def api_link_social_account():
    """Link a social media account."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    data = request.get_json(silent=True) or {}
    result = save_social_account(
        identity_id=identity_id,
        platform=data.get("platform", ""),
        account_name=data.get("account_name", ""),
        account_id=data.get("account_id"),
        access_token=data.get("access_token", ""),
        refresh_token=data.get("refresh_token", ""),
        profile_picture_url=data.get("profile_picture_url"),
        profile_url=data.get("profile_url"),
        follower_count=data.get("follower_count"),
    )
    return jsonify({"success": True, "data": result})


@integration_bp.route("/social/accounts/<int:account_id>", methods=["DELETE"])
def api_unlink_social_account(account_id: int):
    """Unlink a social media account."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    result = remove_social_account(account_id)
    return jsonify({"success": result})


# =========================================================================
# SCHEDULED POSTS
# =========================================================================

@integration_bp.route("/social/posts", methods=["GET"])
def api_list_posts():
    """List scheduled/published posts."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    status = request.args.get("status")
    return jsonify({
        "success": True,
        "data": list_scheduled_posts(identity_id, status=status),
    })


@integration_bp.route("/social/posts", methods=["POST"])
def api_create_post():
    """Create a scheduled post."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    data = request.get_json(silent=True) or {}
    scheduled_at = None
    if data.get("scheduled_at"):
        try:
            scheduled_at = datetime.fromisoformat(data["scheduled_at"])
        except (ValueError, TypeError):
            pass
    result = create_scheduled_post(
        identity_id=identity_id,
        platform=data.get("platform", ""),
        content=data.get("content", ""),
        media_urls=data.get("media_urls", []),
        scheduled_at=scheduled_at,
    )
    return jsonify({"success": True, "data": result})


@integration_bp.route("/social/posts/<int:post_id>", methods=["PUT"])
def api_update_post(post_id: int):
    """Update a scheduled post."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    scheduled_at = None
    if data.get("scheduled_at"):
        try:
            scheduled_at = datetime.fromisoformat(data["scheduled_at"])
        except (ValueError, TypeError):
            pass
    result = update_scheduled_post(
        post_id=post_id,
        content=data.get("content"),
        media_urls=data.get("media_urls"),
        scheduled_at=scheduled_at,
        status=data.get("status"),
    )
    if not result:
        return jsonify({"success": False, "error": "Post not found"}), 404
    return jsonify({"success": True, "data": result})


@integration_bp.route("/social/posts/<int:post_id>", methods=["DELETE"])
def api_delete_post(post_id: int):
    """Delete a scheduled post."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    result = delete_scheduled_post(post_id)
    return jsonify({"success": result})


@integration_bp.route("/social/posts/<int:post_id>/publish", methods=["POST"])
def api_publish_post(post_id: int):
    """Publish a post to its social platform (simulated)."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.integration.models import ScheduledPost
    post = ScheduledPost.query.get(post_id)
    if not post:
        return jsonify({"success": False, "error": "Post not found"}), 404

    result = simulate_platform_post(post.platform, post.content)
    post.status = "published"
    post.published_at = datetime.now(timezone.utc)
    from app import db
    db.session.commit()

    return jsonify({"success": True, "data": {
        **result,
        "post_id": post_id,
        "status": "published",
    }})


# =========================================================================
# AD CAMPAIGNS
# =========================================================================

@integration_bp.route("/ads", methods=["GET"])
def api_list_ads():
    """List ad campaigns."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    platform = request.args.get("platform")
    return jsonify({
        "success": True,
        "data": list_ad_campaigns(identity_id, platform=platform),
    })


@integration_bp.route("/ads", methods=["POST"])
def api_create_ad():
    """Create an ad campaign."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    data = request.get_json(silent=True) or {}

    start_date = None
    end_date = None
    if data.get("start_date"):
        try:
            start_date = datetime.fromisoformat(data["start_date"])
        except (ValueError, TypeError):
            pass
    if data.get("end_date"):
        try:
            end_date = datetime.fromisoformat(data["end_date"])
        except (ValueError, TypeError):
            pass

    result = create_ad_campaign(
        identity_id=identity_id,
        platform=data.get("platform", "meta_ads"),
        campaign_name=data.get("campaign_name", ""),
        campaign_objective=data.get("campaign_objective", "awareness"),
        budget=data.get("budget"),
        budget_type=data.get("budget_type", "daily"),
        start_date=start_date,
        end_date=end_date,
        targeting=data.get("targeting"),
        creative=data.get("creative"),
    )
    return jsonify({"success": True, "data": result})


@integration_bp.route("/ads/<int:campaign_id>", methods=["PUT"])
def api_update_ad(campaign_id: int):
    """Update an ad campaign."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    result = update_ad_campaign(campaign_id, data)
    if not result:
        return jsonify({"success": False, "error": "Campaign not found"}), 404
    return jsonify({"success": True, "data": result})


@integration_bp.route("/ads/<int:campaign_id>", methods=["DELETE"])
def api_delete_ad(campaign_id: int):
    """Delete an ad campaign."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    result = delete_ad_campaign(campaign_id)
    return jsonify({"success": result})


# =========================================================================
# CONTENT GENERATION
# =========================================================================

@integration_bp.route("/content/generate", methods=["POST"])
def api_generate_content():
    """Generate AI content."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    data = request.get_json(silent=True) or {}

    prompt = data.get("prompt", "")
    content_type = data.get("content_type", "blog_post")
    tone = data.get("tone", "professional")
    platform = data.get("platform")
    target_audience = data.get("target_audience")
    word_count = data.get("word_count", 300)
    additional_instructions = data.get("additional_instructions", "")

    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400

    # Generate content via AI
    result = generate_content(
        prompt=prompt,
        content_type=content_type,
        tone=tone,
        platform=platform,
        target_audience=target_audience,
        word_count=word_count,
        additional_instructions=additional_instructions,
    )

    if result["success"]:
        content = result["content"]
        word_count_actual = len(content.split()) if content else 0
        # Save to history
        save_content_generation(
            identity_id=identity_id,
            content_type=content_type,
            prompt=prompt,
            generated_content=content,
            platform=platform,
            tone=tone,
            target_audience=target_audience,
            word_count=word_count_actual,
            ai_model="groq",
        )
        return jsonify({
            "success": True,
            "data": {
                "content": content,
                "word_count": word_count_actual,
                "content_type": content_type,
            },
        })
    else:
        return jsonify({"success": False, "error": result.get("error", "Generation failed")}), 500


@integration_bp.route("/content/history", methods=["GET"])
def api_content_history():
    """List content generation history."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    content_type = request.args.get("content_type")
    limit = request.args.get("limit", 50, type=int)
    return jsonify({
        "success": True,
        "data": list_content_generations(identity_id, content_type=content_type, limit=limit),
    })


@integration_bp.route("/content/history/<int:content_id>/favorite", methods=["POST"])
def api_toggle_favorite(content_id: int):
    """Toggle favorite on a content generation."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    result = toggle_favorite_content(content_id)
    if not result:
        return jsonify({"success": False, "error": "Content not found"}), 404
    return jsonify({"success": True, "data": result})


@integration_bp.route("/content/save", methods=["POST"])
def api_save_content():
    """Save generated content to history."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    data = request.get_json(silent=True) or {}
    title = data.get("title") or data.get("label") or data.get("prompt", "")
    content = data.get("content", "")
    if not content:
        return jsonify({"success": False, "error": "Content is required"}), 400
    # Map frontend types to backend content types
    content_type_map = {
        "blog": "blog_post",
        "social": "social_post",
        "marketing": "ad_copy",
        "blog_post": "blog_post",
        "social_post": "social_post",
        "ad_copy": "ad_copy",
        "marketing_copy": "ad_copy",
    }
    content_type = content_type_map.get(data.get("type") or data.get("content_type") or "blog", "blog_post")
    result = save_content_history(
        identity_id=identity_id,
        content_type=content_type,
        label=title,
        content=content,
        platform=data.get("platform"),
        tone=data.get("tone", "professional"),
    )
    return jsonify({"success": True, "data": result})


@integration_bp.route("/content/history/<int:content_id>", methods=["PUT"])
def api_update_content(content_id: int):
    """Update generated content of a saved record."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    content = data.get("content", "")
    if not content:
        return jsonify({"success": False, "error": "Content is required"}), 400
    result = update_content_generation(content_id, content)
    if not result:
        return jsonify({"success": False, "error": "Content not found"}), 404
    return jsonify({"success": True, "data": result})


@integration_bp.route("/content/history/<int:content_id>", methods=["DELETE"])
def api_delete_content(content_id: int):
    """Delete a content generation record."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    result = delete_content_generation(content_id)
    return jsonify({"success": result})


# =========================================================================
# PROXY SERVICES (Free API proxies)
# =========================================================================

@integration_bp.route("/proxy/unsplash", methods=["GET"])
def api_proxy_unsplash():
    """Proxy search to Unsplash API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    api_key = get_config_value(identity_id, "unsplash")
    if not api_key:
        return jsonify({"success": False, "error": "Unsplash API key not configured"}), 400
    try:
        results = proxy_unsplash_search(query, api_key)
        return jsonify({"success": True, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@integration_bp.route("/proxy/pexels", methods=["GET"])
def api_proxy_pexels():
    """Proxy search to Pexels API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    api_key = get_config_value(identity_id, "pexels")
    if not api_key:
        return jsonify({"success": False, "error": "Pexels API key not configured"}), 400
    try:
        results = proxy_pexels_search(query, api_key)
        return jsonify({"success": True, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@integration_bp.route("/proxy/pixabay", methods=["GET"])
def api_proxy_pixabay():
    """Proxy search to Pixabay API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    api_key = get_config_value(identity_id, "pixabay")
    if not api_key:
        return jsonify({"success": False, "error": "Pixabay API key not configured"}), 400
    try:
        results = proxy_pixabay_search(query, api_key)
        return jsonify({"success": True, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@integration_bp.route("/proxy/tenor", methods=["GET"])
def api_proxy_tenor():
    """Proxy search to Tenor GIF API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    api_key = get_config_value(identity_id, "tenor")
    if not api_key:
        return jsonify({"success": False, "error": "Tenor API key not configured"}), 400
    try:
        results = proxy_tenor_search(query, api_key)
        return jsonify({"success": True, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@integration_bp.route("/proxy/news", methods=["GET"])
def api_proxy_news():
    """Proxy search to News API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    api_key = get_config_value(identity_id, "newsapi")
    if not api_key:
        return jsonify({"success": False, "error": "News API key not configured"}), 400
    try:
        results = proxy_news_search(query, api_key)
        return jsonify({"success": True, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@integration_bp.route("/proxy/weather", methods=["GET"])
def api_proxy_weather():
    """Proxy query to OpenWeather API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    city = request.args.get("city", "")
    if not city:
        return jsonify({"success": False, "error": "City is required"}), 400
    api_key = get_config_value(identity_id, "openweather")
    if not api_key:
        return jsonify({"success": False, "error": "OpenWeather API key not configured"}), 400
    try:
        result = proxy_openweather(city, api_key)
        if not result:
            return jsonify({"success": False, "error": "City not found"}), 404
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@integration_bp.route("/proxy/youtube", methods=["GET"])
def api_proxy_youtube():
    """Proxy search to YouTube Data API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    api_key = get_config_value(identity_id, "youtube")
    if not api_key:
        return jsonify({"success": False, "error": "YouTube API key not configured"}), 400
    try:
        results = proxy_youtube_search(query, api_key)
        return jsonify({"success": True, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@integration_bp.route("/proxy/github", methods=["GET"])
def api_proxy_github():
    """Proxy search to GitHub API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    api_key = get_config_value(identity_id, "github")
    try:
        results = proxy_github_search(query, api_key or "")
        return jsonify({"success": True, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@integration_bp.route("/proxy/microsoft-graph", methods=["POST"])
def api_proxy_microsoft_graph():
    """Proxy request to Microsoft Graph API."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    data = request.get_json(silent=True) or {}
    endpoint = data.get("endpoint", "me")
    method = data.get("method", "GET")
    body = data.get("data")

    # Get the Microsoft Graph access token
    conn = get_connection_raw(identity_id, "microsoft_graph")
    if not conn or not conn.access_token:
        # Try the config
        cfg = get_config_value(identity_id, "microsoft_graph")
        if not cfg:
            return jsonify({"success": False, "error": "Microsoft 365 not connected"}), 400
        access_token = cfg
    else:
        access_token = conn.access_token

    try:
        result = proxy_microsoft_graph(access_token, endpoint, method, body)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


def get_connection_raw(identity_id: str, provider: str):
    """Get the raw IntegrationConnection object."""
    from app.integration.models import IntegrationConnection
    return IntegrationConnection.query.filter_by(
        identity_id=identity_id, provider=provider, is_active=True
    ).first()


# =========================================================================
# EMAILS (existing)
# =========================================================================

@integration_bp.route("/emails", methods=["GET"])
def api_list_emails():
    """List cached emails with pagination."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()
    limit = request.args.get("limit", 20, type=int)
    page = request.args.get("page", 1, type=int)
    limit = min(max(limit, 1), 100)
    page = max(page, 1)

    from app.integration.models import CachedEmail

    query = CachedEmail.query.filter_by(identity_id=identity_id).order_by(
        CachedEmail.received_at.desc().nullslast(),
        CachedEmail.created_at.desc(),
    )
    total = query.count()
    emails = query.offset((page - 1) * limit).limit(limit).all()

    data = []
    for e in emails:
        d = e.to_dict()
        d["is_read"] = e.is_processed
        data.append(d)

    return jsonify({
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
    })


@integration_bp.route("/emails/<int:email_id>", methods=["GET"])
def api_get_email(email_id: int):
    """Get a single cached email with full body text."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = _get_identity_id()

    from app.integration.models import CachedEmail

    email = CachedEmail.query.filter_by(
        id=email_id, identity_id=identity_id
    ).first()

    if not email:
        return jsonify({"success": False, "error": "Email not found"}), 404

    d = email.to_dict()
    d["body_text"] = email.body_text
    d["is_read"] = email.is_processed
    return jsonify({"success": True, "data": d})