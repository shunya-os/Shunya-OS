#!/usr/bin/env python3
"""Generate publication-quality PDF of the SHUNYA Constitution v1.0."""

import pdfkit
from markdown_it import MarkdownIt
import os

CONST_DIR = "/home/shunya-deploy/constitution"

VOLUMES = [
    ("Volume I — First Principles", "FIRST_PRINCIPLES.md"),
    ("Volume II — SHUNYA Constitution", "SHUNYA_CONSTITUTION.md"),
    ("Volume III — Canonical Definitions", "CANONICAL_DEFINITIONS.md"),
    ("Volume IV — Constitutional Compliance", "CONSTITUTIONAL_COMPLIANCE.md"),
    ("Volume V — Hermes Implementation Charter", "HERMES_IMPLEMENTATION_CHARTER.md"),
]

def md_to_html(filepath):
    with open(filepath) as f:
        text = f.read()
    md = MarkdownIt()
    return md.render(text)

# Build complete HTML
html_parts = []
html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SHUNYA Constitution v1.0</title>
<style>
    @page {{
        size: A4;
        margin: 2.5cm 2cm 2.5cm 2cm;
        @top-center {{
            content: "SHUNYA Constitution v1.0";
            font-family: 'Georgia', serif;
            font-size: 9pt;
            color: #666;
        }}
        @bottom-center {{
            content: "Page " counter(page) " of " counter(pages);
            font-family: 'Georgia', serif;
            font-size: 9pt;
            color: #666;
        }}
    }}
    body {{
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #1a1c1d;
        counter-reset: h1-counter;
    }}
    /* Title page */
    .title-page {{
        text-align: center;
        padding-top: 4cm;
        page-break-after: always;
    }}
    .title-page h1 {{
        font-size: 28pt;
        font-weight: bold;
        margin-bottom: 0.5cm;
        letter-spacing: 2px;
        text-transform: uppercase;
    }}
    .title-page .subtitle {{
        font-size: 16pt;
        color: #a4865f;
        margin-bottom: 3cm;
        font-style: italic;
    }}
    .title-page .meta {{
        font-size: 10pt;
        color: #666;
        line-height: 2;
    }}
    .title-page .divider {{
        width: 40%;
        border: none;
        border-top: 1px solid #a4865f;
        margin: 1.5cm auto;
    }}
    /* Volume headers */
    .volume-header {{
        page-break-before: always;
        text-align: center;
        padding-top: 3cm;
        padding-bottom: 1.5cm;
    }}
    .volume-header h2 {{
        font-size: 22pt;
        font-weight: bold;
        letter-spacing: 1px;
        color: #1a1c1d;
    }}
    .volume-header .volume-status {{
        font-size: 10pt;
        color: #666;
        margin-top: 0.5cm;
    }}
    /* Headings */
    h1 {{
        font-size: 18pt;
        font-weight: bold;
        margin-top: 1.5cm;
        margin-bottom: 0.5cm;
        page-break-after: avoid;
        border-bottom: 1px solid #ddd;
        padding-bottom: 0.3cm;
    }}
    h2 {{
        font-size: 14pt;
        font-weight: bold;
        margin-top: 1cm;
        margin-bottom: 0.4cm;
        page-break-after: avoid;
        color: #333;
    }}
    h3 {{
        font-size: 12pt;
        font-weight: bold;
        margin-top: 0.8cm;
        margin-bottom: 0.3cm;
        color: #444;
    }}
    h4 {{
        font-size: 11pt;
        font-weight: bold;
        font-style: italic;
        margin-top: 0.5cm;
        margin-bottom: 0.2cm;
    }}
    /* Tables */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 0.5cm 0;
        font-size: 10pt;
    }}
    th {{
        background-color: #f5f3f0;
        border: 1px solid #ccc;
        padding: 6px 8px;
        text-align: left;
        font-weight: bold;
    }}
    td {{
        border: 1px solid #ccc;
        padding: 6px 8px;
    }}
    tr:nth-child(even) {{
        background-color: #fafaf8;
    }}
    /* Code blocks */
    pre {{
        background-color: #f5f3f0;
        border: 1px solid #ddd;
        border-left: 3px solid #a4865f;
        padding: 10px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 9pt;
        overflow-x: auto;
        margin: 0.5cm 0;
    }}
    code {{
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 9pt;
        background-color: #f5f3f0;
        padding: 1px 3px;
    }}
    pre code {{
        background: none;
        padding: 0;
    }}
    /* Blockquotes */
    blockquote {{
        border-left: 3px solid #a4865f;
        margin: 0.5cm 0;
        padding: 0.3cm 0.8cm;
        background-color: #fafaf8;
        font-style: italic;
        color: #555;
    }}
    /* Lists */
    ul, ol {{
        margin: 0.3cm 0;
        padding-left: 1cm;
    }}
    li {{
        margin-bottom: 0.15cm;
    }}
    /* Horizontal rules */
    hr {{
        border: none;
        border-top: 1px solid #ccc;
        margin: 1cm 0;
    }}
    /* Paragraphs */
    p {{
        margin: 0.3cm 0;
        text-align: justify;
    }}
    /* Links */
    a {{
        color: #1a73e8;
        text-decoration: none;
    }}
    a:hover {{
        text-decoration: underline;
    }}
    /* TOC */
    .toc {{
        page-break-after: always;
    }}
    .toc h1 {{
        text-align: center;
        border: none;
        font-size: 20pt;
    }}
    .toc ul {{
        list-style: none;
        padding-left: 0;
    }}
    .toc li {{
        margin: 0.2cm 0;
        font-size: 11pt;
    }}
    .toc .toc-volume {{
        font-weight: bold;
        font-size: 12pt;
        margin-top: 0.4cm;
    }}
    .section-divider {{
        page-break-before: always;
    }}
    /* Footer */
    .footer-note {{
        text-align: center;
        font-size: 9pt;
        color: #999;
        margin-top: 2cm;
        border-top: 1px solid #ddd;
        padding-top: 0.5cm;
    }}
</style>
</head>
<body>
""")

# Title page
html_parts.append("""
<div class="title-page">
    <h1>SHUNYA Constitution</h1>
    <div class="subtitle">The Supreme Governing Document</div>
    <hr class="divider">
    <div class="meta">
        <strong>Version 1.0</strong><br>
        Status: Candidate for Founder Review<br>
        Date: 2026-07-28<br>
        <br>
        <em>Constitutional Editorial Team</em><br>
        Hermes Agent · Nous Research
    </div>
    <hr class="divider">
    <div class="meta" style="font-size:9pt; font-style:italic;">
        "A constitution is not a description of what exists.<br>
        It is a declaration of what shall be true regardless of what exists."<br>
        <br>
        <span style="font-size:8pt;">— Volume I, First Principles, Preamble</span>
    </div>
</div>
""")

# Table of Contents
html_parts.append("""
<div class="toc">
<h1>Table of Contents</h1>
<ul>
    <li class="toc-volume">Volume I — First Principles</li>
    <li>Preamble</li>
    <li>Principle I: Primacy of Human Purpose</li>
    <li>Principle II: Sovereignty of Reality</li>
    <li>Principle III: Necessity of Intelligence</li>
    <li>Principle IV: Inviolability of Identity</li>
    <li>Principle V: Architecture of Principle</li>
    <li>Principle VI: Unity of Representation</li>
    <li>Principle VII: Discipline of Execution</li>
    <li>Principle VIII: Primacy of Governance</li>
    <li>Principle IX: Permanence of Memory</li>
    <li>Principle X: Partnership of Human and Machine</li>
    <li>Principle XI: Discipline of Words</li>
    <li>Principle XII: Endurance of Design</li>
    <li>Appendix A: Principles Summary Table</li>
    <li>Appendix B: Derivative Authority</li>
    <br>
    <li class="toc-volume">Volume II — SHUNYA Constitution</li>
    <li>Preamble</li>
    <li>Article I: Purpose</li>
    <li>Article II: Reality</li>
    <li>Article III: Intelligence</li>
    <li>Article IV: Identity</li>
    <li>Article V: Canonical Architecture</li>
    <li>Article VI: Universal Representation</li>
    <li>Article VII: Execution</li>
    <li>Article VIII: Evolution</li>
    <li>Article IX: Governance</li>
    <li>Appendix A: Constitutional Guarantees Index</li>
    <li>Appendix B: Cross-Reference Index</li>
    <br>
    <li class="toc-volume">Volume III — Canonical Definitions</li>
    <li>Part I: Constitutional Concepts (§§1–30)</li>
    <li>Part II: Canonical Glossary</li>
    <li>Part III: Mapping to Other Volumes</li>
    <li>Appendix: Definition Invariants</li>
    <br>
    <li class="toc-volume">Volume IV — Constitutional Compliance</li>
    <li>Article I: Compliance Rules</li>
    <li>Article II: Classification of Violations</li>
    <li>Article III: Audit Process</li>
    <li>Article IV: Constitutional Amendment Procedure</li>
    <li>Article V: Constitutional Precedence</li>
    <li>Article VI: Conflict Resolution</li>
    <br>
    <li class="toc-volume">Volume V — Hermes Implementation Charter</li>
    <li>Article I: Constitutional Derivation</li>
    <li>Article II: Obligations of Implementation</li>
    <li>Article III: Implementation Workflow</li>
    <li>Article IV: Constitutional Compliance in Implementation</li>
    <li>Article V: Constitutional Archive and History</li>
    <li>Article VI: Implementation Boundaries</li>
    <li>Article VII: Verification and Review</li>
    <li>Article VIII: Implementation and Canonical Definitions</li>
    <li>Article IX: The Constitutional Relationship</li>
</ul>
</div>
""")

# Each volume
for title, filename in VOLUMES:
    filepath = os.path.join(CONST_DIR, filename)
    html = md_to_html(filepath)
    html_parts.append(f'<div class="section-divider"><div class="volume-header"><h2>{title}</h2><div class="volume-status">SHUNYA Constitution v1.0</div></div></div>')
    # Modify h1 tags to not be title-page style
    html = html.replace('<h1>', '<h1>')
    html_parts.append(html)

html_parts.append("""
<div class="section-divider" style="text-align:center; padding-top:4cm;">
    <hr style="width:40%; border-top:1px solid #a4865f;">
    <p style="font-size:10pt; color:#666; margin-top:1cm;">
        End of the SHUNYA Constitution — Version 1.0<br>
        <em>Candidate for Founder Review</em>
    </p>
    <p style="font-size:8pt; color:#999; margin-top:2cm;">
        Constitutional Editorial Team · Hermes Agent · Nous Research<br>
        2026-07-28
    </p>
</div>
""")

html_parts.append("</body></html>")

complete_html = "\n".join(html_parts)

# Write HTML
html_path = os.path.join(CONST_DIR, "SHUNYA_CONSTITUTION_v1.0.html")
with open(html_path, "w") as f:
    f.write(complete_html)

# Generate PDF
pdf_path = os.path.join(CONST_DIR, "SHUNYA_CONSTITUTION_v1.0.pdf")
options = {
    'page-size': 'A4',
    'margin-top': '25mm',
    'margin-right': '20mm',
    'margin-bottom': '25mm',
    'margin-left': '20mm',
    'encoding': 'UTF-8',
    'no-outline': None,
    'enable-local-file-access': None,
}

pdfkit.from_file(html_path, pdf_path, options=options)

# Report
import os as os2
pdf_size = os2.path.getsize(pdf_path)
html_size = os2.path.getsize(html_path)

print(f"PDF generated: {pdf_path}")
print(f"PDF size: {pdf_size:,} bytes ({pdf_size/1024:.0f} KB)")
print(f"HTML size: {html_size:,} bytes ({html_size/1024:.0f} KB)")

# Count lines across all volumes
total_lines = 0
for _, filename in VOLUMES:
    with open(os.path.join(CONST_DIR, filename)) as f:
        total_lines += len(f.readlines())
print(f"Total lines across all volumes: {total_lines}")