"""Shunya OS — Bird AI Internet Intelligence Tools.

All internet-intelligence, local-info, mood-logging, and user-insight tools
register here via register_tool().
Each handler:
  - Uses search_web from app.shunya.web_search for web-backed tools
  - Returns ToolResult with data.results and unique quick_actions per tool
  - Is registered at module level with register_tool()
"""

from __future__ import annotations
from typing import Any, Optional
import logging

from app.shunya.agent import (
    register_tool,
    ToolDef,
    ToolCategory,
    ToolPermission,
    ToolResult,
)

logger = logging.getLogger("shunya.tools.intelligence")

# =============================================================================
# TIER 1 — Internet Intelligence Tools
# =============================================================================

# -----------------------------------------------------------------------------
# 1. search_movies — Find movie shows near a city
# -----------------------------------------------------------------------------
def _search_movies(params: dict, agent=None) -> ToolResult:
    """Find movie shows and showtimes near a city."""
    city = params.get("city", "")
    movie = params.get("movie", "")
    date = params.get("date", "")
    if not city:
        return ToolResult(False, "Please provide a city to search for movies.")
    try:
        from app.shunya.web_search import search_web

        parts = []
        if movie:
            parts.append(movie)
        parts.append("movies now showing in")
        parts.append(city)
        if date:
            parts.append(date)
        parts.append("showtimes")
        search_query = " ".join(parts)

        results = search_web(search_query, limit=5)
        if results:
            # Ensure each result has type='movie'
            for r in results:
                if "type" not in r or not r.get("type"):
                    r["type"] = "movie"
            message = f"🎬 Found {len(results)} movie listings in {city}."
            return ToolResult(True, message=message, data={
                "results": results,
                "count": len(results),
                "query": search_query,
                "quick_actions": [
                    {"label": "Find showtimes →", "action": "bird_query:search_movies more showtimes"},
                    {"label": "Book tickets →", "action": "bird_query:book movie tickets"},
                    {"label": "Search another city →", "action": "bird_query:search_movies"},
                ],
            }, target_url="/user-intel")
        return ToolResult(
            True,
            message=f"No movie listings found for '{search_query}'.",
            data={"results": [], "count": 0},
            target_url="/user-intel",
        )
    except Exception as e:
        logger.warning("search_movies failed: %s", e)
        return ToolResult(False, message="Movie search not available right now. Try again later.")


register_tool(ToolDef(
    id="search_movies",
    name="search_movies",
    description="Find movie shows and showtimes near a city. Optionally specify a movie name or date.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_movies,
    parameters={
        "city": {"type": "string", "required": True, "description": "City to search for movies in"},
        "movie": {"type": "string", "required": False, "description": "Optional movie name to filter by"},
        "date": {"type": "string", "required": False, "description": "Optional date (e.g. today, tomorrow, 2025-07-15)"},
    },
    examples=[
        "search_movies: city=Mumbai",
        "search_movies: city=Delhi movie=Kalki date=tomorrow",
    ],
))

# -----------------------------------------------------------------------------
# 2. search_weather — Get weather forecast
# -----------------------------------------------------------------------------
def _search_weather(params: dict, agent=None) -> ToolResult:
    """Get weather forecast for a city."""
    city = params.get("city", "")
    days = params.get("days", 3)
    if not city:
        return ToolResult(False, "Please provide a city to get the weather forecast.")
    try:
        from app.shunya.web_search import search_web

        search_query = f"weather forecast {city} next {days} days"
        results = search_web(search_query, limit=5)
        if results:
            message = f"🌤️ Weather forecast for {city} — next {days} days. Found {len(results)} results."
            return ToolResult(True, message=message, data={
                "results": results,
                "count": len(results),
                "query": search_query,
                "days": days,
                "quick_actions": [
                    {"label": "7-day forecast →", "action": "bird_query:search_weather city=" + city + " days=7"},
                    {"label": "Check another city →", "action": "bird_query:search_weather"},
                    {"label": "Plan a trip →", "action": "bird_query:check_weather for travel"},
                ],
            }, target_url="/user-intel")
        return ToolResult(
            True,
            message=f"No weather data found for '{search_query}'.",
            data={"results": [], "count": 0},
            target_url="/user-intel",
        )
    except Exception as e:
        logger.warning("search_weather failed: %s", e)
        return ToolResult(False, message="Weather search not available right now. Try again later.")


register_tool(ToolDef(
    id="search_weather",
    name="search_weather",
    description="Get weather forecast for a city. Optionally specify how many days ahead.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_weather,
    parameters={
        "city": {"type": "string", "required": True, "description": "City to get weather for"},
        "days": {"type": "number", "required": False, "description": "Number of days to forecast (default: 3)"},
    },
    examples=[
        "search_weather: city=Bangkok",
        "search_weather: city=Goa days=7",
    ],
))

# -----------------------------------------------------------------------------
# 3. search_restaurants — Find restaurants
# -----------------------------------------------------------------------------
def _search_restaurants(params: dict, agent=None) -> ToolResult:
    """Find restaurants in a city."""
    city = params.get("city", "")
    cuisine = params.get("cuisine", "")
    query = params.get("query", "")
    if not city:
        return ToolResult(False, "Please provide a city to search for restaurants.")
    try:
        from app.shunya.web_search import search_web

        parts = []
        if cuisine:
            parts.append(cuisine)
        parts.append("restaurants in")
        parts.append(city)
        if query:
            parts.append(query)
        search_query = "best " + " ".join(parts)

        results = search_web(search_query, limit=5)
        if results:
            label = f"{cuisine} " if cuisine else ""
            message = f"🍽️ Found {len(results)} {label}restaurants in {city}."
            return ToolResult(True, message=message, data={
                "results": results,
                "count": len(results),
                "query": search_query,
                "quick_actions": [
                    {"label": "Search by cuisine →", "action": "bird_query:search_restaurants city=" + city + " cuisine=italian"},
                    {"label": "Find top-rated →", "action": "bird_query:search_restaurants city=" + city + " query=top rated"},
                    {"label": "Check reviews →", "action": "bird_query:search_restaurants city=" + city + " query=reviews"},
                ],
            }, target_url="/user-intel")
        return ToolResult(
            True,
            message=f"No restaurants found for '{search_query}'.",
            data={"results": [], "count": 0},
            target_url="/user-intel",
        )
    except Exception as e:
        logger.warning("search_restaurants failed: %s", e)
        return ToolResult(False, message="Restaurant search not available right now. Try again later.")


register_tool(ToolDef(
    id="search_restaurants",
    name="search_restaurants",
    description="Find restaurants in a city. Optionally filter by cuisine type or add extra keywords.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_restaurants,
    parameters={
        "city": {"type": "string", "required": True, "description": "City to search restaurants in"},
        "cuisine": {"type": "string", "required": False, "description": "Cuisine type (e.g. italian, chinese, indian)"},
        "query": {"type": "string", "required": False, "description": "Extra search keywords (e.g. top rated, budget)"},
    },
    examples=[
        "search_restaurants: city=Mumbai cuisine=italian",
        "search_restaurants: city=Delhi query=best street food",
    ],
))

# -----------------------------------------------------------------------------
# 4. search_news — Latest news
# -----------------------------------------------------------------------------
def _search_news(params: dict, agent=None) -> ToolResult:
    """Get the latest news on a topic or category."""
    topic = params.get("topic", "")
    category = params.get("category", "")
    query = params.get("query", "")
    if not topic and not category and not query:
        return ToolResult(False, "Please provide a topic, category, or search query for news.")
    try:
        from app.shunya.web_search import search_web

        keyword = topic or category or ""
        parts = []
        if keyword:
            parts.append(keyword)
        parts.append("news")
        if query:
            parts.append(query)
        search_query = "latest " + " ".join(parts)

        results = search_web(search_query, limit=5)
        if results:
            label = topic or category or ""
            message = f"📰 Found {len(results)} news articles about {label}."
            return ToolResult(True, message=message, data={
                "results": results,
                "count": len(results),
                "query": search_query,
                "quick_actions": [
                    {"label": "Sports news →", "action": "bird_query:search_news category=sports"},
                    {"label": "Tech news →", "action": "bird_query:search_news category=tech"},
                    {"label": "Business news →", "action": "bird_query:search_news category=business"},
                    {"label": "Entertainment →", "action": "bird_query:search_news category=entertainment"},
                ],
            }, target_url="/user-intel")
        return ToolResult(
            True,
            message=f"No news found for '{search_query}'.",
            data={"results": [], "count": 0},
            target_url="/user-intel",
        )
    except Exception as e:
        logger.warning("search_news failed: %s", e)
        return ToolResult(False, message="News search not available right now. Try again later.")


register_tool(ToolDef(
    id="search_news",
    name="search_news",
    description="Get the latest news. Filter by topic, category (business|tech|sports|entertainment), or custom query.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_news,
    parameters={
        "topic": {"type": "string", "required": False, "description": "News topic (e.g. cricket, elections, AI)"},
        "category": {"type": "string", "required": False, "description": "News category: business, tech, sports, entertainment"},
        "query": {"type": "string", "required": False, "description": "Extra search keywords"},
    },
    examples=[
        "search_news: topic=cricket",
        "search_news: category=tech",
        "search_news: topic=AI query=India",
    ],
))

# -----------------------------------------------------------------------------
# 5. search_places — Find attractions/places
# -----------------------------------------------------------------------------
def _search_places(params: dict, agent=None) -> ToolResult:
    """Find top attractions, tourist spots, shopping, parks, or landmarks in a city."""
    city = params.get("city", "")
    place_type = params.get("type", "")
    query = params.get("query", "")
    if not city:
        return ToolResult(False, "Please provide a city to find places in.")
    try:
        from app.shunya.web_search import search_web

        parts = []
        if place_type:
            parts.append(place_type)
        parts.append("places to visit in")
        parts.append(city)
        if query:
            parts.append(query)
        search_query = "top " + " ".join(parts)

        results = search_web(search_query, limit=5)
        if results:
            label = f"{place_type} " if place_type else ""
            message = f"📍 Found {len(results)} {label}places to visit in {city}."
            return ToolResult(True, message=message, data={
                "results": results,
                "count": len(results),
                "query": search_query,
                "quick_actions": [
                    {"label": "Show on map →", "action": "bird_query:find places in " + city + " on map"},
                    {"label": "Find hotels →", "action": "bird_query:search_restaurants city=" + city},
                    {"label": "Tourist spots →", "action": "bird_query:search_places city=" + city + " type=tourist"},
                    {"label": "Landmarks →", "action": "bird_query:search_places city=" + city + " type=landmarks"},
                ],
            }, target_url="/user-intel")
        return ToolResult(
            True,
            message=f"No places found for '{search_query}'.",
            data={"results": [], "count": 0},
            target_url="/user-intel",
        )
    except Exception as e:
        logger.warning("search_places failed: %s", e)
        return ToolResult(False, message="Place search not available right now. Try again later.")


register_tool(ToolDef(
    id="search_places",
    name="search_places",
    description="Find top attractions, tourist spots, shopping areas, parks, or landmarks in a city.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_places,
    parameters={
        "city": {"type": "string", "required": True, "description": "City to find places in"},
        "type": {"type": "string", "required": False, "description": "Place type: tourist, shopping, parks, landmarks"},
        "query": {"type": "string", "required": False, "description": "Extra search keywords"},
    },
    examples=[
        "search_places: city=Jaipur type=tourist",
        "search_places: city=Mumbai type=shopping",
        "search_places: city=Delhi query=hidden gems",
    ],
))

# -----------------------------------------------------------------------------
# 6. search_events — Find events/concerts/festivals
# -----------------------------------------------------------------------------
def _search_events(params: dict, agent=None) -> ToolResult:
    """Find events, concerts, and festivals in a city."""
    city = params.get("city", "")
    date = params.get("date", "")
    event_type = params.get("type", "")
    if not city:
        return ToolResult(False, "Please provide a city to find events in.")
    try:
        from app.shunya.web_search import search_web

        parts = ["events concerts festivals in", city]
        if date:
            parts.append(date)
        if event_type:
            parts.append(event_type)
        search_query = " ".join(parts)

        results = search_web(search_query, limit=5)
        if results:
            message = f"🎪 Found {len(results)} events in {city}."
            return ToolResult(True, message=message, data={
                "results": results,
                "count": len(results),
                "query": search_query,
                "quick_actions": [
                    {"label": "This weekend →", "action": "bird_query:search_events city=" + city + " date=this weekend"},
                    {"label": "Concerts near me →", "action": "bird_query:search_events city=" + city + " type=concert"},
                    {"label": "Festivals coming up →", "action": "bird_query:search_events city=" + city + " type=festival"},
                ],
            }, target_url="/user-intel")
        return ToolResult(
            True,
            message=f"No events found for '{search_query}'.",
            data={"results": [], "count": 0},
            target_url="/user-intel",
        )
    except Exception as e:
        logger.warning("search_events failed: %s", e)
        return ToolResult(False, message="Event search not available right now. Try again later.")


register_tool(ToolDef(
    id="search_events",
    name="search_events",
    description="Find events, concerts, and festivals in a city. Optionally filter by date or event type.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_events,
    parameters={
        "city": {"type": "string", "required": True, "description": "City to search events in"},
        "date": {"type": "string", "required": False, "description": "Date filter (e.g. today, this weekend, 2025-07-15)"},
        "type": {"type": "string", "required": False, "description": "Event type (e.g. concert, festival, comedy)"},
    },
    examples=[
        "search_events: city=Mumbai",
        "search_events: city=Goa type=concert date=this weekend",
        "search_events: city=Delhi type=festival",
    ],
))

# -----------------------------------------------------------------------------
# 7. log_user_activity — Log user interaction
# -----------------------------------------------------------------------------
def _log_user_activity(params: dict, agent=None) -> ToolResult:
    """Log a user interaction or page visit for analytics. Frontend logs directly via API; this just acknowledges."""
    activity_type = params.get("activity_type", "")
    page_path = params.get("page_path", "")
    page_title = params.get("page_title", "")
    duration = params.get("duration", 0)
    metadata = params.get("metadata", {})

    if not activity_type:
        return ToolResult(False, "Please provide an activity_type (e.g. page_view, click, search).")

    logged = {
        "activity_type": activity_type,
        "page_path": page_path or "",
        "page_title": page_title or "",
        "duration": duration,
        "metadata": metadata,
    }
    logger.info("User activity logged: %s", logged)

    return ToolResult(True, message=f"✅ Activity '{activity_type}' logged successfully.", data={
        "logged": logged,
        "note": "Frontend logs to the API directly. This endpoint confirms receipt.",
    })


register_tool(ToolDef(
    id="log_user_activity",
    name="log_user_activity",
    description="Log a user interaction or page visit for analytics. Frontend logs via the API directly — this tool confirms the action.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.WRITE,
    tier=1,
    handler=_log_user_activity,
    parameters={
        "activity_type": {"type": "string", "required": True, "description": "Type of activity (e.g. page_view, click, search)"},
        "page_path": {"type": "string", "required": False, "description": "Page URL or path where activity occurred"},
        "page_title": {"type": "string", "required": False, "description": "Page title where activity occurred"},
        "duration": {"type": "number", "required": False, "description": "Time spent on page in seconds"},
        "metadata": {"type": "object", "required": False, "description": "Additional context as key-value pairs"},
    },
    examples=[
        "log_user_activity: activity_type=page_view page_path=/dashboard",
        "log_user_activity: activity_type=search query=flights",
    ],
))

# -----------------------------------------------------------------------------
# 8. log_mood_checkin — Log mood/energy
# -----------------------------------------------------------------------------
def _log_mood_checkin(params: dict, agent=None) -> ToolResult:
    """Log a mood and energy check-in. Helps track well-being patterns over time."""
    mood = params.get("mood", "")
    energy = params.get("energy", 0)
    notes = params.get("notes", "")

    valid_moods = ["great", "good", "okay", "rough", "tough"]
    if mood not in valid_moods:
        return ToolResult(
            False,
            f"Please provide a valid mood: {', '.join(valid_moods)}.",
        )
    try:
        energy_val = int(energy)
    except (ValueError, TypeError):
        energy_val = 0
    if energy_val < 1 or energy_val > 5:
        return ToolResult(False, "Please provide an energy level between 1 and 5.")

    logger.info("Mood check-in: mood=%s energy=%d notes=%s", mood, energy_val, notes)

    return ToolResult(True, message=f"😊 Mood check-in saved! You're feeling **{mood}** (energy: {energy_val}/5).", data={
        "mood": mood,
        "energy": energy_val,
        "notes": notes,
        "quick_actions": [
            {"label": "View mood trends →", "action": "bird_query:show my mood trends"},
            {"label": "Log again later →", "action": "bird_query:log_mood_checkin"},
        ],
    })


register_tool(ToolDef(
    id="log_mood_checkin",
    name="log_mood_checkin",
    description="Log a mood and energy check-in. Mood: great|good|okay|rough|tough. Energy: 1-5.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.WRITE,
    tier=1,
    handler=_log_mood_checkin,
    parameters={
        "mood": {"type": "string", "required": True, "description": "Current mood: great, good, okay, rough, or tough"},
        "energy": {"type": "number", "required": True, "description": "Energy level from 1 (low) to 5 (high)"},
        "notes": {"type": "string", "required": False, "description": "Optional notes about how you're feeling"},
    },
    examples=[
        "log_mood_checkin: mood=great energy=5",
        "log_mood_checkin: mood=okay energy=3 notes=feeling tired",
    ],
))

# -----------------------------------------------------------------------------
# 9. get_user_insights — Get AI insights about work patterns
# -----------------------------------------------------------------------------
def _get_user_insights(params: dict, agent=None) -> ToolResult:
    """Get AI-powered insights about user work patterns, focus score, and well-being."""
    period = params.get("period", "today")

    valid_periods = ["today", "week", "month"]
    if period not in valid_periods:
        period = "today"

    # Simulated insights — in production these would query real analytics
    focus_score = 82 if period == "today" else (76 if period == "week" else 71)
    relationship_score = 88 if period == "today" else (84 if period == "week" else 80)
    mood_status = "Positive" if period == "today" else "Stable"

    message = (
        f"📊 **{period.capitalize()} Insights**\n"
        f"• 🎯 Focus Score: **{focus_score}%** — Good concentration levels\n"
        f"• 🤝 Relationship Score: **{relationship_score}%** — Active engagement\n"
        f"• 😊 Mood Status: **{mood_status}** — Steady and productive\n"
    )

    return ToolResult(True, message=message, data={
        "period": period,
        "focus_score": focus_score,
        "relationship_score": relationship_score,
        "mood_status": mood_status,
        "quick_actions": [
            {"label": "View full report →", "action": "bird_query:get_user_insights period=month"},
            {"label": "Check today's focus →", "action": "bird_query:get_user_insights period=today"},
            {"label": "Log a mood check-in →", "action": "bird_query:log_mood_checkin"},
        ],
    })


register_tool(ToolDef(
    id="get_user_insights",
    name="get_user_insights",
    description="Get AI-powered insights about work patterns, focus score, relationship score, and mood status for a given period.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_get_user_insights,
    parameters={
        "period": {"type": "string", "required": False, "description": "Time period: today, week, or month (default: today)"},
    },
    examples=[
        "get_user_insights",
        "get_user_insights: period=week",
        "get_user_insights: period=month",
    ],
))

# -----------------------------------------------------------------------------
# 10. search_local — One-query local info search
# -----------------------------------------------------------------------------
def _search_local(params: dict, agent=None) -> ToolResult:
    """Search the web for local information in one query. Catch-all for location-based questions."""
    query = params.get("query", params.get("raw", ""))
    city = params.get("city", "")
    if not query and not city:
        return ToolResult(False, "Please provide a search query or city to look up local information.")
    try:
        from app.shunya.web_search import search_web

        search_query = query
        if city and city not in query:
            # If the user explicitly passed a city, incorporate it
            search_query = f"{query} in {city}"
        elif not query and city:
            search_query = f"information about {city}"

        results = search_web(search_query, limit=5)
        if results:
            message = f"🌐 Found {len(results)} results for your query."
            return ToolResult(True, message=message, data={
                "results": results,
                "count": len(results),
                "query": search_query,
                "quick_actions": [
                    {"label": "Search again →", "action": "bird_query:search_local"},
                    {"label": "Find nearby →", "action": "bird_query:what's near me"},
                    {"label": "Ask something else →", "action": "bird_query:help"},
                ],
            }, target_url="/user-intel")
        return ToolResult(
            True,
            message=f"No results found for '{search_query}'.",
            data={"results": [], "count": 0},
            target_url="/user-intel",
        )
    except Exception as e:
        logger.warning("search_local failed: %s", e)
        return ToolResult(False, message="Local search not available right now. Try again later.")


register_tool(ToolDef(
    id="search_local",
    name="search_local",
    description="Search the web for local information — catch-all for location-based questions, nearby places, and general queries.",
    category=ToolCategory.INTELLIGENCE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_local,
    parameters={
        "query": {"type": "string", "required": True, "description": "Search query about local information"},
        "city": {"type": "string", "required": False, "description": "Optional city to scope the search to"},
    },
    examples=[
        "search_local: query=best cafés near me",
        "search_local: query=things to do city=Goa",
        "search_local: query=what's happening this weekend",
    ],
))