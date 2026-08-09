"""Communication logger — records all outbound intents."""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def log_communication(channel: str, to: str, content: str, entity_id: int = None):
    """Log a outbound communication intent."""
    entry = {
        "channel": channel,
        "to": to,
        "content": content[:500],
        "entity_id": entity_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"[COMMS] {channel} -> {to}: {content[:100]}")
    print(f"[COMMS LOG] {entry}")
    return entry