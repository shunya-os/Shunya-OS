"""SHUNYA Integration Runtime.

The only layer through which SHUNYA communicates with anything outside itself.
No business capability may call external systems directly.

The Execution Runtime performs work.
The Integration Runtime communicates externally.
The Cognitive Runtime decides.

Usage:
    from core.integration_runtime import IntegrationRuntime, IntegrationMessage

    runtime = IntegrationRuntime()
    runtime.register_default_connectors()
    msg = IntegrationMessage(headers={"method": "GET", "path": "/api/data"})
    response = await runtime.send("rest", msg)
"""

from __future__ import annotations

from core.integration_runtime.models import (
    AuditEvent,
    AuthenticationError,
    CircuitBreakerOpenError,
    ConnectionConfig,
    ConnectionInfo,
    ConnectionState,
    ConnectorContract,
    ConnectorEntry,
    ConnectorError,
    ConnectorHealth,
    Credential,
    IntegrationMessage,
    IntegrationTrace,
    MessageDirection,
    MessageType,
    PayloadTooLargeError,
    RateLimitError,
    TimeoutError,
)
from core.integration_runtime.orchestrator import IntegrationRuntime

__all__ = [
    "AuditEvent",
    "AuthenticationError",
    "CircuitBreakerOpenError",
    "ConnectionConfig",
    "ConnectionInfo",
    "ConnectionState",
    "ConnectorContract",
    "ConnectorEntry",
    "ConnectorError",
    "ConnectorHealth",
    "Credential",
    "IntegrationMessage",
    "IntegrationRuntime",
    "IntegrationTrace",
    "MessageDirection",
    "MessageType",
    "PayloadTooLargeError",
    "RateLimitError",
    "TimeoutError",
]