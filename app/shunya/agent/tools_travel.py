"""Shunya OS — Bird AI Travel Intelligence, Knowledge & Document Tools.

All travel-intel, knowledge, and document tools register here via register_tool().
Each handler:
  - Imports needed models from app.models
  - Uses flask.g for context (tenant_id, user_id, role)
  - Returns ToolResult
  - Is registered at module level with register_tool()
"""
from __future__ import annotations
from typing import Any, Optional
from flask import g
from datetime import datetime, date
import json, logging

from app.shunya.agent import (
    register_tool,
    ToolDef,
    ToolCategory,
    ToolPermission,
    ToolResult,
)

logger = logging.getLogger("shunya.tools.travel")

# =============================================================================
# TIER 1 — Travel Intelligence & Knowledge Tools
# =============================================================================

# -----------------------------------------------------------------------------
# 1. search_web — Web search for travel info
# -----------------------------------------------------------------------------
def _search_web(params: dict, agent=None) -> ToolResult:
    """Search the web for travel-related information."""
    query = params.get("query", params.get("raw", ""))
    if not query:
        return ToolResult(False, "Please provide a search query.")
    try:
        from app.shunya.web_search import web_search
        results = web_search(query, limit=5)
        return ToolResult(True, data={
            "results": results,
            "count": len(results) if results else 0,
        })
    except Exception as e:
        logger.warning("Web search failed: %s", e)
        return ToolResult(False, "Web search is not available right now. Try again later.")


register_tool(ToolDef(
    id="search_web",
    name="search_web",
    description="Search the web for travel information — destinations, flights, hotels, attractions, local tips, etc.",
    category=ToolCategory.TRAVEL_INTEL,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_web,
    parameters={
        "query": {"type": "string", "required": True, "description": "Search query for web"},
    },
    examples=["search_web: best restaurants in Bangkok", "search_web: Thailand travel restrictions"],
))

# -----------------------------------------------------------------------------
# 2. search_entities — Full-text search across all entity types
# -----------------------------------------------------------------------------
def _search_entities(params: dict, agent=None) -> ToolResult:
    """Full-text search across all entity types (leads, bookings, etc.)."""
    query = params.get("query", params.get("raw", ""))
    entity_type = params.get("entity_type", "")
    if not query:
        return ToolResult(False, "Please provide a search query.")
    try:
        from app.models import Entity, EntityDefinition
        from sqlalchemy import or_
        tenant_id = g.tenant.id

        definitions = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        results = []

        for d in definitions:
            if entity_type and d.type != entity_type:
                continue
            searchable = d.searchable_fields or []
            if not searchable:
                searchable = [f.get("name", "") for f in (d.schema or []) if f.get("name")]

            filters = []
            for field_name in searchable:
                if field_name in ("name", "title", "description", "email", "phone", "notes", "address", "city", "country"):
                    filters.append(
                        Entity.data[field_name].as_string().ilike(f"%{query}%")
                    )

            if not filters:
                continue

            entities = Entity.query.filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == d.id,
                Entity.is_archived == False,
                or_(*filters)
            ).order_by(Entity.created_at.desc()).limit(10).all()

            for e in entities:
                results.append({
                    "id": e.id,
                    "code": e.code,
                    "display_name": e.display_name,
                    "entity_type": d.label,
                    "entity_type_slug": d.type,
                    "status": e.status,
                    "data": {k: v for k, v in e.data.items() if k in searchable},
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                })

        return ToolResult(True, data={
            "results": results,
            "count": len(results),
        })
    except Exception as e:
        logger.error("search_entities failed: %s", e)
        return ToolResult(False, f"Search failed: {str(e)}")


register_tool(ToolDef(
    id="search_entities",
    name="search_entities",
    description="Full-text search across all entity types — leads, bookings, invoices, orders, etc.",
    category=ToolCategory.KNOWLEDGE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_search_entities,
    parameters={
        "query": {"type": "string", "required": True, "description": "Search query"},
        "entity_type": {"type": "string", "required": False, "description": "Optional: narrow to one entity type (lead, booking, invoice, etc.)"},
    },
    examples=["search_entities: John Smith", "search_entities: Paris booking"],
))

# -----------------------------------------------------------------------------
# 3. get_entity — Get entity details by ID or code
# -----------------------------------------------------------------------------
def _get_entity(params: dict, agent=None) -> ToolResult:
    """Get details of a single entity by ID or code."""
    entity_id = params.get("entity_id", 0)
    entity_code = params.get("entity_code", "")
    entity_type = params.get("entity_type", "")
    try:
        from app.models import Entity, EntityDefinition
        tenant_id = g.tenant.id

        query = Entity.query.filter_by(tenant_id=tenant_id, is_archived=False)

        if entity_type:
            definition = EntityDefinition.query.filter_by(tenant_id=tenant_id, type=entity_type).first()
            if not definition:
                return ToolResult(False, f"No entity type '{entity_type}' found.")
            query = query.filter(Entity.definition_id == definition.id)

        if entity_id and int(entity_id) > 0:
            query = query.filter(Entity.id == int(entity_id))
        elif entity_code:
            query = query.filter(Entity.code == entity_code)
        else:
            return ToolResult(False, "Provide entity_id or entity_code.")

        entity = query.first()
        if not entity:
            return ToolResult(False, "Entity not found.")

        # Get definition type label
        def_label = entity.definition.label if entity.definition else "Record"
        return ToolResult(True, data={
            "id": entity.id,
            "code": entity.code,
            "entity_type": entity.definition.type if entity.definition else None,
            "entity_label": def_label,
            "status": entity.status,
            "assigned_to": entity.assigned_to,
            "data": entity.data,
            "ai_summary": entity.ai_summary,
            "tags": entity.tags,
            "display_name": entity.display_name,
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
        })
    except Exception as e:
        logger.error("get_entity failed: %s", e)
        return ToolResult(False, f"Failed to get entity: {str(e)}")


register_tool(ToolDef(
    id="get_entity",
    name="get_entity",
    description="Get details of a single record by its ID or code.",
    category=ToolCategory.KNOWLEDGE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_get_entity,
    parameters={
        "entity_id": {"type": "number", "required": False, "description": "Record ID"},
        "entity_code": {"type": "string", "required": False, "description": "Record code (e.g. PC11072601)"},
        "entity_type": {"type": "string", "required": False, "description": "Entity type (lead, booking, invoice, etc.)"},
    },
    examples=["get_entity: entity_id=42", "get_entity: entity_code=PC11072601"],
))

# -----------------------------------------------------------------------------
# 4. list_entities — List entities by type/status/date
# -----------------------------------------------------------------------------
def _list_entities(params: dict, agent=None) -> ToolResult:
    """List entities filtered by type, status, date range."""
    entity_type = params.get("entity_type", "")
    status = params.get("status", "")
    limit = int(params.get("limit", 20))
    date_from = params.get("date_from", "")
    date_to = params.get("date_to", "")
    try:
        from app.models import Entity, EntityDefinition
        tenant_id = g.tenant.id

        query = Entity.query.filter_by(tenant_id=tenant_id, is_archived=False)

        if entity_type:
            definition = EntityDefinition.query.filter_by(tenant_id=tenant_id, type=entity_type).first()
            if not definition:
                return ToolResult(False, f"No entity type '{entity_type}' found.")
            query = query.filter(Entity.definition_id == definition.id)
            def_label = definition.label_plural or definition.label
        else:
            def_label = "Records"

        if status:
            query = query.filter(Entity.status == status)

        if date_from:
            try:
                dt = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Entity.created_at >= dt)
            except ValueError:
                pass

        if date_to:
            try:
                dt = datetime.strptime(date_to, "%Y-%m-%d")
                query = query.filter(Entity.created_at <= dt)
            except ValueError:
                pass

        entities = query.order_by(Entity.created_at.desc()).limit(limit).all()

        results = []
        for e in entities:
            results.append({
                "id": e.id,
                "code": e.code,
                "status": e.status,
                "data": e.data,
                "display_name": e.display_name,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            })

        return ToolResult(True, data={
            "entity_type": entity_type or "all",
            "label": def_label,
            "count": len(results),
            "entities": results,
        })
    except Exception as e:
        logger.error("list_entities failed: %s", e)
        return ToolResult(False, f"Failed to list entities: {str(e)}")


register_tool(ToolDef(
    id="list_entities",
    name="list_entities",
    description="List records filtered by type, status, or date range.",
    category=ToolCategory.KNOWLEDGE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_list_entities,
    parameters={
        "entity_type": {"type": "string", "required": False, "description": "Entity type (lead, booking, invoice, etc.)"},
        "status": {"type": "string", "required": False, "description": "Filter by status (new, pending, confirmed, etc.)"},
        "limit": {"type": "number", "required": False, "description": "Max records to return (default: 20)"},
        "date_from": {"type": "string", "required": False, "description": "Start date (YYYY-MM-DD)"},
        "date_to": {"type": "string", "required": False, "description": "End date (YYYY-MM-DD)"},
    },
    examples=["list_entities: entity_type=booking", "list_entities: entity_type=lead status=new"],
))

# -----------------------------------------------------------------------------
# 5. get_analytics — Entity counts, pipeline status
# -----------------------------------------------------------------------------
def _get_analytics(params: dict, agent=None) -> ToolResult:
    """Get analytics — entity counts, pipeline status, activity trends."""
    try:
        from app.models import Entity, EntityDefinition, ActivityLog
        import datetime as dt_mod
        tenant_id = g.tenant.id

        definitions = EntityDefinition.query.filter_by(tenant_id=tenant_id).all()
        total = Entity.query.filter_by(tenant_id=tenant_id, is_archived=False).count()
        active = Entity.query.filter_by(tenant_id=tenant_id, is_archived=False).filter(
            Entity.status.notin_(["cancelled", "archived", "lost", "closed"])
        ).count()

        pipeline = {}
        for d in definitions:
            entities = Entity.query.filter_by(tenant_id=tenant_id, definition_id=d.id, is_archived=False).all()
            statuses = {}
            for e in entities:
                s = e.status or "new"
                statuses[s] = statuses.get(s, 0) + 1
            pipeline[d.type] = {
                "icon": d.icon or "📋",
                "label": d.label,
                "total": len(entities),
                "statuses": statuses,
            }

        activity_trend = []
        now = dt_mod.datetime.utcnow()
        for i in range(6, -1, -1):
            day = now - dt_mod.timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + dt_mod.timedelta(days=1)
            count = ActivityLog.query.filter(
                ActivityLog.tenant_id == tenant_id,
                ActivityLog.created_at >= day_start,
                ActivityLog.created_at < day_end,
            ).count()
            activity_trend.append({"date": day.strftime("%a"), "count": count})

        period = now.strftime("%B %Y")

        return ToolResult(True, data={
            "period": period,
            "total_entities": total,
            "active_entities": active,
            "pipeline": pipeline,
            "activity_trend": activity_trend,
            "entities_by_type": {
                d.label: Entity.query.filter_by(tenant_id=tenant_id, definition_id=d.id, is_archived=False).count()
                for d in definitions
            },
        })
    except Exception as e:
        logger.error("get_analytics failed: %s", e)
        return ToolResult(False, f"Analytics failed: {str(e)}")


register_tool(ToolDef(
    id="get_analytics",
    name="get_analytics",
    description="Get business analytics — entity counts, pipeline status, activity trends.",
    category=ToolCategory.ANALYTICS,
    permission=ToolPermission.READ,
    tier=1,
    handler=_get_analytics,
    parameters={},
    examples=["get_analytics"],
))

# -----------------------------------------------------------------------------
# 6. get_customer_journey — Where customer is in infinite loop
# -----------------------------------------------------------------------------
def _get_customer_journey(params: dict, agent=None) -> ToolResult:
    """Get the customer journey report: where each customer is in the infinite loop."""
    try:
        from app.shunya.journey import build_journey, JourneyStage
        from app.models import Entity, EntityDefinition
        tenant_id = g.tenant.id

        definitions = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        def_counts = {}
        for d in definitions:
            count = Entity.query.filter_by(tenant_id=tenant_id, definition_id=d.id, is_archived=False).count()
            def_counts[d.type] = {"label": d.label_plural or d.label, "icon": d.icon, "count": count}

        journey = build_journey(tenant_id, def_counts)
        stages = []
        for item in journey.stages:
            stages.append({
                "stage": item.stage.value,
                "count": item.count,
                "next_action": item.next_action,
                "next_entity_type": item.next_entity_type,
            })

        return ToolResult(True, data={
            "stages": stages,
            "total_active": journey.total_active,
            "current_focus": journey.current_focus,
        })
    except Exception as e:
        logger.error("get_customer_journey failed: %s", e)
        return ToolResult(False, f"Journey report failed: {str(e)}")


register_tool(ToolDef(
    id="get_customer_journey",
    name="get_customer_journey",
    description="Get the customer journey report — where customers are in the infinite loop (Lead→Quote→Booking→Payment→Trip→Feedback→Retention).",
    category=ToolCategory.TRAVEL_INTEL,
    permission=ToolPermission.READ,
    tier=1,
    handler=_get_customer_journey,
    parameters={},
    examples=["get_customer_journey"],
))

# -----------------------------------------------------------------------------
# 7. get_next_action — Bird AI says what to do next
# -----------------------------------------------------------------------------
def _get_next_action(params: dict, agent=None) -> ToolResult:
    """Get the next best action recommendation from Bird AI."""
    try:
        from app.shunya.bird import Bird
        tenant_id = g.tenant.id
        user_id = g.user.id
        user_role = getattr(g.user, "role", "agent")
        user_name = getattr(g.user, "name", "User")

        bird = Bird(tenant_id, user_id, user_role, user_name)
        suggestions = bird.suggest_next_action()

        return ToolResult(True, data={
            "actions": suggestions if isinstance(suggestions, list) else suggestions.get("actions", []),
            "greeting": None,
        })
    except Exception as e:
        logger.error("get_next_action failed: %s", e)
        return ToolResult(False, f"Next action unavailable: {str(e)}")


register_tool(ToolDef(
    id="get_next_action",
    name="get_next_action",
    description="Get Bird AI's recommended next action — what needs attention right now.",
    category=ToolCategory.TRAVEL_INTEL,
    permission=ToolPermission.READ,
    tier=1,
    handler=_get_next_action,
    parameters={},
    examples=["get_next_action"],
))

# -----------------------------------------------------------------------------
# 8. check_visa_requirements — Visa info for destination + nationality
# -----------------------------------------------------------------------------
def _check_visa_requirements(params: dict, agent=None) -> ToolResult:
    """Get visa requirement guidance for a destination and nationality."""
    destination = params.get("destination", "")
    nationality = params.get("nationality", "IN")
    if not destination:
        return ToolResult(False, "Please provide a destination country.")

    # Return general guidance (non-authoritative — always verify with embassy)
    visa_data = {
        "destination": destination,
        "nationality": nationality,
        "disclaimer": "This is general guidance only. Always verify with the official embassy or consulate.",
        "common_categories": {
            "tourist": "Check if destination offers visa-on-arrival, e-visa, or visa-free travel.",
            "business": "May require additional documentation — invitation letter, company registration.",
            "transit": "Some countries require transit visas even for short layovers.",
        },
        "recommended_action": f"Check the official embassy website of {destination} for your nationality ({nationality}).",
    }

    # Try web search for more specific info
    try:
        from app.shunya.web_search import web_search
        search_query = f"visa requirements {nationality} citizens traveling to {destination} 2025"
        web_results = web_search(search_query, limit=3)
        if web_results:
            visa_data["web_results"] = web_results
    except Exception:
        pass

    return ToolResult(True, data=visa_data)


register_tool(ToolDef(
    id="check_visa_requirements",
    name="check_visa_requirements",
    description="Get visa requirement guidance for a destination country based on traveller nationality. Always verify with official sources.",
    category=ToolCategory.TRAVEL_INTEL,
    permission=ToolPermission.READ,
    tier=1,
    handler=_check_visa_requirements,
    parameters={
        "destination": {"type": "string", "required": True, "description": "Destination country or city"},
        "nationality": {"type": "string", "required": False, "description": "Passport nationality code (e.g. IN, US, GB). Default: IN"},
    },
    examples=["check_visa_requirements: destination=Thailand nationality=IN", "check_visa_requirements: destination=Japan"],
))

# -----------------------------------------------------------------------------
# 9. check_travel_advisory — Government advisories
# -----------------------------------------------------------------------------
def _check_travel_advisory(params: dict, agent=None) -> ToolResult:
    """Check government travel advisories for a destination."""
    destination = params.get("destination", "")
    if not destination:
        return ToolResult(False, "Please provide a destination country or city.")

    advisory = {
        "destination": destination,
        "disclaimer": "This is web-sourced information. Always check official government travel advisory sites.",
        "sources": [
            "https://travel.state.gov (US Department of State)",
            "https://www.gov.uk/foreign-travel-advice (UK Foreign Office)",
            "https://www.smartraveller.gov.au (Australian Government)",
        ],
    }

    # Search web for current advisories
    try:
        from app.shunya.web_search import web_search
        search_query = f"travel advisory {destination} 2025"
        web_results = web_search(search_query, limit=3)
        if web_results:
            advisory["advisories"] = web_results
            advisory["result_count"] = len(web_results)
        else:
            advisory["advisories"] = []
            advisory["result_count"] = 0
    except Exception as e:
        advisory["error"] = str(e)
        advisory["advisories"] = []

    return ToolResult(True, data=advisory)


register_tool(ToolDef(
    id="check_travel_advisory",
    name="check_travel_advisory",
    description="Check government travel advisories, safety warnings, and health notices for a destination.",
    category=ToolCategory.TRAVEL_INTEL,
    permission=ToolPermission.READ,
    tier=1,
    handler=_check_travel_advisory,
    parameters={
        "destination": {"type": "string", "required": True, "description": "Destination country or city"},
    },
    examples=["check_travel_advisory: destination=Thailand", "check_travel_advisory: destination=Japan"],
))

# -----------------------------------------------------------------------------
# 10. get_weather_forecast — Weather for destination + dates
# -----------------------------------------------------------------------------
def _get_weather_forecast(params: dict, agent=None) -> ToolResult:
    """Get weather forecast for a destination around given dates."""
    destination = params.get("destination", "")
    date_from = params.get("date_from", "")
    date_to = params.get("date_to", "")
    if not destination:
        return ToolResult(False, "Please provide a destination.")

    forecast = {
        "destination": destination,
        "disclaimer": "Weather forecast is based on web search. For precise forecasts, check weather services like weather.com or accuweather.",
    }

    if date_from:
        forecast["date_from"] = date_from
    if date_to:
        forecast["date_to"] = date_to

    try:
        from app.shunya.web_search import web_search
        query_parts = [f"weather forecast {destination}"]
        if date_from:
            query_parts.append(date_from)
        if date_to:
            query_parts.append("to " + date_to)
        search_query = " ".join(query_parts)
        web_results = web_search(search_query, limit=3)
        if web_results:
            forecast["forecasts"] = web_results
            forecast["result_count"] = len(web_results)
        else:
            forecast["forecasts"] = []
            forecast["result_count"] = 0
    except Exception as e:
        forecast["error"] = str(e)
        forecast["forecasts"] = []

    return ToolResult(True, data=forecast)


register_tool(ToolDef(
    id="get_weather_forecast",
    name="get_weather_forecast",
    description="Get weather forecast information for a destination around specific travel dates.",
    category=ToolCategory.TRAVEL_INTEL,
    permission=ToolPermission.READ,
    tier=1,
    handler=_get_weather_forecast,
    parameters={
        "destination": {"type": "string", "required": True, "description": "Destination city or country"},
        "date_from": {"type": "string", "required": False, "description": "Start date (YYYY-MM-DD)"},
        "date_to": {"type": "string", "required": False, "description": "End date (YYYY-MM-DD)"},
    },
    examples=["get_weather_forecast: destination=Bangkok date_from=2025-07-20 date_to=2025-07-25"],
))

# -----------------------------------------------------------------------------
# 11. convert_currency — Live currency conversion
# -----------------------------------------------------------------------------
def _convert_currency(params: dict, agent=None) -> ToolResult:
    """Convert an amount from one currency to another using live exchange rates."""
    amount = params.get("amount", 1)
    from_currency = params.get("from_currency", "USD").upper()
    to_currency = params.get("to_currency", "INR").upper()

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return ToolResult(False, "Invalid amount. Provide a numeric value.")

    try:
        import requests
        resp = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{from_currency}",
            timeout=8,
        )
        if resp.status_code == 200:
            rates = resp.json().get("rates", {})
            if to_currency in rates:
                rate = rates[to_currency]
                converted = round(amount * rate, 2)
                return ToolResult(True, data={
                    "amount": amount,
                    "from": from_currency,
                    "to": to_currency,
                    "rate": rate,
                    "converted": converted,
                    "formatted": f"{amount:,.2f} {from_currency} = {converted:,.2f} {to_currency}",
                })
            return ToolResult(False, f"Currency '{to_currency}' not found in exchange rates.")
        return ToolResult(False, "Could not fetch live exchange rates. Try again later.")
    except ImportError:
        return ToolResult(False, "Requests module not available for currency conversion.")
    except Exception as e:
        logger.warning("Currency conversion failed: %s", e)
        return ToolResult(False, "Currency conversion unavailable. Check network connectivity.")


register_tool(ToolDef(
    id="convert_currency",
    name="convert_currency",
    description="Convert an amount from one currency to another using live exchange rates.",
    category=ToolCategory.TRAVEL_INTEL,
    permission=ToolPermission.READ,
    tier=1,
    handler=_convert_currency,
    parameters={
        "amount": {"type": "number", "required": False, "description": "Amount to convert (default: 1)"},
        "from_currency": {"type": "string", "required": False, "description": "Source currency code (e.g. USD, EUR, GBP). Default: USD"},
        "to_currency": {"type": "string", "required": False, "description": "Target currency code (e.g. INR, JPY, THB). Default: INR"},
    },
    examples=["convert_currency: amount=500 from_currency=USD to_currency=INR"],
))

# =============================================================================
# TIER 2 — Document Tools
# =============================================================================

# -----------------------------------------------------------------------------
# 12. generate_pdf — Generate PDF of any entity
# -----------------------------------------------------------------------------
def _generate_pdf(params: dict, agent=None) -> ToolResult:
    """Generate a PDF document for an entity."""
    entity_id = params.get("entity_id", 0)
    entity_type = params.get("entity_type", "")
    entity_label = params.get("entity_label", "Entity Report")

    if not entity_id and not entity_type:
        return ToolResult(False, "Provide entity_id or entity_type to generate a PDF.")

    try:
        from app.models import Entity, EntityDefinition
        from app.shunya.export import export_pdf
        tenant_id = g.tenant.id

        if entity_id and int(entity_id) > 0:
            entity = Entity.query.filter_by(id=int(entity_id), tenant_id=tenant_id, is_archived=False).first()
            if not entity:
                return ToolResult(False, "Entity not found.")
            entities = [entity]
            definition = entity.definition
        else:
            definition = EntityDefinition.query.filter_by(tenant_id=tenant_id, type=entity_type).first()
            if not definition:
                return ToolResult(False, f"No entity type '{entity_type}'.")
            entities = Entity.query.filter_by(tenant_id=tenant_id, definition_id=definition.id, is_archived=False).limit(50).all()

        schema = definition.schema if definition else []
        entity_label = definition.label_plural or definition.label if definition else entity_label

        pdf_bytes = export_pdf(entities, schema, entity_label=entity_label)
        if not pdf_bytes:
            return ToolResult(False, "PDF generation returned no data. Check that wkhtmltopdf or fpdf2 is installed.")

        return ToolResult(True, data={
            "pdf_bytes": list(pdf_bytes) if isinstance(pdf_bytes, bytes) else pdf_bytes,
            "entity_count": len(entities),
            "entity_label": entity_label,
            "format": "pdf",
            "note": "PDF generated. Pass to upload_document or download directly.",
        })
    except Exception as e:
        logger.error("generate_pdf failed: %s", e)
        return ToolResult(False, f"PDF generation failed: {str(e)}. Ensure pdfkit (wkhtmltopdf) or fpdf2 is installed.")


register_tool(ToolDef(
    id="generate_pdf",
    name="generate_pdf",
    description="Generate a PDF report for an entity or entity type. Uses wkhtmltopdf or fpdf2.",
    category=ToolCategory.DOCUMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_generate_pdf,
    parameters={
        "entity_id": {"type": "number", "required": False, "description": "Single entity ID"},
        "entity_type": {"type": "string", "required": False, "description": "Entity type to generate PDF for all records"},
        "entity_label": {"type": "string", "required": False, "description": "Custom label for the PDF report"},
    },
    examples=["generate_pdf: entity_id=42", "generate_pdf: entity_type=booking"],
))

# -----------------------------------------------------------------------------
# 13. generate_itinerary_pdf — Branded travel itinerary PDF
# -----------------------------------------------------------------------------
def _generate_itinerary_pdf(params: dict, agent=None) -> ToolResult:
    """Generate a branded travel itinerary PDF."""
    booking_id = params.get("booking_id", 0)
    if not booking_id or int(booking_id) <= 0:
        return ToolResult(False, "Provide a booking_id to generate an itinerary PDF.")

    try:
        from app.models import Entity, EntityDefinition
        from app.shunya.export import export_pdf
        tenant_id = g.tenant.id

        booking = Entity.query.filter_by(id=int(booking_id), tenant_id=tenant_id, is_archived=False).first()
        if not booking:
            return ToolResult(False, "Booking not found.")

        definition = booking.definition
        schema = definition.schema if definition else []

        # Build a travel itinerary HTML
        data = booking.data or {}
        customer_name = data.get("name", data.get("customer_name", data.get("guest_name", "Guest")))
        destination = data.get("destination", data.get("city", "N/A"))
        check_in = data.get("check_in", data.get("date_from", "N/A"))
        check_out = data.get("check_out", data.get("date_to", "N/A"))
        hotel = data.get("hotel", data.get("accommodation", "TBD"))
        booking_code = booking.code or f"#{booking.id}"

        # Generate a custom HTML itinerary
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      body {{ font-family: 'Inter', 'Helvetica Neue', sans-serif; padding: 40px; background: #f8fafc; }}
      .header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 32px; border-radius: 12px; margin-bottom: 24px; }}
      .header h1 {{ margin: 0; font-size: 28px; }}
      .header .sub {{ font-size: 14px; opacity: 0.8; margin-top: 4px; }}
      .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
      .section h2 {{ margin: 0 0 16px; font-size: 18px; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
      .row {{ display: flex; margin-bottom: 8px; }}
      .label {{ color: #64748b; width: 140px; font-size: 13px; }}
      .value {{ color: #0f172a; font-weight: 500; font-size: 14px; }}
      .footer {{ text-align: center; color: #94a3b8; font-size: 11px; margin-top: 32px; }}
    </style></head><body>
    <div class="header">
      <h1>✈️ Travel Itinerary</h1>
      <div class="sub">Booking: {booking_code} · Generated {datetime.utcnow().strftime('%d %b %Y')}</div>
    </div>
    <div class="section">
      <h2>Guest Details</h2>
      <div class="row"><div class="label">Name</div><div class="value">{customer_name}</div></div>
      <div class="row"><div class="label">Destination</div><div class="value">{destination}</div></div>
    </div>
    <div class="section">
      <h2>Travel Dates</h2>
      <div class="row"><div class="label">Check-in</div><div class="value">{check_in}</div></div>
      <div class="row"><div class="label">Check-out</div><div class="value">{check_out}</div></div>
    </div>
    <div class="section">
      <h2>Accommodation</h2>
      <div class="row"><div class="label">Hotel</div><div class="value">{hotel}</div></div>
    </div>
    <div class="footer">Powered by Shunya OS · Travel Intelligence</div>
    </body></html>"""

        options = {
            "page-size": "A4",
            "margin-top": "15mm", "margin-right": "15mm",
            "margin-bottom": "15mm", "margin-left": "15mm",
            "encoding": "UTF-8", "enable-local-file-access": "",
        }

        pdf_bytes = None
        try:
            import pdfkit
            pdf_bytes = pdfkit.from_string(html, False, options=options)
        except Exception:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 12, "Travel Itinerary", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, f"Booking: {booking_code}", ln=True)
            pdf.cell(0, 8, f"Guest: {customer_name}", ln=True)
            pdf.cell(0, 8, f"Destination: {destination}", ln=True)
            pdf.cell(0, 8, f"Check-in: {check_in} | Check-out: {check_out}", ln=True)
            pdf.cell(0, 8, f"Hotel: {hotel}", ln=True)
            pdf_bytes = bytes(pdf.output(dest="S"))

        if not pdf_bytes:
            return ToolResult(False, "Itinerary PDF generation failed.")

        return ToolResult(True, data={
            "pdf_bytes": list(pdf_bytes) if isinstance(pdf_bytes, bytes) else pdf_bytes,
            "booking_id": booking_id,
            "booking_code": booking_code,
            "format": "itinerary_pdf",
        })
    except Exception as e:
        logger.error("generate_itinerary_pdf failed: %s", e)
        return ToolResult(False, f"Itinerary PDF generation failed: {str(e)}")


register_tool(ToolDef(
    id="generate_itinerary_pdf",
    name="generate_itinerary_pdf",
    description="Generate a branded travel itinerary PDF for a booking. Includes guest details, travel dates, destination, and accommodation.",
    category=ToolCategory.DOCUMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_generate_itinerary_pdf,
    parameters={
        "booking_id": {"type": "number", "required": True, "description": "Booking entity ID"},
    },
    examples=["generate_itinerary_pdf: booking_id=42"],
))

# -----------------------------------------------------------------------------
# 14. generate_invoice_pdf — GST-compliant invoice PDF
# -----------------------------------------------------------------------------
def _generate_invoice_pdf(params: dict, agent=None) -> ToolResult:
    """Generate a GST-compliant invoice PDF."""
    invoice_id = params.get("invoice_id", 0)
    if not invoice_id or int(invoice_id) <= 0:
        return ToolResult(False, "Provide an invoice_id to generate an invoice PDF.")

    try:
        from app.models import Entity, EntityDefinition
        tenant_id = g.tenant.id

        invoice_entity = Entity.query.filter_by(id=int(invoice_id), tenant_id=tenant_id, is_archived=False).first()
        if not invoice_entity:
            return ToolResult(False, "Invoice entity not found.")

        data = invoice_entity.data or {}
        tenant = g.tenant

        customer_name = data.get("name", data.get("customer_name", data.get("client_name", "Customer")))
        amount = data.get("amount", data.get("total", "0"))
        tax_rate = data.get("tax_rate", 18)
        tax = data.get("tax", 0)
        discount = data.get("discount", 0)
        grand_total = data.get("grand_total", data.get("total_amount", 0))

        # Compute if not provided
        try:
            amount_f = float(amount)
            tax_rate_f = float(tax_rate)
            tax_f = float(tax) if tax else round(amount_f * tax_rate_f / 100, 2)
            discount_f = float(discount) if discount else 0
            grand_total_f = float(grand_total) if grand_total else round(amount_f + tax_f - discount_f, 2)
        except (ValueError, TypeError):
            amount_f = 0
            tax_f = 0
            discount_f = 0
            grand_total_f = 0

        invoice_code = invoice_entity.code or f"INV-{invoice_entity.id}"
        company_name = tenant.company_name or "Your Company"
        gstin = data.get("gstin", data.get("gst", "GSTIN: Not provided"))

        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      body {{ font-family: 'Inter', 'Helvetica Neue', sans-serif; padding: 40px; color: #0f172a; }}
      .header {{ display: flex; justify-content: space-between; margin-bottom: 32px; }}
      .company {{ font-size: 24px; font-weight: 700; color: #1e293b; }}
      .company-details {{ font-size: 12px; color: #64748b; }}
      .invoice-title {{ text-align: right; }}
      .invoice-title h1 {{ font-size: 28px; color: #0f172a; margin: 0; }}
      .invoice-title .code {{ font-size: 14px; color: #64748b; }}
      table {{ width: 100%; border-collapse: collapse; margin: 24px 0; }}
      th {{ background: #1e293b; color: white; padding: 10px 12px; text-align: left; font-size: 12px; }}
      td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }}
      .totals {{ text-align: right; margin-top: 16px; }}
      .totals .row {{ margin-bottom: 4px; }}
      .totals .label {{ color: #64748b; font-size: 13px; }}
      .totals .value {{ font-weight: 600; font-size: 14px; margin-left: 20px; }}
      .grand-total {{ font-size: 18px; font-weight: 700; margin-top: 8px; padding-top: 8px; border-top: 2px solid #1e293b; }}
      .footer {{ text-align: center; color: #94a3b8; font-size: 11px; margin-top: 48px; }}
      .gst-badge {{ background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
    </style></head><body>
    <div class="header">
      <div><div class="company">{company_name}</div><div class="company-details">{gstin}<br>Invoice #{invoice_code}</div></div>
      <div class="invoice-title">
        <h1>INVOICE</h1>
        <div class="code">{invoice_code} · {datetime.utcnow().strftime('%d %b %Y')}</div>
      </div>
    </div>
    <table><thead><tr><th>Description</th><th>Amount</th></tr></thead>
    <tbody><tr><td>{customer_name} — {data.get('description', 'Travel Services')}</td><td>₹{amount_f:,.2f}</td></tr></tbody></table>
    <div class="totals">
      <div class="row"><span class="label">Subtotal</span><span class="value">₹{amount_f:,.2f}</span></div>
      <div class="row"><span class="label">GST ({tax_rate_f}%)</span><span class="value">₹{tax_f:,.2f}</span></div>
      <div class="row"><span class="label">Discount</span><span class="value">₹{discount_f:,.2f}</span></div>
      <div class="grand-total">Total Due: ₹{grand_total_f:,.2f}</div>
    </div>
    <div class="footer">GST-compliant invoice · Powered by Shunya OS</div>
    </body></html>"""

        pdf_bytes = None
        try:
            import pdfkit
            options = {
                "page-size": "A4", "margin-top": "15mm", "margin-right": "15mm",
                "margin-bottom": "15mm", "margin-left": "15mm", "encoding": "UTF-8",
                "enable-local-file-access": "",
            }
            pdf_bytes = pdfkit.from_string(html, False, options=options)
        except Exception:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 12, "INVOICE", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, f"{company_name} | {gstin}", ln=True)
            pdf.cell(0, 7, f"Invoice: {invoice_code}", ln=True)
            pdf.ln(8)
            pdf.cell(0, 7, f"Customer: {customer_name}", ln=True)
            pdf.cell(0, 7, f"Amount: Rs.{amount_f:,.2f}", ln=True)
            pdf.cell(0, 7, f"GST ({tax_rate_f}%): Rs.{tax_f:,.2f}", ln=True)
            pdf.cell(0, 7, f"Total: Rs.{grand_total_f:,.2f}", ln=True)
            pdf_bytes = bytes(pdf.output(dest="S"))

        if not pdf_bytes:
            return ToolResult(False, "Invoice PDF generation failed.")

        return ToolResult(True, data={
            "pdf_bytes": list(pdf_bytes) if isinstance(pdf_bytes, bytes) else pdf_bytes,
            "invoice_id": invoice_id,
            "invoice_code": invoice_code,
            "format": "invoice_pdf",
        })
    except Exception as e:
        logger.error("generate_invoice_pdf failed: %s", e)
        return ToolResult(False, f"Invoice PDF generation failed: {str(e)}")


register_tool(ToolDef(
    id="generate_invoice_pdf",
    name="generate_invoice_pdf",
    description="Generate a GST-compliant invoice PDF for travel booking invoices.",
    category=ToolCategory.DOCUMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_generate_invoice_pdf,
    parameters={
        "invoice_id": {"type": "number", "required": True, "description": "Invoice entity ID"},
    },
    examples=["generate_invoice_pdf: invoice_id=42"],
))

# -----------------------------------------------------------------------------
# 15. upload_document — Upload document
# -----------------------------------------------------------------------------
def _upload_document(params: dict, agent=None) -> ToolResult:
    """Upload a document associated with an entity."""
    entity_id = params.get("entity_id", 0)
    filename = params.get("filename", "")
    file_content = params.get("file_content", "")
    file_type = params.get("file_type", "")

    if not entity_id or int(entity_id) <= 0:
        return ToolResult(False, "Provide an entity_id to associate the document with.")
    if not filename:
        return ToolResult(False, "Provide a filename for the document.")
    if not file_content:
        return ToolResult(False, "Provide file content (base64-encoded or text).")

    try:
        import os, base64
        from app import db
        from app.models import Entity, File
        tenant_id = g.tenant.id

        entity = Entity.query.filter_by(id=int(entity_id), tenant_id=tenant_id).first()
        if not entity:
            return ToolResult(False, "Entity not found.")

        # Determine storage path
        upload_dir = f"/root/shunya_os/uploads/{tenant_id}/{entity_id}"
        os.makedirs(upload_dir, exist_ok=True)

        # Try to decode base64 content; if fails, treat as raw text
        try:
            decoded = base64.b64decode(file_content)
            is_binary = True
        except Exception:
            decoded = file_content.encode("utf-8")
            is_binary = False

        file_path = os.path.join(upload_dir, filename)
        mode = "wb" if is_binary else "w"
        with open(file_path, mode) as f:
            f.write(decoded if is_binary else file_content)

        file_record = File(
            tenant_id=tenant_id,
            entity_id=int(entity_id),
            filename=filename,
            file_path=file_path,
            file_type=file_type or filename.split(".")[-1] if "." in filename else "",
            file_size=os.path.getsize(file_path),
            uploaded_by=g.user.id,
        )
        db.session.add(file_record)
        db.session.commit()

        return ToolResult(True, data={
            "file_id": file_record.id,
            "filename": filename,
            "path": file_path,
            "size": file_record.file_size,
            "entity_id": int(entity_id),
        })
    except Exception as e:
        logger.error("upload_document failed: %s", e)
        return ToolResult(False, f"Document upload failed: {str(e)}")


register_tool(ToolDef(
    id="upload_document",
    name="upload_document",
    description="Upload a document (PDF, image, etc.) and associate it with an entity record.",
    category=ToolCategory.DOCUMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_upload_document,
    parameters={
        "entity_id": {"type": "number", "required": True, "description": "Entity ID to associate the document with"},
        "filename": {"type": "string", "required": True, "description": "Filename (e.g. invoice.pdf, passport_scan.jpg)"},
        "file_content": {"type": "string", "required": True, "description": "File content (base64-encoded for binary, or plain text)"},
        "file_type": {"type": "string", "required": False, "description": "File type hint (pdf, image, document)"},
    },
    examples=["upload_document: entity_id=42 filename=passport.pdf file_content=<base64>"],
))

# -----------------------------------------------------------------------------
# 16. create_shareable_link — Secure share link
# -----------------------------------------------------------------------------
def _create_shareable_link(params: dict, agent=None) -> ToolResult:
    """Create a secure, time-limited shareable link for a document or entity."""
    entity_id = params.get("entity_id", 0)
    entity_type = params.get("entity_type", "")
    expires_in_hours = int(params.get("expires_in_hours", 48))
    share_type = params.get("share_type", "view")  # view or download

    if not entity_id or int(entity_id) <= 0:
        return ToolResult(False, "Provide an entity_id to create a shareable link.")

    try:
        import secrets
        from app import db
        from app.models import Entity
        from datetime import timedelta
        tenant_id = g.tenant.id

        entity = Entity.query.filter_by(id=int(entity_id), tenant_id=tenant_id).first()
        if not entity:
            return ToolResult(False, "Entity not found.")

        # Generate a unique share token
        share_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        # Store share link info in a simple JSON-based approach
        # (In production, this would use a ShareLink DB model)
        share_data = {
            "token": share_token,
            "entity_id": int(entity_id),
            "entity_code": entity.code or f"#{entity.id}",
            "entity_type": entity_type or (entity.definition.type if entity.definition else "entity"),
            "share_type": share_type,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "created_by": g.user.id,
            "tenant_id": tenant_id,
        }

        # Store in a simple file-based registry (in prod, add ShareLink DB model)
        import json, os
        shares_dir = f"/root/shunya_os/shares/{tenant_id}"
        os.makedirs(shares_dir, exist_ok=True)
        share_file = os.path.join(shares_dir, f"{share_token}.json")
        with open(share_file, "w") as f:
            json.dump(share_data, f)

        share_url = f"/share/{share_token}"
        display_name = entity.display_name

        return ToolResult(True, data={
            "share_url": share_url,
            "token": share_token,
            "entity_id": int(entity_id),
            "entity": display_name,
            "expires_at": expires_at.isoformat(),
            "expires_in_hours": expires_in_hours,
            "share_type": share_type,
        })
    except Exception as e:
        logger.error("create_shareable_link failed: %s", e)
        return ToolResult(False, f"Failed to create shareable link: {str(e)}")


register_tool(ToolDef(
    id="create_shareable_link",
    name="create_shareable_link",
    description="Create a secure, time-limited shareable link for a document or entity record.",
    category=ToolCategory.DOCUMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_create_shareable_link,
    parameters={
        "entity_id": {"type": "number", "required": True, "description": "Entity ID to share"},
        "entity_type": {"type": "string", "required": False, "description": "Entity type hint"},
        "expires_in_hours": {"type": "number", "required": False, "description": "Link expiry in hours (default: 48)"},
        "share_type": {"type": "string", "required": False, "description": "view or download (default: view)"},
    },
    examples=["create_shareable_link: entity_id=42 expires_in_hours=24"],
))