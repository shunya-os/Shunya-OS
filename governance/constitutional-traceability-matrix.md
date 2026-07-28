# Constitutional Traceability Matrix — Technical Constitution (DNA-CTM-01)

**Status:** Governance — Active  
**Dependency:** SHUNYA Constitution (hierarchy); DNA-01 v2.1 (Under Founder Review)  
**Purpose:** Maps every implementation domain to the Technical Constitution (DNA-01) section that governs it. Every feature must trace to at least one constitutional principle.

---

## 1. Context

DNA-01 is the **Technical Constitution** within the SHUNYA Constitution hierarchy:

```
SHUNYA Constitution
├── Product Constitution       ← Own traceability matrix (separate document)
│   ├── Experience Canon
│   ├── Presence Canon
│   ├── AI Collaboration Canon
│   ├── Navigation Canon
│   └── Workspace Model
├── Technical Constitution     ← THIS MATRIX. DNA-01
│   └── DNA-01 (Device-Native)
├── Design System
└── Implementation
```

This matrix covers only the Technical Constitution domain. Other constitutional documents have their own traceability matrices. A feature that implicates multiple constitutional domains must satisfy all applicable matrices.

---

## 2. Domain-to-Constitution Mapping

| Domain | Governing Principle(s) | DNA-01 Section | Severity | Key Guarantees |
|--------|----------------------|----------------|----------|----------------|
| **Homepage** | Layout Composition, Motion Language, Object Continuity, Experience Invariants | §8, §11, §12, §14 | **Critical** | Intentional per-class layout, fade-based narrative transitions, object remains central, six invariants satisfied |
| **Authentication** | Capability Parity, Navigation Model, Layout Composition | §13, §9, §8 | **Critical** | Auth on all classes, navigation per class, intentional layout per class |
| **Workspace** | Layout Composition, Navigation Model, Object Continuity, Capability Parity | §8, §9, §12, §13 | **Critical** | Three-zone layout, per-class navigation, object survives transitions, same features every class |
| **Navigation** | Navigation Model, Device-Native Never Desktop-Reduced | §9, §4 | **Critical** | Per-class navigation: bottom tabs (Compact) → collapsible (Personal) → persistent rail (Studio). No hidden-then-revealed |
| **Runtime Context** | Runtime Context, Environmental Adaptation, Attention Adaptation | §5, §6, §7 | **Critical** | 9-dimension canonical object, every component receives same context, adaptation to environment and attention |
| **Motion** | Motion Language | §11 | **Critical** | One fade-based vocabulary, ease-out curve, overlapping scenes, reduced-motion collapse |
| **Adaptive Layouts** | Layout Composition, Adaptation Confidence, Predictability over Cleverness | §8, §17, §16 | **Critical** | Intentional rearrangement per class, behavioural guarantees under uncertainty, deterministic predictable adaptation |
| **Typography** | Typography | §10 | Major | Consistent hierarchy across classes, readable without zoom, perceptually identical ratios |
| **Component Composition** | Component Adaptation, Capability Parity | DNA-01.4, §13 | **Critical** | Explicit per-class behaviour for every component, no "same as Studio" on Compact |
| **Failure Modes** | Failure Behaviour | §15 | **Critical** | 9 failure guarantees, safety hierarchy, no blank screen or data loss |
| **Adaptation Engine** | Adaptation Confidence, Predictability over Cleverness, Runtime Context | §17, §16, §5 | **Critical** | Deterministic adaptation, behavioural guarantees under uncertainty, authoritative context |
| **Attention States** | Attention Adaptation | §7 | Major | 7 attention states, override always available, most permissive state when uncertain |
| **Environmental Response** | Environmental Adaptation | §6 | **Critical** | 9 environmental factors, graceful degradation without silent degradation |
| **Object Management** | Object Continuity | §12 | **Critical** | Object remains central across class transitions, state survives |
| **Offline / Connectivity** | Environmental Adaptation, Failure Behaviour | §6, §15 | **Critical** | Fully navigable offline, create/read/local-edit work, sync resumes transparently |
| **AI Integration** | Capability Parity, Failure Behaviour | §13, §15 | **Critical** | AI on all classes, non-AI features work when AI unavailable |

---

## 3. Principle-to-Domain Mapping (Inverse)

| Principle | Section | Severity | Domains Governed |
|-----------|---------|----------|------------------|
| Device-Native, Never Desktop-Reduced | §4 | **Critical** | All layouts, all classes |
| Runtime Context | §5 | **Critical** | Every component, adaptation engine, all feature code |
| Environmental Adaptation | §6 | **Critical** | Offline, accessibility, bandwidth, kiosk/embedded, input methods, screen reader, reduced motion |
| Attention Adaptation | §7 | Major | Workspace chrome, notifications, interruptions, driving mode, presenting mode |
| Layout Composition | §8 | **Critical** | Homepage, workspace, auth, search, AI, settings, object detail |
| Navigation Model | §9 | **Critical** | Side rail, bottom tabs, top bar, breadcrumb, command palette |
| Typography | §10 | Major | All text rendering, hierarchy, type scale |
| Motion Language | §11 | **Critical** | All transitions, animations, micro-interactions |
| Object Continuity | §12 | **Critical** | Object detail, workspace state, cross-class transitions |
| Capability Parity | §13 | **Critical** | Every feature on every class, batch operations, data presentation |
| Experience Invariants | §14 | **Critical** | All UI changes — litmus test |
| Failure Behaviour | §15 | **Critical** | AI offline, network loss, runtime failure, third-party failure, storage full |
| Predictability over Cleverness | §16 | **Critical** | Adaptation engine, user overrides, determinism, understandability |
| Adaptation Confidence | §17 | **Critical** | Runtime confidence evaluation, uncertainty handling, signal conflict resolution |
| Constitutional Archival | §18 | Major | Archive management, version history, document lineage |

---

## 4. Compliance Traceability Requirement

Before any execution mode is declared complete, Hermes shall:

1. Identify all domains affected by the execution mode
2. Look up each domain's governing constitutional section(s) from §2
3. Determine the applicable severity level from the Compliance Checklist
4. Verify compliance against all applicable criteria in the Constitutional Compliance Checklist (DNA-CC-01)
5. Record the result in the execution mode's closure report, noting severity level and pass/fail status

**A feature without constitutional traceability cannot be accepted.**  
**A feature with any Critical failure is Constitutionally Defective and must be redesigned.**

---

## 5. Constitutional Cross-Reference Index

| Cross-Reference | Source | Target |
|-----------------|--------|--------|
| §5 → DNA-01.2 | Runtime Context (core) | Runtime Context Spec |
| §6 → DNA-01.2 §2.3 | Environment (core) | Environment dimension spec |
| §7 → DNA-01.2 §2.2 | Attention (core) | Attention State dimension spec |
| §8 → DNA-01.6 | Layout Composition (core) | Layout Matrix |
| §10 → DNA-01.5 | Typography (core) | Typography Spec |
| §11 → DNA-01.7 | Motion (core) | Motion & Transition Spec |
| §12 → DNA-01.6 | Object Continuity (core) | Layout Matrix |
| §13 → DNA-01.4 | Capability Parity (core) | Component Adaptation Spec |
| §16 → DNA-01.2 §3 | Predictability (core) | Runtime Context determinism |
| §17 → DNA-01.2 §2.9 | Adaptation Confidence (core) | Runtime Context confidence dimension |

---

## 6. Document History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | Initial creation per Constitutional Freeze directive | Hermes Agent |
| 2.0 | 2026-07-28 | Revised per DIRECTIVE — DNA-01 RATIFICATION REVISION: positioned DNA-01 as Technical Constitution within multi-document hierarchy, added severity column to mappings | Hermes Agent |