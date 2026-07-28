"""SHUNYA — Structured Logging.

Centralized structured logging with JSON output, configurable levels,
privacy filters (PII stripping), and correlation_id propagation.

Architectural authority: INFR-004 (SHUNYA_IMPLEMENTATION_PROGRAM.md)
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
from uuid import uuid4

import traceback

# ---- Privacy Filter ---------------------------------------------------------

# Patterns for common PII fields that should be redacted in logs
_PII_PATTERNS: Dict[str, str] = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "password": r"(?i)(password|passwd|pwd|secret|token|api_key|apikey)\s*[:=]\s*\S+",
}

# Keys whose values should always be redacted
_SENSITIVE_KEYS: Set[str] = {
    "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
    "authorization", "x-api-key", "cookie", "set-cookie",
    "aws_access_key_id", "aws_secret_access_key",
    "private_key", "encryption_key",
}

_REDACTED = "***REDACTED***"


def _redact_pii(value: str) -> str:
    """Redact common PII patterns from a string."""
    for _ in range(3):  # Multiple passes for nested patterns
        for pattern_name, pattern in _PII_PATTERNS.items():
            value = re.sub(pattern, _REDACTED, value)
    return value


def _redact_sensitive_keys(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
    """Recursively redact values for keys in _SENSITIVE_KEYS."""
    if depth > 10:
        return data
    result: Dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in _SENSITIVE_KEYS:
            result[key] = _REDACTED
        elif isinstance(value, dict):
            result[key] = _redact_sensitive_keys(value, depth + 1)
        elif isinstance(value, str):
            result[key] = _redact_pii(value)
        elif isinstance(value, list):
            result[key] = [
                _redact_sensitive_keys(v, depth + 1) if isinstance(v, dict)
                else _redact_pii(v) if isinstance(v, str)
                else v
                for v in value
            ]
        else:
            result[key] = value
    return result


# ---- JSON Log Formatter -----------------------------------------------------


class JSONLogFormatter(logging.Formatter):
    """Format log records as JSON with optional PII redaction.

    Output fields:
      - timestamp (ISO 8601 UTC)
      - level
      - logger
      - message
      - correlation_id (if present in extra or thread-local)
      - module, function, line
      - exception (if any)
      - extra fields from the log record
    """

    def __init__(self, privacy_filter_enabled: bool = True) -> None:
        super().__init__()
        self._privacy_filter_enabled = privacy_filter_enabled

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Correlation ID (from extra dict or thread-local)
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_entry["correlation_id"] = record.correlation_id

        # Exception info
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": "".join(
                    traceback.format_exception(*record.exc_info)
                ),
            }

        # Extra fields (keys not in standard LogRecord)
        standard_keys = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "process", "processName", "message",
        }
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_keys
        }
        if extras:
            log_entry["extra"] = extras

        # Privacy filter
        if self._privacy_filter_enabled:
            log_entry = _redact_sensitive_keys(log_entry)

        return json.dumps(log_entry, default=str)


# ---- Logger Factory ---------------------------------------------------------


def create_logger(
    name: str,
    level: str = "INFO",
    output: str = "stdout",
    format_type: str = "json",
    privacy_filter_enabled: bool = True,
) -> logging.Logger:
    """Create a configured logger instance.

    Args:
        name: Logger name (typically module __name__).
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        output: "stdout" or "stderr".
        format_type: "json" or "plain" (plain for development).
        privacy_filter_enabled: If True, redact PII from log output.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    # Handler
    stream = sys.stdout if output == "stdout" else sys.stderr
    handler = logging.StreamHandler(stream)
    handler.setLevel(logger.level)

    # Formatter
    if format_type == "json":
        formatter = JSONLogFormatter(privacy_filter_enabled=privacy_filter_enabled)
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# ---- Convenience Helpers ----------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger for the given module name.

    Uses application configuration for log level and format settings.
    Falls back to sensible defaults if config is not yet loaded.
    """
    try:
        from app.shunya.config import get_config

        cfg = get_config()
        log_cfg = cfg.get_section("logging")
        level = log_cfg.get("level", "INFO")
        format_type = log_cfg.get("format", "json")
        output = log_cfg.get("output", "stdout")
        privacy = log_cfg.get("privacy_filter_enabled", True)
    except Exception:
        level = "INFO"
        format_type = "json"
        output = "stdout"
        privacy = True

    return create_logger(
        name=name,
        level=level,
        output=output,
        format_type=format_type,
        privacy_filter_enabled=privacy,
    )


def with_correlation_id(logger: logging.Logger, correlation_id: str) -> logging.Logger:
    """Return a logger adapter that attaches a correlation_id to every log entry.

    Usage:
        logger = with_correlation_id(get_logger(__name__), "req-abc-123")
        logger.info("Processing request")
    """
    return logging.LoggerAdapter(logger, {"correlation_id": correlation_id})


# ---- Module-level convenience -----------------------------------------------

_loggers: Dict[str, logging.Logger] = {}


def reset_loggers() -> None:
    """Clear the logger cache. Useful for testing."""
    _loggers.clear()


# ---- Explicit re-export of logging constants for convenience ----------------

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL