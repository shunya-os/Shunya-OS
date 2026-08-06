"""Grafana adapter — implements MetricsAdapter for dashboard-centric monitoring.

Grafana is primarily a dashboarding and visualisation layer on top of metric
data sources (Prometheus, Loki, etc.).  This adapter wraps the Grafana HTTP
REST API and provides dashboard management alongside lightweight metric
recording/querying via its API.  Falls back to a local store when the server
is unavailable.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from adapters import MetricsAdapter

logger = logging.getLogger(__name__)


class GrafanaAdapter(MetricsAdapter):
    """Manage Grafana dashboards and query metric annotations."""

    def __init__(
        self,
        api_url: str = "http://localhost:3000",
        api_key: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        api_url : str
            Grafana server URL (default ``http://localhost:3000``).
        api_key : str, optional
            Grafana Service Account token or API key.
        """
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._session = None  # requests.Session
        self._connected = False
        # Local fallback stores
        self._local_store: dict[str, list[dict[str, Any]]] = {}
        self._dashboards: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        """Ping Grafana via the health endpoint."""
        try:
            import requests  # type: ignore[import-untyped]

            self._session = requests.Session()
            if self._api_key:
                self._session.headers.update({"Authorization": f"Bearer {self._api_key}"})
            resp = self._session.get(f"{self._api_url}/api/health", timeout=10)
            resp.raise_for_status()
            self._connected = True
        except Exception:
            logger.warning("Grafana not reachable — using local fallback")
            self._connected = False
            self._session = None
        return self._connected

    # ------------------------------------------------------------------
    # MetricsAdapter interface
    # ------------------------------------------------------------------
    def record(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a metric as an annotation in Grafana (or local store).

        Uses the Grafana Annotation API so the value appears on dashboards
        that query the ``$__annotations`` data source.
        """
        tags = tags or {}

        if self._connected and self._session is not None:
            try:
                payload = {
                    "text": f"{metric}: {value}",
                    "tags": list(tags.values()) + [metric],
                    "time": int(time.time() * 1000),
                }
                self._session.post(
                    f"{self._api_url}/api/annotations",
                    json=payload,
                    timeout=10,
                )
                return
            except Exception:
                self._connected = False

        # Local fallback
        self._local_store.setdefault(metric, []).append(
            {"value": value, "tags": tags, "timestamp": time.time()}
        )

    def query(self, metric: str, duration: str = "1h") -> list[dict[str, Any]]:
        """Query metric annotations from Grafana, or local store."""
        if self._connected and self._session is not None:
            try:
                resp = self._session.get(
                    f"{self._api_url}/api/annotations",
                    params={"tags": metric, "limit": 100},
                    timeout=10,
                )
                resp.raise_for_status()
                return resp.json()
            except Exception:
                self._connected = False

        return self._local_store.get(metric, [])

    # ------------------------------------------------------------------
    # Grafana-specific: dashboard management
    # ------------------------------------------------------------------
    def create_or_update_dashboard(
        self,
        title: str,
        panels: list[dict[str, Any]],
        folder_id: int = 0,
    ) -> str | None:
        """Create or update a Grafana dashboard.

        Parameters
        ----------
        title : str
            Dashboard title.
        panels : list[dict]
            Panel definitions (JSON model).
        folder_id : int
            Folder ID to place the dashboard in.

        Returns
        -------
        str or None
            Dashboard UID on success, None on failure / fallback.
        """
        if self._connected and self._session is not None:
            try:
                payload = {
                    "dashboard": {
                        "title": title,
                        "panels": panels,
                        "timezone": "browser",
                        "schemaVersion": 36,
                    },
                    "folderId": folder_id,
                    "overwrite": True,
                }
                resp = self._session.post(
                    f"{self._api_url}/api/dashboards/db",
                    json=payload,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                uid: str | None = data.get("uid")
                return uid
            except Exception:
                self._connected = False

        # Local fallback — store the dashboard definition
        dash_id = f"local_{title.lower().replace(' ', '_')}"
        self._dashboards[dash_id] = {"title": title, "panels": panels}
        return dash_id

    def list_dashboards(self) -> list[dict[str, Any]]:
        """List all Grafana dashboards."""
        if self._connected and self._session is not None:
            try:
                resp = self._session.get(
                    f"{self._api_url}/api/search",
                    params={"type": "dash-db"},
                    timeout=10,
                )
                resp.raise_for_status()
                return resp.json()
            except Exception:
                self._connected = False

        return list(self._dashboards.values())

    def __repr__(self) -> str:
        return (
            f"GrafanaAdapter(api_url={self._api_url!r}, connected={self._connected})"
        )