"""IMAP email reading adapter.

Uses imaplib (stdlib) for reading/searching emails from IMAP servers.
Falls back to a stub when imaplib is unavailable (unlikely, as it is stdlib).

Usage::

    adapter = IMAPAdapter(host="imap.example.com", username="user", password="pass")
    for msg in adapter.read_emails(folder="INBOX", limit=10):
        print(msg["subject"])
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from adapters import EmailReaderAdapter

logger = logging.getLogger(__name__)


class IMAPAdapter(EmailReaderAdapter):
    """Read and search email via IMAP.

    Parameters
    ----------
    host : str
        IMAP server hostname.
    port : int
        IMAP server port (default 993 for SSL).
    username : str
        Authentication username.
    password : str
        Authentication password.
    use_ssl : bool
        Use SSL (True, default).  Set to False for non-SSL on port 143.
    timeout : int
        Connection timeout in seconds (default 30).
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 993,
        username: str | None = None,
        password: str | None = None,
        use_ssl: bool = True,
        timeout: int = 30,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_ssl = use_ssl
        self._timeout = timeout
        self._available = True

    # ------------------------------------------------------------------
    # EmailReaderAdapter interface
    # ------------------------------------------------------------------

    def read_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        since: str | None = None,
        search_criteria: str | None = None,
        mark_seen: bool = True,
    ) -> list[dict[str, Any]]:
        """Read emails from an IMAP folder.

        Parameters
        ----------
        folder : str
            Mailbox folder name (default "INBOX").
        limit : int
            Max messages to return (default 10).
        since : str | None
            Only messages after this date (ISO-8601, e.g. "2025-01-01").
        search_criteria : str | None
            Raw IMAP search string override (e.g. ``"UNSEEN"``,
            ``'FROM "alice"'``).  When set, *since* is ignored.
        mark_seen : bool
            Whether to mark fetched messages as \\Seen (default True).

        Returns
        -------
        list[dict]
            Each dict has keys: ``uid``, ``subject``, ``from``, ``to``,
            ``date``, ``body`` (plain text), ``html``, ``flags``, ``seen``.
        """
        if not self._available:
            return self._stub_read(folder, limit, since, search_criteria)

        try:
            import imaplib
            import email
            from email.header import decode_header

            if self._use_ssl:
                conn = imaplib.IMAP4_SSL(self._host, self._port, timeout=self._timeout)
            else:
                conn = imaplib.IMAP4(self._host, self._port, timeout=self._timeout)

            conn.login(self._username or "", self._password or "")
            conn.select(folder)

            # Build search criteria
            if search_criteria:
                search_args = search_criteria
            elif since:
                # Convert ISO date to IMAP format (DD-Mon-YYYY)
                try:
                    dt = datetime.fromisoformat(since)
                    imap_date = dt.strftime("%d-%b-%Y")
                    search_args = f'SINCE {imap_date}'
                except ValueError:
                    search_args = "ALL"
            else:
                search_args = "ALL"

            _status, data = conn.search(None, search_args)
            msg_ids = data[0].split() if data[0] else []

            # Fetch newest first (highest UID)
            msg_ids = msg_ids[-limit:] if msg_ids else []
            results: list[dict[str, Any]] = []

            for mid in reversed(msg_ids):
                _status, data = conn.fetch(mid, "(RFC822)")
                if not data or data[0] is None:
                    continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = self._decode_mime_header(msg.get("Subject", "(no subject)"))
                from_addr = self._decode_mime_header(msg.get("From", ""))
                to_addr = self._decode_mime_header(msg.get("To", ""))
                date_str = msg.get("Date", "")
                message_id = msg.get("Message-ID", "")

                # Extract body
                body_text = ""
                body_html = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        if ctype == "text/plain" and not body_text:
                            body_text = self._decode_payload(part)
                        elif ctype == "text/html" and not body_html:
                            body_html = self._decode_payload(part)
                else:
                    body_text = self._decode_payload(msg)

                if not mark_seen:
                    conn.store(mid, "-FLAGS", "\\Seen")

                results.append(
                    {
                        "uid": mid.decode() if isinstance(mid, bytes) else str(mid),
                        "message_id": message_id,
                        "subject": subject,
                        "from": from_addr,
                        "to": to_addr,
                        "date": date_str,
                        "body": body_text[:10000] if body_text else "",
                        "html": body_html[:50000] if body_html else "",
                        "seen": mark_seen,
                    }
                )

            conn.logout()
            logger.info("Fetched %d emails from %s/%s", len(results), self._host, folder)
            return results

        except Exception as exc:
            logger.error("IMAP read failed: %s", exc)
            print(f"[stub] IMAPAdapter.read_emails(folder={folder!r}, limit={limit}) "
                  f"— connection failed ({exc}). Returning stub email data.")
            # Return a stub email on connection failure (no server running)
            from datetime import datetime, timezone
            return [
                {
                    "stub": True,
                    "uid": "1",
                    "subject": "[stub] Welcome to SHUNYA",
                    "from": "system@shunya.local",
                    "to": "founder@shunya.local",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "body": (
                        f"[stub] Connection to {self._host}:{self._port} failed. "
                        f"This is stub data — no real IMAP server was reachable."
                    ),
                    "seen": False,
                }
            ]

    def list_folders(self) -> list[dict[str, Any]]:
        """List available IMAP folders/mailboxes.

        Returns
        -------
        list[dict]
            Each dict has keys: ``name``, ``delimiter``, ``flags``.
        """
        if not self._available:
            msg = f"[stub] IMAPAdapter.list_folders() — would list folders on {self._host}"
            print(msg)
            return [{"stub": True, "message": msg}]

        try:
            import imaplib

            if self._use_ssl:
                conn = imaplib.IMAP4_SSL(self._host, self._port, timeout=self._timeout)
            else:
                conn = imaplib.IMAP4(self._host, self._port, timeout=self._timeout)

            conn.login(self._username or "", self._password or "")
            _status, data = conn.list()
            conn.logout()

            folders: list[dict[str, Any]] = []
            for line in data:
                decoded = line.decode("utf-8", errors="replace") if isinstance(line, bytes) else line
                # IMAP LIST response: (\\HasNoChildren) "/" "INBOX"
                parts = decoded.split('"')
                flags_part = parts[0].strip("() ") if len(parts) > 0 else ""
                name = parts[-1].strip() if len(parts) > 1 else decoded
                folders.append({"name": name, "flags": flags_part.split() if flags_part else []})

            return folders

        except Exception as exc:
            logger.error("IMAP list folders failed: %s", exc)
            return [{"error": str(exc)}]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_mime_header(value: str) -> str:
        """Decode a MIME-encoded header value (e.g. =?UTF-8?Q?...)."""
        from email.header import decode_header

        if not value:
            return ""
        parts = decode_header(value)
        decoded_parts: list[str] = []
        for part_bytes, charset in parts:
            if isinstance(part_bytes, bytes):
                decoded_parts.append(part_bytes.decode(charset or "utf-8", errors="replace"))
            else:
                decoded_parts.append(part_bytes)
        return " ".join(decoded_parts)

    @staticmethod
    def _decode_payload(part: Any) -> str:
        """Safely decode an email part payload."""
        try:
            payload = part.get_payload(decode=True)
            if payload is None:
                return ""
            charset = part.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
        except Exception:
            return ""

    def _stub_read(
        self,
        folder: str,
        limit: int,
        since: str | None,
        search_criteria: str | None,
    ) -> list[dict[str, Any]]:
        """Stub when imaplib is unavailable."""
        msg = (
            f"[stub] IMAPAdapter.read_emails(folder={folder!r}, limit={limit}, "
            f"since={since!r}, search={search_criteria!r}) — "
            f"would connect to {self._host}:{self._port}"
        )
        logger.warning(msg)
        print(msg)
        return [
            {
                "stub": True,
                "uid": "1",
                "subject": "[stub] Welcome to SHUNYA",
                "from": "system@shunya.local",
                "to": "founder@shunya.local",
                "date": datetime.now(timezone.utc).isoformat(),
                "body": msg,
                "seen": False,
            }
        ]

    def __repr__(self) -> str:
        return (
            f"IMAPAdapter(host={self._host!r}, port={self._port}, "
            f"username={self._username!r})"
        )