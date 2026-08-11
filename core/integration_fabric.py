"""
SHUNYA — Provider-Neutral Integration Fabric (FDA5-G4).

Clean interfaces so SHUNYA core depends on capabilities, not providers.
Every external integration implements one of these interfaces.

Provider-specific implementations live behind the boundary.
Core SHUNYA domain code imports from this module, never from provider modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════
# Shared types
# ═══════════════════════════════════════════════════════════════════

class ConnectionStatus(Enum):
    CONFIGURED = "configured"
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ProviderHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    AUTH_FAILURE = "auth_failure"


@dataclass
class IntegrationConfig:
    """Configuration for a provider integration."""
    provider_name: str
    tenant_id: str
    credentials: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)
    scopes: list = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ProviderStatus:
    """Health and status of a provider connection."""
    provider: str
    status: ConnectionStatus
    health: ProviderHealth
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


# ═══════════════════════════════════════════════════════════════════
# Provider Interfaces
# ═══════════════════════════════════════════════════════════════════

class EmailProvider(ABC):
    """Interface for email providers (Gmail, Outlook, SMTP, etc.)."""

    @abstractmethod
    def connect(self, config: IntegrationConfig) -> bool:
        ...

    @abstractmethod
    def disconnect(self) -> bool:
        ...

    @abstractmethod
    def fetch_emails(self, since: Optional[datetime] = None, limit: int = 50) -> list[dict]:
        ...

    @abstractmethod
    def send_email(self, to: list[str], subject: str, body: str, **kwargs) -> dict:
        ...

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        ...

    @abstractmethod
    def refresh_auth(self) -> bool:
        ...


class CalendarProvider(ABC):
    """Interface for calendar providers."""

    @abstractmethod
    def connect(self, config: IntegrationConfig) -> bool:
        ...

    @abstractmethod
    def fetch_events(self, since: datetime, until: datetime) -> list[dict]:
        ...

    @abstractmethod
    def create_event(self, event_data: dict) -> dict:
        ...

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        ...


class StorageProvider(ABC):
    """Interface for storage/file providers."""

    @abstractmethod
    def connect(self, config: IntegrationConfig) -> bool:
        ...

    @abstractmethod
    def upload_file(self, path: str, content: bytes, mime_type: str) -> dict:
        ...

    @abstractmethod
    def download_file(self, file_id: str) -> Optional[bytes]:
        ...

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[dict]:
        ...

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        ...


class CommunicationProvider(ABC):
    """Interface for communication channels (WhatsApp, Slack, etc.)."""

    @abstractmethod
    def connect(self, config: IntegrationConfig) -> bool:
        ...

    @abstractmethod
    def send_message(self, recipient: str, content: str, channel: str) -> dict:
        ...

    @abstractmethod
    def receive_messages(self, since: Optional[datetime] = None) -> list[dict]:
        ...

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        ...


class WebhookProvider(ABC):
    """Interface for webhook handling."""

    @abstractmethod
    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        ...

    @abstractmethod
    def handle_event(self, event_data: dict) -> dict:
        ...

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        ...


class ExternalDataProvider(ABC):
    """Interface for external data sources (CRM, ERP, APIs)."""

    @abstractmethod
    def connect(self, config: IntegrationConfig) -> bool:
        ...

    @abstractmethod
    def fetch_data(self, query: dict) -> list[dict]:
        ...

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        ...


class AIModelProvider(ABC):
    """Interface for AI/model providers (OpenAI, Anthropic, local, etc.)."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        ...

    @abstractmethod
    def generate_structured(self, prompt: str, schema: dict) -> dict:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        ...


# ═══════════════════════════════════════════════════════════════════
# Integration Registry
# ═══════════════════════════════════════════════════════════════════

class IntegrationRegistry:
    """Registry of all provider integrations.

    Core SHUNYA code uses this registry to discover and use providers.
    No core code should directly import provider-specific modules.
    """

    _providers: dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, provider: Any) -> None:
        """Register a provider implementation."""
        cls._providers[name] = provider

    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """Get a provider by name."""
        return cls._providers.get(name)

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered providers."""
        return list(cls._providers.keys())

    @classmethod
    def get_status_all(cls) -> dict[str, ProviderStatus]:
        """Get status of all registered providers."""
        return {
            name: provider.get_status()
            for name, provider in cls._providers.items()
            if hasattr(provider, "get_status")
        }