"""SHUNYA Experience Layer — Stream E.

Voice, notifications, timeline, presence, cross-device continuity,
offline support, accessibility, themes, localization.
Architecture Freeze: composes from existing patterns, no new runtimes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class Notification:
    notification_id: str = ""
    owner_id: str = ""
    title: str = ""
    body: str = ""
    notification_type: str = "info"
    source_ucp: str = ""
    read: bool = False
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {"notification_id": self.notification_id, "title": self.title,
                "body": self.body, "type": self.notification_type,
                "source": self.source_ucp, "read": self.read,
                "timestamp": self.timestamp}


@dataclass
class TimelineEntry:
    entry_id: str = ""
    owner_id: str = ""
    title: str = ""
    description: str = ""
    entry_type: str = "event"
    source_ucp: str = ""
    object_id: str = ""
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {"entry_id": self.entry_id, "title": self.title,
                "description": self.description, "type": self.entry_type,
                "source": self.source_ucp, "timestamp": self.timestamp}


class ExperienceEngine:
    """Experience layer — voice, notifications, timeline, presence, themes."""

    def __init__(self) -> None:
        self._notifications: list[Notification] = []
        self._timeline: list[TimelineEntry] = []
        self._themes: dict[str, dict[str, Any]] = {
            "dark": {"bg": "#0d1117", "surface": "#161b22", "text": "#e6edf3",
                     "border": "#30363d", "accent": "#58a6ff"},
            "light": {"bg": "#ffffff", "surface": "#f6f8fa", "text": "#1f2328",
                      "border": "#d0d7de", "accent": "#0969da"},
            "high_contrast": {"bg": "#000000", "surface": "#0a0a0a", "text": "#ffffff",
                              "border": "#ffffff", "accent": "#ffff00"},
        }
        self._active_theme = "dark"
        self._locale = "en-IN"
        self._locales: dict[str, dict[str, str]] = {
            "en-IN": {"welcome": "Welcome", "search": "Search", "settings": "Settings"},
            "hi-IN": {"welcome": "स्वागत है", "search": "खोजें", "settings": "सेटिंग्स"},
            "ta-IN": {"welcome": "வரவேற்கிறோம்", "search": "தேடு", "settings": "அமைப்புகள்"},
        }
        self._presence: dict[str, dict[str, Any]] = {}

    # ── Notifications ──────────────────────────────────────────────────

    def notify(self, owner_id: str, title: str, body: str = "",
               notification_type: str = "info", source: str = "") -> Notification:
        import uuid
        n = Notification(notification_id=str(uuid.uuid4()), owner_id=owner_id,
                         title=title, body=body, notification_type=notification_type,
                         source_ucp=source)
        self._notifications.append(n)
        return n

    def get_notifications(self, owner_id: str, unread_only: bool = False,
                          limit: int = 50) -> list[dict[str, Any]]:
        ns = [n for n in self._notifications if n.owner_id == owner_id]
        if unread_only:
            ns = [n for n in ns if not n.read]
        return [n.to_dict() for n in ns[-limit:]]

    def mark_read(self, notification_id: str) -> bool:
        for n in self._notifications:
            if n.notification_id == notification_id:
                n.read = True
                return True
        return False

    def mark_all_read(self, owner_id: str) -> int:
        count = 0
        for n in self._notifications:
            if n.owner_id == owner_id and not n.read:
                n.read = True
                count += 1
        return count

    # ── Timeline ──────────────────────────────────────────────────────

    def add_timeline_entry(self, owner_id: str, title: str,
                           description: str = "", entry_type: str = "event",
                           source: str = "", object_id: str = "") -> TimelineEntry:
        import uuid
        e = TimelineEntry(entry_id=str(uuid.uuid4()), owner_id=owner_id,
                          title=title, description=description,
                          entry_type=entry_type, source_ucp=source,
                          object_id=object_id)
        self._timeline.append(e)
        return e

    def get_timeline(self, owner_id: str, limit: int = 50) -> list[dict[str, Any]]:
        entries = [e for e in self._timeline if e.owner_id == owner_id]
        return [e.to_dict() for e in entries[-limit:]]

    # ── Themes ─────────────────────────────────────────────────────────

    def list_themes(self) -> list[str]:
        return list(self._themes.keys())

    def set_theme(self, theme: str) -> bool:
        if theme in self._themes:
            self._active_theme = theme
            return True
        return False

    def get_theme(self) -> dict[str, Any]:
        return {"name": self._active_theme, "colors": self._themes[self._active_theme]}

    def add_theme(self, name: str, colors: dict[str, str]) -> None:
        self._themes[name] = colors

    # ── Localization ───────────────────────────────────────────────────

    def set_locale(self, locale: str) -> bool:
        if locale in self._locales:
            self._locale = locale
            return True
        return False

    def translate(self, key: str) -> str:
        return self._locales.get(self._locale, {}).get(key, key)

    def list_locales(self) -> list[str]:
        return list(self._locales.keys())

    def add_locale(self, code: str, translations: dict[str, str]) -> None:
        self._locales[code] = translations

    # ── Presence ───────────────────────────────────────────────────────

    def update_presence(self, user_id: str, status: str = "online",
                        device: str = "desktop", **kwargs: Any) -> None:
        self._presence[user_id] = {"user_id": user_id, "status": status,
                                    "device": device, "last_seen": _now_iso(),
                                    **kwargs}

    def get_presence(self, user_id: str) -> dict[str, Any] | None:
        return self._presence.get(user_id)

    def get_online_users(self) -> list[dict[str, Any]]:
        return [p for p in self._presence.values() if p.get("status") == "online"]

    # ── Lifecycle ──────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "notifications": len(self._notifications),
                "timeline": len(self._timeline), "theme": self._active_theme,
                "locale": self._locale, "online_users": len(self.get_online_users())}