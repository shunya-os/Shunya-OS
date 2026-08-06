# Deliverable 2: Journey Semantics Design

## Module Location
`core/journey_semantics/__init__.py` — internal shared primitive.

## Not a UCP
Journey Semantics is NOT a Universal Capability Package.
It is NOT user-visible.
It is NOT a Runtime.
It has no public API exports.

## Interface (internal, prefixed with `_` by convention)

### `validate_transition(current, target, transitions) -> bool`
Pure function. Checks if a state transition is valid per the transition table.

### `apply_transition(current, target, transitions, on_transition=None) -> tuple[bool, str]`
Pure function (with optional callback). Validates transition, calls callback on success.

### `Milestone` dataclass
A named checkpoint with status, due_date, dependencies, evidence_ids.

### `MilestoneStatus` enum
PENDING, IN_PROGRESS, COMPLETED, DELAYED, BLOCKED, SKIPPED, CANCELLED with valid_transitions().

### `compute_progress_pct(milestones) -> float`
Percentage of completed milestones.

### `find_delayed_milestones(milestones) -> list[Milestone]`
Explicit delayed + overdue detection.

### `find_blocked_milestones(milestones) -> list[Milestone]`
Filter by blocked status.

### `assess_disruption_impact(current_stage, severity, transitions) -> dict`
Impact assessment with proceed/block recommendation.

### `compute_stage_health(milestones, delays_weight, blocks_weight) -> dict`
Health score from milestone data.

### `journey_lifecycle(name, transitions) -> Enum`
Factory for creating status enums with valid_transitions().

## Design Principles
- Stateless — no Journey Semantics object stores state
- State stays on Living Objects (Agreement, Asset, Initiative, etc.)
- Never replaces Reality Runtime
- All functions are pure — results derived from data, never mutated
- Backward compatible — every Living Object's public API is unchanged