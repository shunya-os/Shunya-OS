"""Text safety for ingestion boundaries (ZG-03 B3).

PostgreSQL rejects the NUL byte (0x00) in ``text``/``varchar`` values
("invalid byte sequence for encoding UTF8: 0x00") — an unfiltered NUL from a
CSV cell, document extraction, webhook body or email payload turns an
otherwise-valid insert into a 500. This is the single sanitization point:
every ingestion boundary strips NUL bytes (and only NUL bytes — no other
content is altered).

Only NUL is stripped: it is never a legitimate part of user text, it is the
only codepoint the database refuses, and altering anything else would corrupt
user content.
"""

from __future__ import annotations

from typing import Any


def sanitize_text(value: Any) -> str:
    """Strip NUL bytes from a value; coerce to str ('' for None)."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.replace(b"\x00", b"").decode("utf-8", errors="replace")
    return str(value).replace("\x00", "")


def sanitize_dict_values(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``data`` with every string-carrying value NUL-stripped."""
    return {
        k: sanitize_text(v) if isinstance(v, (str, bytes)) else v
        for k, v in data.items()
    }