# PROGRAMME-03A — Journey Semantics Consolidation

## Deliverable 1: Journey Duplication Audit

### Methodology
Every frozen UCP was audited for duplicated journey/lifecycle semantics:
status state machines, transition logic, milestone progression, 
disruption/recovery, and health assessment patterns.

### Raw Findings (pattern occurrence counts per UCP)

| UCP | Lifecycle | Transition | Status | Milestone | Disrupt | Replan |
|-----|-----------|------------|--------|-----------|---------|--------|
| UCP-02 Relationship | 2 | 0 | 70 | 23 | 1 | 0 |
| UCP-03 Financial | 1 | 0 | 83 | 0 | 15 | 0 |
| UCP-04 Knowledge | 1 | 0 | 6 | 0 | 0 | 0 |
| UCP-05 Decision | 2 | 0 | 31 | 0 | 0 | 0 |
| **UCP-06 Agreement** | **0** | **12** | **181** | **56** | **0** | **0** |
| **UCP-07 Asset** | **10** | **13** | **62** | **0** | **1** | **0** |
| **UCP-08 Initiative** | **1** | **0** | **58** | **158** | **5** | **14** |
| **UCP-09 Operations** | **0** | **0** | **72** | **0** | **62** | **0** |
| UCP-10 Health | 1 | 0 | 82 | 0 | 25 | 0 |
| UCP-11 Learning | 1 | 0 | 49 | 4 | 39 | 0 |

### Key Duplications Identified

#### 1. Status Transition Engine (IDENTICAL PATTERN in UCP-06, UCP-07)
Both UCP-06 (AgreementStatus) and UCP-07 (AssetStatus) implement:
- `valid_transitions()` classmethod returning `dict[str, list[str]]`
- `transition_to(self, new_status)` instance method
- The same algorithm: lookup current in transitions table, check if target is valid, update status + timestamp

**Lines of duplicated logic: ~30 lines × 2 = ~60 lines**

#### 2. Milestone Progression Logic (UCP-08 duplicates Journey Milestone)
UCP-08 (Initiative) implements:
- `progress_pct` property: sum completed / total milestones
- `delayed_milestones` property: filter by explicit delayed status + overdue detection
- `blocked_milestones` property: filter by blocked status

These are generic milestone operations that any journey-capable UCP needs.

#### 3. Disruption Assessment Logic (UCP-09, UCP-10, UCP-11)
UCP-09 implements disruption assessment with: severity detection, bottleneck analysis,
recovery recommendations. Similar disruption patterns exist in UCP-10 and UCP-11.

#### 4. Stage Health Assessment (UCP-08, UCP-09, UCP-10)
Each UCP implements its own health scoring from stage/milestone data.
The computation pattern is identical: weighted score from progress, delays, blocks.

### Status Updates
- All other UCPs (UCP-02 through UCP-05, UCP-10, UCP-11) use lightweight status patterns
  that don't warrant extraction — their status values are data, not lifecycle engines.