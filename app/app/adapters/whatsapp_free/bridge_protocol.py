"""
SHUNYA — Free Connect Bridge Protocol (Phase 3, EXPERIMENTAL)
Narrow connector protocol between SHUNYA and the unofficial WhatsApp session runtime.
The bridge runs as a separate process — SHUNYA core never depends on the library.
"""
BRIDGE_PROTOCOL_VERSION = "1.0"

# Bridge → SHUNYA events
EVENT_MESSAGE = "message"       # Inbound message
EVENT_QR = "qr"                 # QR code for authentication
EVENT_READY = "ready"           # Bridge connected
EVENT_ERROR = "error"           # Bridge error
EVENT_DISCONNECTED = "disconnected"

# SHUNYA → Bridge commands
COMMAND_SEND = "send"           # (Phase 16A)
COMMAND_STATUS = "status"       # Bridge health check


class BridgeProtocol:
    """Defines the narrow connector protocol between SHUNYA and the Free Connect sidecar.
    Unofficial runtime-specific structures must never leak into this protocol."""

    @staticmethod
    def parse_event(raw: str) -> dict:
        """Parse a bridge event from the sidecar."""
        import json
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"type": EVENT_ERROR, "error": "Invalid protocol payload"}

    @staticmethod
    def format_message(event: dict) -> dict:
        """Format a bridge event into the normalized bridge protocol.
        Input is parsed from the unofficial runtime; output is the bridge protocol."""
        return {
            "protocol_version": BRIDGE_PROTOCOL_VERSION,
            "type": event.get("type", EVENT_MESSAGE),
            "data": {
                "id": event.get("id", ""),
                "chat_id": event.get("from", ""),
                "sender": event.get("author", ""),
                "sender_name": event.get("sender_name", ""),
                "body": event.get("body", ""),
                "type": event.get("type", "text"),
                "is_group": event.get("is_group", False),
                "attachments": event.get("attachments", []),
            },
        }