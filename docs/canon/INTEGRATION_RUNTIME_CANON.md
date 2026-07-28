# Integration Runtime Canon

> **Canonical Document · Phase G**
> **Status: CANONICAL — Implementation Specification**
> **Version: 1.0**

---

## 1. Purpose

The Integration Runtime is the only layer through which SHUNYA communicates with anything outside itself. No business capability may call an external API, send an email, write a file, or invoke an AI provider directly. Every external communication passes through the Integration Runtime.

The Execution Runtime performs work. The Integration Runtime communicates externally. The Cognitive Runtime decides what to do and when.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     INTEGRATION RUNTIME                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Connector Registry                         │  │
│  │  register_connector() | discover_capabilities() | health   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Connection Manager                         │  │
│  │  lifecycle | auth | refresh | pool | retry | circuit break │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                Universal Message Model                       │  │
│  │  IntegrationMessage | Request | Response | Event | Stream  │  │
│  │  Webhook | FileTransfer | Notification | Command | Result   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ Security │ │Observab. │ │Execution │ │  Connectors       │  │
│  │ creds    │ │ trace    │ │Integration│ │ REST | Webhook    │  │
│  │ secrets  │ │ latency  │ │Runtime   │ │ Filesystem | SMTP  │  │
│  │ tenants  │ │ health   │ │ invokes  │ │ OpenAI            │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              External Systems (Email, API, DB, AI, etc.)
```

### 2.1 Layering

| Layer | Authority |
|-------|-----------|
| **Cognitive Runtime** (Phase E) | Decides what to do and when |
| **Execution Runtime** (Phase F) | Performs work via action handlers |
| **Integration Runtime** (Phase G) | Communicates externally on behalf of work |

---

## 3. Universal Message Model

Every inbound and outbound communication is an `IntegrationMessage`.

```python
@dataclass
class IntegrationMessage:
    message_id: str
    connector_id: str
    direction: MessageDirection  # INBOUND | OUTBOUND
    message_type: MessageType    # REQUEST | RESPONSE | EVENT | STREAM | WEBHOOK
    headers: dict
    body: Any
    metadata: dict
    created_at: str
```

### 3.1 Message Types

| Type | Usage |
|------|-------|
| REQUEST | Outbound API call |
| RESPONSE | Inbound API response |
| EVENT | Inbound event / webhook payload |
| STREAM | Streaming data (chunked, SSE) |
| WEBHOOK | Inbound webhook registration + delivery |
| FILE_TRANSFER | File upload / download |
| NOTIFICATION | Push notification |
| COMMAND | Internal command between connectors |
| RESULT | Execution result wrapper |

---

## 4. Connector Contracts

Every connector exposes:

```python
@dataclass
class ConnectorContract:
    connector_id: str
    capabilities: list[str]           # ["rest.get", "rest.post", "email.send", ...]
    input_schema: dict                 # JSON Schema for inputs
    output_schema: dict                # JSON Schema for outputs
    error_schema: dict                 # Error types this connector can return
    required_permissions: list[str]    # ["email:send", "api:read", ...]
    supports_streaming: bool
    idempotent: bool
    version: str
```

### 4.1 Capability Discovery

```python
runtime.discover_capabilities()  # Returns all registered capabilities
runtime.find_connector(capability="email.send")  # Returns matching connectors
```

---

## 5. Connector Registry

### 5.1 Registration

```python
runtime.register_connector(connector_id="gmail", contract=contract, handler=handler)
```

### 5.2 Registry Services

- Dynamic registration (add connectors at runtime)
- Capability discovery (find connectors by capability)
- Versioning (multiple connector versions)
- Health checks (per-connector health status)
- Authentication metadata
- Permission metadata
- Rate limits (per-connector and global)

---

## 6. Connection Manager

### 6.1 Connection Lifecycle

```
DISCONNECTED → CONNECTING → CONNECTED → DISCONNECTING → DISCONNECTED
                                            ↓
                                         FAILED
```

### 6.2 Connection Services

| Service | Description |
|---------|-------------|
| Connection lifecycle | Track connection state |
| Authentication | OAuth, API key, basic auth, token exchange |
| Refresh | Automatic token/credential refresh |
| Pooling | Connection pooling for high-throughput connectors |
| Retries | Exponential backoff on transient failures |
| Backoff | Configurable backoff strategy |
| Circuit breakers | Open/closed/half-open state machine |

---

## 7. Execution Integration

The Execution Runtime (Phase F) never calls external systems directly. Instead, action handlers invoke the Integration Runtime:

```python
async def my_action_handler(inputs):
    result = await integration_runtime.send(
        connector_id="gmail",
        message=IntegrationMessage(
            message_type=MessageType.REQUEST,
            headers={"to": inputs["to"]},
            body={"subject": inputs["subject"], "body": inputs["body"]},
        ),
    )
    return {"status": "sent", "message_id": result.message_id}
```

---

## 8. Security

| Component | Description |
|-----------|-------------|
| Credential abstraction | Credentials stored by ID, never exposed to connectors |
| Secret isolation | Secrets never logged or serialized in messages |
| Permission boundaries | Connectors enforce required_permissions |
| Tenant isolation | Multi-tenant support via tenant_id in metadata |
| Audit logging | Every outbound/inbound call is logged |

---

## 9. Observability

| Metric | Source |
|--------|--------|
| Trace | Every send/receive produces a trace entry |
| Latency | Per-connector, per-operation latency |
| Retries | Retry count per connection |
| Failures | Failure count per connector |
| Throughput | Messages per second |
| Health | Per-connector health status |
| Dependency graph | Connector dependency visualization |

---

## 10. Connectors

### 10.1 Reference Connectors (no business logic)

| Connector | Type | Capabilities |
|-----------|------|--------------|
| REST | HTTP/HTTPS | rest.get, rest.post, rest.put, rest.delete, rest.patch |
| Webhook | HTTP Callback | webhook.register, webhook.deliver, webhook.unregister |
| Filesystem | Local FS | fs.read, fs.write, fs.delete, fs.list |
| SMTP | Email | email.send |
| OpenAI | AI API | ai.chat, ai.embed, ai.complete |

### 10.2 Connector Pattern

Every connector follows the same pattern:
1. Implement `async def handle(message: IntegrationMessage) -> IntegrationMessage`
2. Register via `runtime.register_connector()`

---

## 11. Testing Infrastructure

The integration runtime includes:

| Feature | Description |
|---------|-------------|
| Mock connectors | In-memory connectors for testing |
| Fake providers | Simulated external services (fake SMTP, fake REST, etc.) |
| Failure injection | Configurable failure rates per connector |
| Rate limiting | Test rate limit enforcement |
| Timeouts | Test timeout behaviour |
| Network partitions | Simulate disconnected states |
| Streaming | Test streaming message handling |
| Pagination | Test paginated responses |
| Large payloads | Test payload size limits |
| Authentication expiry | Test token refresh flows |

---

## 12. Future Integration Guarantee

A future integration requires only:
1. Implement a handler for the external system
2. Call `runtime.register_connector()`

No runtime core changes. No business logic in the connector. All security, observability, and connection management inherited automatically.

---

*End of Integration Runtime Canon*