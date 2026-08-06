"""Provider Adapter Interfaces.

Every provider implements a stable capability interface.
Providers are replaceable without changing architecture.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DocumentAdapter(ABC):
    """Document creation, editing, and conversion."""
    @abstractmethod
    def create_document(self, title: str, content: str, fmt: str = "odt") -> str: ...
    @abstractmethod
    def edit_document(
        self,
        path: str,
        new_content: str | None = None,
        insert_at: str | int | None = None,
        **kwargs: Any,
    ) -> str: ...
    @abstractmethod
    def convert(self, source_path: str, target_fmt: str) -> str: ...
    @abstractmethod
    def extract_text(self, path: str) -> str: ...


class ImageAdapter(ABC):
    """Image generation and editing."""
    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str: ...
    @abstractmethod
    def edit(self, image_path: str, prompt: str, **kwargs: Any) -> str: ...


class SpeechRecognitionAdapter(ABC):
    """Speech-to-text."""
    @abstractmethod
    def transcribe(self, audio_path: str, language: str = "en") -> dict[str, Any]: ...


class SpeechSynthesisAdapter(ABC):
    """Text-to-speech."""
    @abstractmethod
    def synthesize(self, text: str, voice: str = "default", **kwargs: Any) -> str: ...


class BrowserAdapter(ABC):
    """Browser automation."""
    @abstractmethod
    def navigate(self, url: str) -> str: ...
    @abstractmethod
    def screenshot(self, url: str) -> str: ...
    @abstractmethod
    def execute(self, url: str, script: str) -> Any: ...


class EmailSenderAdapter(ABC):
    """Outbound email sending via SMTP."""
    @abstractmethod
    def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        from_addr: str | None = None,
        html: bool = False,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]: ...


class EmailReaderAdapter(ABC):
    """Inbound email reading via IMAP."""
    @abstractmethod
    def read_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        since: str | None = None,
        search_criteria: str | None = None,
        mark_seen: bool = True,
    ) -> list[dict[str, Any]]: ...
    @abstractmethod
    def list_folders(self) -> list[dict[str, Any]]: ...


class CalendarAdapter(ABC):
    """Calendar event management via CalDAV."""
    @abstractmethod
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
    ) -> dict[str, Any]: ...
    @abstractmethod
    def get_events(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]: ...


class SearchAdapter(ABC):
    """Web and document search."""
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]: ...


class StorageAdapter(ABC):
    """Object and file storage."""
    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> bool: ...
    @abstractmethod
    def download(self, remote_path: str, local_path: str) -> bool: ...
    @abstractmethod
    def list(self, prefix: str = "") -> list[str]: ...


class VectorSearchAdapter(ABC):
    """Semantic and vector search."""
    @abstractmethod
    def index(self, collection: str, documents: list[dict[str, Any]]) -> int: ...
    @abstractmethod
    def search(self, collection: str, query: str, limit: int = 10) -> list[dict[str, Any]]: ...


class CacheAdapter(ABC):
    """In-memory cache."""
    @abstractmethod
    def get(self, key: str) -> Any: ...
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300) -> bool: ...
    @abstractmethod
    def delete(self, key: str) -> bool: ...


class MessagingAdapter(ABC):
    """Message queue and task distribution."""
    @abstractmethod
    def publish(self, queue: str, message: Any) -> bool: ...
    @abstractmethod
    def consume(self, queue: str, callback: Any) -> None: ...


class MetricsAdapter(ABC):
    """Metrics and monitoring."""
    @abstractmethod
    def record(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None: ...
    @abstractmethod
    def query(self, metric: str, duration: str = "1h") -> list[dict[str, Any]]: ...


class AnalyticsAdapter(ABC):
    """Product analytics."""
    @abstractmethod
    def track(self, event: str, properties: dict[str, Any] | None = None) -> None: ...
    @abstractmethod
    def identify(self, user_id: str, traits: dict[str, Any] | None = None) -> None: ...


# ── Concrete document adapters ──────────────────────────────────────

from adapters.document.libreoffice import LibreOfficeAdapter
from adapters.document.onlyoffice import OnlyOfficeAdapter

# ── Concrete image adapters ─────────────────────────────────────────

from adapters.image.comfyui import ComfyUIAdapter
from adapters.image.flux import FluxAdapter

# ── Concrete speech adapters ────────────────────────────────────────

from adapters.speech.whisper import WhisperAdapter
from adapters.speech.piper import PiperAdapter
from adapters.speech.kokoro import KokoroAdapter


# Convenience registry: name → class
DOCUMENT_ADAPTERS: dict[str, type[DocumentAdapter]] = {
    "libreoffice": LibreOfficeAdapter,
    "onlyoffice": OnlyOfficeAdapter,
}

IMAGE_ADAPTERS: dict[str, type[ImageAdapter]] = {
    "comfyui": ComfyUIAdapter,
    "flux": FluxAdapter,
}

SPEECH_RECOGNITION_ADAPTERS: dict[str, type[SpeechRecognitionAdapter]] = {
    "whisper": WhisperAdapter,
}

SPEECH_SYNTHESIS_ADAPTERS: dict[str, type[SpeechSynthesisAdapter]] = {
    "piper": PiperAdapter,
    "kokoro": KokoroAdapter,
}

# ---------------------------------------------------------------------------
# Concrete infra / automation / search / storage adapters (optional deps)
# ---------------------------------------------------------------------------

# Cache
from adapters.infra.redis import RedisCacheAdapter  # noqa: F402
# Messaging
from adapters.infra.rabbitmq import RabbitMQAdapter  # noqa: F402
# Metrics
from adapters.infra.prometheus import PrometheusAdapter  # noqa: F402
from adapters.infra.grafana import GrafanaAdapter  # noqa: F402
# Analytics
from adapters.infra.posthog import PostHogAdapter  # noqa: F402
# Automation
from adapters.automation.playwright import PlaywrightAdapter  # noqa: F402
# Communication
from adapters.communication.smtp import SMTPAdapter  # noqa: F402
from adapters.communication.imap import IMAPAdapter  # noqa: F402
from adapters.communication.caldav import CalDAVAdapter  # noqa: F402
# Search
from adapters.search.searxng import SearXNGAdapter  # noqa: F402
from adapters.search.opensearch import OpenSearchAdapter  # noqa: F402
from adapters.search.pgvector import PGVectorAdapter  # noqa: F402
# Storage
from adapters.storage.minio import MinIOAdapter  # noqa: F402

COMMUNICATION_ADAPTERS: dict[str, type] = {
    "smtp": SMTPAdapter,
    "imap": IMAPAdapter,
    "caldav": CalDAVAdapter,
}

INFRA_ADAPTERS: dict[str, type] = {
    "redis": RedisCacheAdapter,
    "rabbitmq": RabbitMQAdapter,
    "prometheus": PrometheusAdapter,
    "grafana": GrafanaAdapter,
    "posthog": PostHogAdapter,
    "playwright": PlaywrightAdapter,
    "searxng": SearXNGAdapter,
    "opensearch": OpenSearchAdapter,
    "pgvector": PGVectorAdapter,
    "minio": MinIOAdapter,
}


__all__ = [
    # Interfaces
    "DocumentAdapter",
    "ImageAdapter",
    "SpeechRecognitionAdapter",
    "SpeechSynthesisAdapter",
    "BrowserAdapter",
    "EmailSenderAdapter",
    "EmailReaderAdapter",
    "CalendarAdapter",
    "SearchAdapter",
    "StorageAdapter",
    "VectorSearchAdapter",
    "CacheAdapter",
    "MessagingAdapter",
    "MetricsAdapter",
    "AnalyticsAdapter",
    # Concrete adapters (document / image / speech — eagerly loaded)
    "LibreOfficeAdapter",
    "OnlyOfficeAdapter",
    "ComfyUIAdapter",
    "FluxAdapter",
    "WhisperAdapter",
    "PiperAdapter",
    "KokoroAdapter",
    # Concrete adapters (infra / automation / search / storage)
    "PlaywrightAdapter",
    # Concrete adapters (communication)
    "SMTPAdapter",
    "IMAPAdapter",
    "CalDAVAdapter",
    "SearXNGAdapter",
    "OpenSearchAdapter",
    "PGVectorAdapter",
    "MinIOAdapter",
    "RedisCacheAdapter",
    "RabbitMQAdapter",
    "PrometheusAdapter",
    "GrafanaAdapter",
    "PostHogAdapter",
    # Registries
    "DOCUMENT_ADAPTERS",
    "IMAGE_ADAPTERS",
    "SPEECH_RECOGNITION_ADAPTERS",
    "SPEECH_SYNTHESIS_ADAPTERS",
    "COMMUNICATION_ADAPTERS",
    "INFRA_ADAPTERS",
]