"""Generate Combined System Consolidation + GitHub Audit PDF Report."""
import os
import json
from datetime import datetime, timezone
from html import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable,
    Table, TableStyle, KeepTogether,
)

OUTPUT = "/home/shunya-deploy/shunya_os/SHUNYA_OS_CONSOLIDATION_AUDIT.pdf"

# ── Colors ──
PURPLE = HexColor("#6C4AE2")
GOLD = HexColor("#A4865F")
TEXT_DARK = HexColor("#1A1C1D")
TEXT_MUTED = HexColor("#6B7280")
MID_GRAY = HexColor("#D0CCC4")
LIGHT_GRAY = HexColor("#F0EDE8")
BAND_DARK = HexColor("#1E1B4B")
RED = HexColor("#DC2626")
GREEN = HexColor("#059669")
YELLOW = HexColor("#D97706")

styles = getSampleStyleSheet()

def mk(name, **kw):
    if name in styles:
        return styles[name]
    p = ParagraphStyle(name, parent=styles["Normal"], **kw)
    styles.add(p)
    return p

sty_CoverTitle = mk("sty_CoverTitle", fontName="Helvetica-Bold", fontSize=28,
    textColor=white, alignment=TA_CENTER, leading=34, spaceAfter=6)
sty_CoverSub = mk("sty_CoverSub", fontName="Helvetica", fontSize=13,
    textColor=HexColor("#C4B5FD"), alignment=TA_CENTER, leading=18, spaceAfter=4)
sty_Section = mk("sty_Section", fontName="Helvetica-Bold", fontSize=16,
    textColor=PURPLE, spaceBefore=16, spaceAfter=8, leading=20)
sty_SubSection = mk("sty_SubSection", fontName="Helvetica-Bold", fontSize=12,
    textColor=BAND_DARK, spaceBefore=10, spaceAfter=4, leading=15)
sty_Body = mk("sty_Body", fontName="Helvetica", fontSize=9.5,
    textColor=TEXT_DARK, leading=13, spaceBefore=2, spaceAfter=5, alignment=TA_JUSTIFY)
sty_Bold = mk("sty_Bold", fontName="Helvetica-Bold", fontSize=9.5,
    textColor=TEXT_DARK, leading=13, spaceBefore=2, spaceAfter=2)
sty_Metric = mk("sty_Metric", fontName="Helvetica-Bold", fontSize=22,
    textColor=PURPLE, alignment=TA_CENTER, leading=26)
sty_MetricLabel = mk("sty_MetricLabel", fontName="Helvetica", fontSize=8,
    textColor=TEXT_MUTED, alignment=TA_CENTER, leading=10)
sty_Code = mk("sty_Code", fontName="Courier", fontSize=7,
    textColor=TEXT_DARK, leading=9, spaceBefore=0.5, spaceAfter=0.5)
sty_Learn = mk("sty_Learn", fontName="Helvetica-Bold", fontSize=11,
    textColor=BAND_DARK, leading=15, spaceBefore=6, spaceAfter=3)
sty_Bullet = mk("sty_Bullet", fontName="Helvetica", fontSize=9,
    textColor=TEXT_DARK, leading=12, spaceBefore=1, spaceAfter=2,
    leftIndent=12, bulletIndent=0)
sty_RiskRed = mk("sty_RiskRed", fontName="Helvetica-Bold", fontSize=8.5,
    textColor=RED, leading=11, spaceBefore=1, spaceAfter=2)
sty_RiskYel = mk("sty_RiskYel", fontName="Helvetica-Bold", fontSize=8.5,
    textColor=YELLOW, leading=11, spaceBefore=1, spaceAfter=2)
sty_RiskGrn = mk("sty_RiskGrn", fontName="Helvetica-Bold", fontSize=8.5,
    textColor=GREEN, leading=11, spaceBefore=1, spaceAfter=2)

# ── Read all audit files from disk ──
AUDIT_DIR = "/home/shunya-deploy/audit_dump"
files_order = [
    "loop.py", "decision_engine.py", "entity.py",
    "processor.py", "generator.py", "timeline.py",
    "entity_routes.py", "webhook_routes.py",
]
files_content = {}
for fname in files_order:
    path = os.path.join(AUDIT_DIR, fname)
    with open(path) as f:
        files_content[fname] = f.read()

# ── Page callbacks ──
def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PURPLE)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, A4[1] - 6*mm, A4[0], 6*mm, fill=1, stroke=0)
    canvas.rect(0, 0, A4[0], 2*mm, fill=1, stroke=0)
    canvas.restoreState()

def normal_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PURPLE)
    canvas.rect(0, A4[1] - 4*mm, A4[0], 4*mm, fill=1, stroke=0)
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(20*mm, 10*mm, "SHUNYA OS — Consolidation & GitHub Audit")
    canvas.drawRightString(A4[0] - 20*mm, 10*mm, f"Page {doc.page}")
    canvas.restoreState()

# ── Helper: metric cards ──
def metric_row(cards):
    """cards = [(value, label), ...]"""
    data = [[Paragraph(c[0], sty_Metric) for c in cards],
            [Paragraph(c[1], sty_MetricLabel) for c in cards]]
    t = Table(data, colWidths=[(A4[0] - 36*mm) // len(cards)] * len(cards))
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FAF8F5")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t

# ── Helper: risk table ──
def risk_table(rows):
    """rows = [(severity, item, impact)]"""
    data = [["Severity", "Issue", "Impact"]] + rows
    col_w = [20*mm, 60*mm, 95*mm]
    t = Table(data, colWidths=col_w, repeatRows=1)
    s = [
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        bg = LIGHT_GRAY if i % 2 == 0 else white
        s.append(("BACKGROUND", (0, i), (-1, i), bg))
    t.setStyle(TableStyle(s))
    return t

# ══════════════════════════════════════════════════
# BUILD STORY
# ══════════════════════════════════════════════════
story = []

# ── COVER ──
story.append(Spacer(1, 60*mm))
story.append(Paragraph("SHUNYA OS", sty_CoverTitle))
story.append(Spacer(1, 4*mm))
story.append(Paragraph("SYSTEM CONSOLIDATION & GITHUB AUDIT", sty_CoverSub))
story.append(Spacer(1, 2*mm))
story.append(Paragraph("Complete Repository Analysis", sty_CoverSub))
story.append(Spacer(1, 10*mm))
story.append(HRFlowable(width="60%", thickness=1, color=GOLD, spaceAfter=8))
story.append(Spacer(1, 8*mm))
story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", sty_CoverSub))
story.append(Paragraph("Commit: 49e7e82 - BATCH-09-10", sty_CoverSub))
story.append(Paragraph("Confidential — SHUNYA Internal", sty_CoverSub))
story.append(PageBreak())

# ── SECTION 1: EXECUTIVE SUMMARY ──
story.append(Paragraph("1. Executive Summary", sty_Section))
story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=6))
story.append(Paragraph(
    "This consolidated report combines the System Alignment Audit (architecture files) "
    "with the Full GitHub Repository Audit. It provides a complete picture of the SHUNYA OS "
    "codebase across 122 commits, 10 branches, and approximately 60 MB of source code spanning "
    "Python backend, TypeScript/React frontend, and infrastructure.",
    sty_Body
))
story.append(Spacer(1, 4*mm))

story.append(metric_row([
    ("122", "Total Commits"),
    ("1,569", "Files"),
    ("60 MB", "Repo Size"),
    ("10", "Branches"),
    ("15", "Green CI Runs"),
    ("0", "Open Issues"),
]))
story.append(Spacer(1, 4*mm))

# Quick stats table
stats_data = [
    ["Metric", "Value", "Metric", "Value"],
    ["Repository", "shunya-os/Shunya-OS", "Created", "2026-07-12"],
    ["Default Branch", "master", "Active Branch", "master"],
    ["Master Commits", "122", "Main Commits (diverged)", "4 unique"],
    ["Primary Language", "Python (9.1 MB)", "Frontend", "TypeScript + React (584 MB)"],
    ["CI Status", "✅ Last 15 runs green", "License", "None"],
    ["Branch Protection", "None", "Releases", "0 (5 tags)"],
    ["Contributors", "2 (nish, nishesh)", "Stars/Forks", "0 / 0"],
]
t = Table(stats_data, colWidths=[55*mm, 65*mm, 55*mm, 65*mm], repeatRows=1)
ts = [
    ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
    ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
]
for i in range(1, len(stats_data)):
    bg = LIGHT_GRAY if i % 2 == 0 else white
    ts.append(("BACKGROUND", (0, i), (-1, i), bg))
t.setStyle(TableStyle(ts))
story.append(t)
story.append(PageBreak())

# ── SECTION 2: GIT STATE & BRANCH TOPOLOGY ──
story.append(Paragraph("2. Git State & Branch Topology", sty_Section))
story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=6))

story.append(Paragraph("2.1 Branch Inventory", sty_SubSection))
branch_data = [
    ["Branch", "Last SHA", "Protected", "Status"],
    ["master", "49e7e82", "No", "Active — 23 PROD/BATCH commits"],
    ["main", "920882a", "No", "Stale — 4 FEP commits, diverged"],
    ["docs", "f200828", "No", "Dormant"],
    ["feature/alpha-001a-gmail-oauth", "39de5b1", "No", "Incomplete"],
    ["feature/alpha-001b-gmail-sync", "fe0f0a8", "No", "Incomplete"],
    ["feature/alpha-001c-document-import", "5f153c6", "No", "Incomplete"],
    ["feature/alpha-001j-workflow", "f42eb27", "No", "Incomplete"],
    ["feature/alpha-002a-universal-crm", "bed8ea2", "No", "Incomplete"],
    ["feature/alpha-003a-dashboard", "a78c948", "No", "Incomplete"],
    ["legacy/panchi-backend", "0f3977b", "No", "Archived"],
]
t = Table(branch_data, colWidths=[55*mm, 22*mm, 20*mm, 78*mm], repeatRows=1)
ts2 = [
    ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
    ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 7),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ("LEFTPADDING", (0, 0), (-1, -1), 3),
]
for i in range(1, len(branch_data)):
    ts2.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY if i % 2 == 0 else white))
t.setStyle(TableStyle(ts2))
story.append(t)
story.append(Spacer(1, 4*mm))

story.append(Paragraph("2.2 master ↔ main Divergence", sty_SubSection))
story.append(Paragraph(
    "The two primary branches (master and main) have structurally diverged. "
    "master contains 23 PROD batch commits (the complete intelligence pipeline from PROD-04 through BATCH-09-10). "
    "main contains 4 FEP-cycle commits (Founder Experience Platform fixes including org creation, API client, "
    "and founder signup fixes). The diff spans 734 files with 47,323 insertions and 109,916 deletions — "
    "indicating structural reorganization rather than simple conflict.",
    sty_Body
))
story.append(Spacer(1, 2*mm))
story.append(Paragraph(
    "Key observation: main appears to have been a cleanup/reorganization pass "
    "(removed 110K lines), while master has been the active development trunk building "
    "the runtime layer. These need reconciliation.",
    sty_Body
))
story.append(PageBreak())

# ── SECTION 3: ARCHITECTURE FILE AUDIT ──
story.append(Paragraph("3. Architecture File Analysis", sty_Section))
story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=6))

story.append(Paragraph("3.1 Core Runtime Files", sty_SubSection))

core_files = [
    ["File", "Lines", "Role", "Key Function(s)"],
    ["loop.py", "189", "Autonomous execution engine", "run_cycle(), run_loop()"],
    ["decision_engine.py", "239", "Pure intelligence layer", "get_next_action(), decide_lead_stage(), decide_entity()"],
    ["entity.py", "14", "Generic Entity abstraction", "Entity(db.Model)"],
    ["timeline.py", "33", "Unified entity history", "get_entity_timeline()"],
    ["generator.py", "12", "Structured output", "generate_output()"],
    ["processor.py", "24", "Inbound→Message pipeline", "process_inbound()"],
    ["delivery.py", "11", "Message delivery", "deliver_messages()"],
    ["entity_routes.py", "29", "REST entity API", "list, get, timeline endpoints"],
    ["webhook_routes.py", "19", "Ingestion endpoint", "POST /api/v1/webhook/"],
]
t = Table(core_files, colWidths=[35*mm, 16*mm, 55*mm, 65*mm], repeatRows=1)
ts3 = [
    ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
    ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 7),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ("LEFTPADDING", (0, 0), (-1, -1), 3),
]
for i in range(1, len(core_files)):
    ts3.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY if i % 2 == 0 else white))
t.setStyle(TableStyle(ts3))
story.append(t)
story.append(Spacer(1, 4*mm))

story.append(Paragraph("3.2 Communication Layer (15 files, 1,748 lines)", sty_SubSection))
comm_files = [
    ["models.py (297 loc)", "Message, ExternalMessage, CommunicationSource, OAuthState"],
    ["runtime.py (214 loc)", "Communication runtime orchestration"],
    ["adapters.py (168 loc)", "Provider adapters"],
    ["adapter.py (94 loc)", "Base adapter class"],
    ["policy.py (157 loc)", "Capture policy models"],
    ["conversation.py (154 loc)", "Conversation management"],
    ["normalizer.py (143 loc)", "Message normalization"],
    ["routes.py (130 loc)", "Communication API routes"],
    ["oauth.py (258 loc)", "OAuth flow management"],
]
for name, desc in comm_files:
    story.append(Paragraph(f"<b>{name}</b> — {desc}", sty_Bullet))
story.append(PageBreak())

# ── SECTION 4: GITHUB METADATA ──
story.append(Paragraph("4. GitHub Metadata & Health", sty_Section))
story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=6))

story.append(Paragraph("4.1 CI/CD Pipeline", sty_SubSection))
story.append(Paragraph(
    "Two GitHub Actions workflows: CI (ci.yml) and Dependency Graph. "
    "The CI pipeline is healthy — the last 15 runs on master all completed with success. "
    "Only 3 historical failures exist, all from the DOC-01 / PROD-99 era before the batch pipeline stabilized.",
    sty_Body
))
story.append(Spacer(1, 3*mm))

story.append(Paragraph("4.2 Tags & Releases", sty_SubSection))
tag_data = [
    ["Tag", "SHA", "Significance"],
    ["v0.11.0", "74f8374", "Latest version tag"],
    ["v0.1.0-production", "d49dc5b", "First production tag"],
    ["v0.1-runtime-stable", "f97cfa5", "Runtime stability milestone"],
    ["founder-ready-pre-alpha", "64c0cc3", "Pre-alpha FEP milestone"],
    ["canon-v1.0.0", "1e58690", "Canonical architecture spec"],
]
t = Table(tag_data, colWidths=[50*mm, 25*mm, 100*mm], repeatRows=1)
ts4 = [
    ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
    ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
]
for i in range(1, len(tag_data)):
    ts4.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY if i % 2 == 0 else white))
t.setStyle(TableStyle(ts4))
story.append(t)
story.append(Spacer(1, 3*mm))
story.append(Paragraph(
    "<b>Note:</b> 5 tags exist but 0 formal GitHub Releases. Tags are raw git pointers — no release notes, "
    "no binary assets, no release artifacts. This means the project has never formally shipped.",
    sty_Body
))

story.append(Spacer(1, 4*mm))
story.append(Paragraph("4.3 Risk & Gap Assessment", sty_SubSection))
story.append(risk_table([
    (Paragraph("🔴 HIGH", sty_RiskRed), "No branch protection on master", "Direct pushes bypass code review"),
    (Paragraph("🔴 HIGH", sty_RiskRed), "No license file", "Legal ambiguity — no one can use or contribute"),
    (Paragraph("🟡 MEDIUM", sty_RiskYel), "master ↔ main divergence (734 files)", "Merge conflicts, lost work risk"),
    (Paragraph("🟡 MEDIUM", sty_RiskYel), "Frontend 584 MB vs backend 18 MB", "10x imbalance; possible bloat"),
    (Paragraph("🟡 MEDIUM", sty_RiskYel), "0 formal GitHub Releases", "No shipped milestones despite 5 tags"),
    (Paragraph("🟢 LOW", sty_RiskGrn), "No open issues or PRs", "Clean slate but no tracked work"),
    (Paragraph("🟢 LOW", sty_RiskGrn), "No topics set", "Poor discoverability on GitHub"),
    (Paragraph("🟢 LOW", sty_RiskGrn), "6 dormant alpha feature branches", "Orphaned work, integration burden"),
]))
story.append(PageBreak())

# ── SECTION 5: KEY LEARNINGS ──
story.append(Paragraph("5. Key Learnings & Patterns", sty_Section))
story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=6))

story.append(Paragraph("5.1 Where We Are on the SHUNYA OS Project", sty_SubSection))
story.append(Paragraph(
    "SHUNYA OS has been under active development for approximately 27 days. The project has delivered:",
    sty_Body
))
story.append(Paragraph("A complete intelligence runtime — Object System → Decision Engine → Execution Loop → "
    "Commitments → Observations → Lead Lifecycle → Productization Layer.", sty_Bullet))
story.append(Paragraph("An entity abstraction layer with generic Entity model and REST API.", sty_Bullet))
story.append(Paragraph("A communication layer with Message model, inbound processing, webhook ingestion, "
    "and delivery pipeline.", sty_Bullet))
story.append(Paragraph("CI/CD pipeline with 15 consecutive green builds.", sty_Bullet))
story.append(Paragraph("Frontend (TypeScript/React) infrastructure at 584 MB.", sty_Bullet))
story.append(Spacer(1, 4*mm))

story.append(Paragraph("5.2 What Needs to Be Done to Complete the Project", sty_SubSection))
story.append(Paragraph("<b>Immediate (must fix before continuing):</b>", sty_Learn))
story.append(Paragraph("Resolve master ↔ main branch divergence — merge or rebase", sty_Bullet))
story.append(Paragraph("Add branch protection to master (require PRs + passing CI)", sty_Bullet))
story.append(Paragraph("Add a license file (MIT or proprietary)", sty_Bullet))
story.append(Paragraph("Create a formal GitHub Release from the latest green commit", sty_Bullet))
story.append(Spacer(1, 2*mm))

story.append(Paragraph("<b>Short-term (next batches):</b>", sty_Learn))
story.append(Paragraph("Connect the communication layer to real APIs (WhatsApp, Email)", sty_Bullet))
story.append(Paragraph("Implement the message delivery pipeline end-to-end", sty_Bullet))
story.append(Paragraph("Add entity-to-entity linking in the execution loop", sty_Bullet))
story.append(Paragraph("Clean up or archive dormant alpha feature branches", sty_Bullet))
story.append(Paragraph("Reduce frontend bundle size or audit for dead code", sty_Bullet))
story.append(Spacer(1, 2*mm))

story.append(Paragraph("<b>Medium-term:</b>", sty_Learn))
story.append(Paragraph("Implement user authentication and multi-tenancy", sty_Bullet))
story.append(Paragraph("Build the workspace runtime for end-user interaction", sty_Bullet))
story.append(Paragraph("Add monitoring, observability, and production logging", sty_Bullet))
story.append(Paragraph("Set up staging/production deployment pipeline", sty_Bullet))
story.append(Spacer(1, 4*mm))

story.append(Paragraph("5.3 What Needs to Be Fixed", sty_SubSection))
story.append(risk_table([
    (Paragraph("🔴", sty_RiskRed), "Branch divergence", "master and main must converge before further work"),
    (Paragraph("🔴", sty_RiskRed), "No license", "Legal blocker for any external use or contribution"),
    (Paragraph("🟡", sty_RiskYel), "No branch protection", "Single-actor workflow accepted but risk grows"),
    (Paragraph("🟡", sty_RiskYel), "Zero open issues/PRs", "No work tracking — everything in conversation memory"),
    (Paragraph("🟡", sty_RiskYel), "Frontend bloat (584 MB)", "vs 18 MB backend — investigate"),
    (Paragraph("🟡", sty_RiskYel), "6 orphaned alpha branches", "Either integrate or archive"),
    (Paragraph("🟢", sty_RiskGrn), "No topics on repo", "Easy fix for discoverability"),
]))
story.append(PageBreak())

# ── SECTION 6: THE LOOP ANALYSIS ──
story.append(Paragraph("6. Pattern Analysis: Are We in a Rebuild Loop?", sty_Section))
story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=6))

story.append(Paragraph("6.1 Evidence of Parallel Workstreams", sty_SubSection))
story.append(Paragraph(
    "The repository shows clear evidence of <b>two parallel development streams</b> that never converged:",
    sty_Body
))
story.append(Paragraph(
    "<b>Stream A (master):</b> The PROD batch pipeline — a systematic, bottom-up build of the intelligence stack "
    "(Object System → Decision Engine → Loop → Commitments → Observations → Leads → Productization). "
    "This stream is well-structured, sequentially ordered, and produces green CI.",
    sty_Body
))
story.append(Paragraph(
    "<b>Stream B (main — FEP Cycle):</b> The Founder Experience Platform — a top-down UX/build focused on "
    "founder signup, authentication, workspace rendering, and frontend integration. "
    "This stream was reorganized (110K lines removed) and had bug fixes that master doesn't have.",
    sty_Body
))
story.append(Spacer(1, 3*mm))

story.append(Paragraph("6.2 The Pattern That Concerns Me", sty_SubSection))
story.append(Paragraph(
    "The evidence suggests a <b>fork-and-replace pattern</b> rather than iterative convergence:",
    sty_Body
))
story.append(Paragraph(
    "1. <b>main was reorganized aggressively</b> — 110K lines removed, suggesting a belief that the codebase "
    "needed cleanup rather than extension. This is often a symptom of architecture dissatisfaction.",
    sty_Bullet))
story.append(Paragraph(
    "2. <b>master built the runtime independently</b> — 23 commits of pure runtime construction. "
    "The FEP fixes on main (org creation, auth) were never ported to master.",
    sty_Bullet))
story.append(Paragraph(
    "3. <b>6 alpha feature branches are dormant</b> — each represents a feature that was started but "
    "either never finished or never integrated. This indicates feature-scope creep.",
    sty_Bullet))
story.append(Paragraph(
    "4. <b>0 formal releases despite 5 tags</b> — work is being done and tagged but never shipped. "
    "The project accumulates without publishing.",
    sty_Bullet))
story.append(Paragraph(
    "5. <b>584 MB frontend</b> — the frontend is 32x the backend size. This is unusually large for a "
    "React/TypeScript project and may contain multiple generations of frontend builds.",
    sty_Bullet))
story.append(Spacer(1, 3*mm))

story.append(Paragraph("6.3 Are We Stuck?", sty_SubSection))
story.append(Paragraph(
    "The project is <b>not stuck in a loop of rebuilding ShunyaOS from scratch</b> — "
    "the PROD batch progression is linear and additive. However, there are warning signs:",
    sty_Body
))
story.append(Paragraph(
    "<b>Divergent branches</b> — if you switch between master and main frequently, "
    "you're effectively maintaining two versions of the same system. The 734-file diff means they've "
    "already diverged past easy reconciliation.",
    sty_Body))
story.append(Paragraph(
    "<b>Feature branches that never merge</b> — 6 alpha branches all started but never completed. "
    "If this pattern continues, the project accumulates 'graveyard' branches instead of converging.",
    sty_Body))
story.append(Paragraph(
    "<b>No formal release cadence</b> — without releases, there's no forcing function to resolve "
    "divergence, clean up branches, or stabilize. Work continues indefinitely without shipping.",
    sty_Body))
story.append(Spacer(1, 3*mm))

story.append(Paragraph("6.4 Recommended Next Actions", sty_SubSection))
story.append(Paragraph(
    "<b>1. Converge branches NOW.</b> Merge main into master (or rebase). "
    "Get to a single truth before writing another line of code. This is the highest-risk item.",
    sty_Body))
story.append(Paragraph(
    "<b>2. Publish Release v0.12.0</b> from the current master HEAD (49e7e82). "
    "Create a formal GitHub Release with release notes. This anchors the project.",
    sty_Body))
story.append(Paragraph(
    "<b>3. Decide on alpha branches.</b> For each of the 6 alpha branches: merge, close, or archive. "
    "Do not leave them hanging.",
    sty_Body))
story.append(Paragraph(
    "<b>4. Add license + branch protection.</b> These are quick wins that prevent future problems.",
    sty_Body))
story.append(Paragraph(
    "<b>5. Audit frontend size.</b> 584 MB is suspicious — check for duplicate node_modules, "
    "old build artifacts, or oversized assets.",
    sty_Body))
story.append(Spacer(1, 4*mm))

# ── Callout box ──
callout_data = [[Paragraph(
    "<b>Core Insight:</b> SHUNYA OS has a solid, well-structured backend runtime that is production-viable. "
    "The risk is not in the code quality but in the <i>organizational patterns</i> — branch divergence, "
    "unreconciled workstreams, and lack of formal shipping discipline. The PROD batch methodology is "
    "working. The FEP cycle provided valuable UX feedback that needs integration. Merge the streams, "
    "anchor with a release, and continue.",
    ParagraphStyle("callout", fontName="Helvetica", fontSize=9, textColor=TEXT_DARK,
        leading=12, backColor=HexColor("#FDFBF7"), borderPadding=8))]]
callout = Table(callout_data, colWidths=[A4[0] - 44*mm])
callout.setStyle(TableStyle([
    ("BOX", (0, 0), (-1, -1), 0.8, GOLD),
    ("LINEBEFORE", (0, 0), (0, -1), 3.5, GOLD),
    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FDFBF7")),
]))
story.append(callout)
story.append(PageBreak())

# ── SECTION 7: ARCHITECTURE FILE CONTENTS ──
story.append(Paragraph("7. Architecture File Contents", sty_Section))
story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=6))
story.append(Paragraph(
    "Full source code of all audited architecture files for reference.",
    sty_Body
))

for fname in files_order:
    content = files_content[fname]
    lines = content.count("\n")
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f"File: {fname}  ({lines} lines, {len(content)} bytes)", sty_Section))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=4))

    code_lines = content.split("\n")
    paragraphs = []
    for line in code_lines:
        escaped = escape(line, quote=False)
        displayed = escaped.replace(" ", "\u00a0")
        if displayed == "":
            displayed = " "
        paragraphs.append(Paragraph(displayed, sty_Code))

    chunk_size = 60
    for i in range(0, len(paragraphs), chunk_size):
        chunk = paragraphs[i:i+chunk_size]
        story.append(KeepTogether(chunk))

    story.append(PageBreak())

# ── BUILD PDF ──
doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
    topMargin=20*mm, bottomMargin=16*mm, leftMargin=18*mm, rightMargin=18*mm)

doc.build(story, onFirstPage=cover_page, onLaterPages=normal_page)
print(f"PDF generated: {OUTPUT}")
print(f"Size: {os.path.getsize(OUTPUT)} bytes")