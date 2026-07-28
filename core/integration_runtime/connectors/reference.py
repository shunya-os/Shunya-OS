"""Reference connectors — no business logic, no vendor lock-in."""

from __future__ import annotations

import json
import time
from typing import Any

from core.integration_runtime.models import (
    ConnectorContract,
    IntegrationMessage,
    MessageDirection,
    MessageType,
)

# ── REST Connector ──────────────────────────────────────────────────────────

REST_CONTRACT = ConnectorContract(
    connector_id="rest",
    capabilities=["rest.get", "rest.post", "rest.put", "rest.delete", "rest.patch"],
    supports_streaming=False,
    idempotent=True,
    version="1.0.0",
)


async def rest_handler(message: IntegrationMessage) -> IntegrationMessage:
    """Reference REST connector handler.

    In production, this would make actual HTTP calls via aiohttp/httpx.
    For testing, returns a simulated response.
    """
    method = message.headers.get("method", "GET").upper()
    path = message.headers.get("path", "/")
    status_code = 200
    response_body = {"method": method, "path": path, "received": True}

    if method == "GET":
        status_code = 200
    elif method in ("POST", "PUT", "PATCH"):
        response_body["body_received"] = message.body is not None
        status_code = 201 if method == "POST" else 200
    elif method == "DELETE":
        status_code = 204
        response_body = None  # type: ignore[assignment]
    else:
        status_code = 405
        response_body = {"error": f"Method {method} not supported"}

    return IntegrationMessage(
        connector_id="rest",
        direction=MessageDirection.INBOUND,
        message_type=MessageType.RESPONSE,
        headers={"status_code": str(status_code)},
        body=response_body,
        metadata={"path": path, "method": method, "status_code": status_code},
    )


# ── Webhook Connector ───────────────────────────────────────────────────────

WEBHOOK_CONTRACT = ConnectorContract(
    connector_id="webhook",
    capabilities=["webhook.register", "webhook.deliver", "webhook.unregister"],
    supports_streaming=False,
    idempotent=True,
    version="1.0.0",
)

_webhook_registry: dict[str, dict[str, Any]] = {}


async def webhook_handler(message: IntegrationMessage) -> IntegrationMessage:
    """Reference webhook connector — register, deliver, unregister."""
    action = message.headers.get("action", "")

    if action == "register":
        url = message.headers.get("url", "")
        _webhook_registry[url] = {
            "url": url,
            "events": message.body or [],
            "registered_at": time.time(),
        }
        return IntegrationMessage(
            connector_id="webhook",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body={"status": "registered", "url": url},
        )

    elif action == "unregister":
        url = message.headers.get("url", "")
        _webhook_registry.pop(url, None)
        return IntegrationMessage(
            connector_id="webhook",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body={"status": "unregistered", "url": url},
        )

    elif action == "deliver":
        url = message.headers.get("url", "")
        payload = message.body
        # In production: POST payload to url
        return IntegrationMessage(
            connector_id="webhook",
            direction=MessageDirection.OUTBOUND,
            message_type=MessageType.REQUEST,
            headers={"url": url},
            body=payload,
        )

    return IntegrationMessage(
        connector_id="webhook",
        direction=MessageDirection.INBOUND,
        message_type=MessageType.RESPONSE,
        body={"error": f"Unknown action: {action}"},
        error="unknown_action",
    )


# ── Filesystem Connector ────────────────────────────────────────────────────

FILESYSTEM_CONTRACT = ConnectorContract(
    connector_id="filesystem",
    capabilities=["fs.read", "fs.write", "fs.delete", "fs.list"],
    supports_streaming=True,
    idempotent=True,
    version="1.0.0",
)

_fs_store: dict[str, Any] = {}


async def filesystem_handler(message: IntegrationMessage) -> IntegrationMessage:
    """Reference filesystem connector — in-memory file store."""
    action = message.headers.get("action", "")
    path = message.headers.get("path", "/")

    if action == "write":
        _fs_store[path] = message.body
        return IntegrationMessage(
            connector_id="filesystem",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body={"status": "written", "path": path, "size": len(json.dumps(message.body)) if message.body else 0},
        )

    elif action == "read":
        content = _fs_store.get(path)
        if content is None:
            return IntegrationMessage(
                connector_id="filesystem",
                direction=MessageDirection.INBOUND,
                message_type=MessageType.RESPONSE,
                body={"error": f"Path not found: {path}"},
                error="not_found",
            )
        return IntegrationMessage(
            connector_id="filesystem",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body=content,
        )

    elif action == "delete":
        existed = path in _fs_store
        _fs_store.pop(path, None)
        return IntegrationMessage(
            connector_id="filesystem",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body={"status": "deleted" if existed else "not_found", "path": path},
        )

    elif action == "list":
        prefix = path
        paths = [k for k in _fs_store if k.startswith(prefix)]
        return IntegrationMessage(
            connector_id="filesystem",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body={"paths": paths, "count": len(paths)},
        )

    return IntegrationMessage(
        connector_id="filesystem",
        direction=MessageDirection.INBOUND,
        message_type=MessageType.RESPONSE,
        body={"error": f"Unknown action: {action}"},
        error="unknown_action",
    )


# ── SMTP Connector ──────────────────────────────────────────────────────────

SMTP_CONTRACT = ConnectorContract(
    connector_id="smtp",
    capabilities=["email.send"],
    supports_streaming=False,
    idempotent=True,
    version="1.0.0",
)

_sent_emails: list[dict[str, Any]] = []


async def smtp_handler(message: IntegrationMessage) -> IntegrationMessage:
    """Reference SMTP connector — in-memory email store."""
    email: dict[str, Any] = {
        "to": message.headers.get("to", ""),
        "from": message.headers.get("from", "system@shunya.local"),
        "subject": message.headers.get("subject", ""),
        "body": message.body,
        "sent_at": time.time(),
    }
    _sent_emails.append(email)

    return IntegrationMessage(
        connector_id="smtp",
        direction=MessageDirection.INBOUND,
        message_type=MessageType.RESPONSE,
        body={"status": "sent", "to": email["to"], "subject": email["subject"]},
    )


def get_sent_emails() -> list[dict[str, Any]]:
    return list(_sent_emails)


def clear_sent_emails() -> None:
    _sent_emails.clear()


# ── OpenAI-Compatible AI Connector ──────────────────────────────────────────

OPENAI_CONTRACT = ConnectorContract(
    connector_id="openai",
    capabilities=["ai.chat", "ai.embed", "ai.complete"],
    supports_streaming=True,
    idempotent=False,
    version="1.0.0",
)


async def openai_handler(message: IntegrationMessage) -> IntegrationMessage:
    """Reference OpenAI-compatible AI connector.

    Returns simulated responses. In production, calls OpenAI API.
    """
    capability = message.headers.get("capability", "ai.chat")
    model = message.headers.get("model", "gpt-4")
    messages = message.body if isinstance(message.body, list) else []

    if capability == "ai.chat":
        return IntegrationMessage(
            connector_id="openai",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body={
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"Simulated response from {model} "
                                   f"regarding {messages[0].get('content', '') if messages else 'unknown'}",
                    },
                    "finish_reason": "stop",
                }],
                "model": model,
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            },
        )

    elif capability == "ai.embed":
        return IntegrationMessage(
            connector_id="openai",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body={
                "data": [{"embedding": [0.1] * 128, "index": 0}],
                "model": model,
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            },
        )

    elif capability == "ai.complete":
        prompt = message.body if isinstance(message.body, str) else ""
        return IntegrationMessage(
            connector_id="openai",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.RESPONSE,
            body={
                "choices": [{"text": f"Completion of: {prompt[:50]}...", "finish_reason": "stop"}],
                "model": model,
            },
        )

    return IntegrationMessage(
        connector_id="openai",
        direction=MessageDirection.INBOUND,
        message_type=MessageType.RESPONSE,
        body={"error": f"Unknown capability: {capability}"},
        error="unknown_capability",
    )