"""Canonical timestamp utility — single source of truth for time.

PHASE 3: Time consistency enforcement.
All modules MUST use now() instead of datetime.now().
Ensures timezone-aware UTC timestamps everywhere.
"""

from datetime import datetime, timezone


def now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime.

    Usage:
        from app.core.time.clock import now
        created_at = now()
    """
    return datetime.now(timezone.utc)