"""Standalone PDF-text extraction, runnable as ``python -m app.document.extract_cli <path>``.

Purpose: the upload path needs PDF text extraction isolated in its own process
(a malformed PDF must not take down the web worker). The previous inline
``python3 -c`` invocation embedded the caller-supplied filename directly into
Python source — a quote, newline or backslash in the filename broke the script,
and it hard-coded ``python3`` instead of the interpreter actually running the
server. This module takes the path as argv (never source) and is invoked with
``sys.executable``.

Prints the extracted text (first 5000 chars) to stdout, or a truthful
degradation marker:
  * "No text could be extracted from this PDF."  — extraction ran, found nothing
  * "[extraction limited: ...]"                  — extraction failed internally

Exit codes: 0 = ran (check the marker), 2 = usage error.
"""
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m app.document.extract_cli <file_path>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if text.strip():
            print(text[:5000])
        else:
            print("No text could be extracted from this PDF.")
    except Exception as e:  # noqa: BLE001 — the caller renders the marker truthfully
        print(f"[extraction limited: {e}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())