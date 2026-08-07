"""SMTP email sending adapter.

Uses smtplib (stdlib) when available — which is always, since smtplib is part
of the Python standard library.  Provides a stub path for environments where it
has been explicitly removed.

Usage::

    adapter = SMTPAdapter(host="smtp.example.com", port=587, username="user", password="pass")
    adapter.send_email(to=["alice@example.com"], subject="Hello", body="World")
"""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from adapters import EmailSenderAdapter

logger = logging.getLogger(__name__)


class SMTPAdapter(EmailSenderAdapter):
    """Send email via SMTP.

    Parameters
    ----------
    host : str
        SMTP server hostname.
    port : int
        SMTP server port (default 587 for STARTTLS, 465 for SSL).
    username : str | None
        Authentication username.
    password : str | None
        Authentication password.
    use_tls : bool
        Use STARTTLS (True, default) or direct SSL (False with port 465).
    timeout : int
        Connection timeout in seconds (default 30).
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        timeout: int = 30,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._timeout = timeout
        self._available = True

    # ------------------------------------------------------------------
    # EmailSenderAdapter interface
    # ------------------------------------------------------------------

    def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        from_addr: str | None = None,
        html: bool = False,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send an email.

        Parameters
        ----------
        to : list[str]
            Primary recipients.
        subject : str
            Email subject.
        body : str
            Email body text (plain text or HTML).
        cc : list[str] | None
            CC recipients.
        bcc : list[str] | None
            BCC recipients.
        from_addr : str | None
            Sender address.  Falls back to *username* if not given.
        html : bool
            If True, *body* is treated as HTML.
        attachments : list[dict] | None
            Optional list of attachment dicts with keys ``filename``, ``data``
            (bytes), and ``mimetype`` (str).

        Returns
        -------
        dict
            ``{"success": True, "message_id": "<...>"}`` on success,
            ``{"success": False, "error": "..."}`` on failure.
        """
        if not self._available:
            return self._stub_send(to, subject, body, cc, bcc, from_addr, html, attachments)

        from_addr = from_addr or self._username or "noreply@shunya.local"
        cc = cc or []
        bcc = bcc or []
        attachments = attachments or []

        try:
            import smtplib

            msg = self._build_message(from_addr, to, cc, bcc, subject, body, html, attachments)

            if self._use_tls:
                server = smtplib.SMTP(self._host, self._port, timeout=self._timeout)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(self._host, self._port, timeout=self._timeout)

            if self._username and self._password:
                server.login(self._username, self._password)

            result = server.sendmail(from_addr, to + cc + bcc, msg.as_string())
            server.quit()

            message_id = msg["Message-ID"] or ""
            logger.info("Email sent to %s (subject=%s)", to, subject)
            return {"success": True, "message_id": message_id, "rejected": result}

        except Exception as exc:
            logger.error("SMTP send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_message(
        from_addr: str,
        to: list[str],
        cc: list[str],
        bcc: list[str],
        subject: str,
        body: str,
        html: bool,
        attachments: list[dict[str, Any]],
    ) -> MIMEMultipart:
        """Construct a MIME message."""
        import uuid

        msg = MIMEMultipart("mixed")
        msg["From"] = from_addr
        msg["To"] = ", ".join(to)
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg["Subject"] = subject
        msg["Message-ID"] = f"<{uuid.uuid4().hex}@shunya.local>"

        # Body
        body_part = MIMEMultipart("alternative")
        if html:
            body_part.attach(MIMEText(body, "plain", "utf-8"))
            body_part.attach(MIMEText(body, "html", "utf-8"))
        else:
            body_part.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(body_part)

        # Attachments — each dict has keys: filename, data (bytes), mimetype
        for att in attachments:
            part = MIMEText(att["data"].decode("utf-8", errors="replace"), "base64", "utf-8")
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=att.get("filename", "attachment.bin"),
            )
            if att.get("mimetype"):
                part.set_type(att["mimetype"])
            msg.attach(part)

        return msg

    def _stub_send(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: list[str] | None,
        bcc: list[str] | None,
        from_addr: str | None,
        html: bool,
        attachments: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Stub used when smtplib is unavailable."""
        msg = (
            f"[stub] SMTPAdapter.send_email(to={to}, subject={subject!r}, "
            f"cc={cc}, bcc={bcc}, from={from_addr}, html={html}, "
            f"attachments={len(attachments or [])}) — "
            f"would connect to {self._host}:{self._port}"
        )
        logger.warning(msg)
        print(msg)
        return {"success": True, "stub": True, "message": msg}

    def __repr__(self) -> str:
        return (
            f"SMTPAdapter(host={self._host!r}, port={self._port}, "
            f"username={self._username!r})"
        )