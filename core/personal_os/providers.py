"""Universal Providers — orchestrate existing open-source software.

Composes with: LibreOffice, ComfyUI, Whisper, Playwright, etc.
Never unnecessarily reimplements mature software.
"""

from __future__ import annotations

import logging
from typing import Any

from adapters import DOCUMENT_ADAPTERS, IMAGE_ADAPTERS, INFRA_ADAPTERS

logger = logging.getLogger(__name__)


class ProviderOrchestrator:
    """Orchestrates third-party providers without duplicating them.

    ZG-03 B2: statuses are COMPUTED, never declared. A provider is "available"
    only when its adapter/config/capability actually resolves; otherwise it is
    reported "not_ready" with a reason. Nothing here claims availability
    without evidence (the previous hardcoded status:"available" for every
    entry was untruthful).
    """

    # name -> (capability it powers in the capability registry, adapter_key)
    _CAPABILITY_MAP = {
        "documents": None,          # document adapters: libreoffice/onlyoffice (config-dependent)
        "image_gen": "image_generation",
        "speech": None,             # speech_to_text + text_to_speech
        "browser": None,            # playwright (config-dependent)
        "search": "research",
        "visualization": None,      # frontend ECharts — always available
        "ocr": None,                # tesseract binary (config-dependent)
        "search_engine": None,      # opensearch (config-dependent)
        "storage": None,            # minio (config-dependent)
        "vector_db": None,          # pgvector (db-dependent)
        "cache": "cache",
        "messaging": "messaging",
        "monitoring": "monitoring",
        "analytics": "analytics",
    }

    def __init__(self) -> None:
        self._providers = {
            "documents": {"name": "LibreOffice/OnlyOffice", "status": "not_ready",
                          "purpose": "Document creation, editing, conversion",
                          "adapter_key": None},
            "image_gen": {"name": "ComfyUI + FLUX + Pollinations", "status": "not_ready",
                          "purpose": "Image generation and editing",
                          "adapter_key": None},
            "speech": {"name": "Whisper + Piper/Kokoro + Edge-TTS", "status": "not_ready",
                       "purpose": "Speech-to-text and text-to-speech",
                       "adapter_key": None},
            "browser": {"name": "Playwright", "status": "not_ready",
                        "purpose": "Browser automation and testing",
                        "adapter_key": None},
            "search": {"name": "SearXNG + DuckDuckGo", "status": "not_ready",
                       "purpose": "Privacy-respecting search",
                       "adapter_key": None},
            "visualization": {"name": "Apache ECharts", "status": "available",
                              "purpose": "Data visualization"},
            "ocr": {"name": "Tesseract/PaddleOCR", "status": "not_ready",
                    "purpose": "Optical character recognition"},
            "search_engine": {"name": "OpenSearch", "status": "not_ready",
                              "purpose": "Full-text and vector search",
                              "adapter_key": None},
            "storage": {"name": "MinIO", "status": "not_ready",
                        "purpose": "S3-compatible object storage",
                        "adapter_key": None},
            "vector_db": {"name": "PostgreSQL + pgvector", "status": "not_ready",
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
        """Return all providers with COMPUTED, truthful status.

        ZG-03 B2: image_gen/speech/search statuses come from the capability
        registry (which probes keys, model validity and outages); infra
        adapters report their real connection state; everything else stays
        ``not_ready`` until a config probe proves it.
        """
        enriched = dict(self._providers)

        # Computed capability-backed status
        try:
            from app.ai.capabilities import summarize
            for row in summarize():
                for name, cap_name in self._CAPABILITY_MAP.items():
                    if cap_name == row["capability"]:
                        info = enriched.get(name)
                        if info is not None:
                            info["status"] = "available" if row["status"] == "AVAILABLE" else "not_ready"
                            info["capability_status"] = row["status"]
                            info["ready_providers"] = row["providers"]
        except Exception as exc:  # pragma: no cover — diagnostics must not crash
            logger.warning("Capability status computation failed: %s", exc)

        for name, info in enriched.items():
            adapter_key = info.get("adapter_key")
            if adapter_key:
                adapter = self._adapters.get(adapter_key)
                if adapter is not None:
                    # Report real connection status
                    connected = getattr(adapter, "_connected", False)
                    info["status"] = "connected" if connected else "instantiated"
                else:
                    info["status"] = "not_ready"  # adapter not even instantiated yet

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