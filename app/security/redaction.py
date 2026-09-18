"""SHUNYA OS — Log secret redaction (immune system: secrets hygiene).

A production DB URL was previously written to the journal on every worker
boot, exposing the database credential to anyone able to read logs. This
module closes that class of defect in two layers:

1. **At the source** — :func:`safe_database_descriptor` renders a
   credential-free descriptor (``postgresql://host:port/database``) for
   operational log lines, so the intended diagnostic value is kept while the
   secret is removed.
2. **Defence in depth** — :class:`RedactionFilter`, installed by
   :func:`install_log_redaction`, scrubs credential-shaped text from every
   log record that passes through the configured handlers: the message, its
   interpolation args, arbitrary ``extra=`` attributes (which the JSON
   formatter serialises), and exception text.

The filter is deliberately conservative about *what* it treats as a secret
(URL userinfo, ``key=value`` pairs whose key names a credential, bearer
tokens) so that ordinary product text is not rewritten.

Nothing in this module is business logic; it is a security control and must
remain business-agnostic.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Iterable

REDACTED = "***REDACTED***"

# scheme://user:password@host  ->  scheme://***REDACTED***@host
_URL_CREDENTIALS = re.compile(
    r"(?P<scheme>[a-zA-Z][a-zA-Z0-9+.\-]*://)"
    r"(?P<user>[^:/@\s]+):(?P<password>[^@\s]+)@"
)

# key=value / key: value where the key names a credential
_SECRET_KEY_NAMES = (
    r"password|passwd|pwd|secret|token|api[_-]?key|apikey|access[_-]?key|"
    r"secret[_-]?key|auth[_-]?token|client[_-]?secret|private[_-]?key|"
    r"database_url|db_url|dsn|connection[_-]?string|session[_-]?secret"
)
_KEY_VALUE_SECRET = re.compile(
    r"(?i)\b(?P<key>" + _SECRET_KEY_NAMES + r")\b\s*[:=]\s*"
    r"(?P<quote>[\"']?)(?P<value>[^\s,;\"'&}\]]+)(?P=quote)"
)

# Authorization: Bearer <token>
_BEARER_TOKEN = re.compile(
    r"(?i)\b(?P<key>bearer|authorization)\b\s*[:=]?\s*"
    r"(?P<value>[A-Za-z0-9\-._~+/]{12,}=*)"
)


def redact_secrets(text: str) -> str:
    """Return *text* with credential-shaped substrings replaced.

    Idempotent: already-redacted text is returned unchanged.
    """
    if not isinstance(text, str) or not text:
        return text

    def _url(match: "re.Match[str]") -> str:
        return f"{match.group('scheme')}{REDACTED}@"

    def _kv(match: "re.Match[str]") -> str:
        quote = match.group("quote")
        if match.group("value") == REDACTED:
            return match.group(0)
        return f"{match.group('key')}={quote}{REDACTED}{quote}"

    def _bearer(match: "re.Match[str]") -> str:
        if match.group("value") == REDACTED:
            return match.group(0)
        return f"{match.group('key')} {REDACTED}"

    text = _URL_CREDENTIALS.sub(_url, text)
    text = _KEY_VALUE_SECRET.sub(_kv, text)
    text = _BEARER_TOKEN.sub(_bearer, text)
    return text


def safe_database_descriptor(uri: Any) -> str:
    """Render a connection descriptor that carries no credentials.

    ``postgresql://user:pw@host:5432/db`` -> ``postgresql://host:5432/db``.
    Never raises: an unparseable value degrades to the scheme only.
    """
    if uri is None:
        return "<none>"
    raw = str(uri)

    try:
        from sqlalchemy.engine import make_url

        url = make_url(raw)
        host = url.host or "local"
        port = f":{url.port}" if url.port else ""
        database = url.database or ""
        return redact_secrets(f"{url.drivername}://{host}{port}/{database}")
    except Exception:
        pass

    # Fallback: strip userinfo with a regex rather than guessing at parsing.
    stripped = _URL_CREDENTIALS.sub(lambda m: f"{m.group('scheme')}", raw)
    return redact_secrets(stripped)


# ---------------------------------------------------------------------------
# Logging filter
# ---------------------------------------------------------------------------

_STRUCTURAL_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
)


class RedactionFilter(logging.Filter):
    """Scrub credential-shaped text from a log record before formatting.

    Applied to *handlers* (not loggers) so it sees every record that reaches
    output, including records whose ``extra=`` attributes the JSON formatter
    would otherwise serialise verbatim.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)

        if record.args:
            record.args = self._redact_args(record.args)

        for key, value in list(record.__dict__.items()):
            if key in _STRUCTURAL_ATTRS:
                continue
            if isinstance(value, str):
                redacted = redact_secrets(value)
                if redacted != value:
                    record.__dict__[key] = redacted
            elif isinstance(value, dict):
                record.__dict__[key] = self._redact_mapping(value)
            elif isinstance(value, (list, tuple)):
                record.__dict__[key] = type(value)(
                    redact_secrets(item) if isinstance(item, str) else item
                    for item in value
                )

        # Tracebacks are rendered by the FORMATTER (after filters run), so a
        # credential inside an exception message would bypass scrubbing. Render
        # it here, scrub it, and hand the formatter the scrubbed text instead.
        if record.exc_info:
            record.exc_text = redact_secrets(self._render_traceback(record.exc_info))
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = redact_secrets(record.exc_text)

        if record.stack_info:
            record.stack_info = redact_secrets(record.stack_info)
        return True

    @staticmethod
    def _render_traceback(exc_info: Any) -> str:
        import traceback

        try:
            return "".join(traceback.format_exception(*exc_info))
        except Exception:  # pragma: no cover - defensive: never break logging
            return ""

    @staticmethod
    def _redact_args(args: Any) -> Any:
        if isinstance(args, dict):
            return {k: (redact_secrets(v) if isinstance(v, str) else v) for k, v in args.items()}
        if isinstance(args, tuple):
            return tuple(redact_secrets(a) if isinstance(a, str) else a for a in args)
        return args

    @staticmethod
    def _redact_mapping(mapping: dict) -> dict:
        return {
            k: (redact_secrets(v) if isinstance(v, str) else v)
            for k, v in mapping.items()
        }


_INSTALLED_ATTR = "_shunya_redaction_filter"


def install_log_redaction(*extra_logger_names: str) -> int:
    """Attach :class:`RedactionFilter` to the handlers that emit logs.

    Idempotent — each handler receives at most one instance. Returns the number
    of handlers that now carry the filter. Safe to call before or after the
    gunicorn/app logging configuration runs.
    """
    names: Iterable[str] = (
        "root",
        "app",
        "werkzeug",
        "gunicorn",
        "gunicorn.error",
        "gunicorn.access",
        *extra_logger_names,
    )

    targets: list[logging.Handler] = []
    for name in names:
        logger = logging.getLogger() if name == "root" else logging.getLogger(name)
        targets.extend(logger.handlers)
    targets.extend(logging.getLogger().handlers)

    installed = 0
    for handler in dict.fromkeys(targets):  # de-dupe, preserve order
        if getattr(handler, _INSTALLED_ATTR, False):
            continue
        handler.addFilter(RedactionFilter())
        # Adding a filter also enables the handler if it had no level set.
        setattr(handler, _INSTALLED_ATTR, True)
        installed += 1
    return installed
