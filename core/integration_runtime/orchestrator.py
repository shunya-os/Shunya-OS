"""SHUNYA Integration Runtime — Orchestrator.

The only layer through which SHUNYA communicates with anything outside itself.
No business capability may call external systems directly.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from core.integration_runtime.models import (
    AuditEvent,
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
    PayloadTooLargeError,
    RateLimitError,
    TimeoutError,
    _now_iso,
)

logger = logging.getLogger(__name__)


class IntegrationRuntime:
    """Single authoritative layer for all external communication.

    Usage:
        runtime = IntegrationRuntime()
        runtime.register_default_connectors()
        result = await runtime.send("rest", IntegrationMessage(
            message_type=MessageType.REQUEST,
            headers={"method": "GET", "path": "/api/data"},
        ))
    """

    def __init__(self):
        self._connectors: dict[str, ConnectorEntry] = {}
        self._credentials: dict[str, Credential] = {}
        self._audit_log: list[AuditEvent] = []
        self._traces: list[IntegrationTrace] = []
        self._capability_index: dict[str, list[str]] = {}  # capability → [connector_ids]

    # ── Connector Registry ────────────────────────────────────────────

    def register_connector(
        self,
        connector_id: str,
        contract: ConnectorContract,
        handler: Any,
        config: ConnectionConfig | None = None,
    ) -> None:
        """Register a connector. No runtime core changes required."""
        if connector_id in self._connectors:
            raise ValueError(f"Connector already registered: {connector_id}")

        entry = ConnectorEntry(
            connector_id=connector_id,
            contract=contract,
            handler=handler,
            config=config or ConnectionConfig(connector_id=connector_id),
            version=contract.version,
        )
        self._connectors[connector_id] = entry

        # Index capabilities
        for cap in contract.capabilities:
            self._capability_index.setdefault(cap, []).append(connector_id)

    def get_connector(self, connector_id: str) -> ConnectorEntry | None:
        return self._connectors.get(connector_id)

    def list_connectors(self) -> list[ConnectorEntry]:
        return list(self._connectors.values())

    def discover_capabilities(self) -> dict[str, list[str]]:
        """Return all capabilities and which connectors provide them."""
        return dict(self._capability_index)

    def find_connector(self, capability: str) -> list[str]:
        """Find connectors that provide a specific capability."""
        return self._capability_index.get(capability, [])

    # ── Credential Management ─────────────────────────────────────────

    def register_credential(
        self,
        credential_id: str,
        credential_type: str,
        secrets: dict[str, str] | None = None,
        tenant_id: str = "",
    ) -> Credential:
        """Register a credential. Secrets are stored but never logged."""
        cred = Credential(
            credential_id=credential_id,
            credential_type=credential_type,
            tenant_id=tenant_id,
            _secrets=secrets or {},
        )
        self._credentials[credential_id] = cred
        return cred

    def get_credential(self, credential_id: str) -> Credential | None:
        return self._credentials.get(credential_id)

    # ── Connection Management ─────────────────────────────────────────

    async def connect(self, connector_id: str) -> ConnectionInfo:
        """Establish or verify connection for a connector."""
        entry = self._get_entry(connector_id)
        if entry.connection.state == ConnectionState.CONNECTED:
            return entry.connection

        entry.connection.state = ConnectionState.CONNECTING
        try:
            # Check circuit breaker
            if entry.connection.state == ConnectionState.CIRCUIT_OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker open for {connector_id}",
                    connector_id=connector_id,
                )

            # Simulate connection (in production: actual handshake)
            await asyncio.sleep(0.01)
            entry.connection.state = ConnectionState.CONNECTED
            entry.connection.connected_at = _now_iso()
            entry.connection.last_error = ""
            return entry.connection

        except Exception as exc:
            entry.connection.state = ConnectionState.FAILED
            entry.connection.last_error = str(exc)
            entry.connection.failure_count += 1
            raise

    async def disconnect(self, connector_id: str) -> None:
        """Disconnect a connector."""
        entry = self._get_entry(connector_id)
        entry.connection.state = ConnectionState.DISCONNECTING
        await asyncio.sleep(0.005)
        entry.connection.state = ConnectionState.DISCONNECTED

    # ── Core Send / Receive ───────────────────────────────────────────

    async def send(
        self,
        connector_id: str,
        message: IntegrationMessage,
        credential_id: str | None = None,
        tenant_id: str = "",
    ) -> IntegrationMessage:
        """Send a message through a connector.

        This is the single entry point for all external communication.
        """
        entry = self._get_entry(connector_id)
        trace = IntegrationTrace(
            connector_id=connector_id,
            message_id=message.message_id,
            direction=message.direction.value,
        )
        start = time.time()

        try:
            # Size check
            if message.body is not None:
                import json
                body_size = len(json.dumps(message.body))
                if body_size > entry.config.max_payload_bytes:
                    raise PayloadTooLargeError(
                        f"Payload {body_size} bytes exceeds max {entry.config.max_payload_bytes}",
                        connector_id=connector_id,
                    )

            # Rate limit check (simple counter-based)
            if entry.connection.failure_count > entry.config.circuit_breaker_threshold:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker open after {entry.connection.failure_count} failures",
                    connector_id=connector_id,
                )

            # Connect if needed
            await self.connect(connector_id)

            # Execute with retries
            retry_count = 0
            last_error: Exception | None = None

            while retry_count <= entry.config.max_retries:
                try:
                    # Set connector_id on message
                    message.connector_id = connector_id
                    message.created_at = _now_iso()

                    # Call handler
                    result = entry.handler(message)
                    if asyncio.iscoroutine(result):
                        response = await asyncio.wait_for(
                            result,
                            timeout=entry.config.timeout_ms / 1000,
                        )
                    else:
                        response = result

                    # Success
                    entry.connection.success_count += 1
                    entry.connection.failure_count = 0
                    entry.connection.retry_count = retry_count

                    latency = (time.time() - start) * 1000
                    trace.latency_ms = round(latency, 2)
                    trace.retry_count = retry_count
                    trace.status = "success"

                    # Update health
                    self._update_health(entry, latency, success=True)

                    # Audit
                    self._audit(AuditEvent(
                        connector_id=connector_id,
                        message_id=message.message_id,
                        direction=message.direction.value,
                        message_type=message.message_type.value,
                        tenant_id=tenant_id,
                        latency_ms=round(latency, 2),
                        success=True,
                    ))

                    self._traces.append(trace)
                    return response

                except asyncio.TimeoutError:
                    last_error = TimeoutError(
                        f"Timeout after {entry.config.timeout_ms}ms",
                        connector_id=connector_id,
                    )
                    retry_count += 1
                    if retry_count <= entry.config.max_retries:
                        backoff = entry.config.backoff_ms * (2 ** (retry_count - 1))
                        await asyncio.sleep(backoff / 1000)
                    else:
                        break

                except ConnectorError as exc:
                    last_error = exc
                    if isinstance(exc, (RateLimitError, CircuitBreakerOpenError, PayloadTooLargeError)):
                        # Non-retryable
                        break
                    retry_count += 1
                    if retry_count <= entry.config.max_retries:
                        backoff = entry.config.backoff_ms * (2 ** (retry_count - 1))
                        await asyncio.sleep(backoff / 1000)
                    else:
                        break

                except (ValueError, TypeError, RuntimeError, OSError) as exc:
                    last_error = ConnectorError(str(exc), connector_id=connector_id)
                    retry_count += 1
                    if retry_count <= entry.config.max_retries:
                        backoff = entry.config.backoff_ms * (2 ** (retry_count - 1))
                        await asyncio.sleep(backoff / 1000)
                    else:
                        break

            # All retries exhausted
            entry.connection.failure_count += 1
            entry.connection.last_error = str(last_error)
            entry.connection.retry_count = retry_count

            latency = (time.time() - start) * 1000
            trace.latency_ms = round(latency, 2)
            trace.retry_count = retry_count
            trace.failure_count = entry.connection.failure_count
            trace.status = "failure"

            self._update_health(entry, latency, success=False)

            self._audit(AuditEvent(
                connector_id=connector_id,
                message_id=message.message_id,
                direction=message.direction.value,
                message_type=message.message_type.value,
                tenant_id=tenant_id,
                latency_ms=round(latency, 2),
                success=False,
                error=str(last_error) if last_error else "unknown",
            ))
            self._traces.append(trace)

            if last_error:
                raise last_error
            raise ConnectorError("Unknown error", connector_id=connector_id)

        except CircuitBreakerOpenError:
            trace.status = "circuit_open"
            self._traces.append(trace)
            raise

    # ── Observability ─────────────────────────────────────────────────

    def get_traces(
        self, connector_id: str | None = None, limit: int = 100
    ) -> list[IntegrationTrace]:
        traces = self._traces
        if connector_id:
            traces = [t for t in traces if t.connector_id == connector_id]
        return traces[-limit:]

    def get_audit_log(
        self, connector_id: str | None = None, limit: int = 100
    ) -> list[AuditEvent]:
        log = self._audit_log
        if connector_id:
            log = [e for e in log if e.connector_id == connector_id]
        return log[-limit:]

    def get_health(self, connector_id: str | None = None) -> dict[str, ConnectorHealth]:
        if connector_id:
            entry = self._connectors.get(connector_id)
            if entry:
                return {connector_id: entry.health}
            return {}
        return {cid: e.health for cid, e in self._connectors.items()}

    def health_check(self) -> dict[str, Any]:
        """Runtime health summary."""
        connectors_health = {}
        for cid, entry in self._connectors.items():
            connectors_health[cid] = {
                "status": entry.health.status,
                "connection": entry.connection.state.value,
                "messages_sent": entry.health.messages_sent,
                "messages_failed": entry.health.messages_failed,
                "avg_latency_ms": round(entry.health.avg_latency_ms, 2),
            }

        return {
            "status": "healthy",
            "runtime": "integration_runtime",
            "connectors_registered": len(self._connectors),
            "credentials_registered": len(self._credentials),
            "total_messages": len(self._traces),
            "capabilities_available": len(self._capability_index),
            "connectors": connectors_health,
        }

    # ── Internal Helpers ──────────────────────────────────────────────

    def _get_entry(self, connector_id: str) -> ConnectorEntry:
        entry = self._connectors.get(connector_id)
        if entry is None:
            raise ValueError(f"Unknown connector: {connector_id}")
        return entry

    def _update_health(self, entry: ConnectorEntry, latency: float, success: bool) -> None:
        h = entry.health
        if success:
            h.messages_sent += 1
            h.last_success = _now_iso()
            h.status = "healthy"
        else:
            h.messages_failed += 1
            h.status = "degraded"
        # Running average
        total = h.messages_sent + h.messages_failed
        h.avg_latency_ms = ((h.avg_latency_ms * (total - 1)) + latency) / total if total > 0 else latency
        h.connection_state = entry.connection.state.value

    def _audit(self, event: AuditEvent) -> None:
        self._audit_log.append(event)

    # ── Default Connectors ────────────────────────────────────────────

    def register_default_connectors(self) -> None:
        """Register all reference connectors."""
        from core.integration_runtime.connectors.reference import (
            FILESYSTEM_CONTRACT,
            OPENAI_CONTRACT,
            REST_CONTRACT,
            SMTP_CONTRACT,
            WEBHOOK_CONTRACT,
            filesystem_handler,
            openai_handler,
            rest_handler,
            smtp_handler,
            webhook_handler,
        )

        self.register_connector("rest", REST_CONTRACT, rest_handler)
        self.register_connector("webhook", WEBHOOK_CONTRACT, webhook_handler)
        self.register_connector("filesystem", FILESYSTEM_CONTRACT, filesystem_handler)
        self.register_connector("smtp", SMTP_CONTRACT, smtp_handler)
        self.register_connector("openai", OPENAI_CONTRACT, openai_handler)

    # ── Fault Injection (for testing) ─────────────────────────────────

    def set_connection_state(self, connector_id: str, state: ConnectionState) -> None:
        """Force a connector's connection state (for testing)."""
        entry = self._get_entry(connector_id)
        entry.connection.state = state

    def set_credential(self, connector_id: str, credential_id: str) -> None:
        """Associate a credential with a connector (for testing)."""
        entry = self._get_entry(connector_id)
        entry.config.credential_id = credential_id