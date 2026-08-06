#!/usr/bin/env python3
"""Convert PX-01 report to PDF."""
import markdown, os, subprocess, sys

AUDIT_DIR = "/home/shunya-deploy/shunya_os/audit"
MD = "/home/shunya-deploy/shunya_os/PX-01_REPORT.md"
PDF = os.path.join(AUDIT_DIR, "px-01-report.pdf")
TITLE = "PX-01 Implementation Report"

CSS = """
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #1a1c1d; margin: 24px; }
  h1 { font-size: 22px; color: #4a3f2a; border-bottom: 3px solid #a4865f; padding-bottom: 8px; }
  h2 { font-size: 17px; color: #6b5b3e; margin-top: 24px; border-bottom: 1px solid #d4cec3; padding-bottom: 4px; }
  h3 { font-size: 14px; color: #4a3f2a; margin-top: 18px; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 11px; }
  th, td { border: 1px solid #ccc; padding: 5px 7px; text-align: left; vertical-align: top; }
  th { background: #f2efe9; font-weight: 600; }
  tr:nth-child(even) { background: #faf8f5; }
  code { background: #f2efe9; padding: 1px 4px; border-radius: 3px; font-size: 10.5px; color: #8b3a2a; }
  pre { background: #f2efe9; padding: 10px; border-radius: 4px; overflow-x: auto; }
  strong { color: #8b3a2a; }
</style>
"""

with open(MD, "r", encoding="utf-8") as f: md_text = f.read()
body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "toc"])
html = f"<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>{TITLE}</title>{CSS}</head><body>{body}</body></html>"
tmp = PDF + ".html"
with open(tmp, "w", encoding="utf-8") as f: f.write(html)
cmd = ["wkhtmltopdf", "--enable-local-file-access", "--encoding", "utf-8", "--page-size", "A4", "--margin-top", "15mm", "--margin-bottom", "15mm", "--margin-left", "12mm", "--margin-right", "12mm", "--footer-center", "[page]/[topage]", "--footer-font-size", "8", tmp, PDF]
r = subprocess.run(cmd, capture_output=True, text=True)
os.remove(tmp)
if r.returncode != 0: print(f"ERROR: {r.stderr[:2000]}"); sys.exit(1)
print(f"OK: {PDF} ({os.path.getsize(PDF)} bytes)")