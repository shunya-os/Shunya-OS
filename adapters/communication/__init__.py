"""Communication adapters — SMTP, IMAP, CalDAV for Founder Daily Use."""

from __future__ import annotations

from adapters.communication.smtp import SMTPAdapter
from adapters.communication.imap import IMAPAdapter
from adapters.communication.caldav import CalDAVAdapter

COMMUNICATION_ADAPTERS: dict[str, type] = {
    "smtp": SMTPAdapter,
    "imap": IMAPAdapter,
    "caldav": CalDAVAdapter,
}

__all__ = [
    "SMTPAdapter",
    "IMAPAdapter",
    "CalDAVAdapter",
    "COMMUNICATION_ADAPTERS",
]