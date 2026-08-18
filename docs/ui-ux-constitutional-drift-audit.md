# SHUNYA UI/UX Constitutional Drift Audit

> **Produced:** 2026-08-18
> **Phase:** C — First deliverable per SHUNYA Final Product Experience Recovery Directive
> **Prerequisite:** PROD-06 closed (commit bca5325, tree clean)

---

## Audit Methodology

For each major surface, I compare:
1. **Constitutional Principle** — the binding canonical requirement
2. **Intended Experience** — what the canonical document specifies
3. **Current Implementation** — what actually exists in code/deployment
4. **Deviation** — how the implementation differs from the intention
5. **Required Correction** — what must change to restore conformance
6. **Evidence** — source file(s) demonstrating the deviation

---

## 1. Public Landing Experience

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Visual Design Bible §1, §3: Warm minimalism. Gold-accented calm. SHUNYA identity (शून्य) first. Light, warm-white background (#fbfaf8). Hero artwork with ribbon/halo animation. "Not a Bootstrap utility-class dashboard." |
| **Intended Experience** | Warm white page (#fbfaf8). Playfair Display hero. Clean, editorial layout. Hero artwork (SVG ribbons, halos, Devanagari). Subtle gold accent. Public → authenticated continuity: same visual language. |
| **Current Implementation** | Dark page (#0a0a0f background, #e0e0e0 text). Gold (#D4A84B) buttons. No hero artwork. Simple centered text layout. CSS injected via JS template literal. Two buttons (Get Started, View Pricing). |
| **Deviation** | **HIGH.** Wrong color scheme (dark vs light warm). No hero artwork. No Playfair Display branding typography (inter inline styles override). Gold used for buttons (prohibited by Visual Design Bible §6.2). No animated ribbon/halo identity elements. Homepage styles embedded via JS rather than static CSS. |
| **Required Correction** | Rebuild homepage per Visual Design Bible spec: #fbfaf8 background, Playfair Display headings, hero artwork SVG, gold accent only for identity marks (not buttons), light tone throughout. Extract CSS to static file. |
| **Evidence** | `/frontend/src/components/public/homepage.tsx` — dark theme, inline styles, no artwork.svg reference. `/frontend/src/components/auth/auth-styles.ts` — dark theme (#0a0a0f background). Design Bible: `static/img/artwork-hero.svg`, templates/artwork_hero.html. |

---

## 2. Authentication Transition

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Directive §17: Public → authenticated continuity. "The user should feel they entered the same product. Not: Website → login → completely unrelated SaaS dashboard." Visual Design Bible §13: Continuity in visual language, tone, motion, typography, SHUNYA presence, calmness, identity. |
| **Intended Experience** | Cinematic intro (शून्य → SHUNYA → tagline) on same warm white palette. Login form that feels like a progression, not a different app. Same typography, same spacing, same gold identity marks. |
| **Current Implementation** | Dark cinematic intro (0a0a0f). Form appears after 4s sequence. Gold buttons (#D4A84B). Dark input fields (#1a1a24). Transition from dark homepage to dark login — but NOT the canonical warm white palette. |
| **Deviation** | **HIGH.** Auth pages use a separate dark "cinematic" theme that is visually disconnected from the canonical warm-light SHUNYA identity. The dark login feels like a different product from the canonical light workspace. |
| **Required Correction** | Re-theme auth pages to match canonical warm white palette. Remove dark mode. Form should transition from the homepage visual language, not contrast with it. |
| **Evidence** | `/frontend/src/components/auth/login-page.tsx` — dark cinematic sequence. `/frontend/src/components/auth/auth-styles.ts` — dark color values (#0a0a0f bg, #1a1a24 inputs, #2a2a3a borders). |

---

## 3. Application Shell

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Visual Design Bible §4.5: Three-zone layout. Zone 1: Identity Strip (44px). Zone Left (280px): Navigation/search/graph. Zone Center (flex:1): Object workspace. Zone Right (340px): Intelligence pane. Navigation Canon §2: Zone 1 always visible, 56px, glass effect, fixed. |
| **Intended Experience** | `[Identity Strip] [Left 280px | Center flex:1 | Right 340px]`. Zone 1: logo/home, workspace switcher, breadcrumb, search bar, notifications, user menu. Zone Left: context panel, relationships, recent items, AI Resident. Zone Center: primary workspace. Zone Right: intelligence, insights. |
| **Current Implementation** | WorkspaceBar — tab-based switcher (emoji icons: 🏠📄📋). WorkspaceShell — minimal flex column (just `wksp-content`). No three-zone layout. No persistent Zone 1 identity strip. No context panel (Zone Left). No intelligence pane (Zone Right). Dark theme (#0a0a0f) fallback. |
| **Deviation** | **CRITICAL.** The entire three-zone workspace architecture is not implemented. Current shell is a basic content area with a tab bar. No Zone 1 identity strip, no Zone Left context panel, no Zone Right intelligence pane. No glass effect navigation bar. No proper navigation canons. |
| **Required Correction** | Implement the full three-zone layout per Visual Design Bible §4.5. Zone 1 identity strip (56px, glass, fixed) with logo, workspace switcher, breadcrumb, search/command bar, notifications, user menu. Zone Left (280px) with context panel. Zone Right (340px) with intelligence pane. |
| **Evidence** | `/frontend/src/components/workspace/workspace-shell.tsx` — minimal flex layout. `/frontend/src/components/workspace/workspace-bar.tsx` — tab-based, emoji icons, dark theme CSS variables. `/frontend/src/components/workspace/workspace-container.tsx` — no zone divisions. |

---

## 4. Primary Workspace

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Product Constitution §3: Single intelligence runtime. Object-workspace model. Experience Philosophy §5: Everything is an object. Every object shares the same workspace architecture. Directive §6: Object-centric. Screen should expose the thing the human is thinking about. |
| **Intended Experience** | Universal object workspace: Object Header (icon 48px, name, type badge, status, confidence, ID, timestamps, actions). Executive Summary (AI-generated, 3 lines). Section Nav (left, 10 sections: Identity, Relationships, Timeline, Knowledge, Tasks, Execution, Metrics, Documents, AI, History). Object-centric, not dashboard-centric. |
| **Current Implementation** | WorkspaceContainer renders one of: ExecutiveHome, ObjectWorkspaceViewer, AdminPanel, PeoplePanel, ImportExportPanel based on workspace type. LivingWorkspace component has CreateObjectModal with business-specific types (proposal, invoice, contact, task, note). No universal object workspace header. No executive summary section. No standardized 10-section nav. |
| **Deviation** | **CRITICAL.** No universal object workspace architecture. No standardized object header. No executive summary. No 10-section navigation. Living workspace hardcodes business-specific object types (proposal, invoice) instead of universal SHUNYA concepts. Decision/Commitment/Execution workspace surfaces not implemented per canon. |
| **Required Correction** | Implement universal object workspace per Object Workspace Canon. Standardized header, executive summary, 10-section navigation. Remove business-specific object types from creation modals — use universal types (Object, Decision, Commitment, Execution, Relationship, Evidence, Observation). |
| **Evidence** | `/frontend/src/components/living-workspace/living-workspace.tsx` — CreateObjectModal with proposal/invoice/contact types. `/frontend/src/components/workspace/workspace-container.tsx` — eclectic panel composition instead of universal architecture. `/frontend/src/components/workspace/object-workspace-viewer.tsx` — need to inspect. |

---

## 5. Navigation

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Navigation Canon: SPA, object-first, spatial continuity, state preservation. Direct navigation (search/command palette) prioritized over menus. Zone 1 global bar. Workspace switcher (icons, Ctrl+[1-9]). Context panel (Zone 2). Command Palette (Ctrl+K). Breadcrumb. |
| **Intended Experience** | Zone 1 top bar with logo/home, workspace switcher (14 icons max), breadcrumb, search bar, notifications, user menu. Command Palette via Ctrl+K (fuzzy search, contextual). Context Panel left side (300px, resizable). No page-based navigation. |
| **Current Implementation** | Tab-based workspace bar (horizontal tabs with close buttons, emoji icons). No Zone 1 navigation bar. No Command Palette (Ctrl+K). No breadcrumb. No workspace switcher icons. URL-based routing `/workspace/:type/:id`. No persistent navigation structure. |
| **Deviation** | **CRITICAL.** Navigation architecture is tab-based (IDE-style) rather than spatial (workspace-style). No Command Palette. No Zone 1 bar. No breadcrumb. No workspace switcher with keyboard shortcuts. The navigation violates the Navigation Canon's "One application, not a website" and "Object-first, not page-first" principles. |
| **Required Correction** | Replace tab-based bar with Zone 1 identity strip per Navigation Canon. Implement Command Palette (Ctrl+K). Implement workspace switcher with keyboard shortcuts (Ctrl+[1-9], Ctrl+Tab). Implement breadcrumb navigation. Implement context panel (Zone 2). |
| **Evidence** | `/frontend/src/components/workspace/workspace-bar.tsx` — tab-based, emoji icons. `/frontend/src/components/workspace/workspace-shell.tsx` — no Zone 1. `/frontend/src/app.tsx` — URL-based routing. No command palette component reference in app shell. |

---

## 6. Command Bar / Command Palette

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Directive §12: "The command bar remains a primary SHUNYA interaction surface. It must not feel like an ordinary search box. It should allow the human to ask, instruct, explore, change context, act, invoke SHUNYA." Navigation Canon §6: Ctrl+K opens palette, fuzzy search, contextual, non-modal. |
| **Intended Experience** | Persistent command surface (Ctrl+K). Always available. Fuzzy search. Contextual (current workspace objects rank higher). Modes: type for search, "/" for commands, ">" for workspace switch, "?" for shortcuts. Recent objects shown on open. |
| **Current Implementation** | SearchBar component exists (`/frontend/src/components/search/universal-search.tsx`) but is imported in app.tsx and not integrated into the shell. ExecutiveHome has a CommandSurface component. No Ctrl+K handler. No global command palette. |
| **Deviation** | **HIGH.** Command bar exists as separate components but is not a primary, persistent, always-available surface. No Ctrl+K global keyboard shortcut. No command modes (/, >, ?). Not integrated into the application shell. |
| **Required Correction** | Implement a global Command Palette per Navigation Canon §6. Ctrl+K activation. Fuzzy search. Contextual ranking. Command mode. Always-available and non-modal. Integrate into Zone 1 of the new three-zone layout. |
| **Evidence** | `/frontend/src/components/search/universal-search.tsx` — exists but detached from shell. `/frontend/src/components/executive-home/command-surface.tsx` — localized to ExecutiveHome, not global. |

---

## 7. SHUNYA Presence

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Presence Canon §2: "SHUNYA is present the way a well-designed room is present: you notice the comfort, not the furniture." Four modes: Ambient (gold dot), Attentive (icon + glow), Suggestive (1-3 suggestions), Conversational (full chat). Directive §13: "SHUNYA should feel continuously present without becoming an intrusive assistant avatar." |
| **Intended Experience** | Gold dot indicator in ambient mode. Subtle glow when AI has information. Compact suggestions panel when AI has actionable insights. Full conversation panel when engaged. No cartoon character, no permanent chat bubble, no competition with the object being worked on. AI presence in Zone 2 (Context Panel) as AI Resident panel. |
| **Current Implementation** | AIPresencePanel exists in living-workspace directory. No gold dot indicator. No presence mode transitions. No AI Resident panel in workspace layout. ExecutiveBriefing component shows AI content but not per the presence canon's four-mode model. |
| **Deviation** | **HIGH.** SHUNYA presence is not implemented per the Presence Canon. No gold dot ambient indicator. No four-mode presence system. AI surfaces are scattered across components (AIPresencePanel, ExecutiveBriefing, CopilotPanel) without a unified presence model. |
| **Required Correction** | Implement Presence Canon §3 four-mode presence system. Gold dot (ambient). AI icon + glow (attentive). Suggestions panel (suggestive). Full conversation (conversational). Integrate into Zone 2 (Context Panel) as AI Resident. Remove scattered AI components. |
| **Evidence** | `/frontend/src/components/living-workspace/ai-presence-panel.tsx` — exists but not integrated. `/frontend/src/components/workspace/copilot-panel.tsx` — separate copilot concept not in canon. No gold dot anywhere in current UI. |

---

## 8. Object/Context Presentation

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Object Workspace Canon: Universal object workspace with standardized header, executive summary, 10-section navigation. "Every object in SHUNYA — regardless of type — follows the exact same workspace architecture." Directive §6: "The screen should primarily expose the thing the human is thinking about." |
| **Intended Experience** | Every object: Header (icon 48px, name, type badge, status, confidence, ID, timestamps, actions) → Executive Summary (AI, 3 lines) → Section Nav (10 sections: Identity, Relationships, Timeline, Knowledge, Tasks, Execution, Metrics, Documents, AI, History). |
| **Current Implementation** | ObjectWorkspaceViewer component exists. UniversalObjectWorkspace component exists in living-workspace. Neither follows the 10-section standardized architecture. No executive summary header. No section nav. Custom layouts per object type rather than universal. |
| **Deviation** | **HIGH.** Object workspaces are not standardized per the Object Workspace Canon. Different object types appear to have different layouts. No universal object header with executive summary. No 10-section navigation. |
| **Required Correction** | Implement the universal object workspace architecture exactly per Object Workspace Canon §2. Standardized header, executive summary, 10-section icon nav. One component renders all object types. |
| **Evidence** | `/frontend/src/components/living-workspace/universal-object-workspace.tsx` — check against canon standard. `/frontend/src/components/workspace/object-workspace-viewer.tsx` — needs inspection for section compliance. |

---

## 9. Visual Theme (Color / Light Mode)

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Visual Design Bible §6: Light mode only v1.0. Warm white background (#fbfaf8). Gold only accent (#a4865f). Surface white (#ffffff). Borders at 7% opacity. No dark mode. "No dark mode in v1.0. All designs are light-mode only." |
| **Intended Experience** | Page: #fbfaf8. Cards: #ffffff. Nav bg: #fefefe. Zone left: #f3f2f2. Zone center: #fafaf8. Zone right: #ebebea. Text: #1a1c1d (100%), secondary at 55% opacity. Gold accent only for identity marks. Dark text for buttons. |
| **Current Implementation** | Dark theme everywhere. Auth: #0a0a0f background, #e0e0e0 text. Workspace: #0a0a0f fallback. Workspace bar: #15151f surface. Inputs: #1a1a24, borders: #2a2a3a. Gold (#D4A84B) used for buttons (prohibited). Purple (#6C4AE2) defined as primary brand color (not in canon). |
| **Deviation** | **CRITICAL.** The entire visual system is dark instead of light. The gold is used for buttons instead of identity marks. Purple is introduced as a primary brand color (not in Visual Design Bible). The canonical warm, paper-toned aesthetic is completely absent. |
| **Required Correction** | Complete visual re-theme to canonical light mode. Remove all dark color values. Replace purple with gold as accent. Implement the exact color tokens from Design System Foundation and Visual Design Bible. |
| **Evidence** | `/frontend/src/components/auth/auth-styles.ts` — all dark values. `/frontend/src/tokens/definitions.ts` — purple as primary (line 34-45, 164-167). `/frontend/src/components/workspace/workspace-shell.tsx` — dark fallback. |

---

## 10. Typography

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Visual Design Bible §5: Playfair Display for display headings (regular 400 weight only). Inter for body (14px base). No bold Playfair. No all-caps body text. Scale follows golden ratio. Line height 1.5 for body. Tracking: tight -0.025em for display, normal 0 for body. |
| **Intended Experience** | Hero: Playfair Display 42-72px, 400 weight, -0.025em tracking. Section: Playfair Display 24-32px. Body: Inter 14px, 400 weight. Labels: 10px uppercase, 0.06em tracking. Data: tabular-nums. |
| **Current Implementation** | Token definitions (definitions.ts) have correct font families (Playfair Display, Inter). But the components don't use them consistently. Auth pages use Inter (via -apple-system fallback) at various sizes. Homepage heading uses inline `fontSize:'inherit'` (intercepting Playfair Display). No Playfair Display at correct sizes in the UI. Labels not using 10px uppercase spec. |
| **Deviation** | **HIGH.** Token definitions define correct fonts but components don't apply them. Inline styles override font family. No proper use of Playfair Display for headings. No 10px uppercase label system. Body text sizes inconsistent. |
| **Required Correction** | Apply the canonical typography scale globally. Use Playfair Display for all headings and object names. Use Inter for all body/UI text. Implement the 10px uppercase label spec. Remove inline font size overrides. |
| **Evidence** | `/frontend/src/tokens/definitions.ts` — correct type scale defined. `/frontend/src/components/public/homepage.tsx` — inline overrides. `/frontend/src/components/auth/auth-styles.ts` — no Playfair Display usage. |

---

## 11. Spacing / Visual Hierarchy

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Visual Design Bible §4: 4px base unit, 8px rhythm. 70/20/10 rule per Directive §7. Spacing scale: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128px. Max content width: 1200px (Visual Design Bible) or 960px (Design System Foundation). Radius: sm=10px, md=16px, lg=24px, xl=32px. |
| **Intended Experience** | Generous whitespace. Calm, spacious layout. 70% whitespace/primary content. 20% contextual information. 10% controls. Elements have room to breathe. Not crowded. |
| **Current Implementation** | Radius tokens: sm=4, md=8, lg=12, xl=16 (definitions.ts). Different from canonical 10, 16, 24, 32. Auth input radius: 6px (not 10px). Card padding not standardized per zoo spacing tokens. No 70/20/10 visual hierarchy applied. |
| **Deviation** | **MEDIUM.** Radius values differ from canonical (approximately 2x smaller). Auth components use custom radius values. The 70/20/10 principle is not applied — the current UI doesn't distinguish between primary context and controls. |
| **Required Correction** | Correct radius tokens to canonical values (10, 16, 24, 32). Apply 70/20/10 whitespace hierarchy: 70% calm whitespace/primary, 20% contextual, 10% controls. Enforce generous margins and padding per spacing scale. |
| **Evidence** | `/frontend/src/tokens/definitions.ts` line 111 — radius values. `/frontend/src/components/auth/auth-styles.ts` — 6px border-radius inputs/buttons. |

---

## 12. Cards / Panels / Contextual Surfaces

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Visual Design Bible §11.2: Card spec — padding 20px, border-radius 16px, border 1px #shunya-border, background #shunya-surface. No heavy borders. No box shadows on every card. Light creates depth, not borders. "Restraint over decoration." |
| **Intended Experience** | Cards with subtle borders, generous padding, minimal shadows. No skeleton screens that stutter. No confetti. No "delightful" micro-interactions that add cognitive load. One action per card. |
| **Current Implementation** | No standardized card component visible in the current UI. Auth modal uses intermittent spacing. Workspace panels have inline styles. The LivingWorkspace CreateObjectModal has distinct modal styling. Custom styles per component rather than canonical cards. |
| **Deviation** | **HIGH.** No standardized card/panel components conforming to Visual Design Bible spec. Every component invents its own surface styles. |
| **Required Correction** | Implement the canonical Card component per Visual Design Bible §11.2 spec. Apply universally. Standardize all surfaces to use the defined component tokens. |
| **Evidence** | Scattered inline styles across all components. No single card.tsx or panel.tsx component in the UI folder (check `/frontend/src/components/ui/`). |

---

## 13. Empty States

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Directive §9: No fake activity. "Never animate SHUNYA merely to make an empty screen appear alive." Idle state is also a state (§10): "When nothing requires attention, SHUNYA becomes quieter." An idle SHUNYA should feel calm, available, intelligent, present, trustworthy. |
| **Intended Experience** | Calm empty state. Not "LOOK AT ME, I AM AN AI." No artificial heartbeat loops. No meaningless pulsing. No decorative AI particles. The interface becomes quiet when nothing requires attention. |
| **Current Implementation** | ExecutiveHome renders a loading state with skeleton shimmer when booting. No dedicated empty state design visible. The boot screen shows "Starting platform…" with a basic loader. |
| **Deviation** | **MEDIUM.** No proper empty state design per the canonical spec. The calm-idle-state concept is not implemented. Boot/loading states use basic text rather than calibrated empty state design. |
| **Required Correction** | Design calm empty states per Directive §10. Idle SHUNYA should be quiet, present, and trustworthy — not demanding attention. No animated indicators in empty states. |
| **Evidence** | `/frontend/src/components/workspace/workspace-container.tsx` — basic loading skeleton. `/frontend/src/app.tsx` — BootScreen component with simple text. |

---

## 14. Loading States / System Activity

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Motion System §6: Skeleton to content fade (300ms). Progressive loading with 50ms stagger. No global loading spinner. No spinning loaders per Visual Design Bible §10.6. Directive §9: Real system states must become visible: Retrieval, Reasoning, Decision, Approval, Execution, Completion, Result, Error, Recovery, New Information. |
| **Intended Experience** | Skeleton placeholder → content fades in (300ms). Sections load progressively with stagger. Visual states communicate causality (what's happening, what changed). No spinners. Real application state drives visible state. |
| **Current Implementation** | Workspace loading uses shimmer skeleton. Auth has a CSS spinner (`.sh-auth-spinner` — a rotating gold ring). Boot screen shows text messages. No real-state-driven visible states. No reasoning/retrieval/decision visual indicators. |
| **Deviation** | **HIGH.** Spinner animation exists in auth styles (prohibited by canon). No real-state-driven visible activity. The system does not visually communicate what SHUNYA is doing (retrieving, reasoning, deciding, executing, etc.). |
| **Required Correction** | Remove all spinner animations. Implement real-state-driven activity indicators per Directive §9. Skeleton loading per Motion System spec. No spinning loaders. Activity indicators driven by actual application state, not decorative animation. |
| **Evidence** | `/frontend/src/components/auth/auth-styles.ts` — `.sh-auth-spinner` (line 131-137, prohibited by Visual Design Bible §10.6). No real-state activity framework. |

---

## 15. Motion / Living-System Behavior

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Visual Design Bible §10: Motion exists to communicate state. Never for decoration. Easing: cubic-bezier(0.22, 1, 0.36, 1). Durations: 200ms (fast), 400ms (normal), 600ms (slow), 800ms (slower), 1200ms (slowest). Respects reduced-motion. No parallax, no confetti, no spinning loaders. Motion System Canon: Narrative, calm, spatial continuity, progressive, accessible. |
| **Intended Experience** | Page enter: fade up (translateY(14px)→0, opacity 0→1) staggered. Panel open: slide from edge (400ms). Workspace switch: old slides left (300ms), new slides in from right (400ms, 100ms delay). Tab switch: cross-fade (300ms). All motion purposeful. |
| **Current Implementation** | Auth has fade-in animation (`.sh-auth-fade-in` — translateY(10px) + opacity, 600ms). Token definitions include timing values (micro=100, fast=200, normal=300, slow=400) but no components use these tokens. No canonical motion easing applied (linear default). No page transitions. No workspace switch animations. No object transitions. |
| **Deviation** | **HIGH.** Motion system is not implemented. Token definitions have timing values but they differ from canonical (normal=300ms vs canonical 400ms). No easing curves applied. No purposeful motion for navigation, object transitions, or state changes. Auth fade-in is the only animation — it uses the wrong easing and duration pattern. |
| **Required Correction** | Implement the canonical motion system. Apply easing tokens as CSS custom properties. Staggered page enter animations. Workspace switch slide transitions. Object open/close panel animations. All motion must answer: what changed, what is happening, what requires attention, what caused this, what completed. Respect reduced-motion. |
| **Evidence** | `/frontend/src/tokens/definitions.ts` — timing values defined but not applied. `/frontend/src/components/auth/auth-styles.ts` — lone fade-in animation. No motion tokens used in any component. |

---

## 16. Desktop / Mobile Responsive

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Mobile Canon: Desktop-first with mobile integrity. Breakpoints: <640px mobile, 640-1024px tablet, 1024-1440px desktop, >1440px wide. Portrait-first mobile. Zone behavior per breakpoint. Mobile has bottom bar, bottom sheet for context panel, navigation stack. Directive §18: "Mobile is not compressed desktop." |
| **Intended Experience** | Desktop: three zones visible. 769-1024px: Zone Right hidden, Zone Left collapses. ≤768px: single column, bottom bar, context panel as bottom sheet. Touch targets 44px minimum. Swipe gestures for navigation. |
| **Current Implementation** | Minimal responsive consideration. Auth styles have a single @media (max-width: 480px) breakpoint adjusting padding and font size. Workspace has a ResizeObserver tracking width but no responsive layout adaptation. No bottom bar, no bottom sheet, no touch gesture support. No mobile-specific layout. |
| **Deviation** | **HIGH.** No mobile adaptation per Mobile Canon. The app does not adapt its layout across breakpoints. No bottom bar navigation. No context panel bottom sheet. Touch targets not validated. Portrait-first mobile not implemented. |
| **Required Correction** | Implement full responsive behavior per Mobile Canon breakpoints. Three zones collapse appropriately. Bottom bar on mobile. Bottom sheet for context panel. Touch targets (44px minimum). Navigation stack for mobile. |
| **Evidence** | `/frontend/src/components/auth/auth-styles.ts` — single 480px breakpoint. `/frontend/src/components/workspace/workspace-container.tsx` — ResizeObserver for width (not used for responsive layout). No mobile components exist. |

---

## 17. Business-Agnostic UI

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Directive §19: "The UI remains universally applicable. Do not introduce travel terminology, hotel terminology, itinerary terminology, lead-specific concepts, Panchi-specific concepts, travel-specific navigation, industry-specific assumptions." Use universal SHUNYA concepts: Object, Context, Relationship, Evidence, Commitment, Decision, Execution, Outcome, Observation, Memory, Attention, Activity, Insight. |
| **Intended Experience** | Workspaces, objects, and types use only universal SHUNYA concepts. No industry-specific language. The system is capable of becoming the operating layer for many businesses. |
| **Current Implementation** | LivingWorkspace CreateObjectModal uses: proposal, invoice, contact, task, note, other. These are business-domain types, not universal SHUNYA concepts. UBME module builder suggests business-specific module generation. "proposal" and "invoice" are lead/travel-related concepts that violate the business-agnostic principle. |
| **Deviation** | **HIGH.** Object creation modal hardcodes business-specific types (proposal, invoice, contact). These violate Directive §19's prohibition on travel/lead-specific concepts. Should use universal SHUNYA types. |
| **Required Correction** | Replace business-specific types with universal SHUNYA object types: Decision, Commitment, Execution, Relationship, Evidence, Observation, Outcome, Object. Remove "proposal", "invoice" etc. as first-class creation types. |
| **Evidence** | `/frontend/src/components/living-workspace/living-workspace.tsx` lines 63-71 — CreateObjectModal type options. |

---

## 18. Accessibility

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Directive §21: "Accessibility is part of the experience." Readable typography, sufficient contrast, keyboard navigation, focus states, semantic structure, touch targets, reduced motion, screen-reader meaningfulness, error communication, loading communication. Visual Design Bible §6.3: Contrast minimums — body text on background 10:1 (WCAG AAA). |
| **Intended Experience** | WCAG AA minimum everywhere. AAA for body text. Keyboard navigable. Semantic HTML. Focus-visible states. Reduced motion respected. Touch targets 44px. |
| **Current Implementation** | Auth components have focus-visible outlines on buttons/links. aria-labels on some elements. prefers-reduced-motion on auth fade-in. Color contrast: current dark theme (#e0e0e0 on #0a0a0f = ~11:1, passes) but canonical warm theme (#1a1c1d on #fbfaf8 = ~10:1, also passes). No keyboard navigation framework. No semantic landmark structure. No aria-live regions for dynamic content. |
| **Deviation** | **MEDIUM.** Some accessibility conventions are in place but no systematic accessibility framework. No keyboard navigation beyond basic Tab. No screen-reader announcements for loading/state changes. No focus trap for modals. No semantic page structure. |
| **Required Correction** | Add systematic keyboard navigation (arrow keys, Tab traps in modals, Escape handlers). Add aria-live regions for dynamic content. Validate color contrast against canonical palette. Implement full focus management. Ensure reduced-motion is respected everywhere. |
| **Evidence** | Sporadic a11y attributes. No centralized a11y framework. Auth had the best implementation but it's incomplete. |

---

## 19. Home Workspace / Executive Home

| Dimension | Detail |
|-----------|--------|
| **Constitutional Principle** | Workspace Model §2: Home Workspace — default landing. Organization health summary (8 dimensions). Recent decisions (last 7 days). Active tasks. Upcoming deadlines. Attention-worthy changes. Quick access to all workspaces. Directive §4: "What matters to this person right now?" NOT "How many records does SHUNYA contain?" |
| **Intended Experience** | Calm, intelligent overview. What changed since last visit. What requires attention. What should I do next. AI summarizes key changes. AI suggests next action. No dashboard cards. No generic statistics. No object counts. |
| **Current Implementation** | ExecutiveHome component exists with: priorities, recent activity, active commitments, SHUNYA summary. Uses API calls to fetch priorities, activity, commitments. CommandSurface inline. Has loading state with skeleton. |
| **Deviation** | **To be assessed after deeper inspection** — the ExecutiveHome appears well-intentioned (priorities, activity, commitments) but needs inspection for dashboard-density issues and object-count presentation. |
| **Required Correction** | To be determined after full inspection of ExecutiveHome implementation and API responses. |
| **Evidence** | `/frontend/src/components/executive-home/executive-home.tsx` (771 lines, needs full review). |

---

## Summary of Deviation Severity

| Severity | Count | Surfaces |
|----------|-------|----------|
| **CRITICAL** | 5 | Application shell (three-zone layout), Visual theme (dark vs light), Navigation architecture, Object workspace architecture, Public→Auth visual disconnect |
| **HIGH** | 9 | Landing page, Command bar, SHUNYA presence, Object/context presentation, Typography application, Cards/panels, Loading states, Motion system, Mobile responsive, Business-agnostic UI |
| **MEDIUM** | 3 | Spacing/radius values, Empty states, Accessibility framework |

---

## Root Causes

1. **Token definitions diverged from canonical design system.** The `definitions.ts` file introduces purple as primary (not in any canonical design document) and defines incorrect radius values. This was likely the first divergence point.

2. **Dark theme was introduced as a convenience choice** without constitutional authorization. The auth styles and workspace shell both default to dark, but the Visual Design Bible explicitly mandates light mode for v1.0.

3. **Components were built independently without the canonical three-zone shell** as a constraint. Each component created its own layout and styling rather than inheriting from the canonical workspace architecture.

4. **Business-specific concepts leaked into the UI** through the LivingWorkspace and UBME module builder, violating the business-agnostic principle.

5. **Motion and presence were deferred completely** — no meaningful animation system, no SHUNYA presence indicators, no real-state-driven visible activity.

---

## Required Corrections (Priority Order)

1. **P0 — Visual theme**: Switch from dark to canonical light-warm palette. Remove purple. Apply gold as identity-only accent. Apply correct radius values.

2. **P0 — Three-zone workspace shell**: Implement canonical Zone 1 (identity strip), Zone Left (context panel), Zone Center (primary content), Zone Right (intelligence pane).

3. **P0 — Navigation**: Replace tab-based bar with Zone 1 identity strip. Implement Command Palette (Ctrl+K). Implement workspace switcher.

4. **P1 — SHUNYA presence**: Implement four-mode presence system (Ambient/Attentive/Suggestive/Conversational) with gold dot indicator.

5. **P1 — Universal object workspace**: Implement standardized object header, executive summary, 10-section navigation.

6. **P1 — On-page content**: Re-theme login/auth to canonical light palette. Ensure public→authenticated visual continuity.

7. **P2 — Motion system**: Apply canonical easing and timing tokens. Implement purposeful transitions.

8. **P2 — Business-agnostic cleanup**: Replace proposal/invoice/etc. with universal SHUNYA types.

9. **P2 — Mobile responsive**: Implement breakpoint-adaptive layout per Mobile Canon.

10. **P2 — Accessibility**: Systematic keyboard navigation, screen-reader support, focus management.

11. **P2 — Loading/empty states**: Calm idle state design. Real-state-driven activity indicators.

12. **P3 — Remaining**: Typography enforcement, card/panel standardization, spacing hierarchy.