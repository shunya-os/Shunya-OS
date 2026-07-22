"""Tests for INFR-004: Structured Logging."""

import json
import logging
import io
import sys
import pytest
from app.shunya.infrastructure.logging import (
    create_logger,
    get_logger,
    JSONLogFormatter,
    _redact_pii,
    _redact_sensitive_keys,
    reset_loggers,
    with_correlation_id,
)


class TestPrivacyFilter:
    def test_redact_email(self) -> None:
        result = _redact_pii("user@example.com")
        assert "***REDACTED***" in result

    def test_redact_phone(self) -> None:
        result = _redact_pii("Call +1-555-123-4567 now")
        assert "***REDACTED***" in result

    def test_redact_sensitive_keys_password(self) -> None:
        data = {"password": "supersecret", "name": "test"}
        result = _redact_sensitive_keys(data)
        assert result["password"] == "***REDACTED***"
        assert result["name"] == "test"

    def test_redact_sensitive_keys_nested(self) -> None:
        data = {"config": {"api_key": "abc123", "url": "http://example.com"}}
        result = _redact_sensitive_keys(data)
        assert result["config"]["api_key"] == "***REDACTED***"
        assert result["config"]["url"] == "http://example.com"

    def test_redact_sensitive_keys_list(self) -> None:
        data = {"tokens": [{"token": "secret1"}, {"token": "secret2"}]}
        result = _redact_sensitive_keys(data)
        assert result["tokens"][0]["token"] == "***REDACTED***"
        assert result["tokens"][1]["token"] == "***REDACTED***"

    def test_redact_does_not_affect_safe_data(self) -> None:
        data = {"name": "Alice", "count": 42, "active": True}
        result = _redact_sensitive_keys(data)
        assert result["name"] == "Alice"
        assert result["count"] == 42
        assert result["active"] is True


class TestJSONLogFormatter:
    def test_format_basic(self) -> None:
        formatter = JSONLogFormatter(privacy_filter_enabled=False)
        record = logging.LogRecord(
            name="test_logger", level=logging.INFO,
            pathname="/test.py", lineno=42, msg="Hello %s", args=("world",),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Hello world"
        assert parsed["module"] == "test"

    def test_format_with_correlation_id(self) -> None:
        formatter = JSONLogFormatter(privacy_filter_enabled=False)
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="/test.py", lineno=1, msg="test", args=(),
            exc_info=None,
        )
        record.correlation_id = "req-123"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["correlation_id"] == "req-123"

    def test_format_privacy_filter_redacts_pii(self) -> None:
        formatter = JSONLogFormatter(privacy_filter_enabled=True)
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="/test.py", lineno=1, msg="user@example.com", args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "***REDACTED***" in output
        assert "user@example.com" not in output

    def test_format_exception(self) -> None:
        formatter = JSONLogFormatter(privacy_filter_enabled=False)
        try:
            raise ValueError("test error")
        except ValueError:
            record = logging.LogRecord(
                name="test", level=logging.ERROR,
                pathname="/test.py", lineno=1, msg="Error occurred", args=(),
                exc_info=sys.exc_info(),
            )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["exception"]["type"] == "ValueError"
        assert "test error" in parsed["exception"]["message"]


class TestCreateLogger:
    def test_create_logger_output(self) -> None:
        logger = create_logger("test_create", level="DEBUG", format_type="plain")
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1

    def test_create_logger_json_output(self) -> None:
        logger = create_logger("test_json", level="INFO", format_type="json")
        assert len(logger.handlers) == 1

    def test_logger_handles_are_not_duplicated(self) -> None:
        logger = create_logger("test_no_dupes", level="INFO")
        handler_count = len(logger.handlers)
        logger2 = create_logger("test_no_dupes", level="INFO")
        assert len(logger2.handlers) == handler_count

    def test_get_logger(self) -> None:
        reset_loggers()
        logger = get_logger("test_get")
        assert logger is not None
        assert logger.level == logging.INFO

    def test_with_correlation_id(self) -> None:
        logger = get_logger("test_corr")
        adapted = with_correlation_id(logger, "corr-001")
        assert isinstance(adapted, logging.LoggerAdapter)
        assert adapted.extra["correlation_id"] == "corr-001"

    def test_reset_loggers(self) -> None:
        get_logger("test_reset")
        reset_loggers()
        # Should be able to create a new logger without issues
        logger = get_logger("test_reset")
        assert logger is not None