"""
SHUNYA — Calendar Service

Aggregates Leads (via date-range parsing), ItineraryRefs (with date columns),
and Tasks (with due_date) into a single event stream with color coding.
"""

import re
from datetime import datetime, date, timedelta
from typing import Optional

from app import db
from app.models import Lead, ItineraryRef


# ---------------------------------------------------------------------------
# Date-range parser for Lead.dates strings
# ---------------------------------------------------------------------------

MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_lead_dates(dates_str: str | None) -> tuple[Optional[date], Optional[date]]:
    """Parse a Lead.dates string into (start_date, end_date).

    Handles formats like:
      - "10-14 Jan 2027"       -> (2027-01-10, 2027-01-14)
      - "10 Jan - 14 Jan 2027"  -> (2027-01-10, 2027-01-14)
      - "15 Mar 2027"           -> (2027-03-15, 2027-03-15)
      - "Dec 2026"              -> (2026-12-01, 2026-12-31)
      - "2026"                  -> (2026-01-01, 2026-12-31)
      - "" / None               -> (None, None)
    """
    if not dates_str or not dates_str.strip():
        return None, None
    s = dates_str.strip()

    # Pattern 1: "10-14 Jan 2027" or "10-14 Jan" (assume current year)
    m = re.match(
        r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([A-Za-z]{3,9})\s*(\d{4})?",
        s, re.IGNORECASE,
    )
    if m:
        day_start, day_end, month_name, year_str = m.groups()
        month = MONTH_NAMES.get(month_name.lower()[:3])
        if not month:
            return None, None
        year = int(year_str) if year_str else datetime.utcnow().year
        try:
            start = date(year, month, int(day_start))
            end = date(year, month, int(day_end))
            return start, end
        except ValueError:
            return None, None

    # Pattern 2: "10 Jan - 14 Jan 2027" or "10 Jan to 14 Jan 2027"
    m = re.match(
        r"(\d{1,2})\s+([A-Za-z]{3,9})\s*[-–to]+\s*(\d{1,2})\s+([A-Za-z]{3,9})\s*(\d{4})?",
        s, re.IGNORECASE,
    )
    if m:
        day_start, mon_start, day_end, mon_end, year_str = m.groups()
        month_start = MONTH_NAMES.get(mon_start.lower()[:3])
        month_end = MONTH_NAMES.get(mon_end.lower()[:3])
        if not month_start or not month_end:
            return None, None
        year = int(year_str) if year_str else datetime.utcnow().year
        try:
            start = date(year, month_start, int(day_start))
            end = date(year, month_end, int(day_end))
            return start, end
        except ValueError:
            return None, None

    # Pattern 3: Single date "15 Mar 2027"
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3,9})\s*(\d{4})?", s, re.IGNORECASE)
    if m:
        day_str, month_name, year_str = m.groups()
        month = MONTH_NAMES.get(month_name.lower()[:3])
        if not month:
            return None, None
        year = int(year_str) if year_str else datetime.utcnow().year
        try:
            dt = date(year, month, int(day_str))
            return dt, dt
        except ValueError:
            return None, None

    # Pattern 4: "Jan 2027" or "January 2027"
    m = re.match(r"([A-Za-z]{3,9})\s*(\d{4})", s)
    if m:
        month_name, year_str = m.groups()
        month = MONTH_NAMES.get(month_name.lower()[:3])
        if not month:
            return None, None
        year = int(year_str)
        try:
            start = date(year, month, 1)
            # Last day of month
            if month == 12:
                end = date(year, 12, 31)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
            return start, end
        except ValueError:
            return None, None

    # Pattern 5: Just a year "2026"
    m = re.match(r"(\d{4})", s)
    if m:
        year = int(m.group(1))
        return date(year, 1, 1), date(year, 12, 31)

    # Pattern 6: "DD-MM-YYYY" or "DD/MM/YYYY"
    m = re.match(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            dt = date(year, month, day)
            return dt, dt
        except ValueError:
            return None, None

    return None, None


# ---------------------------------------------------------------------------
# Calendar Service
# ---------------------------------------------------------------------------

class CalendarService:
    """Aggregate events from Leads, ItineraryRefs, and Tasks for the calendar."""

    COLOR_LEAD = "#2563eb"        # Blue
    COLOR_TASK = "#7c3aed"        # Purple
    COLOR_ITINERARY = "#059669"   # Emerald / Green

    def get_events(self, start_date: date, end_date: date) -> list[dict]:
        """Return all events between start_date and end_date (inclusive).

        Each event dict:
          { id, title, date (ISO), type, status, url, color }
        """
        events: list[dict] = []

        # --- Leads ---
        for lead in Lead.query.all():
            start_dt, end_dt = _parse_lead_dates(lead.dates)
            if start_dt and end_dt:
                # Spread across the range (one event per day so calendar shows it)
                current = max(start_dt, start_date)
                range_end = min(end_dt, end_date)
                while current <= range_end:
                    events.append({
                        "id": f"lead-{lead.id}",
                        "title": f"{lead.customer_name or 'Guest'} — {lead.destination or 'Trip'}"[:60],
                        "date": current.isoformat(),
                        "type": "lead",
                        "status": lead.status or "new",
                        "url": f"/leads/{lead.id}",
                        "color": self.COLOR_LEAD,
                    })
                    current += timedelta(days=1)
            elif start_dt and start_date <= start_dt <= end_date:
                # Single date
                events.append({
                    "id": f"lead-{lead.id}",
                    "title": f"{lead.customer_name or 'Guest'} — {lead.destination or 'Trip'}"[:60],
                    "date": start_dt.isoformat(),
                    "type": "lead",
                    "status": lead.status or "new",
                    "url": f"/leads/{lead.id}",
                    "color": self.COLOR_LEAD,
                })

        # --- ItineraryRefs ---
        refs = ItineraryRef.query.filter(
            ItineraryRef.start_date.isnot(None),
            ItineraryRef.end_date.isnot(None),
            ItineraryRef.start_date <= end_date,
            ItineraryRef.end_date >= start_date,
        ).all()
        for ref in refs:
            current = max(ref.start_date, start_date)
            range_end = min(ref.end_date, end_date)
            while current <= range_end:
                events.append({
                    "id": f"itinerary-{ref.id}",
                    "title": f"{ref.guest_name or 'Guest'} — {ref.destination or 'Trip'}"[:60],
                    "date": current.isoformat(),
                    "type": "itinerary",
                    "status": "converted",
                    "url": f"/itineraries?ref_id={ref.id}",
                    "color": self.COLOR_ITINERARY,
                })
                current += timedelta(days=1)

        # --- Tasks (if model exists) ---
        try:
            from app.models import Task
            tasks = Task.query.filter(
                Task.due_date.isnot(None),
                Task.due_date >= start_date,
                Task.due_date <= end_date,
            ).all()
            for task in tasks:
                events.append({
                    "id": f"task-{task.id}",
                    "title": task.title[:60],
                    "date": task.due_date.isoformat(),
                    "type": "task",
                    "status": task.status or "pending",
                    "url": f"/tasks/{task.id}" if hasattr(task, "id") else "#",
                    "color": self.COLOR_TASK,
                })
        except (ImportError, AttributeError):
            pass

        # Sort by date then type
        events.sort(key=lambda e: (e["date"], e["type"]))
        return events