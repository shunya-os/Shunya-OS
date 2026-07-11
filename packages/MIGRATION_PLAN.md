# Shunya OS — TypeScript Monorepo Migration Plan
## July 11, 2026

**Current State:** Python/Flask monolith at `/root/shunya_os/app/`
**Target State:** TypeScript monorepo at `/root/shunya_os/packages/`

### Architecture

```
shunya_os/
├── app/                          ← Python (current, production)
└── packages/                     ← TypeScript (migration target)
    ├── types/                    ← @shunya/types — shared type definitions ✅
    ├── foundation/               ← @shunya/foundation — Result, NextAction, Priority
    ├── governance/               ← @shunya/governance — Draft/Auto/Govern
    ├── knowledge/                ← @shunya/knowledge — memory, search, pipeline
    ├── reasoning/                ← @shunya/reasoning — decision engine
    ├── planner/                  ← @shunya/planner — plan generation
    ├── workflow/                 ← @shunya/workflow — state machine
    ├── executor/                 ← @shunya/executor — controlled adapters
    ├── doctor/                   ← @shunya/doctor — system health
    ├── cli/                      ← @shunya/cli — admin CLI
    ├── shared/                   ← @shunya/shared — utilities
    ├── package.json              ← Workspace root
    └── pnpm-workspace.yaml       ← Workspace config
```

### Build Order

1. ✅ **@shunya/types** — Core type definitions (done)
2. ⬜ **@shunya/foundation** — Result, NextAction, Priority, GovernanceLevel
3. ⬜ **@shunya/governance** — GovernanceEngine, Draft/Auto/Govern tiers
4. ⬜ **@shunya/knowledge** — MemoryStore, KnowledgePipeline, WebSearch
5. ⬜ **@shunya/reasoning** — ReasoningEngine, Decision, Recommendation
6. ⬜ **@shunya/planner** — Planner, Plan, PlanStep, Dependency
7. ⬜ **@shunya/workflow** — WorkflowEngine, TaskState, WorkflowTask
8. ⬜ **@shunya/executor** — Executor, ToolRegistry, ActionType adapters
9. ⬜ **@shunya/doctor** — Doctor, health checks, diagnostics
10. ⬜ **@shunya/cli** — Admin CLI for setup, seed, doctor

### Migration Strategy

**Phase 1 (Current):** Python/Flask prototype serving production at app.panchi.club
**Phase 2 (Parallel):** TypeScript monorepo building alongside Python
**Phase 3 (Cutover):** Frontend migrates first (React/Vue), then API layer
**Phase 4 (Complete):** Python sunsets, only TypeScript remains

### Key Decisions

- **p  n  p  m** for package management (workspace-native)
- **Turborepo** for build orchestration
- **Vitest** for testing
- **ESM** modules throughout
- Publishing to npm registry (reserved @shunya scope)
- Each package independently deployable