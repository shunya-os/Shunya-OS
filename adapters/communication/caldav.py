"""CalDAV calendar adapter.

Implements the CalendarAdapter interface using ``requests`` (HTTP client)
to speak the CalDAV protocol (RFC 4791) against any standards-compliant
CalDAV server (e.g. Nextcloud, Baïkal, FastMail, iCloud, etc.).

If ``caldav`` library is installed, it delegates to that for richer
calendar operations.  Otherwise, sends raw CalDAV XML over HTTP(S).

Usage::

    adapter = CalDAVAdapter(
        base_url="https://calendar.example.com/remote.php/dav/",
        username="user", password="pass",
    )
    adapter.create_event(
        summary="Team Standup",
        dtstart="2025-06-01T09:00:00",
        dtend="2025-06-01T09:30:00",
    )
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from adapters import CalendarAdapter

logger = logging.getLogger(__name__)


class CalDAVAdapter(CalendarAdapter):
    """Create, read, query, and delete calendar events via CalDAV.

    Parameters
    ----------
    base_url : str
        Base CalDAV URL, e.g.
        ``https://calendar.example.com/remote.php/dav/calendars/user/default/``.
    username : str | None
        WebDAV authentication username.
    password : str | None
        WebDAV authentication password.
    calendar_name : str
        Calendar name to operate on (default "personal").
    """

    def __init__(
        self,
        base_url: str = "",
        username: str | None = None,
        password: str | None = None,
        calendar_name: str = "personal",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._calendar_name = calendar_name
        self._use_caldav_lib: bool | None = None  # lazy check

    # ------------------------------------------------------------------
    # CalendarAdapter interface
    # ------------------------------------------------------------------

    def create_event(
        self,
        summary: str,
        dtstart: str,
        dtend: str,
        description: str = "",
        location: str = "",
        timezone: str = "UTC",
        attendees: list[str] | None = None,
        recurrence: str | None = None,
    ) -> dict[str, Any]:
        """Create a calendar event.

        Parameters
        ----------
        summary : str
            Event title.
        dtstart : str
            Start datetime in ISO-8601 format, e.g. ``"2025-06-01T09:00:00"``.
        dtend : str
            End datetime in ISO-8601 format.
        description : str
            Event description / body.
        location : str
            Physical or virtual location.
        timezone : str
            IANA timezone identifier (default "UTC").
        attendees : list[str] | None
            List of email addresses for attendees.
        recurrence : str | None
            RRULE string, e.g. ``"FREQ=WEEKLY;BYDAY=MO,WE,FR"``.

        Returns
        -------
        dict
            ``{"success": True, "uid": "<uuid>", "href": "<url>"}`` on success,
            ``{"success": False, "error": "..."}`` on failure.
        """
        # Try the caldav library path first
        try:
            import caldav  # type: ignore[import-untyped]

            self._use_caldav_lib = True
        except ImportError:
            self._use_caldav_lib = False

        if self._use_caldav_lib:
            return self._create_via_caldav_lib(
                summary, dtstart, dtend, description, location, timezone,
                attendees, recurrence,
            )

        return self._create_via_requests(
            summary, dtstart, dtend, description, location, timezone,
            attendees, recurrence,
        )

    def get_events(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Query calendar events within a date range.

        Parameters
        ----------
        date_from : str | None
            ISO-8601 start of range.
        date_to : str | None
            ISO-8601 end of range.
        limit : int
            Max events to return (default 50).

        Returns
        -------
        list[dict]
            Each dict has keys: ``uid``, ``summary``, ``dtstart``, ``dtend``,
            ``description``, ``location``, ``recurrence``.
        """
        try:
            import caldav
            self._use_caldav_lib = True
        except ImportError:
            self._use_caldav_lib = False

        if self._use_caldav_lib:
            return self._query_via_caldav_lib(date_from, date_to, limit)

        return self._query_via_requests(date_from, date_to, limit)

    # ------------------------------------------------------------------
    # caldav library path
    # ------------------------------------------------------------------

    def _create_via_caldav_lib(
        self,
        summary: str,
        dtstart: str,
        dtend: str,
        description: str,
        location: str,
        timezone: str,
        attendees: list[str] | None,
        recurrence: str | None,
    ) -> dict[str, Any]:
        """Create an event using the caldav PyPI library."""
        try:
            import caldav
            from datetime import datetime

            # Parse datetimes
            fmt = "%Y-%m-%dT%H:%M:%S" if "T" in dtstart else "%Y-%m-%d"
            start_dt = datetime.strptime(dtstart[:19], fmt) if "T" in dtstart else datetime.strptime(dtstart, fmt)
            end_dt = datetime.strptime(dtend[:19], fmt) if "T" in dtend else datetime.strptime(dtend, fmt)

            uid = uuid.uuid4().hex
            href = f"{uid}.ics"

            # Build ICS
            ics_lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//SHUNYA//CalDAVAdapter//EN",
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{summary}",
            ]
            if description:
                escaped_desc = description.replace("\n", "\\n")
                ics_lines.append(f"DESCRIPTION:{escaped_desc}")
            if location:
                ics_lines.append(f"LOCATION:{location}")
            if recurrence:
                ics_lines.append(f"RRULE:{recurrence}")
            if attendees:
                for att in attendees:
                    ics_lines.append(f"ATTENDEE:mailto:{att}")
            ics_lines.extend(["END:VEVENT", "END:VCALENDAR"])
            ics_data = "\r\n".join(ics_lines)

            client = caldav.DAVClient(
                url=self._base_url,
                username=self._username,
                password=self._password,
            )
            principal = client.principal()
            calendars = principal.calendars()
            if not calendars:
                return {"success": False, "error": "No calendars found on server"}

            cal = calendars[0]
            cal.save_event(ics_data)

            logger.info("CalDAV event created: %s", summary)
            return {"success": True, "uid": uid, "href": href}

        except Exception as exc:
            logger.error("CalDAV (lib) create failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def _query_via_caldav_lib(
        self,
        date_from: str | None,
        date_to: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Query events using the caldav PyPI library."""
        try:
            import caldav
            from datetime import datetime

            client = caldav.DAVClient(
                url=self._base_url,
                username=self._username,
                password=self._password,
            )
            principal = client.principal()
            calendars = principal.calendars()
            if not calendars:
                return []

            cal = calendars[0]
            fmt = "%Y%m%dT%H%M%S"
            start = datetime.strptime(date_from.replace("-", "").replace(":", "")[:15], fmt) if date_from else None
            end = datetime.strptime(date_to.replace("-", "").replace(":", "")[:15], fmt) if date_to else None

            events = cal.date_search(start=start, end=end) if (start and end) else cal.events()
            results: list[dict[str, Any]] = []
            for ev in events[:limit]:
                results.append(self._parse_event(ev.data))
            return results

        except Exception as exc:
            logger.error("CalDAV (lib) query failed: %s", exc)
            return []

    @staticmethod
    def _parse_event(ics_data: str) -> dict[str, Any]:
        """Minimal iCalendar parser — extract key VCALENDAR fields."""
        uid = ""
        summary = ""
        dtstart = ""
        dtend = ""
        description = ""
        location = ""
        recurrence = ""
        for line in ics_data.splitlines():
            upper = line.upper()
            if upper.startswith("UID:"):
                uid = line[4:].strip()
            elif upper.startswith("SUMMARY:"):
                summary = line[8:].strip()
            elif upper.startswith("DTSTART"):
                dtstart = line.split(":")[-1].strip() if ":" in line else ""
            elif upper.startswith("DTEND"):
                dtend = line.split(":")[-1].strip() if ":" in line else ""
            elif upper.startswith("DESCRIPTION:"):
                description = line[12:].strip().replace("\\n", "\n")
            elif upper.startswith("LOCATION:"):
                location = line[9:].strip()
            elif upper.startswith("RRULE:"):
                recurrence = line[6:].strip()
        return {
            "uid": uid,
            "summary": summary,
            "dtstart": dtstart or "",
            "dtend": dtend or "",
            "description": description,
            "location": location,
            "recurrence": recurrence or "",
        }

    # ------------------------------------------------------------------
    # Raw HTTP requests path (no caldav library)
    # ------------------------------------------------------------------

    def _create_via_requests(
        self,
        summary: str,
        dtstart: str,
        dtend: str,
        description: str,
        location: str,
        timezone: str,
        attendees: list[str] | None,
        recurrence: str | None,
    ) -> dict[str, Any]:
        """Create an event via raw CalDAV XML/HTTP using ``requests``."""
        uid = uuid.uuid4().hex
        href = f"{uid}.ics"

        # Build ICS
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//SHUNYA//CalDAVAdapter//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART;TZID={timezone}:{self._to_ical_dt(dtstart)}",
            f"DTEND;TZID={timezone}:{self._to_ical_dt(dtend)}",
            f"SUMMARY:{summary}",
        ]
        if description:
            escaped_desc = description.replace("\n", "\\n")
            ics_lines.append(f"DESCRIPTION:{escaped_desc}")
        if location:
            ics_lines.append(f"LOCATION:{location}")
        if recurrence:
            ics_lines.append(f"RRULE:{recurrence}")
        if attendees:
            for att in attendees:
                ics_lines.append(f"ATTENDEE:mailto:{att}")
        ics_lines.extend(["END:VEVENT", "END:VCALENDAR"])
        ics_data = "\r\n".join(ics_lines)

        cal_url = self._base_url.rstrip("/")
        put_url = f"{cal_url}/{href}"

        try:
            import requests

            resp = requests.put(
                put_url,
                data=ics_data,
                headers={"Content-Type": "text/calendar; charset=utf-8"},
                auth=(self._username or "", self._password or ""),
                timeout=30,
            )

            if resp.status_code in (201, 204):
                logger.info("CalDAV event created via requests: %s", summary)
                return {"success": True, "uid": uid, "href": put_url}
            else:
                error = f"PUT {put_url} returned {resp.status_code}: {resp.text[:500]}"
                logger.error("CalDAV create failed: %s", error)
                return {"success": False, "error": error}

        except Exception as exc:
            logger.error("CalDAV (requests) create failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def _query_via_requests(
        self,
        date_from: str | None,
        date_to: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Query events via raw CalDAV REPORT request."""
        import textwrap
        cal_url = self._base_url.rstrip("/")

        # Build CalDAV REPORT XML (RFC 4791, §7.8)
        report_lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<C:calendar-query xmlns:C="urn:ietf:params:xml:ns:caldav"',
            '                  xmlns:D="DAV:">',
            '  <D:prop>',
            '    <D:getetag/>',
            '    <C:calendar-data/>',
            '  </D:prop>',
            '  <C:filter>',
            '    <C:comp-filter name="VCALENDAR">',
            '      <C:comp-filter name="VEVENT">',
        ]

        if date_from or date_to:
            start_str = self._to_ical_dt(date_from) if date_from else ""
            end_str = self._to_ical_dt(date_to) if date_to else ""
            report_lines.append(
                f'        <C:time-range start="{start_str}" end="{end_str}"/>'
            )

        report_lines.extend([
            '      </C:comp-filter>',
            '    </C:comp-filter>',
            '  </C:filter>',
            '</C:calendar-query>',
        ])
        report_xml = "\n".join(report_lines)

        try:
            import requests

            resp = requests.request(
                "REPORT",
                cal_url,
                data=report_xml,
                headers={"Content-Type": "application/xml; charset=utf-8", "Depth": "1"},
                auth=(self._username or "", self._password or ""),
                timeout=30,
            )

            if resp.status_code not in (200, 207):
                logger.warning("CalDAV query returned %s", resp.status_code)
                return []

            results: list[dict[str, Any]] = []
            import xml.etree.ElementTree as ET

            try:
                root = ET.fromstring(resp.content)
                for cal_data in root.iter("{urn:ietf:params:xml:ns:caldav}calendar-data"):
                    if cal_data.text:
                        results.append(self._parse_event(cal_data.text))
                        if len(results) >= limit:
                            break
            except ET.ParseError:
                logger.warning("Failed to parse CalDAV XML response")

            return results

        except Exception as exc:
            logger.error("CalDAV (requests) query failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_ical_dt(iso_dt: str | None, fmt: str = "%Y%m%dT%H%M%S") -> str:
        """Convert ISO-8601 datetime to iCalendar format."""
        if not iso_dt:
            return ""
        # Handle "T" separator
        if "T" in iso_dt:
            date_part = iso_dt[:10].replace("-", "")
            time_part = iso_dt[11:19].replace(":", "")
            return f"{date_part}T{time_part}"
        return iso_dt.replace("-", "")

    def __repr__(self) -> str:
        return (
            f"CalDAVAdapter(base_url={self._base_url!r}, "
            f"username={self._username!r}, "
            f"calendar={self._calendar_name!r})"
        )