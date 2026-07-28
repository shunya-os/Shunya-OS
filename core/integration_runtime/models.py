"""SHUNYA Integration Runtime — data models.

Domain-agnostic message and connector models. No vendor-specific types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    from core.kernel.types import generate_uuid7
    return generate_uuid7()


# ── Message Types ───────────────────────────────────────────────────────────

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    STREAM = "stream"
    WEBHOOK = "webhook"
    FILE_TRANSFER = "file_transfer"
    NOTIFICATION = "notification"
    COMMAND = "command"
    RESULT = "result"


@dataclass
class IntegrationMessage:
    """Universal message model for all external communication."""

    message_id: str = field(default_factory=_generate_id)
    connector_id: str = ""
    direction: MessageDirection = MessageDirection.OUTBOUND
    message_type: MessageType = MessageType.REQUEST
    headers: dict[str, Any] = field(default_factory=dict)
    body: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    error: str | None = None


# ── Connector Contract ─────────────────────────────────────────────────────

@dataclass
class ConnectorContract:
    """Contract that every connector must fulfil."""

    connector_id: str = ""
    capabilities: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    error_schema: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)
    supports_streaming: bool = False
    idempotent: bool = False
    version: str = "1.0.0"


# ── Connection State ───────────────────────────────────────────────────────

class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ConnectionConfig:
    """Configuration for a connector connection."""

    connector_id: str = ""
    credential_id: str = ""
    base_url: str = ""
    timeout_ms: int = 30_000
    max_retries: int = 3
    backoff_ms: int = 100
    pool_size: int = 5
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_ms: int = 60_000
    rate_limit_per_second: int = 100
    max_payload_bytes: int = 10 * 1024 * 1024  # 10MB


@dataclass
class ConnectionInfo:
    """Runtime connection state."""

    state: ConnectionState = ConnectionState.DISCONNECTED
    connected_at: str = ""
    last_error: str = ""
    failure_count: int = 0
    success_count: int = 0
    retry_count: int = 0
    circuit_open_until: str = ""


# ── Credential ──────────────────────────────────────────────────────────────

@dataclass
class Credential:
    """Abstract credential — never exposes secrets in logs or messages."""

    credential_id: str = field(default_factory=_generate_id)
    credential_type: str = ""  # "api_key", "oauth2", "basic", "bearer"
    tenant_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    # Secrets stored externally, never serialized
    _secrets: dict[str, str] = field(default_factory=dict, repr=False)


# ── Audit Event ────────────────────────────────────────────────────────────

@dataclass
class AuditEvent:
    """Immutable audit record for every integration call."""

    event_id: str = field(default_factory=_generate_id)
    connector_id: str = ""
    message_id: str = ""
    direction: str = ""
    message_type: str = ""
    tenant_id: str = ""
    actor: str = ""
    success: bool = True
    error: str = ""
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=_now_iso)


# ── Observability ──────────────────────────────────────────────────────────

@dataclass
class IntegrationTrace:
    """Observability data for integration calls."""

    trace_id: str = field(default_factory=_generate_id)
    connector_id: str = ""
    message_id: str = ""
    direction: str = ""
    latency_ms: float = 0.0
    retry_count: int = 0
    failure_count: int = 0
    status: str = "success"  # success | failure | timeout | circuit_open
    timestamp: str = field(default_factory=_now_iso)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorHealth:
    """Health status for a single connector."""

    connector_id: str = ""
    status: str = "unknown"  # healthy | degraded | down | unknown
    connection_state: str = ""
    uptime_ms: float = 0.0
    messages_sent: int = 0
    messages_failed: int = 0
    avg_latency_ms: float = 0.0
    last_error: str = ""
    last_success: str = ""


# ── Connector Registration Entry ───────────────────────────────────────────

@dataclass
class ConnectorEntry:
    """A registered connector in the registry."""

    connector_id: str
    contract: ConnectorContract
    handler: Any  # async callable(message) -> IntegrationMessage
    config: ConnectionConfig = field(default_factory=ConnectionConfig)
    connection: ConnectionInfo = field(default_factory=ConnectionInfo)
    health: ConnectorHealth = field(default_factory=ConnectorHealth)
    version: str = "1.0.0"


# ── Connector Errors ───────────────────────────────────────────────────────

class ConnectorError(Exception):
    """Base error for connector failures."""
    def __init__(self, message: str, connector_id: str = "", code: str = ""):
        self.connector_id = connector_id
        self.code = code
        super().__init__(message)


class AuthenticationError(ConnectorError):
    """Authentication/authorization failure."""


class RateLimitError(ConnectorError):
    """Rate limit exceeded."""


class TimeoutError(ConnectorError):
    """Connection or operation timed out."""


class CircuitBreakerOpenError(ConnectorError):
    """Circuit breaker is open, operation blocked."""


class PayloadTooLargeError(ConnectorError):
    """"Message payload exceeds size limit."""