# SHUNYA Object Workspace Canon

> **Canonical Reference — Phase X1**
> This is the most important document in the Experience Canon. It defines the universal object workspace architecture that every object type follows identically.

---

## 1. Universal Object Workspace Principle

Every object in SHUNYA — regardless of type (person, project, decision, document, task, financial account, campaign, asset, relationship, etc.) — follows the **exact same workspace architecture**.

This means:

| Aspect | Rule |
|--------|------|
| **Layout** | Every object workspace has the same sections in the same order |
| **Interaction** | Every object workspace behaves identically — same gestures, same shortcuts, same patterns |
| **Navigation** | Every object workspace navigates the same way — same tabs, same panels, same hierarchy |
| **AI Resident** | Every object has an AI resident that understands that object's context |
| **Relationships** | Every object has a relationships panel with the same interaction model |
| **Timeline** | Every object has a timeline with the same interaction model |
| **Header** | Every object has the same header structure |
| **Summary** | Every object has an executive summary |

### Why Universal?

- **Cognitive consistency.** Users learn the workspace once and apply it to every object type. No learning curve per object type.
- **Engineering scalability.** One component set renders every object type. Adding a new object type requires no new UI code — only data definitions.
- **AI scalability.** The AI Resident has a consistent interface across all objects. One AI interaction model, not one per object type.
- **Business agnosticism.** The workspace architecture makes no assumptions about what objects represent. It works for any organization, any domain.

---

## 2. Object Workspace Layout (Full)

```
┌────────────────────────────────────────────────────────────┐
│  OBJECT HEADER                                              │
│  ┌──────┐ ┌────────────────────────────────────────────┐   │
│  │ Icon │ │ Name / Title                                │   │
│  │ 48px │ │ [Type Badge] [Status Badge] [Confidence]    │   │
│  │      │ │ ID: OBJ-0042 · Created 2d ago · Updated 1h  │   │
│  └──────┘ │ [Edit] [Share] [More Actions ▾]            │   │
│           └────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────┤
│  EXECUTIVE SUMMARY                                          │
│  ┌────────────────────────────────────────────────────────┐│
│  │ AI-generated 3-line summary of this object             ││
│  │ Key metric: ████████░░ 78% · Trend: ↑12% · Next step  ││
│  │ Confidence: ████░░░░ 0.42 · Source: Analysis           ││
│  └────────────────────────────────────────────────────────┘│
├──────────┬─────────────────────────────────────────────────┤
│ SECTION  │  TAB BAR (scrollable)                           │
│ NAV      │  [Identity] [Relationships] [Timeline]          │
│ (left)   │  [Knowledge] [Tasks] [Execution]                │
│          │  [Metrics] [Documents] [AI] [History]           │
│          ├─────────────────────────────────────────────────┤
│          │  SECTION CONTENT                                │
│          │                                                 │
│          │  (differs per selected tab)                     │
│          │                                                 │
│          │                                                 │
│          │                                                 │
└──────────┴─────────────────────────────────────────────────┘
```

### Zone Divider

The left section nav is a narrow vertical strip (48px wide) showing section icons. When a section is selected, a subtle indicator (gold bar) appears. Hovering shows the section name in a tooltip. The section nav can be expanded to show text labels (optional, user preference).

---

## 3. Object Header

### Elements

| Element | Content | Rules |
|---------|---------|-------|
| **Icon** | 48x48px object type icon. Custom icons per object type. Fallback: first letter of object type. | Always present. Circular with subtle background. |
| **Name/Title** | Primary display name. Clickable to edit inline. | Max 1 line. Truncated with ellipsis. |
| **Type Badge** | Object type label (e.g., "Decision", "Project"). | Pill-shaped, muted color. |
| **Status Badge** | Current workflow status. Colors: active (green), pending (amber), completed (blue), archived (gray), cancelled (red). | Pill-shaped, semantic color. |
| **Confidence** | Overall confidence score (if AI-derived). Bar + percentage. Only shown when < 0.90 or when explicitly relevant. | Small, muted. Click for breakdown. |
| **ID** | System identifier. | Monospace font. Muted color. |
| **Timestamps** | Created, Updated, Last Accessed. | Small text, muted. |
| **Actions** | Edit, Share, More Actions (dropdown). | Icon buttons with text labels on hover. |

### Header Rules

- Header is always visible at the top of the content area.
- Header does not scroll — it remains fixed as the section content scrolls.
- Header has a subtle bottom border to separate it from content.
- Header height: 72px (icon row) + 24px (badges row) = 96px total.

---

## 4. Executive Summary

### Content

The executive summary is an AI-generated, highly condensed overview of the object:

```
┌─────────────────────────────────────────────────────────────┐
│ ● Decision 42 recommends a 15% budget increase for Q3       │
│   marketing, citing 22% ROI on similar campaigns last year. │
│   Awaiting CFO approval.                                    │
│                                                             │
│   Confidence: ████░░░░ 0.42 · Source: AI Analysis           │
│   Generated: 10 minutes ago · Based on: 3 sources           │
│                                                             │
│   [Review Evidence] [Make Decision] [Assign Reviewer]       │
└─────────────────────────────────────────────────────────────┘
```

### Rules

- Exactly 3 lines of text. No more, no less.
- Generated by AI. Regenerated when object state changes.
- Confidence score is always shown (even if 1.0 — "high confidence").
- Source count shows how many data points the summary is based on.
- Action buttons at the bottom (1–3 most relevant actions for the current object type and state).
- The user can dismiss the summary (collapse to a thin bar). Undismissable via "Show Summary" button.
- The summary is read-only — not editable.
- If AI summarization is unavailable, show a static template based on object type.

---

## 5. Section Navigation (Left)

### Structure

A vertical icon bar with the following sections in fixed order:

| # | Section | Icon | Always Present? |
|---|---------|------|----------------|
| 1 | Identity | 👤 | Yes |
| 2 | Relationships | 🔗 | Yes |
| 3 | Timeline | 📋 | Yes |
| 4 | Knowledge | 🧠 | Yes (unless no knowledge items exist) |
| 5 | Tasks | ✓ | Yes |
| 6 | Execution | ⚡ | Yes |
| 7 | Metrics | 📊 | Conditional (depends on object type) |
| 8 | Documents | 📄 | Conditional |
| 9 | AI | 🤖 | Yes |
| 10 | History | ⏱ | Yes |

### Behavior

| Interaction | Result |
|-------------|--------|
| **Click section icon** | Scroll content area to that section. Section becomes active. |
| **Hover** | Tooltip with section name (250ms delay). |
| **Active section** | Gold left border on the icon. |
| **Section with new content** | Subtle blue dot indicator on the icon. |
| **Scroll past section** | Active section updates to the one currently in view. |

### Section Visibility

Sections that are "conditional" are hidden if the object type does not support them. Example: a Person object may not have "Execution" or "Metrics" sections. Hidden sections are omitted from the navigation entirely — no ghost icons.

Users can reorder sections (persisted per user, not per object).

---

## 6. Identity Section

The canonical definition of the object — what it is, what type, what identifies it.

### Content

```
┌─ Identity ─────────────────────────────────────┐
│  Name                  Budget Increase Q3       │
│  Type                  Decision                 │
│  ID                    DEC-0042                 │
│  Status                Pending Approval         │
│  Created By            Jane Smith               │
│  Created At            2026-07-20 14:30         │
│  Updated By            Mark Chen                │
│  Updated At            2026-07-22 09:15         │
│  Tags                  budget, marketing, Q3    │
│  Confidence            0.42                     │
│                                                  │
│  Custom Fields:                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ Priority:  High                          │   │
│  │ Department: Marketing                    │   │
│  │ Amount:    $150,000                      │   │
│  │ Owner:     Joe Johnson                   │   │
│  └──────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### Rules

- Read-only by default. Click "Edit" to enter edit mode.
- All identity fields are organized as key-value pairs.
- Custom fields are dynamically loaded from the object type definition.
- Tags are clickable — clicking a tag searches for objects with the same tag.
- Identity is always the first section and never hidden.

---

## 7. Relationships Section

### Content

```
┌─ Relationships ─────────────────────────────────┐
│  ┌─ Parent Objects ─────────────────────────┐   │
│  │  ○ Project Alpha        (Project)        │   │
│  │  ○ Q3 Planning         (Project)        │   │
│  └──────────────────────────────────────────┘   │
│  ┌─ Related Objects ───────────────────────┐   │
│  │  ○ Marketing Budget     (Decision)      │   │
│  │  ○ CFO Review           (Task)          │   │
│  │  ○ Q2 Performance       (Report)        │   │
│  └──────────────────────────────────────────┘   │
│  ┌─ Child Objects ────────────────────────┐    │
│  │  ○ Approval Workflow    (Workflow)     │    │
│  │  ○ Impact Assessment    (Document)     │    │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  [Add Relationship] [View Graph]                 │
└──────────────────────────────────────────────────┘
```

### Interaction

| Interaction | Result |
|-------------|--------|
| **Click relationship** | Navigate to the related object (push current onto history) |
| **Right-click relationship** | Context menu: Open in new context, Copy link, Remove relationship |
| **Click "Add Relationship"** | Opened relationship search dialog (search for object to link) |
| **Click "View Graph"** | Open relationship graph panel |
| **Hover** | Tooltip with relationship type and object status |

### Rules

- Relationships are grouped by type (Parent, Related, Child).
- Relationship groups are collapsible.
- Only direct relationships are shown (one level deep).
- For deeper exploration, use "View Graph" or navigate to the Relationship Workspace.
- Relationship count badges show (e.g., "Parent (2)").

---

## 8. Timeline Section

### Content

```
┌─ Timeline ────────────────────────────────────┐
│  Today                                        │
│  ┌─────────────────────────────────────────┐  │
│  │ 09:15  Status changed to Pending        │  │
│  │        by Mark Chen                     │  │
│  │        "Awaiting CFO review"            │  │
│  ├─────────────────────────────────────────┤  │
│  │ 08:30  Document attached: Q2 Report     │  │
│  │        by Jane Smith                    │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  Yesterday                                     │
│  ┌─────────────────────────────────────────┐  │
│  │ 14:30  Object created                   │  │
│  │        by Jane Smith                    │  │
│  │        "Proposing budget increase"      │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  [Load Earlier]                                │
└────────────────────────────────────────────────┘
```

### Rules

- Chronological, newest first. Grouped by date.
- Each event shows: timestamp, actor, action type, description, optional comment.
- Events include: creation, status changes, field changes, relationship additions, document attachments, AI analysis runs, decisions made.
- Events are immutable — no editing or deleting timeline entries.
- Filterable by event type.
- Searchable within the timeline.
- Virtualized for performance (lazy loads older entries).

---

## 9. Knowledge Section

### Content

```
┌─ Knowledge ───────────────────────────────────┐
│  AI-Generated Knowledge                       │
│  ┌─────────────────────────────────────────┐  │
│  │ This decision is part of Q3 budget      │  │
│  │ planning. Similar decisions in Q2       │  │
│  │ resulted in 22% ROI increase.           │  │
│  │ Confidence: 0.78 · Source: AI Analysis  │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  Curated Knowledge                             │
│  ┌─────────────────────────────────────────┐  │
│  │ Budget Allocation Policy (v2.1)         │  │
│  │ Approved by Board — Apr 2026            │  │
│  │ Confidence: 1.0 · Source: Policy Doc    │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  Observations                                  │
│  ┌─────────────────────────────────────────┐  │
│  │ Marketing spend correlates with         │  │
│  │ revenue growth (R²=0.87)               │  │
│  │ Confidence: 0.89 · Source: ML Model     │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  [Add Note] [Propose Knowledge]                │
└────────────────────────────────────────────────┘
```

### Rules

- Three sub-sections: AI-Generated, Curated, Observations.
- Each knowledge item shows: text, confidence score, source, timestamp.
- AI-generated knowledge is auto-produced and updated.
- Curated knowledge is manually added or reviewed.
- Observations are factual statements extracted from data.
- Knowledge items are versioned — previous versions are accessible.

---

## 10. Tasks Section

### Content

```
┌─ Tasks (4) ──────────────────────────────────┐
│  ┌─ ☐ Review budget proposal              ─┐ │
│  │  Assigned to: Mark Chen · Due: Jul 25   │ │
│  │  Priority: High · Status: In Progress   │ │
│  └─────────────────────────────────────────┘ │
│  ┌─ ☐ Approve funding allocation         ──┐ │
│  │  Assigned to: CFO · Due: Jul 28         │ │
│  │  Priority: High · Status: Pending       │ │
│  └─────────────────────────────────────────┘ │
│  ┌─ ☐ Update Q3 projections              ──┐ │
│  │  Assigned to: Jane · Due: Jul 30         │ │
│  │  Priority: Medium · Status: To Do        │ │
│  └─────────────────────────────────────────┘ │
│  ┌─ ☐ Present to board                    ──┐ │
│  │  Assigned to: Jane · Due: Aug 01         │ │
│  │  Priority: Low · Status: To Do           │ │
│  └─────────────────────────────────────────┘ │
│                                                │
│  [Add Task] [View All Tasks]                   │
└────────────────────────────────────────────────┘
```

### Rules

- Tasks linked to this object are shown.
- Each task shows: title, assignee, due date, priority, status.
- Checkbox to mark complete (with confirmation for irreversible actions).
- Tasks are sorted by priority then due date.
- "Add Task" opens inline creation form.
- "View All Tasks" navigates to full task list (or opens Task Workspace).

---

## 11. Execution Section

### Content

```
┌─ Execution ──────────────────────────────────┐
│  Workflow Status: Awaiting Approval           │
│                                                │
│  ┌─ Workflow Steps ────────────────────────┐  │
│  │  1. Draft Proposal       ✓ Completed     │  │
│  │  2. Manager Review       ✓ Completed     │  │
│  │  3. CFO Approval         ▶ In Progress   │  │
│  │  4. Board Presentation   ☐ Pending       │  │
│  │  5. Implementation       ☐ Pending       │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  Current Step Actions:                         │
│  [Approve] [Request Changes] [Reassign]        │
│                                                │
│  Execution History:                            │
│  ┌─────────────────────────────────────────┐  │
│  │ Jul 22  CFO notified of pending review  │  │
│  │ Jul 20  Manager Review completed        │  │
│  │ Jul 18  Proposal drafted                │  │
│  └─────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

### Rules

- Execution shows the current execution state/workflow status.
- Workflow steps show progress with clear current step indicator.
- Action buttons are contextual to the current step.
- Execution history logs each step completion.
- If the object has no execution workflow, this section is hidden.

---

## 12. Metrics Section

### Content

```
┌─ Metrics ───────────────────────────────────┐
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Impact  │ │ Risk    │ │ Urgency │       │
│  │ High    │ │ Medium  │ │ High    │       │
│  │ ▲ 15%   │ │ — 0%    │ │ ▲ 10%   │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ ROI     │ │ Budget  │ │ Time    │       │
│  │ 22%     │ │ $150K   │ │ 14 days │       │
│  │ ▲ 3%    │ │ —       │ │ ▼ 2d    │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│                                              │
│  [Configure Metrics]                         │
└──────────────────────────────────────────────┘
```

### Rules

- Metric cards are 2x3 grid by default.
- Each metric card shows: label, value, trend direction, trend percentage.
- Metric cards are configurable per object type.
- If the object type has no metrics, this section is hidden.
- Metrics are read-only. Configured through object type definitions.

---

## 13. Documents Section

### Content

```
┌─ Documents (3) ──────────────────────────────┐
│  ┌─────────────────────────────────────────┐  │
│  │ 📄 Q2 Performance Report               │  │
│  │   Uploaded by Jane · Jul 20, 2026      │  │
│  │   [Preview] [Download]                 │  │
│  ├─────────────────────────────────────────┤  │
│  │ 📄 Budget Justification Draft          │  │
│  │   Created by AI · Jul 22, 2026         │  │
│  │   Version: 3 · [Preview]               │  │
│  ├─────────────────────────────────────────┤  │
│  │ 📄 Board Presentation Template         │  │
│  │   Uploaded by Mark · Jul 18, 2026      │  │
│  │   [Preview] [Download]                 │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  [Upload Document] [Link Document]             │
└────────────────────────────────────────────────┘
```

### Rules

- Documents linked to or uploaded for this object.
- Each shows: title, uploader, date, version count (if multiple versions).
- Preview opens inline document viewer.
- Documents are objects themselves — clicking opens the Document object workspace.
- If no documents exist and the object type doesn't typically have documents, this section is hidden.

---

## 14. AI Section (AI Resident)

### Content

```
┌─ AI Resident ───────────────────────────────┐
│  🤖 AI Assistant for [Object Name]          │
│                                              │
│  Suggested Actions:                          │
│  ┌───────────────────────────────────────┐  │
│  │ ● Approve this budget increase       │  │
│  │   Confidence: 0.72 · 3 similar       │  │
│  │   decisions approved this quarter    │  │
│  ├───────────────────────────────────────┤  │
│  │ ● Run impact analysis against        │  │
│  │   Q2 results                         │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  Recent Analysis:                            │
│  ┌───────────────────────────────────────┐  │
│  │ Analyzed 5 similar decisions.         │  │
│  │ All with positive outcomes.           │  │
│  │ Confidence: 0.85                      │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  [Ask AI] [View All Suggestions]              │
└──────────────────────────────────────────────┘
```

### Behavior

| Interaction | Result |
|-------------|--------|
| **Click suggestion** | Execute the suggested action (with confirmation) |
| **Click "Ask AI"** | Open AI conversation panel (slides in from right) |
| **Click "View All Suggestions"** | Expand to full suggestion list |
| **AI Resident collapsed** | Show only the icon and suggestion count badge |
| **AI Resident expanded** | Show full content with suggestions, analysis, conversation |

Detailed AI behavior is defined in 06_ai_collaboration.md.

---

## 15. History Section

### Content

```
┌─ History ───────────────────────────────────┐
│  Object Access History                      │
│  ┌───────────────────────────────────────┐  │
│  │ Today 09:15 — Mark Chen — Viewed     │  │
│  │ Today 08:30 — Jane Smith — Edited    │  │
│  │ Yesterday 14:00 — AI — Analyzed      │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  Change History:                             │
│  ┌───────────────────────────────────────┐  │
│  │ v1.3 — Jul 22 — Status changed       │  │
│  │ v1.2 — Jul 20 — Budget amount changed│  │
│  │ v1.1 — Jul 18 — Description updated  │  │
│  │ v1.0 — Jul 15 — Object created       │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  [View Full Audit Log]                       │
└──────────────────────────────────────────────┘
```

### Rules

- Shows access history (who viewed when) and change history (version log).
- Change history shows each version with change summary.
- Click a version to see a diff of what changed.
- "View Full Audit Log" opens the audit trail in the System Workspace.

---

## 16. Object Workspace States

### State Machine

```
┌──────────┐    ┌───────────┐    ┌──────────┐
│  Viewing │───▶│  Editing  │───▶│  Saving  │
└──────────┘    └───────────┘    └─────┬────┘
      ▲                                │
      └────────────────────────────────┘
           (auto-save completes)
```

| State | Description | UI State |
|-------|-------------|----------|
| **Viewing** | Default state. Read-only. Full navigation available. | All sections visible, read-only |
| **Editing** | User is editing one or more fields. | Inline editors active, Save/Cancel buttons visible |
| **Saving** | Autosave in progress. | Transient saving indicator (200ms minimum) |
| **Error** | Save failed. | Error message with retry option |

### Edit Mode

- Edit mode is per-field (inline), not per-page.
- Click any editable field to start editing.
- Changes auto-save after 2 seconds of inactivity.
- "Cancel" reverts all changes since the last save.
- "Undo" works up to 500 changes across the session.

---

## 17. Empty State

When a section has no content:

```
┌─ Section Name ──────────────────────────────┐
│                                              │
│              No [content type] yet.          │
│                                              │
│         [Create First]  [Learn More]         │
│                                              │
└──────────────────────────────────────────────┘
```

### Empty State Rules

- Always show a "Create First" call-to-action when appropriate.
- "Learn More" links to relevant documentation.
- Empty states are informative, not decorative.
- No stock illustrations or generic "no data" messages.
- AI resident can auto-suggest initial content: "Would you like me to generate a preliminary analysis?"

---

## 18. Object Workspace Invariants

1. **Every object has the exact same workspace layout.** Sections, navigation, header, summary — identical.
2. **The section order is fixed.** Identity, Relationships, Timeline, Knowledge, Tasks, Execution, Metrics, Documents, AI, History.
3. **Sections that are not relevant to an object type are hidden.** No disabled or grayed-out sections.
4. **Every section has a viewing state and (where applicable) an editing state.**
5. **The executive summary is always present and always AI-generated.**
6. **The AI Resident is always present.** Never removed. Never muted by default.
7. **The header is always visible and fixed.** Never scrolls away.
8. **Section navigation persists across objects.** If you are on the Timeline tab of one object, switching objects opens the Timeline tab of the new object.
9. **Empty states are informative with a call-to-action.**
10. **All sections support progressive disclosure.** Summary view → Detail view → Exploration view.