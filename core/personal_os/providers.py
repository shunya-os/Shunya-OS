"""Universal Providers — orchestrate existing open-source software.

Composes with: LibreOffice, ComfyUI, Whisper, Playwright, etc.
Never unnecessarily reimplements mature software.
"""

from __future__ import annotations

from typing import Any

from adapters import DOCUMENT_ADAPTERS, IMAGE_ADAPTERS, INFRA_ADAPTERS


class ProviderOrchestrator:
    """Orchestrates third-party providers without duplicating them."""

    def __init__(self) -> None:
        self._providers = {
            "documents": {"name": "LibreOffice/OnlyOffice", "status": "available",
                          "purpose": "Document creation, editing, conversion",
                          "adapter_key": None},
            "image_gen": {"name": "ComfyUI + FLUX", "status": "available",
                          "purpose": "Image generation and editing",
                          "adapter_key": None},
            "speech": {"name": "Whisper + Piper/Kokoro", "status": "available",
                       "purpose": "Speech-to-text and text-to-speech",
                       "adapter_key": None},
            "browser": {"name": "Playwright", "status": "available",
                        "purpose": "Browser automation and testing",
                        "adapter_key": None},
            "search": {"name": "SearXNG", "status": "available",
                       "purpose": "Privacy-respecting search",
                       "adapter_key": None},
            "visualization": {"name": "Apache ECharts", "status": "available",
                              "purpose": "Data visualization"},
            "ocr": {"name": "Tesseract/PaddleOCR", "status": "available",
                    "purpose": "Optical character recognition"},
            "search_engine": {"name": "OpenSearch", "status": "available",
                              "purpose": "Full-text and vector search",
                              "adapter_key": None},
            "storage": {"name": "MinIO", "status": "available",
                        "purpose": "S3-compatible object storage",
                        "adapter_key": None},
            "vector_db": {"name": "PostgreSQL + pgvector", "status": "available",
                          "purpose": "Relational + vector database",
                          "adapter_key": None},
            # --- Infrastructure adapters (lazy-initialised) ---
            "cache": {"name": "Redis", "status": "adapter",
                      "purpose": "In-memory cache and message broker",
                      "adapter_key": "redis"},
            "messaging": {"name": "RabbitMQ", "status": "adapter",
                          "purpose": "Message queue and task distribution",
                          "adapter_key": "rabbitmq"},
            "monitoring": {"name": "Grafana + Prometheus", "status": "adapter",
                           "purpose": "Metrics, dashboards, and monitoring",
                           "adapter_key": None},  # multi-slot
            "analytics": {"name": "PostHog OSS", "status": "adapter",
                          "purpose": "Product analytics",
                          "adapter_key": "posthog"},
        }
        # Lazy-created adapter instances
        self._adapters: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Adapter access
    # ------------------------------------------------------------------
    def get_adapter(self, key: str) -> Any | None:
        """Return a concrete infra adapter instance, creating it on first access.

        Supported keys: ``redis``, ``rabbitmq``, ``prometheus``, ``grafana``, ``posthog``.
        """
        if key in self._adapters:
            return self._adapters[key]

        # Look up the adapter class from the INFRA_ADAPTERS registry
        cls = INFRA_ADAPTERS.get(key)
        if cls is None:
            return None

        # Create with sensible defaults (overridable via env later)
        instance = cls()
        self._adapters[key] = instance
        return instance

    def get_cache(self) -> Any | None:
        """Shortcut: return the Redis cache adapter."""
        return self.get_adapter("redis")

    def get_messaging(self) -> Any | None:
        """Shortcut: return the RabbitMQ messaging adapter."""
        return self.get_adapter("rabbitmq")

    def get_metrics(self) -> tuple[Any | None, Any | None]:
        """Shortcut: return (prometheus, grafana) adapters."""
        return self.get_adapter("prometheus"), self.get_adapter("grafana")

    def get_analytics(self) -> Any | None:
        """Shortcut: return the PostHog analytics adapter."""
        return self.get_adapter("posthog")

    # ------------------------------------------------------------------
    # Provider listing
    # ------------------------------------------------------------------
    def list_available(self) -> dict[str, Any]:
        """Return all providers with enriched status for adapter-backed ones."""
        enriched = dict(self._providers)

        for name, info in enriched.items():
            adapter_key = info.get("adapter_key")
            if adapter_key:
                adapter = self._adapters.get(adapter_key)
                if adapter is not None:
                    # Report real connection status
                    connected = getattr(adapter, "_connected", False)
                    info["status"] = "connected" if connected else "instantiated"
                else:
                    info["status"] = "available"  # will lazy-init on first get_adapter

        # For monitoring (multi-slot), check both Prometheus and Grafana
        mon_info = enriched.get("monitoring", {})
        prom = self._adapters.get("prometheus")
        graf = self._adapters.get("grafana")
        if prom or graf:
            prom_ok = getattr(prom, "_connected", False) if prom else False
            graf_ok = getattr(graf, "_connected", False) if graf else False
            if prom_ok and graf_ok:
                mon_info["status"] = "connected"
            elif prom_ok or graf_ok:
                mon_info["status"] = "partial"
            else:
                mon_info["status"] = "instantiated"

        return {"providers": enriched, "count": len(enriched)}

    def is_available(self, name: str) -> bool:
        return name in self._providers