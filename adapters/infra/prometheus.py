"""Prometheus adapter — implements MetricsAdapter for time-series metrics.

Uses prometheus_client for in-process metric exposition (PushGateway / direct
HTTP scrape), and the Prometheus HTTP API for queries when a server is available.
Falls back to an in-memory store when no server is reachable.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from adapters import MetricsAdapter

logger = logging.getLogger(__name__)


class PrometheusAdapter(MetricsAdapter):
    """Record and query time-series metrics via Prometheus."""

    def __init__(self, pushgateway: str | None = None, api_url: str | None = None) -> None:
        """
        Parameters
        ----------
        pushgateway : str, optional
            PushGateway endpoint, e.g. "http://localhost:9091".
        api_url : str, optional
            Prometheus server HTTP API, e.g. "http://localhost:9090".
        """
        self._pushgateway = pushgateway
        self._api_url = api_url
        self._registry = None  # prometheus_client CollectorRegistry
        self._local_store: dict[str, list[dict[str, Any]]] = {}  # fallback
        self._connected = False

    # ------------------------------------------------------------------
    # Connection / setup
    # ------------------------------------------------------------------
    def setup(self) -> None:
        """Initialise the Prometheus client registry."""
        try:
            from prometheus_client import CollectorRegistry  # type: ignore[import-untyped]

            self._registry = CollectorRegistry()
            self._connected = True
        except ImportError:
            logger.warning("prometheus_client not installed — using local in-memory fallback")
            self._connected = False

    # ------------------------------------------------------------------
    # MetricsAdapter interface
    # ------------------------------------------------------------------
    def record(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a metric observation.

        When prometheus_client is available, pushes to the PushGateway
        (or updates local registry).  Otherwise appends to an in-memory store.
        """
        tags = tags or {}

        if self._connected and self._registry is not None:
            try:
                from prometheus_client import Gauge, push_to_gateway  # type: ignore[import-untyped]

                # Use a unique gauge name incorporating tags for simplicity
                label_names = sorted(tags.keys())
                gauge = Gauge(
                    metric,
                    metric,
                    labelnames=label_names,
                    registry=self._registry,
                )
                if label_names:
                    gauge.labels(**{k: tags[k] for k in label_names}).set(value)
                else:
                    gauge.set(value)

                if self._pushgateway:
                    push_to_gateway(self._pushgateway, job=metric, registry=self._registry)
                return
            except Exception:
                self._connected = False

        # Local fallback
        entry = {"value": value, "tags": tags, "timestamp": time.time()}
        self._local_store.setdefault(metric, []).append(entry)

    def query(self, metric: str, duration: str = "1h") -> list[dict[str, Any]]:
        """Query metric values over *duration*.

        When *api_url* is set, uses the Prometheus HTTP API.
        Otherwise returns the local in-memory store.
        """
        if self._api_url:
            try:
                import requests  # type: ignore[import-untyped]

                # Prometheus instant query — last value within the range
                resp = requests.get(
                    f"{self._api_url}/api/v1/query",
                    params={"query": metric},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                results: list[dict[str, Any]] = []
                for result in data.get("data", {}).get("result", []):
                    results.append(
                        {
                            "metric": result["metric"],
                            "value": result["value"][1] if result.get("value") else None,
                            "timestamp": result["value"][0] if result.get("value") else None,
                        }
                    )
                return results
            except Exception:
                logger.warning("Prometheus API query failed — falling back to local store")

        # Local fallback
        entries = self._local_store.get(metric, [])
        return entries

    def __repr__(self) -> str:
        return (
            f"PrometheusAdapter(pushgateway={self._pushgateway!r}, "
            f"api_url={self._api_url!r}, connected={self._connected})"
        )