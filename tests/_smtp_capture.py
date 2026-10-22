"""In-process STARTTLS SMTP capture server for delivery tests (G1.24).

The invitation journey claims "the invitee received the message". Proving that
against a real inbox needs an authorized provider, which a test environment does
not have — but proving it against a *local capture sink* is both possible and
honest, provided the capture exercises the same protocol path the production
code uses:

    smtplib.SMTP(host, port) → starttls() → login() → sendmail()

So this server speaks ESMTP with STARTTLS and AUTH LOGIN/PLAIN, accepts mail, and
exposes the received messages. It binds loopback only. The certificate is
generated per test run and never committed; ``smtplib`` uses an unverified
context when the caller passes none, so the application code is unchanged.

This is a test helper, not production code: it imports nothing from ``app``.
"""

from __future__ import annotations

import asyncio
import base64
import datetime
import ipaddress
import json
import ssl
import threading
import time

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_self_signed(tmpdir) -> tuple[str, str]:
    """Write a short-lived self-signed cert/key for 127.0.0.1. Returns paths."""
    import os

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                x509.DNSName("localhost"),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path = os.path.join(str(tmpdir), "capture-cert.pem")
    key_path = os.path.join(str(tmpdir), "capture-key.pem")
    with open(cert_path, "wb") as handle:
        handle.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(key_path, "wb") as handle:
        handle.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))
    return cert_path, key_path


class SMTPCaptureServer:
    """Loopback ESMTP sink with STARTTLS + AUTH, running on its own thread."""

    def __init__(self, cert_path: str, key_path: str):
        self.cert_path = cert_path
        self.key_path = key_path
        self.messages: list[dict] = []
        self.port = 0
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._server = None
        self._ready = threading.Event()
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(cert_path, key_path)

    # -- lifecycle ---------------------------------------------------------
    def start(self, timeout: float = 10.0) -> "SMTPCaptureServer":
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="g124-smtp-capture")
        self._thread.start()
        if not self._ready.wait(timeout):
            raise RuntimeError("SMTP capture server did not start")
        return self

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._server = self._loop.run_until_complete(
                asyncio.start_server(self._handle, host="127.0.0.1", port=0)
            )
            self.port = self._server.sockets[0].getsockname()[1]
            self._ready.set()
            self._loop.run_forever()
        finally:
            try:
                self._loop.close()
            except Exception:
                pass

    def stop(self) -> None:
        if self._loop and self._server:
            self._loop.call_soon_threadsafe(self._server.close)
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=5)

    # -- protocol ----------------------------------------------------------
    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        writer.write(b"220 g124-capture ESMTP\r\n")
        await writer.drain()
        envelope = {"from": "", "to": [], "auth_user": "", "tls": False}
        tls_active = False
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                command = line.decode("utf-8", "replace").strip()
                upper = command.upper()

                if upper.startswith("EHLO"):
                    caps = b"250-g124\r\n250-8BITMIME\r\n250-SMTPUTF8\r\n"
                    if not tls_active:
                        caps += b"250-STARTTLS\r\n"
                    caps += b"250-AUTH LOGIN PLAIN\r\n250 OK\r\n"
                    writer.write(caps)
                    await writer.drain()

                elif upper.startswith("HELO"):
                    writer.write(b"250 g124\r\n")
                    await writer.drain()

                elif upper.startswith("STARTTLS"):
                    writer.write(b"220 2.0.0 Ready to start TLS\r\n")
                    await writer.drain()
                    await writer.start_tls(self.ssl_context)
                    tls_active = True
                    envelope["tls"] = True

                elif upper.startswith("AUTH LOGIN"):
                    writer.write(b"334 VXNlcm5hbWU6\r\n")
                    await writer.drain()
                    user_b64 = (await reader.readline()).strip()
                    writer.write(b"334 UGFzc3dvcmQ6\r\n")
                    await writer.drain()
                    pass_b64 = (await reader.readline()).strip()
                    try:
                        envelope["auth_user"] = base64.b64decode(user_b64).decode()
                        envelope["auth_password_present"] = bool(base64.b64decode(pass_b64))
                    except Exception:
                        envelope["auth_user"] = "<undecodable>"
                    writer.write(b"235 2.7.0 Authentication successful\r\n")
                    await writer.drain()

                elif upper.startswith("AUTH PLAIN"):
                    parts = command.split(" ", 2)
                    blob = parts[2] if len(parts) == 3 else ""
                    if not blob:
                        writer.write(b"334 \r\n")
                        await writer.drain()
                        blob = (await reader.readline()).strip().decode()
                    try:
                        decoded = base64.b64decode(blob).decode()
                        fields = decoded.split("\x00")
                        if len(fields) >= 3:
                            envelope["auth_user"] = fields[1]
                            envelope["auth_password_present"] = bool(fields[2])
                    except Exception:
                        pass
                    writer.write(b"235 2.7.0 Authentication successful\r\n")
                    await writer.drain()

                elif upper.startswith("MAIL FROM"):
                    envelope["from"] = command.split(":", 1)[1].strip().strip("<>")
                    writer.write(b"250 2.1.0 OK\r\n")
                    await writer.drain()

                elif upper.startswith("RCPT TO"):
                    envelope["to"].append(command.split(":", 1)[1].strip().strip("<>"))
                    writer.write(b"250 2.1.5 OK\r\n")
                    await writer.drain()

                elif upper == "DATA":
                    writer.write(b"354 End data\r\n")
                    await writer.drain()
                    chunks = []
                    while True:
                        chunk = await reader.readline()
                        if not chunk or chunk in (b".\r\n", b".\n"):
                            break
                        if chunk.startswith(b".."):
                            chunk = chunk[1:]
                        chunks.append(chunk)
                    record = dict(envelope)
                    record.update({
                        "received_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "raw": b"".join(chunks).decode("utf-8", "replace"),
                    })
                    self.messages.append(record)
                    envelope = {"from": "", "to": [], "auth_user": "", "tls": tls_active}
                    writer.write(b"250 2.0.0 OK queued\r\n")
                    await writer.drain()

                elif upper in ("RSET", "NOOP"):
                    writer.write(b"250 OK\r\n")
                    await writer.drain()

                elif upper == "QUIT":
                    writer.write(b"221 2.0.0 Bye\r\n")
                    await writer.drain()
                    break

                else:
                    writer.write(b"502 5.5.2 Not implemented\r\n")
                    await writer.drain()
        except (ConnectionResetError, BrokenPipeError, ssl.SSLError):
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    # -- inspection --------------------------------------------------------
    def dump(self) -> str:
        return json.dumps(self.messages, indent=2)

    def reset(self) -> None:
        self.messages.clear()
