"""PostHog adapter — implements AnalyticsAdapter for product analytics.

Uses the PostHog Python SDK when the server is reachable.
Falls back to a local in-memory store when not available (dev/test).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from adapters import AnalyticsAdapter

logger = logging.getLogger(__name__)


class PostHogAdapter(AnalyticsAdapter):
    """Track events and identify users via PostHog (self-hosted OSS)."""

    def __init__(
        self,
        api_key: str | None = None,
        host: str = "http://localhost:8000",
    ) -> None:
        """
        Parameters
        ----------
        api_key : str, optional
            PostHog project API key (team token).
        host : str
            Self-hosted PostHog instance URL (default ``http://localhost:8000``).
        """
        self._api_key = api_key
        self._host = host.rstrip("/")
        self._client = None
        self._connected = False
        # Local fallback stores
        self._events: list[dict[str, Any]] = []
        self._identities: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        """Initialise the PostHog SDK client.

        Works even without a running server — PostHog's SDK buffers events.
        """
        try:
            from posthog import Posthog  # type: ignore[import-untyped]

            key = self._api_key or "phc_dev_noop"
            self._client = Posthog(api_key=key, host=self._host)
            # SDK doesn't immediately connect — we mark as connected optimistically
            self._connected = True
        except ImportError:
            logger.warning(
                "posthog SDK not installed — using local in-memory fallback. "
                "Install with: uv pip install posthog"
            )
            self._connected = False
        return self._connected

    def close(self) -> None:
        """Flush and shut down the PostHog client."""
        if self._client is not None:
            try:
                self._client.shutdown()
            except Exception:
                pass
            self._client = None
        self._connected = False

    # ------------------------------------------------------------------
    # AnalyticsAdapter interface
    # ------------------------------------------------------------------
    def track(self, event: str, properties: dict[str, Any] | None = None) -> None:
        """Track an event with optional properties.

        When the PostHog SDK is available, ``capture`` is called synchronously.
        (In production the SDK buffers and sends async via a background thread.)
        """
        props = properties or {}
        if self._connected and self._client is not None:
            try:
                self._client.capture(
                    distinct_id="system",
                    event=event,
                    properties=props,
                )
                return
            except Exception:
                self._connected = False

        # Local fallback
        self._events.append(
            {
                "event": event,
                "properties": props,
                "timestamp": time.time(),
            }
        )

    def identify(self, user_id: str, traits: dict[str, Any] | None = None) -> None:
        """Identify a user with optional traits.

        Maps directly to PostHog's ``identify`` call.
        """
        tr = traits or {}
        if self._connected and self._client is not None:
            try:
                self._client.identify(distinct_id=user_id, properties=tr)
                return
            except Exception:
                self._connected = False

        # Local fallback
        old = self._identities.get(user_id, {})
        old.update(tr)
        self._identities[user_id] = old

    # ------------------------------------------------------------------
    # PostHog-specific extras
    # ------------------------------------------------------------------
    def get_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return tracked events (local fallback only)."""
        return self._events[-limit:]

    def get_identities(self) -> dict[str, dict[str, Any]]:
        """Return known identities (local fallback only)."""
        return dict(self._identities)

    def __repr__(self) -> str:
        return (
            f"PostHogAdapter(host={self._host!r}, connected={self._connected})"
        )