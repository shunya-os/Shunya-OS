import os, json
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

PURPLE = HexColor("#6d28d9"); DARK = HexColor("#1a1a1a"); MUTED = HexColor("#6b7280")
GREEN = HexColor("#059669"); RED = HexColor("#dc2626"); AMBER = HexColor("#d97706")
BLUE = HexColor("#2563eb"); LIGHT_BG = HexColor("#f5f5f5"); TABLE_HDR = HexColor("#f0f7ff")

styles = getSampleStyleSheet()
def mk(n, **kw):
    styles.add(ParagraphStyle(n, **kw))

mk("CoverTitle", fontName="Helvetica-Bold", fontSize=28, textColor=PURPLE, spaceAfter=6, alignment=TA_CENTER)
mk("CoverSub", fontName="Helvetica", fontSize=14, textColor=MUTED, spaceAfter=20, alignment=TA_CENTER)
mk("SecH1", fontName="Helvetica-Bold", fontSize=16, textColor=DARK, spaceBefore=16, spaceAfter=8)
mk("SecH2", fontName="Helvetica-Bold", fontSize=13, textColor=PURPLE, spaceBefore=12, spaceAfter=6)
mk("GapItem", fontName="Helvetica", fontSize=9, textColor=DARK, leading=14, spaceAfter=6, leftIndent=8)
mk("Body", fontName="Helvetica", fontSize=10, textColor=DARK, leading=15, spaceAfter=6)
mk("BodyB", fontName="Helvetica-Bold", fontSize=10, textColor=DARK, leading=15, spaceAfter=6)
mk("Small", fontName="Helvetica", fontSize=8, textColor=MUTED, leading=10)
mk("StatLabel", fontName="Helvetica", fontSize=9, textColor=MUTED, alignment=TA_CENTER)

working = [
    "Object model — canonical entity, SQLAlchemy-backed",
    "Execution loop — run_cycle() with crash isolation",
    "Decision engine — stage progression (new->contacted->quoted->closed)",
    "MessageProposal — proposal creation with dedup, approve/reject/edit API",
    "EmailProvider — SMTP email send (ACTIVATION-R1)",
    "ProviderRegistry — 9 LLM providers with auto-fallback chain",
    "MixedIntelligenceRouter — business data + internet + AI synthesis",
    "Integration Registry — pluggable integration framework",
    "Cmd+K command bar — 7 commands + AI query routing",
    "Workspace UI — full entity management with tabs, timeline, tasks, notes",
    "Daily Brief, Risk Detection, Next Best Action — business awareness",
    "Background loop runner — worker.py + CLI + ENABLE_LOOP_AUTOMATION",
    "Polling UI — auto-refresh every 15s",
]

semi_done = [
    "Gmail OAuth — framework exists (communication/oauth.py) but not wired to EmailProvider",
    "SMTP email — works but no Gmail API read (cannot fetch inbox)",
    "WhatsApp — 3 stub implementations, none connected",
    "MixedIntelligenceRouter — works but BusinessDataRetriever fails on SQLite (ILIKE)",
    "AI decision engine integration — done but AI is fallback-only (rule confidence always wins)",
    "Integration Registry — framework exists, only 1 integration registered",
    "Integration API — endpoints exist but sync logic is placeholder",
]

not_connected = [
    "execution_intelligence/ — 3 files, intelligence layer, never called",
    "execution_runtime/ — 2 files, alternative runtime, not wired",
    "decision_runtime/ — 7 files, legacy decision system",
    "executive/ — 3 files, executive engine with models, not wired",
    "cortex/ — 6 files (attention, brief, health, state), not connected to UI",
    "kernel/ — 10 files, kernel modules, not connected",
    "shunya/ — 14 sub-dirs, ~50 files, complete sub-framework, orphaned",
    "orchestration/ + orchestrator/ — 9 files, two systems, neither wired",
    "evidence/ — 6 files, provenance tracking, orphaned",
    "intention/ — 2 files, intention models, orphaned",
    "awareness/ — 3 files, awareness engine, orphaned",
    "automation/ — 4 files, automation models/routes, not triggered",
    "onboarding/ — 3 files, onboarding routes, not connected",
    "planning/ — 6 files, planning engine, no trigger",
]

duplicates = [
    "adapters/email_adapter.py vs communication/email.py — both send email",
    "adapters/whatsapp_adapter.py vs communication/whatsapp.py — both stubs",
    "adapters/whatsapp_free/ + adapters/whatsapp_official/ — 3 WhatsApp impls",
    "graph/ (9 files) vs graph_universal/ (8 files) — similar functionality",
    "decision/ (3 files) vs decision_runtime/ (7 files) — decision overlap",
    "execution/ vs execution_engine/ vs execution_runtime/ vs execution_intelligence/ — 4 parallel systems",
    "objects/ vs object_composer/ vs object_workspace/ — triple object systems",
    "Lead (app/models.py) vs Object (app/objects/models.py) — partially resolved",
    "integration/routes.py (social) vs integration/routes_api.py (v2) — duplicate route files",
]

recommendations = [
    ("PHASE 1 — CORE HARDENING (WEEK 1-2)", [
        "Remove all 152 print() statements -> structured logging",
        "Consolidate 4 execution systems -> 1 canonical execution path",
        "Remove Lead model, ShunyaObject legacy -> Object only",
        "Consolidate dual adapter files -> single adapter interface",
        "Remove debug routes and exempt auth list for production",
        "Add error boundaries to all API routes",
    ]),
    ("PHASE 2 — INTEGRATION REALITY (WEEK 2-4)", [
        "Wire Gmail OAuth -> EmailProvider for inbox read + send",
        "Replace OpenWAProvider with Twilio/WhatsApp Cloud API",
        "Connect WhatsApp webhook for incoming messages",
        "Implement Google Calendar sync -> timeline objects",
        "Connect Integration Registry to real sync logic",
        "Add rate-limit handling and provider health checks",
    ]),
    ("PHASE 3 — INTELLIGENCE ACTIVATION (WEEK 3-5)", [
        "Fix BusinessDataRetriever for PostgreSQL compatibility",
        "Replace hardcoded confidence with data-driven confidence scoring",
        "Wire AI decision results into workspace UI (not just rule)",
        "Add context window builder for MIR queries",
        "Implement source citations and 'View Source' buttons in UI",
    ]),
    ("PHASE 4 — ORPHAN REVIVAL (WEEK 4-6)", [
        "Audit shunya/ (50 files) — extract reusable patterns, archive rest",
        "Connect cortex/ modules to workspace UI",
        "Wire authz/ into auth flow for RBAC",
        "Connect evidence/ provenance tracking to execution logs",
        "Decide on graph vs graph_universal — consolidate into one",
    ]),
    ("PHASE 5 — AUTONOMOUS OPERATIONS (WEEK 5-7)", [
        "Add event triggers: email received -> run_cycle, webhook -> run_cycle",
        "Implement auto-proposal generation for stale leads",
        "Add action queue with retry mechanism",
        "Enable cron-based loop execution",
        "Track delivery status and link responses to proposals",
    ]),
    ("PHASE 6 — USER EXPERIENCE (WEEK 6-8)", [
        "Remove 7,014 unused frontend files — replace with minimal workspace",
        "Add real-time updates via WebSocket (replace polling)",
        "Display real LLM output with provider name and confidence",
        "Add integration connect UI (OAuth flow in workspace)",
        "Add sync status and last-updated timestamps",
        "Implement onboarding flow for new users",
    ]),
]

layer_data = [
    ("Intelligence (AI/LLM/MIR)", "15,621"), ("Core Runtime (loop/objects/execution)", "3,862"),
    ("Execution Engine", "523"), ("Decision Engine", "373"), ("Communication", "249"),
    ("UI/API/Debug", "223"), ("Knowledge (knowledge/knowledge_store)", "100"),
    ("Graph (graph/graph_universal)", "98"), ("Shunya OS sub-framework", "74"),
    ("Orchestration", "63"), ("Auth", "47"), ("Space", "17"), ("Kernel", "10"),
    ("Intake", "10"), ("Finance", "9"), ("Founder", "7"), ("Integrations", "6"),
    ("Evidence", "6"), ("Cortex", "6"),
]

stat_table_data = [
    ["Metric", "Value"],
    ["Python Files", "493"], ["Directories", "112"], ["Blueprints", "60"],
    ["API Routes", "659"], ["Test Files", "144"], ["Frontend Files", "7,014"],
    ["Total Commits", "152"], ["Authors", "2"],
]

mock_table_data = [
    ["Pattern", "Count", "Risk"],
    ["print() statements", "152", "HIGH — no structured logging"],
    ["legacy references", "95", "HIGH — dead code"],
    ["simulate calls", "24", "MEDIUM — mock behavior"],
    ["mock references", "15", "MEDIUM — mock objects"],
    ["simulated platform", "13", "HIGH — fake API responses"],
    ["fake references", "12", "MEDIUM — test data"],
    ["hardcoded values", "7", "LOW — configuration"],
    ["ShunyaObject legacy", "32", "HIGH — unreferenced model"],
    ["Lead model", "8", "RESOLVED (R2) — safe to remove"],
    ["OpenWA mock", "1", "BLOCKER for WhatsApp"],
]

priority_table_data = [
    ["Priority", "Item", "Effort", "Impact"],
    ["P0", "Remove print() -> structured logging", "2 days", "Production readiness"],
    ["P0", "Consolidate 4 execution systems", "3 days", "Removes 80% duplication"],
    ["P0", "Wire Gmail OAuth -> real email read/send", "3 days", "First real integration"],
    ["P1", "Replace WhatsApp mock with Twilio/Cloud API", "2 days", "Real communication"],
    ["P1", "Fix BusinessDataRetriever for PostgreSQL", "1 day", "AI works with real data"],
    ["P1", "Wire decision_source -> workspace UI", "1 day", "AI transparency"],
    ["P2", "Audit shunya/ (50 files) — extract/archive", "3 days", "Codebase cleanup"],
    ["P2", "Remove debug routes + exempt auth", "2 days", "Security hardening"],
    ["P2", "Add error boundaries to all routes", "2 days", "Reliability"],
    ["P3", "Connect cortex/, evidence/, awareness/", "5 days", "Feature completion"],
    ["P3", "WebSocket real-time updates", "3 days", "UX improvement"],
    ["P3", "Onboarding flow", "2 days", "User experience"],
]

doc = SimpleDocTemplate(
    "/home/shunya-deploy/shunya_os/reports/SHUNYA_OS_FULL_AUDIT_2026.pdf",
    pagesize=A4, topMargin=20*mm, bottomMargin=20*mm,
    leftMargin=18*mm, rightMargin=18*mm
)
el = []

# COVER
el.append(Spacer(1, 60*mm))
el.append(Paragraph("SHUNYA OS", ParagraphStyle("cv", fontName="Helvetica-Bold", fontSize=48, textColor=PURPLE, alignment=TA_CENTER)))
el.append(Paragraph("Full System Audit & Gap Analysis", ParagraphStyle("cv2", fontName="Helvetica", fontSize=18, textColor=DARK, alignment=TA_CENTER, spaceAfter=6)))
el.append(Spacer(1, 8*mm))
el.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ParagraphStyle("cv3", fontName="Helvetica", fontSize=11, textColor=MUTED, alignment=TA_CENTER)))
el.append(Spacer(1, 50*mm))
el.append(HRFlowable(width="60%", color=PURPLE, thickness=2, spaceAfter=6))
el.append(Paragraph("CONFIDENTIAL — FOUNDER AUDIT", ParagraphStyle("cv5", fontName="Helvetica-Bold", fontSize=10, textColor=PURPLE, alignment=TA_CENTER)))
el.append(PageBreak())

# EXECUTIVE SUMMARY
el.append(Paragraph("1. EXECUTIVE SUMMARY", styles["SecH1"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=6))
el.append(Paragraph("SHUNYA OS is a 493-file Python codebase with 7,014 frontend files, 659 API routes across 60 blueprints, and 144 test files. The system has 152 commits from 2 authors over its lifetime.", styles["Body"]))
el.append(Spacer(1, 3*mm))
el.append(Paragraph("Active Working System:", styles["BodyB"]))
for f in working:
    el.append(Paragraph(f"  \u2705 {f}", styles["GapItem"]))

# STATS
el.append(Spacer(1, 4*mm))
el.append(Paragraph("2. CODEBASE STATISTICS", styles["SecH1"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=6))
t = Table(stat_table_data, colWidths=[80*mm, 80*mm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), TABLE_HDR),
    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#d4d4d4")),
    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, LIGHT_BG]),
    ("ALIGN", (1, 0), (1, -1), "CENTER"),
]))
el.append(t)

# LAYERS
el.append(Spacer(1, 4*mm))
el.append(Paragraph("3. ARCHITECTURAL LAYER BREAKDOWN", styles["SecH1"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=6))
col1 = layer_data[:10]
col2 = layer_data[10:]
combined = []
for i in range(max(len(col1), len(col2))):
    r1 = col1[i] if i < len(col1) else ("", "")
    r2 = col2[i] if i < len(col2) else ("", "")
    combined.append([f"{r1[0]}: {r1[1]}", f"{r2[0]}: {r2[1]}"])
lt = Table(combined, colWidths=[85*mm, 85*mm])
lt.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
]))
el.append(lt)

# GAP ANALYSIS
el.append(PageBreak())
el.append(Paragraph("4. GAP ANALYSIS", styles["SecH1"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=6))
el.append(Paragraph("4.1 Working Systems (13)", styles["SecH2"]))
for f in working:
    el.append(Paragraph(f"  \u2705 {f}", styles["GapItem"]))
el.append(PageBreak())
el.append(Paragraph("4.2 Semi-Done (need wiring)", styles["SecH2"]))
for item in semi_done:
    el.append(Paragraph(f"  \u26a0\ufe0f {item}", styles["GapItem"]))
el.append(PageBreak())
el.append(Paragraph("4.3 Not Connected (orphaned)", styles["SecH2"]))
for item in not_connected:
    el.append(Paragraph(f"  \u274c {item}", styles["GapItem"]))
el.append(PageBreak())
el.append(Paragraph("4.4 Duplicate/Extra Systems (9)", styles["SecH2"]))
for item in duplicates:
    el.append(Paragraph(f"  \ud83d\udd04 {item}", styles["GapItem"]))

# MOCK & LEGACY
el.append(PageBreak())
el.append(Paragraph("5. MOCK DATA & LEGACY ANALYSIS", styles["SecH1"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=6))
mt = Table(mock_table_data, colWidths=[65*mm, 25*mm, 80*mm])
mt.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), TABLE_HDR),
    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#d4d4d4")),
    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, LIGHT_BG]),
    ("ALIGN", (1, 0), (1, -1), "CENTER"),
]))
el.append(mt)

# COMPLETION STRATEGY
el.append(PageBreak())
el.append(Paragraph("6. COMPLETION STRATEGY — 6 Phases, 8 Weeks", styles["SecH1"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=6))
for i, phase_data in enumerate(recommendations):
    phase_name, steps = phase_data
    el.append(Paragraph(phase_name, styles["SecH2"]))
    for step in steps:
        el.append(Paragraph(f"  \u25b8 {step}", styles["GapItem"]))
    if i < len(recommendations) - 1:
        el.append(PageBreak())

# FINAL VERDICT + PRIORITY MATRIX
el.append(Paragraph("7. FINAL VERDICT", styles["SecH1"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=6))
el.append(Paragraph("<b>System State: PARTIALLY WORKING — ~60% of active code is functional</b>", styles["Body"]))
el.append(Spacer(1, 3*mm))
verdicts = [
    "The ACTIVATION-layer (loop, proposals, UI, decision engine, email) works end-to-end.",
    "The Intelligence layer (MIR, provider chain, LLM fallback) works but has mock data issues.",
    "~40% of the codebase (shunya/, kernel/, cortex/, execution_runtime/, etc.) is orphaned/legacy.",
    "7,014 frontend files exist but only the /workspace page is actively used.",
    "60 blueprints exist but only ~15 are registered in the active app factory.",
    "Real integrations (Gmail, WhatsApp, Calendar) have stubs but no real connectors.",
    "Completion requires consolidating duplicates first, then wiring real integrations.",
]
for v in verdicts:
    el.append(Paragraph(f"  \u25c6 {v}", styles["GapItem"]))
el.append(Spacer(1, 6*mm))
el.append(Paragraph("<b>Bottom Line:</b> SHUNYA OS can serve as a functional demo today. With 6-8 weeks of focused work (2 engineers), it can become a production-ready AI operating system for small businesses.", styles["Body"]))

el.append(Spacer(1, 8*mm))
el.append(Paragraph("8. PRIORITY EXECUTION MATRIX", styles["SecH1"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=6))
pt = Table(priority_table_data, colWidths=[20*mm, 85*mm, 25*mm, 40*mm])
pt.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), TABLE_HDR),
    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#d4d4d4")),
    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, LIGHT_BG]),
    ("ALIGN", (2, 0), (3, -1), "CENTER"),
]))
el.append(pt)
el.append(Spacer(1, 6*mm))
el.append(Paragraph(f"Report generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Small"]))
el.append(HRFlowable(width="100%", color=PURPLE, thickness=1, spaceAfter=2))
el.append(Paragraph("SHUNYA OS — CONFIDENTIAL FOUNDER AUDIT", styles["Small"]))

doc.build(el)
print("PDF generated successfully")
print("Path: /home/shunya-deploy/shunya_os/reports/SHUNYA_OS_FULL_AUDIT_2026.pdf")