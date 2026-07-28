# SHUNYA Workspace Model

> **Canonical Reference — Phase X1**
> Defines the 14 canonical workspaces. Each workspace is a domain of focus organized around an object type. All workspaces share the same architecture — only the content differs.

---

## 1. Workspace Architecture (Universal)

Every workspace follows this architecture:

```
┌──────────────────────────────────────────────────┐
│  Zone 1: Global Navigation Bar                    │
│  Workspace Icon · Workspace Name · [Search]       │
│  [Relationship Graph] [Quick Actions] [Settings]  │
├──────────────────────────────────────────────────┤
│  Zone 2: Context Panel (left, 300px, collapsible) │
│  ┌─ Current Object ──────────────────────────┐   │
│  │  Name · Type · Status · Confidence         │   │
│  │  Summary line                              │   │
│  ├─ Quick Actions ───────────────────────────┤   │
│  │  [Action 1] [Action 2] [Action 3]         │   │
│  ├─ Relationships ───────────────────────────┤   │
│  │  Related objects grouped by type          │   │
│  ├─ Recent Items ────────────────────────────┤   │
│  │  Last 5 objects from this workspace       │   │
│  └─ AI Resident (minimized) ─────────────────┘   │
├──────────────────────────────────────────────────┤
│  Zone 3: Content Area                              │
│  ┌─ Workspace Header ──────────────────────────┐  │
│  │  Workspace title · Default view options     │  │
│  ├─ Object Grid / List / Primary Content ──────┤  │
│  │  (differs per workspace)                    │  │
│  └─────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Universal Rules

- Zone 1 and the three-zone layout are identical across all workspaces.
- Zone 2 (Context Panel) content changes based on the active object, but its structure is universal.
- Zone 3 default view differs per workspace (grid, list, or specific content).
- When no object is selected, Zone 2 shows workspace-level context (recent objects, workspace metrics).
- When an object is selected, Zone 2 shows the object's context panel (same across all workspaces).

---

## 2. Home Workspace

**Purpose:** The default landing workspace. Provides an executive overview of the organization's current state.

**Visible Information:**
- Organization health summary (8 dimensions)
- Recent decisions (last 7 days)
- Active tasks across all workspaces
- Upcoming deadlines
- Attention-worthy changes (what changed since last visit)
- Quick access to all workspaces

**Interaction Rules:**
- Read-only by default. No editing in Home.
- Clicking any item navigates to the relevant workspace and object.
- Grid layout: 2-column on desktop, 1-column on narrow screens.
- Cards are sorted by recency of change.

**AI Behavior:**
- AI Resident summarizes: "Key changes since your last visit: 3 decisions made, 2 tasks completed, 1 metric crossed threshold."
- AI suggests: "You might want to review the Q3 budget decision."
- AI never shows a chat window by default.

**Expandable Regions:**
- Each card group can be expanded to show more items.
- "View all recent decisions" expands the decisions section.
- Organization health panel has expandable per-dimension detail.

**Navigation Rules:**
- Always accessible from the workspace switcher (first icon).
- The only workspace without a required object type.
- Cannot be removed from navigation.

---

## 3. Universal Search Workspace

**Purpose:** The search result surface. Not a standalone workspace — activated by search.

**Visible Information:**
- Search query
- Results grouped by object type
- Filters by workspace, object type, date range, status
- Quick preview on hover

**Interaction Rules:**
- Results update in real time as the query changes.
- Clicking a result navigates to the object in its native workspace.
- Filters are always visible (collapsed on narrow screens).

**AI Behavior:**
- If query is ambiguous, AI suggests: "Did you mean X or Y?"
- AI can expand search to semantically similar terms.
- AI shows related objects not directly matching the query.

**Navigation Rules:**
- Exists only as an overlay / full-screen mode.
- No persistent workspace in the switcher.

---

## 4. Relationship Workspace

**Purpose:** Explore the relationship graph between objects. Understand how entities connect.

**Visible Information:**
- Interactive relationship graph (force-directed)
- Object cards with connection lines
- Filterable by relationship type
- Timeline of when relationships were established

**Interaction Rules:**
- Click a node to select it and see its direct connections.
- Drag to reposition the graph (user view only, not persisted).
- Double-click a node to navigate to that object.
- Pin a node to keep it in focus.
- Zoom in/out with scroll or pinch.

**AI Behavior:**
- AI highlights significant relationships: "This object has unusually many connections."
- AI suggests unexplored relationships: "You haven't reviewed the relationship between X and Y."
- AI can generate a path: "How is A connected to B?"

**Expandable Regions:**
- Node detail panel (slides in on selection).
- Relationship type filter panel.
- Timeline slider to see graph at different points in time.

**Navigation Rules:**
- Workspace is read-only — all actions happen in the target object's workspace.
- Navigation to an object from here goes to that object's native workspace.

---

## 5. Organization Workspace

**Purpose:** View and manage the organization structure, profiles, roles, and groups.

**Visible Information:**
- Organization chart (collapsible hierarchy)
- Person profiles (name, role, contact, relationships)
- Group memberships
- Role definitions
- Organization metrics (headcount, structure changes)

**Interaction Rules:**
- Click a person to see their profile in the Context Panel.
- Click "Open" to navigate to their full Person object workspace.
- Org chart is interactive: expand/collapse departments.
- Drag to reorganize (admin only, with confirmation).

**AI Behavior:**
- AI surfaces: "3 people joined, 1 left since last view."
- AI suggests: "This team has grown 40% — consider restructuring."
- AI can propose optimal team structures based on workload patterns.

**Expandable Regions:**
- Per-person detail panel.
- Department detail on expand.
- Metrics panel (headcount trends, diversity metrics, turnover).

**Navigation Rules:**
- Default view: org chart.
- Secondary view: person directory (table with filters).
- Supports deep links to specific persons.

---

## 6. Project Workspace

**Purpose:** Manage projects, initiatives, and their lifecycles. Fully business-agnostic.

**Visible Information:**
- Project list (board, list, or timeline view)
- Per-project: status, timeline, team, tasks, metrics
- Project health indicators
- Milestones and deadlines

**Interaction Rules:**
- Default view configurable per user (board/list/timeline).
- Drag-and-drop for status changes.
- Click a project card to load it in the Context Panel.
- Double-click or click "Open" to navigate to the full Project object.

**AI Behavior:**
- AI surfaces: "Project X is behind schedule. 3 tasks overdue."
- AI suggests: "Reassign task Y to person Z — they have capacity."
- AI can auto-generate project status summaries.
- AI predicts project completion date with confidence.

**Expandable Regions:**
- Project detail panel.
- Timeline detail (Gantt chart).
- Resource allocation view.
- Risk register.

**Navigation Rules:**
- Default: project board sorted by priority/status.
- Supports filtering by status, owner, date.
- Quick action: create new project.

---

## 7. Document Workspace

**Purpose:** Create, find, and manage documents. Documents are objects with full workspace support.

**Visible Information:**
- Document library (list or grid)
- Per-document: title, type, author, last modified, status
- Document preview on selection
- Version history
- Sharing and access information

**Interaction Rules:**
- Click to select and preview in Context Panel.
- Double-click to open the Document object workspace.
- Documents support inline preview (not just file icons).
- Drag-and-drop to organize into folders/tags.

**AI Behavior:**
- AI summarizes document content.
- AI suggests related documents based on content similarity.
- AI can answer questions about document content.
- AI tracks reading progress: "You've read 60% of this document."

**Expandable Regions:**
- Document preview panel.
- Version history timeline.
- Annotation and comment panel.
- Related documents.

**Navigation Rules:**
- Default: list view sorted by last modified.
- Grid view for visual documents (reports, presentations).
- Tree view for folder-based organization.

---

## 8. Decision Workspace

**Purpose:** Track, review, and manage decisions. Every decision is a first-class object with full provenance.

**Visible Information:**
- Decision register (list by status, date, creator)
- Per-decision: title, status, outcome, confidence, evidence
- Decision tree view
- Pending decisions requiring attention
- Decision metrics (made/pending/overdue)

**Interaction Rules:**
- Default view: decision list sorted by urgency.
- Click to expand decision detail in Context Panel.
- Status transitions are explicit and logged.
- Every decision requires evidence.

**AI Behavior:**
- AI tracks: "5 decisions made today, 3 pending your review."
- AI suggests evidence: "Consider reviewing document X before deciding."
- AI can recommend a decision based on past patterns (with confidence).
- AI can simulate outcomes of different decisions.

**Expandable Regions:**
- Decision detail with evidence chain.
- Outcome tracking panel.
- Decision impact analysis.
- Related decisions graph.

**Navigation Rules:**
- Filter by status, date range, creator, workspace.
- Pending decisions have a dedicated "Needs Attention" view.

---

## 9. Task Workspace

**Purpose:** Manage tasks across all objects. Tasks are atomic units of work.

**Visible Information:**
- Task list (board, list, or timeline)
- Per-task: title, status, assignee, due date, priority
- Task dependencies
- My Tasks (personal view)
- Overdue and upcoming tasks

**Interaction Rules:**
- Drag-and-drop status changes.
- Inline editing for quick updates.
- Click to open task detail in Context Panel.
- Bulk operations (reassign, reschedule).

**AI Behavior:**
- AI prioritizes tasks: "These 3 tasks are most urgent."
- AI suggests task assignments based on workload.
- AI can auto-generate tasks from decisions or meetings.
- AI predicts task completion dates.

**Expandable Regions:**
- Task detail panel.
- Task dependency graph.
- Workload view (per-person).
- Timeline view.

**Navigation Rules:**
- Default: board view (To Do / In Progress / Done).
- "My Tasks" is a saved filter, not a separate view.
- Tasks are linked to their parent object (project, decision, etc.).

---

## 10. Knowledge Workspace

**Purpose:** Organizational knowledge base. Accumulated facts, wisdom, and analysis.

**Visible Information:**
- Knowledge graph
- Article/document index
- Per-knowledge-item: title, category, source, confidence, last updated
- Searchable knowledge base
- AI-generated summaries

**Interaction Rules:**
- Browse by category, tag, or relationship.
- Click to view full knowledge item.
- Knowledge items are versioned with provenance.
- Users can propose knowledge updates (requires review).

**AI Behavior:**
- AI is the primary knowledge curator.
- AI auto-generates knowledge from observations.
- AI identifies knowledge gaps: "You don't have knowledge about X."
- AI can answer questions from the knowledge base directly.

**Expandable Regions:**
- Knowledge item detail.
- Source evidence chain.
- Knowledge graph visualization.
- Confidence and freshness indicators.

**Navigation Rules:**
- Default: search/browse interface.
- Knowledge graph view for relationship exploration.
- Links to knowledge items from all other workspaces.

---

## 11. Financial Workspace

**Purpose:** Financial overview and management. Business-agnostic — works for any organization's financial structure.

**Visible Information:**
- Financial summary (revenue, expenses, balance)
- Budget tracking
- Account/ledger view
- Transaction list
- Financial metrics and trends
- Forecast vs actual

**Interaction Rules:**
- Read-only financial data by default.
- Click to drill into accounts, transactions, or metrics.
- Period selection (monthly, quarterly, annual).
- Export capabilities.

**AI Behavior:**
- AI surfaces: "Expenses exceeded budget by 8% this month."
- AI detects anomalies: "Unusual transaction pattern detected."
- AI forecasts: "Based on current trends, Q4 revenue is projected at X."
- AI can generate financial summaries in natural language.

**Expandable Regions:**
- Per-account detail.
- Transaction list with filters.
- Budget vs actual comparison.
- Forecast detail.

**Navigation Rules:**
- Default: summary dashboard.
- Drill-down: account → transaction group → individual transaction.
- Period picker is always visible.

---

## 12. Communication Workspace

**Purpose:** Manage communications within the organization. Notifications, messages, broadcasts.

**Visible Information:**
- Communication threads
- Announcements
- Scheduled communications
- Communication templates
- Delivery metrics

**Interaction Rules:**
- Threaded view by default.
- Compose new communication (broadcast, targeted, or individual).
- Templates for common communication types.
- Read/unread tracking.

**AI Behavior:**
- AI can draft communications based on context.
- AI suggests recipients: "This communication should include team X."
- AI can analyze communication effectiveness (open rates, response rates).
- AI schedules communications for optimal delivery time.

**Expandable Regions:**
- Thread detail panel.
- Analytics panel (delivery, read rates, responses).
- Template library.
- Scheduled communications.

**Navigation Rules:**
- Default: inbox-like view sorted by date.
- Filter by type, sender, date, read status.
- Compose is a full-screen overlay.

---

## 13. Campaign Workspace

**Purpose:** Plan, execute, and measure campaigns. Fully business-agnostic (marketing, outreach, awareness, or internal).

**Visible Information:**
- Campaign list (board or timeline)
- Per-campaign: name, status, channels, metrics, budget
- Campaign performance dashboard
- Audience/segment management
- Creative asset library

**Interaction Rules:**
- Campaigns have phases: Plan → Execute → Measure → Optimize.
- Click to open campaign object workspace.
- Metrics update in real time during execution.
- Drag-and-drop to reorder or change status.

**AI Behavior:**
- AI recommends campaign optimizations.
- AI can auto-generate campaign briefs.
- AI predicts campaign performance based on historical data.
- AI segments audiences based on patterns.

**Expandable Regions:**
- Campaign detail panel.
- Performance metrics panel.
- Audience segment detail.
- Creative asset preview.

**Navigation Rules:**
- Default: campaign board by status.
- Timeline view for campaign scheduling.
- Performance view for live campaigns.

---

## 14. Asset Workspace

**Purpose:** Manage digital and physical assets. Business-agnostic.

**Visible Information:**
- Asset library (grid of thumbnails)
- Per-asset: name, type, status, metadata, usage
- Asset preview
- Usage tracking
- Version management

**Interaction Rules:**
- Grid view default for visual assets.
- List view for non-visual assets.
- Click to preview in Context Panel.
- Drag-and-drop for upload.

**AI Behavior:**
- AI auto-tags assets based on content.
- AI suggests: "This asset is similar to X you used before."
- AI can generate asset descriptions.
- AI tracks asset usage and suggests archiving unused assets.

**Expandable Regions:**
- Asset preview panel.
- Metadata editor.
- Usage history.
- Related assets.

**Navigation Rules:**
- Default: grid view sorted by last modified.
- Filter by type, tag, status, date.
- Collection/tag-based organization.

---

## 15. System Workspace

**Purpose:** System administration, configuration, and governance. Not for everyday use.

**Visible Information:**
- System status and health
- Configuration settings
- User management
- Access control
- Audit log
- Integration management
- Usage statistics

**Interaction Rules:**
- Admin-only access.
- All changes are logged.
- Configuration changes require confirmation.
- No destructive actions without multi-step verification.

**AI Behavior:**
- AI monitors system health: "No anomalies detected."
- AI alerts on security events.
- AI can suggest configuration improvements.
- AI provides system usage reports.

**Expandable Regions:**
- Per-configuration-section detail.
- Audit log with filters.
- User management detail.
- Integration configuration.

**Navigation Rules:**
- Default: system status overview.
- Sections organize configuration by domain.
- Hidden from non-admin users by default.

---

## 16. Workspace Invariants

1. **Every workspace has the same three-zone layout.** Only content varies.
2. **Every workspace is business-agnostic.** No travel, CRM, ERP, or industry-specific assumptions.
3. **Every workspace centers on an object type.** There is no workspace without a primary object class.
4. **Every workspace supports object relationships.** Objects connect within and across workspaces.
5. **Every workspace has an AI Resident.** AI is always present, always contextual.
6. **Every workspace is accessible from the workspace switcher.** No hidden workspaces (except System, which is role-gated).
7. **Workspaces are not hierarchical.** No workspace contains another workspace. They coexist.
8. **Custom workspaces are possible but inherit the canonical architecture.** Custom workspaces are extensions, not replacements.
9. **A user's workspace set is configurable.** Users hide workspaces they do not use. The canonical 14 are the full set.
10. **Workspace state is preserved.** Switching away and back restores exact state.