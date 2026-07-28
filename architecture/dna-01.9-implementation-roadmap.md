# Implementation Roadmap (DNA-01.9)

**Status:** Design — Not Yet Ratified  
**Version:** 2.0  
**Dependency:** All DNA-01 documents must be ratified before implementation begins

---

## 1. Implementation Rule

**No implementation shall begin until the founder has ratified this architecture.**

After ratification, every SHUNYA interface shall conform to this Device-Native Architecture. No component shall invent its own adaptation behaviour.

## 2. Phasing Strategy

The roadmap is ordered by risk and impact. Low-risk, high-visibility changes come first to validate the architecture. High-risk, foundational changes come after patterns are proven.

Each phase describes **behavioural goals** — what the user and developer experience after implementation. The specific implementation techniques (media queries, runtime, CSS variables, or other) are not prescribed. The goals determine success.

### Phase 0 — Ratification (founder action)

- [ ] Review DNA-01 Device-Native Architecture (Core)
- [ ] Review DNA-01.2 Runtime Context Spec
- [ ] Review DNA-01.3 Device Matrix
- [ ] Review DNA-01.4 Component Adaptation Spec
- [ ] Review DNA-01.5 Typography Spec
- [ ] Review DNA-01.6 Layout Matrix
- [ ] Review DNA-01.7 Motion & Transition Spec
- [ ] Review DNA-01.8 Homepage Narrative Flow Spec
- [ ] Review DNA-01.9 Implementation Roadmap (this document)
- [ ] Ratify or return with corrections

### Phase 1 — Adaptation Infrastructure (foundation, 3–5 days)

Build the context layer that enables all components to adapt.

**Behavioural goals:**
- Every component has access to the canonical device context (device class, orientation, interaction method, safe areas, reduced motion preference)
- Device context is available at first render
- Context changes (orientation, resize) propagate to all components within a perceptible timeframe
- Non-React consumers (templates, legacy pages) also receive context through a mechanism they can read
- A graceful fallback exists if the context system fails — Studio Experience, always a valid experience

**Risk:** Low — isolated layer, no component changes
**Dependency:** None

**Verification:**
- [ ] Every component receives device context [Y/N]
- [ ] Rotating the device propagates the change [Y/N]
- [ ] Fallback experience is functional [Y/N]

### Phase 2 — Homepage Narrative Flow (high-visibility, 3–5 days)

Fix the two constitutional defects identified by the founder.

**Behavioural goals:**
- The शून्य → Scene One transition has an overlapping crossfade — the two scenes feel connected, not abrupt
- Scene Five's five phases (Relationship, Proposal, Finance, Intelligence, CALM) occupy one continuous scroll chapter, not five separate pages
- "One Operating System" heading remains pinned during the phase scroll
- Phase cards are compact (not full-viewport)
- Summary grid follows immediately after CALM with no gap
- Scene Six → Footer transition is smooth, not disconnected

**Key deliverables:**
- `homepage.tsx` — rewrite to comply with DNA-01.8 narrative flow
- Recording (30fps) showing the शून्य → One OS crossfade has ≥300ms overlap

**Risk:** Medium — visual regression risk, but contained to one file
**Dependency:** Phase 1 (needs context for device-aware adaptation)

### Phase 3 — Workspace Shell (highest impact, 4–6 days)

Redesign the three-zone layout to be device-native.

**Behavioural goals:**
- Compact Experience workspace: single-column with bottom navigation, context as slide-up sheet
- Personal/Shared Experience workspace: two-column or three-column depending on orientation, compact navigation
- Studio Experience workspace: three-column with labelled persistent rails
- No panel is hidden on any device — every class has intentional navigation
- Safe areas are respected

**Key deliverables:**
- Device-native workspace shell functioning on all six classes
- `workspace-shell.tsx` adaptation logic

**Risk:** High — touches every workspace component
**Dependency:** Phase 1 (context), Phase 2 (proves adaptation pattern)

### Phase 4 — Typography System (medium impact, 2–3 days)

Implement per-device typographic hierarchy.

**Behavioural goals:**
- Typography hierarchy matches DNA-01.5 on every device class
- Hero dominates the viewport proportionally on every class
- Body text is readable without zoom
- Metadata is distinguishable from body text
- No inline font-size values that bypass the canonical hierarchy

**Key deliverables:**
- Typography scale expressed through the adaptation system
- Zero inline font-size values that diverge from the hierarchy

**Risk:** Low-medium — mechanical replacement, but many files touched
**Dependency:** Phase 1 (context), parallel with Phase 2 and 3

### Phase 5 — Component Adaptation (medium-high impact, 5–8 days)

Implement the Component Adaptation Specification for all major components.

**Behavioural goals:**
- Every component in DNA-01.4 behaves correctly on every device class
- No component uses "same as desktop" behaviour on phone
- Navigation adapts per class: bottom tabs (phone) → compact rail (tablet) → labelled rail (desktop)
- Context panel adapts per class: sheet overlay (phone) → drawer (tablet) → persistent (desktop)
- Object cards use appropriate column counts per class
- Tables become key-value lists on phone
- Dialogs become bottom sheets on phone

| Component | Effort (days) |
|-----------|--------------|
| Navigation (top bar) | 1 |
| Side rail → bottom tabs | 2 |
| Context panel as drawer/sheet | 1 |
| Object cards (per-class grid) | 1 |
| Search (full-screen on phone) | 1 |
| Dialogs (bottom sheet on phone) | 0.5 |
| Tables (key-value list on phone) | 1.5 |
| Forms (single column on phone) | 0.5 |
| Authentication (full-bleed phone) | 0.5 |
| AI/Copilot (full-screen on phone) | 1 |
| Empty states | 0.5 |
| Footer | 0.5 |

**Total:** ~10 days

**Risk:** Medium-high — many components, coordination needed
**Dependency:** Phase 1 (context), Phase 3 (workspace shell)

### Phase 6 — Grid & Layout (medium impact, 2–3 days)

Ensure all grids use explicit per-class column counts.

**Behavioural goals:**
- Every grid layout specifies its column count per device class
- No grid layout leaves column count to the browser
- All grid layouts match the Layout Matrix (DNA-01.6)

**Risk:** Low — mechanical with visual verification
**Dependency:** Phase 1 (context)

### Phase 7 — Legacy Templates (low-medium impact, 3–5 days)

The Jinja2 templates (settings, leads, tasks, calendar, etc.) are transitional/legacy. They need the adaptation system.

**Behavioural goals:**
- Legacy templates receive device context via a mechanism they can read
- Legacy template layouts adapt per class
- Safe areas are respected in legacy templates

**Risk:** Low — these are legacy templates with known migration path
**Dependency:** Phase 1 (context), Phase 4 (typography)

### Phase 8 — Motion Audit (verification, 1–2 days)

Verify all transitions conform to DNA-01.7.

**Behavioural goals:**
- All transitions use the canonical fade vocabulary
- All transitions decelerate (ease-out) into their final state
- Reduced motion collapses all animations
- No prohibited animation types are present

**Risk:** Low — audit + minor fixes
**Dependency:** All phases complete (full system to audit)

## 3. Timeline Estimate

| Phase | Description | Duration | Parallel |
|-------|-------------|----------|----------|
| 0 | Ratification | — | — |
| 1 | Adaptation Infrastructure | 3–5 days | — |
| 2 | Homepage Narrative Flow | 3–5 days | After P1 |
| 3 | Workspace Shell | 4–6 days | After P1 |
| 4 | Typography System | 2–3 days | Parallel with P2/P3 |
| 5 | Component Adaptation | 5–8 days | After P3 |
| 6 | Grid & Layout | 2–3 days | After P1, parallel |
| 7 | Legacy Templates | 3–5 days | After P4 |
| 8 | Motion Audit | 1–2 days | After P5 |

**Total implementation:** ~20–35 days (5–8 weeks)  
**Parallelised:** ~15–25 days (3–5 weeks) with Phases 2, 3, and 4 running in parallel after Phase 1.

## 4. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Context detection fails on edge case | Low | Medium | Most conservative layout fallback is always valid — no single experience class is the only safe option |
| Workspace shell regression breaks existing features | Medium | High | Comprehensive test suite before/after |
| Motion language change feels unfamiliar | Medium | Low | Gradual transition, communicate visual refresh |
| Component adaptation matrix is incomplete | Low | Medium | Add missing components as discovered |
| Legacy templates cannot be migrated | Medium | Low | Context injection works without migration |
| Typography refactor misses inline values | Medium | Low | Automated search across codebase |

## 5. Success Criteria

The architecture is successfully implemented when:

- Each of the six device classes renders a purpose-built experience
- The homepage शून्य → Scene One transition has an overlapping crossfade (≥300ms)
- Scene Five fits in a continuous scroll chapter (not five separate pages)
- Every workspace panel has an intentional phone equivalent (no hidden panels)
- Object continuity is verifiable: switching from desktop to phone preserves the current object
- Capability parity is verifiable: every feature available on desktop has an equivalent on phone
- All transitions use the canonical fade vocabulary
- Reduced motion collapses all animations
- Safe areas are respected on all devices
- The user cannot infer which layout was designed first
- No component invents its own adaptation behaviour outside the canonical system