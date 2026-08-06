"""
ONLYOFFICE Document Adapter.

Creates, edits, converts, exports, and imports documents.
When ``ONLYOFFICE_API_URL`` and ``ONLYOFFICE_JWT_SECRET`` are set in the
environment, this adapter uses the ONLYOFFICE Document Server REST API
(ConvertService.ashx) for conversion.  Otherwise it falls back to a
pure-Python implementation using python-docx and fpdf2 — identical to the
LibreOfficeAdapter's fallback, providing full functionality without a
running ONLYOFFICE server.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from adapters import DocumentAdapter
from adapters.document.libreoffice import (
    _create_docx,
    _create_html,
    _create_odt,
    _create_pdf,
    _create_txt,
    _edit_docx,
    _edit_odt,
    _edit_txt,
    _extract_docx,
    _extract_html,
    _extract_odt,
    _extract_pdf,
    _safe_filename,
    _xml_escape,
)


class OnlyOfficeAdapter(DocumentAdapter):
    """Document editing/conversion via ONLYOFFICE Document Server or
    pure-Python fallback.

    Environment variables (optional):
        ``ONLYOFFICE_API_URL``   — Base URL of the ONLYOFFICE Document
                                   Server, e.g. ``http://docserver:8080``.
        ``ONLYOFFICE_JWT_SECRET`` — JWT secret for API authentication.

    When both variables are set the adapter attempts to use the live server
    for conversions.  Otherwise it uses the same pure-Python helpers that
    the LibreOfficeAdapter uses.
    """

    def __init__(self) -> None:
        self.api_url = os.environ.get("ONLYOFFICE_API_URL", "").rstrip("/")
        self.jwt_secret = os.environ.get("ONLYOFFICE_JWT_SECRET", "")
        self._active = bool(self.api_url and self.jwt_secret)

    # ── Public API ─────────────────────────────────────────────────────

    def create_document(
        self,
        title: str,
        content: str,
        fmt: str = "odt",
    ) -> str:
        """Create a new document.

        Supported output formats: ``odt``, ``docx``, ``pdf``, ``txt``, ``html``.
        """
        fmt = fmt.lower()
        creators: dict[str, Any] = {
            "odt": _create_odt,
            "docx": _create_docx,
            "pdf": _create_pdf,
            "txt": _create_txt,
            "html": _create_html,
        }
        if fmt not in creators:
            raise ValueError(
                f"Unsupported format {fmt!r}. Supported: {sorted(creators)}"
            )

        out_dir = tempfile.mkdtemp(prefix="shunya_oo_")
        out_path = os.path.join(out_dir, f"{_safe_filename(title)}.{fmt}")
        creators[fmt](out_path, title, content)
        return out_path

    def edit_document(
        self,
        path: str,
        new_content: str | None = None,
        insert_at: str | int | None = None,
        **kwargs: Any,
    ) -> str:
        """Edit an existing document in place."""
        src = Path(path)
        if not src.is_file():
            raise FileNotFoundError(f"Document not found: {path}")

        ext = src.suffix.lower()
        content = new_content or ""

        if ext == ".docx":
            _edit_docx(src, content, insert_at)
        elif ext == ".odt":
            _edit_odt(src, content, insert_at)
        elif ext == ".txt":
            _edit_txt(src, content, insert_at)
        else:
            # PDF/HTML: extract → rebuild → convert back
            text = self.extract_text(str(src))
            if new_content is not None:
                text = new_content
            elif insert_at is not None:
                text = text + "\n" + content
            tmp = self.create_document("edited", text, fmt="docx")
            converted = self.convert(tmp, ext.lstrip("."))
            shutil.copy2(converted, str(src))
        return str(src.resolve())

    def convert(self, source_path: str, target_fmt: str) -> str:
        """Convert a document to *target_fmt*.

        Uses the ONLYOFFICE ConvertService API when the server is
        configured; otherwise falls back to pure-Python conversion.
        """
        target_fmt = target_fmt.lower()
        src = Path(source_path)
        if not src.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        out_dir = tempfile.mkdtemp(prefix="shunya_oo_convert_")

        # ── ONLYOFFICE Server path ────────────────────────────────
        if self._active:
            try:
                return _convert_via_onlyoffice_api(
                    self.api_url,
                    self.jwt_secret,
                    str(src.resolve()),
                    target_fmt,
                    out_dir,
                )
            except Exception as exc:
                print(
                    f"[OnlyOfficeAdapter] WARNING: ONLYOFFICE API call "
                    f"failed ({exc}). Falling back to pure-Python."
                )

        # ── Pure-Python fallback ──────────────────────────────────
        return _convert_pure_onlyoffice(src, target_fmt, out_dir)

    def extract_text(self, path: str) -> str:
        """Extract plain text from a document.

        Supports ODT, DOCX, PDF, TXT, HTML.
        """
        src = Path(path)
        if not src.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        ext = src.suffix.lower()
        extractors: dict[str, Any] = {
            ".docx": _extract_docx,
            ".odt": _extract_odt,
            ".pdf": _extract_pdf,
            ".txt": lambda p: p.read_text(encoding="utf-8", errors="replace"),
            ".html": _extract_html,
            ".htm": _extract_html,
        }
        if ext in extractors:
            return extractors[ext](src)
        raise ValueError(f"Unsupported format for text extraction: {ext}")


# ===================================================================
# ONLYOFFICE ConvertService API (live server)
# ===================================================================

def _convert_via_onlyoffice_api(
    api_url: str,
    jwt_secret: str,
    source_path: str,
    target_fmt: str,
    out_dir: str,
) -> str:
    """Convert a file using the ONLYOFFICE Document Server
    `ConvertService.ashx` endpoint.

    See https://api.onlyoffice.com/docs/docs-api/additional-api/conversion-api/
    """
    import base64
    import hmac
    import hashlib
    import time

    convert_url = f"{api_url}/ConvertService.ashx"

    # Read source file as base64
    with open(source_path, "rb") as fh:
        src_data = fh.read()
    src_b64 = base64.b64encode(src_data).decode("ascii")

    src_ext = Path(source_path).suffix.lstrip(".").lower()

    payload = {
        "async": False,
        "filetype": src_ext,
        "key": f"convert_{int(time.time())}",
        "outputtype": target_fmt,
        "title": Path(source_path).name,
        "url": f"data:application/octet-stream;base64,{src_b64}",
    }

    # JWT token
    token_payload = {
        "payload": payload,
        "exp": int(time.time()) + 300,
    }
    token = jwt_encode(token_payload, jwt_secret)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    req = urllib.request.Request(
        convert_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if result.get("error"):
        raise RuntimeError(
            f"ONLYOFFICE conversion error: {result.get('error', 'unknown')} — "
            f"{result.get('errorDescription', '')}"
        )

    # Download the result
    file_url = result.get("fileUrl")
    if not file_url:
        raise RuntimeError(
            f"ONLYOFFICE returned no fileUrl: {result}"
        )

    stem = Path(source_path).stem
    out_path = os.path.join(out_dir, f"{stem}.{target_fmt}")
    urllib.request.urlretrieve(file_url, out_path)
    return out_path


def jwt_encode(payload: dict, secret: str) -> str:
    """Simple HS256 JWT encoding (no external lib needed)."""
    import base64
    import hashlib
    import hmac
    import json

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(
        secret.encode(), signing_input, hashlib.sha256
    ).digest()
    sig_b64 = _b64url(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def _b64url(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


# ===================================================================
# Pure-Python conversion fallback (shared logic with LibreOfficeAdapter)
# ===================================================================

def _convert_pure_onlyoffice(src: Path, target_fmt: str, out_dir: str) -> str:
    """Convert *src* to *target_fmt* using pure-Python libraries."""
    ext = src.suffix.lower()
    stem = src.stem
    out_path = os.path.join(out_dir, f"{stem}.{target_fmt}")

    if ext.lstrip(".") == target_fmt:
        shutil.copy2(str(src), out_path)
        return out_path

    # Extract text first
    extractors: dict[str, Any] = {
        ".docx": _extract_docx,
        ".odt": _extract_odt,
        ".pdf": _extract_pdf,
        ".txt": lambda p: p.read_text(encoding="utf-8", errors="replace"),
        ".html": _extract_html,
        ".htm": _extract_html,
    }

    if ext not in extractors:
        raise ValueError(f"Cannot extract text from {ext} files")

    text = extractors[ext](src)

    # Write target
    creators: dict[str, Any] = {
        "odt": _create_odt,
        "docx": _create_docx,
        "pdf": _create_pdf,
        "txt": _create_txt,
        "html": _create_html,
    }
    if target_fmt not in creators:
        raise ValueError(f"Unsupported target format {target_fmt!r}")
    creators[target_fmt](out_path, stem, text)
    return out_path