#!/usr/bin/env python3
"""Generate M2C.4 Comprehensive Reality Report PDF."""
import pdfkit
from markdown_it import MarkdownIt
import os, glob

BASE = "/home/shunya-deploy/shunya_os"

# Read all report files
files = {
    "Zero-Gap Register (Expanded)": "SHUNYA_ZERO_GAP_REGISTER_EXPANDED.md",
    "User Outcome Matrix": "SHUNYA_USER_OUTCOME_MATRIX.md",
    "Evidence Index": "SHUNYA_EVIDENCE_INDEX.md",
}

def md_to_html(filepath):
    with open(filepath) as f:
        text = f.read()
    md = MarkdownIt()
    return md.render(text)

html_parts = []
html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SHUNYA M2C.4 — Comprehensive Reality Report</title>
<style>
  @page { size: A4; margin: 20mm 15mm; }
  body { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 10pt; line-height: 1.6; color: #1a1c1d; }
  h1 { font-size: 20pt; font-weight: 700; color: #1a1c1d; border-bottom: 3px solid #a4865f; padding-bottom: 8px; margin-top: 30px; }
  h2 { font-size: 15pt; font-weight: 600; color: #2c2e2f; margin-top: 24px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
  h3 { font-size: 12pt; font-weight: 600; color: #3c3e3f; margin-top: 18px; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 8.5pt; }
  th { background: #1a1c1d; color: #fff; padding: 6px 8px; text-align: left; font-weight: 600; }
  td { padding: 4px 8px; border-bottom: 1px solid #eee; vertical-align: top; }
  tr:nth-child(even) { background: #f9f8f6; }
  code { background: #f0efec; padding: 1px 4px; border-radius: 3px; font-size: 8.5pt; }
  pre { background: #f5f4f1; padding: 10px; border-radius: 6px; font-size: 8pt; overflow-x: auto; }
  .verdict-g { color: #1a7d36; font-weight: 700; }
  .verdict-r { color: #c41e3a; font-weight: 700; }
  .verdict-a { color: #b8860b; font-weight: 700; }
  .summary-box { background: #f5f4f1; border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 12px 0; }
  .cover { text-align: center; padding: 80px 0; }
  .cover h1 { font-size: 28pt; border: none; }
  .cover h2 { font-size: 16pt; border: none; color: #6c6e6f; }
  .cover .meta { margin-top: 40px; font-size: 11pt; color: #6c6e6f; }
  .page-break { page-break-before: always; }
</style>
</head>
<body>
<div class="cover">
  <h1>SHUNYA M2C.4</h1>
  <h2>Comprehensive Reality Report</h2>
  <h2>Zero-Gap Register & Product Truth Audit</h2>
  <div class="meta">
    <p><strong>Date:</strong> 2026-08-29</p>
    <p><strong>Git SHA:</strong> 4208dad (main, clean, pushed)</p>
    <p><strong>Authority:</strong> Founder / Product Governance</p>
    <p><strong>Prepared by:</strong> Hermes Agent</p>
  </div>
</div>
""")

# Executive Summary
html_parts.append("""
<div class="page-break"></div>
<h1>Executive Summary</h1>

<div class="summary-box">
<h3>Product Reality: 11% GREEN, 42% RED</h3>
<p>SHUNYA's backend architecture spans 150+ database tables, 60+ route files, and a sophisticated 5-stage AI inference pipeline. However, only <strong>10 of 92</strong> audited capabilities (11%) work end-to-end for a real user. <strong>23 capabilities (25%) are broken or empty.</strong> The remaining capabilities are partial (15%), missing (6%), duplicate (3%), or unverified (6%).</p>

<h3>What Actually Works (GREEN — 10 items)</h3>
<ul>
<li>Public homepage — loads calmly, clear value proposition</li>
<li>Authentication — login/signup/session all functional</li>
<li>Onboarding — 6 paths + skip works cleanly</li>
<li>Content Studio — AI text generator with tone/length controls</li>
<li>Documents — 15 visible with extracted text</li>
<li>Document extraction — all backfilled with PDF/CSV/XLSX extraction</li>
<li>AI context retrieval — answers with Panchi Club knowledge, 5 evidence sources</li>
<li>Git state — main branch, clean tree, pushed to origin</li>
<li>Health endpoint — operational, returns build/DB/environment status</li>
<li>Session management — Secure, HttpOnly, SameSite cookies</li>
</ul>

<h3>Critical Failures (RED — 23 items)</h3>
<ul>
<li>Finance — 20 invoices in DB but 404 on API, no surface</li>
<li>Operations — page times out</li>
<li>People — 0 persons in database, empty surface</li>
<li>Sales — 6 leads in DB but empty UI</li>
<li>Conversations — empty surface</li>
<li>Memory — 0 records, empty surface</li>
<li>Relationships — 0 rows, just a heading</li>
<li>Entities — empty</li>
<li>Outputs — times out</li>
<li>Voice — 404 endpoint</li>
<li>Nginx SSL — certificate permission denied, no HTTPS</li>
<li>Knowledge — no longer crashes but empty (0 knowledge documents)</li>
<li>Customer — 0 customers despite full CRM schema</li>
<li>Proposals — 0 proposals</li>
<li>Test suite — 4,996 tests collected but full run times out (>120s)</li>
</ul>

<h3>M2C.3 Reassessment</h3>
<p>M2C.3 fixed 7 specific issues (Knowledge crash, ID leak, document visibility, extraction, tenant backfill, AI context, git state). These fixes are verified and retained. <strong>However, M2C.3's claim that "all P0/P1 issues were addressed" is rejected.</strong> The product still has 23 RED capabilities, and only 8 of 40 user outcomes work end-to-end. M2C.3 was a partial remediation, not a comprehensive closure.</p>
</div>
""")

# Row counts
html_parts.append("""
<div class="page-break"></div>
<h1>Database Row Counts — All Key Tables</h1>
<table>
<tr><th>Table</th><th>Rows</th><th>Status</th></tr>
<tr><td>team_members</td><td>5</td><td class="verdict-g">SEEDED</td></tr>
<tr><td>organizations</td><td>1</td><td class="verdict-g">ACTIVE (Panchi Club)</td></tr>
<tr><td>tenant</td><td>32</td><td class="verdict-a">DUPLICATE (multiple Panchi Club copies)</td></tr>
<tr><td>documents</td><td>15</td><td class="verdict-g">SEEDED + EXTRACTED</td></tr>
<tr><td>founder_objects</td><td>44</td><td class="verdict-g">SEEDED</td></tr>
<tr><td>objects</td><td>41</td><td class="verdict-a">DUPLICATE (competing with founder_objects)</td></tr>
<tr><td>canonical_objects</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>commitments</td><td>5</td><td class="verdict-g">SEEDED</td></tr>
<tr><td>leads</td><td>6</td><td class="verdict-g">SEEDED</td></tr>
<tr><td>fin_invoices</td><td>20</td><td class="verdict-g">SEEDED but NO API</td></tr>
<tr><td>fin_ledger</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>fin_payments</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>customer</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>persons</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>relationships</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>rel_relationships</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>memory_records</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>knowledge_documents</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
<tr><td>evidence_records</td><td>1</td><td class="verdict-r">MINIMAL</td></tr>
<tr><td>campaigns</td><td>5</td><td class="verdict-g">SEEDED</td></tr>
<tr><td>proposals</td><td>0</td><td class="verdict-r">EMPTY</td></tr>
</table>
""")

# Add each report
for title, filename in files.items():
    filepath = os.path.join(BASE, filename)
    if os.path.exists(filepath):
        html_parts.append(f'<div class="page-break"></div>\n<h1>{title}</h1>\n')
        html_parts.append(md_to_html(filepath))

# Summary
html_parts.append("""
<div class="page-break"></div>
<h1>Summary & Next Steps</h1>

<div class="summary-box">
<h3>Key Insight</h3>
<p>The pattern across all 90+ items is consistent: <strong>database architecture exists for 150+ tables, but only ~11% of promised user outcomes work end-to-end.</strong> The issue is not missing code — it is unwired data. Backend APIs exist, frontend components exist, but the connections between them are broken or absent for 42% of capabilities.</p>

<h3>What To Fix First</h3>
<ol>
<li><strong>Finance API + UI</strong> — 20 invoices sitting unused. Wire the existing fin_invoices table to a route and surface.</li>
<li><strong>People/Person</strong> — Create persons from existing team_members + seed data. Make the People surface useful.</li>
<li><strong>Sales Pipeline</strong> — Wire the 6 existing leads to the SalesPipeline component.</li>
<li><strong>Commitments → UI</strong> — Wire the 5 commitments to the CommitmentWorkspace.</li>
<li><strong>Memory pipeline</strong> — Implement memory recording from AI interactions and document ingestion.</li>
<li><strong>Voice endpoint</strong> — Add a truthful error state or implement the endpoint.</li>
<li><strong>Nginx SSL</strong> — Requires sudo for cert fix. Prerequisite for public launch.</li>
<li><strong>Mobile certification</strong> — Test and fix responsive layout at 390x844+.</li>
<li><strong>Test suite</strong> — Diagnose and fix the suite timeout (>120s for 4,996 tests).</li>
</ol>

<h3>Remaining Artifacts (In Progress)</h3>
<ul>
<li>FDA1-FDA36 Traceability Matrix — subagent running</li>
<li>Constitution Compliance Matrix — subagent running</li>
<li>Canonical Architecture Map + Data Lineage Map — subagent running</li>
</ul>

<h3>GOVERNANCE STATE</h3>
<p><strong>AWAITING FOUNDER REVIEW</strong></p>
<p>This report is the comprehensive reality baseline. No remediation has been started. The next step is founder review of this evidence, followed by an implementation directive.</p>
</div>

<p style="text-align:center; color:#6c6e6f; margin-top:40px;">
SHUNYA M2C.4 — Comprehensive Reality Report<br>
Generated 2026-08-29 | Git SHA 4208dad<br>
Prepared by Hermes Agent for Founder Governance Review
</p>
</body></html>
""")

# Write HTML
html_path = os.path.join(BASE, "audit", "M2C4_REALITY_REPORT.html")
os.makedirs(os.path.join(BASE, "audit"), exist_ok=True)
with open(html_path, "w") as f:
    f.write("\n".join(html_parts))
print(f"HTML written: {html_path}")

# Generate PDF
pdf_path = os.path.join(BASE, "audit", "M2C4_REALITY_REPORT.pdf")
options = {
    'page-size': 'A4',
    'margin-top': '15mm',
    'margin-right': '12mm',
    'margin-bottom': '20mm',
    'margin-left': '12mm',
    'encoding': 'UTF-8',
    'no-outline': None,
    'enable-local-file-access': None,
}
pdfkit.from_file(html_path, pdf_path, options=options)
print(f"PDF generated: {pdf_path}")
print(f"Size: {os.path.getsize(pdf_path)} bytes")