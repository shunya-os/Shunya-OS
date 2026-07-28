# Planning & Reasoning Runtime Canon

> **Canonical Document · Phase I**
> **Status: CANONICAL — Implementation Specification**
> **Version: 1.0**

---

## 1. Purpose

The Planning & Reasoning Runtime is the bridge between thinking and execution. It transforms goals into actionable plans, manages constraints and resources, generates alternatives, validates approaches, repairs broken plans, and provides complete observability.

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│               PLANNING & REASONING RUNTIME                        │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Goal         │  │  Hierarchical│  │  Constraint          │  │
│  │ Decomposer   │  │  Task Network│  │  Manager             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Dependency   │  │  Resource    │  │  Temporal            │  │
│  │ Graph Engine │  │  Planner     │  │  Planner             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Multi-Step   │  │  Alternative │  │  Cost/Risk           │  │
│  │ Reasoner     │  │  Generator   │  │  Estimator           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Plan         │  │  Plan Repair │  │  Re-planning         │  │
│  │ Validator    │  │  Engine      │  │  Engine              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                   │
│  ┌──────────────┐  ┌────────────────────────────────────────┐  │
│  │ Human        │  │  Provenance + Observability            │  │
│  │ Approval     │  │  trace, version, rationale, timeline   │  │
│  └──────────────┘  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## 3. Goal Decomposition

A goal is broken into sub-goals recursively until primitive tasks are reached. Each sub-goal inherits constraints from its parent.

## 4. Hierarchical Task Network

Tasks form a tree: compound tasks decompose into smaller tasks. Primitive leaf tasks map to Execution Runtime actions.

## 5. Constraints

| Type | Description |
|------|-------------|
| Hard | Must be satisfied (resources, dependencies, deadlines) |
| Soft | Should be satisfied (cost, risk, preference) |

## 6. Plan Lifecycle

DRAFT → VALIDATED → APPROVED → EXECUTING → COMPLETED / FAILED / REPAIRED

---

*End of Planning & Reasoning Runtime Canon*