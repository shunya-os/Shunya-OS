"""
LibreOffice Document Adapter — REAL implementation via ``libreoffice`` CLI.

Requires: ``libreoffice --headless`` on PATH (system package).

Converts between ODT, DOCX, PDF, TXT, HTML. Creates ODT documents
using a basic zip-based ODF template.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from adapters import DocumentAdapter


class LibreOfficeAdapter(DocumentAdapter):
    """Document creation and conversion backed by LibreOffice headless."""

    # Mapping from short format names to LibreOffice filter names
    FILTER_MAP: dict[str, str] = {
        "odt": "writer8",
        "docx": "MS Word 2007 XML",
        "pdf": "writer_pdf_Export",
        "txt": "Text",
        "html": "HTML",
        "rtf": "Rich Text Format",
    }

    SUPPORTED_CREATE_FORMATS = {"odt"}

    # ── DocumentAdapter ──────────────────────────────────────────────

    def create_document(self, title: str, content: str, fmt: str = "odt") -> str:
        """Create a minimal ODF document with *title* and *content*.

        Returns the path to the created file.
        """
        fmt = fmt.lower()
        if fmt not in self.SUPPORTED_CREATE_FORMATS:
            raise ValueError(
                f"LibreOfficeAdapter.create_document only supports {self.SUPPORTED_CREATE_FORMATS}, "
                f"got {fmt!r}. Use .convert() afterwards for other formats."
            )

        out_dir = tempfile.mkdtemp(prefix="shunya_lo_")
        out_path = os.path.join(out_dir, f"{_safe_filename(title)}.{fmt}")

        _build_minimal_odt(out_path, title, content)
        return out_path

    def convert(self, source_path: str, target_fmt: str) -> str:
        """Convert a document to *target_fmt* via ``libreoffice --headless``.

        Returns the path to the converted file.
        Raises ``RuntimeError`` on failure.
        """
        target_fmt = target_fmt.lower()
        filter_name = self.FILTER_MAP.get(target_fmt)
        if filter_name is None:
            raise ValueError(
                f"Unsupported target format {target_fmt!r}. "
                f"Supported: {list(self.FILTER_MAP)}"
            )

        src = Path(source_path)
        if not src.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        out_dir = tempfile.mkdtemp(prefix="shunya_lo_convert_")

        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to", f"{target_fmt}:{filter_name}",
            "--outdir", out_dir,
            str(src.resolve()),
        ]

        _run_or_stub(cmd, hint=f"libreoffice --headless --convert-to {target_fmt} {source_path}")

        # LibreOffice output: <stem>.<target_fmt> in out_dir
        stem = src.stem
        result = os.path.join(out_dir, f"{stem}.{target_fmt}")
        if os.path.isfile(result):
            return result

        # Fallback: search out_dir for any file
        candidates = list(Path(out_dir).iterdir())
        if candidates:
            return str(candidates[0])

        raise RuntimeError(
            f"LibreOffice conversion produced no output file in {out_dir}"
        )

    def extract_text(self, path: str) -> str:
        """Extract plain text by converting to TXT with LibreOffice."""
        txt_path = self.convert(path, "txt")
        with open(txt_path, encoding="utf-8", errors="replace") as fh:
            return fh.read()


# ── helpers ─────────────────────────────────────────────────────────


def _safe_filename(title: str) -> str:
    """Sanitise *title* for use as a filesystem name."""
    safe = "".join(c if c.isalnum() or c in " _.-" else "_" for c in title)
    return safe.strip() or "untitled"


def _build_minimal_odt(path: str, title: str, content: str) -> None:
    """Build a minimal valid ODF (ODT) file at *path*.

    The ODF format is a ZIP archive containing XML files.  We write
    just enough for LibreOffice/Word to open it.
    """
    ns = (
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
        'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"'
    )

    mimetype = b"application/vnd.oasis.opendocument.text"

    content_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<office:document-content {ns} '
        'office:version="1.2">'
        '<office:body>'
        '<office:text>'
        f'<text:h text:style-name="Heading_20_1">{_xml_escape(title)}</text:h>'
        f'<text:p>{_xml_escape(content)}</text:p>'
        '</office:text>'
        '</office:body>'
        '</office:document-content>'
    )

    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<office:document-styles {ns} office:version="1.2">'
        '<office:styles>'
        '<style:style style:name="Heading_20_1" style:family="paragraph" '
        'style:parent-style-name="Standard" style:next-style-name="Text_20_body" '
        'style:default-outline-level="1">'
        '<style:text-properties fo:font-size="140%" fo:font-weight="bold"/>'
        '</style:style>'
        '</office:styles>'
        '</office:document-styles>'
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        # ODF *requires* mimetype to be stored uncompressed and first
        zf.writestr("mimetype", mimetype, compress_type=zipfile.ZIP_STORED)
        zf.writestr("content.xml", content_xml)
        zf.writestr("styles.xml", styles_xml)
        # Minimal manifest
        manifest = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" '
            'manifest:version="1.2">'
            '<manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.text" '
            'manifest:full-path="/"/>'
            '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>'
            '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="styles.xml"/>'
            '</manifest:manifest>'
        )
        zf.writestr("META-INF/manifest.xml", manifest)


def _xml_escape(text: str) -> str:
    """Minimal XML escaping for text content."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _run_or_stub(cmd: list[str], hint: str) -> None:
    """Run *cmd* or, if the binary is not found, emit a clear stub notice.

    This lets the adapter function during development even when
    LibreOffice is not installed.
    """
    try:
        subprocess.run(
            cmd,
            capture_output=True,
            timeout=120,
            check=True,
        )
    except FileNotFoundError:
        print(
            f"[LibreOfficeAdapter] WARNING: 'libreoffice' not found on PATH. "
            f"Would run: {hint}"
        )
    except subprocess.CalledProcessError as exc:
        msg = exc.stderr.decode() if exc.stderr else str(exc)
        raise RuntimeError(f"LibreOffice conversion failed: {msg}") from exc
