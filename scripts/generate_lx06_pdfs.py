#!/usr/bin/env python3
"""Convert the LX-06 duplication report markdown files to styled PDFs for public sharing."""
import markdown
import os
import subprocess
import sys

AUDIT_DIR = "/home/shunya-deploy/shunya_os/audit"

REPORTS = [
    {
        "md": "/home/shunya-deploy/shunya_os/frontend/src/DUPLICATION_MAP.md",
        "pdf": os.path.join(AUDIT_DIR, "LX-06_FRONTEND_DUPLICATION_MAP.pdf"),
        "title": "SHUNYA Frontend — Complete Duplication Map",
    },
    {
        "md": "/home/shunya-deploy/shunya_os/app/ARCHITECTURAL_DUPLICATION_REPORT.md",
        "pdf": os.path.join(AUDIT_DIR, "LX-06_BACKEND_DUPLICATION_REPORT.pdf"),
        "title": "SHUNYA OS — Backend Architectural Duplication Report (LX-06 Audit)",
    },
]

CSS = """
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 12px;
    line-height: 1.5;
    color: #1a1c1d;
    margin: 24px;
  }
  h1 { font-size: 22px; color: #4a3f2a; border-bottom: 3px solid #a4865f; padding-bottom: 8px; }
  h2 { font-size: 17px; color: #6b5b3e; margin-top: 24px; border-bottom: 1px solid #d4cec3; padding-bottom: 4px; }
  h3 { font-size: 14px; color: #4a3f2a; margin-top: 18px; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 11px; }
  th, td { border: 1px solid #ccc; padding: 5px 7px; text-align: left; vertical-align: top; }
  th { background: #f2efe9; font-weight: 600; }
  tr:nth-child(even) { background: #faf8f5; }
  code { background: #f2efe9; padding: 1px 4px; border-radius: 3px; font-size: 10.5px; color: #8b3a2a; }
  pre { background: #f2efe9; padding: 10px; border-radius: 4px; overflow-x: auto; }
  pre code { background: none; color: #1a1c1d; }
  strong { color: #8b3a2a; }
</style>
"""

def convert(md_path, pdf_path, title):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "toc"])
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>{CSS}</head>
<body>{body}</body></html>"""
    tmp_html = pdf_path + ".html"
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)
    # wkhtmltopdf options
    cmd = [
        "wkhtmltopdf",
        "--enable-local-file-access",
        "--encoding", "utf-8",
        "--page-size", "A4",
        "--margin-top", "15mm",
        "--margin-bottom", "15mm",
        "--margin-left", "12mm",
        "--margin-right", "12mm",
        "--footer-center", "[page]/[topage]",
        "--footer-font-size", "8",
        tmp_html, pdf_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(tmp_html)
    if result.returncode != 0:
        print(f"ERROR converting {md_path}:\n{result.stderr[:2000]}")
        return False
    print(f"OK: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
    return True

ok = True
for r in REPORTS:
    if not os.path.exists(r["md"]):
        print(f"MISSING: {r['md']}")
        ok = False
        continue
    if not convert(r["md"], r["pdf"], r["title"]):
        ok = False

sys.exit(0 if ok else 1)