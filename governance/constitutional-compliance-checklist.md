# Constitutional Compliance Checklist (DNA-CC-01)

**Status:** Governance — Active  
**Dependency:** SHUNYA Constitution (hierarchy); DNA-01 v2.1 (Under Founder Review)  
**Scope:** Every implementation, execution mode, and feature acceptance  
**Rule:** No feature shall be accepted without constitutional traceability

---

## 1. Mandate

Per the Constitutional Freeze directive, every future execution mode declared complete must verify compliance against the applicable constitutional document(s). This checklist is the canonical verification instrument for DNA-01 (Technical Constitution). It enumerates every constitutional principle, its verification criteria, the evidence required, and the compliance severity level.

**Compliance is risk-weighted.** Criteria are classified as Critical, Major, or Minor:
- **Critical** — architectural invariants. Execution stops on failure. Feature rejected or redesigned.
- **Major** — workflow and UX. Execution proceeds with required remediation plan. Feature may not ship with Major failures.
- **Minor** — polish. Recorded and queued for iterative refinement. Execution may proceed.

---

## 2. Severity Taxonomy

| Level | Definition | Gate |
|-------|-----------|------|
| **Critical** | Architectural invariant. Violation breaks a constitutional guarantee, user safety, data integrity, or a foundational principle (Device-Native, Capability Parity, Predictability, Failure Behaviour, etc.). | Execution stops. Feature must be redesigned. |
| **Major** | Workflow or UX degradation. Violation reduces usability, discoverability, efficiency, or accessibility but does not break an architectural invariant. | Execution proceeds with mandatory remediation plan. Feature does not ship with Major violations. |
| **Minor** | Polish or refinement. Violation affects visual consistency, animation smoothness, micro-interaction quality, or non-essential presentation. | Recorded in observation log. Queued for iterative refinement. Execution proceeds. |

---

## 3. Compliance by Constitutional Principle

### 3.1 Runtime Context (§5)

Every component receives the canonical Runtime Context with all 9 dimensions.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| RC-01 | **Critical** | Every component receives the full Runtime Context (experienceClass, attentionState, environment, interactionMethod, motionPreference, accessibility, network, deviceCapability, runtimeConfidence) | [ ] | Code review: component entry point |
| RC-02 | **Critical** | Runtime Context is available before first render | [ ] | Render timing trace |
| RC-03 | Major | Changes to any dimension propagate to all components within a perceptible timeframe | [ ] | Propagation timing measurement |
| RC-04 | **Critical** | No component guesses its environment — all components read from the canonical Runtime Context | [ ] | Code search: inline detection logic |
| RC-05 | **Critical** | The same Runtime Context is available to CSS, JavaScript, and server-rendered templates | [ ] | Integration test per delivery channel |
| RC-06 | **Critical** | Runtime Context is not used for analytics, profiling, or personalisation that would violate Predictability | [ ] | Code review: context consumers |

### 3.2 Experience Classes (§3)

Exactly six canonical experience classes. Every implementation supports all ratified classes.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| EC-01 | **Critical** | All six experience classes (EXP-01 through EXP-06) are implemented with intentional layouts | [ ] | Visual audit per class |
| EC-02 | **Critical** | No experience class layout is derived from another — each is designed from scratch in intent | [ ] | CSS review: no shared base styles |
| EC-03 | Major | A user on any class cannot infer which layout was designed first | [ ] | User test: blind comparison |
| EC-04 | **Critical** | Exactly one experience class is active at any time | [ ] | Runtime trace |
| EC-05 | **Critical** | The implementation maps hardware to experience class through the canonical adaptation system | [ ] | Code review: mapping logic |

### 3.3 Object Continuity (§12)

The object remains central across device transitions.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| OC-01 | **Critical** | Switching experience class preserves the current object as primary focus | [ ] | Screen recording: class switch |
| OC-02 | **Critical** | Object state survives experience class transitions | [ ] | State comparison before/after |
| OC-03 | Major | Workspace state is portable across form factors | [ ] | Session transfer test |
| OC-04 | **Critical** | No object data is lost during class transition | [ ] | Data integrity check |

### 3.4 Capability Parity (§13)

Every experience class has the same features. Only presentation differs.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| CP-01 | **Critical** | Every feature available on Studio Experience has an equivalent on Compact Experience | [ ] | Feature matrix audit |
| CP-02 | **Critical** | Compact Experience is not a subset of Studio Experience — features are presented differently, not hidden | [ ] | Per-class feature comparison |
| CP-03 | Major | No feature is hidden behind an extra click on any class unless the same extra click exists on all classes | [ ] | Click-path measurement |
| CP-04 | Major | Batch operations exist on all classes (not only Studio Experience) | [ ] | Functional test per class |

### 3.5 Motion Language (§11)

One fade-based vocabulary throughout.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| ML-01 | **Critical** | All narrative transitions use fade (opacity change) as the primary mechanism | [ ] | 30fps recording per transition |
| ML-02 | Major | All transitions use ease-out curve that decelerates into position | [ ] | Animation curve trace |
| ML-03 | Major | Scene changes overlap — no black gaps, no jump cuts | [ ] | 30fps recording: overlap measurement |
| ML-04 | Minor | Micro-interactions inherit the same easing language | [ ] | Code review: animation definitions |
| ML-05 | **Critical** | When reduced motion is preferred, all animations collapse to instant transitions preserving opacity hierarchy | [ ] | Reduced-motion mode recording |
| ML-06 | **Critical** | Prohibited types (slide, scale, rotate, bounce, parallax, stagger, typewriter, flash/glitch) are absent | [ ] | Code search: animation types |

### 3.6 Predictability over Cleverness (§16)

SHUNYA shall never surprise the user.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| PR-01 | **Critical** | Every adaptation is understandable — the user can perceive why the interface changed | [ ] | User test: explain adaptation |
| PR-02 | **Critical** | Every adaptation is reversible — the user can override any adaptation decision | [ ] | Override test per context dimension |
| PR-03 | **Critical** | Every adaptation is predictable — identical Runtime Context values produce identical behaviour | [ ] | Determinism test (same input, same output) |
| PR-04 | **Critical** | The adaptation function does not vary for A/B testing, personalisation, or any non-deterministic purpose | [ ] | Code review: adaptation logic |
| PR-05 | Major | User overrides persist until explicitly changed | [ ] | Persistence test |

### 3.7 Failure Behaviour (§15)

What the system guarantees when things break.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| FB-01 | **Critical** | If runtime fails to load, the interface is still usable (static CSS fallback, no blank screen) | [ ] | JS-disabled render test |
| FB-02 | **Critical** | If AI service is unavailable, the workspace continues without AI (no spinner waiting for AI) | [ ] | AI-offline functional test |
| FB-03 | **Critical** | If network disappears, the current object remains editable; sync resumes transparently | [ ] | Offline edit + reconnect test |
| FB-04 | **Critical** | If adaptation system fails, the safest experience class is selected (most capable layout) | [ ] | Adaptation failure simulation |
| FB-05 | **Critical** | If capability is uncertain, user work is never removed — operation is permitted and user notified | [ ] | Uncertainty behaviour test |
| FB-06 | **Critical** | If third-party service is unavailable, the feature degrades gracefully — no global timeout | [ ] | Service failure isolation test |
| FB-07 | **Critical** | Graceful degradation is never silent degradation — user perceives when capability is reduced | [ ] | Degradation visibility audit |
| FB-08 | **Critical** | Safety hierarchy preserved: user work > navigation > awareness > features > visual fidelity | [ ] | Multi-failure scenario test |
| FB-09 | **Critical** | No failure mode results in blank screen, infinite spinner, unresponsive interface, or data loss | [ ] | Failure mode matrix verification |

### 3.8 Adaptation Confidence (§17)

Behavioural guarantees when the runtime is uncertain.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| AC-01 | Major | When signals agree: adapt normally, override control remains available | [ ] | Normal adaptation test |
| AC-02 | **Critical** | When signals conflict: preserve current layout, inform user, expose manual class selector, no automatic re-adaptation | [ ] | Conflict simulation test |
| AC-03 | **Critical** | When Runtime Confidence dimension is unavailable: select most conservative layout (not a fixed default class) | [ ] | Confidence-absent test |
| AC-04 | Major | When user overrides: override persists until explicitly changed — system does not re-evaluate user's choice | [ ] | Override persistence test |
| AC-05 | Major | When uncertainty resolves: notify user, offer re-adaptation option, do not re-adapt automatically | [ ] | Uncertainty resolution test |
| AC-06 | **Critical** | User work is preserved under all adaptation uncertainty conditions | [ ] | State preservation test |
| AC-07 | **Critical** | Runtime never fabricates confidence — reports actual certainty | [ ] | Confidence honesty audit |
| AC-08 | **Critical** | Escape control is visibly available at all times, requires no more than one gesture/click | [ ] | Accessibility audit |

### 3.9 Environmental Adaptation (§6)

Response to conditions beyond screen size.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| EA-01 | **Critical** | Reduced motion: all animations collapse to instant transitions | [ ] | Reduced-motion recording |
| EA-02 | **Critical** | Accessibility preferences: increased contrast, larger type, reduced transparency without degrading information density | [ ] | Accessibility mode audit |
| EA-03 | **Critical** | High contrast mode: all information remains distinguishable | [ ] | High-contrast render audit |
| EA-04 | Major | Low bandwidth: images, fonts, media degrade gracefully — no feature removed, only compressed | [ ] | Bandwidth throttling test |
| EA-05 | **Critical** | Offline: interface fully navigable, create/read/local-edit work, sync resumes transparently | [ ] | Offline functional test |
| EA-06 | Major | Kiosk/public mode: no persistent auth tokens, restricted navigation, gesture deletion disabled | [ ] | Kiosk mode audit |
| EA-07 | Minor | Embedded mode: navigation adapts to host chrome | [ ] | Embedded render test |
| EA-08 | Major | Touch vs mouse vs keyboard-first: targets, hover, shortcuts, gestures adapt to active input | [ ] | Interaction method switch test |
| EA-09 | **Critical** | Screen reader active: all content surfaced as semantic structure, navigation order matches visual hierarchy | [ ] | Screen reader audit |
| EA-10 | **Critical** | Environmental adaptation never degrades below Capability Parity guarantee | [ ] | Cross-environment parity audit |

### 3.10 Attention Adaptation (§7)

Response to the user's cognitive state.

| # | Severity | Criterion | Pass/Fail | Evidence Required |
|---|----------|-----------|-----------|-------------------|
| AA-01 | Major | Focused work: silence notifications, reduce chrome, maximise workspace, disable non-essential animations | [ ] | Focused mode test |
| AA-02 | Major | Presenting: hide unnecessary controls, show only presented content, disable flow-breaking navigation | [ ] | Presenting mode audit |
| AA-03 | Major | Driving: voice-first, critical notifications only, gesture/visual UI suppressed | [ ] | Driving mode test |
| AA-04 | Major | In meeting: passive assistance, notifications deferred, observe without interrupting | [ ] | Meeting mode audit |
| AA-05 | Minor | Typing rapidly: auto-complete/suggestions/validation active, UI transitions suppressed | [ ] | Typing mode test |
| AA-06 | Major | Idle/paused: interface may dim/consolidate, all state preserved, no data lost | [ ] | Idle mode test |
| AA-07 | **Critical** | Interrupted: exact state preserved on return — no reload, no restart | [ ] | Interruption recovery test |
| AA-08 | **Critical** | Attention adaptation never overrides user intent — user may override detected state at any time | [ ] | Override test |
| AA-09 | Major | When attention state is uncertain, assume most permissive state (focused work) | [ ] | Uncertainty fallback test |

---

## 4. Verification Rule

Every implementation change must be tested against:

1. **All six Experience Invariants** (§14): Calm, Continuity, Object Centrality, Context Awareness, Predictability, Capability Parity
2. **All applicable constitutional criteria** from the sections above, filtered by severity
3. **The principle of Predictability over Cleverness** (§16) as the governing meta-rule

**Critical** criteria are gating — any failure blocks execution.  
**Major** criteria require a documented remediation plan before feature acceptance.  
**Minor** criteria are recorded in the observation log for iterative refinement.

A feature that passes all **Critical** criteria and has remediation plans for all **Major** failures is **Conditionally Compliant**.  
A feature that passes all **Critical** and **Major** criteria is **Constitutionally Compliant**.  
A feature that fails any **Critical** criterion is **Constitutionally Defective** and must be rejected or redesigned.

---

## 5. Compliance Scoring

| Result | Meaning | Action |
|--------|---------|--------|
| **PASS** | All criteria satisfied (Critical, Major, Minor) | Feature may proceed |
| **PASS-WITH-OBSERVATIONS** | All Critical and Major satisfied; Minor observations recorded | Proceed, log observations |
| **CONDITIONAL-PASS** | All Critical satisfied; Major failures have documented remediation plan | Proceed with mandatory remediation tracking. Feature does not ship until Major resolved. |
| **FAIL-CRITICAL** | Any Critical criterion failed | Execution stops. Feature rejected, design reset required. |
| **FAIL-MAJOR** | Any Major criterion failed without remediation plan | Execution stops. Remediation plan required before re-review. |

---

## 6. Document History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | Initial creation per Constitutional Freeze directive | Hermes Agent |
| 2.0 | 2026-07-28 | Revised per DIRECTIVE — DNA-01 RATIFICATION REVISION: introduced Critical/Major/Minor severity taxonomy, risk-weighted compliance scoring, execution-stop only on Critical failures, severity tags on all 72 criteria | Hermes Agent |