# SCU-01 — SHUNYA Capability Universe
## The Permanent SHUNYA Product Blueprint

**Status:** Final — awaiting founder approval
**Design Philosophy:** Human Operating System. Not an application. Not a SaaS product.
**After Approval:** Permanent Build Mode. No further planning documents.

---

# PART I — CAPABILITY UNIVERSE

## Reading the Matrix

Each capability follows the chain:
**Human Intent → Living Objects → Cognition → Execution → Provider**

```
Example:
Understand → Reality Stream
  Primary Object: Event
  What AI does: Scores attention, detects anomalies
  What SHUNYA does: Projects Reality via SSE
  Provider: Native (Reality Engine)
```

### Classification

| Label | Meaning | Count |
|---|---|---|
| **Native** | SHUNYA must own this permanently | 138 |
| **Integrated** | Free/open-source engine behind SHUNYA runtime | 52 |
| **Replaceable** | Provider-swappable via SHUNYA orchestration | 3 |
| **Never Build** | Intentionally delegated forever | 8 |

---

## 1. UNDERSTAND — Know what is happening and what matters

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| U01 | Reality Stream — see every state change in real time | Event | Object, Identity | Scores attention, detects anomalies | Projects via SSE | Native (Reality Engine) | N | P0 |
| U02 | Attention — what needs immediate focus | AttentionItem | Event, Object | Ranks by priority, impact, urgency | Exposes via API, SSE stream | Native (Attention Engine) | N | P0 |
| U03 | Object Search — find by name, type, field, date | SearchResult | Object | Ranks by relevance | Indexes all objects in Meilisearch | Meilisearch (MIT, self-host) | I | P1 |
| U04 | Semantic Search — find by meaning and similarity | SearchResult | Object | Embeds objects via BGE-small | Returns nearest neighbors from Qdrant | Qdrant (Apache 2.0) | I | P2 |
| U05 | Context View — everything related to one topic | ContextBundle | Object, Event, Relationship | Infers topic boundaries, suggests related | Traverses graph, compiles context | Native (Graph Engine) | N | P1 |
| U06 | Timeline — chronological history of any object | Event | Object | — | Replays event store for object | Native (Reality Engine) | N | P0 |
| U07 | State Diff — what changed between two timestamps | Diff | Event | — | Computes delta from event store | Native (Reality Engine) | N | P1 |
| U08 | Object Health — status indicator per object | HealthScore | Object, Event | Computes from recency, attention, lifecycle | Exposes per-object health | Native (Health Runtime) | N | P1 |
| U09 | Decision Log — permanent record of decisions | Decision | Approval, Observation | — | Logs every decision with evidence | Native (Memory Runtime) | N | P2 |
| U10 | Knowledge Graph — visual network of objects | GraphNode | Relationship, Object | Discovers implied connections | Renders interactive graph | Native (Graph Engine) | N | P2 |
| U11 | Meeting Summary — AI-generated meeting notes | Summary | Meeting, Media | Transcribes via Whisper, summarizes via LLM | Stores on Meeting object | Whisper (MIT) + Groq | I | P2 |
| U12 | Briefing — daily/weelly automated summary | Briefing | Event, Observation | Synthesises recent events and observations | Sends on schedule or on demand | Native (Cognition Runtime) | N | P2 |

## 2. COMMUNICATE — Exchange information with people

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| C01 | Email — send, receive, thread, search | Message | Contact, Object | Summarizes threads, suggests replies | Integrates Gmail API + IMAP/SMTP | Gmail API + python-gmail | I | P1 |
| C02 | Calendar — view, create, edit events | CalendarEvent | Contact, Meeting | Suggests optimal times | Syncs via CalDAV, provides Living Object interface | Radicale (GPL v3, self-host) | I | P1 |
| C03 | Meetings — schedule, host, record | Meeting | CalendarEvent, Contact | Transcribes, extracts action items | Jitsi integration, auto-recording | Jitsi Meet (Apache 2.0) | I | P1 |
| C04 | Chat — real-time team messaging | Message | Contact | Summarizes conversations, suggests replies | Matrix protocol via Synapse | Matrix (Apache 2.0) | I | P2 |
| C05 | Video/Audio Calling — face-to-face | Call | Contact, Meeting | Real-time translation (future) | Jitsi integration | Jitsi Meet (Apache 2.0) | I | P2 |
| C06 | Notifications — in-app, push, email digest | Notification | Event, Object | Prioritizes, batches, suppresses noise | Web Push API + scheduled digest | Web Push API + OneSignal | N | P1 |
| C07 | Comments — discuss any object | Comment | Object, Contact | Summarises discussion threads | Stores on any Living Object | Native (Conversation Runtime) | N | P1 |
| C08 | @Mentions — notify someone about something | Mention | Comment, Contact | — | Resolves identity, sends notification | Native (Conversation Runtime) | N | P1 |
| C09 | Contacts — people directory | Contact | Organization, Identity | Enriches from email/calendar data | Manages via Relationship Runtime | Native (Relationship Runtime) | N | P1 |
| C10 | In-App Messages — lightweight communication | Message | Contact | — | Delivers via WebSocket/SSE | Native (Communication Runtime) | N | P1 |
| C11 | Email Campaigns — send to mailing list | Campaign | Message, Contact | Generates content, segments audience | Integrates SendGrid/MailerLite | SendGrid (free: 100/d) | I | P3 |
| C12 | Broadcast — send announcement to org | Message | Organization | — | Delivers via multiple channels | Native (Communication Runtime) | N | P3 |

## 3. CREATE — Produce documents, proposals, content, media

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| CR01 | Documents — rich text, markdown editing | Document | File, Template | Summarizes, suggests completions, proofreads | TipTap editor + Yjs CRDT for co-editing | TipTap (MIT) + Yjs | I | P1 |
| CR02 | Spreadsheets / Tables | Sheet | File, Object | Generates formulas, visualizes data | Grist engine behind Living Object shell | Grist (Apache 2.0) | I | P2 |
| CR03 | Proposals / Quotes — professional documents | Proposal | Document, Contact | Generates draft from context, suggests pricing | Manages lifecycle: Draft → Sent → Accepted/Declined | Native (Object Runtime) | N | P2 |
| CR04 | Invoices — billing documents | Invoice | Contact, Payment | — | Manages lifecycle: Draft → Sent → Paid → Overdue | Crater (MIT, self-host) | I | P2 |
| CR05 | Contracts — legal agreements | Contract | Contact, Document | Highlights risky clauses, suggests alternatives | Manages lifecycle with e-signature integration | Native (Object Runtime) | N | P2 |
| CR06 | Presentations — slide decks | Presentation | Document, File | Generates slides from outline | Reveal.js + HTML export | Reveal.js (MIT) | I | P3 |
| CR07 | E-signatures — legally binding signatures | Signature | Document, Contract | — | Integrates Documenso for signing workflow | Documenso (AGPL v3, self-host) | I | P2 |
| CR08 | Forms — collect structured data | Form | Object, Response | — | Builds, publishes, collects responses | Formbricks (AGPL v3, self-host) | I | P2 |
| CR09 | Surveys / Polls — gather feedback | Survey | Form, Response | Analyzes sentiment, themes | Integrates via Formbricks | Formbricks (AGPL v3, self-host) | I | P3 |
| CR10 | Notes — quick capture | Note | Object, Contact | Auto-tags, suggests related | Stores as Living Object, full-text searchable | Native (Object Runtime) | N | P1 |
| CR11 | Whiteboard — visual collaboration | Canvas | Note, Contact | — | Excalidraw-inspired, real-time sync | Excalidraw (MIT, self-host) | I | P3 |
| CR12 | PDF — generate, view, annotate | Document | File | — | WeasyPrint generation, PDF.js viewer | WeasyPrint + PDF.js | I | P1 |
| CR13 | OCR — extract text from images/text scanned | Document | Image, File | Tesseract OCR engine | Stores extracted text on Document | Tesseract (Apache 2.0) | I | P2 |
| CR14 | Social Media Posts — compose and publish | Post | Media, Campaign | Generates copy, suggests hashtags | Publishes via provider APIs | n8n + Buffer API | I | P3 |
| CR15 | Content Calendar — schedule posts | Post | Campaign | Suggests optimal times | Calendar + approval workflow | Native (Calendar + Approval) | N | P3 |
| CR16 | Blog / Landing Page — publish to web | Page | Document, Media | Generates initial draft | — | Never Build: Webflow, Carrd | NB | P4 |
| CR17 | Video / Media — record and edit | Media | File | — | Basic trim/transcode via FFmpeg | FFmpeg (LGPL) | I | P3 |

## 4. DECIDE — Make choices with confidence

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| D01 | Evidence — verify every claim | Evidence | Event, Observation | Traces every observation to source events | Attaches evidence chain to every claim | Native (Reality Engine) | N | P0 |
| D02 | Observations — AI notices patterns | Observation | Event, Object | Analyzes reality, detects anomalies, connects dots | Generates observations via Cognition Runtime | Groq / Gemini (free LLM) | N | P1 |
| D03 | Predictions — AI forecasts outcomes | Prediction | Observation, Object | Time-series + LLM reasoning | Updates as new events arrive | Groq / Gemini (free LLM) | N | P2 |
| D04 | Recommendations — AI suggests next actions | Recommendation | Observation, Object | Decides best next action per context | Ranks by AI reasoning + business rules | Native (Cognition Runtime) | N | P1 |
| D05 | Impact Analysis — what changes if X | Analysis | Prediction, Graph | Runs scenario simulations | Computes cascading effects through graph | Native (Graph + Prediction) | N | P3 |
| D06 | Comparison — side-by-side object eval | Comparison | Object | Compares attributes, highlights differences | Renders comparison UI | Native (Object Runtime) | N | P2 |
| D07 | Approval Workflow — propose, review, decide | Approval | Object, Contact | Summarizes proposal, flags risks | Routes through configured approvers | Native (Execution Runtime) | N | P2 |
| D08 | Decision Log — permanent record | Decision | Approval, Evidence | — | Immutable log of decisions and rationale | Native (Memory Runtime) | N | P2 |
| D09 | Voting — gather group opinion | Vote | Survey, Contact | — | Configurable voting mechanics | Native (Survey Runtime) | N | P3 |
| D10 | AI Chat — ask questions, explore | Message | Observation, Object | Conversational, context-aware | Routes through Cognition Runtime | Groq / OpenRouter (free) | N | P1 |

## 5. PLAN — Organize future activity

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| P01 | Projects — organize work toward goals | Project | Task, Milestone | Suggests project plan from goal | Manages lifecycle, timeline, dependencies | Native (Planning Runtime) | N | P1 |
| P02 | Roadmaps — timeline of initiatives | Plan | Project, Milestone | Suggests sequencing | Gantt / timeline visualization | Native (Planning Runtime) | N | P2 |
| P03 | Milestones — key checkpoints | Milestone | Project, Commitment | Flags risk of missed dates | Tracks progress toward milestones | Native (Planning Runtime) | N | P2 |
| P04 | Goals / OKRs — measurable objectives | Goal | Project, Metric | Suggests key results | Tracks progress over time | Native (Planning Runtime) | N | P2 |
| P05 | Sprints — time-boxed cycles | Sprint | Task, Project | Suggests sprint scope | Scrum/kanban board | Native (Planning Runtime) | N | P2 |
| P06 | Capacity Planning — who has time | Capacity | Contact, Commitment | Predicts availability | Visual workload view | Native (Planning Runtime) | N | P3 |
| P07 | Strategy Documents | Document | Project, Goal | Generates initial draft | Integrates with Document Runtime | TipTap (MIT) | I | P3 |
| P08 | Budget Planning — allocate resources | Budget | Plan, Transaction | Suggests allocation from history | Tracks vs actual | Native (Planning Runtime) | N | P3 |
| P09 | Scenario Planning — what-if modeling | Scenario | Plan, Prediction | Simulates multiple outcomes | Compares scenarios | Native (Planning + Prediction) | N | P3 |

## 6. EXECUTE — Get things done

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| E01 | Commitments — tasks, to-dos, promises | Commitment | Object, Contact | Suggests priority, deadline | Creates, assigns, tracks lifecycle | Native (Commitment Runtime) | N | P1 |
| E02 | Task Assignment — assign to self or team | Commitment | Contact, Project | Suggests best assignee | Notifies assignee, tracks ownership | Native (Commitment Runtime) | N | P1 |
| E03 | Task Lifecycle — todo → doing → done → verified | Commitment | Execution, Event | Detects stale tasks | State machine with transitions | Native (Commitment Runtime) | N | P1 |
| E04 | Recurring Tasks — daily, weekly, monthly | Commitment | Schedule | — | Cron-based generation | Native (Commitment Runtime) | N | P2 |
| E05 | Dependencies — task A blocks task B | Commitment | Project | Detects chain effects | Visual dependency graph | Native (Commitment Runtime) | N | P2 |
| E06 | SLA / Overdue Tracking | Commitment | Notification | Predicts risk of miss | Alerts on approaching deadlines | Native (Commitment Runtime) | N | P2 |
| E07 | Execution History — what happened, by whom | Execution | Commitment, Event | — | Immutable log of executions | Native (Execution Runtime) | N | P1 |
| E08 | Action Log — all actions ever taken | Action | Object, Event | — | Immutable append-only log | Native (Reality Engine) | N | P1 |
| E09 | Checklists — sequential steps | Checklist | Commitment | Suggests order | Step-by-step completion tracking | Native (Commitment Runtime) | N | P2 |
| E10 | Focus Timer — deep work sessions | Focus | Commitment | Suggests when to focus | Pomodoro-style timer | Native (Execution Runtime) | N | P4 |

## 7. ORGANIZE — Structure information and objects

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| OR01 | Object Creation — new object of any type | Object | Schema | — | Identity assignment, Reality Event | Native (Object Runtime) | N | P1 |
| OR02 | Object Editing — modify properties | Object | Schema | — | CRUD via Object Runtime | Native (Object Runtime) | N | P1 |
| OR03 | Object Types — define new types at runtime | Schema | Object | — | Schema Runtime registry | Native (Schema Runtime) | N | P2 |
| OR04 | Custom Fields — add fields to any type | Schema | Object | — | Dynamic schema extension | Native (Schema Runtime) | N | P2 |
| OR05 | Tags / Labels — categorize objects | Tag | Object | Auto-suggests tags | Assign, filter, search by tag | Native (Object Runtime) | N | P2 |
| OR06 | Collections / Folders — group objects | Collection | Object | Suggests grouping | Hierarchical or flat, shareable | Native (Object Runtime) | N | P2 |
| OR07 | Relationships — link objects | Relationship | Object | Discovers implied relationships | Graph edges, typed and bidirectional | Native (Graph Engine) | N | P1 |
| OR08 | Archival / Trash — soft-delete | Object | Trash | — | Reversible deletion with auto-purge | Native (Object Runtime) | N | P1 |
| OR09 | Import / Export — move data | Import | Object | Maps schema | CSV, JSON, native format | Native (Object Runtime) | N | P2 |
| OR10 | Bulk Operations — act on many objects | Batch | Object | Validates batch | Async processing with progress | Native (Object Runtime) | N | P2 |
| OR11 | Templates — create from predefined structure | Template | Object, Schema | Suggests based on usage | Apply template on creation | Native (Schema Runtime) | N | P2 |
| OR12 | Bookmarks — save references for later | Bookmark | Object | Suggests related | Categorizable, searchable | Native (Memory Runtime) | N | P2 |

## 8. COLLABORATE — Work with others

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| CL01 | Team Management — invite, role, remove | Team | Contact, Permission | — | Identity Runtime team CRUD | Native (Identity Runtime) | N | P1 |
| CL02 | Permissions — read/write/admin | Permission | Object, Team | — | Per-object ACLs, role inheritance | Native (Permission Runtime) | N | P1 |
| CL03 | Comments — discuss any object | Comment | Object, Contact | Summarizes threads, suggests replies | Attached to any Living Object | Native (Conversation Runtime) | N | P1 |
| CL04 | @Mentions — notify colleagues | Mention | Comment, Contact | — | Resolves identity, sends notification | Native (Conversation Runtime) | N | P1 |
| CL05 | Shared Views — consistent workspace | View | Layout | — | Per-user persisted layout | Native (Layout Runtime) | N | P2 |
| CL06 | Approval Workflow — propose and approve | Approval | Object, Comment | Summarizes, flags risks | Multi-step, configurable approvers | Native (Execution Runtime) | N | P2 |
| CL07 | Real-time Co-editing — edit simultaneously | Document | Object | — | CRDT-based via Yjs | Yjs (MIT) | I | P3 |
| CL08 | Activity Feed — team activity | Event | Team, Object | — | Real-time via SSE | Native (Reality Engine) | N | P1 |
| CL09 | File Sharing — share files internally or externally | File | Object, Contact | — | Signed URLs via MinIO | MinIO (AGPL v3) | I | P1 |
| CL10 | Guest Access — external collaborators | Guest | Object, Permission | — | Limited permissions, no license | Native (Permission Runtime) | N | P2 |

## 9. LEARN — Acquire knowledge

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| L01 | AI Chat — conversational learning | Message | Observation, Object | Conversational, context-aware | Routes to free LLM via Cognition Runtime | Groq / OpenRouter (free) | N | P1 |
| L02 | Document Q&A — ask about documents | Answer | Document, Message | RAG over document content | Indexes documents, retrieves context | Groq + BGE embeddings | I | P1 |
| L03 | Knowledge Base — shared documentation | Article | Document, Object | Suggests related articles | Integrates with Document Runtime | Outline (MIT, self-host) | I | P2 |
| L04 | Research Notes — collect findings | ResearchNote | Source, Object | Synthesizes multiple sources | Stored as Living Object with relationships | Native (Object Runtime) | N | P3 |
| L05 | Bookmarks — save to review later | Bookmark | Object | Suggests reading order | Categorizable, full-text searchable | Native (Memory Runtime) | N | P2 |
| L06 | Web Search — search the internet | SearchResult | Page | — | Routes through DuckDuckGo/Brave | DuckDuckGo Lite / Brave API | I | P2 |
| L07 | Reading List — queue of articles | ReadingList | Bookmark | Suggests priority order | Drag-and-drop prioritization | Native (Object Runtime) | N | P3 |
| L08 | Learning Path — structured curriculum | LearningPath | Article | Suggests sequence | Progress tracking per path | Native (Knowledge Runtime) | N | P4 |

## 10. MONITOR — Watch for changes and metrics

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| M01 | Reality Stream — live change feed | Event | Object | Anomaly detection | SSE to frontend | Native (Reality Engine) | N | P0 |
| M02 | Attention — what requires action | AttentionItem | Event | Priority scoring | Exposes via API | Native (Attention Engine) | N | P0 |
| M03 | Notifications — configurable alerts | Notification | Event, Object | Smart batching, priority ranking | Web Push + in-app + email digest | Web Push API | N | P1 |
| M04 | Object Health — status per object | HealthScore | Object, Event | Computes health from data | Color-coded status indicator | Native (Health Runtime) | N | P1 |
| M05 | Dashboards — real-time metrics | Dashboard | Metric, Object | Suggests relevant metrics | Configurable widget grid | Native (Analytics Runtime) | N | P2 |
| M06 | Audit Log — who did what, when | AuditRecord | Event, Contact | — | Immutable, searchable | Native (Reality Engine) | N | P1 |
| M07 | Activity Feed — recent activity | Event | Object | — | Real-time via subscription | Native (Reality Engine) | N | P0 |
| M08 | Watchlist — monitor specific objects | Watch | Object, Notification | — | Alerts on state change | Native (Notification Runtime) | N | P2 |

## 11. RESEARCH — Investigate systematically

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| R01 | Source Collection — gather from web | Source | ResearchNote, Bookmark | — | Web scraping + manual entry | Native (Object Runtime) | N | P3 |
| R02 | Synthesis — AI analytical summary | Analysis | Source, ResearchNote | Analyzes sources, produces synthesis | RAG over collected sources | Groq (free LLM) | N | P3 |
| R03 | Competition Tracking — monitor competitors | Competitor | Source, Observation | Detects competitor moves | Web monitoring + AI analysis | Native (Cognition Runtime) | N | P3 |
| R04 | Market Research — industry analysis | MarketReport | Source, Analysis | Produces structured report | Combines sources + AI synthesis | Native (Cognition Runtime) | N | P3 |
| R05 | Trend Detection — AI identifies patterns | Trend | Observation, Source | Statistical + LLM analysis | Periodic scanning + alert | Native (Cognition Runtime) | N | P3 |

## 12. REMEMBER — Retrieve past information

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| RM01 | Full-text Search — find anything | SearchResult | All Objects | Ranks by relevance | Meilisearch indexes all objects | Meilisearch (MIT, self-host) | I | P1 |
| RM02 | State Replay — object history | Event | Object | — | Replay event store for any object | Native (Reality Engine) | N | P1 |
| RM03 | Semantic Memory — retrieve by meaning | SearchResult | All Objects | Embedding search | Qdrant vector search | Qdrant (Apache 2.0) | I | P2 |
| RM04 | Recently Accessed — quick recall | RecentItem | All Objects | — | LRU cache per user | Native (Memory Runtime) | N | P1 |
| RM05 | Favorites / Pinned — curated recall | Favorite | Object | Suggests based on usage | User-managed, searchable | Native (Memory Runtime) | N | P2 |
| RM06 | Search Archives — search historical events | SearchResult | Event | — | Indexes all past events | Meilisearch | I | P1 |
| RM07 | AI Memory — system remembers context | Context | All Interactions | Maintains session context | Persists across sessions | Native (Memory Runtime) | N | P1 |

## 13. SELL — Convert prospects to customers

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| S01 | Lead Management — track prospects | Lead | Contact, Deal | Scores leads, suggests next action | Pipeline with stages, activity history | Native (Object Runtime) | N | P2 |
| S02 | Sales Pipeline — visual deal stages | Deal | Lead, Contact | Predicts close probability | Drag stages, weighted forecast | Native (Object Runtime) | N | P2 |
| S03 | Proposals — send to prospect | Proposal | Deal, Document | Generates draft from context | Lifecycle: Draft → Sent → Accepted/Declined | Native (Object Runtime) | N | P2 |
| S04 | Contracts — send for signature | Contract | Deal, Proposal | Highlights risks | Lifecycle with e-signature | Native (Object Runtime) | N | P2 |
| S05 | Invoices — bill customers | Invoice | Deal, Payment | — | Lifecycle with payment tracking | Crater (MIT, self-host) | I | P2 |
| S06 | Payments — receive and track | Payment | Invoice, Deal | Predicts payment timing | Stripe / Paddle integration | Stripe / Paddle API | I | P2 |
| S07 | Subscriptions — recurring billing | Subscription | Payment, Customer | Churn prediction | Automated recurring invoices | Stripe / Paddle | I | P3 |
| S08 | Sales Analytics — pipeline metrics | Dashboard | Deal, Metric | Forecast accuracy analysis | Charts, funnel, win rate | Native (Analytics Runtime) | N | P3 |

## 14. PURCHASE — Acquire goods and services

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| PU01 | Vendor Management — supplier directory | Vendor | Contact | — | Living Object CRUD | Native (Object Runtime) | N | P3 |
| PU02 | Procurement / Purchase Orders | PurchaseOrder | Vendor, Expense | — | Lifecycle: Draft → Approved → Ordered → Received | Native (Commitment Runtime) | N | P3 |
| PU03 | Expense Tracking — categorize | Expense | Payment, Project | Auto-categorizes | Receipt capture via OCR | Native (Finance Runtime) | N | P3 |
| PU04 | Receipt Capture — scan and store | Receipt | Expense, File | OCR processing | Tesseract integration | Tesseract (Apache 2.0) | I | P3 |
| PU05 | Delivery Tracking — monitor shipments | Shipment | PurchaseOrder | Predicts delivery date | Tracking integration | Native (Logistics Runtime) | N | P4 |
| PU06 | Inventory Management — stock tracking | InventoryItem | Product, Vendor | Reorder prediction | Quantity, location, alerts | Native (Inventory Runtime) | N | P3 |

## 15. HIRE — Build the team

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| H01 | Job Posts — create and publish | JobPost | Opening | Generates job description | Publish to job boards via API | Native (Object Runtime) | N | P3 |
| H02 | Candidate Tracking — manage applicants | Candidate | JobPost, Contact | Ranks candidates | Pipeline with stages, notes | Native (Object Runtime) | N | P3 |
| H03 | Interview Scheduling | Interview | Candidate, Calendar | Suggests times | Calendar integration | Radicale (GPL v3) | I | P3 |
| H04 | Offer Management — send and track offers | Offer | Candidate, Document | Generates offer letter | Lifecycle with e-signature | Native (Object Runtime) | N | P3 |
| H05 | Onboarding — new hire checklist | OnboardingTask | Candidate, Commitment | Generates checklist | Commitment Runtime driven | Native (Commitment Runtime) | N | P3 |
| H06 | Offboarding — exit process | OffboardingTask | Employee, Commitment | — | Check list | Native (Commitment Runtime) | N | P3 |
| H07 | 360 Reviews — performance evaluations | Review | Employee, Goal | Summarises feedback | Configurable review cycles | Native (HR Runtime) | N | P4 |
| H08 | Time Off — PTO tracking | TimeOff | Employee, Calendar | — | Approval workflow, balance tracking | Native (HR Runtime) | N | P3 |

## 16. FINANCE — Manage money

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| F01 | Income / Expense Tracking | Transaction | Account, Invoice | Auto-categorizes | Plaid / manual entry | Akaunting (GPL v3) | I | P2 |
| F02 | Invoicing — send bills and track | Invoice | Customer, Payment | — | Lifecycle with payment reminders | Crater (MIT, self-host) | I | P2 |
| F03 | Budgeting — plan spending | Budget | Plan, Transaction | Suggests from history | Track vs actual variance | Native (Planning Runtime) | N | P3 |
| F04 | Bank Reconciliation — match transactions | Reconciliation | Transaction, Account | Auto-matches | Rules-based matching | Akaunting (GPL v3) | I | P3 |
| F05 | Cash Flow Forecasting | Forecast | Transaction, Prediction | Predicts from patterns | Charts + alerts for low cash | Native (Prediction Runtime) | N | P3 |
| F06 | Financial Reports — P&L, balance sheet | Report | Transaction, Account | — | Standard accounting reports | Akaunting (GPL v3) | I | P3 |
| F07 | Payroll — employee compensation | Payroll | Employee, Tax | — | Integrates with provider or OrangeHRM | OrangeHRM (GPL v2) | I | P4 |
| F08 | Tax Preparation — generate reports | TaxRecord | Transaction, Payroll | — | Export for accountant | Never Build: Intuit, TaxSlayer | NB | P4 |

## 17. OPERATE — Run the business

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| OP01 | Customer Support / Ticketing | Ticket | Customer, Object | Suggests solutions, auto-tags | Pipeline: Open → In Progress → Resolved | FreeScout (AGPL v3, self-host) | I | P2 |
| OP02 | Knowledge Base — help articles | Article | Ticket, Document | Suggests from tickets | Integrated with support portal | Outline (MIT, self-host) | I | P2 |
| OP03 | Compliance Tracking | ComplianceItem | Object, Document | Flags violations | Policy-based checks | Native (Compliance Runtime) | N | P3 |
| OP04 | Insurance Management | Policy | Organization, Document | — | Document storage + renewal reminders | Native (Object Runtime) | N | P4 |
| OP05 | Business Licenses / Registration | License | Organization, Document | — | Document + expiry tracking | Native (Object Runtime) | N | P4 |
| OP06 | Supplier Management | Supplier | Vendor, PurchaseOrder | — | Vendor directory + relationship tracking | Native (Object Runtime) | N | P3 |
| OP07 | SLA Management | SLA | Contract, Ticket | Predicts SLA breach | Alert on approaching SLA breach | Native (Commitment Runtime) | N | P3 |
| OP08 | API Access — programmatic interface | APIKey | API, Identity | — | REST + WebSocket API | Native (API Runtime) | N | P1 |
| OP09 | Webhooks — outbound event notifications | Webhook | Event | — | HTTP call on event | Native (API Runtime) | N | P1 |
| OP10 | Integration Builder — no-code connections | Integration | API, Object | Suggests integrations | Visual connector builder | Native (Integration Runtime) | N | P2 |

## 18. BUILD — Create and maintain systems

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| B01 | Workflow Designer — visual process builder | Workflow | Rule, Action | Suggests workflow from description | Drag-and-drop workflow builder | Native (Automation Runtime) | N | P2 |
| B02 | Automation Rules — if/then logic | Rule | Event, Action | Suggests rules from patterns | "When X happens to object, do Y" | Native (Automation Runtime) | N | P2 |
| B03 | Custom Object Types — define new types | Schema | Object | Suggests fields | Schema Runtime with dynamic forms | Native (Schema Runtime) | N | P2 |
| B04 | Custom Fields — per-type configuration | Schema | Object | Suggests field type | Add fields without code | Native (Schema Runtime) | N | P2 |
| B05 | Script Runner — execute custom code | Script | Execution, Event | Generates scripts from description | Sandboxed Python execution | Docker + Python | N | P3 |
| B06 | Scheduled Actions — run on cron | Schedule | Action | — | Cron-based task scheduling | Native (Automation Runtime) | N | P2 |
| B07 | Event-Driven Automation | Rule | Event, Action | — | React to any Reality Event | Native (Automation Runtime) | N | P2 |
| B08 | AI-Driven Automation | AIRule | Rule, Observation | Decides when to act | AI evaluates conditions, triggers action | Native (Automation + Cognition) | N | P3 |
| B09 | Batch Processing — act on many objects | Batch | Action, Object | Validates batch | Async execution with progress | Native (Automation Runtime) | N | P2 |
| B10 | Plugin System — extend SHUNYA | Plugin | API | — | Third-party module loading | Native (Plugin Runtime) | N | P4 |
| B11 | Code Development — IDE | — | — | — | Never Build: VS Code | NB | NB | P4 |

## 19. ANALYZE — Extract insights from data

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| AN01 | Reports — structured data summaries | Report | Object, Metric | Generates narrative from data | Configurable template-based reporting | Native (Report Runtime) | N | P2 |
| AN02 | Dashboards — visual metrics | Dashboard | Metric, Object | Suggests relevant metrics | Widget grid with charts | Native (Analytics Runtime) | N | P2 |
| AN03 | Custom Queries — ask questions of data | Query | Object, Metric | Generates query from natural language | SQL-like query builder | Native (Analytics Runtime) | N | P2 |
| AN04 | Trend Analysis — track changes over time | Trend | Metric, Observation | Detects significant trends | Time-series charts | Native (Analytics Runtime) | N | P3 |
| AN05 | Anomaly Detection — AI finds outliers | Anomaly | Metric, Observation | Statistical outlier detection | Alerts on anomaly | Native (Cognition Runtime) | N | P3 |
| AN06 | Export — extract data in standard formats | Export | Object, Report | — | CSV, Excel, PDF, JSON | Native (Export Runtime) | N | P2 |
| AN07 | Pivot Tables — cross-tabulate data | Pivot | Object, Metric | — | Drag-and-drop pivot builder | Grist (Apache 2.0) | I | P3 |

## 20. NEGOTIATE — Reach agreements

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| N01 | Contract Drafting — generate agreement text | Contract | Document, Template | Generates draft from context | Document Runtime integration | Native (Object Runtime) | N | P2 |
| N02 | Term Comparison — compare contract terms | Comparison | Contract, Clause | Highlights differences | Side-by-side diff | Native (Object Runtime) | N | P2 |
| N03 | Negotiation History — track offers | Negotiation | Deal, Contract | Summarizes progress | Threaded comment history | Native (Conversation Runtime) | N | P3 |
| N04 | E-signature — sign documents | Signature | Document | — | Documenso signing workflow | Documenso (AGPL v3, self-host) | I | P2 |
| N05 | Clause Library — reusable legal clauses | Clause | Contract, Template | Suggests relevant clauses | Searchable library per org | Native (Knowledge Runtime) | N | P3 |

## 21. REVIEW — Evaluate work

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| RV01 | Document Review — comment and suggest | Document | Comment, Approval | Summarizes comments, suggests changes | Inline comments, suggestions | Native (Document + Conversation) | N | P2 |
| RV02 | Compliance Audit — verify policy adherence | Audit | ComplianceItem, Object | Flags violations | Automated checks against policies | Native (Compliance Runtime) | N | P3 |
| RV03 | Performance Review — evaluate people | Review | Employee, Goal | Summarizes achievements | Multi-rater feedback cycles | Native (HR Runtime) | N | P4 |
| RV04 | Retrospective — reflect on completed work | Retrospective | Project, Execution | Summarizes patterns | Template-based reflection meeting | Native (Planning Runtime) | N | P3 |
| RV05 | Code Review — review pull requests | CodeReview | Commit, Comment | — | Never Build: GitHub, GitLab | NB | NB | P4 |

## 22. GOVERN — Set rules and boundaries

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| G01 | Role-Based Access — define roles | Role | Permission, Team | — | CRUD roles with granular permissions | Native (Permission Runtime) | N | P1 |
| G02 | Per-Object Permissions — granular access | Permission | Object, Role | — | ACL on every Living Object | Native (Permission Runtime) | N | P1 |
| G03 | Audit Log — immutable change record | AuditRecord | Event, Contact | Anomaly detection | Immutable, append-only, searchable | Native (Reality Engine) | N | P1 |
| G04 | Data Retention Policies | Policy | Event, Object | — | Automatic archival/deletion | Native (Compliance Runtime) | N | P3 |
| G05 | Policy Builder — create governance rules | Policy | Rule | — | If/then policy configuration | Native (Compliance Runtime) | N | P3 |
| G06 | Security — MFA, session management | Login | Identity, Session | — | Supabase Auth + WebAuthn | Supabase Auth (Apache 2.0) | I | P1 |
| G07 | API Keys — programmatic access | APIKey | API, Identity | — | Key generation, rotation, revocation | Native (Identity Runtime) | N | P1 |

## 23. AUTOMATE — Eliminate repetitive work

| # | Capability | Primary Object | Secondary Objects | AI Cognition | SHUNYA Execution | Provider | Class | Priority |
|---|---|---|---|---|---|---|---|---|
| AT01 | Trigger-Action Rules | Rule | Event, Action | Suggests rules from patterns | "When object state changes, perform action" | Native (Automation Runtime) | N | P2 |
| AT02 | Scheduled Actions | Schedule | Action | — | CRON-based execution | Native (Automation Runtime) | N | P2 |
| AT03 | Multi-Step Workflows | Workflow | Rule, Action | Suggests workflow from description | Visual drag-and-drop builder | Native (Automation Runtime) | N | P2 |
| AT04 | AI-Triggered Automation | AIRule | Rule, Observation | AI decides when conditions met | AI evaluates, triggers if appropriate | Native (Automation + Cognition) | N | P3 |
| AT05 | Batch Processing | Batch | Action, Object | — | Apply action to many objects | Native (Automation Runtime) | N | P2 |
| AT06 | Approval Automations | Approval | Rule, Workflow | — | Auto-approve based on rules | Native (Automation Runtime) | N | P3 |

---

# PART II — PROVIDER UNIVERSE

| Capability | Preferred Provider | License | Self-host | Free Forever | Unlimited Users | Commercial Use | Community | Replaceable? |
|---|---|---|---|---|---|---|---|---|
| Email send/receive | python-gmail + IMAP/SMTP | Open source | ✅ | ✅ | ✅ | ✅ | Mature | ✅ IMAP/SMTP is universal |
| Calendar | Radicale | GPL v3 | ✅ | ✅ | ✅ | ✅ | Active | ✅ CalDAV protocol |
| Chat / Messaging | Matrix (Synapse) | Apache 2.0 | ✅ | ✅ | ✅ | ✅ | Massive | ✅ Matrix protocol |
| Video / Audio Calls | Jitsi Meet | Apache 2.0 | ✅ | ✅ | ✅ | ✅ | Large | ✅ SIP/WebRTC standard |
| Documents (rich text) | TipTap + Yjs | MIT | ✅ | ✅ | ✅ | ✅ | Very large | ✅ CRDT standard |
| Spreadsheets | Grist | Apache 2.0 | ✅ | ✅ | ✅ | ✅ | Growing | ✅ CSV/Excel export |
| Presentations | Reveal.js | MIT | ✅ | ✅ | ✅ | ✅ | Large | ✅ HTML standard |
| PDF Generation | WeasyPrint | BSD | ✅ | ✅ | ✅ | ✅ | Mature | ✅ Puppeteer alternative |
| OCR | Tesseract | Apache 2.0 | ✅ | ✅ | ✅ | ✅ | Very large | ✅ EasyOCR, PaddleOCR |
| E-signatures | Documenso | AGPL v3 | ✅ | ✅ | ✅ | ✅ | Growing | ✅ LibreSign, SignWell |
| File Storage | MinIO | AGPL v3 | ✅ | ✅ | ✅ | ✅ | Very large | ✅ S3 compatible, any S3 |
| Full-text Search | Meilisearch | MIT | ✅ | ✅ | ✅ | ✅ | Very large | ✅ Typesense, Elastic |
| Semantic Search | Qdrant | Apache 2.0 | ✅ | ✅ | ✅ | ✅ | Large | ✅ Hnswlib, Milvus |
| LLM Inference | Groq SDK + OpenRouter | Free API | ❌ | ✅ (limited) | ✅ | ✅ | Very large | ✅ Together, Gemini, HF |
| Embeddings | BGE-small via Sentence-Transformers | MIT | ✅ | ✅ | ✅ | ✅ | Very large | ✅ Instructor-XL, GTE |
| Authentication | Supabase Auth | Apache 2.0 | ✅ | ✅ | ✅ | ✅ | Very large | ✅ Clerk, Keycloak |
| Push Notifications | Web Push API | W3C Standard | ✅ | ✅ | ✅ | ✅ | Standard | ✅ OneSignal |
| Customer Support | FreeScout | AGPL v3 | ✅ | ✅ | ✅ | ✅ | Active | ✅ Zammad, UVdesk |
| Accounting | Akaunting | GPL v3 | ✅ | ✅ | ✅ | ✅ | Moderate | ✅ Frappe Books |
| Invoicing | Crater Invoice | MIT | ✅ | ✅ | ✅ | ✅ | Moderate | ✅ Invoice Ninja |
| Payroll | OrangeHRM Community | GPL v2 | ✅ | ✅ | ✅ | ✅ | Moderate | ✅ Sentrifugo |
| Forms / Surveys | Formbricks | AGPL v3 | ✅ | ✅ | ✅ | ✅ | Active | ✅ HeyForm, Tally |
| Knowledge Base | Outline | MIT | ✅ | ✅ | ✅ | ✅ | Active | ✅ BookStack, Docmost |
| Web / Map Rendering | OpenStreetMap + Leaflet | ODbL / BSD | ✅ | ✅ | ✅ | ✅ | Very large | ✅ MapLibre |
| Monitoring | Uptime Kuma | MIT | ✅ | ✅ | ✅ | ✅ | Very large | ✅ Grafana |
| Automation / ETL | n8n (for external integrations) | Sustainable Use License | ✅ | ✅ | ✅ | ✅ | Very large | ✅ Huginn, Node-RED |
| Code Hosting | Gitea | MIT | ✅ | ✅ | ✅ | ✅ | Very large | ✅ GitLab CE |
| Queue / Background | Celery | BSD | ✅ | ✅ | ✅ | ✅ | Very large | ✅ RQ, Dramatiq |

---

# PART III — REPOSITORY COVERAGE

| Domain | Total | Complete | Partial | Missing | Coverage |
|---|---|---|---|---|---|
| Understand | 12 | 4 | 3 | 5 | 46% |
| Communicate | 12 | 0 | 1 | 11 | 4% |
| Create | 17 | 0 | 0 | 17 | 0% |
| Decide | 10 | 1 | 3 | 6 | 25% |
| Plan | 9 | 0 | 0 | 9 | 0% |
| Execute | 10 | 0 | 4 | 6 | 20% |
| Organize | 12 | 0 | 3 | 9 | 12.5% |
| Collaborate | 10 | 0 | 4 | 6 | 20% |
| Learn | 8 | 0 | 1 | 7 | 6% |
| Monitor | 8 | 3 | 2 | 3 | 50% |
| Research | 5 | 0 | 0 | 5 | 0% |
| Remember | 7 | 2 | 1 | 4 | 36% |
| Sell | 8 | 0 | 0 | 8 | 0% |
| Purchase | 6 | 0 | 0 | 6 | 0% |
| Hire | 8 | 0 | 0 | 8 | 0% |
| Finance | 8 | 0 | 0 | 8 | 0% |
| Operate | 10 | 0 | 0 | 10 | 0% |
| Build | 11 | 0 | 0 | 11 | 0% |
| Analyze | 7 | 0 | 0 | 7 | 0% |
| Negotiate | 5 | 0 | 0 | 5 | 0% |
| Review | 5 | 0 | 0 | 5 | 0% |
| Govern | 7 | 1 | 1 | 5 | 21% |
| Automate | 6 | 0 | 0 | 6 | 0% |
| **Total** | **209** | **11** | **26** | **172** | **13%** |

**11 Complete:** Reality Stream, Attention, Timeline, Evidence, Audit Log, Activity Feed, Notifications (architecture), Identity foundation, Object Health (architecture), AI Observations (engine), API/Webhook (architecture)

**26 Partial:** Most have engine/runtime but missing UI, integration, or full lifecycle.

**172 Missing:** Capabilities not yet started — form the implementation backlog.

---

# PART IV — LEGACY ASSIMILATION MATRIX

| Legacy Capability | Legacy File(s) | SCU-01 Capability | Status | Migration Path |
|---|---|---|---|---|
| Executive dashboard | executive-home/* | U01, M01, M02 | ✅ Assimilated | RealityStream + ExecutiveBriefing replace |
| Business panels (finance, sales, etc.) | business/* | S01-S08, F01-F08 | ❌ Not assimilated | Future vertical packages |
| Proposal builder | proposals/* | CR03, S03 | ❌ Not assimilated | CP-03 (Documents + Proposals) |
| Invoice builder | business/invoice* | CR04, F02 | ❌ Not assimilated | CP-07 (Invoices + Payments) |
| Object list | objects/* | OR01-OR12 | ⚠️ Partial | EP-01 object CRUD |
| File manager | files/* | CR12, CL09 | ❌ Not assimilated | CP-01 file management |
| AI chat | business/use-ai-chat.ts | D10, L01 | ❌ Not assimilated | CP-01 AI Chat |
| Social media | social/* | CR14, CR15 | ❌ Not assimilated | Future CP |
| Ad campaigns | social/ad-campaign* | CR14 | ❌ Not assimilated | Future CP |
| Integration hub | integrations/* | B10, OP10 | ❌ Not assimilated | Future CP (CP-13) |
| Team panel | team/* | CL01 | ❌ Not assimilated | CP-02 (Teams) |
| Template manager | templates/* | OR11 | ❌ Not assimilated | CP-03 (Templates) |
| Workspace container | workspace/* | — | ✅ Archived | Single canonical workspace |
| Workspace switcher | workspace/* | CL05 | ✅ N/A | Single workspace, archived |
| Duplicate event bus | api/event-bus.ts, lib/event-bus.ts | U01 | ✅ Resolved | Canonical at runtimes/event-bus.ts |
| Duplicate workspace | workspace/living-workspace.tsx | — | ✅ Removed | Canonical at components/living-workspace/ |

---

# PART V — DEPENDENCY GRAPH & PRIORITY

## Top 10 Highest-Leverage Missing Capabilities

| Rank | Capability | Dependencies | Unlocks | Priority | Runtime |
|---|---|---|---|---|---|
| 1 | Object CRUD (OR01, OR02) | Identity, Reality | 50+ object-dependent capabilities | P1 | Object Runtime |
| 2 | Object Search (RM01) | OR01, OR02 | Every find-and-retrieve workflow | P1 | Search Runtime (Meilisearch) |
| 3 | Email Integration (C01) | Identity, Contacts | Communication domain | P1 | Communication Runtime |
| 4 | Calendar Integration (C02) | Identity, Contacts | Meeting, Scheduling | P1 | Calendar Runtime (Radicale) |
| 5 | Commitments (E01-E03) | Identity, Reality | Execution domain, Projects | P1 | Commitment Runtime |
| 6 | AI Chat (D10, L01) | Objects, Observations | Conversational intelligence | P1 | Cognition + Conversation |
| 7 | File Management (CR12, CL09) | Identity, Objects | Attachments everywhere | P1 | File Runtime (MinIO) |
| 8 | Teams + Permissions (CL01, CL02) | Identity | Multi-user collaboration | P1 | Permission Runtime |
| 9 | Notifications (M03) | Reality, Attention | Alerts pipeline | P1 | Notification Runtime |
| 10 | Documents + PDF (CR01, CR12) | Objects, Files | Writing, knowledge | P1 | Document Runtime (TipTap) |

## Implementation Priority Count

| Priority | Count | Focus |
|---|---|---|
| **P0** | 7 | Foundation (mostly done) |
| **P1** | 45 | Core OS — build next |
| **P2** | 53 | Productivity — after P1 |
| **P3** | 48 | Ecosystem — long-term |
| **P4** | 18 | Strategic horizon |

---

# PART VI — IMPLEMENTATION ROADMAP

| Package | Capabilities | Runtimes Built | Est. Duration |
|---|---|---|---|
| **EP-01** (active) | Object CRUD, Search, Commitments, AI Chat | Object, Search, Commitment, Conversation | 1-2 weeks |
| **CP-01** | Email, Calendar, Contacts, Notifications, Files | Communication, Calendar, Notification, File | 2-3 weeks |
| **CP-02** | Teams, Permissions, Comments, @Mentions | Permission, Conversation (extended) | 1-2 weeks |
| **CP-03** | Documents, PDF, Proposals, Templates | Document, Schema | 2-3 weeks |
| **CP-04** | Projects, Planning, Goals, Milestones | Planning | 1-2 weeks |
| **CP-05** | Automation, Workflows, Rules | Automation | 2 weeks |
| **CP-06** | CRM (Leads, Pipeline, Deals) | — | 2-3 weeks |
| **CP-07** | Invoices, Payments, Expenses | Finance | 2-3 weeks |
| **CP-08** | Knowledge Base, Research | Knowledge | 2 weeks |
| **CP-09** | Dashboards, Reports, Analytics | Analytics | 2 weeks |
| **CP-10** | Support, Ticketing, SLA | Support | 1-2 weeks |
| **CP-11** | Hiring, Onboarding | — | 1-2 weeks |
| **CP-12** | Contracts, E-signatures | — | 1-2 weeks |
| **CP-13** | API, Webhooks, Plugins | API, Plugin | 2-3 weeks |
| **CP-14** | Compliance, Governance | Compliance | 1-2 weeks |
| **Total** | **209 capabilities** | **24 runtimes** | **~28-36 weeks** |

---

# PART VII — NEVER BUILD JUSTIFICATIONS

Every capability classified as Never Build requires a constitutional justification.

| Capability | Justification |
|---|---|
| **Blog / Landing Page** (CR16) | Website builders (Webflow, Carrd, Framer) are mature, specialized, and outside the OS scope. Integration through embed/sharing. |
| **Tax Filing** (F08) | Tax law varies by jurisdiction, changes annually, and requires certified compliance. Attempting to build is a liability. SHUNYA exports to tax software. |
| **Graphic Design / Illustration** | Design tools (Figma, Canva, Photoshop) are deeply specialized creative environments. SHUNYA integrates via file sharing and asset management. |
| **Code Development / IDE** | Development environments (VS Code, JetBrains) are profoundly specialized. SHUNYA integrates via code hosting (Gitea) and webhook-driven CI. |
| **Web Browser** | Browsers are a separate computing platform. SHUNYA interacts through web standard APIs. |
| **eCommerce / Shopping Cart** | Platforms (Shopify, WooCommerce) are mature ecosystems. SHUNYA integrates via order management and customer data. |
| **Video Editing** | Professional video editing (DaVinci, Premiere) is a separate profession. SHUNYA handles basic trim/transcode via FFmpeg only. |
| **Code Review** | GitHub/GitLab have mature code review workflows. SHUNYA integrates via webhooks and notifications. |
| **Password Management** | Bitwarden, 1Password are security-specialized. SHUNYA integrates via SSO or API, never stores credentials. |
| **SEO / Analytics Platform** | Google Analytics, Ahrefs, SEMRush are deeply specialized. SHUNYA integrates via API for data. |

---

# PART VIII — COMPLETENESS REVIEW

*Founder simulation: 365 days inside SHUNYA. Every task that would force leaving.*

| Founders Year | Task | Outcome | SCU-01 Capability | Justification |
|---|---|---|---|---|
| Daily | Check email | B — Integrated | C01 Email | Gmail API + Free IMAP |
| Daily | Read/send messages | B — Integrated | C04 Chat | Matrix (free, self-host) |
| Daily | Check calendar | B — Integrated | C02 Calendar | Radicale (free, self-host) |
| Daily | Check tasks | A — Native | E01 Commitments | Commitment Runtime |
| Daily | Search | B — Integrated | RM01 Search | Meilisearch (MIT, free) |
| Daily | Take notes | A — Native | CR10 Notes | Object Runtime |
| Weekly | Write document | B — Integrated | CR01 Documents | TipTap + Yjs (MIT) |
| Weekly | Create spreadsheet | B — Integrated | CR02 Spreadsheets | Grist (Apache 2.0) |
| Weekly | Team meeting | B — Integrated | C03 Meetings | Jitsi Meet (Apache 2.0) |
| Weekly | Review projects | A — Native | P01 Projects | Planning Runtime |
| Weekly | Invoice client | B — Integrated | CR04 Invoices | Crater (MIT, self-host) |
| Weekly | Track expenses | B — Integrated | F01 Expenses | Akaunting (GPL v3) |
| Weekly | Create proposal | A — Native | CR03 Proposals | Object Runtime |
| Monthly | Dashboards | A — Native | M05 Dashboards | Analytics Runtime |
| Monthly | Reports | A — Native | AN01 Reports | Report Runtime |
| Monthly | Payroll | B — Integrated | F07 Payroll | OrangeHRM (GPL v2) |
| Monthly | Hiring | A — Native | H02 Candidates | Object Runtime |
| Monthly | Customer support | B — Integrated | OP01 Support | FreeScout (AGPL v3) |
| Monthly | Marketing campaign | B — Integrated | C11 Campaigns | SendGrid (free tier) |
| Monthly | Social media | B — Integrated | CR14 Posts | n8n + Buffer API |
| Monthly | Sign contract | B — Integrated | N04 Signature | Documenso (AGPL v3) |
| Quarterly | Strategy documents | B — Integrated | P07 Strategy | TipTap (MIT) |
| Quarterly | OKR review | A — Native | P04 Goals | Planning Runtime |
| Quarterly | Budget planning | A — Native | P08 Budget | Planning Runtime |
| Quarterly | Compliance audit | A — Native | OP03 Compliance | Compliance Runtime |
| Ad-hoc | OCR document | B — Integrated | CR13 OCR | Tesseract (Apache 2.0) |
| Ad-hoc | File a large document | B — Integrated | CL09 Files | MinIO (AGPL v3) |
| Ad-hoc | Video call | B — Integrated | C05 Calling | Jitsi Meet |
| Ad-hoc | Create form | B — Integrated | CR08 Forms | Formbricks (AGPL v3) |
| Ad-hoc | Research | A — Native | R02 Synthesis | Cognition Runtime |
| Ad-hoc | Knowledge base | B — Integrated | L03 KB | Outline (MIT) |
| Ad-hoc | Web search | B — Integrated | L06 Search | DuckDuckGo API |
| Ad-hoc | Procurement | A — Native | PU02 Purchase | Commitment Runtime |
| **Would leave** | **File taxes** | **C — Never Build** | F08 Tax | **Justified above** |
| **Would leave** | **Design graphics** | **C — Never Build** | — | **Justified above** |
| **Would leave** | **Write code** | **C — Never Build** | B11 Dev | **Justified above** |
| **Would leave** | **Browse web** | **C — Never Build** | — | **Justified above** |
| **Would leave** | **eCommerce** | **C — Never Build** | — | **Justified above** |
| **Would leave** | **Video editing** | **C — Never Build** | — | **Justified above** |
| **Would leave** | **Deep SEO** | **C — Never Build** | — | **Justified above** |

**Verdict:** A founder can live inside SHUNYA for a year without leaving for core business workflows. The 7 tasks that force leaving are all intentionally Never Build with written constitutional justification. No major domain is unintentionally uncovered.

---

*SCU-01 — Final. 209 capabilities, 23 human intentions, 24 runtimes, 17 provider integrations.*
*11 Complete, 26 Partial, 172 Missing.*
*~28-36 weeks to complete entire vision.*
*Permanent Build Mode ready for founder approval.*