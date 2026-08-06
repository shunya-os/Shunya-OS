"""RabbitMQ adapter — implements MessagingAdapter for message-queue tasks.

Uses pika when the RabbitMQ server is available.
Falls back to an in-process callback registry for development/testing.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from adapters import MessagingAdapter

logger = logging.getLogger(__name__)


class RabbitMQAdapter(MessagingAdapter):
    """Publish and consume messages via RabbitMQ / AMQP."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        virtual_host: str = "/",
        username: str = "guest",
        password: str = "guest",
    ) -> None:
        self._host = host
        self._port = port
        self._virtual_host = virtual_host
        self._username = username
        self._password = password
        self._connection = None
        self._channel = None
        self._connected = False
        # In-process fallback: queue_name -> list of callbacks
        self._local_subscribers: dict[str, list[Callable[..., Any]]] = {}

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        """Open a blocking connection to RabbitMQ; fall back to local on failure."""
        try:
            import pika  # type: ignore[import-untyped]

            credentials = pika.PlainCredentials(self._username, self._password)
            params = pika.ConnectionParameters(
                host=self._host,
                port=self._port,
                virtual_host=self._virtual_host,
                credentials=credentials,
                heartbeat=30,
            )
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._connected = True
        except Exception:
            logger.warning("RabbitMQ not available — using local in-process fallback")
            self._connected = False
        return self._connected

    def close(self) -> None:
        """Gracefully close the connection."""
        if self._connection and self._connected:
            try:
                self._connection.close()
            except Exception:
                pass
        self._connection = None
        self._channel = None
        self._connected = False

    # ------------------------------------------------------------------
    # MessagingAdapter interface
    # ------------------------------------------------------------------
    def publish(self, queue: str, message: Any) -> bool:
        """Publish a JSON-serializable message to *queue*."""
        if self._connected and self._channel is not None:
            try:
                import pika  # type: ignore[import-untyped]

                self._channel.queue_declare(queue=queue, durable=True)
                body = json.dumps(message, default=str)
                self._channel.basic_publish(
                    exchange="",
                    routing_key=queue,
                    body=body,
                    properties=pika.BasicProperties(delivery_mode=2),  # persistent
                )
                return True
            except Exception:
                self._connected = False

        # Local fallback — log and dispatch
        logger.debug("[local] published to %s: %s", queue, message)
        if queue in self._local_subscribers:
            for cb in self._local_subscribers[queue]:
                try:
                    cb(message)
                except Exception:
                    logger.exception("callback error on queue %s", queue)
        return True

    def consume(self, queue: str, callback: Callable[..., Any]) -> None:
        """Register *callback* to receive messages from *queue*.

        When connected to RabbitMQ, starts a blocking consume loop
        (call from a background thread).  In local mode the callback
        is registered and invoked synchronously by ``publish``.
        """
        if self._connected and self._channel is not None:
            self._channel.queue_declare(queue=queue, durable=True)

            def _on_message(
                ch: Any,
                method: Any,
                properties: Any,
                body: bytes,
            ) -> None:
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError:
                    payload = body.decode("utf-8")  # type: ignore[assignment]
                callback(payload)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            self._channel.basic_consume(queue=queue, on_message_callback=_on_message)
            self._channel.start_consuming()
        else:
            self._local_subscribers.setdefault(queue, []).append(callback)
            logger.debug("[local] registered consumer on %s", queue)

    def __repr__(self) -> str:
        return (
            f"RabbitMQAdapter(host={self._host}, port={self._port}, "
            f"connected={self._connected})"
        )