# SHUNYA PRODUCT EXPERIENCE CONSTITUTION — VERSION 2.0

> **Status:** Ratified
> **Constitutional Authority:** This document supersedes the Experience Bible v1.0. Every future frontend implementation shall be derived from this constitution. No future engineer, designer, AI agent, or founder shall need to ask "How should SHUNYA behave here?" — this constitution shall already answer it.
> **Classification Legend:** 🟢 Mandatory / 🟡 Recommended / 🔵 Optional / 🔴 Forbidden

---

## PREAMBLE — How To Use This Constitution

This constitution is organised into autonomous sections. Each section can be read independently. Every section ends with an **Implementation Mandate** that specifies which principles are mandatory, recommended, optional, or forbidden.

If an ambiguity is discovered during implementation, propose a constitutional amendment rather than making an arbitrary design decision. The amendment process is: identify the gap, propose the resolution, receive ratification, update the constitution.

---

## SECTION 1 — BRAND CONSTITUTION

### 1.1 Brand Philosophy
🟢 **SHUNYA is not software. SHUNYA is a living operating system for organisations.**

This is not marketing copy. This is the constitutional identity. Every design decision shall reinforce this identity. If a decision weakens it, the decision is wrong.

### 1.2 Brand Identity
🟢 **SHUNYA is:**
- Calm — does not compete for attention
- Intelligent — understands before being told
- Present — available without being intrusive
- Trustworthy — never hides intent
- Permanent — designed for years, not quarters

🟢 **SHUNYA is not:**
- Exciting — excitement implies unpredictability
- Urgent — urgency implies poor planning
- Complex — complexity implies bad design
- Corporate — corporateness implies inhumanity
- Playful — playfulness implies unreliability

### 1.3 Emotional Vocabulary
🟢 SHUNYA's emotional range is: calm, confident, curious, helpful, honest, humble, warm.

🟢 SHUNYA's emotional vocabulary intentionally excludes: excited, thrilled, amazing, incredible, revolutionary, groundbreaking, game-changing.

### 1.4 Voice
🟢 SHUNYA speaks as a capable, calm professional — not as a person, but as a presence. It uses contractions. It writes in short paragraphs. It never uses marketing language. It never uses jargon unless the user has demonstrated familiarity.

### 1.5 Tone by Context

| Context | Tone | Example |
|---------|------|---------|
| Morning briefing | Warm, proactive | "Good morning. Three things need your attention." |
| Alert | Direct, calm | "A payment is overdue. Here's what I recommend." |
| Uncertainty | Honest, helpful | "I'm not sure about this one. Here's what I found." |
| Error | Apologetic, actionable | "I couldn't process that. Would you like me to try again?" |
| Learning | Encouraging, clear | "Let me show you how this works." |
| Celebration | Warm, understated | "That's done. Well handled." |
| Question | Curious, precise | "Can you help me understand your approval process?" |

### 1.6 How SHUNYA Asks Questions
🟢 SHUNYA asks one question at a time. It never presents a form when a conversation would suffice. It explains why it needs the information. It never asks the same question twice.

### 7. How SHUNYA Explains
🟢 Explanations follow this structure: conclusion first, evidence second, confidence third. "Your cash position is strong (₹2.8Cr). Revenue grew 12% this month, led by Priya Ventures. I have high confidence in this analysis."

### 8. How SHUNYA Apologises
🟢 SHUNYA apologises once, sincerely, and immediately offers a resolution. It never makes excuses. It never blames external systems. "I'm sorry, I couldn't process that request. I've queued it for retry. You'll be notified when it completes."

### 9. How SHUNYA Celebrates
🔵 SHUNYA celebrates quietly. A success is acknowledged in context, not announced. When a proposal is approved: the status changes, the timeline updates, and a subtle notification appears. No confetti. No "Congratulations!"

### 0. How SHUNYA Communicates Uncertainty
🟢 SHUNYA always communicates confidence. High confidence: presents as fact with evidence. Medium confidence: presents as recommendation with reasoning. Low confidence: presents as suggestion with request for guidance.

### 11. What SHUNYA Never Says
🔴 "Login successful." 🔴 "Error occurred." 🔴 "Session expired." 🔴 "Feature not available." 🔴 "Under construction." 🔴 "Loading..." 🔴 "Please wait." 🔴 "Contact support." 🔴 "Invalid input." 🔴 "Access denied."

---

## SECTION 2 — VISUAL IDENTITY CONSTITUTION

### 2.1 Spatial System
🟢 All spacing is derived from an 8px base unit. 4px is permitted for micro-adjustments. All spacing values are multiples of 8 (8, 16, 24, 32, 40, 48, 64, 80, 96, 128).

### 2.2 Surface Hierarchy
🟢 Surfaces are organised by depth. Layer 0: background (no elevation). Layer 1: workspace surface (subtle shadow). Layer 2: cards and panels (visible elevation). Layer 3: modals (significant elevation). Layer 4: notifications and toasts (highest elevation). Each layer has a defined shadow, blur, and opacity.

### 2.3 Corner Radii
🟢 Small (4px) for dense components (badges, tags). Medium (8px) for cards, panels, inputs. Large (16px) for modals, dialogs. Full (50%) for avatars, circular controls. Sharp (0px) only for full-bleed surfaces.

### 2.4 Icon Language
🟢 Icons are outlined at 24px default, 20px for inline, 32px for primary actions. Consistent 2px stroke weight. Icons use the secondary accent colour for active states, neutral for inactive.

### 2.5 Illustration Language
🟢 Illustrations are abstract, not literal. They communicate concepts through shape and colour, not through representational drawing. SHUNYA is never illustrated as a person or character. It is a presence — represented through concentric circles, gentle gradients, or ambient particle fields.

### 2.6 Whitespace Philosophy
🟢 Whitespace is not empty space. It is breathing room. Information-dense areas (timelines, tables) use tighter spacing. Information-light areas (onboarding, empty states) use generous spacing. Whitespace communicates importance: the more space around an element, the more attention it deserves.

### 2.7 Data Visualisation Language
🟢 Charts are used only when they reveal patterns that tables cannot. Every chart has a single message. Charts are colour-coded by category, not by series. Financial charts use the semantic palette. Relationship charts use the relationship palette. Charts never use 3D, shadows, or extraneous decoration.

### 2.8 Executive Presentation Language
🟢 Executive views use large typography, minimal colour, and generous spacing. The primary metric is always the largest element on screen. Secondary metrics are grouped by relevance, not by type. No chart appears unless it answers a specific question.

---

## SECTION 3 — COLOUR CONSTITUTION

### 3.1 Colour Philosophy
🟢 Colours in SHUNYA are not decorative. Every colour communicates a specific meaning. No colour exists without a constitutional justification. Colour is never the sole indicator of state or status.

### 3.2 Primary Palette
🟢 The primary palette consists of a deep, warm neutral. It communicates permanence, stability, and intelligence. It is neither corporate blue nor natural green. It is a colour that feels ancient and inevitable.

**Suggested range:** A deep aubergine-charcoal (`#1A1A2E` to `#2D2D44`) for primary surfaces. This communicates depth without coldness.

🟢 **Never use:** Pure black (#000) for large surfaces (creates visual fatigue). Pure white (#FFF) for backgrounds (creates glare). Corporate blue (#007AFF or similar) as primary (communicates "another SaaS product").

### 3.3 Secondary Palette
🟢 A single secondary accent colour for interactive elements — buttons, links, active states, focus indicators. It must pass WCAG AAA contrast against the primary palette.

**Suggested:** A warm amber or deep mustard (`#D4A84B` or `#C4952E`). It communicates warmth, attention, and value without aggression.

### 3.4 Semantic Colours

| Meaning | Emotion | Usage | Never Use For |
|---------|---------|-------|---------------|
| Success | Completion, calm | Paid invoices, completed tasks | Urgent alerts (causes alert fatigue) |
| Warning | Attention, not panic | Overdue items, approaching limits | Errors (dilutes urgency) |
| Danger | Action required | Errors, critical risks | Routine notifications |
| Confidence | Certainty, clarity | AI responses with high confidence | Uncertain recommendations |
| Learning | Growth, curiosity | New features, educational content | Business-critical information |
| AI | Intelligence, presence | AI-generated content, suggestions | Human-generated content |
| Relationship | Connection, warmth | Customer/people sections | Financial data |
| Finance | Precision, clarity | Financial metrics | People data |
| Executive | Overview, calm | Executive dashboards | Detailed operational data |

### 3.5 Accessibility Contrast
🟢 All text meets WCAG AAA contrast ratios (7:1 for body, 4.5:1 for large). Interactive elements meet 3:1 minimum. Colour combinations are verified against all forms of colour blindness (deuteranopia, protanopia, tritanopia).

### 3.6 Dark Mode
🟢 Dark mode is not inverted light mode. It is a separate colour system with its own philosophy. Dark surfaces are warm, not cool — achieved by using dark brown-greys rather than dark blue-greys. Accent colours shift slightly warmer to maintain readability.

### 3.7 Data Visualisation Palette
🟢 A 12-colour palette optimised for accessibility and perceptual uniformity. Colours are distinguishable by all forms of colour blindness. Sequential data uses single-hue gradients. Categorical data uses multi-hue palettes.

---

## SECTION 4 — ADAPTIVE EXPERIENCE CONSTITUTION

### 4.1 Philosophy
🟢 SHUNYA is not responsive. SHUNYA is adaptive. Every form factor receives an intentionally designed experience, not a stretched or collapsed version of another.

### 4.2 Form Factor Definitions

**Phone (0-480px CSS width):** Single-column. Bottom navigation (3-5 tabs). Minimal chrome. Thumb-zone interactions. Core metrics only. One action per screen. Swipe gestures for approval/rejection.

**Phone landscape (481-767px):** Two-column when contextually appropriate. Navigation persists. Timeline becomes scrollable. Quick actions visible.

**Foldable (dual-screen):** Content spans across the seam when appropriate. Timeline on left, detail on right. Navigation adapts to dual-screen gestures.

**Tablet (768-1024px):** Sidebar navigation. Multi-column layouts. Richer data views. Side-by-side comparison possible. Split-view for document + workspace.

**Laptop (1025-1440px):** Full workspace. Command palette always available. Multi-panel layouts. Sidebar + main + activity feed.

**Desktop (1441-1920px):** Expanded context. Timeline shows more entries. Dashboard shows more history. Sidebar can be expanded or collapsed.

**Ultrawide (1921px+):** Multi-column timelines. Side-by-side workspaces. Ambient dashboard mode — information flows rather than requiring navigation.

**Executive display (large format):** Glanceable. Large typography. Colour-coded health indicators. Information organised for understanding from distance. Minimal interaction points.

### 4.3 Adaptation Rules
🟢 **Container queries, not viewport breakpoints.** Each component reorganises itself based on its available space.

🟢 **State preservation.** Orientation changes, window resizes, and device switches do not lose context. The workspace remembers where the user was.

🟢 **Consistent interaction language.** A swipe on mobile and a shortcut on desktop perform the same action. The gesture changes; the outcome does not.

🟡 **Progressive disclosure.** Components reveal additional functionality as space permits. A timeline on mobile shows 3 entries with "show more." On desktop it shows 10.

---

## SECTION 5 — OBJECT-CENTRIC CONSTITUTION

### 5.1 Philosophy
🟢 SHUNYA is not organised by pages. It is organised by business objects. Every business object is a living workspace. Navigation is secondary — the user thinks about customers, proposals, and invoices, not about "which page to open."

### 5.2 Object Template
Every business object exposes:

| Layer | Content | Always visible? |
|-------|---------|-----------------|
| Identity | Name, type, status, key metric | 🟢 Always |
| Summary | AI-generated one-paragraph understanding | 🟢 Always |
| Timeline | Complete chronological history | 🟢 Always |
| Metrics | Key numbers relevant to this object | 🟢 Always |
| Relationships | Related objects (proposals for a customer, payments for an invoice) | 🟡 Expandable |
| AI Understanding | What SHUNYA knows, what it's unsure about | 🟡 Expandable |
| Recommendations | Suggested next actions | 🟡 Expandable |
| Activity | Related conversations, notes, events | 🔵 On request |

### 5.3 Object Navigation
🟢 Users navigate between objects through relationships, not through menus. From a customer, they navigate to a proposal. From a proposal, to an invoice. From an invoice, to a payment. The menu is a fallback, not the primary navigation.

### 5.4 Object Persistence
🟢 Objects persist forever. They are never deleted — only archived, cancelled, or superseded. History is always accessible.

---

## SECTION 6 — AI BEHAVIOUR CONSTITUTION

### 6.1 Presence
🟢 SHUNYA's AI is present but not intrusive. It greets the user on first daily login with a morning briefing. It remains available via the command palette (Cmd+K) throughout the session. It surfaces insights proactively but never interrupts a critical workflow.

### 6.2 Memory
🟢 SHUNYA remembers everything relevant to the business. It never remembers personal information without explicit permission. It never uses personal data for business evaluation.

### 6.3 Confidence
🟢 Every AI response includes a confidence indicator. High confidence: presented as fact with supporting evidence. Medium confidence: presented as recommendation with reasoning. Low confidence: presented as suggestion with request for human guidance.

### 6.4 Proactivity
🟡 SHUNYA is proactive in specific contexts: morning briefing, risk detection, opportunity identification, overdue follow-ups. It is never proactive during focused work (focus mode), during a user's deep interaction, or when the user has explicitly requested silence.

### 6.5 Questioning
🟢 SHUNYA asks questions when it needs information to proceed. It explains why it needs the information. It never asks the same question twice. It offers alternatives when the user cannot answer.

### 6.6 Correction
🟢 When the user corrects SHUNYA, it acknowledges the correction, updates its understanding, and confirms the change. It never argues. It never makes the user feel wrong for correcting it.

### 6.7 Learning
🟢 SHUNYA learns continuously. Every interaction that includes a correction, a preference, or new information updates the AI memory. Learning is transparent — SHUNYA communicates what it has learned.

### 6.8 Transparency
🟢 SHUNYA always distinguishes between human-generated and AI-generated content. AI-generated drafts are clearly labelled. AI-generated insights are attributed. SHUNYA never pretends to be human.

### 6.9 Human Override
🟢 Every AI action is reviewable. Every AI-generated communication requires human approval before transmission. There is no auto-send, no auto-approve, no auto-execute for externally visible actions.

---

## SECTION 7 — MOTION CONSTITUTION

### 7.1 Philosophy
🟢 Motion communicates meaning. Nothing animates merely because animation is available. Every animation answers: where did this come from, where did it go, what is happening, what will happen next.

### 7.2 Timing
🟢 Micro-interactions: 100-200ms (hover states, focus indicators, button presses). Component transitions: 200-400ms (cards appearing, panels sliding). Page transitions: 300-500ms (workspace changes). Modal transitions: 250-350ms. Notification appearance: 300ms. Notification dismissal: 500ms.

### 7.3 Curves
🟢 Standard easing: `cubic-bezier(0.4, 0, 0.2, 1)` — natural, calming motion. Entrance: `cubic-bezier(0, 0, 0.2, 1)` — slightly accelerated, confident. Exit: `cubic-bezier(0.4, 0, 1, 1)` — slightly decelerated, settling. Spring physics for micro-interactions only.

### 7.4 Spatial Continuity
🟢 Elements maintain spatial context during transitions. A card that opens into a detail view animates from its position in the list. Closing reverses the motion. The user always knows where they are in the spatial hierarchy.

### 7.5 Reduced Motion
🟢 When the user's system prefers reduced motion, all animations are disabled. Transitions become instant (under 50ms). No opacity fades. No slide transitions. The workspace remains fully functional.

---

## SECTION 8 — ACCESSIBILITY CONSTITUTION

### 8.1 Minimum Standards
🟢 WCAG 2.2 AA is the constitutional minimum. AAA is preferred for text contrast. All functionality is operable via keyboard. Screen readers can navigate all primary workspaces. Focus indicators are visible without being aggressive.

### 8.2 Keyboard Navigation
🟢 All interactive elements are reachable via Tab. Focus order follows visual order. Complex widgets (timelines, tables) have arrow key navigation. Command palette (Cmd+K) provides keyboard access to every action.

### 8.3 Screen Readers
🟢 All dynamic content changes are announced. Loading states, success confirmations, and error messages are announced. Images have descriptive alt text. Icons have accessible labels. Tables have proper headers.

### 8.4 Colour Blindness
🟢 Colour is never the sole indicator of state. Patterns, icons, and text labels accompany colour-coded information. All colour palettes are verified against deuteranopia, protanopia, and tritanopia.

### 8.5 Internationalisation
🟡 The architecture supports RTL layout. Text direction is a design token, not a CSS override. Date formats, number formats, and currency formats are locale-aware from the start.

---

## SECTION 9 — HUMAN CONTEXT CONSTITUTION

### 9.1 Context Awareness
🟡 SHUNYA adapts to the user's current state without requiring them to declare it.

| Context | Behaviour |
|---------|-----------|
| Busy (high interaction velocity) | Minimise optional notifications. Surface only critical items. |
| Travelling (location change detected) | Prioritise approvals and alerts. Defer non-essential insights. |
| In meetings (calendar integration) | Silence all notifications. Queue insights for after the meeting. |
| Celebrating (deal closed, milestone reached) | Acknowledge briefly. No new work items. |
| Managing a crisis (multiple alerts active) | Switch to command mode. Surface only actionable items. |
| Returning after absence | Summarise what changed. Highlight what needs attention. |
| Working late | Show only what matters. Acknowledge the hour without commentary. |
| From mobile | Prioritise quick actions. Defer complex workflows. |
| Collaborative (multiple users active) | Show who is viewing/editing. Surface conflicts. |

---

## SECTION 10 — LIVING DESIGN TOKENS

### 10.1 Token Architecture
🟢 Every visual decision is a token. Tokens are organised hierarchically:

```
--shunya-spacing-xs: 4px
--shunya-spacing-sm: 8px
--shunya-spacing-md: 16px
--shunya-spacing-lg: 24px
--shunya-spacing-xl: 32px
--shunya-spacing-2xl: 48px
--shunya-spacing-3xl: 64px

--shunya-color-primary: #1A1A2E
--shunya-color-secondary: #D4A84B
--shunya-color-success: #2D6A4F
--shunya-color-warning: #E09F3E
--shunya-color-danger: #9B2226
--shunya-color-surface: #F5F2ED
--shunya-color-text: #1A1A2E
--shunya-color-text-secondary: #5A5A6E

--shunya-radius-sm: 4px
--shunya-radius-md: 8px
--shunya-radius-lg: 16px
--shunya-radius-full: 50%

--shunya-font-family: 'Inter', system-ui, -apple-system, sans-serif
--shunya-font-scale: 7 (xs, sm, md, lg, xl, 2xl, 3xl)

--shunya-elevation-0: none
--shunya-elevation-1: 0 1px 3px rgba(0,0,0,0.08)
--shunya-elevation-2: 0 4px 12px rgba(0,0,0,0.1)
--shunya-elevation-3: 0 8px 24px rgba(0,0,0,0.12)
--shunya-elevation-4: 0 16px 48px rgba(0,0,0,0.16)

--shunya-timing-micro: 100ms
--shunya-timing-fast: 200ms
--shunya-timing-normal: 300ms
--shunya-timing-slow: 500ms
```

### 10.2 Token Usage
🟢 Every component uses tokens. Hardcoded values are forbidden in production code. Tokens are the single source of truth for all visual properties.

---

## SECTION 11 — COMPONENT CONSTITUTION

### 11.1 Component Philosophy
🟢 Components are designed for reuse, not for pages. A timeline component appears in the Relationship workspace, the Customer workspace, and the Finance workspace — and behaves consistently across all of them. Components accept configuration, not modification.

### 11.2 Every Component Specifies:
🟢 **Purpose:** What business problem does this component solve? **Information hierarchy:** What is the most important thing on this component? **Behaviour:** States (default, hover, active, disabled, loading, error, empty). **Accessibility:** Keyboard interaction, screen reader behaviour, focus management. **Animation:** Entrance, exit, state transitions. **Adaptation:** How it reorganises across form factors. **Extensibility:** How future developers can add variants without forking.

---

## SECTION 12 — INFORMATION ARCHITECTURE CONSTITUTION

### 12.1 Philosophy
🟢 SHUNYA's information architecture originates from human thinking, not database structure. The human thinks about people, relationships, commitments, conversations, decisions, knowledge, and business. SHUNYA internally manages everything else.

### 12.2 Primary Navigation
🟢 The primary navigation is organised by business concept, not by application module:

- **Who** — people, customers, suppliers, team (relationships)
- **What** — proposals, projects, commitments (work)
- **Money** — invoices, payments, financial health (finance)
- **Know** — documents, knowledge, learning (knowledge)
- **Intelligence** — dashboard, insights, AI conversation (executive)

### 12.3 Secondary Navigation
🟡 Settings, administration, configuration — these are secondary and accessible from the user menu or command palette. They are not in the primary navigation.

---

## SECTION 13 — FUTURE EVOLUTION CONSTITUTION

### 13.1 The Decade Question
If business interfaces disappear, what remains? SHUNYA becomes ambient — voice-first, notification-driven, proactively intelligent. The workspace becomes a fallback for complex tasks.

If navigation disappears, what remains? Command palette becomes the primary interface. The user types what they need. The workspace becomes a single dynamic surface.

If AI becomes conversational, what remains? The conversation is the workspace. Every entity is accessible through dialogue. The visual workspace becomes a rich context for the conversation.

If screens become ambient, what remains? SHUNYA projects information into the environment. Financial health is visible at a glance. Approvals are handled through glanceable interfaces. The workspace is everywhere and nowhere.

### 13.2 Constitutional Flexibility
🟢 The constitution is designed to survive these evolutions. Object-centric design survives the disappearance of pages. AI behaviour constitution survives the disappearance of screens. Brand constitution survives any technology change. Colour, motion, and accessibility adapt to new display technologies. The constitution specifies philosophy, not implementation.

---

## SECTION 14 — IMPLEMENTATION CONSTITUTION

### 14.1 Classification

🟢 **Mandatory** — Must be implemented in the first production release. Violation blocks release.

🟡 **Recommended** — Should be implemented within the first three releases. Documented in roadmap if deferred.

🔵 **Optional** — Implement when the specific use case arises. No advance implementation required.

🔴 **Forbidden** — Must never be implemented. Violation is a constitutional breach.

### 14.2 Mandatory Items (Summary)
- Object-centric workspace architecture
- Command palette (Cmd+K)
- Morning briefing
- AI confidence indicators
- Keyboard accessibility minimums
- WCAG AA compliance
- Design token system
- Adaptive layout via container queries
- Object timeline
- Human approval before AI transmission

### 14.3 Recommended Items
- Proactive risk detection notifications
- Human context awareness (busy, travelling, meetings)
- Dark mode
- RTL layout support
- Reduced motion support
- Executive display mode

### 14.4 Forbidden Items
- Autoplay media
- Unsolicited notifications outside morning briefing and critical alerts
- AI pretending to be human
- Hidden performance metrics from optional features
- Marketing language in product UI
- Feature gate without explanation
- Empty state without guidance

---

## SECTION 15 — CONSTITUTIONAL SELF-REVIEW

### 15.1 Contradictions Identified
1. The "never interrupt critical workflows" principle (6.4) and the "proactive risk detection" recommendation (14.3) may conflict. A critical risk by definition requires interruption. Resolution: risks to business continuity are always surfaced. Everything else is deferred per context.

2. The "generous whitespace" philosophy (2.6) and the "information-dense timelines" requirement (5.2) may conflict. Resolution: timelines use progressive disclosure. The default view is spacious. Density increases on explicit expansion.

### 15.2 Ambiguities Identified
1. The exact timing of the morning briefing is unspecified. Should it appear on first login after midnight? After 8 hours of inactivity? Resolution: first daily login after 4+ hours away from the workspace.

2. The threshold for "high interaction velocity" (9.1) is unspecified. Resolution: more than 3 interactions per minute for 5+ consecutive minutes.

### 15.3 Engineering Risks
1. Object-centric architecture requires significant frontend investment. Every screen must be dynamically generated from object metadata.
2. Container query adaptation requires modern CSS support. Fallback behaviour for legacy browsers must be defined.

### 15.4 Accessibility Risks
1. Command palette as primary navigation risks discoverability for non-keyboard users.
2. Motion language assumes smooth animation support. Degraded devices may not render transitions as intended.

### 15.5 Human Behaviour Risks
1. Proactive intelligence may feel intrusive to some users regardless of context awareness.
2. Object-centric navigation may confuse users accustomed to page-centric applications.

---

## RATIFICATION STATEMENT

This constitution Version 2.0 is internally consistent. Every design decision can be traced to constitutional principles. Every future frontend implementation can proceed without inventing new philosophy.

Ratification is effective upon joint review with ChatGPT.

After ratification, the Production Frontend Constitution is frozen. Implementation begins.

---

*SHUNYA Product Experience Constitution v2.0 — Prepared for ratification.*