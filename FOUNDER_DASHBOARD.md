# SHUNYA Founder Navigation Dashboard
> **Part of the Canonical Repository & Knowledge Runtime Directive**
> **Date:** 2026-07-28
> **Status:** Candidate for Founder Review

This dashboard enables the Founder to answer:

- **Where is this defined?**
- **Why does this exist?**
- **What depends on it?**
- **Can I safely change it?**
- **What will break if I remove it?**

---

## 1. Quick Navigation

| What You Want | Look Here |
|---------------|-----------|
| Constitutional foundation | `constitution/FIRST_PRINCIPLES.md` |
| System authority | `constitution/SHUNYA_CONSTITUTION.md` |
| Term definitions | `constitution/CANONICAL_DEFINITIONS.md` |
| Compliance rules | `constitution/CONSTITUTIONAL_COMPLIANCE.md` |
| Implementation rules | `constitution/HERMES_IMPLEMENTATION_CHARTER.md` |
| Architecture | `SHUNYA_ARCHITECTURE_v1.0.md`, `architecture/` |
| Governance | `governance/SHUNYA_GOVERNANCE_MODEL.md` |
| Engineering standards | `governance/SHUNYA_ENGINEERING_CONSTITUTION.md` |
| Engine specs | `governance/engine_specs/` |
| ADRs | `architecture/adr/`, `governance/adr/` |
| Implementation plan | `SHUNYA_IMPLEMENTATION_PROGRAM.md` |
| Phase progress | `SHUNYA_ENGINEERING_DASHBOARD.md` |
| Sprint plan | `SHUNYA_SPRINT_PLAN.md` |
| Backlog | `SHUNYA_PROGRAM_BACKLOG.md` |
| Design canons | `docs/canon/` |
| UX canons | `design/experience/` |
| Visual design | `design/visual-design-bible/` |
| DNA architecture | `architecture/dna-01*.md` |
| AI context | `AI_CONTEXT_INDEX.yaml` |
| Full index | `REPOSITORY_INDEX.md` |
| Dependencies | `DEPENDENCY_MAPS.md` |
| Duplicates | `DUPLICATE_ANALYSIS.md` |
| Health | `scripts/repo-health-check.sh` |

---

## 2. Where Is This Defined?

### Engine X

| Engine | ID | Constitution | Definitions | Engine Spec | Runtime |
|--------|-----|-------------|-------------|-------------|---------|
| Observer | ENG-OBS | CONST-II §3.1(1) | DEF-026 | ES-006 | core/intelligence/perception/ |
| Memory | ENG-MEM | CONST-II §3.1(2) | DEF-025 | ES-007 (shared) | core/memory_knowledge_runtime/ |
| Knowledge | ENG-KNW | CONST-II §3.1(3) | DEF-021 | ES-002 | core/memory_knowledge_runtime/ |
| Reasoner | ENG-RSN | CONST-II §3.1(4) | DEF-010 (Engine) | ES-003 | core/intelligence/reasoning/ |
| Simulation | ENG-SIM | CONST-II §3.7 | DEF-031 | (proposed) | core/projection/ |
| Planner | ENG-PLN | CONST-II §3.1(6) | DEF-010 (Engine) | ES-004 | core/planning_runtime/ |
| Executive | ENG-EXC | CONST-II §3.1(7) | DEF-010 (Engine) | ES-005 | core/execution_runtime/ |
| Evaluator | ENG-EVL | CONST-II §3.1(8) | DEF-028 (Outcome) | — | core/intelligence/decision/ |
| Learner | ENG-LRN | CONST-II §3.1(9) | DEF-023 | ES-007 | core/intelligence/learning/ |
| Governance | ENG-GOV | CONST-II §3.1(10), §9.1 | DEF-017 | ES-001 | core/runtime_pipeline/ |

### Constitutional Definition X

| Definition | ID | Section | Volume | Defined In |
|-----------|----|---------|--------|------------|
| Architecture | DEF-001 | §1 | CONST-III | constitution/CANONICAL_DEFINITIONS.md |
| Audit Trail | DEF-002 | §2 | CONST-III | constitution/CANONICAL_DEFINITIONS.md |
| Business-Agnostic Core | DEF-003 | §3 | CONST-III | constitution/CANONICAL_DEFINITIONS.md |
| Canonical Source | DEF-004 | §4 | CONST-III | constitution/CANONICAL_DEFINITIONS.md |
| Cognitive Architecture | DEF-005 | §5 | CONST-III | constitution/CANONICAL_DEFINITIONS.md |
| Simulation Engine | DEF-031 | §31 | CONST-III | constitution/CANONICAL_DEFINITIONS.md |

### Phase X

| Phase | ID | Report | Plan | Engine | Status |
|-------|----|--------|------|--------|--------|
| A | PHASE-A | PHASE_A_IMPLEMENTATION_REPORT.md | — | Foundation | Completed |
| B | PHASE-B | PHASE_B_IMPLEMENTATION_REPORT.md | — | Reasoner | Completed |
| C | PHASE-C | PHASE_C_IMPLEMENTATION_REPORT.md | — | Observer | Completed |
| D | PHASE-D | PHASE_D_IMPLEMENTATION_REPORT.md | — | Evaluator | Completed |
| E | PHASE-E | PHASE_E_IMPLEMENTATION_REPORT.md | — | Knowledge | Completed |
| F | PHASE-F | PHASE_F_IMPLEMENTATION_REPORT.md | — | Executive | Completed |
| G | PHASE-G | PHASE_G_COMPLETION_REPORT.md | — | Learner | Completed |
| H | PHASE-H | PHASE_H_COMPLETION_REPORT.md | — | Memory | Completed |
| I | PHASE-I | PHASE_I_COMPLETION_REPORT.md | PHASE_I_IMPLEMENTATION_PLAN.md | Planner | Completed |
| J | PHASE-J | PHASE_J_COMPLETION_REPORT.md | PHASE_J_IMPLEMENTATION_PLAN.md | Automation | Completed |
| K | PHASE-K | PHASE_K_COMPLETION_REPORT.md | PHASE_K_IMPLEMENTATION_PLAN.md | Projection/Simulation | Completed |
| L | PHASE-L | PHASE_L_COMPLETION_REPORT.md | PHASE_L_IMPLEMENTATION_PLAN.md | Convergence | Completed |
| M | PHASE-M | PHASE_M_COMPLETION_REPORT.md | PHASE_M_IMPLEMENTATION_PLAN.md | Platform | Completed |
| N | PHASE-N | — | PHASE_N_IMPLEMENTATION_PLAN.md | Platform | In Progress |

---

## 3. Why Does This Exist?

### Constitutional Authority Chain

Every artifact exists because it derives from a constitutional source:

```
FIRST PRINCIPLE (CONST-I)
  → Why: Core axiom of the system
  → Authority: Self-evident (asserted, not derived)

CONSTITUTIONAL ARTICLE (CONST-II)
  → Why: Operationalizes a First Principle
  → Authority: "Authority: Principle [N]" in article header

CANONICAL DEFINITION (CONST-III)
  → Why: Gives precise meaning to a constitutional term
  → Authority: "Canonical owner: [Volume II, §N]" in definition

ENGINE SPEC (ES-NNN)
  → Why: Specifies how a constitutional article is implemented
  → Authority: "Authority: [CONST-I Principle N]" in spec header

ARCHITECTURE DECISION (ADR-NNN)
  → Why: Records a design decision with constitutional traceability
  → Authority: "Governing articles: [CONST-II §N]" in ADR

IMPLEMENTATION (PHASE-N)
  → Why: Builds the system according to the specs
  → Authority: Derivation chain in implementation documentation
```

### Quick Answers

| Question | Answer |
|----------|--------|
| Why does the Observer Engine exist? | CONST-I Principle III (Necessity of Intelligence) → CONST-II §3.1(1) → ES-006 | |
| Why does the Governance Engine exist? | CONST-I Principle VIII (Primacy of Governance) → CONST-II §9.1 → ES-001 |
| Why does the Simulation Engine exist? | CONST-I Principle XIII (Necessity of Foresight) → CONST-II §3.7 → DEF-031 |
| Why does ADR-004 exist? | To define the Universal Object Protocol per CONST-II §6.6 |
| Why does PHASE-A exist? | To implement the foundation infrastructure (ES-001 Governance Engine first) |
| Why does DNA-01 exist? | To define device-native architecture per CONST-II §5.2 (Layer Architecture) |

---

## 4. What Depends on It?

### Impact Analysis — "What will break if I remove X?"

| If You Remove | Directly Affected | Indirectly Affected | Risk Level |
|---------------|-------------------|---------------------|------------|
| CONST-I (First Principles) | All 5 downstream volumes | Entire system | 🔴 CRITICAL — no system without principles |
| CONST-II §3.1 (Engine list) | All 10 engines, ADRs, specs | Implementation phases | 🔴 CRITICAL — no architecture |
| CONST-III (Definitions) | All documents referencing definitions | All AI agents, code | 🔴 CRITICAL — vocabulary collapses |
| Observer Engine | Memory, Knowledge, Reasoner | All downstream engines | 🔴 CRITICAL — no perception |
| Governance Engine | All engines, all operations | Entire system | 🔴 CRITICAL — no enforcement |
| Simulation Engine | Planner (precedence), Reasoner | Prediction quality | 🟡 MEDIUM — planning continues without simulation |
| ADR-004 (Object Protocol) | All objects, kernel | All APIs | 🔴 CRITICAL — no object standard |
| DNA-01 (Device-Native) | Frontend | UX on mobile/tablet | 🟡 MEDIUM — desktop still works |
| PHASE-A report | — | Historical record | 🟢 LOW — historical only |
| archive/ directory | — | — | 🟢 LOW — static archives |

### Dependency Tracing

To trace what depends on a given artifact:

1. **Look up the artifact ID** in CANONICAL_MANIFEST.yaml
2. **Search KNOWLEDGE_GRAPH.yaml** for all relationships where `source:` or `target:` matches the ID
3. **Check ADRs** for constitutional references to the artifact
4. **Check engine specs** for dependency declarations
5. **Check implementation code** for direct imports

---

## 5. Can I Safely Change It?

### Change Classification

| Change Type | Authorization Required | Risk |
|-------------|----------------------|------|
| Constitutional amendment (Principle) | Founder approval + CAP | 🔴 CRITICAL |
| Constitutional article amendment | Founder approval + CAP | 🔴 CRITICAL |
| Engine spec change | Chief Architect + ADR | 🟡 MEDIUM |
| ADR creation | Chief Architect | 🟢 LOW |
| Implementation detail | Engineering team | 🟢 LOW |
| Phase report | Engineering team | 🟢 LOW |
| Documentation | Engineering team | 🟢 LOW |
| Design canon | Experience team | 🟢 LOW |

### Safety Check Process

Before changing any artifact:

1. **Check if it's a Protected Guarantee** (CONST-II, Appendix A, G-01 through G-17)
   - If yes, change requires CAP with restricted article provisions
   - If no, proceed to step 2
2. **Check if the artifact is referenced by other artifacts**
   - Search KNOWLEDGE_GRAPH.yaml for incoming relationships
   - If dependents exist, trace the impact
3. **Check if the change would weaken an architectural invariant**
   - Layer boundaries cannot be violated
   - Engine responsibilities cannot be duplicated
   - Timeline is append-only
   - Identity is permanent

---

## 6. Repository Health

| Check | Status | Last Run |
|-------|--------|----------|
| Git integrity | ✅ | `scripts/repo-health-check.sh` |
| Canonical manifest | ✅ | CANONICAL_MANIFEST.yaml |
| Knowledge graph | ✅ | KNOWLEDGE_GRAPH.yaml |
| Traceability matrix | ✅ | TRACEABILITY_MATRIX.md |
| Repository index | ✅ | REPOSITORY_INDEX.md |
| Dependency maps | ✅ | DEPENDENCY_MAPS.md |
| Duplicate analysis | ✅ | DUPLICATE_ANALYSIS.md |
| AI context index | ✅ | AI_CONTEXT_INDEX.yaml |
| Automated health check | ✅ | scripts/repo-health-check.sh |
| Cross-volume references | ✅ | Verified by health check |

---

## 7. Quick Reference: Canonical IDs

| Prefix | Type | Example |
|--------|------|---------|
| CONST- | Constitutional volume | CONST-I, CONST-II |
| ENG- | Engine | ENG-OBS, ENG-GOV |
| ES- | Engine spec | ES-001, ES-010 |
| RUNTIME- | Core runtime | RUNTIME-KRNL, RUNTIME-PIPE |
| ADR- | Architecture Decision Record | ADR-001, ADR-007 |
| CANON- | Design canon | CANON-00, CANON-12 |
| CANON-UX- | Experience canon | CANON-UX-01, CANON-UX-19 |
| CANON-* | Runtime canon | CANON-COG, CANON-EXEC |
| DNA- | Device-native architecture | DNA-01, DNA-01.9 |
| ARCH- | Architecture document | ARCH-ADAPT, ARCH-BASELINE |
| GOV- | Governance document | GOV-ENG, GOV-MODEL |
| PHASE- | Implementation phase | PHASE-A, PHASE-N |
| DSGN- | Design artifact | DSGN-VDB, DSGN-LN |
| FE- | Frontend document | FE-COMP, FE-DS |
| KNOW- | Knowledge artifact | KNOW-VAULT, KNOW-AI-ROADMAP |
| DEF- | Constitutional definition (CONST-III) | DEF-001, DEF-031 |
| G- | Protected Guarantee | G-01, G-17 |
| GIT- | Git branch | GIT-main, GIT-docs |
| CAP- | Constitutional Amendment Proposal | CAP-01 |

---

## 8. File Search Quick Reference

```bash
# Find where an artifact is defined
grep -r "ENG-OBS" . --include="*.yaml" --include="*.md" | head -5

# Find what depends on an artifact
grep -r "ENG-OBS\|ADR-001\|PHASE-A" KNOWLEDGE_GRAPH.yaml

# Find all references to a constitutional article
grep -r "§3.7\|CONST-II.*3.7" . --include="*.md" | head -10

# Check if an artifact is documented
grep -r "ENG-SIM" . --include="*.md" --include="*.yaml" | wc -l

# Trace the authority chain for an artifact
grep -A5 "id: ENG-OBS" CANONICAL_MANIFEST.yaml
```