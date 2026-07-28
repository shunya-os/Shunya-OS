# SHUNYA Device-Native Architecture (DNA-01)

**Status:** Under Founder Review  
**Version:** 2.1  
**Supersedes:** All prior responsive layout conventions  
**Constitutional scope:** Every SHUNYA interface, present and future

---

## 1. Architectural Statement

SHUNYA is not a responsive web application. It is a **device-native operating system** that manifests appropriately on each canonical form factor. Every layout is intentionally designed for its experience class. No layout is derived from another.

The objective is not to make layouts fit. The objective is to ensure that every supported device feels purpose-built while remaining recognizably SHUNYA.

This constitution defines **behavioural guarantees** — the user-visible contract that every SHUNYA implementation must satisfy. The specific implementation mechanisms (CSS, runtime context, media queries, container queries, CSS variables, or future technologies) are free to evolve as long as the resulting behaviour matches the constitutional design. Architecture defines behaviour. It does not mandate implementation technology.

### Constitutional Principles

SHUNYA's device-native architecture is governed by these constitutional principles. Each is defined in its own section below.

| Principle | Section |
|-----------|---------|
| Device-Native, Never Desktop-Reduced | §4 |
| **Runtime Context** — a canonical, authoritative object capturing every dimension of the user's situation | §5 |
| Environmental Adaptation — response to conditions beyond screen size | §6 |
| Attention Adaptation — response to the user's cognitive state | §7 |
| Layout Composition — intentional arrangement per experience class | §8 |
| Navigation Model — per-class navigation, never hidden-then-revealed | §9 |
| Typography — consistent hierarchy, physically appropriate | §10 |
| Motion Language — one fade-based vocabulary throughout | §11 |
| Object Continuity — the object remains central across device transitions | §12 |
| Capability Parity — every class has the same features, differently presented | §13 |
| Experience Invariants — Calm, Continuity, Object Centrality, Context Awareness, **Predictability**, Capability Parity | §14 |
| Failure Behaviour — what the system guarantees when things break | §15 |
| **Predictability over Cleverness** — understandable, reversible, and deterministic adaptation | §16 |
| Adaptation Confidence — behavioural guarantees when the runtime is uncertain | §17 |
| Constitutional Archival Policy — superseded documents are archived, not deleted | §18 |

## 2. Constitutional Hierarchy

SHUNYA's experience architecture is governed by four layers. Each layer is concerned with a different abstraction level. No layer shall bypass the layer above it.

**Constitution** — What must always be true. Behavioural guarantees, principles, invariants. Changes only by founder ratification. This document.

↓

**Experience Bible** — What it looks and feels like on each canonical device. Intentional design narratives for every class. References the Constitution but adds device-specific fidelity. Updated by design ratification, not code review.

↓

**Design System** — Exact values, tokens, components, spacing, type scales, colour. The implementation toolkit. References the Experience Bible. Updated by design review.

↓

**Implementation** — Code, runtime, build tooling. References the Design System. The only layer that touches production.

**Constitutional rule:** A value or dimension that is not behavioural must not appear in the Constitution. A layout that is not tied to a specific device narrative must not appear in the Experience Bible. Implementation detail must not determine constitutional design.

This hierarchy ensures the Constitution remains stable for years while the Design System evolves quarterly and the Implementation changes weekly.

## 3. Canonical Experience Classes

SHUNYA recognises six canonical experience classes. These are abstract categories defined by **attention, interaction, density, available space, and context** — not by hardware specifications. The implementation may map specific hardware to these classes. The example dimensions shown in the Experience Bible are illustrative, not constitutional.

**This set is not frozen for all time.** Additional classes may be added by constitutional amendment as new form factors emerge. No current class shall be removed — doing so would break the Capability Parity guarantee.

| ID | Class | Interaction | Density | Typical Context |
|----|-------|-------------|---------|-----------------|
| EXP-01 | Compact Experience | Touch | High | On-the-go awareness |
| EXP-02 | Personal Experience | Touch / Keyboard | Medium | Extended reading |
| EXP-03 | Shared Experience | Touch / Keyboard | Medium | Split-view work |
| EXP-04 | Workstation Experience | Keyboard + Pointing | Standard | Deep work |
| EXP-05 | Studio Experience | Keyboard + Mouse | Standard | Studio work |
| EXP-06 | Orchestration Experience | Keyboard + Mouse | Low | Multi-panel orchestration |

**Constitutional rule:** Every implementation must support all currently ratified experience classes. The implementation decides the mapping from hardware to class.

## 4. Principle: Device-Native, Never Desktop-Reduced

The current codebase defines smaller screens as `display: none` of desktop panels. This is forbidden.

**Constitutional guarantee:** Every experience class must be designed from scratch in intent. A Compact Experience workspace is not a Studio Experience workspace with missing panels. It is a workspace that was designed for a Compact Experience.

**Verification:** A user on any experience class should never be able to infer that another layout existed first.

## 5. Principle: Adaptation, Not Replication

Components shall adapt through the canonical **Runtime Context** — a single authoritative object that captures every dimension of the user's current situation. Whether that adaptation is implemented through media queries, container queries, runtime JavaScript, CSS variables, or another mechanism is an implementation decision — provided the resulting behaviour matches this constitution.

The implementation shall make available to every component the canonical **Runtime Context**, which includes:

| Dimension | Description | Constitutional |
|-----------|-------------|----------------|
| **Experience Class** | The canonical experience class (EXP-01 through EXP-06) | Required |
| **Attention State** | The user's cognitive mode (focused, presenting, driving, in meeting, typing, idle, interrupted) | Required |
| **Environment** | Environmental conditions (reduced motion, high contrast, low bandwidth, offline, kiosk, embedded, screen reader active) | Required |
| **Interaction Method** | The active input modality (touch, mouse, keyboard, hybrid, assistive) | Required |
| **Motion Preference** | Whether reduced motion is preferred | Required |
| **Accessibility** | Active accessibility preferences (contrast, font scale, colour scheme) | Required |
| **Network** | Connectivity state (online, offline, metered, degraded) | Required |
| **Device Capability** | Hardware capabilities (display density, safe area boundaries, available sensors, input coexistence) | Required |
| **Runtime Confidence** | The system's certainty in its adaptation decision (see §17) | Required |

**Constitutional guarantee:** No component shall guess its environment. The Runtime Context shall provide authoritative, consistent, and timely information about every dimension. Every component receives the same Runtime Context in the same render cycle.

## 6. Principle: Environmental Adaptation

**Runtime Context dimension:** `Environment`

Experience class is not the only context that matters. SHUNYA must also adapt to the user's **environment** — conditions that change independently of form factor. The Environment dimension of the Runtime Context captures these conditions as a single, authoritative signal.

**Constitutional guarantee:** Every SHUNYA interface shall adapt to environmental conditions beyond experience class. The presentation shall respond to the user's current constraints and preferences, not only their screen size. Every environmental condition is carried in the canonical Runtime Context (§5).

### Environmental Factors

| Factor | Constitutional Requirement |
|--------|--------------------------|
| Reduced motion | All animations collapse to instant transitions preserving opacity hierarchy. See §11. Also captured in the Motion Preference dimension of Runtime Context. |
| Accessibility preferences | Increased contrast, larger type, reduced transparency — implemented without degrading information density below Capability Parity. |
| High contrast mode | All information must remain distinguishable when colour is reduced to a high-contrast palette. |
| Low bandwidth | Images, fonts, and media degrade gracefully. No feature is removed — only compressed. |
| Offline | The interface remains fully navigable. Create, read, and local-edit work. Sync resumes when connectivity returns. |
| Kiosk / public mode | No persistent authentication tokens. Navigation is restricted to the authorised scope. Gesture-based deletion is disabled. |
| Embedded mode | The interface operates within a constrained container (iframe, widget, portal). Navigation adapts to the host's chrome. |
| Touch vs. mouse vs. keyboard-first | Interaction targets, hover states, accelerator visibility, and gesture support adapt to the active input. Also captured in the Interaction Method dimension of Runtime Context. |
| Screen reader active | All content is surfaced as semantic structure. Navigation order matches visual hierarchy. |

**Constitutional rule:** Environmental adaptation must never degrade below the Capability Parity guarantee. A feature that is available on Studio Experience with full bandwidth and mouse input must also be available on the same Studio Experience with reduced motion, high contrast, keyboard-only input, and offline. Only the presentation changes.

## 7. Principle: Attention Adaptation

**Runtime Context dimension:** `Attention State`

SHUNYA's most important differentiator is not that it understands devices — it is that it understands **human attention**. The interface shall respond to the user's cognitive state, not only their screen size. The Attention State dimension of the Runtime Context captures this as a canonical, always-available signal.

**Constitutional guarantee:** Every SHUNYA interface shall adapt to the user's attention state. The presentation shall respond to what the user is doing and how they are doing it, not only to what device they are using.

### Attention States

| State | Constitutional Requirement |
|-------|--------------------------|
| Focused work | Silence notifications. Reduce chrome. Maximise workspace. Disable non-essential animations. |
| Presenting | Hide unnecessary controls. Show only the content being presented. Disable navigation that would break the flow. |
| Driving | Voice-first. All interaction is audio. Critical notifications only. Gesture and visual UI are suppressed. |
| In a meeting | Passive assistance. Notifications are deferred. The interface observes but does not interrupt. |
| Typing rapidly | The user is producing. Auto-complete, suggestions, and validation are active. UI transitions are suppressed to avoid disrupting the flow. |
| Idle / paused | The interface may dim, consolidate, or show a screensaver. All state is preserved. No data is lost. |
| Interrupted | The interface preserves the exact state the user left. On return, the user picks up exactly where they were. No reload. No restart. |

**Constitutional rule:** Attention adaptation must never override user intent. The user may override the detected attention state at any time. When attention state is uncertain, the interface shall assume the most permissive state (focused work) rather than restricting access.

**Implementation guidance:** Attention state may be detected through interaction patterns (typing speed, scroll behaviour, navigation cadence), system signals (focus mode, do-not-disturb, driving mode), calendar context, or explicit user input. The detection mechanism is an implementation decision. The resulting behaviour must match these constitutional guarantees.

## 8. Principle: Layout Composition

Every page defines a **Primary Object** (the reason the user is here), a **Secondary Object** (supporting focus), and **Supporting Context** (reference material).

The implementation shall rearrange these intentionally per experience class. The browser's default auto-layout shall not determine information architecture.

| Experience Class | Composition Guarantee |
|-----------------|----------------------|
| Compact Experience | Single-column stack: Primary → Secondary → Context |
| Personal Experience | Two-column: Primary dominates, Context as drawer |
| Shared Experience | Three-column or Primary + split secondary |
| Workstation Experience | Three-column with collapsible rails |
| Studio Experience | Three-column at comfortable width |
| Orchestration Experience | Three-column with room for expanded context |

## 9. Principle: Navigation Model

Each experience class has its own navigation model. No hamburger menu on Studio Experience. No persistent side rail on Compact Experience.

**Constitutional guarantees:**

| Experience Class | Navigation Guarantee |
|-----------------|---------------------|
| Compact Experience | Persistent bottom navigation (tabs or equivalent). No side rail. |
| Personal Experience | Collapsible top navigation or slide-out drawer. Not bottom tabs. |
| Shared Experience | Persistent or easily-revealed side navigation. |
| Workstation Experience | Persistent side navigation with labels. |
| Studio Experience | Persistent side navigation with sections. |
| Orchestration Experience | Persistent side navigation with metadata. |

## 10. Principle: Typography

**Constitutional guarantee:** SHUNYA's typographic hierarchy shall remain visually identical across all experience classes while being physically appropriate to each form factor.

The hierarchy is always:

```
Hero (one per page)
  → Section Headings
    → Body text
      → Metadata
        → Labels
```

**Constitutional rules:**

- Hero typography shall dominate the viewport while preserving comfortable reading distance
- Body text shall be readable without zoom on every supported device
- Metadata shall be distinguishable from body text without being illegible
- The hierarchy shall be immediately apparent from size alone
- Typefaces shall be consistent across all experience classes

## 11. Principle: Motion Language

SHUNYA has one motion language. The opening "शून्य" sequence — a slow, cinematic fade — establishes the visual vocabulary. Every subsequent transition inherits it.

**Constitutional guarantees:**

- All narrative transitions use a fade (opacity change) as the primary mechanism — no sudden appearance of content
- All transitions use an ease-out curve that decelerates into position
- Scene changes shall overlap slightly (the departing scene fades out as the arriving scene fades in) — no black gaps, no jump cuts
- Micro-interactions (hover, click, focus) may use faster durations but must inherit the same easing language
- When reduced motion is preferred, all animations collapse to instant transitions while preserving the opacity hierarchy

## 12. Principle: Object Continuity

No matter what experience class the user changes to, the object they are currently thinking about remains central.

**Constitutional guarantee:** When a user is focused on an object (a customer, an invoice, a task, a proposal), switching experience class shall preserve that object as the primary focus. The layout may change. The object does not.

**Example:**
```
Studio Experience:
  Customer
   ├ Timeline
   ├ AI
   └ Relationships

Compact Experience:
  Customer
   ↓
  Timeline
   ↓
  AI
```

The customer remains the focal object. The layout changes. The thinking does not.

**Implementation requirement:** Object state must survive experience class transitions. Workspace state must be portable across form factors.

## 13. Principle: Capability Parity

**Constitutional guarantee:** No experience class shall receive fewer capabilities than another. Only different presentation.

If a feature exists on Studio Experience, it must exist on Compact Experience — presented appropriately for that form factor.

**Permitted differences:**
- Edit vs. view with inline edit trigger
- Full table vs. card list with sort/filter
- Side-by-side panels vs. sequential sheets
- Drag-and-drop vs. tap-to-move

**Forbidden differences:**
- Studio Experience has a feature. Compact Experience does not.
- Studio Experience shows data. Compact Experience hides it behind an extra click.
- Studio Experience provides batch operations. Compact Experience provides single-item only.

## 14. Experience Invariants

Regardless of experience class or environment, every SHUNYA experience must preserve these six invariants. They are the litmus test for every present and future interface.

### Calm

SHUNYA does not demand attention. Navigation is predictable. Transitions are gradual. No modal, notification, or animation shall startle, interrupt, or block the user's flow. The interface recedes when the user is working and returns when the user needs it.

### Continuity

The user's mental state is never reset. Moving between devices, going offline and back online, or switching tasks preserves the user's place in every dimension: scroll position, object focus, navigation depth, and input state. No experience restarts unless the user explicitly requests it.

### Object Centrality

Every page exists because of an object. The layout may reconfigure around that object per experience class, but the object is always the anchor. No page shall present itself as a generic canvas — it must always be a canvas for something specific. See §12.

### Context Awareness

Every interface element knows the full Runtime Context — experience class, attention state, environment, interaction method, motion preference, accessibility, network, device capability, and runtime confidence. No element shall guess, assume defaults, or ignore its environment. See §5.

### Predictability

A pattern that works in one place works in every place. Navigation, typography, component behaviour, motion, and interaction patterns are consistent across every page and experience class. The user never encounters two variants of the same component. See §16 for the governing principle of adaptation predictability.

### Capability Parity

Every experience class — and every environment — has the same features. Only the presentation differs. No user is told they need a different device to accomplish their task. See §13.

**Verification:** Before any UI change is accepted, test it against all six invariants. If any invariant is violated, the change must be redesigned.

## 15. Principle: Failure Behaviour

Every architecture defines success. A great architecture also defines what happens when things fail. These constitutional guarantees ensure that SHUNYA remains usable, predictable, and safe under adverse conditions.

### Failure Modes

| Failure | Constitutional Guarantee |
|---------|------------------------|
| Runtime fails to load | The interface must still be usable. A fallback layout (Studio Experience-class behaviour implemented in static CSS) shall render without JavaScript. No blank screen. |
| AI service unavailable | The workspace continues without AI. All non-AI features (create, read, update, delete, navigate, search) remain fully functional. The user never sees a spinner waiting for AI. |
| Network disappears | The current object remains editable. All local state is preserved. Sync resumes transparently when connectivity returns. The user never loses work. |
| Adaptation system fails | The safest experience class shall be selected — Studio Experience (the most capable layout). No component guesses its own adaptation. |
| Capability uncertain | Never remove user work. If the system cannot determine whether an operation is safe, the operation shall be permitted and the user notified — not blocked. |
| Third-party service unavailable | The feature degrades gracefully. The rest of the interface is unaffected. No global timeout, no cascading failure. |
| Storage full | The user is warned before data loss is possible. The current object is always saved before any new operation is attempted. |
| Degradation visibility | Graceful degradation must never become silent degradation. When AI is unavailable, synchronisation stops, search is degraded, or any capability is reduced, the user must be able to perceive the change. The interface shall never behave differently while appearing identical to the fully-functioning state. A system that works differently but looks the same has deceived the user. |

### Safety Hierarchy

When multiple failures occur simultaneously, the system shall preserve in order:

1. **User work** — No data loss, ever.
2. **User navigation** — The user can always move to another page.
3. **User awareness** — The user is informed of degraded state without being alarmed.
4. **Feature degradation** — Non-essential features may be disabled before essential ones.
5. **Visual fidelity** — The interface may render without animations, images, or custom fonts before it loses functionality.

**Constitutional rule:** No failure mode shall result in a blank screen, infinite spinner, unresponsive interface, or data loss. If the system cannot determine the correct behaviour, it shall preserve the user's work and render the safest known layout.

## 16. Principle: Predictability over Cleverness

**Constitutional principle:** SHUNYA shall never surprise the user.

One danger of adaptive interfaces is trying to be "too smart." Every adaptation must be understandable, reversible, and predictable. The interface should feel like "Of course it did that" — never "Why did it suddenly change?"

This principle governs every adaptation decision in the Runtime Context. No adaptation, no matter how well-intentioned, may violate the user's expectation of stability.

### Understandable

Every adaptation SHUNYA makes must be obvious to the user. When the interface changes — layout, navigation, input mode, information density — the user must be able to perceive why.

**Constitutional guarantee:** The user shall never wonder why the interface changed. The cause of any adaptation shall be self-evident from the context. When the cause is not self-evident, SHUNYA shall explain the change plainly.

### Reversible

Every adaptation SHUNYA makes can be overridden by the user. The user always has the final say about their experience.

**Constitutional guarantee:** The user may manually override any adaptation decision — experience class, attention state, environment mode, or any other Runtime Context dimension — and that override shall persist until explicitly changed. No adaptation shall lock the user into a mode they cannot escape.

### Predictable

A given set of Runtime Context dimensions always produces the same adaptation. The interface does not change randomly, creatively, or experimentally. The user can predict what will happen when they move to a different device, enter a different environment, or change their attention state.

**Constitutional guarantee:** The adaptation function is deterministic with respect to the Runtime Context. Identical Runtime Context values produce identical interface behaviour. The system shall not vary its adaptation for A/B testing, personalisation, or any other purpose that would make behaviour unpredictable.

### Relationship to Experience Invariants

The Predictability invariant (§14) guarantees consistency of patterns across the interface. This principle extends that guarantee to the adaptation engine itself — the act of adapting must feel as natural and predictable as the adapted interface.

## 17. Principle: Adaptation Confidence

**Runtime Context dimension:** `Runtime Confidence`

The constitution assumes SHUNYA always knows which Experience Class to use. Reality is messier. The runtime may encounter situations where the correct adaptation is ambiguous — a foldable phone half-open, a desktop browser resized to phone width, a remote desktop session, a car display mirrored from a phone, a Vision Pro or XR headset, an external monitor connected to a tablet.

**Constitutional guarantee:** When the runtime is uncertain about the correct adaptation, SHUNYA's behaviour is governed by a defined set of guarantees. The system shall never fabricate certainty, guess at the correct experience class, or silently adapt to a potentially incorrect layout.

### Behavioural Guarantees

| Condition | Guarantee |
|-----------|-----------|
| **Signals agree on the correct experience class** | Adapt normally. The experience class selected by the canonical adaptation system is authoritative. The user may still override. |
| **Signals conflict or environment is unrecognised** | The system shall not silently adapt. It shall preserve the current layout, inform the user that the environment could not be fully determined, and expose a direct control to switch experience class manually. No automatic re-adaptation occurs while uncertainty persists. |
| **Runtime Confidence dimension is unavailable** | The system shall assume the most conservative experience class — the one that preserves the most user-visible structure. This default is not a fixed class name; it is determined at runtime by selecting the layout that exposes the most content without adaptation guesswork. |
| **User overrides the adaptation** | The user override persists until explicitly changed. The system shall not re-evaluate or override the user's choice. |
| **Uncertainty resolves** | When previously conflicting signals converge on a clear experience class, the system may notify the user and offer the option to re-adapt — but shall not re-adapt automatically. See §16 (Predictability over Cleverness) — the user decides, not the system. |

### Required Implementation Behaviour

1. **Preserve user work** — Under all conditions of adaptation uncertainty, the current object, scroll position, input state, and navigation depth are preserved exactly. No adaptation decision shall cause data loss, a page reload, or a state reset.

2. **Never fabricate confidence** — The runtime shall not report High or Medium confidence when signals disagree. The `Runtime Confidence` dimension reflects actual certainty, never an assumption, guess, or heuristic default. Fabricating confidence violates both the Predictability (§16) and Failure Behaviour (§15) principles.

3. **Provide escape at all times** — The user must be able to switch to any experience class directly, without navigating through menus, settings, or confirmation dialogs. The override control shall be visibly available at all times and require no more than one gesture or click — regardless of confidence level.

4. **Inform, never alarm** — When uncertainty arises, the user is informed of the situation plainly and without alarmist language. A simple, single-line indication that the environment could not be fully determined is sufficient. No modal, no interruption of workflow.

### Relationship to Failure Behaviour

Adaptation Confidence is distinct from the Failure Behaviour guarantees (§15). Failure Behaviour governs what happens when components break. Adaptation Confidence governs what happens when the runtime is uncertain about the correct adaptation. Both are independent concerns — a system may be confident but still fail, or uncertain but perfectly functional.

**Constitutional rule:** When adaptation confidence is Low, the Predictability over Cleverness principle (§16) takes precedence. The system shall not attempt clever adaptations, animations, or transitions while uncertain. The safest, most predictable behaviour is the only correct response.

## 18. Constitutional Archival Policy

Constitutional documents evolve. When a document is superseded — by a new version, a new constitution, or a constitutional amendment — the superseded document is **archived, not deleted**.

### Archival Rules

1. **Superseded documents are moved to an archive directory**, preserving their exact content, version, and ratification date. The archive path mirrors the source path under an `archive/` prefix (e.g., `docs/architecture/archive/dna-01-v1-device-native-architecture.md`).

2. **The archived document is read-only.** No edits are made to archived documents. Typographical corrections in the canonical version do not propagate to the archive.

3. **The archive preserves architectural history.** Future engineers can trace how constitutional thinking evolved — which principles were added, removed, or refined, and why. The archive is evidence of architectural maturity, not obsolete debris.

4. **Archived documents remain referencable by version number.** If a past implementation was built against an earlier version of the constitution, the archived document provides the exact governing principles at that time.

5. **No document is deleted.** Even if a constitutional principle is entirely superseded (not just revised), the document that introduced or governed it is archived rather than destroyed. Deleting architectural history erases the reasoning that led to the current constitution.

### Relationship to Constitutional Hierarchy

The archival policy applies to all four layers (Constitution, Experience Bible, Design System, Implementation) when a document at any layer is superseded. The archive preserves the full lineage of SHUNYA's design thinking.

## 19. Constitutional Defects (Closed)

The following are permanently closed as design violations:

- Hiding panels on smaller form factors without providing equivalent navigation or content in an appropriate presentation
- Auto-scaling grids that allow the browser to decide column count without design intent
- Fixed-size layout elements that do not scale with form factor
- Studio-first CSS that requires overriding all Studio Experience styles to achieve Compact Experience behaviour
- Any experience class receiving fewer capabilities than another

## 20. Implementation Rule

No implementation begins until this architecture is ratified. After ratification, every SHUNYA interface shall conform to these constitutional guarantees. No component shall invent its own adaptation behaviour.