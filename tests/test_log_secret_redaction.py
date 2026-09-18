"""Secrets hygiene — no credential may reach a log sink.

Regression coverage for the production defect where ``create_app()`` logged the
first 30 characters of ``SQLALCHEMY_DATABASE_URI`` on every worker boot,
emitting ``<scheme>://<user>:<password>@<host>`` into the systemd journal.

Two layers are asserted here:
  * source-level  — ``safe_database_descriptor`` for operational log lines
  * record-level  — ``RedactionFilter`` scrubbing anything credential-shaped,
                    including ``extra=`` attributes the JSON formatter writes

NOTE ON FIXTURE CONSTRUCTION: the DSNs below are assembled at runtime rather
than written as literals. A credential-shaped literal in a source file is
subject to secret-scrubbers (and is bad practice even for fake values); only a
runtime-built string exercises the redaction path honestly.
"""

import io
import json
import logging

from app.security.redaction import (
    REDACTED,
    RedactionFilter,
    install_log_redaction,
    redact_secrets,
    safe_database_descriptor,
)

# Assembled at runtime — no user:password@ literal exists in this file.
USER = "shunya"
PASSWORD = "Xk7-not-a-real-password"
HOST = "127.0.0.1"
DBNAME = "shunya_db"
AUTHORITY = USER + ":" + PASSWORD + "@" + HOST
CREDENTIAL_URI = "postgresql://" + AUTHORITY + ":5432/" + DBNAME
JSON_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s"


# ---------------------------------------------------------------------------
# Source-level: the descriptor used for operational log lines
# ---------------------------------------------------------------------------


def test_safe_database_descriptor_removes_credentials():
    descriptor = safe_database_descriptor(CREDENTIAL_URI)
    assert PASSWORD not in descriptor
    assert AUTHORITY not in descriptor
    assert DBNAME in descriptor  # useful diagnostic value is preserved
    assert HOST in descriptor


def test_safe_database_descriptor_handles_redis_sqlite_and_none():
    assert "hunter2" not in safe_database_descriptor("redis://:hunter2@" + HOST + ":6379/0")
    assert "hunter2" not in safe_database_descriptor("redis://u:hunter2@" + HOST + ":6379/0")
    assert "hunter2" not in safe_database_descriptor("postgres://u:hunter2@db.internal:5432/x")
    assert ":memory:" in safe_database_descriptor("sqlite:///:memory:")
    assert safe_database_descriptor(None) == "<none>"
    # unparseable values must not raise and must not leak
    assert "hunter2" not in safe_database_descriptor("postgresql://u:hunter2@[bad:port/x")


# ---------------------------------------------------------------------------
# Record-level: string scrubbing
# ---------------------------------------------------------------------------


def test_redact_secrets_covers_urls_key_values_and_bearer_tokens():
    cases = [
        ("connect via " + CREDENTIAL_URI, PASSWORD),
        ("dsn=" + AUTHORITY, PASSWORD),
        ("password=topsecret12 ok", "topsecret12"),
        ("api_key: sk-abcdef1234567890", "sk-abcdef1234567890"),
        ("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig", "eyJhbGciOiJIUzI1NiJ9"),
        ("client_secret=zzzzzzzzzzzz", "zzzzzzzzzzzz"),
    ]
    for text, secret in cases:
        redacted = redact_secrets(text)
        assert secret not in redacted, f"leaked: {text!r}"
        assert REDACTED in redacted


def test_redact_secrets_does_not_over_redact_clean_text():
    clean = [
        "SHUNYA OS initialised",
        "Rate limiter initialised (storage: redis://127.0.0.1:6379)",
        "GET /health 200 in 0.008s",
        "https://shunyaos.com/health",
        "postgresql://127.0.0.1:5432/shunya_db",
        "user shunya created a customer",
    ]
    for text in clean:
        assert redact_secrets(text) == text, f"over-redacted: {text!r}"


def test_redact_secrets_is_idempotent():
    once = redact_secrets("POST " + CREDENTIAL_URI + " password=abc123456")
    assert PASSWORD not in once
    assert redact_secrets(once) == once


# ---------------------------------------------------------------------------
# Record-level: the filter, exercised through the production JSON formatter
# ---------------------------------------------------------------------------


def _handler_with_filter():
    from pythonjsonlogger import jsonlogger

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(jsonlogger.JsonFormatter(JSON_FORMAT))
    handler.addFilter(RedactionFilter())
    logger = logging.getLogger("shunya.test.redaction")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger, handler, stream


def test_filter_scrubs_production_shaped_json_extra_attribute():
    """The exact production defect: credential in an `extra=` field the JSON formatter writes."""
    logger, handler, stream = _handler_with_filter()
    logger.info(
        "SHUNYA OS initialised",
        extra={"request_id": "bootstrap", "db": CREDENTIAL_URI},
    )
    handler.flush()
    rendered = stream.getvalue()
    assert PASSWORD not in rendered
    assert DBNAME in rendered  # the diagnostic survived the scrub


def test_filter_scrubs_message_and_interpolation_args():
    logger, handler, stream = _handler_with_filter()
    logger.info("db url is %s", CREDENTIAL_URI, extra={"request_id": "r1"})
    handler.flush()
    assert PASSWORD not in stream.getvalue()


def test_filter_scrubs_exception_traceback_text():
    """A credential inside an exception message must not reach the sink."""
    logger, handler, stream = _handler_with_filter()
    try:
        raise RuntimeError("cannot connect to " + CREDENTIAL_URI)
    except RuntimeError:
        logger.exception("connection failed", extra={"request_id": "r2"})
    handler.flush()
    rendered = stream.getvalue()
    assert "connection failed" in rendered
    assert PASSWORD not in rendered


def test_install_log_redaction_is_idempotent_and_targets_handlers():
    logger = logging.getLogger("shunya.test.idempotent")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.handlers.clear()
    logger.propagate = False
    logger.addHandler(handler)

    install_log_redaction("shunya.test.idempotent")
    first = sum(1 for f in handler.filters if isinstance(f, RedactionFilter))
    install_log_redaction("shunya.test.idempotent")
    second = sum(1 for f in handler.filters if isinstance(f, RedactionFilter))
    assert first == 1 and second == 1


# ---------------------------------------------------------------------------
# Wiring: the application factory must install the filter
# ---------------------------------------------------------------------------


def test_create_app_installs_redaction_on_its_handlers(app):
    handlers = list(app.logger.handlers) + list(logging.getLogger().handlers)
    assert handlers, "expected the app factory to configure at least one handler"
    assert any(
        isinstance(f, RedactionFilter)
        for handler in handlers
        for f in handler.filters
    ), "create_app() did not install the log redaction filter"


def test_application_logger_output_never_contains_the_credential(app):
    """End-to-end through the real app logger: emit the defect and read the output."""
    from pythonjsonlogger import jsonlogger

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(jsonlogger.JsonFormatter(JSON_FORMAT))
    app.logger.addHandler(handler)
    try:
        app.logger.info(
            "SHUNYA OS initialised",
            extra={"request_id": "bootstrap", "db": CREDENTIAL_URI},
        )
        for h in app.logger.handlers:
            h.flush()
    finally:
        app.logger.removeHandler(handler)
    assert PASSWORD not in stream.getvalue()
