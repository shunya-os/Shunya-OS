"""
ONLYOFFICE Document Adapter — STUB implementation.

ONLYOFFICE is a self-hosted document server with a REST API.
This stub documents the integration points for a real deployment.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

from adapters import DocumentAdapter


class OnlyOfficeAdapter(DocumentAdapter):
    """Document editing/conversion via ONLYOFFICE Document Server.

    .. caution:: **STUB** — a live ONLYOFFICE server is required.
       Set ``ONLYOFFICE_JWT_SECRET`` and ``ONLYOFFICE_API_URL`` env vars
       to activate.
    """

    def __init__(self) -> None:
        self.api_url = os.environ.get("ONLYOFFICE_API_URL", "")
        self.jwt_secret = os.environ.get("ONLYOFFICE_JWT_SECRET", "")
        self._active = bool(self.api_url and self.jwt_secret)

    # ── DocumentAdapter ──────────────────────────────────────────────

    def create_document(self, title: str, content: str, fmt: str = "odt") -> str:
        """Create a document via ONLYOFFICE.

        Uses the Conversion API (``ConvertService.ashx``) to produce a
        document from a plain-text source or template.

        STUB: Returns a placeholder path when the server is not configured.
        """
        if self._active:
            # Real implementation would POST to the Conversion API
            raise NotImplementedError(
                "OnlyOfficeAdapter.create_document: ONLYOFFICE server is configured "
                "but the REST integration is not yet implemented. "
                f"API URL: {self.api_url}"
            )

        # Stub: write a plain text file as a placeholder
        out_dir = tempfile.mkdtemp(prefix="shunya_oo_")
        stub_path = os.path.join(out_dir, f"{_safe(title)}.{fmt}")
        with open(stub_path, "w") as fh:
            fh.write(f"Title: {title}\n\n{content}")
        print(
            f"[OnlyOfficeAdapter] STUB: create_document({title!r}, fmt={fmt!r}) "
            f"→ {stub_path}. Install ONLYOFFICE Document Server and set "
            "ONLYOFFICE_API_URL / ONLYOFFICE_JWT_SECRET for a real document."
        )
        return stub_path

    def convert(self, source_path: str, target_fmt: str) -> str:
        """Convert a document via ONLYOFFICE Conversion API.

        STUB: Returns a placeholder path.
        """
        if self._active:
            raise NotImplementedError(
                "OnlyOfficeAdapter.convert: ONLYOFFICE server is configured "
                "but the REST integration is not yet implemented."
            )

        out_dir = tempfile.mkdtemp(prefix="shunya_oo_convert_")
        stub_path = os.path.join(out_dir, f"converted.{target_fmt}")
        with open(stub_path, "w") as fh:
            fh.write(f"[ONLYOFFICE STUB — converted from {source_path} to {target_fmt}]")
        print(
            f"[OnlyOfficeAdapter] STUB: convert({source_path}, {target_fmt!r}) → {stub_path}"
        )
        return stub_path

    def extract_text(self, path: str) -> str:
        """Extract text — falls back to reading the file directly for stubs,
        or would call the ONLYOFFICE Conversion API with output format=txt.
        """
        if os.path.isfile(path) and path.endswith(".txt"):
            with open(path, encoding="utf-8", errors="replace") as fh:
                return fh.read()

        # Stub fallback
        print(
            f"[OnlyOfficeAdapter] STUB: extract_text({path}) — returning dummy content."
        )
        return f"[ONLYOFFICE STUB — text extracted from {path}]"


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in " _.-" else "_" for c in name).strip() or "doc"
