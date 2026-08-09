"""Integration Registry — manages all external integrations.

Each integration registers itself with:
- name: unique identifier
- display_name: human-readable name
- icon: emoji icon
- status: connected/disconnected/error
- sync: last_sync_at, sync_status
- actions: list of available actions

ACTIVATION-14D: Integration Foundation.
All integrations use real APIs (no mocks).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class IntegrationBase:
    """Base class for all integrations."""

    name: str = ""
    display_name: str = ""
    icon: str = "🔌"
    description: str = ""

    def __init__(self):
        self._status: str = "disconnected"
        self._last_sync_at: Optional[datetime] = None
        self._error: Optional[str] = None

    def is_configured(self) -> bool:
        """Check if this integration has credentials configured."""
        return False

    def connect(self) -> bool:
        """Attempt to connect. Returns True if successful."""
        raise NotImplementedError

    def disconnect(self):
        """Disconnect and clean up."""
        self._status = "disconnected"
        self._last_sync_at = None

    def sync(self) -> dict:
        """Run a sync cycle. Returns summary dict."""
        raise NotImplementedError

    @property
    def status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "icon": self.icon,
            "connected": self._status == "connected",
            "status": self._status,
            "last_sync_at": self._last_sync_at.isoformat() if self._last_sync_at else None,
            "error": self._error,
            "configured": self.is_configured(),
        }


class IntegrationRegistry:
    """Registry of all integrations. Thread-safe singleton."""

    def __init__(self):
        self._integrations: dict[str, IntegrationBase] = {}

    def register(self, integration: IntegrationBase):
        """Register an integration."""
        self._integrations[integration.name] = integration
        logger.info("Integration registered: %s (%s)", integration.name, integration.display_name)

    def get(self, name: str) -> Optional[IntegrationBase]:
        return self._integrations.get(name)

    def list(self) -> list[dict]:
        return [intg.status for intg in self._integrations.values()]

    def connect_all(self):
        """Attempt to connect all configured integrations."""
        results = []
        for name, intg in self._integrations.items():
            if intg.is_configured():
                try:
                    ok = intg.connect()
                    results.append({"name": name, "connected": ok})
                    if ok:
                        logger.info("Integration connected: %s", name)
                    else:
                        logger.warning("Integration failed to connect: %s", name)
                except Exception as e:
                    logger.error("Integration connect error %s: %s", name, e)
                    results.append({"name": name, "connected": False, "error": str(e)})
        return results

    def sync_all(self) -> list[dict]:
        """Sync all connected integrations."""
        results = []
        for name, intg in self._integrations.items():
            if intg._status == "connected":
                try:
                    result = intg.sync()
                    results.append({"name": name, **result})
                except Exception as e:
                    logger.error("Integration sync error %s: %s", name, e)
                    results.append({"name": name, "status": "error", "error": str(e)})
        return results


# Singleton
registry = IntegrationRegistry()