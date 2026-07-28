# Runtime Context Specification (DNA-01.2)

**Status:** Design — Not Yet Ratified
**Version:** 3.0
**Supersedes:** DNA-01.2 Universal Adaptive Runtime Specification (v2.1)
**Dependency:** DNA-01 Device-Native Architecture

---

## 1. Purpose

The **Runtime Context** is the canonical object that every SHUNYA component receives. It captures every dimension of the user's current situation — not only which device they are using, but what they are doing, how they are interacting, what environment they are in, and how confident the system is in its adaptation.

This document defines **what information must be available**, not **how that information is obtained**. The implementation decides the detection mechanism, delivery mechanism, and update strategy — provided the resulting behaviour matches the constitutional design.

```text
Runtime Context
├── Experience Class
├── Attention State
├── Environment
├── Interaction Method
├── Motion Preference
├── Accessibility
├── Network
├── Device Capability
└── Runtime Confidence
```

## 2. Contract: The Runtime Context Object

Every component in SHUNYA shall receive the full Runtime Context. The implementation decides the delivery mechanism (CSS custom properties, React context, global object, CSS classes, attribute selectors, or any combination).

### 2.1 Experience Class (Required)

**Canonical ID:** `experienceClass`

The six canonical experience classes. See DNA-01 §3.

| Value | Intended Behaviour |
|-------|-------------------|
| `EXP-01` — Compact Experience | Single-column, touch-first, bottom navigation |
| `EXP-02` — Personal Experience | Two-column or drawer-based, touch/keyboard hybrid |
| `EXP-03` — Shared Experience | Three-column or split-view, persistent navigation |
| `EXP-04` — Workstation Experience | Three-column with labelled rails, keyboard-driven |
| `EXP-05` — Studio Experience | Three-column with generous spacing, full interaction |
| `EXP-06` — Orchestration Experience | Three-column with expanded context, multi-panel |

**Guarantee:** Exactly one experience class is active at any time. The experience class is determined by the canonical adaptation system. When the runtime is uncertain about the correct class — see DNA-01 §17 for the behavioural guarantees that govern adaptation uncertainty.

### 2.2 Attention State (Required)

**Canonical ID:** `attentionState`

The user's cognitive mode. See DNA-01 §7.

| Value | Meaning |
|-------|---------|
| `focused` | Deep work. Silence notifications. Reduce chrome. |
| `presenting` | Showing content to others. Hide controls. |
| `driving` | Voice-first. Critical notifications only. |
| `in-meeting` | Passive assistance. Defer notifications. |
| `typing` | Producing content. Suppress transitions. |
| `idle` | Not actively interacting. Dim, consolidate. |
| `interrupted` | Left mid-task. Preserve exact state. |

**Guarantee:** Attention state is always available. When uncertain, the system shall assume `focused` — the most permissive state. The user may override the detected state at any time.

### 2.3 Environment (Required)

**Canonical ID:** `environment`

Environmental conditions beyond form factor. See DNA-01 §6.

| Dimension | Values | Description |
|-----------|--------|-------------|
| `reducedMotion` | `yes`, `no` | User prefers reduced motion (may overlap with Motion Preference) |
| `highContrast` | `yes`, `no` | High contrast mode active |
| `accessibilityPrefs` | `default`, `large-type`, `reduced-transparency`, `custom` | Active accessibility preferences |
| `bandwidth` | `full`, `low`, `metered` | Network bandwidth quality |
| `connectivity` | `online`, `offline`, `intermittent` | Network connectivity state |
| `mode` | `normal`, `kiosk`, `embedded`, `public` | Operating mode |
| `screenReader` | `active`, `inactive` | Screen reader state |

**Guarantee:** All environment dimensions are available at all times. Default values are the most conservative (e.g., `bandwidth: full`, `connectivity: online`, `mode: normal`).

### 2.4 Interaction Method (Required)

**Canonical ID:** `interactionMethod`

The active input modality.

| Value | Description |
|-------|-------------|
| `touch` | Touch-primary input |
| `mouse` | Pointing device primary |
| `keyboard` | Keyboard-only navigation |
| `hybrid` | Multiple input methods active simultaneously |
| `assistive` | Assistive technology (switch, eye-tracking, voice) |

**Guarantee:** The primary interaction method is identified. Components may use this to adjust target sizes, hover behaviour, shortcut visibility, and gesture support. The method may change during a session (e.g., keyboard attached to tablet).

### 2.5 Motion Preference (Required)

**Canonical ID:** `motionPreference`

Whether the user prefers reduced motion — separate from the environment dimension to allow independent detection and override.

| Value | Meaning |
|-------|---------|
| `reduced` | All animations collapse to instant transitions |
| `full` | Normal motion language applies |

**Guarantee:** When `reduced` is active, every animation, transition, and micro-interaction collapses to instant opacity changes. The opacity hierarchy is preserved — content still appears in the correct order, but without motion. See DNA-01 §11.

### 2.6 Accessibility (Required)

**Canonical ID:** `accessibility`

Active accessibility preferences beyond motion.

| Dimension | Values | Description |
|-----------|--------|-------------|
| `contrast` | `normal`, `increased`, `high` | Contrast preference |
| `fontScale` | `100%`, `125%`, `150%`, `200%` | Font size scaling |
| `colourScheme` | `system`, `light`, `dark`, `high-contrast` | Colour scheme preference |
| `reducedTransparency` | `yes`, `no` | Transparency reduction |

**Guarantee:** Accessibility preferences are applied without degrading information density below the Capability Parity guarantee. See DNA-01 §13.

### 2.7 Network (Required)

**Canonical ID:** `network`

Connectivity state — separated from the environment dimension for independent detection and override.

| Dimension | Values | Description |
|-----------|--------|-------------|
| `state` | `online`, `offline`, `metered`, `degraded` | Connectivity status |
| `latency` | `low`, `high`, `unknown` | Observed latency |
| `bandwidth` | `full`, `reduced`, `minimal` | Estimated bandwidth |

**Guarantee:** The interface is fully navigable in all network states. Create, read, and local-edit work offline. Sync resumes transparently when connectivity returns. No feature is removed — only presentation changes (e.g., images degrade, auto-save defers).

### 2.8 Device Capability (Required)

**Canonical ID:** `deviceCapability`

Hardware capabilities that influence adaptation decisions.

| Dimension | Values | Description |
|-----------|--------|-------------|
| `displayDensity` | Pixel ratio (e.g., `1.0`, `2.0`, `3.0`) | Screen pixel density |
| `safeArea` | `{top, bottom, left, right}` | Hardware-safe boundaries |
| `orientation` | `portrait`, `landscape` | Current orientation |
| `inputCoexistence` | `yes`, `no` | Whether multiple input methods can be active (e.g., touch + keyboard on tablet) |
| `sensors` | `[]` | Available sensors (accelerometer, gyroscope, ambient light, proximity) |
| `formFactor` | `phone`, `tablet`, `laptop`, `desktop`, `large-desktop`, `foldable`, `xr`, `embedded`, `unknown` | Physical form factor (distinct from experience class — the implementation maps this to an EXP class) |

**Guarantee:** Device Capability is determined from hardware signals, user-agent hints, and system APIs. The implementation shall not fabricate capability data. When capability is unknown, the most conservative value is assumed (e.g., `formFactor: unknown`).

### 2.9 Runtime Confidence (Required)

**Canonical ID:** `runtimeConfidence`

The system's certainty in its adaptation decision. This dimension captures whether contextual signals agree or conflict — not a numerical score. See DNA-01 §17 for the full behavioural guarantees.

| State | Meaning | Implementation Behaviour |
|-------|---------|------------------------|
| **Certain** | All contextual signals converge on one experience class | Adapt normally. The override control remains available. |
| **Uncertain** | Signals conflict, or the environment is not recognised | Preserve current layout. Inform the user. Expose manual experience class selector. Do not re-adapt automatically. |

**Guarantee:** Runtime Confidence is always available and is the first dimension the adaptation system evaluates. When uncertain, the system shall not adapt until uncertainty resolves through user action (see DNA-01 §17).

## 3. Reliability Guarantees

| Guarantee | Description |
|-----------|-------------|
| **Availability** | Runtime Context is available before first render |
| **Reactivity** | Changes to any dimension are propagated within a perceptible timeframe |
| **Accuracy** | Context reflects the actual device and environment, not a guessed or simulated state |
| **Graceful fallback** | If Runtime Context is entirely unavailable, the fallback is the most conservative layout — the one that preserves the most user-visible structure across all dimensions, with all other context dimensions set to their most conservative defaults |
| **Consistency** | Every component sees the same Runtime Context in the same render cycle |
| **Determinism** | Identical Runtime Context values always produce identical interface behaviour (see DNA-01 §16) |

## 4. What the Implementation Must Not Do

The implementation must not:

- Require every component to repeat detection logic
- Block rendering while determining any dimension of the Runtime Context
- Assume a single interaction method (e.g., mouse-only on desktop)
- Force all components into a single adaptation mechanism
- Hide any dimension of the Runtime Context from any component layer (CSS, JS, templates)
- Fabricate certainty where none exists (e.g., adapting as if certain when signals conflict)
- Use the Runtime Context for any purpose other than adaptation (e.g., analytics, profiling, personalisation that would violate Predictability)

## 5. Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| DNA-01 §5 | Defines the Runtime Context as the canonical adaptation system |
| DNA-01 §6 | Environment dimension constitutional requirements |
| DNA-01 §7 | Attention State dimension constitutional requirements |
| DNA-01 §16 | Predictability over Cleverness — governs how Runtime Context changes are applied |
| DNA-01 §17 | Adaptation Confidence — behavioural guarantees when the runtime is uncertain |
| DNA-01.3 | Device Matrix — maps hardware to experience classes |
| DNA-01.4 | Component Adaptation — defines per-class behaviour |

## 6. Verification Criteria

Before ratification, the Runtime Context system must pass:

- [ ] Every component receives the full Runtime Context with all 9 dimensions [Y/N]
- [ ] Changing any dimension propagates to all components within a perceptible timeframe [Y/N]
- [ ] When Runtime Confidence is Uncertain, the behavioural guarantees activate (preserve work, inform user, expose manual override, no automatic re-adaptation) [Y/N]
- [ ] The user can override any Runtime Context dimension and the override persists [Y/N]
- [ ] When Runtime Context is entirely unavailable, the most conservative layout renders without JavaScript [Y/N]
- [ ] Identical Runtime Context values produce identical interface behaviour [Y/N]
- [ ] A component can distinguish between all interaction methods [Y/N]
- [ ] Network state changes (online → offline → online) propagate without data loss [Y/N]
- [ ] No content is occluded by device safe areas across all experience classes [Y/N]
- [ ] The same Runtime Context is available to CSS, JavaScript, and server-rendered templates [Y/N]