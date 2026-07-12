"""Unified calendar view — query all date-based entities across entity types."""

import logging
from datetime import date, datetime
from typing import Optional

from app import db
from app.models import EntityDefinition, Entity

logger = logging.getLogger("app.shunya.calendar")

# ── Helpers ──


def _parse_date_value(raw) -> Optional[date]:
    """Try to parse a value as a date. Accepts strings, datetime, date."""
    if raw is None:
        return None
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        # Try ISO formats
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(raw[:10], fmt).date()
            except ValueError:
                continue
    return None


def _get_date_fields(schema: list) -> list[dict]:
    """Return all field definitions in a schema with type=='date'."""
    return [f for f in schema if isinstance(f, dict) and f.get("type") == "date"]


# ── Main Query ──


def get_events_for_month(
    tenant_id: int,
    year: int,
    month: int,
) -> list[dict]:
    """Query ALL entity types that have date fields and return events for the given month.

    Returns a list of dicts, each with:
        date:         str (YYYY-MM-DD)
        title:        str — the entity's primary display name
        entity_type:  str — the entity definition type
        entity_id:    int
        code:         str or None
        icon:         str — the entity definition icon
        status:       str — the entity's current status
        field_label:  str — which date field triggered this event
    """
    all_events = []

    # 1. Fetch all active definitions for this tenant
    definitions = (
        EntityDefinition.query
        .filter_by(tenant_id=tenant_id, is_active=True)
        .all()
    )

    for definition in definitions:
        date_fields = _get_date_fields(definition.schema)
        if not date_fields:
            continue  # skip entity types that have no date fields

        # 2. Query entities of this type
        entities = (
            Entity.query
            .filter_by(tenant_id=tenant_id, definition_id=definition.id, is_archived=False)
            .all()
        )

        for entity in entities:
            if not entity.data:
                continue

            display_name = entity.display_name

            for field in date_fields:
                field_name = field["name"]
                raw = entity.data.get(field_name)
                d = _parse_date_value(raw)
                if d is None:
                    continue

                # Check if this date falls in the requested month
                if d.year == year and d.month == month:
                    all_events.append({
                        "date": d.isoformat(),
                        "title": display_name,
                        "entity_type": definition.type,
                        "entity_id": entity.id,
                        "code": entity.code,
                        "icon": definition.icon or "📋",
                        "status": entity.status or "new",
                        "field_label": field.get("label", field_name),
                    })

    # Sort by date then title
    all_events.sort(key=lambda e: (e["date"], e["title"]))

    return all_events


def get_day_events(
    tenant_id: int,
    year: int,
    month: int,
    day: int,
) -> list[dict]:
    """Return events for a specific day (convenience wrapper)."""
    all_month = get_events_for_month(tenant_id, year, month)
    day_str = f"{year:04d}-{month:02d}-{day:02d}"
    return [e for e in all_month if e["date"] == day_str]